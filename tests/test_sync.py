"""The sync against a server kept in memory: what happens to the notes when the place changes.

    python3 -m pytest tests/        (or: python3 tests/test_sync.py)
"""
import os
import sys
import tempfile
from urllib.parse import unquote

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import readers_notes as rn  # noqa: E402


class Server:
    """Folders of files, by URL, with an etag that changes at every write."""

    def __init__(self):
        self.files, self.dirs, self.n = {}, set(), 0

    def client(self, *_args, **_kw):
        return FakeDav(self)


class FakeDav:
    def __init__(self, server):
        self.s = server

    def exists(self, url):
        return url in self.s.dirs

    def mkcol(self, url):
        self.s.dirs.add(url)

    def list(self, url):
        out = [{"name": unquote(d[len(url):].rstrip("/")), "dir": True, "etag": None, "modified": 0}
               for d in self.s.dirs if d.startswith(url) and d != url and "/" not in d[len(url):].rstrip("/")]
        out += [{"name": unquote(u[len(url):]), "dir": False, "etag": e, "modified": 0}
                for u, (_t, e) in self.s.files.items() if u.startswith(url) and "/" not in u[len(url):]]
        return out

    def get(self, url, allow_missing=False):
        return self.s.files[url][0] if url in self.s.files else None

    def put(self, url, text):
        self.s.n += 1
        self.s.files[url] = (text, "e%d" % self.s.n)
        return self.s.files[url][1]

    def delete(self, url):
        self.s.files.pop(url, None)
        self.s.dirs.discard(url)


def setup(texts=("Milk\nand eggs", "Call the plumber", "Packing list\nboots")):
    server = Server()
    rn.WebDav = server.client
    store = rn.Store(tempfile.mkdtemp(prefix="notes-test-"))
    for t in texts:
        store.create(t)
    return server, store


def cfg(folder="Notes", server="https://a.example/dav"):
    return {"server": server, "folder": folder, "username": "u", "password": "p"}


def titles(store):
    return sorted(store.text(n["id"]).split("\n")[0] for n in store.all() if not n.get("deleted"))


def names(server, place):
    return sorted(unquote(u[len(place):]) for u in server.files if u.startswith(place))


ALL = ["Call the plumber", "Milk", "Packing list"]


def test_first_sync_uploads():
    server, store = setup()
    assert rn.sync_run(store, cfg()) == (3, 0, 0)
    assert len(names(server, rn.folder_url(cfg()))) == 3


def test_another_folder_set_without_the_settings_dialog_keeps_the_notes():
    # the configuration changed outside the window (--import-credentials, or the file edited)
    server, store = setup()
    rn.sync_run(store, cfg())
    rn.sync_run(store, cfg("Elsewhere"))
    assert titles(store) == ALL
    assert len(names(server, rn.folder_url(cfg("Elsewhere")))) == 3
    assert len(names(server, rn.folder_url(cfg()))) == 3


def test_another_server_holding_other_notes_keeps_both():
    server, store = setup()
    rn.sync_run(store, cfg())
    other = cfg(server="https://b.example/dav")
    server.dirs.add(rn.folder_url(other))
    FakeDav(server).put(rn.folder_url(other) + "Theirs.txt", "Theirs\nalready there")
    rn.sync_run(store, other)
    assert titles(store) == sorted(ALL + ["Theirs"])


def test_there_and_back_does_not_double_the_notes():
    server, store = setup()
    rn.sync_run(store, cfg())
    rn.sync_run(store, cfg("Elsewhere"))
    rn.sync_run(store, cfg())
    assert titles(store) == ALL
    assert len(names(server, rn.folder_url(cfg()))) == 3


def test_there_and_back_through_the_settings_does_not_double_the_notes():
    server, store = setup()
    rn.sync_run(store, cfg())
    store.forget_server()   # what the settings window does when the folder changes
    rn.sync_run(store, cfg("Elsewhere"))
    store.forget_server()
    rn.sync_run(store, cfg())
    assert titles(store) == ALL
    assert len(names(server, rn.folder_url(cfg()))) == 3


def test_the_same_notes_already_on_the_server_are_not_doubled():
    # a computer set up by hand next to a phone that holds the same notes
    server, store = setup()
    place = rn.folder_url(cfg())
    server.dirs.add(place)
    for t in ("Milk\nand eggs", "Call the plumber", "Packing list\nboots"):
        FakeDav(server).put(place + rn.encode_segment(rn.file_name_of(t)), t)
    rn.sync_run(store, cfg())
    assert titles(store) == ALL
    assert len(names(server, place)) == 3


def test_same_title_other_text_keeps_both():
    server, store = setup(("Milk\nand eggs",))
    place = rn.folder_url(cfg())
    server.dirs.add(place)
    FakeDav(server).put(place + "Milk.txt", "Milk\nand butter")
    rn.sync_run(store, cfg())
    assert len(titles(store)) == 2 and len(names(server, place)) == 2


def test_deleted_on_the_server_is_still_deleted_here():
    server, store = setup()
    rn.sync_run(store, cfg())
    place = rn.folder_url(cfg())
    FakeDav(server).delete(place + "Milk.txt")
    rn.sync_run(store, cfg())
    assert titles(store) == ["Call the plumber", "Packing list"]


def test_a_trailing_slash_is_the_same_place():
    server, store = setup()
    rn.sync_run(store, cfg())
    assert rn.sync_run(store, cfg(server="https://a.example/dav/")) == (0, 0, 0)
    assert len(names(server, rn.folder_url(cfg()))) == 3


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn(); print("ok  ", name)
            except AssertionError as e:
                failed += 1; print("FAIL", name, e)
    sys.exit(1 if failed else 0)
