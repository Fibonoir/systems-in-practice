"""Small explicit operator helper. Run from the companion directory.

No deletion, no scheduling, no remote destination. Python 3.11+.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def compose(project, *args, **kwargs):
    return subprocess.run(['docker', 'compose', '-p', project, *args],
                          cwd=ROOT, check=True, **kwargs)


def rows(project):
    result = compose(project, 'exec', '-T', 'db', 'psql', '-U', 'shelf',
        '-d', 'shelf', '-At', '-c',
        'SELECT json_agg(t ORDER BY id) FROM (SELECT * FROM items) t',
        capture_output=True)
    return json.loads(result.stdout)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['backup', 'restore', 'rows'])
    p.add_argument('--project', required=True)
    p.add_argument('--file', type=Path)
    a = p.parse_args()
    if not a.project.startswith('shelf-'):
        p.error('use a distinct shelf- project name')
    if a.action == 'rows':
        print(json.dumps(rows(a.project), indent=2))
        return
    if a.file is None:
        p.error('--file is required')
    if a.action == 'backup':
        a.file.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidental overwrite of an older copy.
        with a.file.open('xb') as stream:
            compose(a.project, 'exec', '-T', 'db', 'pg_dump', '-U',
                    'shelf', '-d', 'shelf', '-Fc', stdout=stream)
        digest = hashlib.sha256(a.file.read_bytes()).hexdigest()
        a.file.with_suffix(a.file.suffix + '.sha256').write_text(digest + '\n')
        print('backup written; restoration still required:', a.file)
    else:
        sidecar = a.file.with_suffix(a.file.suffix + '.sha256')
        if hashlib.sha256(a.file.read_bytes()).hexdigest() != sidecar.read_text().strip():
            sys.exit('backup checksum mismatch')
        # A restore is allowed only into a database without public tables.
        count = compose(a.project, 'exec', '-T', 'db', 'psql', '-U',
            'shelf', '-d', 'shelf', '-At', '-c',
            "SELECT count(*) FROM pg_tables WHERE schemaname='public'",
            capture_output=True).stdout.strip()
        if count != b'0':
            sys.exit('restore target contains tables; choose a fresh project')
        with a.file.open('rb') as stream:
            compose(a.project, 'exec', '-T', 'db', 'pg_restore', '-U',
                'shelf', '-d', 'shelf', '--exit-on-error',
                '--single-transaction', '--no-owner', stdin=stream)
        print('archive restored; compare rows and exercise the application')


if __name__ == '__main__':
    main()
