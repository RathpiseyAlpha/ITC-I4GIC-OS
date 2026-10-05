#!/usr/bin/env bash
# Public model for the simple two-field fixture, not general CSV parsing.
set -euo pipefail
[[ $# -eq 1 && -f "$1" && -r "$1" ]] || {
    echo 'usage: report_solution.sh READABLE_CSV' >&2; exit 2;
}
awk -F, '$1 == "ok" { total += $2 } END { print "ok total: " total+0 }' "$1"
