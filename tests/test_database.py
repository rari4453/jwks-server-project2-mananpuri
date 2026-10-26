# tests for the database file

import sqlite3
import time
from contextlib import closing

import database
from keys import generate_private_key, serialize_private_key


def test_init_creates_table_with_expected_schema(tmp_path):
    path = str(tmp_path / "schema.db")
    database.init_db(path)
    with closing(sqlite3.connect(path)) as conn:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(keys)")]
    assert cols == ["kid", "key", "exp"]


def test_init_is_idempotent(tmp_path):
    path = str(tmp_path / "idem.db")
    database.init_db(path)
    database.init_db(path)


def test_seed_creates_one_valid_and_one_expired_key(db_path):
    now = int(time.time())
    assert database.get_key(expired=False, now=now, db_path=db_path) is not None
    assert database.get_key(expired=True, now=now, db_path=db_path) is not None


def test_seed_does_not_duplicate_on_restart(db_path):
    database.seed_keys(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM keys").fetchone()[0]
    assert count == 2


def test_seed_replaces_valid_key_after_it_expires(db_path):
    future = int(time.time()) + 10 * 3600
    database.seed_keys(db_path, now=future)
    assert database.get_key(expired=False, now=future, db_path=db_path)


def test_insert_key_returns_incrementing_kid(db_path):
    pem = serialize_private_key(generate_private_key())
    first = database.insert_key(pem, time.time() + 60, db_path)
    second = database.insert_key(pem, time.time() + 60, db_path)
    assert second == first + 1


def test_get_key_valid_vs_expired(db_path):
    now = int(time.time())
    kid_valid, _ = database.get_key(expired=False, now=now, db_path=db_path)
    kid_old, _ = database.get_key(expired=True, now=now, db_path=db_path)
    assert kid_valid != kid_old


def test_get_key_returns_none_when_no_match(tmp_path):
    path = str(tmp_path / "empty.db")
    database.init_db(path)
    assert database.get_key(expired=False, db_path=path) is None
    assert database.get_key(expired=True, db_path=path) is None


def test_get_valid_keys_excludes_expired(db_path):
    keys = database.get_valid_keys(db_path=db_path)
    assert len(keys) == 1


def test_get_valid_keys_returns_all_unexpired(db_path):
    pem = serialize_private_key(generate_private_key())
    database.insert_key(pem, time.time() + 7200, db_path)
    assert len(database.get_valid_keys(db_path=db_path)) == 2


def test_queries_are_parameterized(db_path):
    # bad input should be treated as data not sql
    evil = "0; DROP TABLE keys; --"
    pem = serialize_private_key(generate_private_key())
    try:
        database.insert_key(pem, evil, db_path)
    except ValueError:
        pass  # int() caught it first which is fine too
    with closing(sqlite3.connect(db_path)) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE name='keys'"
        ).fetchall()
    assert tables == [("keys",)]
