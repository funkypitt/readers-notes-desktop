"""The sync against a server kept in memory: what happens to the notes when the place changes.

    python3 -m pytest tests/        (or: python3 tests/test_sync.py)
"""
import os
import sys
import tempfile
import time
from urllib.parse import unquote

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import readers_notes as rn  # noqa: E402


class Server:
    """Folders of files, by URL, with an etag that changes at every write."""

    def __init__(self):
        self.files, self.dirs, self.n = {}, set(), 0
        self.mtime = {}          # url → last-modified in ms (0: the server does not say)

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
        out += [{"name": unquote(u[len(url):]), "dir": False, "etag": e, "modified": self.s.mtime.get(u, 0)}
                for u, (_t, e) in self.s.files.items() if u.startswith(url) and "/" not in u[len(url):]]
        return out

    def get(self, url, allow_missing=False):
        return self.s.files[url][0] if url in self.s.files else None

    def put(self, url, text):
        self.s.n += 1
        self.s.files[url] = (text, "e%d" % self.s.n)
        return self.s.files[url][1]

    def get_bytes(self, url):
        return self.s.files[url][0] if url in self.s.files else None

    def put_bytes(self, url, data, content_type):
        assert isinstance(data, bytes) and content_type.startswith("image/")
        assert url.rsplit("/", 1)[0] + "/" in self.s.dirs, "PUT into a folder that was not made"
        self.put(url, data)
        self.s.mtime[url] = int(rn.time.time() * 1000)

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


# ---- the book notes: Reader's Books writes them into a subfolder, read here and never written ----

def books_url(c=None):
    return rn.folder_url(c or cfg()) + rn.encode_segment(rn.BOOKS_FOLDER) + "/"


def with_books(texts=("The Old Garden\nA hedge is a slow wall.",), **kw):
    """Notes synced once, then a books folder appears on the server with these files."""
    server, store = setup(**kw)
    rn.sync_run(store, cfg())
    server.dirs.add(books_url())
    for i, t in enumerate(texts):
        FakeDav(server).put(books_url() + "book%d.txt" % i, t)
    return server, store


def book_notes(store):
    return [n for n in store.all() if n.get("folder") == rn.BOOKS_FOLDER]


def test_a_book_note_comes_down_without_folders():
    server, store = with_books()
    assert rn.sync_run(store, cfg()) == (0, 1, 0)
    assert titles(store) == sorted(ALL + ["The Old Garden"])
    assert [store.text(n["id"]) for n in book_notes(store)] == ["The Old Garden\nA hedge is a slow wall."]
    assert not book_notes(store)[0]["dirty"]
    # still someone who never used folders: no folder registered, the ordinary notes where they were
    assert not store.uses_folders() and store.folders_state() == ([], [])
    assert rn.sync_run(store, cfg()) == (0, 0, 0)
    assert len(names(server, rn.folder_url(cfg()))) == 4


def test_a_book_note_changed_there_is_replaced_here():
    server, store = with_books()
    rn.sync_run(store, cfg())
    FakeDav(server).put(books_url() + "book0.txt", "The Old Garden\nA hedge is a slow wall.\nMoss keeps the hours.")
    assert rn.sync_run(store, cfg()) == (0, 1, 0)
    assert [store.text(n["id"]) for n in book_notes(store)] == ["The Old Garden\nA hedge is a slow wall.\nMoss keeps the hours."]
    assert not store.uses_folders()


def test_a_book_note_removed_there_is_removed_here():
    server, store = with_books(("The Old Garden\nA hedge is a slow wall.", "Tides\nThe sea returns what it borrows."))
    rn.sync_run(store, cfg())
    assert len(book_notes(store)) == 2
    FakeDav(server).delete(books_url() + "book0.txt")
    assert rn.sync_run(store, cfg()) == (0, 0, 1)
    assert titles(store) == sorted(ALL + ["Tides"])
    # the whole subfolder gone: the last one goes too, the ordinary notes stay
    FakeDav(server).delete(books_url() + "book1.txt")
    FakeDav(server).delete(books_url())
    assert rn.sync_run(store, cfg()) == (0, 0, 1)
    assert titles(store) == ALL and not store.uses_folders()
    assert books_url() not in server.dirs


