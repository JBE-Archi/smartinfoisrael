#!/usr/bin/env python3
import json
import os
import re
from datetime import date
from html import escape

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOPICS_PATH = os.path.join(REPO_ROOT, "finance", "topics.json")
TEMPLATE_PATH = os.path.join(REPO_ROOT, "finance", "templates", "longtail_template.html")
OUTPUT_ROOT = os.path.join(REPO_ROOT, "finance")
CNAME_PATH = os.path.join(REPO_ROOT, "CNAME")
UPDATES_PATH = os.path.join(REPO_ROOT, "finance", "updates", "index.html")

SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def read_domain():
    if os.path.exists(CNAME_PATH):
        with open(CNAME_PATH, "r", encoding="utf-8") as f:
            domain = f.read().strip()
            return domain.split("/")[0] if domain else "smartinfoisrael.com"
    return "smartinfoisrael.com"


def load_topics():
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("topics.json must be a list")
    return data


def validate_topics(topics):
    seen = set()
    for item in topics:
        slug = item.get("slug", "")
        if not SLUG_RE.match(slug):
            raise ValueError(f"Invalid slug: {slug}")
        if slug in seen:
            raise ValueError(f"Duplicate slug: {slug}")
        seen.add(slug)
        required = ["title_he", "main_question_he", "short_answer_he", "table_rows", "faqs"]
        for key in required:
            if key not in item:
                raise ValueError(f"Missing {key} for slug {slug}")
    return True


def build_table_rows(rows):
    lines = []
    for row in rows:
        topic = escape(str(row.get("topic", "")))
        check = escape(str(row.get("check", "")))
        reason = escape(str(row.get("reason", "")))
        lines.append(
            "        <tr>\n"
            f"          <td>{topic}</td>\n"
            f"          <td>{check}</td>\n"
            f"          <td>{reason}</td>\n"
            "        </tr>"
        )
    return "\n".join(lines)


def build_faq_html(faqs):
    lines = []
    for faq in faqs:
        q = escape(str(faq.get("q", "")))
        a = escape(str(faq.get("a", "")))
        lines.append(
            f"    <h3>{q}</h3>\n"
            "    <p>\n"
            f"      {a}\n"
            "    </p>\n"
        )
    return "\n".join(lines).rstrip()


def build_faq_schema(faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": str(faq.get("q", "")),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": str(faq.get("a", ""))
                }
            }
            for faq in faqs
        ]
    }


def build_related_slugs(slug, topics):
    slugs = [item["slug"] for item in topics]
    slug_set = set(slugs)

    def add_unique(targets, candidates):
        for cand in candidates:
            if cand == slug:
                continue
            if cand in slug_set and cand not in targets:
                targets.append(cand)
            if len(targets) >= 3:
                break
        return targets

    related = []
    if slug.startswith("loan-consolidation-"):
        pairings = [
            ["loan-consolidation-bad-credit", "loan-consolidation-after-refusal", "loan-consolidation-guarantor"],
            ["loan-consolidation-bank-restrictions", "loan-consolidation-after-refusal", "loan-consolidation-bad-credit"],
            ["loan-consolidation-overdraft", "loan-consolidation-mortgage-vs-loan"],
        ]
        for group in pairings:
            if slug in group:
                add_unique(related, group)
        if len(related) < 2:
            add_unique(related, [s for s in slugs if s.startswith("loan-consolidation-")])
    elif slug.startswith("personal-loan-"):
        add_unique(related, [s for s in slugs if s.startswith("personal-loan-")])
        if "self-employed-loans-israel" in slug_set:
            add_unique(related, ["self-employed-loans-israel"])
    elif slug.startswith("small-business-"):
        add_unique(related, [s for s in slugs if s.startswith("small-business-")])
    else:
        add_unique(related, [s for s in slugs if s.startswith("personal-loan-")])

    if len(related) < 2:
        add_unique(related, list(reversed(slugs)))

    return related[:3]


