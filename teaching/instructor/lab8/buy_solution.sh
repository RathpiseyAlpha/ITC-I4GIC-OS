#!/usr/bin/env bash
# Public model: never use as a confidential graded answer.
set -euo pipefail
[[ $# -eq 2 ]] || { echo 'usage: buy_solution.sh STORE POSITIVE_QUANTITY' >&2; exit 2; }
store=$1
qty=$2
[[ -d "$store" && "$qty" =~ ^[1-9][0-9]*$ ]] || { echo 'invalid input' >&2; exit 2; }
exec 9>"$store/stock.lock"
flock -x -w 2 9 || { echo 'lock timeout' >&2; exit 3; }
stock=$(<"$store/stock.txt")
[[ "$stock" =~ ^[0-9]+$ ]] || { echo 'invalid stock' >&2; exit 2; }
if (( qty > stock )); then echo 'sold out' >&2; exit 1; fi
printf '%s\n' "$((stock - qty))" > "$store/stock.txt"
printf 'sold %s\n' "$qty" >> "$store/sales.log"
echo 'accepted'
