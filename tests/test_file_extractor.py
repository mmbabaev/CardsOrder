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

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Неподдерживаемый формат"):
            extract_html(FIXTURES / "sample_cart.html.rename_me.pdf")

    def test_supported_extensions_set(self):
        assert {".html", ".htm", ".txt", ".webarchive", ".mhtml", ".mht"} == SUPPORTED_EXTENSIONS
