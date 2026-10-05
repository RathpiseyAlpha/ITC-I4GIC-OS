#!/usr/bin/env bash
# Two owned workers only. Use timeout 6 externally for an additional bound.
set -euo pipefail
[[ $# -eq 3 && "$2" =~ ^(A|B)$ && "$3" =~ ^(opposite|ordered)$ ]] || {
  echo 'usage: worker_solution.sh VAULT A|B opposite|ordered' >&2; exit 2;
}
vault=$1
role=$2
mode=$3
[[ -d "$vault" && ! -L "$vault" ]] || exit 2
mkdir -p "$vault/coord"
first=alpha
second=beta
if [[ "$mode" = opposite && "$role" = B ]]; then first=beta; second=alpha; fi
exec 8>"$vault/$first.lock"
flock -x -w 2 8 || exit 3
printf '%s holds %s\n' "$role" "$first"
if [[ "$mode" = opposite ]]; then
  touch "$vault/coord/$role.ready"
  # A controlled barrier makes both first acquisitions observable. Bound the wait.
  other=B
  [[ "$role" = B ]] && other=A
  for i in {1..30}; do
    [[ -f "$vault/coord/$other.ready" ]] && break
    sleep 0.1
  done
  [[ -f "$vault/coord/$other.ready" ]] || { echo 'barrier timeout' >&2; exit 4; }
fi
exec 9>"$vault/$second.lock"
flock -x -w 2 9 || { echo "$role second lock timeout" >&2; exit 5; }
printf '%s holds both\n' "$role"
