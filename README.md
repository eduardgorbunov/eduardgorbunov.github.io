# Eduard Gorbunov Academic Website

Static GitHub Pages website for Eduard Gorbunov.

## Structure

- `index.html`: news and research updates
- `about.html`: biography, service, awards, positions, and education
- `research.html`: research themes and links to related publications
- `team.html`: current students, research opportunities, and inquiry checklist
- `publications.html`: publications, book, abstracts, topic filters, and paper-type filters
- `data/publications.json`: canonical publication metadata and curated review fields
- `data/publications.schema.json`: machine-readable publication data contract
- `conferences.html`: talks and posters
- `teaching.html`, `amc2019.html`, `pr_th.html`: teaching materials

The site uses a custom stylesheet in `assets/theme/css/modern-academic.css` and lightweight JavaScript in `assets/theme/js/`.
The root `.nojekyll` marker keeps GitHub Pages serving the static files directly.

## Maintenance

The website is intentionally independent of generated-builder assets and legacy framework bundles. Keep ordinary page edits in the static HTML files, publication edits in `data/publications.json`, shared styles in `assets/theme/css/modern-academic.css`, and shared behavior in `assets/theme/js/`.

Shared navigation, footer markup, update dates, sitemap dates, and asset cache versions are defined in `site.config.json`. After changing shared assets or site-wide information, run:

```bash
python3 scripts/sync-site.py
```

Content conventions:

- Keep the shared sidebar, metadata, canonical links, and footer consistent across pages.
- Use explicit semantic hooks such as `data-accent`, `eg-publication-type-badge`, and `eg-student-meta-wide` instead of position-based styling.
- Add publications with real abstracts, stable anchors, highlighted `Eduard Gorbunov` author names, type metadata, topic tags, and action links.
- Treat topic tags, mentoring markers, contribution and senior-authorship notes, distinctions, representative-paper selections, news wording, and removals as human-reviewed fields.
- Mark direct PDF links, including local files, arXiv PDFs, publisher PDFs, and OpenReview PDFs, with `type="application/pdf"` and keep new-tab links paired with `rel="noopener noreferrer"`.
- Keep `assets/images/eg-social-card.png` at 1200x630 for social previews; update `assets/images/eg-social-card.svg` first when changing the card.
- Preserve accessibility and print polish: keep skip links, focus-visible states, reduced-motion support, high-contrast/forced-colors modes, and print-expanded abstracts/disclosures working after layout changes.
- Bump shared asset versions once in `site.config.json`; the synchronization script applies them to every page.

There is no build step for deployment: GitHub Pages serves the files in this repository directly. The publication generator is a maintenance tool that keeps the static publication page synchronized. For a local preview, run a static server from the repository root:

```bash
python3 -m http.server 8000
```

Useful local checks before publishing:

```bash
python3 -m pip install -r requirements-automation.txt
python3 scripts/validate-publications-schema.py
python3 scripts/check-site.py
python3 scripts/publication_assistant.py validate --require-approved --generated
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/sync-site.py
git diff --check
node --check assets/theme/js/script.js
node --check assets/theme/js/publication-filters.js
node --check assets/theme/js/activity-filters.js
```

The site check validates local links and assets, shared page-shell
structure, strict layout-tag nesting, heading structure, image attributes, sidebar consistency,
publication counters, filters, abstracts, tag/action structure, and author
highlighting, shared navigation behavior, canonical and Open Graph URLs,
metadata, JSON-LD, ARIA references, new-tab link attributes,
legacy-template cleanup, and sitemap/robots consistency.
It also checks the `.nojekyll` marker used for GitHub Pages publishing.

The repository also ignores Finder metadata and local QA artifacts via `.gitignore`.

## Human-reviewed publication updates

The publication assistant discovers repetitive metadata changes while leaving scholarly judgment with the site owner. It uses arXiv, OpenAlex, Crossref, and optionally ORCID. Google Scholar is a manual comparison link; its profile pages are not scraped.

Run a local dry review without changing the website:

```bash
python3 scripts/publication_assistant.py discover --only-changes
```

The report is written to `automation/publication-review.md`. To prepare local proposal changes and a visual-review manifest, run:

```bash
python3 scripts/publication_assistant.py discover --apply --only-changes
```

New records and metadata changes remain marked `needs-review`. Correct the structured record as needed, then approve it explicitly and regenerate the static page:

```bash
python3 scripts/publication_assistant.py approve --id <publication-id> --apply-pending
python3 scripts/publication_assistant.py generate
python3 scripts/publication_assistant.py validate --require-approved --generated
```

Matching prefers DOI, then arXiv id, then normalized title and author overlap. The report classifies findings as `new paper`, `published version found`, `metadata update`, `possible duplicate`, or `conflict`, and records source provenance for review. Published versions retain their arXiv links.

The assistant never silently changes topic tags, author mentoring markers, equal-contribution or shared-senior-authorship notes, oral/spotlight/award distinctions, representative-paper selections, custom news wording, or removals. Its optional news draft is never inserted into `index.html` automatically.

The scheduled workflow in `.github/workflows/publication-sync.yml` runs every Monday and can also be started manually from GitHub Actions. When it finds anything reviewable, it opens a draft pull request and uploads desktop and mobile screenshots. An existing review pull request is left untouched so that a later run cannot overwrite human edits.

The normal validation workflow checks the JSON Schema and data contract, identifiers, duplicate records, links, counters, filters, topic and marker values, accessibility rules, deterministic rendering, and all explicit approvals. Merging the pull request remains a manual decision.

For GitHub to open the draft pull request, repository **Settings > Actions > General > Workflow permissions** must allow read/write access and permit GitHub Actions to create pull requests. `OPENALEX_API_KEY` and `ORCID_ACCESS_TOKEN` may be added as repository secrets; both are optional for a small weekly run.
