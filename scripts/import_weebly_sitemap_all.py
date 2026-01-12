#!/usr/bin/env python3
import os
import re
import html
import datetime as dt
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup, NavigableString

SITE = "https://www.simpsong00.com"
SITEMAP_URL = f"{SITE}/sitemap.xml"

OUT_DIR = "src/content/blog"
IMG_DIR = "public/images/uploads/weebly"
IMG_WEB_PREFIX = "/images/uploads/weebly"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (import script)"})

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:90].strip("-") or "post"

def download_image(url: str) -> str | None:
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            ext = ".jpg"
        base = slugify(os.path.basename(path) or "image")
        filename = f"{base}{ext}"
        out_path = os.path.join(IMG_DIR, filename)

        i = 2
        while os.path.exists(out_path):
            filename = f"{base}-{i}{ext}"
            out_path = os.path.join(IMG_DIR, filename)
            i += 1

        with open(out_path, "wb") as f:
            f.write(r.content)

        return f"{IMG_WEB_PREFIX}/{filename}"
    except Exception:
        return None

def html_to_markdownish(node: BeautifulSoup) -> str:
    # Replace images with Markdown images
    for img in node.find_all("img"):
        src = img.get("src") or ""
        alt = img.get("alt") or ""
        local = download_image(src) if src.startswith("http") else None
        md_src = local or src
        img.replace_with(NavigableString(f"\n\n![{alt}]({md_src})\n\n"))

    # Replace links with Markdown links
    for a in node.find_all("a"):
        href = a.get("href") or ""
        text = a.get_text(" ", strip=True) or href
        a.replace_with(NavigableString(f"[{text}]({href})"))

    # Line breaks
    for br in node.find_all("br"):
        br.replace_with("\n")

    text = node.get_text("\n")
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def parse_lastmod(s: str) -> dt.date:
    # Handles: 2026-01-11T19:43:25+00:00 or 2021-04-12T19:36:05-07:00
    s = s.strip()
    try:
        # Python 3.11+: fromisoformat handles offsets if the colon is present (it is)
        return dt.datetime.fromisoformat(s).date()
    except Exception:
        # fallback: just take YYYY-MM-DD
        m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
        if m:
            return dt.date.fromisoformat(m.group(1))
    return dt.date.today()

def is_blog_post_path(path: str) -> bool:
    p = path.rstrip("/")

    # Must be under /blog/
    if not p.startswith("/blog/"):
        return False

    # Exclude landing and listing pages
    if p in ("/blog", "/blog.html"):
        return False
    if "/archives/" in p:
        return False
    if "/category/" in p:
        return False

    # Keep everything else under /blog/<something>
    return True

def extract_post(url: str) -> tuple[str, list[str], str] | None:
    r = session.get(url, timeout=30)
    r.raise_for_status()
    page = BeautifulSoup(r.text, "html.parser")

    # Title: first H2 is usually the blog post title on Weebly
    h2 = page.find("h2")
    title = (h2.get_text(" ", strip=True) if h2 else "").strip()
    if not title:
        t = page.find("title")
        title = (t.get_text(" ", strip=True) if t else "Untitled").strip()

    # Tags/categories (best effort)
    tags = []
    for a in page.select('a[href*="/blog/category/"]'):
        term = a.get_text(" ", strip=True)
        if term:
            tags.append(term)
    tags = sorted(set(tags))

    # Content: try common Weebly containers
    content = None
    for sel in [
        ".blog-content",
        ".blog-post",
        ".wsite-blog-post",
        "#wsite-content",
        ".wsite-section-content",
        "article",
        "main",
    ]:
        node = page.select_one(sel)
        if node and node.get_text(strip=True):
            content = node
            break

    if not content:
        return None

    body_md = html_to_markdownish(content)
    return title, tags, body_md

def read_sitemap() -> list[tuple[str, str]]:
    r = session.get(SITEMAP_URL, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.text)

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    out = []
    for u in root.findall("sm:url", ns):
        loc = u.find("sm:loc", ns)
        lastmod = u.find("sm:lastmod", ns)
        if loc is None or not loc.text:
            continue
        out.append((loc.text.strip(), (lastmod.text.strip() if lastmod is not None and lastmod.text else "")))
    return out

def write_post(date: dt.date, title: str, tags: list[str], body: str, source_url: str) -> str:
    fname = f"{date.isoformat()}-{slugify(title)}.md"
    out_path = os.path.join(OUT_DIR, fname)

    if os.path.exists(out_path):
        return fname

    fm = [
        "---",
        f'title: "{title.replace(chr(34), r"\"")}"',
        'description: ""',
        f'pubDate: "{date.isoformat()}"',
        "tags: [" + ", ".join([f'"{t.replace(chr(34), r"\"")}"' for t in tags]) + "]",
        "draft: false",
        "---",
        "",
        f"_Imported from: {source_url}_",
        "",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fm))
        f.write(body.strip() + "\n")

    return fname

def main():
    entries = read_sitemap()
    blog_entries = []
    for loc, lastmod in entries:
        path = urlparse(loc).path
        if is_blog_post_path(path):
            blog_entries.append((loc, lastmod))

    print(f"Found {len(blog_entries)} blog-related URLs in sitemap.")

    imported = 0
    for i, (url, lastmod) in enumerate(blog_entries, start=1):
        try:
            date = parse_lastmod(lastmod) if lastmod else dt.date.today()
            extracted = extract_post(url)
            if not extracted:
                print(f"[{i}/{len(blog_entries)}] Skipped (no content found): {url}")
                continue
            title, tags, body = extracted
            fname = write_post(date, title, tags, body, url)
            imported += 1
            print(f"[{i}/{len(blog_entries)}] Imported: {fname}")
        except Exception as e:
            print(f"[{i}/{len(blog_entries)}] ERROR: {url} -> {e}")

    print(f"\nDone. Imported {imported} posts into {OUT_DIR}")
    print(f"Images downloaded to {IMG_DIR} (when possible).")

if __name__ == "__main__":
    main()
