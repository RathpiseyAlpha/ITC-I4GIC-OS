#!/usr/bin/env bash
# Public model: preserve boundaries and aggregate failures.
set -u
[[ $# -gt 0 ]] || { echo 'usage: count_words_solution.sh FILE...' >&2; exit 2; }
status=0
for file in "$@"; do
    if [[ ! -f "$file" || ! -r "$file" ]]; then
        printf 'unreadable file: %s\n' "$file" >&2
        status=1
        continue
    fi
    if count=$(wc -w -- "$file"); then
        # wc prefixes the count, followed by the operand; print our own label.
        read -r words _ <<< "$count"
        printf '%s: %s words\n' "$file" "$words"
    else
        status=1
    fi
done
exit "$status"