def test_nothing_ever_goes_up_to_the_books_folder():
    server, store = with_books()
    rn.sync_run(store, cfg())
    before = {u: v for u, v in server.files.items() if u.startswith(books_url())}
    book = book_notes(store)[0]["id"]
    # the store refuses: typing, deleting, moving out, moving in, a new note inside
    assert store.save(book, "The Old Garden\nmine now") is None
    store.delete(book)
    store.move(book, "")
    mine = store.create("Shopping\nnails", folder=rn.BOOKS_FOLDER)
    store.move(mine, rn.BOOKS_FOLDER)
    assert store.text(book) == "The Old Garden\nA hedge is a slow wall." and store.get(book)["folder"] == rn.BOOKS_FOLDER
    assert not store.get(book)["dirty"] and not store.get(book)["deleted"] and store.get(mine)["folder"] == ""
    # and an index that says otherwise (written by hand): a book note changed here, a note of ours placed there
    store._write(book, "The Old Garden\nmine now")
    store._find(book)["dirty"] = True
    store._find(mine)["folder"] = rn.BOOKS_FOLDER
    rn.sync_run(store, cfg())
    assert {u: v for u, v in server.files.items() if u.startswith(books_url())} == before
    assert store.text(book) == "The Old Garden\nA hedge is a slow wall." and not store.get(book)["dirty"]
    assert "Shopping.txt" in names(server, rn.folder_url(cfg())) and store.get(mine)["folder"] == ""
    assert not store.uses_folders()
    # deleted here by such an index: not deleted there, and back here
    store._find(book)["deleted"] = True
    rn.sync_run(store, cfg())
    assert {u: v for u, v in server.files.items() if u.startswith(books_url())} == before
    assert len(book_notes(store)) == 1


def test_the_books_folder_is_never_created():
    server, store = setup()
    store._find(store.create("Shopping\nnails"))["folder"] = rn.BOOKS_FOLDER
    rn.sync_run(store, dict(cfg(), folders=True))
    assert books_url() not in server.dirs
    assert not [u for u in server.files if u.startswith(books_url())]
    assert titles(store) == sorted(ALL + ["Shopping"])


def test_another_place_does_not_send_the_book_notes_up():
    server, store = with_books()
    rn.sync_run(store, cfg())
    rn.sync_run(store, cfg("Elsewhere"))
    assert titles(store) == ALL
    assert len(names(server, rn.folder_url(cfg("Elsewhere")))) == 3
    rn.sync_run(store, cfg())
    assert titles(store) == sorted(ALL + ["The Old Garden"])
    assert len(names(server, rn.folder_url(cfg()))) == 4


def test_with_folders_the_books_folder_is_not_one_of_them():
    server, store = with_books()
    on = dict(cfg(), folders=True)
    server.dirs.add(rn.folder_url(cfg()) + "Work/")
    FakeDav(server).put(rn.folder_url(cfg()) + "Work/Agenda.txt", "Agenda\nmonday")
    dirs = set(server.dirs)
    assert rn.sync_run(store, on) == (0, 2, 0)
    assert store.folder_names() == ["Work"] and store.folders_state()[1] == []
    assert len(book_notes(store)) == 1
    # no folder of that name can be made, and the user's folder machinery leaves it alone
    assert store.add_folder(rn.BOOKS_FOLDER) is None and store.rename_folder("Work", rn.BOOKS_FOLDER) is None
    assert store.rename_folder(rn.BOOKS_FOLDER, "Mine") is None
    store.delete_folder(rn.BOOKS_FOLDER)
    assert rn.sync_run(store, on) == (0, 0, 0)
    assert len(book_notes(store)) == 1 and store.folder_names() == ["Work"] and server.dirs == dirs
    # an index of a version that took it for a folder
    store.folders.append({"name": rn.BOOKS_FOLDER, "onServer": True})
    store._save_index()
    again = rn.Store(os.path.dirname(store.index_file))
    assert again.folder_names() == ["Work"]



# ---- pictures (docs/PICTURES.md) ---------------------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n fake drawing"


def pictures_url():
    return rn.folder_url(cfg()) + ".pictures/"


def note_with_picture(store, name="drawing-20261104-093012-a3f9.png", data=PNG, title="Plan"):
    store.save_picture(name, data)
    return store.create(title + "\n" + rn.picture_line(name) + "\nafter")


def test_picture_line_rule():
    assert rn.picture_of_line(" ![](.pictures/drawing-20261104-093012-a3f9.png) ") == "drawing-20261104-093012-a3f9.png"
    assert rn.picture_of_line("![a cat](.pictures/x.JPG)") == "x.JPG"
    for no in ("![](pictures/x.png)", "![](.pictures/../x.png)", "![](.pictures/x.gif)", "text ![](.pictures/x.png)", "![](.pictures/.x.png)"):
        assert rn.picture_of_line(no) is None, no
    text = "![](.pictures/a.png)\n\nTitle\n![](.pictures/b.jpg)\nmore"
    assert rn.title_of(text) == "Title" and rn.file_name_of(text) == "Title.txt"
    assert rn.pictures_of(text) == ["a.png", "b.jpg"]
    assert rn.plain_text(text) == "\nTitle\nmore"
    assert rn.file_name_of("![](.pictures/a.png)") == "untitled.txt"
    n = rn.new_picture_name("drawing")
    assert rn.picture_of_line(rn.picture_line(n)) == n and n.endswith(".png") and rn.picture_kind(n) == "drawing"
    assert rn.new_picture_name("picture").endswith(".jpg")


