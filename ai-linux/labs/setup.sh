#!/bin/bash
# Creates a new fixture; keeps existing directories.
set -u
umask 077
lab=$(mktemp -d "$HOME/aala-lab.XXXXXX") || exit 1
mkdir -p -- "$lab/incoming/nested" "$lab/events" \
    "$lab/reports" "$lab/snapshots" "$lab/quarantine" \
    "$lab/run" || exit 1
printf 'aala-v1\n' > "$lab/.aala-lab" || exit 1
printf 'alpha\n' > "$lab/incoming/brief.txt" || exit 1
printf 'needs review\n' > "$lab/incoming/draft notes.txt" \
    || exit 1
: > "$lab/incoming/empty.txt" || exit 1
: > "$lab/incoming/.keep" || exit 1
printf 'nested\n' > "$lab/incoming/nested/deep.txt" || exit 1
ln -s brief.txt "$lab/incoming/brief-link" || exit 1
printf '%s\n' \
    '2026-10-01T09:00:00Z|INFO|import|12' \
    '2026-10-01T09:01:00Z|ERROR|render|30' \
    '2026-10-01T09:02:00Z|WARN|import|18' \
    '2026-10-01T09:03:00Z|INFO|render|10' \
    '2026-10-01T09:04:00Z|ERROR|import|20' \
    > "$lab/events/day.log" || exit 1
printf '%s\n' "$lab"
