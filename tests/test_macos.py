"""What a Mac opened from the Finder gets wrong without care: the month of a date in the
interface's language (no LANG, so the C library speaks English), ⌘ in the hints, and a server
whose certificate is not trusted, said so rather than « cannot reach the server ».

    python3 -m pytest tests/        (or: python3 tests/test_macos.py)
"""
import os
import sys
import unittest
from datetime import datetime
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests  # noqa: E402
import readers_notes as rn  # noqa: E402


def millis(d):
    return int(d.timestamp() * 1000)


class DatesTest(unittest.TestCase):
    def test_the_month_follows_the_interface_language(self):
        this_year = datetime.now().year
        for lang, month in (("en", "feb"), ("fr", "févr."), ("de", "feb."), ("ru", "февр.")):
            with mock.patch.object(rn, "_LANG", lang):
                self.assertEqual(f"3 {month}", rn.when_label(millis(datetime(this_year, 2, 3, 10))), lang)

    def test_another_year_is_written_after_the_month(self):
        with mock.patch.object(rn, "_LANG", "fr"):
            self.assertEqual("24 déc. 2025", rn.when_label(millis(datetime(2025, 12, 24, 10))))

    def test_a_language_without_a_translation_is_english(self):
        with mock.patch.object(rn, "_LANG", "it"):
            self.assertEqual("7 may 2025", rn.when_label(millis(datetime(2025, 5, 7, 10))))


class KeysTest(unittest.TestCase):
    def test_command_on_a_mac_ctrl_elsewhere(self):
        with mock.patch.object(rn.sys, "platform", "darwin"):
            self.assertEqual("réglages (⌘,)", rn.keys_text("réglages (Ctrl+,)"))
            self.assertEqual("Einstellungen (⌘,)", rn.keys_text("Einstellungen (Strg+,)"))
        with mock.patch.object(rn.sys, "platform", "linux"):
            self.assertEqual("settings (Ctrl+,)", rn.keys_text("settings (Ctrl+,)"))


class CertificateTest(unittest.TestCase):
    def failing(self, error):
        dav = rn.WebDav("u", "p")
        with mock.patch.object(dav.s, "request", side_effect=error):
            with self.assertRaises(rn.WebDavError) as e:
                dav._req("PROPFIND", "https://example.invalid/")
        return str(e.exception)

    def test_an_untrusted_certificate_is_named(self):
        with mock.patch.object(rn, "_LANG", "en"):
            self.assertIn("certificate is not trusted", self.failing(requests.exceptions.SSLError("x")))
            self.assertEqual("cannot reach the server", self.failing(requests.exceptions.ConnectionError("x")))

    def test_every_language_says_it(self):
        key = "the server's certificate is not trusted — check the address, or trust its certificate on this computer"
        for lang, table in rn._TR.items():
            self.assertIn(key, table, lang)


if __name__ == "__main__":
    unittest.main()
