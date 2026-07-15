# Eduard Gorbunov Academic Website

Static GitHub Pages website for Eduard Gorbunov.

## Structure

- `index.html`: news and research updates
- `about.html`: biography, service, awards, positions, and education
- `research.html`: research themes and links to related publications
- `team.html`: current students, research opportunities, and inquiry checklist
- `publications.html`: publications, book, abstracts, topic filters, and paper-type filters
- `conferences.html`: talks and posters
- `teaching.html`, `amc2019.html`, `pr_th.html`: teaching materials

The site uses a custom stylesheet in `assets/theme/css/modern-academic.css` and lightweight JavaScript in `assets/theme/js/`.
The root `.nojekyll` marker keeps GitHub Pages serving the static files directly.

## Maintenance

The website is intentionally independent of generated-builder assets and legacy framework bundles. Keep page edits in the static HTML files, shared styles in `assets/theme/css/modern-academic.css`, and shared behavior in `assets/theme/js/`.

Shared navigation, footer markup, update dates, sitemap dates, and asset cache versions are defined in `site.config.json`. After changing shared assets or site-wide information, run:

```bash
python3 scripts/sync-site.py
```

Content conventions:

- Keep the shared sidebar, metadata, canonical links, and footer consistent across pages.
- Use explicit semantic hooks such as `data-accent`, `eg-publication-type-badge`, and `eg-student-meta-wide` instead of position-based styling.
- Add publications with real abstracts, stable anchors, highlighted `Eduard Gorbunov` author names, type metadata, topic tags, and action links.
- Mark direct PDF links, including local files, arXiv PDFs, publisher PDFs, and OpenReview PDFs, with `type="application/pdf"` and keep new-tab links paired with `rel="noopener noreferrer"`.
- Keep `assets/images/eg-social-card.png` at 1200x630 for social previews; update `assets/images/eg-social-card.svg` first when changing the card.
- Preserve accessibility and print polish: keep skip links, focus-visible states, reduced-motion support, high-contrast/forced-colors modes, and print-expanded abstracts/disclosures working after layout changes.
- Bump shared asset versions once in `site.config.json`; the synchronization script applies them to every page.

There is no build step: GitHub Pages serves the files in this repository directly. For a local preview, run a static server from the repository root:

```bash
python3 -m http.server 8000
```

Useful local checks before publishing:

```bash
python3 scripts/check-site.py
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
