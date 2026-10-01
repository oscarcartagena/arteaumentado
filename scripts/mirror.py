import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = "https://arteaumentado.com/"
OUT = Path(__file__).resolve().parents[1] / "public"
HOSTS = {"arteaumentado.com", "www.arteaumentado.com"}
seen: set[str] = set()


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=40) as res:
        return res.read()


def local_path(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc not in HOSTS:
        return None
    path = parsed.path or "/"
    if path.endswith("/"):
        path += "index.html"
    if path == "/":
        path = "/index.html"
    return OUT / path.lstrip("/")


def save(url: str, data: bytes) -> Path | None:
    dest = local_path(url)
    if dest is None:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"saved {dest.relative_to(OUT)} ({len(data)})")
    return dest


def refs_from_css(text: str, base: str) -> list[str]:
    found = []
    for raw in re.findall(r"url\(\s*['\"]?([^)'\"]+)", text, flags=re.I):
        if raw.startswith("data:"):
            continue
        found.append(urljoin(base, raw))
    for raw in re.findall(r"@import\s+['\"]([^'\"]+)", text, flags=re.I):
        found.append(urljoin(base, raw))
    return found


def refs_from_html(text: str, base: str) -> list[str]:
    found = []
    for raw in re.findall(r"(?:src|href)=['\"]([^'\"]+)", text, flags=re.I):
        if raw.startswith(("data:", "mailto:", "javascript:", "#", "tel:")):
            continue
        found.append(urljoin(base, raw))
    for raw in re.findall(r"url\((?:&quot;|['\"])?([^)'\"&]+)", text, flags=re.I):
        if raw.startswith("data:"):
            continue
        found.append(urljoin(base, raw))
    return found


def crawl(url: str) -> None:
    url = url.split("#")[0]
    if url in seen:
        return
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in HOSTS:
        return
    seen.add(url)
    try:
        data = fetch(url)
    except Exception as exc:
        print(f"FAIL {url} {exc}")
        return
    dest = save(url, data)
    if dest is None:
        return
    kind = dest.suffix.lower()
    text = ""
    if kind in {".html", ".css", ".js"} or "text" in kind:
        text = data.decode("utf-8", "replace")
    refs = refs_from_html(text, url) if kind == ".html" else []
    if kind == ".css":
        refs = refs_from_css(text, url)
    for ref in refs:
        crawl(ref)


if __name__ == "__main__":
    crawl(ROOT)
    index = OUT / "index.html"
    html = index.read_text(encoding="utf-8", errors="replace")
    html = html.replace("http://www.arteaumentado.com/", "/")
    html = html.replace("https://www.arteaumentado.com/", "/")
    html = html.replace("http://arteaumentado.com/", "/")
    html = html.replace("https://arteaumentado.com/", "/")
    index.write_text(html, encoding="utf-8")
    print("done", len(seen))