def build_related_links_html(slug, topics):
    by_slug = {item["slug"]: item for item in topics}
    related_slugs = build_related_slugs(slug, topics)
    lines = []
    for rel_slug in related_slugs:
        item = by_slug.get(rel_slug)
        if not item:
            continue
        title = escape(item.get("title_he", rel_slug))
        lines.append(f"      <li><a href=\"/finance/{rel_slug}/\">{title}</a></li>")
    return "\n".join(lines)


def build_article_schema(title, canonical_url, published, modified):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "author": {
            "@type": "Organization",
            "name": "מערכת SmartInfo Israel"
        },
        "publisher": {
            "@type": "Organization",
            "name": "SmartInfo Israel"
        },
        "datePublished": published,
        "dateModified": modified,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url
        }
    }


def render_page(template, context):
    html = template
    for key, value in context.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html


def generate_updates_page(domain, topics):
    today = date.today().isoformat()
    links = []
    for item in topics:
        slug = item["slug"]
        title = escape(item["title_he"])
        links.append(
            f"      <li><a href=\"/finance/{slug}/\">{title}</a></li>"
        )
    links_html = "\n".join(links)
    article_schema = json.dumps(
        build_article_schema(
            "עדכונים אחרונים בדפי הלוואות",
            f"https://{domain}/finance/updates/",
            today,
            today,
        ),
        ensure_ascii=False,
        indent=2,
    )

    html = f"""<!DOCTYPE html>
<html lang=\"he\" dir=\"rtl\">
<head>
  <meta charset=\"UTF-8\">
  <title>עדכונים אחרונים בדפי הלוואות | SmartInfo Israel</title>
  <meta name=\"description\" content=\"רשימת דפי עומק אחרונים בתחום ההלוואות בישראל. מידע כללי בלבד.\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <meta name=\"robots\" content=\"index,follow\">
  <link rel=\"stylesheet\" href=\"/styles.css\">
  <script type=\"application/ld+json\">
{article_schema}
  </script>
</head>
<body>

<header>
  <div class=\"container\">
    <h1>עדכונים אחרונים בדפי הלוואות</h1>
    <nav>
      <a href=\"/\">דף הבית</a>
      <a href=\"/finance/loan-options/\">השוואת אפשרויות הלוואה</a>
      <a href=\"/finance/loan-consolidation-israel/\">איחוד הלוואות</a>
      <a href=\"/finance/personal-loans-israel/\">הלוואות פרטיות</a>
      <a href=\"/finance/business-loans-israel/\">הלוואות לעסקים</a>
      <a href=\"/about.html\">אודות</a>
      <a href=\"/legal-disclaimer.html\">הצהרה משפטית</a>
    </nav>
  </div>
</header>

<nav class=\"container\" aria-label=\"breadcrumbs\">
  <p>
    <a href=\"/\">דף הבית</a> &gt; <a href=\"/finance/\">פיננסים</a> &gt; <span>עדכונים אחרונים בדפי הלוואות</span>
  </p>
</nav>

<main class=\"container\">

  <section>
    <p class=\"notice\">
      המידע בעמוד זה הוא מידע כללי בלבד ואינו ייעוץ פיננסי/משפטי או הצעה למתן אשראי.
    </p>
  </section>

  <section>
    <h2>דפי עומק שנוספו לאחרונה</h2>
    <ul>
{links_html}
    </ul>
  </section>

</main>

<footer>
  <div class=\"container\">
    <nav aria-label=\"footer-finance-links\">
      <a href=\"/finance/loan-consolidation-israel/\">איחוד הלוואות</a>
      <a href=\"/finance/personal-loans-israel/\">הלוואות פרטיות</a>
      <a href=\"/finance/business-loans-israel/\">הלוואות לעסקים</a>
      <a href=\"/finance/loan-options/\">השוואת אפשרויות</a>
    </nav>
    <p>© <span id=\"year\"></span> SmartInfo Israel - מידע כללי בלבד.</p>
  </div>
</footer>

<script>
  document.getElementById('year').textContent = new Date().getFullYear();
</script>

</body>
</html>
"""

    os.makedirs(os.path.dirname(UPDATES_PATH), exist_ok=True)
    with open(UPDATES_PATH, "w", encoding="utf-8") as f:
        f.write(html)


