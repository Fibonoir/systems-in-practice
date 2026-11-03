#!/bin/bash
set -u
if [[ $# -ne 1 || ! -d $1 ]]; then
    printf 'usage: manifest.sh DIRECTORY\n' >&2
    exit 2
fi
# Resolve before passing the root to find.
root=$(realpath -e -- "$1") || exit 1
find -P "$root" -type f -print0
