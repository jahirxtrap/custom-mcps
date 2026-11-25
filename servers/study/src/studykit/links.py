"""Reference links opened on the live web, with an archived copy for each one that does not answer."""
from __future__ import annotations

import http.client
import ipaddress
import json
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

_URL = re.compile(r"https?://[^\s<>\"'`]+")
_DOI = re.compile(r"\bdoi\s*[=:]\s*\{?\s*(10\.\d{4,9}/[^\s}\"']+)", re.IGNORECASE)
_TRAILING = ".,;:!?)]}*>»"
_TEXT_EXT = (".bib", ".md", ".txt", ".py", ".json", ".html", ".tex", ".rst")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist"}
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
_SAFE = ":/?#[]@!$&'()*+,;=%~"
_SCHEMES = {"http", "https"}
_HOST = re.compile(r"^[A-Za-z0-9.\-]+$|^[0-9A-Fa-f:.]+$")
_SECRET_WORDS = ("token", "key", "sig", "auth", "pass", "pwd", "secret", "credential", "jwt", "session", "x-amz-")
_SECRET_NAMES = {"code", "sid"}
_DOI_HOSTS = {"doi.org", "dx.doi.org", "www.doi.org"}
_HANDLE = "https://doi.org/api/handles/"
_HANDLE_FOUND = 1
_TIMEOUT = 12
_ARCHIVE_TIMEOUT = 25
_WORKERS = 8
_LIMIT = 150
_WHERE = 5
_CDX = "https://web.archive.org/cdx/search/cdx"
_ARCHIVE = "https://web.archive.org/web/{timestamp}/{url}"
_ATTEMPTS = 2
_SSL = ssl.create_default_context()


def _clean(raw: str) -> str:
    url = raw
    while url and url[-1] in _TRAILING:
        if url[-1] == ")" and url.count("(") >= url.count(")"):
            break
        url = url[:-1]
    return url


def extract_urls(text: str) -> list[str]:
    """Every distinct URL in the text, in order of appearance, DOIs resolved to doi.org links."""
    found: list[str] = []
    for match in _URL.finditer(text):
        url = _clean(match.group(0))
        if url and url not in found:
            found.append(url)
    for match in _DOI.finditer(text):
        url = f"https://doi.org/{_clean(match.group(1))}"
        if url not in found:
            found.append(url)
    return found


def _files(base: Path):
    if base.is_file():
        yield base
        return
    for entry in sorted(base.rglob("*")):
        parts = entry.relative_to(base).parts
        if entry.is_file() and entry.suffix.lower() in _TEXT_EXT and not any(part in _SKIP_DIRS for part in parts):
            yield entry


def _global(sockaddr: tuple) -> bool:
    return ipaddress.ip_address(sockaddr[0].split("%")[0]).is_global


def _public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True
    return all(_global(info[4]) for info in infos)


