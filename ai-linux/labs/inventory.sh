#!/bin/bash
set -u
if [[ $# -ne 1 || ! -d $1 || ! -r $1 || ! -x $1 ]]; then
    printf 'usage: inventory.sh READABLE_DIRECTORY\n' >&2
    exit 2
fi
root=$1
shopt -s nullglob dotglob
paths=("$root"/*)
files=0
bytes=0
for path in "${paths[@]}"; do
    [[ -f $path && ! -L $path ]] || continue
    if size=$(wc -c < "$path"); then
        files=$((files + 1))
        bytes=$((bytes + size))
    else
        printf 'cannot read: %s\n' "$path" >&2
        exit 1
    fi
done
printf 'files=%d bytes=%d\n' "$files" "$bytes"
