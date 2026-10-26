# jwks server project 2 - Manan Puri 

a jwks server in python. it saves the rsa private keys in a sqlite database
instead of keeping them in memory.

## how to run
pip install -r requirements.txt
python main.py

it makes totally_not_my_privateKeys.db in the folder you run it from.
the keys stay saved if you restart the server.

## endpoints
- POST /auth gives back a jwt. add ?expired to sign it with an expired key.
- GET /.well-known/jwks.json shows the keys that havent expired yet.

all the sql uses ? placeholders so theres no sql injection.

## tests
python -m pytest --cov --cov-report=term-missing

## gradebot
gradebot.exe project-2 --run "python main.py" --port 8080 --code-dir . --database totally_not_my_privateKeys.db

screenshots of gradebot and the test coverage are in this repo.
