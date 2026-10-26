# tests that hit the running server

import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import HTTPServer

import jwt
import pytest

import database
import server
from keys import deserialize_private_key


def request(url, method="GET", data=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def get_jwks(base_url):
    status, body = request(base_url + "/.well-known/jwks.json")
    assert status == 200
    return json.loads(body)["keys"]


def public_key_for(jwks, kid):
    jwk = next(k for k in jwks if k["kid"] == kid)
    return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))


def test_auth_returns_jwt_verifiable_with_jwks(base_url):
    status, body = request(base_url + "/auth", "POST")
    assert status == 200
    token = body.decode()
    kid = jwt.get_unverified_header(token)["kid"]
    key = public_key_for(get_jwks(base_url), kid)
    claims = jwt.decode(token, key, algorithms=["RS256"])
    assert claims["user"] == "username"


def test_auth_accepts_json_body(base_url):
    payload = json.dumps({"username": "userABC", "password": "password123"})
    status, body = request(base_url + "/auth", "POST", payload.encode(),
                           {"Content-Type": "application/json"})
    assert status == 200
    assert body.count(b".") == 2


def test_auth_accepts_basic_auth(base_url):
    headers = {"Authorization": "Basic dXNlckFCQzpwYXNzd29yZDEyMw=="}
    status, _ = request(base_url + "/auth", "POST", b"", headers)
    assert status == 200


def test_expired_param_uses_expired_key(base_url, db_path):
    status, body = request(base_url + "/auth?expired=true", "POST")
    assert status == 200
    token = body.decode()
    kid = int(jwt.get_unverified_header(token)["kid"])
    # expired key should not be in the jwks
    assert str(kid) not in [k["kid"] for k in get_jwks(base_url)]
    # token exp should be in the past
    claims = jwt.decode(token, options={"verify_signature": False,
                                        "verify_exp": False})
    assert claims["exp"] < time.time()
    # signature should still match the stored key
    _, pem = database.get_key(expired=True, db_path=db_path)
    public = deserialize_private_key(pem).public_key()
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, public, algorithms=["RS256"])


def test_expired_flag_without_value_still_counts(base_url):
    status, body = request(base_url + "/auth?expired", "POST")
    assert status == 200
    kid = jwt.get_unverified_header(body.decode())["kid"]
    assert kid not in [k["kid"] for k in get_jwks(base_url)]


def test_valid_token_kid_is_in_jwks(base_url):
    _, body = request(base_url + "/auth", "POST")
    kid = jwt.get_unverified_header(body.decode())["kid"]
    assert kid in [k["kid"] for k in get_jwks(base_url)]


def test_jwks_only_contains_valid_keys(base_url, db_path):
    keys = get_jwks(base_url)
    assert len(keys) == len(database.get_valid_keys(db_path=db_path))
    for jwk in keys:
        assert set(jwk) == {"alg", "kty", "use", "kid", "n", "e"}


def test_jwks_content_type(base_url):
    with urllib.request.urlopen(base_url + "/.well-known/jwks.json") as resp:
        assert resp.headers["Content-type"] == "application/json"


def test_auth_returns_500_when_no_key_available(tmp_path):
    # no keys in the db should give a 500
    path = str(tmp_path / "empty.db")
    database.init_db(path)
    httpd = HTTPServer(("127.0.0.1", 0), server.make_handler(path))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        status, _ = request("http://127.0.0.1:%d/auth" % httpd.server_port,
                            "POST")
        assert status == 500
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "HEAD"])
def test_unsupported_methods_return_405(base_url, method):
    status, _ = request(base_url + "/auth", method)
    assert status == 405


def test_unknown_paths_return_405(base_url):
    assert request(base_url + "/nope", "GET")[0] == 405
    assert request(base_url + "/nope", "POST")[0] == 405


def test_create_server_initializes_and_seeds_db(tmp_path):
    path = str(tmp_path / "created.db")
    httpd = server.create_server("127.0.0.1", 0, path)
    httpd.server_close()
    assert os.path.exists(path)
