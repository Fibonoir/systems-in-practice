"""Run from companion root. Stage one request, then inspect/approve locally."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def run(args):
    target = StdioServerParameters(command=sys.executable,
        args=['-m', 'benchdesk.server', '--db',
              str(Path(args.db).resolve()), '--allow-writes',
              '--principal', 'local-operator-client'])
    receipt = Path(args.receipt)
    async with Client(target, mode='2026-07-28') as client:
        if args.action == 'propose':
            if receipt.exists():
                raise FileExistsError('use a new receipt path')
            result = await client.call_tool('propose_status_change',
                {'ticket_id': 101, 'new_status': 'inspecting',
                 'expected_version': 1})
            if not result.is_error:
                data = json.loads(result.content[0].text)
                data['operation_key'] = 'write_demo_0001'
                receipt.parent.mkdir(parents=True, exist_ok=True)
                with receipt.open('x') as stream:
                    json.dump(data, stream, indent=2)
        else:
            data = json.loads(receipt.read_text())
            result = await client.call_tool('commit_status_change',
                {'proposal_id': data['proposal_id'],
                 'operation_key': data['operation_key']})
        print(result.model_dump_json(by_alias=True))
        return 2 if result.is_error else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['propose', 'commit'])
    parser.add_argument('--db', default='lab/write.sqlite')
    parser.add_argument('--receipt', default='lab/proposal.json')
    raise SystemExit(asyncio.run(run(parser.parse_args())))