def build_loan_options_intents(topics):
    groups = {
        "איחוד הלוואות": [t for t in topics if t["slug"].startswith("loan-consolidation-")],
        "הלוואות פרטיות": [t for t in topics if t["slug"].startswith("personal-loan-")],
        "הלוואות לעסקים": [t for t in topics if t["slug"].startswith("small-business-")],
    }
    if any(t["slug"] == "self-employed-loans-israel" for t in topics):
        groups["הלוואות פרטיות"].append(
            next(t for t in topics if t["slug"] == "self-employed-loans-israel")
        )

    sections = []
    for label, items in groups.items():
        if not items:
            continue
        items_sorted = sorted(items, key=lambda x: x["slug"])
        links = "\n".join(
            f"      <li><a href=\"/finance/{t['slug']}/\">{escape(t['title_he'])}</a></li>"
            for t in items_sorted
        )
        sections.append(
            f"""    <h3>{label}</h3>
    <ul>
{links}
    </ul>"""
        )
    return "\n".join(sections)


def update_loan_options_page(topics):
    loan_options_path = os.path.join(REPO_ROOT, "finance", "loan-options", "index.html")
    if not os.path.exists(loan_options_path):
        return
    with open(loan_options_path, "r", encoding="utf-8") as f:
        html = f.read()

    start = "<!-- COMMON-CASES-START -->"
    end = "<!-- COMMON-CASES-END -->"
    block = build_loan_options_intents(topics)
    section = f"""  <section>
    <h2>מצבים נפוצים</h2>
{block}
  </section>"""

    if start in html and end in html:
        before = html.split(start)[0]
        after = html.split(end)[1]
        html = before + start + "\n" + section + "\n" + end + after
    else:
        insert_point = "  <section>\n    <h2>שאלות נפוצות (FAQ)</h2>"
        if insert_point in html:
            html = html.replace(insert_point, start + "\n" + section + "\n" + end + "\n\n" + insert_point)
        else:
            html = html + "\n" + start + "\n" + section + "\n" + end + "\n"

    with open(loan_options_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    domain = read_domain()
    topics = load_topics()
    validate_topics(topics)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    today = date.today().isoformat()

    for item in topics:
        slug = item["slug"]
        title = item["title_he"]
        main_q = item["main_question_he"]
        short_a = item["short_answer_he"]
        table_rows = item["table_rows"]
        faqs = item["faqs"]

        canonical_url = f"https://{domain}/finance/{slug}/"
        article_schema = json.dumps(
            build_article_schema(title, canonical_url, today, today),
            ensure_ascii=False,
            indent=2,
        )
        faq_schema = json.dumps(
            build_faq_schema(faqs),
            ensure_ascii=False,
            indent=2,
        )

        context = {
            "TITLE_HE": escape(title),
            "DESCRIPTION_HE": escape(f"{title}. מידע כללי בלבד."),
            "H1_HE": escape(title),
            "MAIN_QUESTION_HE": escape(main_q),
            "SHORT_ANSWER_HE": escape(short_a),
            "TABLE_ROWS_HTML": build_table_rows(table_rows),
            "FAQ_HTML": build_faq_html(faqs),
            "RELATED_LINKS_HTML": build_related_links_html(slug, topics),
            "ARTICLE_SCHEMA_JSON": article_schema,
            "FAQ_SCHEMA_JSON": faq_schema,
        }

        output_dir = os.path.join(OUTPUT_ROOT, slug)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(render_page(template, context))

    generate_updates_page(domain, topics)
    update_loan_options_page(topics)


if __name__ == "__main__":
    main()
