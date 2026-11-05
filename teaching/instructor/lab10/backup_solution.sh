#!/usr/bin/env bash
# Public sequential model. The values below are examples: a student's script has their own keep= and name= lines.
set -euo pipefail
keep=3
name=daily
work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mkdir -p "$work/backups"
stamp=$(date -u +%Y%m%dT%H%M%S%N)
final="$work/backups/$name-$stamp-$$.tar.gz"
pending=$(mktemp "$work/backups/.pending-XXXXXX")
trap 'rm -f -- "$pending"' EXIT
tar -czf "$pending" -C "$work" project
tar -tzf "$pending" >/dev/null
mv -- "$pending" "$final"

# Recognize only the script's own names (NAME-STAMP-PID.tar.gz), not every .tar.gz file.
shopt -s nullglob
owned=()
for path in "$work"/backups/"$name"-*.tar.gz; do
    file=${path##*/}
    if [[ -f "$path" && ! -L "$path" && "$file" =~ ^${name}-[0-9]{8}T[0-9]{15}-[0-9]+\.tar\.gz$ ]]; then
        owned+=("$path")
    fi
done
if (( ${#owned[@]} > keep )); then
    mapfile -t ordered < <(printf '%s\n' "${owned[@]}" | LC_ALL=C sort -r)
    for path in "${ordered[@]:keep}"; do
        rm -- "$path"
    done
fi
printf 'created %s\n' "$final"
