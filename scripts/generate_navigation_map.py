#!/usr/bin/env python3
import json
import os
import re
from collections import defaultdict, deque
from datetime import date

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINANCE_ROOT = os.path.join(REPO_ROOT, "finance")
OUTPUT_PATH = os.path.join(FINANCE_ROOT, "navigation_map.json")

HREF_RE = re.compile(r"href=\"([^\"]+)\"")

CORE_URLS = {
    "/finance/": "hub",
    "/finance/updates/": "updates",
    "/finance/loan-options/": "loan-options",
    "/finance/loan-consolidation-israel/": "core",
    "/finance/personal-loans-israel/": "core",
    "/finance/business-loans-israel/": "core",
}


def find_finance_pages():
    pages = []
    for root, _, files in os.walk(FINANCE_ROOT):
        if "index.html" in files:
            full_path = os.path.join(root, "index.html")
            rel_path = os.path.relpath(full_path, REPO_ROOT)
            pages.append(rel_path)
    return pages


def rel_to_url(rel_path):
    rel_path = rel_path.replace("\\", "/")
    if rel_path.endswith("/index.html"):
        return "/" + rel_path[: -len("index.html")]
    return "/" + rel_path


def normalize_href(href, current_url):
    if not href or href.startswith("#"):
        return None
    if href.startswith("mailto:") or href.startswith("tel:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return None
    if href.startswith("/"):
        path = href
    else:
        if not current_url.startswith("/finance/"):
            return None
        base = current_url
        if not base.endswith("/"):
            base += "/"
        path = base + href

    path = path.split("#")[0].split("?")[0]
    if not path.startswith("/finance/"):
        return None
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    if not path.endswith("/") and "." not in os.path.basename(path):
        path += "/"
    return path


def extract_title(html):
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.DOTALL | re.IGNORECASE)
    if match:
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        if title:
            return title
    return "(no title)"


def page_type(url):
    if url in CORE_URLS:
        return CORE_URLS[url]
    if url.startswith("/finance/"):
        return "long-tail"
    return "other"


def build_graph():
    pages = find_finance_pages()
    url_to_path = {rel_to_url(p): p for p in pages}

    outgoing = defaultdict(set)
    titles = {}

    for url, rel_path in url_to_path.items():
        with open(os.path.join(REPO_ROOT, rel_path), "r", encoding="utf-8") as f:
            html = f.read()
        titles[url] = extract_title(html)
        for href in HREF_RE.findall(html):
            normalized = normalize_href(href, url)
            if not normalized:
                continue
            outgoing[url].add(normalized)

    incoming_count = defaultdict(int)
    broken_targets = set()
    for src, targets in outgoing.items():
        for tgt in targets:
            if tgt in url_to_path:
                incoming_count[tgt] += 1
            else:
                broken_targets.add(tgt)

    nodes = {}
    for url in sorted(url_to_path.keys()):
        nodes[url] = {
            "title": titles.get(url, "(no title)"),
            "type": page_type(url),
            "outgoing": sorted(outgoing.get(url, set())),
            "incoming_count": incoming_count.get(url, 0),
        }

    return nodes, sorted(broken_targets)


def compute_summary(nodes, broken_targets):
    urls = list(nodes.keys())

    orphans = [url for url, data in nodes.items() if data["incoming_count"] == 0 and url != "/finance/"]
    dead_ends = [url for url, data in nodes.items() if len(data["outgoing"]) == 0]

    return {
        "generated_at": date.today().isoformat(),
        "total_pages": len(urls),
        "orphans": sorted(orphans),
        "dead_ends": sorted(dead_ends),
        "broken_targets": sorted(broken_targets),
        "notes": [
            "Only /finance/**/index.html pages are scanned.",
            "External and anchor links are ignored.",
        ],
    }


def main():
    nodes, broken_targets = build_graph()
    summary = compute_summary(nodes, broken_targets)

    output = {
        "summary": summary,
        "nodes": {k: nodes[k] for k in sorted(nodes.keys())},
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
