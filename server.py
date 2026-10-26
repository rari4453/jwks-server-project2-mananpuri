# the http server, handles /auth and the jwks endpoint
import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import jwt

import database
from keys import deserialize_private_key, private_key_to_jwk


def make_handler(db_path):
    # handler class that knows which db file to use

    class JWKSHandler(BaseHTTPRequestHandler):

        def _send_status(self, code):
            self.send_response(code)
            self.end_headers()

        def _read_body(self):
            # we dont check the login, just read the body and ignore it
            length = int(self.headers.get("Content-Length") or 0)
            if length > 0:
                self.rfile.read(length)

        # methods we dont support
        def do_PUT(self):
            self._send_status(405)

        def do_PATCH(self):
            self._send_status(405)

        def do_DELETE(self):
            self._send_status(405)

        def do_HEAD(self):
            self._send_status(405)

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path != "/auth":
                self._send_status(405)
                return
            self._read_body()

            # keep_blank_values so ?expired with no value still works
            params = parse_qs(parsed.query, keep_blank_values=True)
            want_expired = "expired" in params

            row = database.get_key(expired=want_expired, db_path=db_path)
            if row is None:
                self._send_status(500)
                return
            kid, pem = row

            now = datetime.datetime.now(datetime.timezone.utc)
            hour = datetime.timedelta(hours=1)
            if want_expired:
                exp = now - hour
            else:
                exp = now + hour
            payload = {"user": "username", "exp": exp}

            token = jwt.encode(
                payload,
                deserialize_private_key(pem),
                algorithm="RS256",
                headers={"kid": str(kid)},
            )
            self.send_response(200)
            self.end_headers()
            self.wfile.write(token.encode("utf-8"))

        def do_GET(self):
            if self.path != "/.well-known/jwks.json":
                self._send_status(405)
                return
            # only the keys that havent expired
            keys = []
            for kid, pem in database.get_valid_keys(db_path=db_path):
                keys.append(private_key_to_jwk(kid, deserialize_private_key(pem)))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"keys": keys}).encode("utf-8"))

        def log_message(self, format, *args):
            # no logging so the console stays clean
            pass

    return JWKSHandler


def create_server(host="localhost", port=8080, db_path=database.DB_FILE):
    # set up the db, add keys, then return the server
    database.init_db(db_path)
    database.seed_keys(db_path)
    return HTTPServer((host, port), make_handler(db_path))
