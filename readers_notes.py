#!/usr/bin/env python3
"""Reader's Notes — black-and-white, plain-text notes for the desktop, one .txt file per note in a
WebDAV folder (kDrive, Nextcloud…), in step with the Android app. One file, PyQt5 + requests.
MIT licence."""

import json
import locale
import os
import random
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote, unquote, urljoin, urlparse

import requests
from PyQt5 import QtCore, QtGui, QtWidgets

APP = "readers-notes"
VERSION = "1.1.0"
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), APP)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DATA_DIR = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), APP)
SYNC_MINUTES = 2          # while the window is open
IDLE_SYNC_SECONDS = 20    # after the last keystroke
SAVE_MS = 400             # typing pause before the file is written


# ------------------------------------------------------------------------------------------
# Six languages, the English text as the key (the launcher's languages: en, fr, de, es, pt, ru)
# ------------------------------------------------------------------------------------------

_TR = {
 "fr": {
  "+ new note": "+ nouvelle note",
  "new note": "nouvelle note",
  "untitled": "sans titre",
  "write here. The first line is the title.": "écrire ici. La première ligne est le titre.",
  "nothing yet. The first line of a note is its title.": "rien pour l'instant. La première ligne d'une note est son titre.",
  "nothing found": "rien trouvé",
  "find": "chercher",
  "sync now": "synchroniser",
  "on this computer only — Ctrl+, to set up a WebDAV folder": "sur cet ordinateur seulement — Ctrl+, pour configurer un dossier WebDAV",
  "delete": "supprimer",
  "delete this note": "supprimer cette note",
  "settings": "réglages",
  "settings (Ctrl+,)": "réglages (Ctrl+,)",
  "white on black": "blanc sur noir",
  "black on white": "noir sur blanc",
  "server": "serveur",
  "username": "identifiant",
  "password": "mot de passe",
  "folder on the server": "dossier sur le serveur",
  "font": "police",
  "cancel": "annuler",
  "save": "enregistrer",
  "syncing…": "synchronisation…",
  "synced %1": "synchronisé %1",
  "yesterday": "hier",
  "wrong username or password": "identifiant ou mot de passe incorrect",
  "cannot reach the server": "serveur injoignable",
  "not a WebDAV folder at this address": "pas de dossier WebDAV à cette adresse",
  "A WebDAV folder keeps the notes in step with your phone: the same server, folder and login as in the Android app. kDrive: server https://ID.connect.kdrive.infomaniak.com (the ID is the number in the kDrive web address), your Infomaniak login, and an application password if two-factor authentication is on. Nextcloud and any WebDAV server work the same way.": "Un dossier WebDAV garde les notes à jour avec le téléphone : les mêmes serveur, dossier et identifiants que dans l'app Android. kDrive : serveur https://ID.connect.kdrive.infomaniak.com (l'ID est le nombre dans l'adresse web de kDrive), votre identifiant Infomaniak et un mot de passe d'application si la double authentification est active. Nextcloud et tout serveur WebDAV fonctionnent de la même façon.",
  "Pierre Gallaz · developed with Claude Code": "Pierre Gallaz · développé avec Claude Code",
 },
 "de": {
  "+ new note": "+ neue Notiz",
  "new note": "neue Notiz",
  "untitled": "ohne Titel",
  "write here. The first line is the title.": "hier schreiben. Die erste Zeile ist der Titel.",
  "nothing yet. The first line of a note is its title.": "noch nichts. Die erste Zeile einer Notiz ist ihr Titel.",
  "nothing found": "nichts gefunden",
  "find": "suchen",
  "sync now": "jetzt synchronisieren",
  "on this computer only — Ctrl+, to set up a WebDAV folder": "nur auf diesem Computer — Strg+, um einen WebDAV-Ordner einzurichten",
  "delete": "löschen",
  "delete this note": "diese Notiz löschen",
  "settings": "Einstellungen",
  "settings (Ctrl+,)": "Einstellungen (Strg+,)",
  "white on black": "Weiß auf Schwarz",
  "black on white": "Schwarz auf Weiß",
  "server": "Server",
  "username": "Benutzername",
  "password": "Passwort",
  "folder on the server": "Ordner auf dem Server",
  "font": "Schrift",
  "cancel": "abbrechen",
  "save": "speichern",
  "syncing…": "synchronisiere…",
  "synced %1": "synchronisiert %1",
  "yesterday": "gestern",
  "wrong username or password": "falscher Benutzername oder falsches Passwort",
  "cannot reach the server": "Server nicht erreichbar",
  "not a WebDAV folder at this address": "kein WebDAV-Ordner unter dieser Adresse",
  "A WebDAV folder keeps the notes in step with your phone: the same server, folder and login as in the Android app. kDrive: server https://ID.connect.kdrive.infomaniak.com (the ID is the number in the kDrive web address), your Infomaniak login, and an application password if two-factor authentication is on. Nextcloud and any WebDAV server work the same way.": "Ein WebDAV-Ordner hält die Notizen mit dem Telefon gleich: derselbe Server, Ordner und Login wie in der Android-App. kDrive: Server https://ID.connect.kdrive.infomaniak.com (die ID ist die Zahl in der kDrive-Webadresse), Ihr Infomaniak-Login und bei Zwei-Faktor-Anmeldung ein App-Passwort. Nextcloud und jeder WebDAV-Server funktionieren genauso.",
  "Pierre Gallaz · developed with Claude Code": "Pierre Gallaz · entwickelt mit Claude Code",
 },
 "es": {
  "+ new note": "+ nueva nota",
  "new note": "nueva nota",
  "untitled": "sin título",
  "write here. The first line is the title.": "escribe aquí. La primera línea es el título.",
  "nothing yet. The first line of a note is its title.": "nada todavía. La primera línea de una nota es su título.",
  "nothing found": "nada encontrado",
  "find": "buscar",
  "sync now": "sincronizar ahora",
  "on this computer only — Ctrl+, to set up a WebDAV folder": "solo en este ordenador — Ctrl+, para configurar una carpeta WebDAV",
  "delete": "eliminar",
  "delete this note": "eliminar esta nota",
  "settings": "ajustes",
  "settings (Ctrl+,)": "ajustes (Ctrl+,)",
  "white on black": "blanco sobre negro",
  "black on white": "negro sobre blanco",
  "server": "servidor",
  "username": "usuario",
  "password": "contraseña",
  "folder on the server": "carpeta en el servidor",
  "font": "fuente",
  "cancel": "cancelar",
  "save": "guardar",
  "syncing…": "sincronizando…",
  "synced %1": "sincronizado %1",
  "yesterday": "ayer",
  "wrong username or password": "usuario o contraseña incorrectos",
  "cannot reach the server": "no se puede contactar con el servidor",
  "not a WebDAV folder at this address": "no hay una carpeta WebDAV en esta dirección",
  "A WebDAV folder keeps the notes in step with your phone: the same server, folder and login as in the Android app. kDrive: server https://ID.connect.kdrive.infomaniak.com (the ID is the number in the kDrive web address), your Infomaniak login, and an application password if two-factor authentication is on. Nextcloud and any WebDAV server work the same way.": "Una carpeta WebDAV mantiene las notas al día con tu teléfono: el mismo servidor, carpeta y usuario que en la app Android. kDrive: servidor https://ID.connect.kdrive.infomaniak.com (el ID es el número de la dirección web de kDrive), tu usuario de Infomaniak y una contraseña de aplicación si tienes la verificación en dos pasos. Nextcloud y cualquier servidor WebDAV funcionan igual.",
  "Pierre Gallaz · developed with Claude Code": "Pierre Gallaz · desarrollado con Claude Code",
 },
 "pt": {
  "+ new note": "+ nova nota",
  "new note": "nova nota",
  "untitled": "sem título",
  "write here. The first line is the title.": "escreva aqui. A primeira linha é o título.",
  "nothing yet. The first line of a note is its title.": "nada ainda. A primeira linha de uma nota é o seu título.",
  "nothing found": "nada encontrado",
  "find": "procurar",
  "sync now": "sincronizar agora",
  "on this computer only — Ctrl+, to set up a WebDAV folder": "só neste computador — Ctrl+, para configurar uma pasta WebDAV",
  "delete": "apagar",
  "delete this note": "apagar esta nota",
  "settings": "definições",
  "settings (Ctrl+,)": "definições (Ctrl+,)",
  "white on black": "branco sobre preto",
  "black on white": "preto sobre branco",
  "server": "servidor",
  "username": "utilizador",
  "password": "palavra-passe",
  "folder on the server": "pasta no servidor",
  "font": "tipo de letra",
  "cancel": "cancelar",
  "save": "guardar",
  "syncing…": "a sincronizar…",
  "synced %1": "sincronizado %1",
  "yesterday": "ontem",
  "wrong username or password": "utilizador ou palavra-passe incorretos",
  "cannot reach the server": "servidor inacessível",
  "not a WebDAV folder at this address": "nenhuma pasta WebDAV neste endereço",
  "A WebDAV folder keeps the notes in step with your phone: the same server, folder and login as in the Android app. kDrive: server https://ID.connect.kdrive.infomaniak.com (the ID is the number in the kDrive web address), your Infomaniak login, and an application password if two-factor authentication is on. Nextcloud and any WebDAV server work the same way.": "Uma pasta WebDAV mantém as notas em dia com o telefone: o mesmo servidor, pasta e utilizador que na app Android. kDrive: servidor https://ID.connect.kdrive.infomaniak.com (o ID é o número no endereço web do kDrive), o seu utilizador Infomaniak e uma palavra-passe de aplicação se tiver a verificação em dois passos. O Nextcloud e qualquer servidor WebDAV funcionam da mesma forma.",
  "Pierre Gallaz · developed with Claude Code": "Pierre Gallaz · desenvolvido com Claude Code",
 },
 "ru": {
  "+ new note": "+ новая заметка",
  "new note": "новая заметка",
  "untitled": "без названия",
  "write here. The first line is the title.": "пишите здесь. Первая строка — название.",
  "nothing yet. The first line of a note is its title.": "пока пусто. Первая строка заметки — её название.",
  "nothing found": "ничего не найдено",
  "find": "найти",
  "sync now": "синхронизировать",
  "on this computer only — Ctrl+, to set up a WebDAV folder": "только на этом компьютере — Ctrl+, чтобы настроить папку WebDAV",
  "delete": "удалить",
  "delete this note": "удалить эту заметку",
  "settings": "настройки",
  "settings (Ctrl+,)": "настройки (Ctrl+,)",
  "white on black": "белым по чёрному",
  "black on white": "чёрным по белому",
  "server": "сервер",
  "username": "имя пользователя",
  "password": "пароль",
  "folder on the server": "папка на сервере",
  "font": "шрифт",
  "cancel": "отмена",
  "save": "сохранить",
  "syncing…": "синхронизация…",
  "synced %1": "синхронизировано %1",
  "yesterday": "вчера",
  "wrong username or password": "неверное имя пользователя или пароль",
  "cannot reach the server": "сервер недоступен",
  "not a WebDAV folder at this address": "по этому адресу нет папки WebDAV",
  "A WebDAV folder keeps the notes in step with your phone: the same server, folder and login as in the Android app. kDrive: server https://ID.connect.kdrive.infomaniak.com (the ID is the number in the kDrive web address), your Infomaniak login, and an application password if two-factor authentication is on. Nextcloud and any WebDAV server work the same way.": "Папка WebDAV держит заметки в одном состоянии с телефоном: тот же сервер, папка и логин, что и в приложении Android. kDrive: сервер https://ID.connect.kdrive.infomaniak.com (ID — число в веб-адресе kDrive), ваш логин Infomaniak и пароль приложения при двухфакторной аутентификации. Nextcloud и любой WebDAV-сервер работают так же.",
  "Pierre Gallaz · developed with Claude Code": "Pierre Gallaz · разработано с Claude Code",
 },
}


