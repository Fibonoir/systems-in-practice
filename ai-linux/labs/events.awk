BEGIN { FS="[|]"; info=0; warn=0; errors=0; total=0; bad=0 }
{
    if (NF != 4 ||
        $1 !~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:/ ||
        $1 !~ /:[0-9]{2}:[0-9]{2}Z$/ ||
        length($1) != 20 ||
        $2 !~ /^(INFO|WARN|ERROR)$/ ||
        $3 !~ /^[a-z][a-z0-9_-]*$/ ||
        $4 !~ /^(0|[1-9][0-9]{0,5})$/) {
        printf "invalid record at line %d\n", NR \
            > "/dev/stderr"
        bad=1
        next
    }
    if ($2 == "INFO") info++
    if ($2 == "WARN") warn++
    if ($2 == "ERROR") errors++
    total += $4
}
END {
    if (bad) exit 2
    printf "records=%d info=%d warn=%d errors=%d ms=%d\n", \
        NR, info, warn, errors, total
}
