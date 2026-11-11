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
"${tool[@]}" check lab2 | grep -q 'milestones: 4/5'
# Core 3: a real Error: line, and a Fix: path that reaches the report from the reader department.
reader=$(value lab2 reader)
error="Error: cat: 'reports/$file1': No such file or directory"
printf '%s\n' "$error" "Fix: reports/$file1" >> "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q 'TRY : evidence/paths.txt has your Error: line'
printf '%s\n' "../$owner/$file1" "$lab2/TechCorp/$owner/$file1" "$error" "Fix: cat '../../reports/$file1'" > "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q 'milestones: 5/5'
grep -q '"path_error": {"error": true, "fix": true}' $(ls -t "$OSLAB_INBOX"/lab2.check.student-a.*.json | head -1)
# Students type variables in nano, as the instruction shows them: the check reads them the way bash would.
cp -- "$lab2/evidence/paths.txt" "$tmp/paths.keep"
printf '%s\n' 'mv -- "$file1" ../reports/' 'mv -- "$OSLAB_WORKSPACE/lab2/incoming/$file2" "${OSLAB_WORKSPACE}/lab2/reports/"' \
  "$error" 'Fix: ../../reports/"$file1"' > "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q 'milestones: 5/5'
printf '%s\n' "$error" "Fix: ../../reports/'$file1'" 'cat ~/x' > "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q 'milestones: 5/5'
# A failed milestone says why, on screen and in the record for the marking screen.
printf '%s\n' 'Error: I forgot' 'Fix: reports/$file1' > "$lab2/evidence/paths.txt"
out=$("${tool[@]}" check lab2)
grep -q 'why: no relative path' <<<"$out"
grep -q 'why: no absolute path' <<<"$out"
grep -q 'why: the Error: line must hold' <<<"$out"
grep -q "leads to TechCorp/$reader/reports/$file1" <<<"$out"
printf '%s\n' "$error" 'Fix: "$OSLAB_WORKSPACE/lab2/reports/$file1"' > "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q 'why: Fix: .* This is an absolute path'
printf '%s\n' "$error" 'Fix: ../reports/"$file1"' > "$lab2/evidence/paths.txt"
"${tool[@]}" check lab2 | grep -q "leads to TechCorp/reports/$file1"
grep -q '"reasons": {' $(ls -t "$OSLAB_INBOX"/lab2.check.student-a.*.json | head -1)
cp -- "$tmp/paths.keep" "$lab2/evidence/paths.txt"
test -d "$lab2/TechCorp/$owner" && test -n "$reader"
# Debrief: the right answers after the lab, marked against the prediction key; it may be run again.
printf '../reports\nyes\n1\n2\nI guessed\n' | "${tool[@]}" predict lab2 | grep -q 'Saved and sent'
printf '../reports\nno\n1\n2\n' | "${tool[@]}" debrief lab2 | grep -q 'Saved and sent'
"${teach[@]}" export lab2 | grep -q '^student-a,[^,]*,[^,]*,3/4,.*,4/4,'
python3 - "$script_dir" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import oslab
assert oslab.mark("dir", "TechCorp/HR", "TechCorp/HR/") and oslab.mark("dir", "TechCorp/HR", "./TechCorp/HR")
assert oslab.mark("dir", ".", ".") and not oslab.mark("dir", "TechCorp/HR", "TechCorp") and not oslab.mark("dir", ".", "")
# A quote in the middle of a path, or none around a name with a space, is read as bash reads it.
assert oslab.mark("path", ["TechCorp/HR", "reports/a b.txt"], "../../reports/'a b.txt'")
assert oslab.mark("path", ["TechCorp/HR", "reports/a b.txt"], "../../reports/a b.txt")
# Arrow keys typed without readline leave ESC [ D; none of it may stay in the answer.
assert oslab.clean("../re\x1b[Dports\x1bOA") == "../reports"
env = {"file1": "a b.txt", "OSLAB_WORKSPACE": "/w", "HOME": "/h"}
assert oslab.shell_words('cat "$OSLAB_WORKSPACE/lab2/$file1" ~/x \'$file1\' a\\ b', env) == ["cat", "/w/lab2/a b.txt", "/h/x", "$file1", "a b"]
assert oslab.read_path("../$owner/x", env)[1].startswith("oslab does not know the variable $owner")
PY
# Each check records the hash of the evidence it saw, so the submitted copy can be compared with it.
sha=$(sha256sum -- "$lab2/evidence/paths.txt" | cut -d' ' -f1)
grep -q "\"sha256\": \"$sha\"" "$OSLAB_INBOX"/lab2.check.student-a.*.json
# A lab without milestones still records its evidence; dotfiles and links are left out.
printf 'normal run\n' > "$OSLAB_WORKSPACE/lab3/evidence-note.txt"
mkdir -p -- "$OSLAB_WORKSPACE/lab3/evidence"
printf 'kept\n' > "$OSLAB_WORKSPACE/lab3/evidence/links.txt"
printf 'hidden\n' > "$OSLAB_WORKSPACE/lab3/evidence/.hidden"
ln -s links.txt "$OSLAB_WORKSPACE/lab3/evidence/alias.txt"
"${tool[@]}" check lab3 >/dev/null
record=$(ls "$OSLAB_INBOX"/lab3.check.student-a.*.json)
grep -q '"path": "evidence/links.txt"' "$record"
grep -q '"path": "evidence-note.txt"' "$record"
if grep -q 'hidden\|alias' "$record"; then echo 'dotfile or link recorded' >&2; exit 1; fi
rm -- "$OSLAB_WORKSPACE/lab3/evidence-note.txt" "$OSLAB_WORKSPACE/lab3/evidence/alias.txt"
printf 'changed\n' > "$lab2/TechCorp/$owner/$file2"
"${tool[@]}" check lab2 | grep -q 'TRY : TechCorp'
"${tool[@]}" reset lab2
test -e "$OSLAB_WORKSPACE/lab2/incoming/$file1"
test -e "$OSLAB_WORKSPACE/.attempts"/lab2-*/my\ work.txt
printf 'unrelated\n' > "$OSLAB_WORKSPACE/unrelated.txt"
"${tool[@]}" clean lab2
test -e "$OSLAB_WORKSPACE/unrelated.txt"
test ! -e "$OSLAB_WORKSPACE/lab2"
# Lab 3: personal names, an older workspace, five milestones on real files, and the checkpoint chain.
lab3="$OSLAB_WORKSPACE/lab3"
name=$(value lab3 name); tag=$(value lab3 tag); v1=$(value lab3 v1); v2=$(value lab3 v2)
test -n "$name" && test -n "$tag" && test "$v2" -gt "$v1"
test "$(cat "$lab3/links/$name.txt")" = "version $v1"
test "$(ls -A "$lab3/notes" | wc -l)" = 5
test -e "$lab3/notes/.$name.txt"
test ! -e "$lab3/links/source.txt"
# A workspace from before the update holds the shared files: start removes them while they are unchanged and adds yours.
rm -rf -- "$lab3/links" "$lab3/notes" "$lab3/evidence"
mkdir -p -- "$lab3/links" "$lab3/evidence"
printf 'version 1\n' > "$lab3/links/source.txt"; printf 'A symlink target for diagnosis.\n' > "$lab3/links/target-name.txt"
"${tool[@]}" start lab3 | grep -q 'links/source.txt was an old shared file'
test ! -e "$lab3/links/source.txt" && test ! -e "$lab3/links/target-name.txt"
test "$(cat "$lab3/links/$name.txt")" = "version $v1"
test -e "$lab3/notes/$name.log"
printf 'my own edit\n' > "$lab3/links/source.txt"
"${tool[@]}" start lab3 | grep -q 'existing work preserved'
test "$(cat "$lab3/links/source.txt")" = 'my own edit'
rm -- "$lab3/links/source.txt"
"${tool[@]}" check lab3 | grep -q 'milestones: 0/5'
# Core 1 to 3 as a student types them. The middle wildcard command is the one the student writes.
(
  cd "$lab3"
  { printf '<%s>\n' notes/*.txt; printf '<%s>\n' notes/"$name"?.txt; printf '<%s>\n' 'notes/*.txt'; } | tee evidence/wildcards.txt >/dev/null
  cd links
  ln "$name.txt" "$name-hard.txt"
  ln -s "$name.txt" "$name-soft.txt"
  { printf '\n=== BEFORE RENAME ===\n'; ls -li "$name.txt" "$name-hard.txt" "$name-soft.txt"
    printf 'hard: '; cat "$name-hard.txt"; printf 'soft: '; cat "$name-soft.txt"; printf 'stored target: '; readlink "$name-soft.txt"; } > ../evidence/links.txt
  mv -- "$name.txt" "$name-$tag.txt"
  { printf '\n=== AFTER RENAME, BEFORE REPAIR ===\n'; printf 'hard: '; cat "$name-hard.txt"
    printf 'stored target: '; readlink "$name-soft.txt"; printf 'soft: '; cat "$name-soft.txt"; } >> ../evidence/links.txt 2>&1 || true  # cat fails: expected
  printf 'version %s\n' "$v2" > "$name.txt"
  { printf '\n=== NEW FILE USING THE OLD NAME ===\n'; printf 'hard: '; cat "$name-hard.txt"; printf 'soft: '; cat "$name-soft.txt"; } > ../evidence/replacement.txt 2>&1
)
grep -q 'No such file or directory' "$lab3/evidence/links.txt"
grep -q "^soft: version $v2\$" "$lab3/evidence/replacement.txt"
out=$("${tool[@]}" check lab3 || true)
printf '%s\n' "$out" | grep -q 'milestones: 3/5'
printf '%s\n' "$out" | grep -q 'it reads the NEW file'
printf '%s\n' "$out" | grep -q 'no `=== AFTER REPAIR'
# An absolute target is refused, a copy is not a hard link, a middle command with * instead of ? is named.
(cd "$lab3/links" && rm -- "$name-soft.txt" && ln -s "$lab3/links/$name-$tag.txt" "$name-soft.txt")
"${tool[@]}" check lab3 | grep -q 'is an absolute path'
(cd "$lab3/links" && rm -- "$name-soft.txt" && ln -s "$name-$tag.txt" "$name-soft.txt")
cp -- "$lab3/evidence/wildcards.txt" "$tmp/wildcards.keep"
{ printf '<%s>\n' "$lab3"/notes/*.txt | sed "s|$lab3/||"; printf '<%s>\n' "$lab3"/notes/"$name"*.txt | sed "s|$lab3/||"; printf '<notes/*.txt>\n'; } > "$lab3/evidence/wildcards.txt"
"${tool[@]}" check lab3 | grep -q "the lines for notes/$name?.txt must be"
cp -- "$tmp/wildcards.keep" "$lab3/evidence/wildcards.txt"
(cd "$lab3/links" && printf '\n=== AFTER REPAIR ===\n' >> ../evidence/links.txt && printf 'stored target: '  >> ../evidence/links.txt && readlink "$name-soft.txt" >> ../evidence/links.txt \
  && printf 'soft: ' >> ../evidence/links.txt && cat "$name-soft.txt" >> ../evidence/links.txt && printf 'Decision: relative, so it survives a move of the folder\n' >> ../evidence/links.txt)
"${tool[@]}" check lab3 | grep -q 'milestones: 5/5'
grep -q '"path_error": {"error": true, "fix": true}' "$(ls -t "$OSLAB_INBOX"/lab3.check.student-a.*.json | head -1)"
# A copy is not a hard link: equal bytes but another inode.
(cd "$lab3/links" && rm -- "$name-hard.txt" && cp -- "$name-$tag.txt" "$name-hard.txt")
"${tool[@]}" check lab3 | grep -q 'are not the same file'
(cd "$lab3/links" && rm -- "$name-hard.txt" && ln "$name-$tag.txt" "$name-hard.txt")
printf 'no\n%s\n%s\nit stores a name\n' "$v1" "$v2" | "${tool[@]}" predict lab3 | grep -q 'Saved and sent'
"${teach[@]}" release lab3
cpout=$(printf 'yes\nno\n../x.txt\nyes\nthe folder of the link\n' | "${tool[@]}" checkpoint lab3)
moved=$(printf '%s\n' "$cpout" | sed -n 's/^  mv [^ ]* \(.*\)$/\1/p')
build=$(printf '%s\n' "$cpout" | sed -n 's/^  \(cd .*\|mkdir .*\|printf .*\|ln .*\|mv .*\)$/\1/p')
saver=$(printf '%s\n' "$cpout" | sed -n 's/^  \({ ls .*\)$/\1/p')
test -n "$moved" && test -n "$saver"
"${tool[@]}" check lab3 | grep -q 'milestones: 5/6'
bash -c "$build"$'\n'"rm -- links/first.txt"$'\n'"ln -s ../$moved links/first.txt"$'\n'"$saver"
"${tool[@]}" check lab3 | grep -q 'milestones: 6/6'
printf 'no\n%s\n%s\n' "$v1" "$v2" | "${tool[@]}" debrief lab3 | grep -q 'Saved and sent'
"${teach[@]}" export lab3 | grep -q '^student-a,'
"${tool[@]}" hint lab3 3 | grep -q 'rm --'
# Lab 4: direct command evidence, migration, negative cases and a fresh checkpoint.
lab4="$OSLAB_WORKSPACE/lab4"
status=$(value lab4 status); other=$(value lab4 other)
test -n "$status" && test -n "$other" && test "$status" != "$other"
if "${tool[@]}" values lab4 | grep -q '^ *_'; then echo 'a hidden value was shown' >&2; exit 1; fi
test "$(cat "$lab4/data/expected.txt")" = 3
"${tool[@]}" check lab4 | grep -q 'milestones: 0/4'
printf 'status,count\nok,3\nfail,2\nok,5\n' > "$lab4/data/events.csv"
printf 'ok total: 8\n' > "$lab4/data/expected.txt"
"${tool[@]}" check lab4 | grep -q 'NOTE: data/events.csv is the old shared file'
"${tool[@]}" start lab4 | grep -q 'was the old shared file'
grep -q "^$status-late," "$lab4/data/events.csv"
test "$(cat "$lab4/data/expected.txt")" = 3
# Migrate only the generated personalized total; retain user edits and old scripts.
total=$(awk -F, -v s="$status" '$1 == s { t += $2 } END { print t }' "$lab4/data/events.csv")
printf '%s total: %s\n' "$status" "$total" > "$lab4/data/expected.txt"
printf 'old student work\n' > "$lab4/report.sh"
"${tool[@]}" start lab4 | grep -q 'migrated generated expected total'
test "$(cat "$lab4/report.sh")" = 'old student work'
printf 'my expected edit\n' > "$lab4/data/expected.txt"
"${tool[@]}" start lab4 >/dev/null
test "$(cat "$lab4/data/expected.txt")" = 'my expected edit'
mkdir -p "$lab4/evidence"
grep "^$status," "$lab4/data/events.csv" > "$lab4/evidence/selected.txt"
cut -d, -f2 "$lab4/evidence/selected.txt" > "$lab4/evidence/fields.txt"
wc -l < "$lab4/evidence/selected.txt" > "$lab4/evidence/normal.txt"
printf 'status,count\n%s,2\n' "$other" > "$lab4/data/no-match.csv"
cp "$lab4/data/events.csv" "$lab4/data/changed.csv"
printf '%s,7\n%s-late,99\n' "$status" "$status" >> "$lab4/data/changed.csv"
printf '0\n4\n' > "$lab4/evidence/edge.txt"
cat "$lab4/data/missing.csv" > "$lab4/evidence/stdout.txt" 2> "$lab4/evidence/stderr.txt" && code=0 || code=$?
printf '%s\n' "$code" > "$lab4/evidence/status.txt"
"${tool[@]}" check lab4 | grep -q 'milestones: 4/4'
printf '4\n' > "$lab4/evidence/edge.txt"
"${tool[@]}" check lab4 | grep -q 'milestones: 3/4'
printf '0\n4\n' > "$lab4/evidence/edge.txt"
printf '0\n' > "$lab4/evidence/status.txt"
"${tool[@]}" check lab4 | grep -q 'milestones: 3/4'
printf '%s\n' "$code" > "$lab4/evidence/status.txt"
printf '1\n9\n2\nI guessed\n' | "${tool[@]}" predict lab4 | grep -q 'Saved and sent'
"${teach[@]}" release lab4
cpout=$(printf '2\n1\n2\nit counts rows\n' | "${tool[@]}" checkpoint lab4)
(cd "$lab4" && eval "$(printf '%s\n' "$cpout" | sed -n 's/^  \(printf .*\)$/\1/p')")
cpname=$(printf '%s\n' "$cpout" | sed -n 's/^  printf .* > data\/\(.*\)$/\1/p')
grep "^$status," "$lab4/data/$cpname" > "$lab4/evidence/checkpoint-selected.txt"
wc -l < "$lab4/evidence/checkpoint-selected.txt" > "$lab4/checkpoint.txt"
"${tool[@]}" check lab4 | grep -q 'milestones: 5/5'
printf '3\n' > "$lab4/checkpoint.txt"
"${tool[@]}" check lab4 | grep -q 'milestones: 4/5'
printf '2\n' > "$lab4/checkpoint.txt"
"${teach[@]}" export lab4 | grep -q '^student-a,'
"${tool[@]}" hint lab4 3 | grep -q 'exactly your status'
# Lab 5: a program with personal numbers, a check that builds and runs it, and a checkpoint copy with new step counts.
lab5="$OSLAB_WORKSPACE/lab5"
ida=$(value lab5 id_a); idb=$(value lab5 id_b); sa=$(value lab5 steps_a); sb=$(value lab5 steps_b)
test -n "$ida" && test -n "$sb"
grep -q "struct job a = {$ida, $sa, 0}, b = {$idb, $sb, 0};" "$lab5/threads/two_workers.c"
# A workspace from before the update has no two_workers.c: start adds it, and check names numbers that are not yours.
rm -- "$lab5/threads/two_workers.c"
"${tool[@]}" start lab5 | grep -q 'added threads/two_workers.c'
grep -q "struct job a = {$ida, $sa, 0}, b = {$idb, $sb, 0};" "$lab5/threads/two_workers.c"
cp -- "$lab5/threads/two_workers.c" "$tmp/two_workers.keep"
sed -i 's/struct job a = {[0-9]*, [0-9]*, 0}, b = {[0-9]*, [0-9]*, 0};/struct job a = {2, 3, 0}, b = {3, 4, 0};/' "$lab5/threads/two_workers.c"
"${tool[@]}" check lab5 | grep -q 'NOTE: your program has the numbers a = {2, 3} and b = {3, 4}'
cp -- "$tmp/two_workers.keep" "$lab5/threads/two_workers.c"
"${tool[@]}" check lab5 | grep -q 'milestones: 1/4'
python3 - "$lab5/threads/two_workers.c" <<'PY'
import sys
path = sys.argv[1]
text = open(path).read()
text = text.replace("/* TODO: join both workers and check each return code. */",
                    "rc = pthread_join(ta, NULL); if (rc) return 1;\n    rc = pthread_join(tb, NULL); if (rc) return 1;")
text = text.replace("/* TODO: after both joins, print a.result and b.result. */",
                    'printf("A result=%d B result=%d\\n", a.result, b.result);')
open(path, "w").write(text)
PY
"${tool[@]}" check lab5 | grep -q 'milestones: 4/4'
test -z "$(ls -A "$lab5" | grep '^\.check-' || true)"
printf 'yes\n%s\n%s\nI guessed\n' 1 2 | "${tool[@]}" predict lab5 | grep -q 'Saved and sent'
printf 'no\n%s\n%s\n' "$((ida * sa))" "$((idb * sb))" | "${tool[@]}" debrief lab5 | grep -q 'Saved and sent'
"${teach[@]}" release lab5
cpout=$(printf 'no\n0\n3\nmain does not know if B finished\n' | "${tool[@]}" checkpoint lab5)
word=$(printf '%s\n' "$cpout" | sed -n 's/^  cp threads\/two_workers.c threads\/\(.*\)\.c$/\1/p')
csa=$(printf '%s\n' "$cpout" | sed -n 's/.*worker A \([0-9]*\) steps and worker B \([0-9]*\) steps.*/\1/p')
csb=$(printf '%s\n' "$cpout" | sed -n 's/.*worker A \([0-9]*\) steps and worker B \([0-9]*\) steps.*/\2/p')
test -n "$word" && test -n "$csa" && test -n "$csb"
cp -- "$lab5/threads/two_workers.c" "$lab5/threads/$word.c"
sed -i "s/struct job a = {$ida, $sa, 0}, b = {$idb, $sb, 0};/struct job a = {$ida, $csa, 0}, b = {$idb, $csb, 0};/" "$lab5/threads/$word.c"
(cd "$lab5" && gcc -Wall -Wextra -pthread "threads/$word.c" -o "threads/$word" && timeout 5 "threads/$word" > checkpoint.txt)
"${tool[@]}" check lab5 | grep -q 'milestones: 5/5'
"${teach[@]}" export lab5 | grep -q '^student-a,'
"${tool[@]}" hint lab5 2 | grep -q 'its own pthread_join'
# Lab 6: policy sentences become modes; the check reads modes, survives an unreadable folder, and marks the checkpoint folder.
lab6="$OSLAB_WORKSPACE/lab6"
policy_modes() {  # prints "file_mode dir_mode group_list" for a policy sentence
  case "$1" in
    "The owner may change the file."*) echo "640 750 y" ;;
    "Everyone may read the file"*) echo "644 711 n" ;;
    "The owner and the owner's group"*) echo "660 770 y" ;;
    "Only the owner may use"*) echo "600 700 n" ;;
    *) echo "unknown policy: $1" >&2; return 1 ;;
  esac
}
notice=$(value lab6 notice); box=$(value lab6 box)
read -r fm dm gl <<< "$(policy_modes "$notice")"
case "$box" in sealed-*) ;; *) echo 'bad box name' >&2; exit 1 ;; esac
if "${tool[@]}" values lab6 | grep -q '^ *_'; then echo 'a hidden value was shown' >&2; exit 1; fi
"${tool[@]}" check lab6 | grep -q 'milestones: 0/4'
chmod 700 "$lab6/private"; chmod 600 "$lab6/private/record.txt"
chmod "$dm" "$lab6/shared"; chmod "$fm" "$lab6/shared/notice.txt"
mkdir -p "$lab6/evidence"
(cd "$lab6" && stat -c '%A %a %U:%G %n' private private/record.txt shared shared/notice.txt > evidence/policy.txt \
  && printf 'owner update\n' >> private/record.txt \
  && mkdir -p "demo/$box" && printf 'inside\n' > "demo/$box/item.txt" && chmod 600 "demo/$box")
