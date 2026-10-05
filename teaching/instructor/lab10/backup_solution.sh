#!/usr/bin/env bash
# Public sequential model; sources and destination are owned lab fixtures.
set -euo pipefail
work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mkdir -p "$work/backups"
stamp=$(date -u +%Y%m%dT%H%M%S%N)
final="$work/backups/backup-$stamp-$$.tar.gz"
pending=$(mktemp "$work/backups/.pending-XXXXXX")
trap 'rm -f -- "$pending"' EXIT
tar -czf "$pending" -C "$work" project
tar -tzf "$pending" >/dev/null
mv -- "$pending" "$final"

# Recognize only the script's timestamp/PID filenames, not every .tar.gz file.
shopt -s nullglob
owned=()
for path in "$work"/backups/backup-*.tar.gz; do
    name=${path##*/}
    if [[ -f "$path" && ! -L "$path" && "$name" =~ ^backup-[0-9]{8}T[0-9]{15}-[0-9]+\.tar\.gz$ ]]; then
        owned+=("$path")
    fi
done
if (( ${#owned[@]} > 3 )); then
    mapfile -t ordered < <(printf '%s\n' "${owned[@]}" | LC_ALL=C sort -r)
    for path in "${ordered[@]:3}"; do
        rm -- "$path"
    done
fi
printf 'created %s\n' "$final"
