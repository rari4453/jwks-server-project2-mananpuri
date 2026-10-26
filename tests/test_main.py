# tests for main.py

import main


class FakeServer:
    def __init__(self, raise_interrupt):
        self.raise_interrupt = raise_interrupt
        self.closed = False

    def serve_forever(self):
        if self.raise_interrupt:
            raise KeyboardInterrupt

    def server_close(self):
        self.closed = True


def test_main_closes_server_after_normal_exit(monkeypatch):
    fake = FakeServer(False)
    monkeypatch.setattr(main, "create_server", lambda host, port: fake)
    main.main()
    assert fake.closed


def test_main_handles_keyboard_interrupt(monkeypatch):
    fake = FakeServer(True)
    monkeypatch.setattr(main, "create_server", lambda host, port: fake)
    main.main()
    assert fake.closed
