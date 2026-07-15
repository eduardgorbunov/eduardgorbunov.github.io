#!/usr/bin/env python3
"""Synchronize shared site chrome, asset versions, and update metadata."""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "site.config.json"
PUBLIC_PAGES = sorted(ROOT.glob("*.html"))
RUSSIAN_PAGES = {"amc2019.html", "pr_th.html"}


def load_config() -> dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def render_sidebar(page_name: str, config: dict[str, object]) -> str:
    language = ' lang="en"' if page_name in RUSSIAN_PAGES else ""
    profile_links = []
    for link in config["profileLinks"]:
        attributes = [
            'class="eg-sidebar-profile-link"',
            f'href="{escape(link["href"], quote=True)}"',
            f'aria-label="{escape(link["ariaLabel"], quote=True)}"',
        ]
        if link.get("external"):
            attributes.extend(['target="_blank"', 'rel="me noopener noreferrer"'])
        profile_links.append(f'<a {" ".join(attributes)}>{escape(link["label"])}</a>')

    topic_links = "".join(
        f'<a class="eg-sidebar-topic-link" href="{escape(link["href"], quote=True)}">'
        f'{escape(link["label"])}</a>'
        for link in config["researchLinks"]
    )

    nav_items = []
    for link in config["navigation"]:
        pages = link.get("pages", [])
        active = page_name in pages and page_name != "404.html"
        current = link.get("current", "page")
        if page_name in RUSSIAN_PAGES and link["label"] == "Teaching":
            current = "location"
        item_class = ' class="eg-nav-item is-active"' if active else ' class="eg-nav-item"'
        attributes = [
            'class="eg-nav-link"',
            f'href="{escape(link["href"], quote=True)}"',
        ]
        if active:
            attributes.append(f'aria-current="{current}"')
        if link.get("document"):
            attributes.extend(
                [
                    'type="application/pdf"',
                    'target="_blank"',
                    'rel="noopener noreferrer"',
                    f'aria-label="{escape(link["ariaLabel"], quote=True)}"',
                ]
            )
        nav_items.append(
            f'<li{item_class}><a {" ".join(attributes)}>{escape(link["label"])}</a></li>'
        )

    return f'''  <aside class="eg-sidebar" id="site-navigation" aria-label="Site profile and navigation"{language}>
    <nav class="eg-sidebar-nav" aria-label="Primary navigation">
      <div class="eg-sidebar-logo">
        <span class="eg-sidebar-photo-frame"><img class="eg-sidebar-photo" src="assets/images/img-3924-690x1130.jpeg" alt="Eduard Gorbunov" width="104" height="104" decoding="async" fetchpriority="high"></span>
        <div class="eg-sidebar-brand">
          <span class="eg-sidebar-title-wrap"><a class="eg-sidebar-title" href="index.html">Eduard Gorbunov</a></span>
          <p class="eg-sidebar-affiliation"><span>MBZUAI</span><span>Statistics and Data Science</span></p>
          <div class="eg-sidebar-topics" role="group" aria-label="Research focus links">{topic_links}</div>
          <div class="eg-sidebar-profiles" role="group" aria-label="Profile links">{"".join(profile_links)}</div>
        </div>
      </div>
      <div class="eg-sidebar-links-wrap" id="primary-navigation-links">
        <ul class="eg-sidebar-links">{"".join(nav_items)}</ul>
      </div>
    </nav>
  </aside>'''


