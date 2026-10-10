# Reader's Notes (desktop)

One list, one page, black and white: a note is a `.txt` file whose first line is its title.
Optional two-way sync with your own WebDAV folder (kDrive, Nextcloud…), the same one as
[Reader's Notes](https://github.com/funkypitt/readers-notes) for Android, of which this is the
desktop twin. No formatting, no folders, no account with the app.

## Key points

- Type on the empty page or press Ctrl+N to start a note; an empty note is dropped when you leave it.
- Ctrl+F finds in the whole text (Enter opens the first match, Esc clears); Alt+Up / Alt+Down move between notes; right click or ⋯ deletes.
- Sync: enter the same server, username, password and folder (`Notes` by default) as on the phone, in the settings (Ctrl+,). kDrive: `https://<ID>.connect.kdrive.infomaniak.com`.
- It syncs when the window opens, every two minutes, 20 seconds after you stop typing, when you change note or window, on quitting, and on F5. The status line says what happened.
- A note changed on both sides keeps the server's text as a second note ("… (server copy)"). Nothing is overwritten without a copy.
- A book's highlights, written by Reader's Books into the `Reader's Books` subfolder of the notes folder, show here as notes to read and copy from, under « books » when the notes are filed in folders. They follow the server and are never changed from here.
- Without a server the notes stay on this computer: `~/.local/share/readers-notes/` on Linux, settings in `~/.config/readers-notes/config.json`, readable by you only.
- A new computer: *export credentials…* writes a JSON file that Reader's Calendar, Tasks and Notes share; *import credentials…* reads it back. It holds passwords in clear: delete it once imported.
- Ctrl+T flips white on black / black on white; Ctrl+= and Ctrl+- change the text size.
- English, French, German, Spanish, Portuguese and Russian, following the system language.

More detail: [docs/NOTES.md](docs/NOTES.md).

## Install

- Debian, Ubuntu, Pop!_OS: add the [apt repository](https://funkypitt.github.io/apt-repo/), then `sudo apt install readers-notes`. Or take the `.deb` from the [latest release](https://github.com/funkypitt/readers-notes-desktop/releases/latest): `sudo apt install ./readers-notes_*_all.deb`.
- Arch, Manjaro: `git clone https://github.com/funkypitt/readers-notes-desktop && cd readers-notes-desktop/packaging && makepkg -si`.
- Windows (`.exe`) and macOS (`.dmg`, `apple-silicon` or `intel`): from the latest release. They are unsigned: on Windows *More info* › *Run anyway*, on macOS right click on the app › *Open* the first time.
- Anywhere else: `python3 readers_notes.py` with PyQt5 and requests installed.

## Build

`packaging/build-deb.sh` builds the .deb. The Windows and macOS binaries are built by GitHub Actions
at every `v*` tag. Single file, PyQt5 + requests, no WebDAV library.

## Crédits / Credits

© 2026 Pierre Gallaz. Développé avec [Claude Code](https://claude.com/claude-code) (Anthropic).
Licence MIT, voir `LICENSE`.

© 2026 Pierre Gallaz. Developed with [Claude Code](https://claude.com/claude-code) (Anthropic).
MIT licence, see `LICENSE`.