def _lang():
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var)
        if v:
            return v[:2].lower()
    return "en"


_LANG = _lang()


def _(key, *args):
    s = _TR.get(_LANG, {}).get(key, key)
    for i, a in enumerate(args):
        s = s.replace("%" + str(i + 1), str(a))
    return s


# ------------------------------------------------------------------------------------------
# Notes on disk: the same model as the phone. One note = one text file, its first line the
# title; notes.json remembers each note's name and etag on the server, whether it changed
# since (dirty), and whether it was deleted here (a tombstone until the server knows).
# ------------------------------------------------------------------------------------------

_LINES = re.compile(r"\r\n|\n|\r")


def title_of(text):
    for line in _LINES.split(text):
        line = line.strip()
        if line:
            # the phone takes 80 UTF-16 units; count the same way so both name the file alike
            return line.encode("utf-16-le")[:160].decode("utf-16-le", "ignore")
    return ""


def file_name_of(text):
    """A file name the server, the phone and a desktop all accept (same rule as the phone)."""
    base = re.sub(r'[\\/:*?"<>|\x00-\x1f\x7f]', " ", title_of(text))
    base = re.sub(r"[ \t\n\x0b\f\r]+", " ", base).strip().rstrip(".")
    return (base or "untitled") + ".txt"


def server_copy_text(text):
    lines = text.split("\n")
    return lines[0] + " (server copy)" + "\n" + "\n".join(lines[1:])


def _new_id():
    n, digits, out = int(time.time() * 1000), "0123456789abcdefghijklmnopqrstuvwxyz", ""
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return out + str(random.randint(1000, 9999))


