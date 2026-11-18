// Run: node tools/test_critical_section.cjs
// Exercises the real inline script against a small DOM stand-in. This checks
// code/label/state agreement, not browser painting or animation timing.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../lectures/visualizations/critical-section.html'), 'utf8');
const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)];
for (const script of scripts) new vm.Script(script[1]);
const main = scripts.find(script => script[1].includes('const CS='))[1];
const nodes = new Map();
const timers = new Map();
let timerId = 0;
let flights = 0;

class Element {
  constructor() {
    this.style = {};
    this.className = '';
    this.textContent = '';
    this.attributes = {};
    this.clientWidth = 900;
    this.html = '';
    this.queries = {};
    this.classList = {
      add: (...names) => { this.className = [...new Set([...this.className.split(' ').filter(Boolean), ...names])].join(' '); },
      remove: (...names) => { this.className = this.className.split(' ').filter(name => !names.includes(name)).join(' '); },
      toggle: (name, on) => { on ? this.classList.add(name) : this.classList.remove(name); },
      contains: name => this.className.split(' ').includes(name),
    };
  }
  set innerHTML(value) {
    for (const match of this.html.matchAll(/\bid="([^"]+)"/g)) nodes.delete(match[1]);
    this.html = value;
    for (const match of value.matchAll(/\bid="([^"]+)"/g)) nodes.set(match[1], new Element());
  }
  get innerHTML() { return this.html; }
  setAttribute(name, value) { this.attributes[name] = value; }
  querySelector(selector) { return this.queries[selector] ??= new Element(); }
  appendChild() {}
  animate() { flights++; return {}; }
  remove() {}
}

for (const match of html.slice(0, html.indexOf('/* Each thread')).matchAll(/\bid="([^"]+)"/g)) {
  nodes.set(match[1], new Element());
}
const context = vm.createContext({
  document: {
    getElementById: id => nodes.get(id) || null,
    createElement: () => new Element(),
    addEventListener() {},
  },
  window: { matchMedia: () => ({ matches: false }) },
  setInterval: callback => { const id = ++timerId; timers.set(id, callback); return id; },
  clearInterval: id => timers.delete(id),
});
vm.runInContext(main, context);
const run = source => vm.runInContext(source, context);
const plain = value => JSON.parse(JSON.stringify(value));
const el = id => nodes.get(id);
const text = value => value.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<');

// Independent instruction-order fixtures, rather than expectations generated
// from the implementation's labels or instruction descriptions.
const remainder = '/* other work */';
const update = ['reg = counter;', 'reg = reg + 1;', 'counter = reg;'];
const plans = {
  none: [remainder, ...update],
  lockvar: [remainder, 'while (lock == 1) ;', 'lock = 1;', ...update, 'lock = 0;'],
  turn: [remainder, 'while (turn == j) ;', ...update, 'turn = j;'],
  flags: [remainder, 'flag[i] = true;', 'while (flag[j]) ;', ...update, 'flag[i] = false;'],
  peterson: [remainder, 'flag[i] = true;', 'turn = j;', 'while (flag[j] && turn == j) ;', ...update, 'flag[i] = false;'],
  tas: [remainder, 'while (test_and_set(&lock)) ;', ...update, 'lock = 0;'],
  cas: [remainder, 'while (compare_and_swap(&lock, 0, 1) != 0) ;', ...update, 'lock = 0;'],
  atomic: [remainder, 'temp = *v;', '} while (temp != compare_and_swap(v, temp, temp + 1));'],
  mutex: [remainder, 'acquire(lock);', ...update, 'release(lock);'],
};

function checkDisplay(id, state) {
  run(`st=${JSON.stringify(state)};lastStep=null;render()`);
  const threadHtml = el('threads').innerHTML.split('<div class="thr').slice(1);
  assert.equal(threadHtml.length, 2);
  for (const i of [0, 1]) {
    const code = threadHtml[i];
    const lines = [...code.matchAll(/data-line="(\d+)" class="([^"]*)"><span class="src">([\s\S]*?)<\/span>(?:<span class="(?:tag|c rc)">|<\/div>)/g)];
    assert.deepEqual(lines.map(line => text(line[3])), plans[id].map((source, n) => `${n + 1} ${source}`));
    const highlighted = lines.filter(line => line[2].split(' ').includes('pc'));
    if (state.pc[i] === plans[id].length) {
      assert.equal(highlighted.length, 0);
      assert.equal(el('bub' + i).textContent, `T${i} · finished`);
      assert.equal(el('bub' + i).attributes['data-line'], '');
    } else {
      const line = state.pc[i] + 1;
      assert.equal(highlighted.length, 1);
      assert.equal(Number(highlighted[0][1]), line);
      assert.equal(el('bub' + i).attributes['data-line'], String(line));
      const [heading, source] = el('bub' + i).textContent.split('\n');
      assert(heading.startsWith(`T${i} · next ${line}`));
      assert.equal(source, plans[id][state.pc[i]]);
    }
  }
}

