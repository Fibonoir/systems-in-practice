import asyncio
import json
from pathlib import Path
import sys
import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from benchdesk.server import make_server
from benchdesk.store import Store


@pytest.fixture
def desk(tmp_path):
    store = Store(tmp_path/'desk.sqlite')
    store.initialize()
    return store


def payload(result):
    if result.structured_content is not None:
        value = result.structured_content
        return value.get('result', value)
    return json.loads(result.content[0].text)


def test_in_memory_contract(desk):
    async def run():
        async with Client(make_server(desk),
                          mode='2026-07-28') as client:
            assert client.protocol_version == '2026-07-28'
            tools = (await client.list_tools()).tools
            assert {t.name for t in tools} == {
                'search_tickets', 'get_ticket'}
            for arguments in [{'limit': 6}, {'after': -1},
                              {'limit': True}, {'query': 'x'*81}]:
                result = await client.call_tool(
                    'search_tickets', arguments)
                assert result.is_error
            good = await client.call_tool('get_ticket',
                                           {'ticket_id': 101})
            assert payload(good)['status'] == 'queued'
            missing = await client.call_tool('get_ticket',
                                              {'ticket_id': 999})
            assert missing.is_error
            resources = await client.list_resources()
            assert 'benchdesk://equipment' in {
                str(r.uri) for r in resources.resources}
            resource = await client.read_resource(
                'benchdesk://tickets/101')
            assert json.loads(resource.contents[0].text)['id'] == 101
            prompt = await client.get_prompt(
                'triage_ticket', {'ticket_id': '101'})
            assert 'Do not propose' in prompt.messages[0].content.text
    asyncio.run(run())


@pytest.mark.parametrize('mode,expected', [
    ('2026-07-28', '2026-07-28'), ('legacy', '2025-11-25')])
def test_real_stdio(desk, mode, expected):
    async def run():
        target = StdioServerParameters(command=sys.executable,
            args=['-m', 'benchdesk.server', '--db', str(desk.path)],
            cwd=str(Path(__file__).resolve().parents[1]))
        async with Client(target, mode=mode,
                          read_timeout_seconds=15) as client:
            assert client.protocol_version == expected
            result = await client.call_tool('get_ticket',
                                             {'ticket_id': 101})
            assert payload(result)['equipment_id'] == 'EQ-01'
    asyncio.run(run())


def test_write_path_over_protocol(desk):
    async def run():
        async with Client(make_server(desk, True, 'writer')) as client:
            result = await client.call_tool('propose_status_change',
                {'ticket_id': 101, 'new_status': 'inspecting',
                 'expected_version': 1})
            assert not result.is_error
            pid = payload(result)['proposal_id']
            arguments = {'proposal_id': pid,
                         'operation_key': 'protocol_0001'}
            denied = await client.call_tool('commit_status_change',
                                             arguments)
            assert denied.is_error
            desk.approve(pid)
            done = await client.call_tool('commit_status_change',
                                           arguments)
            replay = await client.call_tool('commit_status_change',
                                             arguments)
            assert payload(done) == payload(replay)
            assert len(desk.audit()) == 1
    asyncio.run(run())
