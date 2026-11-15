import concurrent.futures
import sqlite3
import pytest
from benchdesk.store import DeskError, Store


@pytest.fixture
def desk(tmp_path):
    store = Store(tmp_path/'desk.sqlite')
    store.initialize()
    return store


def test_fixture_and_literal_search(desk):
    assert desk.ticket(101)['status'] == 'queued'
    assert len(desk.equipment()) == 4
    assert desk.search('LAMP')['items'][0]['id'] == 102
    assert desk.search("' OR 1=1 --")['items'] == []
    assert desk.search('%')['items'] == []


def test_pagination(desk):
    first = desk.search(limit=3)
    assert [r['id'] for r in first['items']] == [101, 102, 103]
    second = desk.search(after=first['next_after'], limit=3)
    assert [r['id'] for r in second['items']] == [104, 105, 106]
    assert second['next_after'] is None


@pytest.mark.parametrize('kwargs', [
    {'limit': 0}, {'limit': 6}, {'limit': True},
    {'after': -1}, {'after': '0'}, {'query': 'x'*81}])
def test_search_rejections(desk, kwargs):
    with pytest.raises(DeskError):
        desk.search(**kwargs)


def test_missing_and_read_only(desk):
    with pytest.raises(DeskError, match='TICKET_NOT_FOUND'):
        desk.ticket(999)
    with desk.connect() as db:
        with pytest.raises(sqlite3.OperationalError):
            db.execute('DELETE FROM tickets')


def proposal(desk, owner='writer'):
    return desk.propose(owner, 101, 'inspecting', 1)['proposal_id']


def test_operator_approval_and_atomic_replay(desk):
    pid = proposal(desk)
    with pytest.raises(DeskError, match='OPERATOR_APPROVAL_REQUIRED'):
        desk.commit('writer', pid, 'attempt_0001')
    assert desk.ticket(101)['version'] == 1
    assert desk.audit() == []
    desk.approve(pid)
    result = desk.commit('writer', pid, 'attempt_0001')
    assert result['version'] == 2
    assert desk.commit('writer', pid, 'attempt_0001') == result
    assert len(desk.audit()) == 1
    with pytest.raises(DeskError, match='PROPOSAL_CONSUMED'):
        desk.commit('writer', pid, 'attempt_0002')


def test_stale_approval(desk):
    first, second = proposal(desk), proposal(desk)
    desk.approve(first)
    desk.approve(second)
    desk.commit('writer', first, 'attempt_0001')
    with pytest.raises(DeskError, match='STALE_VERSION'):
        desk.commit('writer', second, 'attempt_0002')
    assert len(desk.audit()) == 1


def test_owner_expiry_and_transition(desk):
    pid = proposal(desk)
    with pytest.raises(DeskError, match='OWNER_MISMATCH'):
        desk.commit('reader', pid, 'attempt_0001')
    with pytest.raises(DeskError, match='EXPIRED'):
        desk.approve(pid, clock=lambda: 10**12)
    with pytest.raises(DeskError, match='TRANSITION'):
        desk.propose('writer', 101, 'ready', 1)
    with pytest.raises(DeskError, match='STALE_VERSION'):
        desk.propose('writer', 101, 'inspecting', 2)


def test_key_bound_to_request(desk):
    pid = proposal(desk)
    desk.approve(pid)
    desk.commit('writer', pid, 'attempt_0001')
    with pytest.raises(DeskError, match='KEY_CONFLICT'):
        desk.commit('writer', 'different', 'attempt_0001')


def test_simultaneous_retry(desk):
    pid = proposal(desk)
    desk.approve(pid)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: desk.commit(
            'writer', pid, 'attempt_0001'), range(2)))
    assert results[0] == results[1]
    assert len(desk.audit()) == 1


def test_initialize_never_overwrites(desk):
    before = desk.path.read_bytes()
    with pytest.raises(FileExistsError):
        desk.initialize()
    assert desk.path.read_bytes() == before


def test_proposal_limit(desk):
    for _ in range(20):
        proposal(desk)
    with pytest.raises(DeskError, match='TOO_MANY_PROPOSALS'):
        proposal(desk)


def test_audit_failure_rolls_back_entire_commit(desk):
    pid = proposal(desk)
    desk.approve(pid)
    with desk.connect(write=True) as db:
        db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit "
                   "BEGIN SELECT RAISE(ABORT,'test audit failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        desk.commit('writer', pid, 'rollback_0001')
    assert desk.ticket(101)['version'] == 1
    assert desk.ticket(101)['status'] == 'queued'
    assert desk.inspect_proposal(pid)['consumed'] == 0
    assert desk.audit() == []
    with desk.connect() as db:
        assert db.execute('SELECT count(*) FROM operations').fetchone()[0] == 0
