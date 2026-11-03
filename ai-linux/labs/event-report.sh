#!/bin/bash
set -u
export LC_ALL=C
if [[ $# -ne 1 || ! -f $1 || ! -r $1 ]]; then
    printf 'usage: event-report.sh READABLE_FILE\n' >&2
    exit 2
fi
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) \
    || exit 1
input=$(realpath -e -- "$1") || exit 1
awk -f "$here/events.awk" -- "$input"
