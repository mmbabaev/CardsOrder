"""Извлечение HTML из разных форматов браузерных сохранений."""

import plistlib
from email import message_from_binary_file
from pathlib import Path


SUPPORTED_EXTENSIONS = {'.html', '.htm', '.txt', '.webarchive', '.mhtml', '.mht'}


def extract_html(path: Path) -> str:
    """
    Извлекает HTML из файла любого поддерживаемого формата.

    Поддерживаемые форматы:
    - .html, .htm, .txt  — читается напрямую
    - .webarchive        — Safari (macOS/iOS), plist-архив
    - .mhtml, .mht       — Chrome/Edge, multipart-архив

    Returns:
        HTML строка.

    Raises:
        ValueError: Если формат не поддерживается или HTML не найден внутри архива.
    """
    suffix = path.suffix.lower()

    if suffix in ('.html', '.htm', '.txt'):
        return path.read_text(encoding='utf-8', errors='ignore')

    if suffix == '.webarchive':
        return _extract_from_webarchive(path)

    if suffix in ('.mhtml', '.mht'):
        return _extract_from_mhtml(path)

    raise ValueError(f"Неподдерживаемый формат файла: {suffix}")


def _extract_from_webarchive(path: Path) -> str:
    with open(path, 'rb') as f:
        plist = plistlib.load(f)

    main = plist.get('WebMainResource', {})
    data = main.get('WebResourceData')
    if not data:
        raise ValueError("HTML не найден в .webarchive файле")

    encoding = main.get('WebResourceTextEncodingName') or 'utf-8'
    return data.decode(encoding, errors='ignore')


def _extract_from_mhtml(path: Path) -> str:
    with open(path, 'rb') as f:
        msg = message_from_binary_file(f)

    for part in msg.walk():
        if part.get_content_type() in ('text/html', 'text/xhtml+xml'):
            charset = part.get_content_charset() or 'utf-8'
            return part.get_payload(decode=True).decode(charset, errors='ignore')

    raise ValueError("HTML часть не найдена в .mhtml файле")
