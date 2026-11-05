#!/usr/bin/env bash
# Public model for the simple two-field fixture, not general CSV parsing.
# Every student has a personal status word. Set it with STATUS=ready (default: ok).
set -euo pipefail
[[ $# -eq 1 && -f "$1" && -r "$1" ]] || {
    echo 'report_solution.sh: usage: report_solution.sh READABLE_CSV' >&2; exit 2;
}
awk -F, -v s="${STATUS:-ok}" '$1 == s { total += $2 } END { print s " total: " total+0 }' "$1"
