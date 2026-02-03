#!/usr/bin/env python3
import os
import subprocess
from datetime import date

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CNAME_PATH = os.path.join(REPO_ROOT, "CNAME")
SITEMAP_PATH = os.path.join(REPO_ROOT, "sitemap.xml")


def read_domain():
    if os.path.exists(CNAME_PATH):
        with open(CNAME_PATH, "r", encoding="utf-8") as f:
            domain = f.read().strip()
            return domain.split("/")[0] if domain else "smartinfoisrael.com"
    return "smartinfoisrael.com"


def git_lastmod(path):
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        lastmod = result.stdout.strip()
        if lastmod:
            return lastmod
    except Exception:
        pass
    return date.today().isoformat()


def find_finance_pages():
    finance_root = os.path.join(REPO_ROOT, "finance")
    pages = []
    for root, _, files in os.walk(finance_root):
        if "index.html" in files:
            full_path = os.path.join(root, "index.html")
            rel_path = os.path.relpath(full_path, REPO_ROOT)
            pages.append(rel_path)
    return pages


def build_url(domain, rel_path):
    rel_path = rel_path.replace("\\", "/")
    if rel_path.endswith("/index.html"):
        loc_path = "/" + rel_path[: -len("index.html")]
    else:
        loc_path = "/" + rel_path
    return f"https://{domain}{loc_path}"


def main():
    domain = read_domain()
    pages = find_finance_pages()
    entries = []
    for rel_path in pages:
        loc = build_url(domain, rel_path)
        lastmod = git_lastmod(rel_path)
        entries.append((loc, lastmod))

    entries.sort(key=lambda x: x[0])

    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for loc, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
