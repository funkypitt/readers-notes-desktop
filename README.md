# Reader's Notes (desktop)

Plain-text notes for the Linux desktop, black and white: the desktop twin of
[Reader's Notes](https://github.com/funkypitt/readers-notes) for Android, in the family of
[Reader's Tasks](https://github.com/funkypitt/readers-tasks) and
[Reader's Calendar](https://github.com/funkypitt/readers-calendar-desktop).

One window. The notes on the left (title, when it changed, the next line), the page on the
right. A note is a text file; its first line is its title. No formatting, no folders, no
colours. White on black or black on white.

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

Without a server the notes stay on this computer, in `~/.local/share/readers-notes/`; the
settings (password included) are in `~/.config/readers-notes/config.json`, readable by you only.

## A new computer

The settings (Ctrl+,) › *export credentials…* writes the accounts (server, folder, username, password) into a JSON file. Reader's
Calendar, Tasks and Notes can all write into the same file, each in its own section. On the new
computer, *import credentials…* at the same place brings them back — or, before the first
window, `readers-notes --import-credentials readers-credentials.json` (and `--export-credentials FILE` the
other way). The look (colours, text size, font) stays out of it.

The file holds your passwords in clear and is written readable by you only: carry it on a USB key
or in your own cloud folder, not by e-mail, and delete it once imported.

## Install

Debian, Ubuntu, Pop!_OS:

```
sudo apt install ./readers-notes_1.1.1_all.deb
```

Arch, Manjaro:

```
git clone https://github.com/funkypitt/readers-notes-desktop
cd readers-notes-desktop/packaging && makepkg -si
```

Anywhere else: `python3 readers_notes.py` with PyQt5 and requests installed.

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

## Languages

English, French, German, Spanish, Portuguese and Russian, following the system language
(`LANG`).

## Build the .deb

```
packaging/build-deb.sh
```

Single file, PyQt5 + requests, no WebDAV library: PROPFIND, GET, PUT, DELETE and MKCOL. MIT.

## Crédits / Credits

© 2026 Pierre Gallaz. Développé avec [Claude Code](https://claude.com/claude-code) (Anthropic).
Licence MIT, voir `LICENSE`.

© 2026 Pierre Gallaz. Developed with [Claude Code](https://claude.com/claude-code) (Anthropic).
MIT licence, see `LICENSE`.
