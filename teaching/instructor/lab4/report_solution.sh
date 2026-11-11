#!/usr/bin/env bash
# Historical script-era reference for later scripting lessons; NOT a Lab 4 requirement or checker model.
# Retained to preserve earlier work; see plan.md for the current command-only model.
# Every student has a personal status word. Set it with STATUS=ready (default: ok).
set -euo pipefail
[[ $# -eq 1 && -f "$1" && -r "$1" ]] || {
    echo 'report_solution.sh: usage: report_solution.sh READABLE_CSV' >&2; exit 2;
}
awk -F, -v s="${STATUS:-ok}" '$1 == s { total += $2 } END { print s " total: " total+0 }' "$1"