let statesChecked = 0;
for (const id of Object.keys(plans)) {
  for (let x = 1; x <= 3; x++) for (let y = 1; y <= 3; y++) {
    run(`setAlgo('${id}');iters=[${x},${y}];analysis=analyse()`);
    assert.deepEqual(plain(run('prog.map(ins=>ins.s)')), plans[id]);
    const analysis = plain(run('analysis'));
    if (['peterson', 'tas', 'cas', 'atomic', 'mutex'].includes(id)) {
      assert.equal(analysis.clash, null);
      assert.equal(analysis.stuck, null);
      assert.deepEqual(analysis.finals, [x + y]);
    } else if (id === 'none' || id === 'lockvar') {
      assert(analysis.clash !== null);
      assert(analysis.finals.some(value => value < x + y));
    } else if (id === 'flags') {
      assert.equal(analysis.clash, null);
      assert.equal(analysis.stuckKind, 'deadlock');
    } else {
      assert.equal(analysis.clash, null);
      assert.deepEqual(analysis.finals, x === y || x === y + 1 ? [x + y] : []);
    }
    const start = plain(run('init()'));
    const queue = [start], seen = new Set([JSON.stringify(start)]);
    for (let n = 0; n < queue.length; n++) {
      const state = queue[n];
      checkDisplay(id, state);
      statesChecked++;
      for (const i of [0, 1]) {
        const next = plain(run(`stepState(${JSON.stringify(state)},${i}).s`));
        const key = JSON.stringify(next);
        if (!seen.has(key)) { seen.add(key); queue.push(next); }
      }
    }
  }
  console.log(`PASS ${id}: instruction order, robot labels and highlighted lines in every reachable state`);
}

// Exercise the real controls, including failed waits, hand-off and undo.
run("setAlgo('lockvar');stepT(0);stepT(0)");
assert(el('captionText').innerHTML.includes('next entry instruction'));
assert(!el('captionText').innerHTML.includes('enters the critical section'));
for (const id of ['tas', 'cas', 'mutex']) {
  run(`setAlgo('${id}');stepT(0);stepT(0);stepT(1);stepT(1)`);
  assert(el('bub1').textContent.includes(id === 'mutex' ? 'will wait' : 'will spin'));
  assert(el('bub1').textContent.includes(plans[id][1]));
  assert.equal(el('bot1').classList.contains('spin'), id !== 'mutex');
  if (id === 'tas') assert.match(el('captionText').innerHTML, /previous value, true/);
  if (id === 'cas') assert.match(el('captionText').innerHTML, /expected 0 and returned 1/);
  run('stepT(0);stepT(0);stepT(0)');
  assert.equal(run('st.lock'), 1);
  assert.equal(el('padv').textContent, 'lock = 1');
  assert.equal(run('inCS(st,0)'), false);
  const count = flights;
  run('render()');
  assert.equal(flights, count, 'a render must not repeat an old write animation');
  const beforeRelease = plain(run('st'));
  run('stepT(0)');
  assert.equal(run('st.lock'), 0);
  run('undo()');
  assert.deepEqual(plain(run('st')), beforeRelease);
  checkDisplay(id, beforeRelease);
}

run("setAlgo('atomic');iters=[1,1];stepT(0);stepT(0);stepT(1);stepT(1);stepT(0);stepT(1)");
assert.equal(run('st.counter'), 1);
assert.equal(run('st.pc[1]'), 1, 'failed CAS must return to the read');
assert.match(el('captionText').innerHTML, /expected 0 and returned 1/);
assert.equal(el('bot1').classList.contains('spin'), false);
run('undo()');
assert.equal(run('st.pc[1]'), 2, 'undo must restore the pending CAS');
run('stepT(1);stepT(1);stepT(1)');
assert.equal(run('st.counter'), 2);
assert.match(el('captionText').innerHTML, /expected 1 and returned 1/);
assert.match(el('lectureCode').innerHTML, /slide 25/);
assert.match(el('lectureCode').innerHTML, /void increment\(atomic_int \*v\)/);
run("setAlgo('mutex')");
assert.match(el('lectureCode').innerHTML, /slide 28/);
assert.match(el('lectureCode').innerHTML, /slide 30/);
assert.match(el('lectureCode').innerHTML, /pthread_mutex_lock\(&amp;m\)/);