def render_footer(page_name: str, date_iso: str) -> str:
    date = datetime.strptime(date_iso, "%Y-%m-%d")
    visible_date = f"{date:%B} {date.day}, {date.year}"
    language = ' lang="en"' if page_name in RUSSIAN_PAGES else ""
    return f'''<footer class="eg-site-footer"{language}>
  <div class="eg-container">
    <div class="eg-footer-main">
      <p><strong>Eduard Gorbunov</strong><span>Assistant Professor, Department of Statistics and Data Science, MBZUAI</span></p>
      <nav class="eg-footer-links" aria-label="Footer links">
        <div class="eg-footer-link-group" aria-label="Contact and profiles">
          <a href="mailto:eduard.gorbunov@mbzuai.ac.ae" aria-label="Email Eduard Gorbunov">Email</a>
          <a href="https://scholar.google.com/citations?user=QPVriwoAAAAJ&amp;hl=en" target="_blank" rel="me noopener noreferrer" aria-label="Google Scholar profile">Google Scholar</a>
          <a href="https://arxiv.org/search/math?searchtype=author&amp;query=Gorbunov%2C+E" target="_blank" rel="me noopener noreferrer" aria-label="arXiv author profile">arXiv</a>
        </div>
        <div class="eg-footer-link-group" aria-label="Site sections">
          <a href="index.html">News</a><a href="about.html">About me</a><a href="research.html">Research</a><a href="team.html">Team</a><a href="publications.html">Publications</a><a href="conferences.html#talks">Talks</a><a href="conferences.html#posters">Posters</a><a href="teaching.html">Teaching</a>
        </div>
        <div class="eg-footer-link-group" aria-label="Documents">
          <a href="assets/files/CV_short.pdf" type="application/pdf" target="_blank" rel="noopener noreferrer" aria-label="Open short academic CV PDF">Short CV</a>
          <a href="assets/files/CV.pdf" type="application/pdf" target="_blank" rel="noopener noreferrer" aria-label="Open full academic CV PDF">Full CV</a>
        </div>
      </nav>
    </div>
    <p class="eg-footer-note">Last updated <time datetime="{date_iso}">{visible_date}</time>.</p>
  </div>
</footer>'''


def update_page(path: Path, config: dict[str, object]) -> None:
    text = path.read_text(encoding="utf-8")
    versions = config["assetVersions"]
    replacements = {
        r"assets/theme/css/modern-academic\.css(?:\?v=[^\"']+)?": f'assets/theme/css/modern-academic.css?v={versions["stylesheet"]}',
        r"assets/theme/js/script\.js(?:\?v=[^\"']+)?": f'assets/theme/js/script.js?v={versions["sharedScript"]}',
        r"assets/theme/js/publication-filters\.js(?:\?v=[^\"']+)?": f'assets/theme/js/publication-filters.js?v={versions["publicationFilters"]}',
        r"assets/theme/js/activity-filters\.js(?:\?v=[^\"']+)?": f'assets/theme/js/activity-filters.js?v={versions["activityFilters"]}',
        r"assets/images/eg-favicon\.svg(?:\?v=[^\"']+)?": f'assets/images/eg-favicon.svg?v={versions["favicon"]}',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    text = re.sub(
        r'"dateModified"\s*:\s*"\d{4}-\d{2}-\d{2}"',
        f'"dateModified": "{config["lastUpdated"]}"',
        text,
    )
    text, sidebar_count = re.subn(
        r"\s*<aside class=\"eg-sidebar\".*?</aside>",
        "\n\n" + render_sidebar(path.name, config),
        text,
        count=1,
        flags=re.DOTALL,
    )
    text, footer_count = re.subn(
        r"<footer class=\"eg-site-footer\".*?</footer>",
        render_footer(path.name, config["lastUpdated"]),
        text,
        count=1,
        flags=re.DOTALL,
    )
    if sidebar_count != 1 or footer_count != 1:
        raise RuntimeError(f"Could not synchronize shared shell in {path.name}")
    path.write_text(text, encoding="utf-8")


def update_sitemap(date_iso: str) -> None:
    path = ROOT / "sitemap.xml"
    tree = ElementTree.parse(path)
    root = tree.getroot()
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    for lastmod in root.iter(f"{namespace}lastmod"):
        lastmod.text = date_iso
    ElementTree.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    config = load_config()
    for page in PUBLIC_PAGES:
        update_page(page, config)
    update_sitemap(config["lastUpdated"])
    print(f"Synchronized {len(PUBLIC_PAGES)} pages and sitemap.xml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
