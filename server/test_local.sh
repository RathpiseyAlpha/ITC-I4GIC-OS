#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
tmp=$(mktemp -d "${TMPDIR:-/tmp}/oslab-test.XXXXXX")
trap 'rm -rf -- "$tmp"' EXIT
export HOME="$tmp/home with spaces"
mkdir -m 700 -p -- "$HOME"
export OSLAB_WORKSPACE="$HOME/work space"
# Fake class inbox and release folder; "students" are test names because every test runs as one uid.
export OSLAB_INBOX="$tmp/inbox" OSLAB_RELEASE_DIR="$tmp/release" OSLAB_TEACH_STATE="$tmp/teach" OSLAB_TEACH_TRUST_NAME=1
export OSLAB_TEST_USER=student-a
mkdir -- "$OSLAB_INBOX" "$OSLAB_RELEASE_DIR"
tool=(python3 "$script_dir/oslab.py")
teach=(python3 "$script_dir/oslab_teach.py")
value() { "${tool[@]}" values "$1" | awk -v key="$2" '$1 == key { sub(/^[^=]*= /, ""); print }'; }
"${tool[@]}" doctor
"${tool[@]}" list
for n in {1..11}; do "${tool[@]}" start "lab$n"; done
printf 'student work\n' > "$OSLAB_WORKSPACE/lab2/my work.txt"
"${tool[@]}" start lab2
grep -q 'student work' "$OSLAB_WORKSPACE/lab2/my work.txt"
file1=$(value lab2 file1); file2=$(value lab2 file2); owner=$(value lab2 owner)
lab2="$OSLAB_WORKSPACE/lab2"
mv -- "$lab2/incoming/$file1" "$lab2/incoming/$file2" "$lab2/reports/"
"${tool[@]}" check lab2 | grep -q 'PASS: both files were moved'
mkdir -p -- "$lab2/TechCorp/$owner/archive" "$lab2/evidence"
cp -- "$lab2/reports/$file1" "$lab2/reports/$file2" "$lab2/TechCorp/$owner/"
cp -- "$lab2/reports/$file1" "$lab2/TechCorp/$owner/archive/first-original.txt"
printf '%s\n' "../$owner/$file1" "$lab2/TechCorp/$owner/$file1" > "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q 'milestones: 4/4'
printf 'changed\n' > "$lab2/TechCorp/$owner/$file2"
"${tool[@]}" check lab2 | grep -q 'TRY : TechCorp'
"${tool[@]}" reset lab2
test -e "$OSLAB_WORKSPACE/lab2/incoming/$file1"
test -e "$OSLAB_WORKSPACE/.attempts"/lab2-*/my\ work.txt
printf 'unrelated\n' > "$OSLAB_WORKSPACE/unrelated.txt"
"${tool[@]}" clean lab2
test -e "$OSLAB_WORKSPACE/unrelated.txt"
test ! -e "$OSLAB_WORKSPACE/lab2"
ln -s source.txt "$OSLAB_WORKSPACE/lab3/links/good.txt"
ln -s missing.txt "$OSLAB_WORKSPACE/lab3/links/dangling.txt"
"${tool[@]}" start lab3
"${tool[@]}" status lab3
"${tool[@]}" reset lab3
test -L "$OSLAB_WORKSPACE/.attempts"/lab3-*/links/good.txt
test -L "$OSLAB_WORKSPACE/.attempts"/lab3-*/links/dangling.txt
ln -s "$tmp" "$OSLAB_WORKSPACE/lab3/escape"
if "${tool[@]}" clean lab3 2>/dev/null; then echo 'symlink guard failed' >&2; exit 1; fi
test -e "$OSLAB_WORKSPACE/lab3/.oslab-managed.json"
if OSLAB_WORKSPACE="$tmp/outside" "${tool[@]}" list 2>/dev/null; then echo 'path guard failed' >&2; exit 1; fi
mkdir -p "$tmp/fakebin"
export FAKE_CRONTAB="$tmp/personal-crontab"
printf '15 9 * * * /usr/bin/true # unrelated\n' > "$FAKE_CRONTAB"
cat > "$tmp/fakebin/crontab" <<'SH'
#!/usr/bin/env bash
case "$1" in
  -l) cat "$FAKE_CRONTAB" ;;
  -) cat > "$FAKE_CRONTAB" ;;
  *) exit 2 ;;