def test_picture_preview_skips_the_line():
    _server, store = setup(())
    nid = store.create("Plan\n![](.pictures/a.png)\nthe second line")
    assert store.preview(nid) == "the second line"


def test_a_picture_goes_up_with_its_note():
    server, store = setup(())
    note_with_picture(store)
    up, _down, _del = rn.sync_run(store, cfg())
    assert up == 2      # the note and its picture
    assert server.files[pictures_url() + "drawing-20261104-093012-a3f9.png"][0] == PNG
    assert rn.sync_run(store, cfg()) == (0, 0, 0)     # nothing twice


def test_no_pictures_no_folder():
    server, store = setup()
    rn.sync_run(store, cfg())
    assert pictures_url() not in server.dirs


def test_a_picture_comes_down_to_another_computer():
    server, store = setup(())
    note_with_picture(store)
    rn.sync_run(store, cfg())
    other = rn.Store(tempfile.mkdtemp(prefix="notes-test-"))
    _up, down, _d = rn.sync_run(other, cfg())
    assert down == 2 and other.picture_bytes("drawing-20261104-093012-a3f9.png") == PNG


def test_a_picture_not_sent_yet_is_no_error():
    server, store = setup(())
    store.create("Plan\n" + rn.picture_line("picture-20261104-093012-0000.jpg"))   # its file is elsewhere
    server.dirs.add(rn.folder_url(cfg()))
    server.dirs.add(pictures_url())
    assert rn.sync_run(store, cfg()) == (1, 0, 0)
    assert not store.has_picture("picture-20261104-093012-0000.jpg")
    FakeDav(server).put_bytes(pictures_url() + "picture-20261104-093012-0000.jpg", b"jpeg", "image/jpeg")
    assert rn.sync_run(store, cfg()) == (0, 1, 0)
    assert store.picture_bytes("picture-20261104-093012-0000.jpg") == b"jpeg"


def test_a_picture_nobody_holds_leaves_the_server_after_two_days():
    server, store = setup(())
    nid = note_with_picture(store)
    rn.sync_run(store, cfg())
    url = pictures_url() + "drawing-20261104-093012-a3f9.png"
    store.save(nid, "Plan\nno more picture")
    rn.sync_run(store, cfg())
    assert url in server.files                    # still young: another device may be on its way
    server.mtime[url] -= 3 * 24 * 3600 * 1000
    rn.sync_run(store, cfg())
    assert url not in server.files


def test_a_picture_without_a_date_is_kept():
    server, store = setup(())
    nid = note_with_picture(store)
    rn.sync_run(store, cfg())
    url = pictures_url() + "drawing-20261104-093012-a3f9.png"
    server.mtime[url] = 0
    store.save(nid, "Plan")
    rn.sync_run(store, cfg())
    assert url in server.files


def test_a_picture_removed_there_is_sent_again():
    server, store = setup(())
    note_with_picture(store)
    rn.sync_run(store, cfg())
    url = pictures_url() + "drawing-20261104-093012-a3f9.png"
    del server.files[url]
    assert rn.sync_run(store, cfg()) == (1, 0, 0)
    assert server.files[url][0] == PNG


def test_a_picture_failure_does_not_fail_the_notes():
    server, store = setup(())
    note_with_picture(store)
    real = FakeDav.put_bytes
    FakeDav.put_bytes = lambda *a, **k: (_ for _ in ()).throw(rn.WebDavError("refused"))
    try:
        assert rn.sync_run(store, cfg()) == (1, 0, 0)
    finally:
        FakeDav.put_bytes = real
    assert rn.sync_run(store, cfg()) == (1, 0, 0)    # next time it goes


def test_unused_pictures_here_go_after_two_days():
    _server, store = setup(())
    nid = note_with_picture(store)
    store.save_picture("picture-20261101-000000-beef.jpg", b"old")
    old = time.time() - 3 * 24 * 3600
    for n in ("picture-20261101-000000-beef.jpg", "drawing-20261104-093012-a3f9.png"):
        os.utime(store.picture_path(n), (old, old))
    store.save_picture("picture-20261104-000000-cafe.jpg", b"new")     # young
    assert store.forget_unused_pictures() == 1
    assert store.local_pictures() == {"drawing-20261104-093012-a3f9.png", "picture-20261104-000000-cafe.jpg"}
    store.delete(nid)
    assert store.forget_unused_pictures() == 1

if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn(); print("ok  ", name)
            except AssertionError as e:
                failed += 1; print("FAIL", name, e)
    sys.exit(1 if failed else 0)
