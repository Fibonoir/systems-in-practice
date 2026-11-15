"""Deterministic MCP probe, with no model or paid service."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def probe(args):
    if args.url:
        target = args.url
    else:
        command = ['-m', 'benchdesk.server', '--db',
                   str(Path(args.db).resolve())]
        if args.allow_writes:
            command += ['--allow-writes', '--principal',
                        'local-operator-client']
        target = StdioServerParameters(
            command=sys.executable, args=command,
            cwd=str(Path(__file__).resolve().parents[1]))
    async with Client(target, mode=args.mode,
                      read_timeout_seconds=5) as client:
        tools = await client.list_tools()
        print(json.dumps({'protocol': client.protocol_version,
                          'tools': [t.name for t in tools.tools]}))
        if args.action == 'list':
            for tool in tools.tools:
                print(tool.model_dump_json(by_alias=True))
        elif args.action == 'call':
            result = await client.call_tool(
                args.name, json.loads(args.arguments))
            print(result.model_dump_json(by_alias=True))
            if result.is_error:
                return 2
        elif args.action == 'resource':
            result = await client.read_resource(args.uri)
            print(result.model_dump_json(by_alias=True))
        elif args.action == 'prompt':
            result = await client.get_prompt(
                'triage_ticket', {'ticket_id': '101'})
            print(result.model_dump_json(by_alias=True))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='lab/desk.sqlite')
    parser.add_argument('--url')
    parser.add_argument('--allow-writes', action='store_true')
    parser.add_argument('--mode', default='auto',
                        choices=['auto', 'legacy', '2026-07-28'])
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    call = sub.add_parser('call')
    call.add_argument('name')
    call.add_argument('arguments')
    resource = sub.add_parser('resource')
    resource.add_argument('uri')
    sub.add_parser('prompt')
    args = parser.parse_args()
    raise SystemExit(asyncio.run(probe(args)))


if __name__ == '__main__':
    main()
