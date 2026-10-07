#!/usr/bin/env bash
# Public model of the repaired student script: the fixture plus one lock around the whole transaction.
# Never use as a confidential graded answer.
set -euo pipefail
store=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ $# -ne 1 || ! "$1" =~ ^[1-9][0-9]{0,2}$ ]]; then
    echo 'usage: buy.sh QUANTITY (1..999)' >&2
    exit 2
fi
quantity=$1
exec 9>"$store/stock.lock"
flock -x -w 5 9 || { echo 'lock timeout' >&2; exit 3; }
stock=$(<"$store/stock.txt")
[[ "$stock" =~ ^(0|[1-9][0-9]{0,2})$ ]] || { echo 'invalid stock' >&2; exit 2; }
if (( quantity > stock )); then
    echo 'insufficient stock' >&2
    exit 1
fi
sleep "${BUY_DELAY:-0}"   # the payment takes time; keep this line
printf '%s\n' "$((stock - quantity))" > "$store/stock.txt"
printf 'sold %s\n' "$quantity" >> "$store/sales.log"
echo 'accepted'