esac
SH
chmod 700 "$tmp/fakebin/crontab"
export PATH="$tmp/fakebin:$PATH"
cron=(python3 "$script_dir/lab10_cron.py")
"${cron[@]}" install
"${cron[@]}" install
test "$(grep -c 'OSLAB-LAB10' "$FAKE_CRONTAB")" -eq 1
"${cron[@]}" remove
grep -q '# unrelated' "$FAKE_CRONTAB"
if grep -q 'OSLAB-LAB10' "$FAKE_CRONTAB"; then echo 'cron isolation failed' >&2; exit 1; fi
store="$OSLAB_WORKSPACE/lab8/store"
printf '5\n' > "$store/stock.txt"
bash "$script_dir/../teaching/instructor/lab8/buy_flawed.sh" "$store" 4 & p1=$!
bash "$script_dir/../teaching/instructor/lab8/buy_flawed.sh" "$store" 4 & p2=$!
wait "$p1"; wait "$p2"
test "$(grep -c '^sold 4$' "$store/sales.log")" -eq 2
test "$(cat "$store/stock.txt")" -eq 1
printf '5\n' > "$store/stock.txt"; : > "$store/sales.log"
bash "$script_dir/../teaching/instructor/lab8/buy_solution.sh" "$store" 4 > "$tmp/buy1.out" 2>&1 & p1=$!
bash "$script_dir/../teaching/instructor/lab8/buy_solution.sh" "$store" 4 > "$tmp/buy2.out" 2>&1 & p2=$!
wait "$p1" || true; wait "$p2" || true
test "$(grep -c '^sold 4$' "$store/sales.log")" -eq 1
test "$(cat "$store/stock.txt")" -eq 1
vault="$OSLAB_WORKSPACE/lab9/vault"
timeout 6 bash "$script_dir/../teaching/instructor/lab9/worker_solution.sh" "$vault" A opposite > "$tmp/deadA.out" 2>&1 & p1=$!
timeout 6 bash "$script_dir/../teaching/instructor/lab9/worker_solution.sh" "$vault" B opposite > "$tmp/deadB.out" 2>&1 & p2=$!
wait "$p1" || true; wait "$p2" || true
grep -q 'holds' "$tmp/deadA.out"
grep -q 'holds' "$tmp/deadB.out"
if ! grep -q 'second lock timeout' "$tmp/deadA.out" && ! grep -q 'second lock timeout' "$tmp/deadB.out"; then
  echo 'opposite-order conflict was not observed' >&2; exit 1
fi
timeout 6 bash "$script_dir/../teaching/instructor/lab9/worker_solution.sh" "$vault" A ordered > "$tmp/orderA.out" 2>&1 & p1=$!
timeout 6 bash "$script_dir/../teaching/instructor/lab9/worker_solution.sh" "$vault" B ordered > "$tmp/orderB.out" 2>&1 & p2=$!
wait "$p1"; wait "$p2"
grep -q 'holds both' "$tmp/orderA.out"
grep -q 'holds both' "$tmp/orderB.out"
# Personal values are stable for one student and differ between students.
test "$("${tool[@]}" values lab2)" = "$("${tool[@]}" values lab2)"
test "$("${tool[@]}" values lab2)" != "$(OSLAB_TEST_USER=student-b "${tool[@]}" values lab2)"
# Pre-lab, a single prediction, and a checkpoint that stays closed until release.
printf 'a\nb\nb\nb\n' | "${tool[@]}" prelab lab1 | grep -q 'Saved and sent'
printf '2\n9\n1\nboth read the old value\n' | "${tool[@]}" predict lab8 | grep -q 'Saved and sent'
if printf '2\n9\n1\nagain\n' | "${tool[@]}" predict lab8 2>/dev/null; then echo 'second prediction accepted' >&2; exit 1; fi
if "${tool[@]}" checkpoint lab8 </dev/null 2>/dev/null; then echo 'checkpoint open before release' >&2; exit 1; fi
"${tool[@]}" hint lab8 3 | grep -q 'flock'
# Lab 8 check: the supplied script and each wrong "AI answer" lose the invariant; the repaired model keeps it.
"${tool[@]}" reset lab8 >/dev/null
"${tool[@]}" check lab8 | grep -q 'TRY : two buyers at once'
for wrong in a b c; do
  cp -- "$store/ai-answers/$wrong.sh" "$store/buy.sh"
  "${tool[@]}" check lab8 | grep -q 'TRY : two buyers at once' || { echo "wrong answer $wrong passed" >&2; exit 1; }
done
cp -- "$script_dir/../teaching/instructor/lab8/buy_fixed.sh" "$store/buy.sh"
"${tool[@]}" check lab8 | grep -q 'milestones: 3/3'
# Release, answer with the key, then make the live change and check it.
"${teach[@]}" release lab8 | grep -q 'released'
if "${teach[@]}" release lab8 2>/dev/null; then echo 'second release accepted' >&2; exit 1; fi
printf 'student-a\n' > "$tmp/roster.txt"
"${teach[@]}" key lab8 --roster "$tmp/roster.txt" > "$tmp/key.txt"
answer() { awk -v key="$1" '$1 == "checkpoint" && $2 == key { gsub(/[^0-9]/, "", $3); print $3 }' "$tmp/key.txt"; }
limit=$(grep -o "'limit': [0-9]*" "$tmp/key.txt" | tr -dc '0-9')
printf '%s\n%s\n%s\nthe lock line before the read\n' "$(answer accepted)" "$(answer stock)" "$(answer sold)" \
  | "${tool[@]}" checkpoint lab8 | grep -q "at most $limit units"
"${tool[@]}" check lab8 | grep -q 'TRY : checkpoint'
awk -v limit="$limit" '{ print } $0 == "quantity=$1" { print "if (( quantity > " limit " )); then echo over-limit >&2; exit 4; fi" }' \
  "$store/buy.sh" > "$tmp/buy.limited" && cp -- "$tmp/buy.limited" "$store/buy.sh"
"${tool[@]}" check lab8 | grep -q 'milestones: 4/4'
"${teach[@]}" board lab8 > "$tmp/board.txt"
grep -Eq '^student-a +.* 3/3 +done' "$tmp/board.txt"
"${teach[@]}" export lab8 | grep -q '^student-a,.*,3/3,done,2,'
echo 'local lifecycle, isolation, personal values, checks and instructor board PASS'
