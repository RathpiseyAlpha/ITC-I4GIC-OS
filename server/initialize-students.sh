#!/usr/bin/env bash
# Initialize only explicitly listed existing accounts. Default is dry-run.
set -euo pipefail
mode=dry-run
allowlist=
for arg in "$@"; do
  case "$arg" in
    --apply) mode=apply ;;
    --dry-run) mode=dry-run ;;
    --allowlist=*) allowlist=${arg#*=} ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done
[[ -n "$allowlist" && -f "$allowlist" && ! -L "$allowlist" ]] || { echo 'provide real --allowlist=file' >&2; exit 2; }
[[ "$mode" = dry-run || $EUID -eq 0 ]] || { echo 'apply requires root' >&2; exit 2; }
while IFS= read -r user || [[ -n "$user" ]]; do
  [[ -z "$user" || "$user" = \#* ]] && continue
  [[ "$user" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]] || { echo "invalid user: $user" >&2; exit 2; }
  entry=$(getent passwd "$user") || { echo "account missing: $user" >&2; exit 2; }
  uid=$(printf '%s' "$entry" | cut -d: -f3)
  [[ "$uid" =~ ^[0-9]+$ && "$uid" -ne 0 ]] || { echo "root account refused: $user" >&2; exit 2; }
  home_dir=$(printf '%s' "$entry" | cut -d: -f6)
  [[ -d "$home_dir" && ! -L "$home_dir" ]] || { echo "unsafe home for $user" >&2; exit 2; }
  printf '%s: home=%s mode=%s\n' "$user" "$home_dir" "$mode"
  if [[ "$mode" = apply ]]; then
    runuser -u "$user" -- /usr/local/bin/oslab doctor
    for n in {1..11}; do runuser -u "$user" -- /usr/local/bin/oslab start "lab$n"; done
  fi
done < "$allowlist"
