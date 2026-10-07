#!/usr/bin/env bash
# Local administrator install. Defaults to a change-free dry run.
set -euo pipefail
mode=dry-run
prefix=/opt/itc-os-labs
allowlist=
term=
reader=
state=/var/lib/itc-oslab
for arg in "$@"; do
  case "$arg" in
    --apply) mode=apply ;;
    --dry-run) mode=dry-run ;;
    --prefix=*) prefix=${arg#*=} ;;
    --allowlist=*) allowlist=${arg#*=} ;;
    --term=*) term=${arg#*=} ;;
    --inbox-reader=*) reader=${arg#*=} ;;
    *) printf 'unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done
[[ "$prefix" = /opt/* && "$prefix" != *'/../'* && "$prefix" != *'/./'* && "$prefix" != */.. && "$prefix" != */. ]] || { echo 'prefix must be a clean path below /opt' >&2; exit 2; }
[[ ! -L "$prefix" ]] || { echo 'symlink prefix refused' >&2; exit 2; }
[[ ! -L /opt ]] || { echo 'symlink /opt refused' >&2; exit 2; }
part_path=/opt
IFS=/ read -r -a path_parts <<< "${prefix#/opt/}"
for part in "${path_parts[@]}"; do
  [[ -n "$part" ]] || { echo 'empty prefix component' >&2; exit 2; }
  part_path="$part_path/$part"
  [[ ! -L "$part_path" ]] || { echo 'symlink in prefix path refused' >&2; exit 2; }