run("setAlgo('turn')");
assert.match(el('algos').innerHTML, />Turn only \(strict alternation\)<\/button><button[^>]+>Peterson/);
assert.equal(run('analysis.stuckKind'), 'progress');

for (const id of ['tas', 'cas', 'atomic']) {
  run(`setAlgo('${id}');playTrace('calls')`);
  const tick = () => { for (const callback of [...timers.values()]) callback(); };
  const readySteps = id === 'atomic' ? 4 : 2;
  for (let i = 0; i < readySteps; i++) tick();
  const ready = el('callDetails').innerHTML;
  assert.match(ready, /T0 next, line/);
  assert.match(ready, /T1 next, line/);
  assert.match(ready, id === 'tas' ? /target = &amp;lock/ : id === 'cas' ? /value = &amp;lock/ : /value = v.*shared <code>counter/);
  tick();
  const first = el('callDetails').innerHTML;
  assert.match(first, /Arguments from T0.*Read the shared .*Return to T0/);
  assert.match(first, id === 'tas' ? /lock false → true.*gives <code>false/ : /0 → 1.*gives <code>0/);
  tick();
  const second = el('callDetails').innerHTML;
  assert.match(second, /class="call-flow play"/);
  assert.match(second, id === 'tas' ? /class="wrote".*Wrote <code>true<\/code> again.*lock true → true/ : /class="skipped".*mismatch.*Skipped the write.*1 → 1.*gives <code>1/);
  assert(el(id === 'atomic' ? 'box' : 'pad').classList.contains('call-target'));
  while (timers.size) tick();
  assert.equal(el('callDemo').disabled, false);
  assert.equal(run('hist.length'), readySteps + 2, 'the replay must stop on the second caller’s failed attempt');
  if (id === 'atomic') {
    assert.equal(run('st.counter'), 1);
    assert.equal(run('st.pc[1]'), 1);
    run('stepT(1);stepT(1)');
    assert.match(el('callDetails').innerHTML, /expected = 1.*new_value = 2.*counter 1 → 2/);
    run('undo();undo()');
  }
  run('undo()');
  assert.match(el('callDetails').innerHTML, new RegExp(`Last call · step ${readySteps + 1} · T0`));
  run('reset()');
  assert.doesNotMatch(el('callDetails').innerHTML, /Last call/);
}

// These are geometry calculations, not a browser-layout or screenshot check.
for (const width of [252, 292, 326, 540, 900, 1400]) {
  el('scene').clientWidth = width;
  run("setAlgo('cas')");
  for (const section of ['rem', 'entry', 'cs', 'exit', 'done']) {
    for (const i of [0, 1]) {
      const x = run(`scenePoint('${section}',${i},${width})`);
      if (section === 'entry' || section === 'exit') assert(i === 0 ? x + 30 < width * .3 : x - 30 > width * .7);
    }
  }
  run('stepT(0);stepT(0);stepT(1)');
  const left = parseFloat(el('bub0').style.left), right = parseFloat(el('bub1').style.left);
  const bubbleWidth = parseFloat(el('bub0').style.width);
  assert(left >= 8 && right + bubbleWidth <= width - 8);
  assert(left + bubbleWidth < right, 'the two labels must not overlap');
}
el('bub0').offsetHeight = 110;
el('bub1').offsetHeight = 80;
run('updateScene()');
assert.equal(el('scene').style.minHeight, '296px', 'wrapped labels need room below the counter');

for (const id of Object.keys(plans)) {
  el('scene').clientWidth = 900;
  run(`setAlgo('${id}');stepT(0);undo()`);
  checkDisplay(id, plain(run('init()')));
  for (const trace of ['clash', 'stuck']) {
    if (!run(`analysis.${trace}`)) continue;
    run(`playTrace('${trace}')`);
    let ticks = 0;
    while (timers.size && ticks++ < 200) for (const callback of [...timers.values()]) callback();
    assert.equal(timers.size, 0);
    checkDisplay(id, plain(run('st')));
  }
  run('randomRun()');
  checkDisplay(id, plain(run('st')));
  run('reset()');
  checkDisplay(id, plain(run('init()')));
}
console.log(`PASS ${statesChecked} reachable-state displays across 81 configurations; stepping, waits, undo, replay, random, reset and 6 width calculations`);