class Store:
    """Thread-safe: the sync runs off the UI thread. `on_change` is called after every change."""

    def __init__(self, root):
        self.dir = os.path.join(root, "notes")
        os.makedirs(self.dir, exist_ok=True)
        self.index_file = os.path.join(root, "notes.json")
        self.lock = threading.RLock()
        self.on_change = None
        self._texts = {}
        try:
            with open(self.index_file, encoding="utf-8") as f:
                self.notes = json.load(f).get("notes", [])
        except (OSError, ValueError):
            self.notes = []

    def _save_index(self):
        tmp = self.index_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"notes": self.notes}, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.index_file)
        if self.on_change:
            self.on_change()

    def _path(self, nid):
        return os.path.join(self.dir, nid + ".txt")

    def _write(self, nid, text):
        tmp = self._path(nid) + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, self._path(nid))
        self._texts[nid] = text

    def text(self, nid):
        with self.lock:
            if nid not in self._texts:
                try:
                    with open(self._path(nid), encoding="utf-8", newline="") as f:
                        self._texts[nid] = f.read()
                except (OSError, UnicodeDecodeError):
                    return ""
            return self._texts[nid]

    def all(self):
        with self.lock:
            return [dict(n) for n in self.notes]

    def get(self, nid):
        with self.lock:
            return next((dict(n) for n in self.notes if n["id"] == nid), None)

    def _find(self, nid):
        return next((n for n in self.notes if n["id"] == nid), None)

    def live(self):
        return sorted((n for n in self.all() if not n.get("deleted")), key=lambda n: -n["modified"])

    def title(self, nid):
        return title_of(self.text(nid))

    def preview(self, nid):
        lines = [l.strip() for l in _LINES.split(self.text(nid)) if l.strip()]
        return lines[1] if len(lines) > 1 else ""

    def _create(self, text, nid=None):
        nid = nid or _new_id()
        self._write(nid, text)
        self.notes.append({"id": nid, "modified": int(time.time() * 1000), "remoteName": None, "etag": None, "dirty": True, "deleted": False})
        return nid

    def create(self, text=""):
        with self.lock:
            nid = self._create(text)
            self._save_index()
            return nid

    def save(self, nid, text, base=None):
        """Called after a typing pause. `base` is the text the editor started from: if the file
        changed underneath (a sync brought the server's version meanwhile), that version is kept
        as a second note "… (server copy)", as the phone does. Returns that copy's id, or None."""
        with self.lock:
            n = self._find(nid)
            if n is None or n.get("deleted"):
                # removed meanwhile (on the server, by a sync): writing brings it back as a new note
                if not text.strip():
                    return None
                if n is not None:
                    self.notes.remove(n)
                self._create(text, nid)
                self._save_index()
                return None
            cur = self.text(nid)
            if cur == text:
                return None
            copy = None
            if base is not None and cur != base and cur.strip():
                copy = self._create(server_copy_text(cur))
            self._write(nid, text)
            n.update(modified=int(time.time() * 1000), dirty=True)
            self._save_index()
            return copy

    def delete(self, nid):
        with self.lock:
            n = self._find(nid)
            if n is None:
                return
            if not n.get("remoteName"):
                self._purge(nid)
            else:
                n.update(deleted=True, modified=int(time.time() * 1000))
            self._save_index()

    # ---- sync side --------------------------------------------------------------------

    def _purge(self, nid):
        try:
            os.remove(self._path(nid))
        except OSError:
            pass
        self._texts.pop(nid, None)
        self.notes = [n for n in self.notes if n["id"] != nid]

    def purge(self, nid, only_if_clean=False):
        with self.lock:
            n = self._find(nid)
            if n is None or (only_if_clean and n.get("dirty")):
                return
            self._purge(nid)
            self._save_index()

    def mark_synced(self, nid, remote_name, etag, uploaded):
        with self.lock:
            n = self._find(nid)
            if n is None:
                return
            # typed again while the upload ran: still dirty, it goes up next time
            n.update(remoteName=remote_name, etag=etag, dirty=self.text(nid) != uploaded)
            self._save_index()

    def apply_remote(self, nid, remote_name, etag, text, modified):
        """A file from the server, new here (nid None) or changed there. A note that changed
        here since the sync started is left alone: the next run sees both sides moved."""
        with self.lock:
            if nid is not None:
                n = self._find(nid)
                if n is None or n.get("dirty") or n.get("deleted"):
                    return None
                self._write(nid, text)
                n.update(modified=modified, remoteName=remote_name, etag=etag, dirty=False)
            else:
                nid = _new_id()
                self._write(nid, text)
                self.notes.append({"id": nid, "modified": modified, "remoteName": remote_name, "etag": etag, "dirty": False, "deleted": False})
            self._save_index()
            return nid

    def forget_server(self):
        """Another server or folder: every note goes up again as new."""
        with self.lock:
            for n in list(self.notes):
                if n.get("deleted"):
                    self._purge(n["id"])
            for n in self.notes:
                n.update(remoteName=None, etag=None, dirty=True)
            self._save_index()


# ------------------------------------------------------------------------------------------
# WebDAV: PROPFIND, GET, PUT, DELETE, MKCOL — the five requests a notes folder needs
# ------------------------------------------------------------------------------------------

class WebDavError(Exception):
    pass


def encode_segment(s):
    return quote(s, safe="")


def folder_url(cfg):
    folder = (cfg.get("folder") or "Notes").strip().strip("/") or "Notes"
    return cfg.get("server", "").strip().rstrip("/") + "/" + "/".join(encode_segment(p) for p in folder.split("/")) + "/"


class WebDav:
    def __init__(self, username, password, timeout=30):
        self.s = requests.Session()
        self.s.auth = (username, password)
        self.s.headers["User-Agent"] = f"{APP}/{VERSION}"
        self.timeout = (min(15, timeout), timeout)

    def _req(self, method, url, body=None, depth=None, headers=None, content_type="text/plain; charset=utf-8", allow=()):
        h = dict(headers or {})
        if depth is not None:
            h["Depth"] = str(depth)
        if body is not None:
            h["Content-Type"] = content_type
        try:
            r = self.s.request(method, url, data=body.encode("utf-8") if isinstance(body, str) else body, headers=h, timeout=self.timeout)
        except requests.RequestException:
            raise WebDavError(_("cannot reach the server"))
        if r.status_code == 401:
            raise WebDavError(_("wrong username or password"))
        if r.status_code >= 400 and r.status_code not in allow:
            raise WebDavError(f"{method}: HTTP {r.status_code}")
        return r

    @staticmethod
    def _etag(v):
        return v.strip().strip('"') if v else None

    def list(self, url):
        """The files directly inside the folder (the folder itself excluded)."""
        body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:getetag/><d:getlastmodified/><d:resourcetype/></d:prop></d:propfind>'
        r = self._req("PROPFIND", url, body, depth=1, content_type="application/xml; charset=utf-8")
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            raise WebDavError(_("not a WebDAV folder at this address"))
        here = unquote(urlparse(url).path).rstrip("/")
        out = []
        for resp in root.iter("{DAV:}response"):
            href = resp.findtext("{DAV:}href")
            if not href:
                continue
            path = unquote(urlparse(urljoin(url, href.strip())).path).rstrip("/")
            if path == here:
                continue
            modified = 0
            lm = resp.findtext(".//{DAV:}getlastmodified")
            if lm:
                try:
                    modified = int(parsedate_to_datetime(lm.strip()).timestamp() * 1000)
                except (TypeError, ValueError):
                    pass
            out.append({"name": path.rsplit("/", 1)[-1], "etag": self._etag(resp.findtext(".//{DAV:}getetag")),
                        "modified": modified, "dir": resp.find(".//{DAV:}resourcetype/{DAV:}collection") is not None})
        return out

    def get(self, url, allow_missing=False):
        r = self._req("GET", url, allow=(404,) if allow_missing else ())
        return None if r.status_code == 404 else r.content.decode("utf-8", "replace")

    def put(self, url, text):
        """The new etag when the server says it, otherwise asked with a PROPFIND."""
        r = self._req("PUT", url, text)
        etag = self._etag(r.headers.get("ETag"))
        if etag:
            return etag
        body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:getetag/></d:prop></d:propfind>'
        r = self._req("PROPFIND", url, body, depth=0, content_type="application/xml; charset=utf-8")
        try:
            return self._etag(ET.fromstring(r.content).findtext(".//{DAV:}getetag"))
        except ET.ParseError:
            return None

    def delete(self, url):
        self._req("DELETE", url, allow=(404,))

    def mkcol(self, url):
        self._req("MKCOL", url, allow=(405, 301))

    def exists(self, url):
        return self._req("PROPFIND", url, depth=0, allow=(404,)).status_code != 404