def _blocked(url: str) -> str | None:
    """Why a URL is never opened: a non-http(s) scheme, credentials in it, or a non-public host."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in _SCHEMES:
        return "not an http(s) URL"
    if parsed.username or parsed.password:
        return "carries credentials"
    host = parsed.hostname or ""
    if not host or not _HOST.match(host):
        return "no valid host"
    if not _public(host):
        return "not a public host"
    return None


def _bare(url: str) -> str:
    return urllib.parse.urlsplit(url)._replace(fragment="").geturl()


def _secret(url: str) -> bool:
    query = urllib.parse.urlsplit(url).query.replace(";", "&")
    names = [name.lower() for name, _ in urllib.parse.parse_qsl(query, keep_blank_values=True)]
    return any(name in _SECRET_NAMES or any(word in name for word in _SECRET_WORDS) for name in names)


class _Vetted:
    """A connection that resolves once, refuses any non-public address and connects to the vetted one."""

    def connect(self) -> None:
        infos = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        if not infos:
            raise OSError("dns")
        if not all(_global(info[4]) for info in infos):
            raise OSError("not a public host")
        family, kind, proto, _, sockaddr = infos[0]
        sock = socket.socket(family, kind, proto)
        sock.settimeout(self.timeout)
        sock.connect(sockaddr)
        self.sock = sock


class _VettedHTTP(_Vetted, http.client.HTTPConnection):
    pass


class _VettedHTTPS(_Vetted, http.client.HTTPSConnection):
    def connect(self) -> None:
        super().connect()
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


class _HTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_VettedHTTP, req)


class _HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_VettedHTTPS, req, context=self._context)


def _shown(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if not parsed.username and not parsed.password:
        return url
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urllib.parse.urlunsplit(parsed._replace(netloc=netloc))


class _Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if _blocked(newurl):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_Redirects(), _HTTPHandler(), _HTTPSHandler(context=_SSL))


def _reason(error: object) -> str:
    if isinstance(error, (socket.timeout, TimeoutError)) or "timed out" in str(error):
        return "timeout"
    if isinstance(error, socket.gaierror):
        return "dns"
    if isinstance(error, ConnectionRefusedError):
        return "connection refused"
    return str(error)[:80]


def _open(url: str, timeout: int, accept: str = "*/*"):
    request = urllib.request.Request(
        urllib.parse.quote(url, safe=_SAFE), headers={"User-Agent": _USER_AGENT, "Accept": accept}
    )
    return _OPENER.open(request, timeout=timeout)


def _doi_of(url: str) -> str | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.netloc.lower() in _DOI_HOSTS and parsed.path.strip("/"):
        return parsed.path.strip("/")
    return None


def _failure(error: Exception) -> str:
    return _reason(error.reason) if isinstance(error, urllib.error.URLError) else _reason(error)


def _retry(fetch, fallback):
    """Run fetch once more after a non-timeout connection failure; fallback renders the last reason."""
    for attempt in range(_ATTEMPTS):
        try:
            return fetch()
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, OSError, ValueError) as error:
            reason = _failure(error)
            if attempt + 1 == _ATTEMPTS or reason == "timeout":
                return fallback(reason)
    return fallback("unreachable")


def _handle(doi: str) -> dict[str, Any]:
    def fetch() -> dict[str, Any]:
        with _open(_HANDLE + doi, _TIMEOUT, "application/json") as response:
            data = json.loads(response.read().decode("utf-8", "replace") or "{}")
        if data.get("responseCode") != _HANDLE_FOUND:
            return {"status": 404, "type": "doi", "error": "DOI not registered"}
        target = next((item["data"]["value"] for item in data.get("values", []) if item.get("type") == "URL"), None)
        return {"status": 200, "type": "doi", "final": target}

    try:
        return _retry(fetch, lambda reason: {"status": None, "type": "doi", "error": reason})
    except urllib.error.HTTPError as error:
        return {"status": error.code, "type": "doi", "error": "DOI not registered"}


def _status(url: str) -> dict[str, Any]:
    doi = _doi_of(url)
    if doi:
        return _handle(doi)

    def fetch() -> dict[str, Any]:
        with _open(url, _TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "")
            return {"status": response.status, "type": content_type.split(";")[0], "final": _shown(response.geturl())}

    try:
        return _retry(fetch, lambda reason: {"status": None, "error": reason})
    except urllib.error.HTTPError as error:
        content_type = error.headers.get("Content-Type", "") if error.headers else ""
        return {"status": error.code, "type": content_type.split(";")[0], "final": _shown(error.geturl())}


def _cdx(url: str) -> list[list[str]]:
    query = urllib.parse.urlencode(
        {"url": url, "output": "json", "fl": "timestamp,statuscode", "filter": "statuscode:200", "limit": "-1"}
    )
    with _open(f"{_CDX}?{query}", _ARCHIVE_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8", "replace") or "[]")


def _capture(url: str) -> dict[str, Any]:
    if _secret(url):
        return {"archive": None, "archive_error": "not sent to the archive: a credential-like parameter in the URL"}
    try:
        rows = _retry(lambda: _cdx(url), lambda reason: reason)
    except urllib.error.HTTPError as error:
        return {"archive": None, "archive_error": f"HTTP {error.code}"}
    if isinstance(rows, str):
        return {"archive": None, "archive_error": rows}
    if len(rows) < 2:
        return {"archive": None}
    timestamp = str(rows[-1][0])
    return {
        "archive": _ARCHIVE.format(timestamp=timestamp, url=url),
        "captured": f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}",
    }


def _alive(result: dict[str, Any]) -> bool:
    status = result.get("status")
    return status is not None and 200 <= status < 300


def check_links(text: str = "", path: str | Path = "") -> dict[str, Any]:
    """Every URL in the text or under the path opened live; the ones not answering, with an archived copy."""
    where: dict[str, list[str]] = {}

    def note(label: str, content: str) -> None:
        for number, line in enumerate(content.splitlines(), 1):
            for url in extract_urls(line):
                places = where.setdefault(url, [])
                if len(places) < _WHERE:
                    places.append(f"{label}:{number}")

    if text:
        note("text", text)
    if path:
        base = Path(path)
        for file in _files(base):
            label = str(file.relative_to(base)) if base.is_dir() else file.name
            note(label, file.read_text(encoding="utf-8", errors="replace"))
    skipped: list[dict[str, str]] = []
    urls: list[str] = []
    for url in where:
        reason = "over the limit of 150 URLs per call" if len(urls) >= _LIMIT else _blocked(url)
        if reason:
            skipped.append({"url": _shown(url), "reason": reason})
        else:
            urls.append(url)
    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        results = dict(zip(urls, pool.map(_status, map(_bare, urls)), strict=True))
    failing: list[dict[str, Any]] = []
    redirected: list[dict[str, str]] = []
    for url in urls:
        result = results[url]
        if _alive(result):
            if result.get("type") != "doi" and result.get("final") and result["final"] != _bare(url):
                redirected.append({"url": url, "to": result["final"]})
            continue
        detail = {key: value for key, value in result.items() if key != "final"}
        failing.append({"url": url, "where": where[url], **detail, **_capture(_bare(url))})
    return {
        "checked": len(urls),
        "ok": len(urls) - len(failing),
        "failing": failing,
        "redirected": redirected,
        "skipped": skipped,
        "note": "Only a 2xx passes. A doi.org link is checked at the DOI registry, not at the publisher, so a "
        "registered DOI passes even where the publisher refuses robots. For the rest, a 403, a 429 or a "
        "timeout from here may still open for the reader, so the status is reported, not judged; a 404 or "
        "410 is gone. archive is the latest copy the Internet Archive holds, the URL to cite when the "
        "original stays dead; archive null means no copy exists and the reference needs another source. "
        "Not opened at all: non-http(s) URLs, URLs carrying credentials and non-public hosts, including a "
        "redirect to one; a URL with a credential-like parameter is opened but never sent to the archive. "
        "Up to 150 URLs per call; the rest come back in skipped.",
    }
