"""The macOS build's Info.plist completed after PyInstaller: the version (PyInstaller writes 0.0.0),
and the oldest macOS the bundle can start on, read from its own binaries. Run before codesign.
usage: python packaging/macos-info.py "dist/Readers Notes.app" 1.9.1"""
import os
import plistlib
import re
import subprocess
import sys

MACHO = {b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}


def minimum_macos(app):
    """The highest minimum macOS among the bundle's Mach-O files (Python, Qt, the wheels): the
    Finder must refuse the app on an older Mac rather than let it vanish at its first import.
    An Intel build and an Apple silicon build may well differ."""
    best = (10, 13)
    for folder, _dirs, files in os.walk(app):
        for name in files:
            path = os.path.join(folder, name)
            if os.path.islink(path):
                continue
            try:
                with open(path, "rb") as f:
                    if f.read(4) not in MACHO:
                        continue
            except OSError:
                continue
            out = subprocess.run(["otool", "-arch", "all", "-l", path], capture_output=True, text=True).stdout
            # LC_BUILD_VERSION gives "minos 11.0", the older LC_VERSION_MIN_MACOSX "version 10.13"
            for m in re.finditer(r"cmd LC_BUILD_VERSION\n\s*cmdsize \d+\n\s*platform (\d+)\n\s*minos (\d+)\.(\d+)"
                                 r"|cmd LC_VERSION_MIN_MACOSX\n\s*cmdsize \d+\n\s*version (\d+)\.(\d+)", out):
                if m.group(1) is not None:
                    if m.group(1) != "1":            # 1 = macOS (not a simulator or iOS slice)
                        continue
                    v = (int(m.group(2)), int(m.group(3)))
                else:
                    v = (int(m.group(4)), int(m.group(5)))
                best = max(best, v)
    return "%d.%d" % best


app, version = sys.argv[1], sys.argv[2]
path = os.path.join(app, "Contents", "Info.plist")
with open(path, "rb") as f:
    info = plistlib.load(f)
info["CFBundleShortVersionString"] = version
info["CFBundleVersion"] = version
info["LSMinimumSystemVersion"] = minimum_macos(app)
with open(path, "wb") as f:
    plistlib.dump(info, f)
print("Info.plist:", version, "· macOS", info["LSMinimumSystemVersion"], "or later")
