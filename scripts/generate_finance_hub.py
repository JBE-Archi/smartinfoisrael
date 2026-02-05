#!/usr/bin/env python3
import json
import os
from datetime import date
from html import escape

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOPICS_PATH = os.path.join(REPO_ROOT, "finance", "topics.json")
HUB_PATH = os.path.join(REPO_ROOT, "finance", "index.html")
CNAME_PATH = os.path.join(REPO_ROOT, "CNAME")


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


def main():
    domain = read_domain()
    topics = load_topics()

    topic_by_slug = {item.get("slug", ""): item for item in topics}
    common_intents = [
        ("במינוס", "loan-consolidation-overdraft"),
        ("אחרי סירוב", "loan-consolidation-after-refusal"),
        ("מוגבלים בבנק", "loan-consolidation-bank-restrictions"),
        ("דירוג אשראי נמוך", "loan-consolidation-bad-credit"),
        ("עם ערב", "loan-consolidation-guarantor"),
        ("חוץ-בנקאי", "personal-loan-nonbank"),
        ("עסק קטן בלי בטחונות", "small-business-loan-no-collateral"),
    ]

    links = []
    for item in topics:
        slug = item.get("slug", "")
        title = escape(item.get("title_he", ""))
        links.append(f"      <li><a href=\"/finance/{slug}/\">{title}</a></li>")
    links_html = "\n".join(links)

    intent_links = []
    for label, slug in common_intents:
        item = topic_by_slug.get(slug)
        if not item:
            continue
        title = escape(item.get("title_he", ""))
        intent_links.append(
            f"      <li>{escape(label)}: <a href=\"/finance/{slug}/\">{title}</a></li>"
        )
    intent_links_html = "\n".join(intent_links)

    today = date.today().isoformat()
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "מרכז פיננסים - כל הנושאים",
        "author": {"@type": "Organization", "name": "מערכת SmartInfo Israel"},
        "publisher": {"@type": "Organization", "name": "SmartInfo Israel"},
        "datePublished": today,
        "dateModified": today,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"https://{domain}/finance/",
        },
    }

    html = f"""<!DOCTYPE html>
<html lang=\"he\" dir=\"rtl\">
<head>
  <meta charset=\"UTF-8\">
  <title>פיננסים - כל הנושאים | SmartInfo Israel</title>
  <meta name=\"description\" content=\"מרכז פיננסים עם קישורים לכל דפי ההלוואות באתר. מידע כללי בלבד.\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <meta name=\"robots\" content=\"index,follow\">
  <link rel=\"stylesheet\" href=\"/styles.css\">
  <!-- Cloudflare Web Analytics -->
  <script defer src='https://static.cloudflareinsights.com/beacon.min.js'
  data-cf-beacon='{{\"token\": \"7a7fe009e5124495a79c4d728f3a6eb1\"}}'></script>
  <!-- End Cloudflare Web Analytics -->
  <script type=\"application/ld+json\">
{json.dumps(article_schema, ensure_ascii=False, indent=2)}
  </script>
</head>
<body>

<header>
  <div class=\"container\">
    <h1>פיננסים - כל הנושאים</h1>
    <nav>
      <a href=\"/\">דף הבית</a>
      <a href=\"/finance/\">פיננסים (כל הנושאים)</a>
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
    <a href=\"/\">דף הבית</a> &gt; <a href=\"/finance/\">פיננסים</a> &gt; <span>פיננסים - כל הנושאים</span>
  </p>
</nav>

<main class=\"container\">

  <section>
    <p class=\"notice\">
      המידע בעמוד זה הוא מידע כללי בלבד ואינו ייעוץ פיננסי/משפטי או הצעה למתן אשראי.
    </p>
  </section>

  <section>
    <h2>עמודי מפתח</h2>
    <ul>
      <li><a href=\"/finance/loan-consolidation-israel/\">איחוד הלוואות בישראל</a></li>
      <li><a href=\"/finance/personal-loans-israel/\">הלוואות פרטיות בישראל</a></li>
      <li><a href=\"/finance/business-loans-israel/\">הלוואות לעסקים בישראל</a></li>
      <li><a href=\"/finance/loan-options/\">השוואת אפשרויות הלוואה בישראל</a></li>
    </ul>
  </section>

  <section>
    <h2>דפי עומק</h2>
    <ul>
{links_html}
    </ul>
  </section>

  <section>
    <h2>מצבים נפוצים</h2>
    <ul>
{intent_links_html}
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

    with open(HUB_PATH, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
