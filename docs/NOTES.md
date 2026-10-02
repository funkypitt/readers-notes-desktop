# Reader's Notes (desktop) — notes

Reference material moved out of the README.

## Sync with the phone

Both apps keep the notes in the same WebDAV folder, one `.txt` file per note, so enter the
same four things as in the Android app's settings (Ctrl+, here):

- **server** — kDrive: `https://<ID>.connect.kdrive.infomaniak.com` (the ID is the number in
  the kDrive web address); Nextcloud and other servers take their usual WebDAV address
- **username** — your Infomaniak login
- **password** — an application password when two-factor authentication is on
- **folder on the server** — `Notes` unless you changed it on the phone

The sync is the phone's, file for file. Etags decide who moved: a note changed here and
untouched there is uploaded; changed there and untouched here is downloaded; changed on both
sides keeps the server's text as a second note ("… (server copy)") and uploads yours. Deleted
here, deleted there, unless the other side changed it since. Nothing is ever overwritten
without a copy.

It runs when the window opens, every two minutes, 20 seconds after you stop typing, when you
move to another note, when you switch to another window, when you quit, and with F5. The
status line under the list says what happened ("synced 09:33 1↑ 2↓") or what went wrong.
A page open on screen follows the server when you are not typing in it.

Without a server the notes stay on this computer; the settings (password included) sit beside
them, readable by you only:

| | notes and settings |
|---|---|
| Linux | `~/.local/share/readers-notes/` and `~/.config/readers-notes/config.json` |
| Windows | `%APPDATA%\Readers Notes\` |
| macOS | `~/Library/Application Support/readers-notes/` |

## A new computer

The settings (Ctrl+,) › *export credentials…* writes the accounts (server, folder, username, password) into a JSON file. Reader's
Calendar, Tasks and Notes can all write into the same file, each in its own section. On the new
computer, *import credentials…* at the same place brings them back — or, before the first
window, `readers-notes --import-credentials readers-credentials.json` (and `--export-credentials FILE` the
other way). The look (colours, text size, font) stays out of it.

The file holds your passwords in clear and is written readable by you only: carry it on a USB key
or in your own cloud folder, not by e-mail, and delete it once imported.

## Windows and macOS: first opening

**Windows** — take the `.exe` from the
[latest release](https://github.com/funkypitt/readers-notes-desktop/releases/latest) and open it:
one file, nothing to install, no Python needed. The app is not signed by a paid certificate, so
Windows shows a blue "Windows protected your PC" panel the first time: *More info* › *Run anyway*.

**macOS** — take the `.dmg` for your Mac (`apple-silicon` for an M1 and later, `intel` for an
older one), open it and drag the app onto *Applications*. It is not signed by a paid Apple
certificate either, so the first opening must be a **right click on the app › Open** › *Open*; a
double click at that point says the app "cannot be opened" and offers nothing but the bin. Once
opened that way it starts normally ever after. If macOS still refuses, in a Terminal:
`xattr -dr com.apple.quarantine "/Applications/Readers Notes.app"`.

## Keys

| Key | Effect |
|---|---|
| type on the empty page | starts a note |
| Ctrl+N or "+ new note" | new note |
| Ctrl+F | find (in the whole text); Enter opens the first match, Esc clears |
| Alt+Up / Alt+Down | previous / next note |
| right click on a note, or ⋯ | delete |
| Ctrl+T | flip white on black / black on white |
| Ctrl+= / Ctrl+- | larger / smaller text |
| F5 or Ctrl+R | sync now |
| Ctrl+, or ⚙ | settings: server, folder, font |
| Ctrl+Q | quit |

An empty note is dropped when you leave it, as on the phone.

## Building

The .deb, on the machine itself:

```
packaging/build-deb.sh
```

The Windows and macOS binaries are built by GitHub, since neither can be built here:
`.github/workflows/desktop-builds.yml` runs PyInstaller on a Windows runner and on two macOS
runners at every `v*` tag and attaches the `.exe` and the two `.dmg` to the release of that tag.
*Actions* › *Windows and macOS builds* › *Run workflow* builds them without a tag, kept as
artifacts. The icons come from `packaging/readers-notes.png` (`.ico` beside it, `.icns` built on
the runner).

Single file, PyQt5 + requests, no WebDAV library: PROPFIND, GET, PUT, DELETE and MKCOL. MIT.

## Folders (1.3.0, optional, same as the phone 1.6.0)

Settings: « ranger les notes en dossiers » (`cfg["folders"]`). On: the left pane starts on the
folders (`place == FOLDERS`): « all notes », each folder with a small glyph and its count, « + new
folder »; a click opens one (the « ← … » line above the find field goes back); a note's
right-click has « move to »; a folder's: rename, delete. New notes go into the open folder.
Store/sync: `folder`/`remoteFolder` per note, `folders`/`goneFolders` in notes.json; sync keyed
"folder/name" — identical rules to the phone (see readers-notes docs/NOTES.md). Headless test:
`XDG_CONFIG_HOME=… XDG_DATA_HOME=… QT_QPA_PLATFORM=offscreen` and a wsgidav on 127.0.0.1:8085.

## Another server or folder (1.3.3, same as the phone 1.6.2)

notes.json remembers the folder URL the notes were last synced with (`place`). `sync_run` calls
`store.syncing_with(root)` once the place has answered: at another place than last time, however
it was set (the settings, `--import-credentials`, the configuration file edited by hand), every
note is treated as never synced, so all are kept and uploaded and none is taken for deleted there.
A never-synced note whose file is already there with the same text takes that file instead of a
second « … (2).txt » (a place left and come back to, or a computer set up next to the phone).
`tests/test_sync.py` runs the sync against a server kept in memory.
