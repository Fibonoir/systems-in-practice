"""FreshRSS local stopped-writer data backup and fresh-project restore."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent


def run(*args, **kw):
    return subprocess.run(args, cwd=ROOT, check=True, **kw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['backup', 'restore'])
    p.add_argument('--project', required=True)
    p.add_argument('--file', required=True, type=Path)
    p.add_argument('--port', type=int, default=8092)
    a = p.parse_args()
    if not re.fullmatch(r'shelf-[a-z0-9-]+', a.project):
        p.error('project must be a lower-case shelf- name')
    if not 1024 <= a.port <= 65535:
        p.error('choose an unused local port 1024..65535')
    pins = dict(line.split('=', 1) for line in
                (ROOT/'images.env').read_text().splitlines() if '=' in line)
    image = pins['FRESHRSS_IMAGE']
    dc = ['docker', 'compose', '-p', a.project,
          '-f', 'compose.transfer.yaml']
    volume = a.project + '_reader_data'
    checksum = a.file.with_suffix(a.file.suffix + '.sha256')
    if a.action == 'backup':
        run(*dc, 'stop', 'reader')
        # Inspect first: docker run would otherwise create a missing volume.
        run('docker', 'volume', 'inspect', volume, stdout=subprocess.DEVNULL)
        a.file.parent.mkdir(parents=True, exist_ok=True)
        with a.file.open('xb') as stream:
            run('docker', 'run', '--rm', '--mount',
                'type=volume,src='+volume+',dst=/data,readonly',
                '--entrypoint', 'tar', image, '-C', '/data',
                '-cf', '-', '.', stdout=stream)
        checksum.write_text(hashlib.sha256(a.file.read_bytes()).hexdigest()+'\n')
        print('Data archived; source left stopped. Empty extensions excluded.')
    else:
        if hashlib.sha256(a.file.read_bytes()).hexdigest() != checksum.read_text().strip():
            p.error('checksum mismatch')
        existing = subprocess.run(['docker', 'volume', 'inspect', volume],
            capture_output=True, cwd=ROOT)
        if existing.returncode == 0:
            p.error('target volume already exists; choose a fresh project')
        # Also refuse existing target containers and the extensions volume.
        containers = run(*dc, 'ps', '-a', '-q', capture_output=True).stdout
        other = subprocess.run(['docker', 'volume', 'inspect',
            a.project+'_reader_extensions'], capture_output=True, cwd=ROOT)
        if containers.strip() or other.returncode == 0:
            p.error('target resources already exist; choose a fresh project')
        env = os.environ.copy()
        env['READER_PORT'] = str(a.port)
        run(*dc, 'create', env=env)
        with a.file.open('rb') as stream:
            run('docker', 'run', '--rm', '-i', '--mount',
                'type=volume,src='+volume+',dst=/data',
                '--entrypoint', 'tar', image, '-C', '/data',
                '-xf', '-', stdin=stream)
        run(*dc, 'up', '-d', env=env)
        print('Restored. Verify users, content, and target base URL before use.')


if __name__ == '__main__':
    main()