done
if [[ -e "$prefix" && ! -f "$prefix/.itc-oslab-install" ]]; then
  echo 'unmanaged install directory refused' >&2; exit 2
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
[[ -f "$script_dir/oslab.py" ]] || { echo 'oslab.py missing' >&2; exit 2; }
[[ -f "$script_dir/lab10_cron.py" ]] || { echo 'lab10_cron.py missing' >&2; exit 2; }
[[ -f "$script_dir/oslab_teach.py" ]] || { echo 'oslab_teach.py missing' >&2; exit 2; }
[[ -z "$term" || "$term" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || { echo 'term must be 1-64 letters, digits, dot, dash or underscore' >&2; exit 2; }
# The account that runs the course website may list the inbox, so the instructor can mark from the dashboard.
# The name is remembered, so a later install without the option keeps the access.
if [[ -z "$reader" && -f "$prefix/inbox-reader" && ! -L "$prefix/inbox-reader" ]]; then
  IFS= read -r reader < "$prefix/inbox-reader" || true
fi
if [[ -n "$reader" ]]; then
  [[ "$reader" =~ ^[a-z_][a-z0-9_-]*$ ]] || { echo 'invalid inbox reader name' >&2; exit 2; }
  reader_uid=$(id -u -- "$reader" 2>/dev/null) || { echo "inbox reader account missing: $reader" >&2; exit 2; }
  [[ "$reader_uid" -ne 0 ]] || { echo 'root needs no inbox reader entry' >&2; exit 2; }
  command -v setfacl >/dev/null || { echo 'setfacl missing: install the acl package' >&2; exit 2; }
fi
[[ ! -L "$state" && ! -L "$state/inbox" && ! -L "$state/release" ]] || { echo 'symlink in state path refused' >&2; exit 2; }
if [[ -e /usr/local/bin/oslab ]] && ! grep -Fq -- '# ITC-OSLAB-MANAGED' /usr/local/bin/oslab; then
  echo 'existing oslab wrapper refused' >&2; exit 2
fi
if [[ -e /usr/local/bin/lab10-cron ]] && ! grep -Fq -- '# ITC-OSLAB-MANAGED' /usr/local/bin/lab10-cron; then
  echo 'existing lab10-cron wrapper refused' >&2; exit 2
fi
if [[ -e /usr/local/bin/oslab-teach ]] && ! grep -Fq -- '# ITC-OSLAB-MANAGED' /usr/local/bin/oslab-teach; then
  echo 'existing oslab-teach wrapper refused' >&2; exit 2
fi
if [[ -n "$allowlist" ]]; then
  [[ -f "$allowlist" && ! -L "$allowlist" ]] || { echo 'allowlist must be a real file' >&2; exit 2; }
  while IFS= read -r user || [[ -n "$user" ]]; do
    [[ -z "$user" || "$user" = \#* ]] && continue
    [[ "$user" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]] || { echo 'invalid username in allowlist' >&2; exit 2; }
    entry=$(getent passwd "$user") || { echo "account missing: $user" >&2; exit 2; }
    uid=$(printf '%s' "$entry" | cut -d: -f3)
    [[ "$uid" =~ ^[0-9]+$ && "$uid" -ne 0 ]] || { echo "root account refused: $user" >&2; exit 2; }
  done < "$allowlist"
fi
printf 'mode=%s prefix=%s source=%s\n' "$mode" "$prefix" "$script_dir/oslab.py"
if [[ "$mode" = dry-run ]]; then
  echo 'would install read-only oslab.py, lab10_cron.py, oslab_teach.py and command wrappers; no accounts or workspaces changed'
  printf 'would create %s/inbox (mode 1733, students drop answers) and %s/release (mode 0755)\n' "$state" "$state"
  [[ -z "$reader" ]] || printf 'would let account %s list the inbox (read only)\n' "$reader"
  if [[ -f "$prefix/term.conf" ]]; then echo 'would keep the existing term.conf (personal values stay the same)'
  else printf 'would create term.conf with term name: %s\n' "${term:-term-$(date +%Y)}"; fi
  exit 0
fi
[[ $EUID -eq 0 ]] || { echo 'apply requires root' >&2; exit 2; }
if [[ -e /usr/local/bin/oslab && ! -f "$prefix/.itc-oslab-install" ]]; then
  echo 'existing /usr/local/bin/oslab refused' >&2; exit 2
fi
install -d -m 0755 -- "$prefix"
install -m 0644 -- "$script_dir/oslab.py" "$prefix/oslab.py"
install -m 0644 -- "$script_dir/lab10_cron.py" "$prefix/lab10_cron.py"
install -m 0644 -- "$script_dir/oslab_teach.py" "$prefix/oslab_teach.py"
# The term name seeds every student's personal values. Never replace it during a term.
if [[ ! -f "$prefix/term.conf" ]]; then
  printf '%s\n' "${term:-term-$(date +%Y)}" > "$prefix/term.conf"
  chmod 0644 "$prefix/term.conf"
elif [[ -n "$term" ]]; then
  echo 'term.conf already exists and was kept; edit it by hand only before a new term starts' >&2
fi
# Students may add files to the inbox but cannot list it or remove each other's files.
install -d -m 0755 -o root -g root -- "$state" "$state/release"
install -d -m 1733 -o root -g root -- "$state/inbox"
setfacl -b -- "$state/inbox" 2>/dev/null || true
if [[ -n "$reader" ]]; then
  setfacl -m "u:$reader:r-x" -- "$state/inbox"
  printf '%s\n' "$reader" > "$prefix/inbox-reader"
  chmod 0644 "$prefix/inbox-reader"
fi
printf 'ITC OS labs managed install v1\n' > "$prefix/.itc-oslab-install"
chmod 0644 "$prefix/.itc-oslab-install"
wrapper=$(mktemp)
printf '#!/usr/bin/env bash\n# ITC-OSLAB-MANAGED\nexec python3 %q "$@"\n' "$prefix/oslab.py" > "$wrapper"
install -m 0755 -- "$wrapper" /usr/local/bin/oslab
rm -f -- "$wrapper"
wrapper=$(mktemp)
printf '#!/usr/bin/env bash\n# ITC-OSLAB-MANAGED\nexec python3 %q "$@"\n' "$prefix/lab10_cron.py" > "$wrapper"
install -m 0755 -- "$wrapper" /usr/local/bin/lab10-cron
rm -f -- "$wrapper"
wrapper=$(mktemp)
printf '#!/usr/bin/env bash\n# ITC-OSLAB-MANAGED\nexec python3 %q "$@"\n' "$prefix/oslab_teach.py" > "$wrapper"
install -m 0755 -- "$wrapper" /usr/local/bin/oslab-teach
rm -f -- "$wrapper"
echo 'installed; no student workspace initialized'