# While the demo folder has no search permission the check must still run (and not crash on it).
"${tool[@]}" check lab6 | grep -q 'milestones: 3/4'
(cd "$lab6" && { ls "demo/$box" | tee evidence/traversal.txt; cat "demo/$box/item.txt" 2>&1 | tee -a evidence/traversal.txt || true
  chmod 700 "demo/$box"; cat "demo/$box/item.txt" | tee -a evidence/traversal.txt; })
"${tool[@]}" check lab6 | grep -q 'milestones: 4/4'
# A wrong mode is named with the mode it has and the mode it needs.
chmod 644 "$lab6/private/record.txt"
"${tool[@]}" check lab6 | grep -q 'private/record.txt has mode 644 (-rw-r--r--) but a private record needs 600'
chmod 600 "$lab6/private/record.txt"
printf 'n\ny\n600\ny\nguess\n' | "${tool[@]}" predict lab6 | grep -q 'Saved and sent'
printf 'y\nn\n640\n%s\n' "$gl" | "${tool[@]}" debrief lab6 | grep -q 'Saved and sent'
"${teach[@]}" release lab6
cpout=$(printf '640\n750\ny\nit needs x\n' | "${tool[@]}" checkpoint lab6)
cpsentence=$(printf '%s\n' "$cpout" | sed -n 's/^    \(.*\)$/\1/p' | head -1)
read -r cfm cdm cgl <<< "$(policy_modes "$cpsentence")"
folder=$(printf '%s\n' "$cpout" | sed -n 's/^  mkdir \(.*\)$/\1/p')
test -n "$folder"
(cd "$lab6" && mkdir "$folder" && printf 'checkpoint text\n' > "$folder/data.txt" && chmod "$cfm" "$folder/data.txt" && chmod "$cdm" "$folder" \
  && stat -c '%A %a %n' "$folder" "$folder/data.txt" > checkpoint.txt)
