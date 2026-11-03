#!/bin/bash
set -u
umask 077
export PATH=/usr/bin:/bin LC_ALL=C
if [[ $# -ne 1 || ! -d $1 || -L $1 ]]; then
    printf 'usage: daily.sh LAB_DIRECTORY\n' >&2
    exit 2
fi
lab=$(realpath -e -- "$1") || exit 2
[[ -f $lab/.aala-lab && ! -L $lab/.aala-lab ]] || exit 2
[[ $(cat -- "$lab/.aala-lab") == aala-v1 ]] || exit 2
for dir in incoming events reports snapshots run; do
    [[ -d $lab/$dir && ! -L $lab/$dir ]] || exit 2
done
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) \
    || exit 1
exec 9> "$lab/run/daily.lock" || exit 1
if flock -n -E 75 9; then
    :
else
    status=$?
    printf 'lock unavailable: status=%d\n' "$status" >&2
    exit "$status"
fi
log() { printf '%s\n' "$*" >&2; }
log 'stage=inventory'
if inventory=$(timeout -k 2s 10s \
    bash "$here/inventory.sh" "$lab/incoming"); then
    log "$inventory"
else
    status=$?; log "inventory failed: $status"; exit "$status"
fi
log 'stage=report'
if timeout -k 2s 10s bash "$here/publish.sh" \
    "$lab/events/day.log" "$lab/reports"; then
    :
else
    status=$?; log "report failed: $status"; exit "$status"
fi
log 'stage=snapshot'
if snapshot=$(timeout -k 2s 10s \
    bash "$here/snapshot.sh" "$lab"); then
    log "snapshot=$snapshot"
else
    status=$?; log "snapshot failed: $status"; exit "$status"
fi
printf 'daily job complete\n'
