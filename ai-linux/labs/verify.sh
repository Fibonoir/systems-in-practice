#!/bin/bash
# Acceptance checks. Creates and retains an isolated Linux fixture.
set -eu
export PATH=/usr/bin:/bin LC_ALL=C
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
LAB=$(bash "$here/setup.sh")
passed=0
ok() { passed=$((passed + 1)); printf 'PASS %02d %s\n' "$passed" "$1"; }
expect_status() {
    local expected=$1 actual
    shift
    if "$@" > "$LAB/run/test.out" 2> "$LAB/run/test.err"; then
        actual=0
    else
        actual=$?
    fi
    [[ $actual -eq $expected ]] || {
        printf 'FAIL status expected=%d actual=%d\n' \
            "$expected" "$actual" >&2
        cat "$LAB/run/test.err" >&2
        exit 1
    }
}
printf 'fixture=%s\n' "$LAB"
cat /etc/os-release
uname -r
bash --version | head -n 1
for command in find tar awk flock timeout realpath wc sha256sum mv; do
    command -v "$command"
    "$command" --version | head -n 1
done
for script in "$here"/*.sh; do bash -n "$script"; done
ok syntax
[[ $(bash "$here/inventory.sh" "$LAB/incoming") == 'files=4 bytes=19' ]]
ok inventory-normal
mkdir "$LAB/empty"
[[ $(bash "$here/inventory.sh" "$LAB/empty") == 'files=0 bytes=0' ]]
ok inventory-empty
expect_status 2 bash "$here/inventory.sh"
[[ ! -s $LAB/run/test.out && -s $LAB/run/test.err ]]
ok inventory-missing-argument
expect_status 2 bash "$here/inventory.sh" "$LAB/missing"
ok inventory-missing-directory
printf x > "$LAB/incoming/star*.txt"
[[ $(bash "$here/inventory.sh" "$LAB/incoming") == 'files=5 bytes=20' ]]
ok inventory-literal-glob
ln "$LAB/incoming/brief.txt" "$LAB/incoming/hard-copy"
[[ $(bash "$here/inventory.sh" "$LAB/incoming") == 'files=6 bytes=26' ]]
ok inventory-hardlink-names
printf x > "$LAB/incoming/line"$'\n'"break.txt"
bash "$here/manifest.sh" "$LAB/incoming" > "$LAB/run/names.nul"
count=0
while IFS= read -r -d '' path; do
    [[ -f $path && ! -L $path ]]
    count=$((count + 1))
done < "$LAB/run/names.nul"
[[ $count -eq 8 ]]
ok manifest-newline-and-nested
expect_status 2 bash "$here/manifest.sh" "$LAB/absent"
ok manifest-missing
expected='records=5 info=2 warn=1 errors=2 ms=90'
[[ $(bash "$here/event-report.sh" "$LAB/events/day.log") == "$expected" ]]
ok events-normal
: > "$LAB/events/empty.log"
[[ $(bash "$here/event-report.sh" "$LAB/events/empty.log") == 'records=0 info=0 warn=0 errors=0 ms=0' ]]
ok events-empty
printf '2026-10-01T09:00:00Z|INFO|import|12' > "$LAB/events/final.log"
[[ $(bash "$here/event-report.sh" "$LAB/events/final.log") == 'records=1 info=1 warn=0 errors=0 ms=12' ]]
ok events-unterminated
for record in \
    '2026-10-01T09:00:00Z|DEBUG|import|12' \
    '2026-10-01T09:00:00Z|INFO|import|012' \
    '2026-10-01T09:00:00Z|INFO|import|-1' \
    '2026-10-01T09:00:00Z|INFO|import|12|extra' \
    '2026-10-01T09:00:00Z|INFO||12' \
    'not-a-timestamp|INFO|import|12' \
    ''; do
    cp "$LAB/events/day.log" "$LAB/events/bad.log"
    printf '%s\n' "$record" >> "$LAB/events/bad.log"
    expect_status 2 bash "$here/event-report.sh" "$LAB/events/bad.log"
    [[ ! -s $LAB/run/test.out && -s $LAB/run/test.err ]]
    ok events-invalid-no-partial-output
done
printf 'old report\n' > "$LAB/reports/daily.txt"
expect_status 2 bash "$here/publish.sh" "$LAB/events/bad.log" "$LAB/reports"
[[ $(cat "$LAB/reports/daily.txt") == 'old report' ]]
ok publication-keeps-old-on-invalid
bash "$here/publish.sh" "$LAB/events/day.log" "$LAB/reports"
[[ $(cat "$LAB/reports/daily.txt") == "$expected" ]]
ok publication-replaces-valid
[[ -z $(find "$LAB/reports" -name '.daily.*' -print) ]]
ok publication-cleans-temp
mkdir "$LAB/reports/daily-dir"
mkdir "$LAB/blocked-report"
mkdir "$LAB/blocked-report/daily.txt"
expect_status 1 bash "$here/publish.sh" "$LAB/events/day.log" "$LAB/blocked-report"
[[ -d $LAB/blocked-report/daily.txt ]]
ok publication-refuses-directory-target
batch=$(bash "$here/snapshot.sh" "$LAB")
(cd "$batch" && sha256sum -c SHA256SUMS)
ok snapshot-checksum
mkdir "$LAB/restore"
tar -xf "$batch/data.tar" -C "$LAB/restore"
diff -r --no-dereference "$LAB/incoming" "$LAB/restore/incoming"
ok snapshot-restored-content-and-links
cp "$batch/data.tar" "$LAB/run/corrupt.tar"
printf damage >> "$LAB/run/corrupt.tar"
[[ $(sha256sum < "$batch/data.tar") != $(sha256sum < "$LAB/run/corrupt.tar") ]]
ok checksum-detects-change
expect_status 2 bash "$here/snapshot.sh" "$LAB/incoming"
ok snapshot-refuses-unmarked-root
: > "$LAB/incoming/discard.tmp"
printf keep > "$LAB/incoming/keep.tmp"
ln -s empty.txt "$LAB/incoming/link.tmp"
mkdir "$LAB/incoming/dir.tmp"
bash "$here/quarantine.sh" "$LAB" --preview > "$LAB/run/preview.txt"
[[ -f $LAB/incoming/discard.tmp ]]
grep -qx 'candidates=1' "$LAB/run/preview.txt"
ok quarantine-preview-no-change
bash "$here/quarantine.sh" "$LAB" --apply > "$LAB/run/applied.txt"
[[ ! -e $LAB/incoming/discard.tmp ]]
[[ -s $LAB/incoming/keep.tmp && -L $LAB/incoming/link.tmp && -d $LAB/incoming/dir.tmp ]]
[[ $(find "$LAB/quarantine" -type f -name discard.tmp | wc -l) -eq 1 ]]
ok quarantine-preserves-exclusions
bash "$here/quarantine.sh" "$LAB" --preview > "$LAB/run/preview-again.txt"
grep -qx 'candidates=0' "$LAB/run/preview-again.txt"
ok quarantine-repeat-zero
expect_status 2 bash "$here/quarantine.sh" "$LAB" --delete
ok quarantine-rejects-unknown-mode
bash "$here/daily.sh" "$LAB" > "$LAB/run/daily.out" 2> "$LAB/run/daily.err"
grep -qx 'daily job complete' "$LAB/run/daily.out"
ok daily-normal
exec 8> "$LAB/run/daily.lock"
flock -n 8
expect_status 75 bash "$here/daily.sh" "$LAB"
[[ ! -s $LAB/run/test.out ]]
ok daily-lock-conflict
flock -u 8
exec 8>&-
cp "$LAB/events/day.log" "$LAB/events/good.saved"
printf 'broken\n' >> "$LAB/events/day.log"
before=$(sha256sum < "$LAB/reports/daily.txt")
sets_before=$(find "$LAB/snapshots" -mindepth 1 -maxdepth 1 -type d | wc -l)
expect_status 2 bash "$here/daily.sh" "$LAB"
[[ $(sha256sum < "$LAB/reports/daily.txt") == "$before" ]]
[[ $(find "$LAB/snapshots" -mindepth 1 -maxdepth 1 -type d | wc -l) -eq $sets_before ]]
ok daily-stops-before-snapshot-on-bad-events
mv "$LAB/events/good.saved" "$LAB/events/day.log"
expect_status 124 timeout -k 1s 0.1s sleep 3
ok timeout-bounded
[[ $(bash "$here/inspect-config.sh" "$here/desk.conf") == $'label=morning-desk\nmax_files=200\ninclude_hidden=yes' ]]
ok configuration-valid
cp "$here/desk.conf" "$LAB/run/config.conf"
printf 'label=second\n' >> "$LAB/run/config.conf"
expect_status 2 bash "$here/inspect-config.sh" "$LAB/run/config.conf"
[[ ! -s $LAB/run/test.out ]]
ok configuration-duplicate-no-partial
for content in \
    $'label=desk\nmax_files=0200\ninclude_hidden=yes' \
    $'label=desk\nmax_files=200\ninclude_hidden=maybe' \
    $'label=desk\nmax_files=200\nunknown=yes' \
    $'label=\nmax_files=200\ninclude_hidden=yes'; do
    printf '%s\n' "$content" > "$LAB/run/config.conf"
    expect_status 2 bash "$here/inspect-config.sh" "$LAB/run/config.conf"
    [[ ! -s $LAB/run/test.out ]]
    ok configuration-invalid
done
printf 'label=$(touch %s)\nmax_files=200\ninclude_hidden=yes\n' \
    "$LAB/run/MUST_NOT_EXIST" > "$LAB/run/config.conf"
expect_status 2 bash "$here/inspect-config.sh" "$LAB/run/config.conf"
[[ ! -e $LAB/run/MUST_NOT_EXIST ]]
ok configuration-no-evaluation
printf 'label=desk\nmax_files=0\ninclude_hidden=no' > "$LAB/run/config.conf"
expect_status 0 bash "$here/inspect-config.sh" "$LAB/run/config.conf"
ok configuration-final-record-no-newline
printf secret > "$LAB/incoming/unreadable.txt"
chmod 000 "$LAB/incoming/unreadable.txt"
expect_status 1 bash "$here/inventory.sh" "$LAB/incoming"
[[ ! -s $LAB/run/test.out && -s $LAB/run/test.err ]]
chmod 600 "$LAB/incoming/unreadable.txt"
ok inventory-read-failure-no-summary
mkdir "$LAB/age-study"
: > "$LAB/age-study/equal"
: > "$LAB/run/cutoff"
touch -d '2026-10-01 12:00:00 UTC' "$LAB/run/cutoff"
touch -r "$LAB/run/cutoff" "$LAB/age-study/equal"
[[ $(find "$LAB/age-study" -type f ! -newer "$LAB/run/cutoff" -printf '%f') == equal ]]
ok age-equality-inclusive
printf 'ALL %d CHECKS PASSED\n' "$passed"
