#!/bin/bash
# One transient user timer; no persistent installation.
set -u
export PATH=/usr/bin:/bin LC_ALL=C
[[ $# -eq 1 ]] || exit 2
lab=$(realpath -e -- "$1") || exit 2
[[ -f $lab/.aala-lab ]] || exit 2
[[ $(cat -- "$lab/.aala-lab") == aala-v1 ]] || exit 2
[[ -d $lab/run && ! -L $lab/run ]] || exit 2
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) \
    || exit 1
unit="aala-demo-$$"
out="$lab/run/$unit.out"
err="$lab/run/$unit.err"
cleanup() {
    systemctl --user stop "$unit.timer" "$unit.service" \
        2>/dev/null || :
    systemctl --user reset-failed "$unit.service" \
        2>/dev/null || :
}
trap cleanup EXIT
systemctl --user show-environment > /dev/null || {
    printf 'user systemd manager unavailable\n' >&2
    exit 1
}
if systemd-run --user --unit="$unit" \
    --on-active=2s --timer-property=AccuracySec=100ms \
    --property="StandardOutput=append:$out" \
    --property="StandardError=append:$err" \
    /bin/bash "$here/daily.sh" "$lab"; then
    :
else
    exit 1
fi
for ((attempt=0; attempt<100; attempt++)); do
    if [[ -f $out ]] && \
        grep -qx 'daily job complete' "$out"; then
        printf 'timer completed: %s\n' "$unit"
        cat -- "$out"
        cat -- "$err" >&2
        exit 0
    fi
    sleep 0.2
done
printf 'timer did not complete; inspect %s\n' "$err" >&2
exit 1
