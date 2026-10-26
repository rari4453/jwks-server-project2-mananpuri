# run this file to start the server
from server import create_server

HOST_NAME = "localhost"
SERVER_PORT = 8080


def main():
    web_server = create_server(HOST_NAME, SERVER_PORT)
    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        web_server.server_close()


if __name__ == "__main__":
    main()  # pragma: no cover
