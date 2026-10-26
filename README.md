# jwks server (project 2)

python jwks server that saves its rsa private keys in a sqlite database.

## files
- main.py: starts the server
- server.py: the /auth and jwks endpoints
- database.py: all the sqlite code
- keys.py: key helpers (pem and jwk stuff)
- tests/: pytest tests

## run it
```
pip install -r requirements.txt
python main.py
```
the server makes `totally_not_my_privateKeys.db` in the current folder. it keeps one valid key and one expired key in there. keys stay saved after a restart.

## endpoints
- `POST /auth` signs a jwt with a valid key from the db. add `?expired` to use an expired key instead. login is fake so any body works.
- `GET /.well-known/jwks.json` shows all keys that havent expired.

## sql injection
all queries use `?` placeholders so user values are never put into the sql string.

## tests and lint
```
python -m pytest --cov --cov-report=term-missing
flake8
```

## gradebot
run the server, then run `./gradebot project2` from the same folder so it can find the db file.