def _is_note(name):
    return name.lower().endswith((".txt", ".md"))


def sync_run(store, cfg, timeout=30):
    """Two-way sync of the folder, the phone's algorithm. Etags decide who moved: changed here and
    untouched there is uploaded; changed there and untouched here is downloaded; changed on both
    sides keeps the server's text as a second note ("… (server copy)") and uploads ours. Deleted
    here → deleted there unless it changed there since; deleted there → deleted here unless it
    changed here since. Anything new on either side crosses over. Returns (up, down, deleted)."""
    dav = WebDav(cfg.get("username", ""), cfg.get("password", ""), timeout)
    folder = folder_url(cfg)
    if not dav.exists(folder):
        dav.mkcol(folder)
    remote = {f["name"]: f for f in dav.list(folder) if not f["dir"] and _is_note(f["name"])}
    up = down = deleted = 0
    taken, gone = set(), set()

    for note in store.all():
        name0 = note.get("remoteName")
        r = remote.get(name0) if name0 else None
        if note.get("deleted"):
            if r is not None and (note.get("etag") is None or r["etag"] == note.get("etag")):
                dav.delete(folder + encode_segment(name0))
                gone.add(name0)
                deleted += 1
            store.purge(note["id"])   # changed on the server meanwhile: it comes back below as a new note
            continue
        text = store.text(note["id"])
        if note.get("dirty"):
            if not text.strip():
                continue              # a note being started on this desktop: nothing to send yet
            name = file_name_of(text)
            if name != name0:
                # a fresh name must not collide with another server file
                i, base = 2, name[:-4]
                while (name in remote and name0 != name) or name in taken:
                    name = f"{base} ({i}).txt"
                    i += 1
            taken.add(name)
            unchanged_there = r is None or note.get("etag") is None or r["etag"] == note.get("etag")
            if not unchanged_there:
                # both sides moved: keep theirs as a second note, ours takes the name
                theirs = dav.get(folder + encode_segment(name0))
                if theirs.strip() != text.strip():
                    store.create(server_copy_text(theirs))
                    down += 1
            if name0 and name0 != name and r is not None:
                dav.delete(folder + encode_segment(name0))
                gone.add(name0)
            etag = dav.put(folder + encode_segment(name), text)
            store.mark_synced(note["id"], name, etag, text)
            up += 1
        else:
            if not name0:
                continue
            if r is None:
                store.purge(note["id"], only_if_clean=True)
                deleted += 1
            elif r["etag"] != note.get("etag"):
                theirs = dav.get(folder + encode_segment(name0))
                store.apply_remote(note["id"], name0, r["etag"], theirs, r["modified"] or int(time.time() * 1000))
                down += 1
            taken.add(name0)

    known = {n.get("remoteName") for n in store.all() if n.get("remoteName")}
    for name, r in remote.items():
        if name in known or name in gone:
            continue
        theirs = dav.get(folder + encode_segment(name), allow_missing=True)
        if theirs is None:
            continue                  # vanished meanwhile
        store.apply_remote(None, name, r["etag"], theirs, r["modified"] or int(time.time() * 1000))
        down += 1
    return up, down, deleted


# ------------------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------------------

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG_FILE)

CREDENTIAL_KEYS = ('server', 'folder', 'username', 'password')


# ------------------------------------------------------------------------------------------
# Credentials file: the accounts of every Reader's desktop app in one JSON file, to set up a new
# computer in one step. One section per app; exporting adds or replaces this app's section and
# keeps the others, so Calendar, Tasks and Notes can share the same file. It holds passwords
# and tokens in clear: it is written readable by its owner only.
# ------------------------------------------------------------------------------------------

CREDENTIALS_FORMAT = "readers-credentials"

_CRED_TR = {
 "fr": {"import credentials…": "importer les identifiants…", "export credentials…": "exporter les identifiants…", "Reader's credentials (*.json)": "Identifiants Reader's (*.json)",
        "credentials exported to %1 — the file holds your passwords: keep it private": "identifiants exportés dans %1 — le fichier contient vos mots de passe : gardez-le privé",
        "credentials imported": "identifiants importés", "not a Reader's credentials file": "ce n'est pas un fichier d'identifiants Reader's", "this file holds nothing for %1": "ce fichier ne contient rien pour %1"},
 "de": {"import credentials…": "Zugangsdaten importieren…", "export credentials…": "Zugangsdaten exportieren…", "Reader's credentials (*.json)": "Reader's-Zugangsdaten (*.json)",
        "credentials exported to %1 — the file holds your passwords: keep it private": "Zugangsdaten nach %1 exportiert — die Datei enthält Ihre Passwörter: halten Sie sie privat",
        "credentials imported": "Zugangsdaten importiert", "not a Reader's credentials file": "keine Reader's-Zugangsdatendatei", "this file holds nothing for %1": "diese Datei enthält nichts für %1"},
 "es": {"import credentials…": "importar credenciales…", "export credentials…": "exportar credenciales…", "Reader's credentials (*.json)": "Credenciales Reader's (*.json)",
        "credentials exported to %1 — the file holds your passwords: keep it private": "credenciales exportadas a %1 — el archivo contiene sus contraseñas: manténgalo privado",
        "credentials imported": "credenciales importadas", "not a Reader's credentials file": "no es un archivo de credenciales Reader's", "this file holds nothing for %1": "este archivo no contiene nada para %1"},
 "pt": {"import credentials…": "importar credenciais…", "export credentials…": "exportar credenciais…", "Reader's credentials (*.json)": "Credenciais Reader's (*.json)",
        "credentials exported to %1 — the file holds your passwords: keep it private": "credenciais exportadas para %1 — o ficheiro contém as suas palavras-passe: mantenha-o privado",
        "credentials imported": "credenciais importadas", "not a Reader's credentials file": "não é um ficheiro de credenciais Reader's", "this file holds nothing for %1": "este ficheiro não contém nada para %1"},
 "ru": {"import credentials…": "импортировать учётные данные…", "export credentials…": "экспортировать учётные данные…", "Reader's credentials (*.json)": "Учётные данные Reader's (*.json)",
        "credentials exported to %1 — the file holds your passwords: keep it private": "учётные данные экспортированы в %1 — файл содержит ваши пароли: храните его в тайне",
        "credentials imported": "учётные данные импортированы", "not a Reader's credentials file": "это не файл учётных данных Reader's", "this file holds nothing for %1": "в этом файле нет ничего для %1"},
}
for _l, _d in _CRED_TR.items():
    _TR.setdefault(_l, {}).update(_d)


