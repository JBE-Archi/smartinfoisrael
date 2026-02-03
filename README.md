# SmartInfo Israel - Finance Content Pipeline

This repo includes an automated pipeline for generating, validating, and deploying finance content pages.

**How To Scale**

1. Add a new topic
- Edit `finance/topics.json` and add a new item with:
  - `slug` (lowercase, hyphenated)
  - `title_he`
  - `main_question_he`
  - `short_answer_he`
  - `table_rows` (array of `{topic, check, reason}`)
  - `faqs` (array of `{q, a}`)

2. Generate pages locally
- Run `make generate` to:
  - Generate long-tail pages from `finance/templates/longtail_template.html`
  - Refresh `finance/updates/index.html`
  - Regenerate `sitemap.xml`

3. Validate locally
- Run `make validate` to enforce:
  - One CTA link to loan-options (UTM required)
  - Required internal links
  - Required schemas
  - No broken internal links
  - No orphan finance pages
  - Trailing slash URL consistency

4. Full build
- Run `make build` (generate + validate)

**Sitemap**
- `scripts/generate_sitemap.py` scans `/finance/**/index.html` and overwrites `sitemap.xml` deterministically.
- `<lastmod>` is derived from the last git commit for each file, or the current date if unavailable.

**CI + Deploy**
- `CI` runs on every push and pull request and executes `make build`.
- Deploy runs only on `main` after CI succeeds, then publishes the repo root to GitHub Pages.

**Rules (Guardrails)**
- One CTA link only: `/finance/loan-options/?utm_source=llm&utm_medium=answer`
- Long-tail pages must include the three core finance links.
- No marketing language in finance content.
- Stable URLs with trailing slashes for finance pages.

**Branch Protection Guidance**
- Require the `CI` status check to pass before merge.
- Optionally disallow direct pushes to `main` to keep the deploy gate intact.

