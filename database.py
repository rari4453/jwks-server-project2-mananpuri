# all the sqlite stuff lives here
# i use ? placeholders everywhere so sql injection cant happen
import sqlite3
import time
from contextlib import closing

from keys import generate_private_key, serialize_private_key

DB_FILE = "totally_not_my_privateKeys.db"

# one hour in seconds
HOUR = 3600

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS keys(
    kid INTEGER PRIMARY KEY AUTOINCREMENT,
    key BLOB NOT NULL,
    exp INTEGER NOT NULL
)
"""


def connect(db_path=DB_FILE):
    return sqlite3.connect(db_path)


def init_db(db_path=DB_FILE):
    # make the file and table if they arent there yet
    with closing(connect(db_path)) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()


def insert_key(pem_bytes, exp, db_path=DB_FILE):
    # save a key, returns the new kid
    with closing(connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO keys (key, exp) VALUES (?, ?)",
            (pem_bytes, int(exp)),
        )
        conn.commit()
        return cursor.lastrowid


def get_key(expired=False, now=None, db_path=DB_FILE):
    # returns (kid, pem) or None if nothing matches
    if now is None:
        now = int(time.time())
    if expired:
        query = "SELECT kid, key FROM keys WHERE exp <= ? ORDER BY exp DESC LIMIT 1"
    else:
        query = "SELECT kid, key FROM keys WHERE exp > ? ORDER BY exp DESC LIMIT 1"
    with closing(connect(db_path)) as conn:
        row = conn.execute(query, (int(now),)).fetchone()
    if row is None:
        return None
    return row[0], row[1]


def get_valid_keys(now=None, db_path=DB_FILE):
    # all the keys that havent expired yet
    if now is None:
        now = int(time.time())
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT kid, key FROM keys WHERE exp > ? ORDER BY kid",
            (int(now),),
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def seed_keys(db_path=DB_FILE, now=None):
    # make sure theres at least one good key and one expired key
    # only adds what is missing so restarts keep old keys
    if now is None:
        now = int(time.time())
    if get_key(expired=False, now=now, db_path=db_path) is None:
        pem = serialize_private_key(generate_private_key())
        insert_key(pem, now + HOUR, db_path)
    if get_key(expired=True, now=now, db_path=db_path) is None:
        pem = serialize_private_key(generate_private_key())
        insert_key(pem, now - HOUR, db_path)
