#!/usr/bin/env bash
# Public demonstration only. A delay makes the stale-read race easier to see.
set -euo pipefail
[[ $# -eq 2 && "$2" =~ ^[1-9][0-9]*$ ]] || exit 2
store=$1
qty=$2
stock=$(<"$store/stock.txt")
(( qty <= stock )) || exit 1
sleep 1
printf '%s\n' "$((stock - qty))" > "$store/stock.txt"
printf 'sold %s\n' "$qty" >> "$store/sales.log"
