"""Real sockets and a separately running server, never fake inference."""
import asyncio
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx2
import jwt
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from benchdesk.auth_lab import ISSUER, provision
from benchdesk.store import Store


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@contextmanager
def service(tmp_path, authenticated=False):
    store = Store(tmp_path/'desk.sqlite')
    store.initialize()
    port = free_port()
    url = f'http://127.0.0.1:{port}/mcp'
    private = tmp_path/'private'
    if authenticated:
        provision(private, url)
        command = ['-m', 'benchdesk.auth_lab', 'serve',
                   '--private-dir', str(private), '--db',
                   str(store.path), '--port', str(port)]
    else:
        command = ['-m', 'benchdesk.server', '--http',
                   '--db', str(store.path), '--port', str(port)]
    with (tmp_path/'server.log').open('w') as log:
        proc = subprocess.Popen([sys.executable, *command],
            cwd=Path(__file__).resolve().parents[1],
            stdout=log, stderr=log,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic()+15
            while True:
                if proc.poll() is not None:
                    raise RuntimeError('server exited: '+
                        (tmp_path/'server.log').read_text())
                try:
                    with socket.create_connection(
                            ('127.0.0.1', port), timeout=.2):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        raise TimeoutError('server did not listen')
                    time.sleep(.05)
            yield store, url, private
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def test_real_http(tmp_path):
    with service(tmp_path) as (store, url, _):
        async def run():
            async with Client(url, mode='2026-07-28') as client:
                assert client.protocol_version == '2026-07-28'
                result = await client.call_tool('get_ticket',
                                                 {'ticket_id': 101})
                assert result.structured_content['id'] == 101
            async with httpx2.AsyncClient() as http:
                bad = await http.post(url,
                    headers={'Origin': 'https://attacker.invalid'},
                    json={'jsonrpc': '2.0', 'id': 1,
                          'method': 'server/discover'})
                assert bad.status_code in {400, 403, 421}
        asyncio.run(run())
    # The exact lab-owned process has stopped. A new call must fail.
    async def stopped():
        try:
            async with Client(url, read_timeout_seconds=.5):
                raise AssertionError('stopped server connected')
        except (AssertionError, KeyboardInterrupt):
            raise
        except Exception:
            return
        raise AssertionError('expected transport failure')
    asyncio.run(stopped())


def test_auth_scopes_and_approval(tmp_path):
    with service(tmp_path, True) as (store, url, private):
        async def run():
            async with httpx2.AsyncClient() as http:
                missing = await http.post(url, json={})
                invalid = await http.post(url, json={},
                    headers={'Authorization': 'Bearer invalid'})
                assert missing.status_code == 401
                assert invalid.status_code == 401
                assert 'resource_metadata' in missing.headers[
                    'www-authenticate']
            for role in ('reader', 'writer'):
                token = (private/f'{role}.token').read_text()
                async with httpx2.AsyncClient(headers={
                    'Authorization': f'Bearer {token}'}) as http:
                    transport = streamable_http_client(
                        url, http_client=http)
                    async with Client(transport) as client:
                        good = await client.call_tool('get_ticket',
                            {'ticket_id': 101})
                        assert not good.is_error
                        proposed = await client.call_tool(
                            'propose_status_change',
                            {'ticket_id': 101,
                             'new_status': 'inspecting',
                             'expected_version': 1})
                        if role == 'reader':
                            assert proposed.is_error
                            continue
                        assert not proposed.is_error
                        pid = json.loads(
                            proposed.content[0].text)['proposal_id']
                        args = {'proposal_id': pid,
                                'operation_key': 'authlab_0001'}
                        denied = await client.call_tool(
                            'commit_status_change', args)
                        assert denied.is_error
                        store.approve(pid)
                        result = await client.call_tool(
                            'commit_status_change', args)
                        assert not result.is_error
                        assert len(store.audit()) == 1
        asyncio.run(run())


def test_token_validation(tmp_path):
    from benchdesk.auth_lab import LabVerifier
    key = b'x'*32
    audience = 'http://127.0.0.1:8766/mcp'
    now = int(time.time())
    valid = {'iss': ISSUER, 'aud': audience, 'sub': 'reader',
             'scope': 'tickets:read', 'iat': now, 'exp': now+60}
    async def run():
        verifier = LabVerifier(key, audience)
        assert await verifier.verify_token(jwt.encode(
            valid, key, algorithm='HS256')) is not None
        for changes in [{'aud': 'https://other.invalid'},
                        {'iss': 'https://other.invalid'},
                        {'exp': now-1}, {'sub': 'unknown'},
                        {'scope': 'admin'}]:
            token = jwt.encode({**valid, **changes}, key,
                               algorithm='HS256')
            assert await verifier.verify_token(token) is None
    asyncio.run(run())
