#!/bin/bash
set -u
umask 077
if [[ $# -ne 2 || ! -d $2 || -L $2 ]]; then
    printf 'usage: publish.sh INPUT REPORT_DIRECTORY\n' >&2
    exit 2
fi
input=$1
out=$(realpath -e -- "$2") || exit 1
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) \
    || exit 1
tmp=$(mktemp "$out/.daily.XXXXXX") || exit 1
cleanup() { rm -f -- "$tmp"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if bash "$here/event-report.sh" "$input" > "$tmp"; then
    if mv -fT -- "$tmp" "$out/daily.txt"; then
        printf 'published daily.txt\n'
    else
        printf 'publication failed\n' >&2
        exit 1
    fi
else
    status=$?
    printf 'report rejected; previous file kept\n' >&2
    exit "$status"
fi
