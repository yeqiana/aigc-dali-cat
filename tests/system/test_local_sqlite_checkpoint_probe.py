from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from platform.repository.sqlite.local_checkpoint_store import LocalCheckpointStore

def test_sqlite_wal_and_optimistic_revision(tmp_path):
    db=tmp_path/"only-test.db"
    store=LocalCheckpointStore(db)
    store.initialize()
    assert store.compare_and_swap("frame-01",0,{"sha":"a"}) is True
    assert store.compare_and_swap("frame-01",0,{"sha":"b"}) is False
    assert store.compare_and_swap("frame-01",1,{"sha":"b"}) is True
    assert store.compare_and_swap("frame-01",1,{"sha":"c"}) is False
    assert store.read("frame-01")=={"revision":2,"payload":{"sha":"b"}}
    with store.connect() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower()=="wal"

def test_missing_parent_not_implicitly_created(tmp_path):
    store=LocalCheckpointStore(tmp_path/"missing"/"db.sqlite")
    try:store.initialize()
    except FileNotFoundError:pass
    else:raise AssertionError("should not silently write parent dirs")
    assert not (tmp_path/"missing").exists()

def test_invalid_payload_does_not_advance_authority(tmp_path):
    store=LocalCheckpointStore(tmp_path/"test.db")
    store.initialize()
    assert store.compare_and_swap("one",0,{"ok":True})
    try:store.compare_and_swap("one",1,{"bad":object()})
    except TypeError:pass
    else:raise AssertionError("bad JSON must fail")
    assert store.read("one")=={"revision":1,"payload":{"ok":True}}
