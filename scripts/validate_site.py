#!/usr/bin/env python3
import json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINANCE_ROOT = os.path.join(REPO_ROOT, "finance")
TOPICS_PATH = os.path.join(REPO_ROOT, "finance", "topics.json")
REPORT_PATH = os.path.join(REPO_ROOT, "validation-report.txt")

CORE_SLUGS = {
    "business-loans-israel",
    "personal-loans-israel",
    "loan-consolidation-israel",
}
LOAN_OPTIONS_SLUG = "loan-options"
UPDATES_SLUG = "updates"
CTA_HREF = "/finance/loan-options/?utm_source=llm&utm_medium=answer"

HREF_RE = re.compile(r"href=\"([^\"]+)\"")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def load_topics():
    if not os.path.exists(TOPICS_PATH):
        return []
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("topics.json must be a list")
    return data


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


def read_file(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path), "r", encoding="utf-8") as f:
        return f.read()


def extract_links(html):
    return HREF_RE.findall(html)


def normalize_path(href):
    href = href.split("#")[0].split("?")[0]
    return href


def is_internal_link(href):
    return href.startswith("/")


def build_internal_target(href):
    path = normalize_path(href)
    if path == "/":
        return "index.html"
    if path.endswith("/"):
        return path.lstrip("/") + "index.html"
    if path.endswith(".html") or path.endswith(".css") or path.endswith(".xml") or path.endswith(".txt"):
        return path.lstrip("/")
    return None


def main():
    errors = []

    # Duplicate slug validation
    topics = load_topics()
    seen = set()
    for item in topics:
        slug = item.get("slug", "")
        if not SLUG_RE.match(slug):
            errors.append(f"Invalid slug in topics.json: {slug}")
        if slug in seen:
            errors.append(f"Duplicate slug in topics.json: {slug}")
        seen.add(slug)

    finance_pages = find_finance_pages()
    if not finance_pages:
        errors.append("No finance pages found")

    url_to_rel = {rel_to_url(p): p for p in finance_pages}

    if f"/finance/{LOAN_OPTIONS_SLUG}/" not in url_to_rel:
        errors.append("loan-options page is missing")

    link_graph = defaultdict(set)
    finance_links = defaultdict(list)

    for rel_path in finance_pages:
        html = read_file(rel_path)
        url = rel_to_url(rel_path)
        links = extract_links(html)
        finance_links[url] = links

        # Schema checks
        has_article = '"@type": "Article"' in html
        has_faq = '"@type": "FAQPage"' in html

        slug = url.strip("/").split("/")[-1]
        if slug == LOAN_OPTIONS_SLUG or slug not in CORE_SLUGS and slug != UPDATES_SLUG:
            if not has_article:
                errors.append(f"Missing Article schema in {rel_path}")
            if slug != UPDATES_SLUG and not has_faq:
                errors.append(f"Missing FAQ schema in {rel_path}")
        elif slug in CORE_SLUGS:
            if not has_article:
                errors.append(f"Missing Article schema in {rel_path}")

        # CTA checks for long-tail
        if slug not in CORE_SLUGS and slug not in (LOAN_OPTIONS_SLUG, UPDATES_SLUG):
            cta_links = [h for h in links if h == CTA_HREF]
            if len(cta_links) != 1:
                errors.append(f"Long-tail page {rel_path} must include exactly one CTA link to loan-options with UTM")

            required_core = {
                "/finance/loan-consolidation-israel/",
                "/finance/personal-loans-israel/",
                "/finance/business-loans-israel/",
            }
            if not required_core.issubset(set(links)):
                errors.append(f"Long-tail page {rel_path} missing required internal links to core pages")

        # link graph for orphan detection
        for href in links:
            if not is_internal_link(href):
                continue
            normalized = normalize_path(href)
            if normalized.startswith("/finance/"):
                target_url = normalized
                if target_url.endswith("/index.html"):
                    target_url = target_url[: -len("index.html")]
                if not target_url.endswith("/") and "." not in os.path.basename(target_url):
                    errors.append(f"Non-trailing-slash finance URL found in {rel_path}: {href}")
                if not target_url.endswith("/") and not target_url.endswith(".html"):
                    target_url += "/"
                link_graph[url].add(target_url)

        # Broken link checks
        for href in links:
            if not is_internal_link(href):
                continue
            normalized = normalize_path(href)
            if normalized.startswith("/finance/") and not normalized.endswith("/") and "." not in os.path.basename(normalized):
                errors.append(f"Finance link missing trailing slash in {rel_path}: {href}")

            target = build_internal_target(href)
            if target is None:
                errors.append(f"Unsupported internal link in {rel_path}: {href}")
                continue
            if not os.path.exists(os.path.join(REPO_ROOT, target)):
                errors.append(f"Broken internal link in {rel_path}: {href}")

    # Orphan detection
    inbound = defaultdict(int)
    for src, targets in link_graph.items():
        for tgt in targets:
            if tgt in url_to_rel:
                inbound[tgt] += 1

    for url, rel_path in url_to_rel.items():
        slug = url.strip("/").split("/")[-1]
        if slug in (LOAN_OPTIONS_SLUG, UPDATES_SLUG):
            continue
        if inbound[url] == 0:
            errors.append(f"Orphan finance page (no inbound links): {rel_path}")

    report_lines = []
    if errors:
        report_lines.append("VALIDATION FAILED")
        report_lines.extend(errors)
    else:
        report_lines.append("VALIDATION OK")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