def export_credentials(cfg, path):
    """Write this app's accounts into the file at path (created, or merged into an existing
    credentials file)."""
    path = os.path.expanduser(path)
    data = {}
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except ValueError:
                raise ValueError(_("not a Reader's credentials file"))
        if not isinstance(data, dict) or data.get("format") != CREDENTIALS_FORMAT:
            raise ValueError(_("not a Reader's credentials file"))
    data.update({"format": CREDENTIALS_FORMAT, "version": 1})
    data[APP] = {k: cfg[k] for k in CREDENTIAL_KEYS if cfg.get(k) not in (None, "", [], {})}
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


def import_credentials(cfg, path):
    """Take this app's accounts from a credentials file into cfg (the look and the rest stay)."""
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        try:
            data = json.load(f)
        except ValueError:
            raise ValueError(_("not a Reader's credentials file"))
    if not isinstance(data, dict) or data.get("format") != CREDENTIALS_FORMAT:
        raise ValueError(_("not a Reader's credentials file"))
    section = data.get(APP)
    if not isinstance(section, dict) or not section:
        raise ValueError(_("this file holds nothing for %1", APP))
    for k in CREDENTIAL_KEYS:
        if k in section:
            cfg[k] = section[k]
    return cfg


def credentials_cli(argv):
    """readers-… --export-credentials FILE / --import-credentials FILE, without opening a window."""
    for flag in ("--export-credentials", "--import-credentials"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv):
                print(f"{flag} FILE", file=sys.stderr); sys.exit(2)
            path = argv[i + 1]
            cfg = load_config()
            try:
                if flag == "--export-credentials":
                    print(_("credentials exported to %1 — the file holds your passwords: keep it private", export_credentials(cfg, path)))
                else:
                    save_config(import_credentials(cfg, path)); print(_("credentials imported"))
            except (OSError, ValueError) as e:
                print(str(e), file=sys.stderr); sys.exit(1)
            sys.exit(0)


def credentials_dialog(parent, export, cfg):
    """The file picker for export (merging) or import. Returns (ok, message)."""
    title = _("export credentials…") if export else _("import credentials…")
    start = os.path.expanduser("~/readers-credentials.json")
    if export:
        path, _f = QtWidgets.QFileDialog.getSaveFileName(parent, title, start, _("Reader's credentials (*.json)"), options=QtWidgets.QFileDialog.DontConfirmOverwrite)
    else:
        path, _f = QtWidgets.QFileDialog.getOpenFileName(parent, title, os.path.dirname(start), _("Reader's credentials (*.json)"))
    if not path:
        return False, ""
    try:
        if export:
            return True, _("credentials exported to %1 — the file holds your passwords: keep it private", export_credentials(cfg, path))
        import_credentials(cfg, path)
        return True, _("credentials imported")
    except (OSError, ValueError) as e:
        return False, str(e)


def when_label(millis):
    d = datetime.fromtimestamp(millis / 1000)
    today = date.today()
    if d.date() == today:
        return d.strftime("%H:%M")
    if d.date() == today - timedelta(days=1):
        return _("yesterday")
    return f"{d.day} {d.strftime('%b' if d.year == today.year else '%b %Y')}".lower()


# ------------------------------------------------------------------------------------------
# UI
# ------------------------------------------------------------------------------------------

class Worker(QtCore.QObject):
    """Runs one job off the UI thread."""
    done = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.done.emit(self.fn())
        except Exception as e:  # network, auth, disk — all end up as one line of text
            self.failed.emit(str(e))


