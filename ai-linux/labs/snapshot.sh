#!/bin/bash
set -u
umask 077
if [[ $# -ne 1 || ! -f $1/.aala-lab || -L $1 ]]; then
    printf 'usage: snapshot.sh LAB_DIRECTORY\n' >&2
    exit 2
fi
lab=$(realpath -e -- "$1") || exit 1
[[ $(cat -- "$lab/.aala-lab") == aala-v1 ]] || exit 2
[[ -d $lab/incoming && ! -L $lab/incoming ]] || exit 2
[[ -d $lab/snapshots && ! -L $lab/snapshots ]] || exit 2
batch=$(mktemp -d "$lab/snapshots/set.XXXXXX") || exit 1
if tar -cf "$batch/data.tar" -C "$lab" -- incoming; then
    if (cd -- "$batch" &&
        sha256sum data.tar > SHA256SUMS); then
        printf '%s\n' "$batch"
    else
        printf 'checksum failed: %s\n' "$batch" >&2
        exit 1
    fi
else
    printf 'incomplete snapshot: %s\n' "$batch" >&2
    exit 1
fi
