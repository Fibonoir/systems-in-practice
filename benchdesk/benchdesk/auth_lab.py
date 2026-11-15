"""Loopback bearer-verification lab, NOT an OAuth authorization server.

Tokens are pre-provisioned by a local operator; no network token endpoint,
login flow, refresh, discovery of an actual issuer, or key distribution.
Use an established OAuth deployment for remote service.
"""
import argparse
import json
from pathlib import Path
import secrets
import time
import jwt
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from .server import make_server
from .store import Store

ISSUER = 'https://issuer.invalid/benchdesk-lab'


class LabVerifier:
    def __init__(self, key, audience):
        self.key, self.audience = key, audience

    async def verify_token(self, token):
        try:
            claims = jwt.decode(
                token, self.key, algorithms=['HS256'],
                audience=self.audience, issuer=ISSUER,
                options={'require': ['exp', 'iat', 'iss',
                                     'aud', 'sub', 'scope']})
            if claims['sub'] not in {'reader', 'writer'}:
                return None
            if not isinstance(claims['scope'], str):
                return None
            scopes = claims['scope'].split()
            if not set(scopes) <= {'tickets:read', 'tickets:write'}:
                return None
            return AccessToken(
                token=token, client_id='benchdesk-local-lab',
                scopes=scopes, subject=claims['sub'],
                expires_at=claims['exp'], resource=self.audience,
                claims={'iss': ISSUER})
        except (jwt.InvalidTokenError, TypeError, ValueError):
            return None


def provision(directory, audience):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Refuse replacement: key rotation is an explicit new lab.
    key = secrets.token_bytes(32)
    with (directory/'key.bin').open('xb') as stream:
        stream.write(key)
    for subject, scope in [('reader', 'tickets:read'),
                           ('writer', 'tickets:read tickets:write')]:
        now = int(time.time())
        token = jwt.encode({'iss': ISSUER, 'aud': audience,
                            'sub': subject, 'scope': scope,
                            'iat': now, 'exp': now+900},
                           key, algorithm='HS256')
        with (directory/f'{subject}.token').open('x') as stream:
            stream.write(token)
    return {'files': ['key.bin', 'reader.token', 'writer.token'],
            'expires_in_seconds': 900,
            'protection': 'inherited directory permissions'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['provision', 'serve'])
    parser.add_argument('--private-dir', required=True)
    parser.add_argument('--db')
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    audience = f'http://127.0.0.1:{args.port}/mcp'
    if args.action == 'provision':
        print(json.dumps(provision(args.private_dir, audience)))
        return
    if not args.db:
        parser.error('--db is required to serve')
    key = (Path(args.private_dir)/'key.bin').read_bytes()
    server = make_server(
        Store(args.db), allow_writes=True,
        token_verifier=LabVerifier(key, audience),
        auth=AuthSettings(
            issuer_url=ISSUER, resource_server_url=audience,
            required_scopes=['tickets:read'],
            validate_token_resource=True))
    server.run(transport='streamable-http', host='127.0.0.1',
               port=args.port, stateless_http=True,
               json_response=True)


if __name__ == '__main__':
    main()
