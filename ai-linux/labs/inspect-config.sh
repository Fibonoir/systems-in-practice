#!/bin/bash
# A strict data format, never shell source.
set -u
export LC_ALL=C
if [[ $# -ne 1 || ! -f $1 || ! -r $1 ]]; then
    printf 'usage: inspect-config.sh READABLE_FILE\n' >&2
    exit 2
fi
input=$1
declare -A seen values
number=0
fail() {
    printf 'invalid configuration at line %d: %s\n' \
        "$number" "$1" >&2
    exit 2
}
while IFS= read -r line || [[ -n $line ]]; do
    number=$((number + 1))
    [[ -z $line || $line == \#* ]] && continue
    [[ $line == *=* ]] || fail 'expected key=value'
    key=${line%%=*}
    value=${line#*=}
    case $key in
        label)
            pattern='^[a-z][a-z0-9_-]{0,31}$'
            [[ $value =~ $pattern ]] || fail 'label' ;;
        max_files)
            pattern='^(0|[1-9][0-9]{0,3})$'
            [[ $value =~ $pattern ]] || fail 'max_files' ;;
        include_hidden)
            [[ $value == yes || $value == no ]] \
                || fail 'include_hidden' ;;
        *) fail 'unknown key' ;;
    esac
    [[ ! ${seen[$key]+present} ]] || fail 'duplicate key'
    seen[$key]=1
    values[$key]=$value
done < "$input"
for key in label max_files include_hidden; do
    [[ ${seen[$key]+present} ]] || fail 'missing key'
done
printf 'label=%s\nmax_files=%s\ninclude_hidden=%s\n' \
    "${values[label]}" "${values[max_files]}" \
    "${values[include_hidden]}"
