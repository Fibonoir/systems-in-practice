#!/bin/bash
set -u
umask 077
if [[ $# -ne 2 ]]; then
    printf 'usage: quarantine.sh LAB --preview|--apply\n' >&2
    exit 2
fi
case $2 in
    --preview|--apply) mode=$2 ;;
    *) printf 'unknown mode\n' >&2; exit 2 ;;
esac
lab=$(realpath -e -- "$1") || exit 2
[[ -f $lab/.aala-lab && ! -L $lab/.aala-lab ]] || exit 2
[[ $(cat -- "$lab/.aala-lab") == aala-v1 ]] || exit 2
for dir in incoming quarantine run; do
    [[ -d $lab/$dir && ! -L $lab/$dir ]] || exit 2
done
plan=$(mktemp "$lab/run/plan.XXXXXX") || exit 1
trap 'rm -f -- "$plan"' EXIT
if ! find -P "$lab/incoming" -maxdepth 1 -type f \
    -name '*.tmp' -size 0c -print0 > "$plan"; then
    exit 1
fi
batch=
if [[ $mode == --apply ]]; then
    batch=$(mktemp -d "$lab/quarantine/batch.XXXXXX") \
        || exit 1
fi
count=0
while IFS= read -r -d '' path; do
    printf '%s %q\n' "$mode" "$path"
    if [[ $mode == --apply ]]; then
        if [[ ! -f $path || -L $path || -s $path ]]; then
            printf 'candidate changed; stopped\n' >&2
            exit 1
        fi
        name=${path##*/}
        [[ ! -e $batch/$name && ! -L $batch/$name ]] \
            || exit 1
        mv -T -- "$path" "$batch/$name" || exit 1
    fi
    count=$((count + 1))
done < "$plan"
printf 'candidates=%d\n' "$count"
[[ -z $batch ]] || printf 'batch=%s\n' "$batch"
