#!/bin/bash
# Builds readers-notes_<version>_all.deb next to this script. Needs dpkg-deb and fakeroot.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; SRC="$HERE/.."
VERSION=$(grep -oE '^VERSION = "[^"]+"' "$SRC/readers_notes.py" | cut -d'"' -f2)
ROOT="$HERE/deb-root"; rm -rf "$ROOT"
install -Dm755 "$SRC/readers_notes.py" "$ROOT/usr/lib/readers-notes/readers_notes.py"
install -Dm755 /dev/stdin "$ROOT/usr/bin/readers-notes" <<'SH'
#!/bin/sh
exec python3 /usr/lib/readers-notes/readers_notes.py "$@"
SH
install -Dm644 "$HERE/readers-notes.desktop" "$ROOT/usr/share/applications/readers-notes.desktop"
install -Dm644 "$HERE/readers-notes.svg" "$ROOT/usr/share/icons/hicolor/scalable/apps/readers-notes.svg"
install -Dm644 "$SRC/LICENSE" "$ROOT/usr/share/doc/readers-notes/copyright"
mkdir -p "$ROOT/DEBIAN"
cat > "$ROOT/DEBIAN/control" <<CTRL
Package: readers-notes
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-pyqt5, python3-requests
Maintainer: funkypitt <pierregallaz@gmail.com>
Homepage: https://github.com/funkypitt/readers-notes-desktop
Description: Black-and-white, plain-text notes synced over WebDAV
 A single-window desktop notebook: the notes on the left, the page on the
 right, one .txt file per note in a WebDAV folder (kDrive, Nextcloud...), in
 step with the Reader's Notes Android app. White on black or black on white.
CTRL
fakeroot dpkg-deb --build "$ROOT" "$HERE/readers-notes_${VERSION}_all.deb"
rm -rf "$ROOT"
echo "built $HERE/readers-notes_${VERSION}_all.deb"