class Clickable(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def __init__(self, text="", name=None):
        super().__init__(text)
        if name:
            self.setObjectName(name)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()


class NoteDelegate(QtWidgets.QStyledItemDelegate):
    """A note in the list: the title, then a dim line with when it changed and the next line.
    The chosen note is drawn inverted, like every selection in the Reader's apps."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fg, self.bg = QtGui.QColor("#000"), QtGui.QColor("#fff")
        self.big, self.small = QtGui.QFont(), QtGui.QFont()

    def sizeHint(self, option, index):
        if index.data(QtCore.Qt.UserRole) is None:
            return QtCore.QSize(100, QtGui.QFontMetrics(self.small).height() * 3 + 24)
        return QtCore.QSize(100, QtGui.QFontMetrics(self.big).height() + QtGui.QFontMetrics(self.small).height() + 22)

    def paint(self, p, option, index):
        p.save()
        r = option.rect.adjusted(22, 10, -22, -10)
        sel = bool(option.state & QtWidgets.QStyle.State_Selected)
        fg, bg = (self.bg, self.fg) if sel else (self.fg, self.bg)
        p.fillRect(option.rect, bg)
        dim = QtGui.QColor(fg)
        dim.setAlphaF(0.6 if sel else 0.55)
        if index.data(QtCore.Qt.UserRole) is None:   # the empty-list message
            p.setFont(self.small)
            p.setPen(dim)
            p.drawText(r, QtCore.Qt.TextWordWrap | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, index.data(QtCore.Qt.DisplayRole))
            p.restore()
            return
        fb, fs = QtGui.QFontMetrics(self.big), QtGui.QFontMetrics(self.small)
        p.setFont(self.big)
        p.setPen(fg)
        p.drawText(QtCore.QRect(r.left(), r.top(), r.width(), fb.height()), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                   fb.elidedText(index.data(QtCore.Qt.DisplayRole), QtCore.Qt.ElideRight, r.width()))
        p.setFont(self.small)
        p.setPen(dim)
        p.drawText(QtCore.QRect(r.left(), r.top() + fb.height(), r.width(), fs.height()), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                   fs.elidedText(index.data(QtCore.Qt.UserRole + 1), QtCore.Qt.ElideRight, r.width()))
        p.restore()


class Editor(QtWidgets.QTextEdit):
    """The note: plain text on a reading column, the phone's generous line height."""

    def __init__(self):
        super().__init__()
        self.setAcceptRichText(False)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.column = 680

    def set_column(self, px):
        self.column = px
        self._margins()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._margins()

    def _margins(self):
        side = max(36, (self.width() - self.column) // 2)
        self.setViewportMargins(side, 22, side, 22)

    def insertFromMimeData(self, source):
        """Pasted text goes in as typed text, so its lines keep the page's line height."""
        if source.hasText():
            self.textCursor().insertText(source.text())

    def _spacing(self):
        c = QtGui.QTextCursor(self.document())
        c.select(QtGui.QTextCursor.Document)
        fmt = QtGui.QTextBlockFormat()
        fmt.setLineHeight(145, QtGui.QTextBlockFormat.ProportionalHeight)
        c.mergeBlockFormat(fmt)

    def load(self, text):
        self.setUndoRedoEnabled(False)
        self.setPlainText(text)
        self._spacing()
        self.setUndoRedoEnabled(True)


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("reader's notes")
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(16)
        intro = QtWidgets.QLabel(_("A WebDAV folder keeps the notes in step with your phone: the same server, folder and login as in the Android app. kDrive: server https://ID.connect.kdrive.infomaniak.com (the ID is the number in the kDrive web address), your Infomaniak login, and an application password if two-factor authentication is on. Nextcloud and any WebDAV server work the same way."))
        intro.setObjectName("dim")
        intro.setWordWrap(True)
        outer.addWidget(intro)
        form = QtWidgets.QFormLayout()
        form.setSpacing(12)
        outer.addLayout(form)
        self.server = QtWidgets.QLineEdit(cfg.get("server", ""))
        self.server.setPlaceholderText("https://123456.connect.kdrive.infomaniak.com")
        self.user = QtWidgets.QLineEdit(cfg.get("username", ""))
        self.password = QtWidgets.QLineEdit(cfg.get("password", ""))
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.folder = QtWidgets.QLineEdit(cfg.get("folder", "Notes"))
        form.addRow(_("server"), self.server)
        form.addRow(_("username"), self.user)
        form.addRow(_("password"), self.password)
        form.addRow(_("folder on the server"), self.folder)
        self.font = QtWidgets.QComboBox()
        for key, label in (("sans", "sans-serif"), ("serif", "serif"), ("mono", "mono")):
            self.font.addItem(label, key)
        self.font.setCurrentIndex(max(0, self.font.findData(cfg.get("font", "sans"))))
        form.addRow(_("font"), self.font)
        row = QtWidgets.QHBoxLayout()
        self.cfg = cfg
        for text, export in ((_("import credentials…"), False), (_("export credentials…"), True)):
            b = QtWidgets.QPushButton(text); b.setObjectName("quiet"); b.clicked.connect(lambda _c=False, x=export: self.credentials(x)); row.addWidget(b)
        row.addStretch(1)
        cancel = QtWidgets.QPushButton(_("cancel"))
        cancel.clicked.connect(self.reject)
        ok = QtWidgets.QPushButton(_("save"))
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(ok)
        outer.addLayout(row)
        self.message = QtWidgets.QLabel(""); self.message.setObjectName("dim"); self.message.setWordWrap(True); outer.addWidget(self.message)
        credits = QtWidgets.QLabel(f"reader's notes {VERSION} · " + _("Pierre Gallaz · developed with Claude Code"))
        credits.setObjectName("dim")
        outer.addWidget(credits)
        self.resize(680, 500)

    IMPORTED = 2

    def credentials(self, export):
        # an import lands in a copy: the window decides (a new server means every note goes up again)
        target = self.cfg if export else dict(self.cfg)
        ok, message = credentials_dialog(self, export, target)
        self.message.setText(message)
        if ok and not export:
            self.imported_cfg = target
            self.done(self.IMPORTED)

    def values(self):
        return {"server": self.server.text().strip(), "username": self.user.text().strip(),
                "password": self.password.text(), "folder": self.folder.text().strip().strip("/") or "Notes",
                "font": self.font.currentData()}


class Main(QtWidgets.QMainWindow):
    store_changed = QtCore.pyqtSignal()

    def __init__(self, store=None):
        super().__init__()
        self.cfg = load_config()
        self.store = store or Store(DATA_DIR)
        self.store.on_change = self.store_changed.emit     # from any thread: queued to the UI
        self.threads = []
        self.current = None      # id of the note in the editor
        self.base = ""           # its text when loaded or last saved
        self.pending = False     # typed, not yet written
        self.loading = False
        self.syncing = False
        self.sync_again = False
        self.setWindowTitle("reader's notes")
        self.resize(1080, 760)
        self.font_size = int(self.cfg.get("font_size", 13))
        self.dark = bool(self.cfg.get("dark", False))

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        outer = QtWidgets.QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left: find, the list, + new note, the status line
        self.left = QtWidgets.QWidget()
        self.left.setObjectName("left")
        left = QtWidgets.QVBoxLayout(self.left)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)
        self.find = QtWidgets.QLineEdit()
        self.find.setObjectName("find")
        self.find.setPlaceholderText(_("find"))
        self.find.textChanged.connect(self.refresh_list)
        self.find.installEventFilter(self)
        left.addWidget(self.find)
        self.list = QtWidgets.QListWidget()
        self.list.setObjectName("notes")
        self.list.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.delegate = NoteDelegate(self.list)
        self.list.setItemDelegate(self.delegate)
        self.list.currentItemChanged.connect(self.list_moved)
        self.list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.list_menu)
        left.addWidget(self.list, 1)
        self.new_row = Clickable(_("+ new note"), "newrow")
        self.new_row.clicked.connect(self.new_note)
        left.addWidget(self.new_row)
        bottom = QtWidgets.QHBoxLayout()
        bottom.setContentsMargins(22, 0, 16, 12)
        self.status = Clickable("", "dim")
        self.status.clicked.connect(lambda: self.sync() if self.configured() else self.setup())
        bottom.addWidget(self.status, 1)
        self.gear = Clickable("⚙", "dim")
        self.gear.setToolTip(_("settings (Ctrl+,)"))
        self.gear.clicked.connect(self.setup)
        bottom.addWidget(self.gear, 0)
        left.addLayout(bottom)
        outer.addWidget(self.left)
        vrule = QtWidgets.QFrame()
        vrule.setObjectName("sep")
        vrule.setFixedWidth(1)
        outer.addWidget(vrule)

        # Right: the note's title line with ⋯, a rule, the page
        right = QtWidgets.QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        head = QtWidgets.QHBoxLayout()
        head.setContentsMargins(36, 12, 24, 12)
        self.head = QtWidgets.QLabel("")
        self.head.setObjectName("dim")
        head.addWidget(self.head, 1)
        self.more = Clickable("⋯", "more")
        self.more.clicked.connect(self.show_menu)
        head.addWidget(self.more, 0)
        right.addLayout(head)
        rule = QtWidgets.QFrame()
        rule.setObjectName("sep")
        rule.setFixedHeight(1)
        right.addWidget(rule)
        self.editor = Editor()
        self.editor.setPlaceholderText(_("write here. The first line is the title."))
        self.editor.textChanged.connect(self.typed)
        right.addWidget(self.editor, 1)
        outer.addLayout(right, 1)

        self.save_timer = QtCore.QTimer(self, singleShot=True, interval=SAVE_MS, timeout=self.flush)
        self.idle_timer = QtCore.QTimer(self, singleShot=True, interval=IDLE_SYNC_SECONDS * 1000, timeout=self.sync_if_dirty)
        self.refresh_timer = QtCore.QTimer(self, singleShot=True, interval=0, timeout=self.after_change)
        self.store_changed.connect(self.refresh_timer.start)
        self.periodic = QtCore.QTimer(self, interval=SYNC_MINUTES * 60 * 1000, timeout=self.sync)
        self.periodic.start()

        for keys, fn in (("Ctrl+N", self.new_note), ("Ctrl+F", self.focus_find), ("Ctrl+T", self.toggle_theme),
                         ("F5", self.sync), ("Ctrl+R", self.sync), ("Ctrl+=", lambda: self.zoom(1)),
                         ("Ctrl++", lambda: self.zoom(1)), ("Ctrl+-", lambda: self.zoom(-1)), ("Ctrl+,", self.setup),
                         ("Alt+Up", lambda: self.step(-1)), ("Alt+Down", lambda: self.step(1)), ("Ctrl+Q", self.close)):
            QtWidgets.QShortcut(QtGui.QKeySequence(keys), self, fn)

        self.apply_style()
        self.refresh_list()
        live = self.store.live()
        last = self.cfg.get("last_note")
        start = last if any(n["id"] == last for n in live) else (live[0]["id"] if live else None)
        if start:
            self.open_note(start)
        self.editor.setFocus()
        self.update_status()
        if self.configured():
            QtCore.QTimer.singleShot(0, self.sync)
        elif not self.cfg.get("asked"):
            self.cfg["asked"] = True
            save_config(self.cfg)
            QtCore.QTimer.singleShot(0, self.setup)

    def configured(self):
        return bool(self.cfg.get("server"))

    # ---- look ------------------------------------------------------------------------

    def apply_style(self):
        bg, fg = ("#000000", "#ffffff") if self.dark else ("#ffffff", "#000000")
        dim = "rgba(255,255,255,0.55)" if self.dark else "rgba(0,0,0,0.55)"
        rule = "rgba(255,255,255,0.25)" if self.dark else "rgba(0,0,0,0.25)"
        s = self.font_size
        family = {"serif": "serif", "mono": "monospace"}.get(self.cfg.get("font"), "sans-serif")
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {bg}; color: {fg}; font-size: {s}pt; font-weight: 300; }}
            QLabel#dim {{ color: {dim}; }}
            QLabel#more {{ font-size: {s + 5}pt; padding: 0 6px; }}
            QLabel#newrow {{ font-size: {s + 1}pt; padding: 14px 22px; border-top: 1px solid {rule}; }}
            QFrame#sep {{ background: {rule}; }}
            QLineEdit#find {{ border: none; border-bottom: 1px solid {rule}; padding: 14px 22px; }}
            QListWidget#notes {{ background: {bg}; border: none; outline: none; padding: 6px 0; }}
            QTextEdit {{ background: {bg}; color: {fg}; border: none; font-family: "{family}"; font-size: {s + 3}pt;
                         selection-background-color: {fg}; selection-color: {bg}; }}
            QScrollBar:vertical {{ background: {bg}; width: 6px; }} QScrollBar::handle:vertical {{ background: {rule}; min-height: 24px; }}
            QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }} QScrollBar::add-page, QScrollBar::sub-page {{ background: {bg}; }}
            QMenu {{ background: {bg}; color: {fg}; border: 1px solid {rule}; padding: 4px 0; }}
            QMenu::item {{ padding: 6px 22px; }} QMenu::item:selected {{ background: {fg}; color: {bg}; }}
            QMenu::separator {{ height: 1px; background: {rule}; margin: 4px 0; }}
            QDialog QLineEdit, QComboBox {{ background: {bg}; color: {fg}; border: 1px solid {rule}; padding: 6px; }}
            QComboBox QAbstractItemView {{ background: {bg}; color: {fg}; selection-background-color: {fg}; selection-color: {bg}; }}
            QPushButton {{ background: {bg}; color: {fg}; border: 1px solid {fg}; padding: 6px 18px; }}
            QPushButton:default {{ background: {fg}; color: {bg}; }}
            QPushButton#quiet {{ border: none; color: {dim}; padding: 6px 4px; }}
            QToolTip {{ background: {bg}; color: {fg}; border: 1px solid {rule}; }}
        """)
        self.delegate.fg, self.delegate.bg = QtGui.QColor(fg), QtGui.QColor(bg)
        big = QtGui.QFont(family)
        big.setPointSize(s + 1)
        big.setWeight(QtGui.QFont.Light)
        small = QtGui.QFont(family)
        small.setPointSize(max(8, s - 2))
        small.setWeight(QtGui.QFont.Light)
        self.delegate.big, self.delegate.small = big, small
        self.left.setFixedWidth(max(280, s * 24))
        page = QtGui.QFont(family)
        page.setPointSize(s + 3)
        self.editor.set_column(QtGui.QFontMetrics(page).averageCharWidth() * 72)
        self.list.doItemsLayout()
        self.list.viewport().update()

    def toggle_theme(self):
        self.dark = not self.dark
        self.cfg["dark"] = self.dark
        save_config(self.cfg)
        self.apply_style()

    def zoom(self, delta):
        self.font_size = max(9, min(24, self.font_size + delta))
        self.cfg["font_size"] = self.font_size
        save_config(self.cfg)
        self.apply_style()

    # ---- the list ----------------------------------------------------------------------

    def refresh_list(self):
        q = self.find.text().strip().lower()
        notes = [n for n in self.store.live() if not q or q in self.store.text(n["id"]).lower()]
        mark = self.configured()
        self.list.blockSignals(True)
        self.list.clear()
        if not notes:
            item = QtWidgets.QListWidgetItem(_("nothing found") if q else _("nothing yet. The first line of a note is its title."))
            item.setFlags(QtCore.Qt.NoItemFlags)
            self.list.addItem(item)
        for n in notes:
            nid = n["id"]
            preview = self.store.preview(nid)
            sub = when_label(n["modified"]) + (f" · {preview}" if preview else "") + (" · ✎" if n.get("dirty") and mark else "")
            item = QtWidgets.QListWidgetItem(self.store.title(nid) or _("untitled"))
            item.setData(QtCore.Qt.UserRole, nid)
            item.setData(QtCore.Qt.UserRole + 1, sub)
            self.list.addItem(item)
            if nid == self.current:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)

    def list_moved(self, item, _prev):
        nid = item.data(QtCore.Qt.UserRole) if item else None
        if nid and nid != self.current:
            self.open_note(nid)

    def step(self, delta):
        row = self.list.currentRow() + delta
        if 0 <= row < self.list.count() and self.list.item(row).data(QtCore.Qt.UserRole):
            self.list.setCurrentRow(row)

    def list_menu(self, pos):
        item = self.list.itemAt(pos)
        nid = item.data(QtCore.Qt.UserRole) if item else None
        m = QtWidgets.QMenu(self)
        if nid:
            m.addAction(_("delete"), lambda: self.delete_note(nid))
        else:
            m.addAction(_("+ new note"), self.new_note)
        m.exec_(self.list.mapToGlobal(pos))

    def focus_find(self):
        self.find.setFocus()
        self.find.selectAll()

    def eventFilter(self, obj, e):
        if obj is self.find and e.type() == QtCore.QEvent.KeyPress:
            if e.key() == QtCore.Qt.Key_Escape:
                self.find.clear()
                self.editor.setFocus()
                return True
            if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Down):
                first = self.list.item(0)
                if first and first.data(QtCore.Qt.UserRole):
                    self.list.setCurrentRow(0)
                    self.list.setFocus() if e.key() == QtCore.Qt.Key_Down else self.editor.setFocus()
                return True
        return super().eventFilter(obj, e)

    # ---- the note ----------------------------------------------------------------------

    def open_note(self, nid):
        self.leave_note()
        self.current = nid
        self.loading = True
        text = self.store.text(nid)
        self.editor.load(text)
        self.loading = False
        self.base = text
        self.head.setText(title_of(text) or _("new note"))
        self.cfg["last_note"] = nid
        save_config(self.cfg)
        self.refresh_list()

    def leave_note(self):
        """An empty note is not worth keeping; a written one goes to the server."""
        if self.current is None:
            return
        self.flush()
        nid, self.current = self.current, None
        n = self.store.get(nid)
        if n and not n.get("deleted") and not self.store.text(nid).strip():
            self.store.delete(nid)
        self.sync_if_dirty()

    def typed(self):
        if self.loading:
            return
        text = self.editor.toPlainText()
        if self.current is None:
            if not text.strip():
                return
            self.current = self.store.create()   # typing on the empty page starts a note
            self.base = ""
            self.cfg["last_note"] = self.current
        self.pending = True
        self.head.setText(title_of(text) or _("new note"))
        self.save_timer.start()
        self.idle_timer.start()

    def flush(self):
        self.save_timer.stop()
        if not self.pending or self.current is None:
            return
        self.pending = False
        text = self.editor.toPlainText()
        self.store.save(self.current, text, self.base)
        self.base = text

    def new_note(self):
        self.leave_note()
        self.find.blockSignals(True)
        self.find.clear()
        self.find.blockSignals(False)
        self.open_note(self.store.create())
        self.editor.setFocus()

    def delete_note(self, nid):
        if nid == self.current:
            self.save_timer.stop()
            self.pending = False
            self.current = None
        self.store.delete(nid)
        if self.current is None:
            live = self.store.live()
            if live:
                self.open_note(live[0]["id"])
            else:
                self.loading = True
                self.editor.load("")
                self.loading = False
                self.head.setText("")
        self.sync()

    def after_change(self):
        """The store changed (typing, or a sync bringing the server's side): redraw the list and
        take the server's text into the page when nothing typed is waiting."""
        if self.current is not None and not self.pending:
            n = self.store.get(self.current)
            if n is None or n.get("deleted"):
                self.current = None     # deleted on the server
                live = self.store.live()
                if live:
                    self.open_note(live[0]["id"])
                else:
                    self.loading = True
                    self.editor.load("")
                    self.loading = False
                    self.head.setText("")
            else:
                text = self.store.text(self.current)
                if text != self.editor.toPlainText():
                    cursor = min(self.editor.textCursor().position(), len(text))
                    scroll = self.editor.verticalScrollBar().value()
                    self.loading = True
                    self.editor.load(text)
                    self.loading = False
                    c = self.editor.textCursor()
                    c.setPosition(cursor)
                    self.editor.setTextCursor(c)
                    self.editor.verticalScrollBar().setValue(scroll)
                    self.head.setText(title_of(text) or _("new note"))
                self.base = text
        elif self.current is None and not self.editor.toPlainText():
            live = self.store.live()   # the first sync brought notes to an empty page
            if live:
                self.open_note(live[0]["id"])
                return
        self.refresh_list()

    def show_menu(self):
        m = QtWidgets.QMenu(self)
        m.addAction(_("+ new note"), self.new_note)
        m.addAction(_("find"), self.focus_find)
        if self.configured():
            m.addAction(_("sync now"), self.sync)
        if self.current is not None:
            m.addSeparator()
            nid = self.current
            m.addAction(_("delete this note"), lambda: self.delete_note(nid))
        m.addSeparator()
        m.addAction(_("black on white") if self.dark else _("white on black"), self.toggle_theme)
        m.addAction(_("settings"), self.setup)
        m.exec_(self.more.mapToGlobal(QtCore.QPoint(self.more.width() - m.sizeHint().width(), self.more.height())))

    # ---- sync --------------------------------------------------------------------------

    def run(self, fn, on_done, on_failed):
        thread = QtCore.QThread(self)
        worker = Worker(fn)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(on_done)
        worker.failed.connect(on_failed)
        worker.done.connect(thread.quit)
        worker.failed.connect(thread.quit)
        # Keep both alive until the thread ends: a collected worker never runs its slot.
        pair = (thread, worker)
        thread.finished.connect(lambda: self.threads.remove(pair) if pair in self.threads else None)
        self.threads.append(pair)
        thread.start()

    def has_changes(self):
        return any((n.get("dirty") and self.store.text(n["id"]).strip()) or n.get("deleted") for n in self.store.all())

    def sync_if_dirty(self):
        self.flush()
        if self.configured() and self.has_changes():
            self.sync()

    def sync(self):
        if not self.configured():
            self.update_status()
            return
        if self.syncing:
            self.sync_again = True
            return
        self.flush()
        self.syncing = True
        self.status.setText(_("syncing…"))
        cfg = dict(self.cfg)
        self.run(lambda: sync_run(self.store, cfg), self.synced, self.sync_failed)

    def synced(self, result):
        self.syncing = False
        up, down, deleted = result
        arrows = "".join(f" {n}{a}" for n, a in ((up, "↑"), (down, "↓"), (deleted, "−")) if n)
        self.last_status = _("synced %1", datetime.now().strftime("%H:%M")) + arrows
        self.update_status()
        if self.sync_again:
            self.sync_again = False
            self.sync_if_dirty()

    def sync_failed(self, message):
        self.syncing = False
        self.last_status = message
        self.update_status()
        self.sync_again = False

    def update_status(self):
        if not self.configured():
            self.status.setText(_("on this computer only — Ctrl+, to set up a WebDAV folder"))
        else:
            self.status.setText(getattr(self, "last_status", ""))
        self.status.setToolTip(self.status.text())

    def setup(self):
        dlg = SettingsDialog(self.cfg, self)
        result = dlg.exec_()
        if result == SettingsDialog.IMPORTED:
            v = {"server": "", "folder": "Notes", "username": "", "password": ""}
            v.update({k: dlg.imported_cfg[k] for k in CREDENTIAL_KEYS if dlg.imported_cfg.get(k) is not None})
            v["font"] = self.cfg.get("font", "sans")
        elif result != QtWidgets.QDialog.Accepted:
            return
        else:
            v = dlg.values()
        moved = (v["server"].rstrip("/"), v["folder"]) != (self.cfg.get("server", "").rstrip("/"), self.cfg.get("folder", "Notes"))
        if moved and self.cfg.get("server"):
            self.flush()
            self.store.forget_server()
        self.cfg.update(v)
        save_config(self.cfg)
        self.last_status = ""
        self.apply_style()
        self.refresh_list()
        self.update_status()
        self.sync()

    # ---- window ------------------------------------------------------------------------

    def changeEvent(self, e):
        # leaving the window for another one: what was written goes to the server
        if e.type() == QtCore.QEvent.ActivationChange and not self.isActiveWindow():
            self.sync_if_dirty()
        super().changeEvent(e)

    def closeEvent(self, e):
        self.leave_note()
        save_config(self.cfg)
        for thread, _w in list(self.threads):
            thread.wait(15000)
        if self.configured() and self.has_changes():
            try:
                sync_run(self.store, self.cfg, timeout=10)
            except Exception:
                pass            # stays dirty on disk, goes up next time
        super().closeEvent(e)


def main():
    credentials_cli(sys.argv)
    try:
        locale.setlocale(locale.LC_TIME, "")
    except locale.Error:
        pass
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("reader's notes")
    app.setDesktopFileName(APP)
    w = Main()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