"${tool[@]}" check lab6 | grep -q 'milestones: 5/5'
"${teach[@]}" export lab6 | grep -q '^student-a,'
"${tool[@]}" hint lab6 2 | grep -q 'Add read=4'
# Lab 7: personal awkward names, a check that runs the student's own script, and the ways a script can go wrong.
lab7="$OSLAB_WORKSPACE/lab7"
f1=$(value lab7 file1); f2=$(value lab7 file2)
test -f "$lab7/input/$f1" && test -f "$lab7/input/$f2"
case "$f1" in *" "*.txt) ;; *) echo 'file1 has no space' >&2; exit 1 ;; esac
case "$f2" in -*.txt) ;; *) echo 'file2 has no leading dash' >&2; exit 1 ;; esac
if "${tool[@]}" values lab7 | grep -q '^ *_'; then echo 'a hidden value was shown' >&2; exit 1; fi
test ! -e "$lab7/input/one file.txt"
"${tool[@]}" check lab7 | grep -q 'milestones: 0/4'
model="$script_dir/../teaching/instructor/lab7/count_words_solution.sh"
cp -- "$model" "$lab7/count_words.sh"; chmod 644 "$lab7/count_words.sh"
out=$("${tool[@]}" check lab7 || true)
printf '%s\n' "$out" | grep -q 'not executable by its owner'
chmod u+x "$lab7/count_words.sh"
"${tool[@]}" check lab7 | grep -q 'milestones: 4/4'
test -z "$(ls -A "$lab7" | grep '^\.check-' || true)"
printf '%s\n' '#!/usr/bin/env bash' 'for f in $@; do echo "$f: $(wc -w < "$f") words"; done' > "$lab7/count_words.sh"; chmod u+x "$lab7/count_words.sh"
"${tool[@]}" check lab7 | grep -q 'TRY : two files at once'
printf '%s\n' '#!/usr/bin/env bash' 'for f in "$@"; do echo "$f: $(wc -w "$f" | cut -d" " -f1) words"; done' > "$lab7/count_words.sh"
"${tool[@]}" check lab7 | grep -q 'TRY : run inside input/'
printf '%s\n' '#!/usr/bin/env bash' '[[ $# -gt 0 ]] || { echo usage >&2; exit 2; }' \
  'for f in "$@"; do if [[ -f "$f" ]]; then echo "$f: $(wc -w -- "$f" | cut -d" " -f1) words"; else echo "no $f" >&2; fi; done' > "$lab7/count_words.sh"
