"""« export as PDF »: a note with text, a picture and a picture not here yet becomes a real PDF.

    python3 tests/test_pdf.py        (offscreen; pdfinfo/pdftotext used when installed)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import readers_notes as rn  # noqa: E402
from PyQt5 import QtGui, QtWidgets  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
rn.load_bundled_fonts()

DRAWING = "drawing-20261104-093012-a3f9.png"
MISSING = "picture-20261104-093013-0000.jpg"


class PdfTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pics = os.path.join(self.dir, "pictures"); os.makedirs(self.pics)
        img = QtGui.QImage(800, 600, QtGui.QImage.Format_RGB32); img.fill(QtGui.QColor("white"))
        p = QtGui.QPainter(img); p.setPen(QtGui.QPen(QtGui.QColor("black"), 12)); p.drawEllipse(100, 100, 600, 400); p.end()
        img.save(os.path.join(self.pics, DRAWING))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_blocks_keep_the_order_and_take_the_title_out(self):
        heading, blocks = rn.pdf_blocks(f"\n Shopping \nmilk\n\nbread\n{rn.picture_line(DRAWING)}\nafter\n{rn.picture_line(MISSING)}")
        self.assertEqual("Shopping", heading)
        self.assertEqual([("words", "milk\n\nbread"), ("picture", DRAWING), ("words", "after"), ("picture", MISSING)], blocks)
        self.assertEqual(("", [("picture", DRAWING)]), rn.pdf_blocks(rn.picture_line(DRAWING)))

    def test_file_name(self):
        self.assertEqual("readers-notes-a b c.pdf", rn.pdf_file_name("a/b: c?"))
        self.assertEqual("readers-notes.pdf", rn.pdf_file_name(" // "))

    def test_a_note_with_pictures_becomes_a_pdf(self):
        long = "\n".join(f"Line {i}: the quick brown fox jumps over the lazy dog, again and again, until the page is full." for i in range(120))
        text = f"Été à Zürich\nFirst paragraph.\n\n{rn.picture_line(DRAWING)}\nBetween the pictures.\n{rn.picture_line(MISSING)}\n{long}\n#travel"
        path = os.path.join(self.dir, rn.pdf_file_name("Été à Zürich"))
        pages = rn.export_pdf(text, path, self.pics)
        self.assertGreater(pages, 1)
        with open(path, "rb") as f:
            data = f.read()
        self.assertTrue(data.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", data[-64:])
        self.assertFalse(os.path.exists(path + ".part"))
        if shutil.which("pdfinfo"):
            info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
            self.assertRegex(info, rf"Pages:\s+{pages}\n")
            self.assertIn("(A4)", info)
        if shutil.which("pdftotext"):
            out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
            self.assertIn("Été à Zürich", out)
            self.assertIn(rn._("picture on its way"), out)
            self.assertIn("Line 119", out)
            self.assertRegex(out, rf"1\s*/\s*{pages}")
            self.assertNotIn(".pictures/", out)
        if os.environ.get("KEEP_PDF"):
            shutil.copy(path, os.environ["KEEP_PDF"])

    def test_a_drawing_alone_is_titled_by_its_kind(self):
        path = os.path.join(self.dir, "d.pdf")
        self.assertEqual(1, rn.export_pdf(rn.picture_line(DRAWING), path, self.pics, heading_if_none="drawing"))
        if shutil.which("pdftotext"):
            self.assertIn("drawing", subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout)


if __name__ == "__main__":
    unittest.main()
