#!/usr/bin/env bash
# Local administrator install. Defaults to a change-free dry run.
set -euo pipefail
mode=dry-run
prefix=/opt/itc-os-labs
allowlist=
for arg in "$@"; do
  case "$arg" in
    --apply) mode=apply ;;
    --dry-run) mode=dry-run ;;
    --prefix=*) prefix=${arg#*=} ;;
    --allowlist=*) allowlist=${arg#*=} ;;
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
if [[ -e /usr/local/bin/oslab ]] && ! grep -Fq -- '# ITC-OSLAB-MANAGED' /usr/local/bin/oslab; then
  echo 'existing oslab wrapper refused' >&2; exit 2
fi
if [[ -e /usr/local/bin/lab10-cron ]] && ! grep -Fq -- '# ITC-OSLAB-MANAGED' /usr/local/bin/lab10-cron; then
  echo 'existing lab10-cron wrapper refused' >&2; exit 2
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
  echo 'would install read-only oslab.py, lab10_cron.py and command wrappers; no accounts or workspaces changed'
  exit 0
fi
[[ $EUID -eq 0 ]] || { echo 'apply requires root' >&2; exit 2; }
if [[ -e /usr/local/bin/oslab && ! -f "$prefix/.itc-oslab-install" ]]; then
  echo 'existing /usr/local/bin/oslab refused' >&2; exit 2
fi
install -d -m 0755 -- "$prefix"
install -m 0644 -- "$script_dir/oslab.py" "$prefix/oslab.py"
install -m 0644 -- "$script_dir/lab10_cron.py" "$prefix/lab10_cron.py"
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
echo 'installed; no student workspace initialized'
