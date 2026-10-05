#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
tmp=$(mktemp -d "${TMPDIR:-/tmp}/oslab-test.XXXXXX")
trap 'rm -rf -- "$tmp"' EXIT
export HOME="$tmp/home with spaces"
mkdir -m 700 -p -- "$HOME"
export OSLAB_WORKSPACE="$HOME/work space"
tool=(python3 "$script_dir/oslab.py")
"${tool[@]}" doctor
"${tool[@]}" list
for n in {1..11}; do "${tool[@]}" start "lab$n"; done
printf 'student work\n' > "$OSLAB_WORKSPACE/lab2/my work.txt"
"${tool[@]}" start lab2
grep -q 'student work' "$OSLAB_WORKSPACE/lab2/my work.txt"
mv -- "$OSLAB_WORKSPACE/lab2/incoming/quarter 1.txt" "$OSLAB_WORKSPACE/lab2/reports/"
mv -- "$OSLAB_WORKSPACE/lab2/incoming/quarter 2.txt" "$OSLAB_WORKSPACE/lab2/reports/"
"${tool[@]}" check lab2 | grep -q 'PASS'
"${tool[@]}" reset lab2
test -e "$OSLAB_WORKSPACE/lab2/incoming/quarter 1.txt"
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
echo 'local lifecycle and isolation PASS'
