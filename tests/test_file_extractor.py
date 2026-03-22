import shutil
import tempfile
import pytest
from pathlib import Path

from src.file_extractor import extract_html, SUPPORTED_EXTENSIONS

FIXTURES = Path("tests/fixtures")


class TestExtractHtml:
    def test_webarchive_returns_html(self):
        html = extract_html(FIXTURES / "sample_cart.webarchive")
        assert "<html" in html.lower() or "<!doctype" in html.lower()

    def test_webarchive_contains_cardkingdom(self):
        html = extract_html(FIXTURES / "sample_cart.webarchive")
        assert "cardkingdom" in html.lower()

    def test_mht_returns_html(self):
        html = extract_html(FIXTURES / "sample_cart.mht")
        assert "<html" in html.lower() or "<!doctype" in html.lower()

    def test_mht_contains_cardkingdom(self):
        html = extract_html(FIXTURES / "sample_cart.mht")
        assert "cardkingdom" in html.lower()

    def test_html_file_passthrough(self):
        html = extract_html(FIXTURES / "sample_cart.html")
        assert "<html" in html.lower() or "<!doctype" in html.lower()

    def test_unrecognized_content_raises(self):
        tmp = Path(tempfile.mktemp())
        tmp.write_bytes(b"this is not html or any archive format")
        try:
            with pytest.raises(ValueError):
                extract_html(tmp)
        finally:
            tmp.unlink()

    def test_supported_extensions_set(self):
        assert {".html", ".htm", ".txt", ".webarchive", ".mhtml", ".mht"} == SUPPORTED_EXTENSIONS


class TestContentDetection:
    """Tests for format detection when Telegram strips the file extension."""

    def _copy_without_extension(self, src: Path) -> Path:
        tmp = Path(tempfile.mktemp())
        shutil.copy(src, tmp)
        return tmp

    def test_webarchive_no_extension(self):
        tmp = self._copy_without_extension(FIXTURES / "sample_cart.webarchive")
        try:
            html = extract_html(tmp)
            assert "cardkingdom" in html.lower()
        finally:
            tmp.unlink()

    def test_mht_no_extension(self):
        tmp = self._copy_without_extension(FIXTURES / "sample_cart.mht")
        try:
            html = extract_html(tmp)
            assert "cardkingdom" in html.lower()
        finally:
            tmp.unlink()

    def test_html_no_extension(self):
        tmp = self._copy_without_extension(FIXTURES / "sample_cart.html")
        try:
            html = extract_html(tmp)
            assert "<html" in html.lower() or "<!doctype" in html.lower()
        finally:
            tmp.unlink()