"${tool[@]}" check lab7 | grep -q 'TRY : no argument: usage on stderr'
cp -- "$model" "$lab7/count_words.sh"; chmod u+x "$lab7/count_words.sh"
pieces=$(printf '%s' "${f1%.txt}" | awk '{ print NF }')
printf '%s\nn\nn\nI guessed\n' "$pieces" | "${tool[@]}" predict lab7 | grep -q 'Saved and sent'
printf '%s\nn\nn\n' "$pieces" | "${tool[@]}" debrief lab7 | grep -q 'Saved and sent'
"${teach[@]}" release lab7
cpout=$(printf '2\n3\nn\nquotes keep the name together\n' | "${tool[@]}" checkpoint lab7)
(cd "$lab7" && eval "$(printf '%s\n' "$cpout" | sed -n -e 's/^  \(printf .*\)$/\1/p' -e 's/^  \(bash count_words.sh .*\)$/\1/p')")
"${tool[@]}" check lab7 | grep -q 'milestones: 5/5'
"${teach[@]}" export lab7 | grep -q '^student-a,'
"${tool[@]}" hint lab7 2 | grep -q 'Quote every expansion'
# Lab 9: personal lock names; the check starts the student's own two workers; a stale one-line worker is replaced.
lab9="$OSLAB_WORKSPACE/lab9"
r1=$(value lab9 res1); r2=$(value lab9 res2); af=$(value lab9 a_first)
test -n "$r1" && test -n "$r2" && test "$r1" != "$r2"
test -f "$lab9/vault/$r1.txt" && test -f "$lab9/vault/$r2.txt" && grep -q "^res1=$r1$" "$lab9/vault/worker.sh"
test ! -e "$lab9/vault/alpha.txt"
"${tool[@]}" check lab9 | grep -q 'milestones: 1/4'
# A workspace from before the update: the one-line worker and the two old data files are replaced.
printf '#!/usr/bin/env bash\nset -euo pipefail\n# TODO: acquire two owned lock files with flock -w 2; log each acquisition.\n' > "$lab9/vault/worker.sh"
printf 'alpha\n' > "$lab9/vault/alpha.txt"; printf 'beta\n' > "$lab9/vault/beta.txt"
"${tool[@]}" start lab9 | grep -q 'worker.sh was the old shared file'
grep -q "^res1=$r1$" "$lab9/vault/worker.sh"
test ! -e "$lab9/vault/alpha.txt" && test ! -e "$lab9/vault/beta.txt"
sed -i 's/if \[\[ "\$role" = B \]\]; then tmp/if [[ "$role" = B \&\& "$mode" = opposite ]]; then tmp/' "$lab9/vault/worker.sh"
mkdir -p "$lab9/evidence"
printf 'opposite A=5 B=0\nB holds both\nA second lock timeout\n' > "$lab9/evidence/opposite.txt"
printf 'ordered A=0 B=0\nA holds both\nB holds both\n' > "$lab9/evidence/ordered.txt"
"${tool[@]}" check lab9 | grep -q 'milestones: 4/4'
test -z "$(ls -A "$lab9" | grep '^\.check-' || true)"
printf 'n\n2\nn\nn\nthe timeout does not change the circle\n' | "${tool[@]}" predict lab9 | grep -q 'Saved and sent'
printf 'n\n2\nn\nn\n' | "${tool[@]}" debrief lab9 | grep -q 'Saved and sent'
"${teach[@]}" release lab9
cpout=$(printf 'y\nC\n0\nany total order works\n' | "${tool[@]}" checkpoint lab9)
cx=$(printf '%s\n' "$cpout" | sed -n 's/^    A holds \([a-z]*\) and requests .*$/\1/p')
cy=$(printf '%s\n' "$cpout" | sed -n 's/^    A holds [a-z]* and requests \([a-z]*\)$/\1/p')
test -n "$cx" && test -n "$cy"
(cd "$lab9" && cp vault/worker.sh vault/third.sh && sed -i "s/^res1=.*/res1=$cx/; s/^res2=.*/res2=$cy/" vault/third.sh \
  && { timeout 6 bash vault/third.sh A ordered > evidence/cp-a.txt 2>&1 & timeout 6 bash vault/third.sh B ordered > evidence/cp-b.txt 2>&1 & wait; } \
  && cat evidence/cp-a.txt evidence/cp-b.txt > checkpoint.txt)
