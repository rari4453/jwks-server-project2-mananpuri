# fixtures used by the tests

import os
import sys
import threading

import pytest

# so imports from the project folder work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database  # noqa: E402
from server import make_handler  # noqa: E402
from http.server import HTTPServer  # noqa: E402


@pytest.fixture
def db_path(tmp_path):
    # new db file for each test
    path = str(tmp_path / "test_keys.db")
    database.init_db(path)
    database.seed_keys(path)
    return path


@pytest.fixture
def base_url(db_path):
    # start the real server on a random free port
    httpd = HTTPServer(("127.0.0.1", 0), make_handler(db_path))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % httpd.server_port
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)
