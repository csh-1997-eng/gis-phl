"""Shared utilities and result contracts for source probes."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen

USER_AGENT = "gis-phl-minimal-ingest/0.2"
TIMEOUT_SECONDS = 45


@dataclass
class FetchResult:
    name: str
    ok: bool
    details: Dict[str, object]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.title_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join(part.strip() for part in self.title_parts if part.strip())


def http_get_bytes(url: str, max_bytes: Optional[int] = None) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return resp.read() if max_bytes is None else resp.read(max_bytes)


def first_successful_url(urls: List[str], max_bytes: Optional[int] = None) -> tuple[str, bytes]:
    errors: List[str] = []
    for url in urls:
        try:
            return url, http_get_bytes(url, max_bytes=max_bytes)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url} -> {exc}")
    raise RuntimeError("All URL candidates failed: " + " | ".join(errors))


def scrape_links_from_html(base_url: str, html_text: str) -> List[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_text)
    return [urljoin(base_url, href) for href in hrefs]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_bytes(path: Path, content: bytes) -> None:
    ensure_dir(path.parent)
    path.write_bytes(content)


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
