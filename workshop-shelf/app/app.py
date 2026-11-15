"""Workshop Shelf: intentionally local teaching fixture, not public software."""
import html
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import psycopg

VERSION = os.getenv('APP_VERSION', '1')
REQUIRED = int(VERSION)


def connect():
    password = Path(os.environ['DB_PASSWORD_FILE']).read_text().strip()
    return psycopg.connect(
        host=os.getenv('DB_HOST', 'db'), dbname='shelf',
        user='shelf', password=password, connect_timeout=3,
        options='-c statement_timeout=3000')


def schema(conn):
    row = conn.execute('SELECT version FROM schema_version').fetchone()
    if row is None or row[0] != REQUIRED:
        raise RuntimeError('schema version mismatch')


def initialize():
    with connect() as conn:
        conn.execute('CREATE TABLE schema_version (version integer)')
        conn.execute('INSERT INTO schema_version VALUES (1)')
        conn.execute('''CREATE TABLE items (
            id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name text NOT NULL UNIQUE,
            quantity integer NOT NULL CHECK (quantity >= 0))''')
        conn.execute('''INSERT INTO items (name, quantity)
            VALUES ('Bench clamps', 4), ('Safety glasses', 7)''')
    print('initialized schema 1; two fictional records', flush=True)


def migrate():
    with connect() as conn:
        conn.execute('LOCK TABLE schema_version IN EXCLUSIVE MODE')
        row = conn.execute('SELECT version FROM schema_version').fetchone()
        if row != (1,):
            raise RuntimeError('migration requires schema 1')
        conn.execute("ALTER TABLE items ADD COLUMN note text NOT NULL DEFAULT ''")
        conn.execute('UPDATE schema_version SET version=2')
    print('migrated schema 1 to 2 in one transaction', flush=True)


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, kind='application/json'):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/live':
            return self.reply(200, {'live': True, 'version': VERSION})
        try:
            with connect() as conn:
                schema(conn)
                if self.path == '/ready':
                    return self.reply(200, {'ready': True, 'schema': REQUIRED})
                fields = 'id, name, quantity' + (', note' if REQUIRED == 2 else '')
                rows = conn.execute('SELECT ' + fields + ' FROM items ORDER BY id')
                keys = ['id', 'name', 'quantity'] + (['note'] if REQUIRED == 2 else [])
                items = [dict(zip(keys, row)) for row in rows]
            if self.path == '/api/items':
                return self.reply(200, items)
            if self.path != '/':
                return self.reply(404, {'error': 'unknown path'})
            listing = ''.join('<li>' + html.escape(i['name']) + ': ' +
                              str(i['quantity']) + '</li>' for i in items)
            return self.reply(200, '<!doctype html><html lang="en"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width">'
                '<title>Workshop Shelf</title><h1>Workshop Shelf</h1>'
                '<p>Local teaching fixture. Version ' + VERSION + '</p><ul>' +
                listing + '</ul><p>Use the companion API lab to add stock.</p></html>',
                'text/html')
        except Exception as exc:
            print('readiness failure: ' + type(exc).__name__, flush=True)
            return self.reply(503, {'error': 'database unavailable or schema mismatch'})

    def do_POST(self):
        if self.path != '/api/items':
            return self.reply(404, {'error': 'unknown path'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 1 <= length <= 2048:
                raise ValueError('request size')
            data = json.loads(self.rfile.read(length))
            if set(data) != {'name', 'quantity'}:
                raise ValueError('fields')
            name, quantity = data['name'], data['quantity']
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
                raise ValueError('name')
            if type(quantity) is not int or not 0 <= quantity <= 100000:
                raise ValueError('quantity')
        except (ValueError, TypeError, KeyError):
            return self.reply(400, {'error': 'use name and nonnegative integer quantity'})
        try:
            with connect() as conn:
                schema(conn)
                conn.execute('INSERT INTO items (name, quantity) VALUES (%s, %s)',
                             (name.strip(), quantity))
            return self.reply(201, {'created': name.strip()})
        except psycopg.errors.UniqueViolation:
            return self.reply(409, {'error': 'name already exists'})
        except Exception as exc:
            print('write failure: ' + type(exc).__name__, flush=True)
            return self.reply(503, {'error': 'database unavailable or schema mismatch'})


if __name__ == '__main__':
    if len(sys.argv) > 1:
        {'init': initialize, 'migrate': migrate}[sys.argv[1]]()
    else:
        print('Workshop Shelf v' + VERSION + ' listening on 8000', flush=True)
        HTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
