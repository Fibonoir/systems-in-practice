"""Read token from a file; never print it or put it in an argument."""
import argparse
import asyncio
from pathlib import Path
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


async def run(args):
    token = Path(args.token_file).read_text().strip()
    async with httpx2.AsyncClient(headers={
        'Authorization': f'Bearer {token}'}) as http:
        transport = streamable_http_client(args.url,
                                           http_client=http)
        async with Client(transport, mode='2026-07-28') as client:
            result = await client.call_tool('get_ticket',
                                             {'ticket_id': 101})
            print(result.model_dump_json(by_alias=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--token-file', required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8766/mcp')
    asyncio.run(run(parser.parse_args()))