"${tool[@]}" check lab9 | grep -q 'milestones: 5/5'
"${teach[@]}" export lab9 | grep -q '^student-a,'
"${tool[@]}" hint lab9 3 | grep -q 'opposite'
# Lab 10: personal archive name and number, a check that runs the student's own backup.sh in a disposable folder.
lab10="$OSLAB_WORKSPACE/lab10"
keep=$(value lab10 keep); nm=$(value lab10 name)
test -n "$keep" && test -n "$nm"
grep -q "^keep=$keep$" "$lab10/backup.sh" && grep -q "^name=$nm$" "$lab10/backup.sh"
"${tool[@]}" check lab10 | grep -q 'milestones: 2/4'
# A workspace from before the update holds the one-line starter script: it is replaced, not kept.
printf '#!/usr/bin/env bash\nset -euo pipefail\n# TODO: archive project with absolute paths, verify it, retain newest three owned archives.\n' > "$lab10/backup.sh"
"${tool[@]}" start lab10 | grep -q 'backup.sh was the old shared file'
grep -q "^keep=$keep$" "$lab10/backup.sh"
cat > "$tmp/retain.txt" <<'RETAIN'
shopt -s nullglob
owned=()
for path in "$work"/backups/"$name"-*.tar.gz; do
    base=${path##*/}
    if [[ -f "$path" && ! -L "$path" && "$base" =~ ^$name-[0-9]{8}T[0-9]{15}-[0-9]+\.tar\.gz$ ]]; then owned+=("$path"); fi
done
if (( ${#owned[@]} > keep )); then
    mapfile -t ordered < <(printf '%s\n' "${owned[@]}" | LC_ALL=C sort -r)
    for path in "${ordered[@]:$keep}"; do rm -- "$path"; done
fi
RETAIN
cp -- "$lab10/backup.sh" "$tmp/backup.skeleton"
splice_retention() {  # $1 = file with the retention lines, $2 = script to write
  awk -v snippet="$1" '/# TODO: retain only/ { while ((getline line < snippet) > 0) print line; next } { print }' "$tmp/backup.skeleton" > "$2"
}
# Wrong 1: a loose pattern also counts the look-alike file.
cat > "$tmp/loose.txt" <<'LOOSE'
shopt -s nullglob
owned=()
for path in "$work"/backups/"$name"-*.tar.gz; do
    if [[ -f "$path" ]]; then owned+=("$path"); fi
done
if (( ${#owned[@]} > keep )); then
    mapfile -t ordered < <(printf '%s\n' "${owned[@]}" | LC_ALL=C sort -r)
    for path in "${ordered[@]:$keep}"; do rm -- "$path"; done
fi
LOOSE
splice_retention "$tmp/loose.txt" "$lab10/backup.sh"
out=$("${tool[@]}" check lab10 || true)
printf '%s\n' "$out" | grep -q 'TRY : retention'
printf '%s\n' "$out" | grep -q 'does your pattern also match'
# Wrong 2: nothing is deleted. The test of files that are not yours must not pass for free.
cp -- "$tmp/backup.skeleton" "$lab10/backup.sh"
out=$("${tool[@]}" check lab10 || true)
printf '%s\n' "$out" | grep -q 'TRY : files that are not yours stay'
# The model retention.
splice_retention "$tmp/retain.txt" "$lab10/backup.sh"
"${tool[@]}" check lab10 | grep -q 'milestones: 4/4'
test -z "$(ls -A "$lab10" | grep '^\.check-' || true)"
printf 'n\n%s\nnewest\nn\nthe names have a time stamp\n' "$((keep))" | "${tool[@]}" predict lab10 | grep -q 'Saved and sent'
printf 'n\n%s\nnewest\nn\n' "$((keep))" | "${tool[@]}" debrief lab10 | grep -q 'Saved and sent'
"${teach[@]}" release lab10
cpout=$(printf '2\noldest\nn\nkeep is a variable\n' | "${tool[@]}" checkpoint lab10)
ckeep=$(printf '%s\n' "$cpout" | sed -n 's/.*to  keep=\([0-9]*\)$/\1/p')
truns=$(printf '%s\n' "$cpout" | sed -n 's/.*seq 1 \([0-9]*\)).*/\1/p')
test -n "$ckeep" && test -n "$truns" && test "$ckeep" != "$keep"
(cd "$lab10" && cp backup.sh backup-cp.sh && sed -i "s/^keep=.*/keep=$ckeep/" backup-cp.sh \
  && for i in $(seq 1 "$truns"); do bash backup-cp.sh > /dev/null; done && ls backups > checkpoint.txt)
"${tool[@]}" check lab10 | grep -q 'milestones: 5/5'
# Wrong 3: the old number is written into the logic of the copy; the checkpoint milestone must now fail.
sed -i "s/\${ordered\[@\]:\$keep}/\${ordered[@]:$keep}/; s/> keep ))/> $keep ))/" "$lab10/backup-cp.sh"
out=$("${tool[@]}" check lab10 || true)
printf '%s\n' "$out" | grep -q 'TRY : checkpoint'
"${teach[@]}" export lab10 | grep -q '^student-a,'
"${tool[@]}" hint lab10 2 | grep -q 'time stamp'
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
