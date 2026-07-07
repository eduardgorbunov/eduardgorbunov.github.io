#!/usr/bin/env python3
"""Static quality checks for the academic website."""

from __future__ import annotations

import json
import re
from collections import Counter
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://eduardgorbunov.github.io"

PRIMARY_STYLESHEET = "assets/theme/css/modern-academic.css"
PRIMARY_STYLESHEET_VERSION = "20260706e"
SHARED_SCRIPT = "assets/theme/js/script.js"
SHARED_SCRIPT_VERSION = "20260705a"
PUBLICATION_FILTER_SCRIPT = "assets/theme/js/publication-filters.js"
PUBLICATION_FILTER_SCRIPT_VERSION = "20260706a"
PUBLICATION_FILTER_TARGETS = "publication-list publication-count-status publication-filter-summary"
SIDEBAR_PHOTO = "assets/images/img-3924-690x1130.jpeg"
SOCIAL_CARD_IMAGE = "assets/images/eg-social-card.png"
SOCIAL_CARD_SOURCE = "assets/images/eg-social-card.svg"
SITE_FAVICON = "assets/images/eg-favicon.svg?v=20260706a"
MATHJAX_SCRIPT = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"
MATHJAX_PRECONNECT = "https://cdn.jsdelivr.net"
DISALLOWED_FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
INLINE_MATH_PATTERN = re.compile(r"\$(?![\s,\]])[^$<>]{1,240}\$|\\\(|\\\[")
LETTER_SPACING_VALUE_PATTERN = re.compile(r"letter-spacing\s*:\s*([^;]+);")
FONT_SIZE_VALUE_PATTERN = re.compile(r"font-size\s*:\s*([^;]+);")
VIEWPORT_FONT_UNIT_PATTERN = re.compile(r"(?<![a-z])(?:vw|vh|vmin|vmax|svw|lvw|dvw|svh|lvh|dvh)(?![a-z])")
TIME_DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}(?:-\d{2}(?:T\d{2}:\d{2})?)?")
COURSE_RESOURCE_DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?")
RUSSIAN_MONTHS = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
}
SIDEBAR_PHOTO_URL = f"{SITE_URL}/{SIDEBAR_PHOTO}"
SHARE_IMAGE_URL = f"{SITE_URL}/{SOCIAL_CARD_IMAGE}"
SHARE_IMAGE_ALT = "Eduard Gorbunov academic website preview"
SHARE_IMAGE_ALT_BY_LANG = {
    "en": SHARE_IMAGE_ALT,
    "ru": "Превью академического сайта Эдуарда Горбунова",
}
SHARE_IMAGE_WIDTH = "1200"
SHARE_IMAGE_HEIGHT = "630"
SHARE_IMAGE_TYPE = "image/png"
SITEMAP_LASTMOD = "2026-07-05"
FOOTER_UPDATED_TEXT = '<p class="eg-footer-note">Last updated <time datetime="2026-07-05">July 5, 2026</time>.</p>'
FOOTER_ROLE_TEXT = '<span>Assistant Professor, Department of Statistics and Data Science, MBZUAI</span>'
OLD_FOOTER_ROLE_TEXT = '<span>Assistant Professor of Statistics and Data Science, MBZUAI</span>'
NOJEKYLL_MARKER = ".nojekyll"
README_FILE = "README.md"
GITIGNORE_FILE = ".gitignore"
EXPECTED_GITIGNORE_PATTERNS = [
    ".DS_Store",
    "**/.DS_Store",
    ".qa-screenshots/",
    "qa-screenshots/",
    "playwright-report/",
    "test-results/",
    "*.log",
    "__pycache__/",
    ".pytest_cache/",
    "node_modules/",
]
EXPECTED_FOOTER_LINKS = [
    ("Email", "mailto:eduard.gorbunov@mbzuai.ac.ae"),
    ("Google Scholar", "https://scholar.google.com/citations?user=QPVriwoAAAAJ&hl=en"),
    ("arXiv", "https://arxiv.org/search/math?searchtype=author&query=Gorbunov%2C+E"),
    ("News", "index.html"),
    ("About me", "about.html"),
    ("Research", "research.html"),
    ("Team", "team.html"),
    ("Publications", "publications.html"),
    ("Talks", "conferences.html#talks"),
    ("Posters", "conferences.html#posters"),
    ("Teaching", "teaching.html"),
    ("CV", "assets/files/CV.pdf"),
]
DISALLOWED_RSS_SNIPPETS = ("application/rss+xml", "feed.xml", "News RSS feed")
FOOTER_CONTEXTUAL_ARIA_LABELS = {
    "Email": "Email Eduard Gorbunov",
    "Google Scholar": "Google Scholar profile",
    "arXiv": "arXiv author profile",
    "CV": "Open academic CV PDF",
}
SIDEBAR_CV_LINK_MARKUP = (
    '<a class="eg-nav-link" href="assets/files/CV.pdf" type="application/pdf" target="_blank" '
    'rel="noopener noreferrer" aria-label="Open academic CV PDF">CV</a>'
)
FOOTER_PROFILE_LINK_LABELS = {"Google Scholar", "arXiv"}
EXPECTED_HEAD_PROFILE_LINKS = [
    "https://scholar.google.com/citations?user=QPVriwoAAAAJ&hl=en",
    "https://arxiv.org/search/math?searchtype=author&query=Gorbunov%2C+E",
    "https://www.researchgate.net/profile/Eduard_Gorbunov",
    "https://x.com/ed_gorbunov",
]
EXPECTED_PERSON_SAME_AS = [
    "https://scholar.google.com/citations?user=QPVriwoAAAAJ&hl=en",
    "https://www.researchgate.net/profile/Eduard_Gorbunov",
    "https://arxiv.org/search/math?searchtype=author&query=Gorbunov%2C+E",
    "https://x.com/ed_gorbunov",
]
EXPECTED_PERSON_KNOWS_ABOUT = [
    "Stochastic optimization",
    "Distributed learning",
    "Variational inequalities",
    "High-probability bounds",
    "Byzantine robustness",
    "Differential privacy",
]
STRICT_LAYOUT_TAGS = {
    "html",
    "head",
    "body",
    "main",
    "aside",
    "nav",
    "header",
    "footer",
    "section",
    "article",
    "div",
    "ul",
    "ol",
    "details",
    "summary",
    "form",
}
EXPECTED_SIDEBAR_PROFILE_LINKS = [
    {
        "label": "Email",
        "href": "mailto:eduard.gorbunov@mbzuai.ac.ae",
        "aria_label": "Email Eduard Gorbunov",
        "target": "",
        "rel": "",
    },
    {
        "label": "Scholar",
        "href": "https://scholar.google.com/citations?user=QPVriwoAAAAJ&hl=en",
        "aria_label": "Google Scholar profile",
        "target": "_blank",
        "rel": "me noopener noreferrer",
    },
    {
        "label": "arXiv",
        "href": "https://arxiv.org/search/math?searchtype=author&query=Gorbunov%2C+E",
        "aria_label": "arXiv author profile",
        "target": "_blank",
        "rel": "me noopener noreferrer",
    },
    {
        "label": "RG",
        "href": "https://www.researchgate.net/profile/Eduard_Gorbunov",
        "aria_label": "ResearchGate profile",
        "target": "_blank",
        "rel": "me noopener noreferrer",
    },
    {
        "label": "X",
        "href": "https://x.com/ed_gorbunov",
        "aria_label": "X profile",
        "target": "_blank",
        "rel": "me noopener noreferrer",
    },
]
EXPECTED_SIDEBAR_AFFILIATION = (
    '<p class="eg-sidebar-affiliation"><span>MBZUAI</span>'
    '<span>Statistics and Data Science</span></p>'
)
EXPECTED_SIDEBAR_TOPIC_LINKS = [
    {
        "label": "Stochastic Optimization",
        "href": "publications.html?tag=stochastic-optimization#publication-list",
    },
    {
        "label": "Distributed Learning",
        "href": "publications.html?tag=distributed-learning#publication-list",
    },
    {
        "label": "Variational Inequalities",
        "href": "publications.html?tag=min-max-variational-inequalities#publication-list",
    },
]
EXPECTED_BREADCRUMBS = {
    "index.html": [
        ("News", f"{SITE_URL}/"),
    ],
    "about.html": [
        ("News", f"{SITE_URL}/"),
        ("About me", f"{SITE_URL}/about.html"),
    ],
    "research.html": [
        ("News", f"{SITE_URL}/"),
        ("Research", f"{SITE_URL}/research.html"),
    ],
    "team.html": [
        ("News", f"{SITE_URL}/"),
        ("Research team", f"{SITE_URL}/team.html"),
    ],
    "publications.html": [
        ("News", f"{SITE_URL}/"),
        ("Publications", f"{SITE_URL}/publications.html"),
    ],
    "conferences.html": [
        ("News", f"{SITE_URL}/"),
        ("Talks and posters", f"{SITE_URL}/conferences.html"),
    ],
    "teaching.html": [
        ("News", f"{SITE_URL}/"),
        ("Teaching", f"{SITE_URL}/teaching.html"),
    ],
    "amc2019.html": [
        ("Новости", f"{SITE_URL}/"),
        ("Преподавание", f"{SITE_URL}/teaching.html"),
        ("Алгоритмы и модели вычислений", f"{SITE_URL}/amc2019.html"),
    ],
    "pr_th.html": [
        ("Новости", f"{SITE_URL}/"),
        ("Преподавание", f"{SITE_URL}/teaching.html"),
        ("Теория вероятностей", f"{SITE_URL}/pr_th.html"),
    ],
    "404.html": [
        ("News", f"{SITE_URL}/"),
        ("Page not found", f"{SITE_URL}/404.html"),
    ],
}
EXPECTED_MSC_STUDENTS = [
    {
        "name": "Bilal Ashfaq",
        "institution": "MBZUAI",
        "period": "2025/09 - present",
        "datetime": "2025-09",
        "profile": "https://www.linkedin.com/in/bashfaq/",
        "co_supervisor": "https://nilslukas.github.io/",
    },
    {
        "name": "Mohamed Ayman Mohamed Mohamed Awad",
        "institution": "MBZUAI",
        "period": "2025/09 - present",
        "datetime": "2025-09",
        "profile": "https://www.linkedin.com/in/mohamed-ayman-7ba40321a/",
        "co_supervisor": "",
    },
    {
        "name": "Saurabh Singh",
        "institution": "MBZUAI",
        "period": "2025/09 - present",
        "datetime": "2025-09",
        "profile": "",
        "co_supervisor": "",
    },
    {
        "name": "Viktor Kovalchuk",
        "institution": "MBZUAI",
        "period": "2025/09 - present",
        "datetime": "2025-09",
        "profile": "https://www.linkedin.com/in/viktor-kovalchuk-147831325/",
        "co_supervisor": "https://mtakac.com/",
    },
]
TEAM_DISALLOWED_PATTERNS = (
    (re.compile(r"\bmy\s+group\b"), "group-centric phrasing"),
)
EXPECTED_RESEARCH_FOCUS_LINKS = [
    (
        "Stochastic optimization",
        "publications.html?tag=stochastic-optimization#publication-list",
    ),
    (
        "Distributed learning",
        "publications.html?tag=distributed-learning#publication-list",
    ),
    (
        "Variational inequalities",
        "publications.html?tag=min-max-variational-inequalities#publication-list",
    ),
    (
        "Generalized smoothness",
        "publications.html?tag=generalized-smoothness#publication-list",
    ),
]
RESEARCH_COUNT_LINKS = [
    ("All publications", "publications", "publications.html", None, "blue"),
    (
        "Stochastic optimization",
        "stochastic optimization papers",
        "publications.html?tag=stochastic-optimization#publication-list",
        "stochastic-optimization",
        "teal",
    ),
    (
        "Distributed learning",
        "distributed learning papers",
        "publications.html?tag=distributed-learning#publication-list",
        "distributed-learning",
        "gold",
    ),
    (
        "Variational inequalities",
        "variational inequality papers",
        "publications.html?tag=min-max-variational-inequalities#publication-list",
        "min-max-variational-inequalities",
        "rose",
    ),
    (
        "Generalized smoothness",
        "Generalized smoothness papers",
        "publications.html?tag=generalized-smoothness#publication-list",
        "generalized-smoothness",
        "",
    ),
    (
        "High-probability bounds",
        "High-probability bounds papers",
        "publications.html?tag=high-probability-bounds#publication-list",
        "high-probability-bounds",
        "",
    ),
    (
        "Byzantine robustness",
        "Byzantine robustness papers",
        "publications.html?tag=byzantine-robustness#publication-list",
        "byzantine-robustness",
        "",
    ),
    (
        "Differential privacy",
        "Differential privacy papers",
        "publications.html?tag=differential-privacy#publication-list",
        "differential-privacy",
        "",
    ),
]
RESEARCH_ENTRY_LINK_TAIL = [
    ("Talks", "conferences.html#talks"),
    ("Posters", "conferences.html#posters"),
    ("Team", "team.html"),
]
EXPECTED_RESEARCH_REPRESENTATIVE_PAPERS = [
    (
        "representative-last-iterate-clipped-sgd",
        "publications.html#pub-last-iterate-clipped-sgd",
    ),
    (
        "representative-heavy-tailed-composite-distributed",
        "publications.html#pub-high-probability-convergence-for-composite-and-distributed-stochastic-minimization-and-variational-inequalities",
    ),
    (
        "representative-generalized-smoothness",
        "publications.html#pub-methods-for-convex-l0-l1-smooth-optimization-clipping-acceleration-and-adaptivity",
    ),
    (
        "representative-byzantine-variational-inequalities",
        "publications.html#pub-byzantine-tolerant-methods-for-distributed-variational-inequalities",
    ),
]
EXPECTED_COURSE_ARCHIVES = {
    "amc2019.html": {"return_label": "Все курсы", "required_shortcuts": {"#seminars", "#homework", "#course-news"}},
    "pr_th.html": {"return_label": "Все курсы", "required_shortcuts": {"#seminars", "#optional-homework", "#course-news"}},
}
EXPECTED_TEACHING_OVERVIEW_STATS = [
    ("created", "#courses-created", "2", "courses created"),
    ("assistant", "#teaching-assistant-roles", "4", "teaching assistantships"),
    ("archive", "#course-mipt-amc-spring-2019", "2", "course archives"),
]
EXPECTED_PAGE_SECTION_LABELS = {
    "404.html": [
        '<section class="eg-error-page" aria-labelledby="error-heading">',
        '<h1 id="error-heading">Page not found</h1>',
        '<nav class="eg-error-primary-actions" aria-label="Primary recovery links">',
        '<a href="publications.html" aria-label="Browse the publications page">Browse publications</a>',
        '<a href="mailto:eduard.gorbunov@mbzuai.ac.ae" aria-label="Email Eduard Gorbunov">Contact by email</a>',
        '<section class="eg-error-next-steps" aria-label="Recommended pages" role="list">',
        '<a href="research.html" data-accent="teal" role="listitem"><strong>Research</strong><small>main themes and papers</small></a>',
        '<a href="team.html" data-accent="blue" role="listitem"><strong>Team</strong><small>students and opportunities</small></a>',
        '<a href="conferences.html#talks" data-accent="gold" role="listitem"><strong>Talks</strong><small>slides and presentations</small></a>',
        '<a href="teaching.html" data-accent="rose" role="listitem"><strong>Teaching</strong><small>courses and archives</small></a>',
        '<a href="research.html">Research</a>',
        '<a href="team.html">Team</a>',
        '<a href="conferences.html#talks">Talks</a>',
        '<a href="conferences.html#posters">Posters</a>',
    ],
    "index.html": [
        '<section class="eg-news-page" id="news" aria-labelledby="news-heading">',
        '<h1 id="news-heading">News</h1>',
    ],
    "publications.html": [
        '<section class="eg-publications-page" id="publications" aria-labelledby="publications-heading">',
        '<h1 id="publications-heading">Publications</h1>',
    ],
    "team.html": [
        '<section class="eg-team-page" id="team" aria-labelledby="team-heading">',
        '<h1 id="team-heading">Research team</h1>',
    ],
    "teaching.html": [
        '<section class="eg-teaching-page" id="teaching" aria-labelledby="teaching-heading">',
        '<h1 id="teaching-heading">Teaching</h1>',
    ],
    "amc2019.html": [
        '<section class="eg-course-page" id="course-top" aria-labelledby="course-heading">',
        '<h1 id="course-heading">Алгоритмы и модели вычислений</h1>',
    ],
    "pr_th.html": [
        '<section class="eg-course-page" id="course-top" aria-labelledby="course-heading">',
        '<h1 id="course-heading">Теория вероятностей</h1>',
    ],
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.html_attrs: dict[str, str] = {}
        self.assets: list[str] = []
        self.links: list[dict[str, str]] = []
        self.sidebar_links: list[tuple[str, str]] = []
        self.sidebar_current_links: list[dict[str, object]] = []
        self.sidebar_profile_links: list[dict[str, str]] = []
        self.sidebar_profile_containers: list[dict[str, str]] = []
        self.sidebar_topic_links: list[dict[str, str]] = []
        self.sidebar_topic_containers: list[dict[str, str]] = []
        self.sidebar_photos: list[dict[str, str]] = []
        self.sidebar_landmarks: list[dict[str, str]] = []
        self.skip_links: list[str] = []
        self.main_attrs: list[dict[str, str]] = []
        self.site_footer_count = 0
        self.site_footer_attrs: list[dict[str, str]] = []
        self.footer_links: list[dict[str, str]] = []
        self.stylesheets: list[str] = []
        self.icons: list[dict[str, str]] = []
        self.preconnects: list[str] = []
        self.image_preloads: list[dict[str, str]] = []
        self.head_profile_links: list[str] = []
        self.scripts: list[str] = []
        self.has_sidebar_photo = False
        self.ids: list[str] = []
        self.aria_refs: list[tuple[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.times: list[dict[str, str]] = []
        self.headings: list[tuple[int, str]] = []
        self.title = ""
        self.has_description = False
        self.meta_names: dict[str, list[str]] = {}
        self.meta_properties: dict[str, list[str]] = {}
        self.canonical_urls: list[str] = []
        self.og_urls: list[str] = []
        self.json_ld: list[str] = []
        self._heading_level: int | None = None
        self._heading_text: list[str] = []
        self._in_title = False
        self._in_json_ld = False
        self._json_ld_text: list[str] = []
        self._sidebar_depth = 0
        self._sidebar_nav_item_active_stack: list[bool] = []
        self._sidebar_link_href: str | None = None
        self._sidebar_link_text: list[str] = []
        self._sidebar_link_is_active = False
        self._sidebar_link_aria_current = ""
        self._sidebar_profile_link: dict[str, str] | None = None
        self._sidebar_profile_link_text: list[str] = []
        self._sidebar_topic_link: dict[str, str] | None = None
        self._sidebar_topic_link_text: list[str] = []
        self._footer_depth = 0
        self._footer_link_href: str | None = None
        self._footer_link_text: list[str] = []
        self._footer_link_aria_label = ""
        self._footer_link_target = ""
        self._footer_link_rel = ""
        self._footer_link_type = ""
        self._link_attr: dict[str, str] | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "html":
            self.html_attrs = attr

        if self._sidebar_depth:
            self._sidebar_depth += 1
        elif "eg-sidebar" in classes:
            self._sidebar_depth = 1
            self.sidebar_landmarks.append({"tag": tag, **attr})

        if self._footer_depth:
            self._footer_depth += 1
        elif tag == "footer" and "eg-site-footer" in classes:
            self._footer_depth = 1

        if self._sidebar_depth and tag == "li" and "eg-nav-item" in classes:
            self._sidebar_nav_item_active_stack.append("is-active" in classes)

        if self._sidebar_depth and "eg-sidebar-profiles" in classes:
            self.sidebar_profile_containers.append({"tag": tag, **attr})

        if self._sidebar_depth and "eg-sidebar-topics" in classes:
            self.sidebar_topic_containers.append({"tag": tag, **attr})

        if "id" in attr:
            self.ids.append(attr["id"])

        if tag == "a" and attr.get("href"):
            self._link_attr = attr
            self._link_text = []
            if "eg-skip-link" in classes:
                self.skip_links.append(attr["href"])
            if self._footer_depth:
                self._footer_link_href = attr["href"]
                self._footer_link_text = []
                self._footer_link_aria_label = attr.get("aria-label", "")
                self._footer_link_target = attr.get("target", "")
                self._footer_link_rel = attr.get("rel", "")
                self._footer_link_type = attr.get("type", "")
            if self._sidebar_depth and "eg-nav-link" in classes:
                self._sidebar_link_href = attr["href"]
                self._sidebar_link_text = []
                self._sidebar_link_is_active = bool(
                    self._sidebar_nav_item_active_stack and self._sidebar_nav_item_active_stack[-1]
                )
                self._sidebar_link_aria_current = attr.get("aria-current", "")
            if self._sidebar_depth and "eg-sidebar-profile-link" in classes:
                self._sidebar_profile_link = {
                    "href": attr["href"],
                    "aria_label": attr.get("aria-label", ""),
                    "target": attr.get("target", ""),
                    "rel": attr.get("rel", ""),
                }
                self._sidebar_profile_link_text = []
            if self._sidebar_depth and "eg-sidebar-topic-link" in classes:
                self._sidebar_topic_link = {"href": attr["href"]}
                self._sidebar_topic_link_text = []

        if tag == "main":
            self.main_attrs.append(attr)

        if tag == "footer" and "eg-site-footer" in classes:
            self.site_footer_count += 1
            self.site_footer_attrs.append(attr)

        if tag in {"img", "script"} and attr.get("src"):
            self.assets.append(attr["src"])

        if tag == "script" and attr.get("src"):
            self.scripts.append(attr["src"])

        if tag == "img":
            self.images.append(attr)
            if self._sidebar_depth and "eg-sidebar-photo" in classes:
                self.has_sidebar_photo = True
                self.sidebar_photos.append(attr)

        if tag == "time":
            self.times.append(attr)

        if tag == "link" and attr.get("href"):
            rel_tokens = set(attr.get("rel", "").split())
            if "stylesheet" in rel_tokens:
                self.stylesheets.append(attr["href"])
            if "preconnect" in rel_tokens:
                self.preconnects.append(attr["href"])
            if "preload" in rel_tokens and attr.get("as") == "image":
                self.image_preloads.append(attr)
            if rel_tokens & {"stylesheet", "icon"}:
                self.assets.append(attr["href"])
            if "icon" in rel_tokens:
                self.icons.append(attr)
            if "preload" in rel_tokens and attr.get("as") == "image":
                self.assets.append(attr["href"])
            if "canonical" in rel_tokens:
                self.canonical_urls.append(attr["href"])
            if "me" in rel_tokens:
                self.head_profile_links.append(attr["href"])

        if tag == "meta" and attr.get("name"):
            self.meta_names.setdefault(attr["name"], []).append(attr.get("content", ""))
            if attr.get("name") == "description" and attr.get("content"):
                self.has_description = True

        if tag == "meta" and attr.get("property"):
            self.meta_properties.setdefault(attr["property"], []).append(attr.get("content", ""))

        if tag == "meta" and attr.get("property") == "og:url" and attr.get("content"):
            self.og_urls.append(attr["content"])

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_level = int(tag[1])
            self._heading_text = []

        if tag == "title":
            self._in_title = True

        if tag == "script" and attr.get("type") == "application/ld+json":
            self._in_json_ld = True
            self._json_ld_text = []

        for name in ("aria-controls", "aria-labelledby", "aria-describedby"):
            for token in attr.get(name, "").split():
                self.aria_refs.append((name, token))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._link_attr is not None:
            self.links.append(
                {
                    **self._link_attr,
                    "label": " ".join("".join(self._link_text).split()),
                }
            )
            self._link_attr = None
            self._link_text = []

        if tag == "a" and self._sidebar_link_href is not None:
            label = " ".join("".join(self._sidebar_link_text).split())
            self.sidebar_links.append((self._sidebar_link_href, label))
            if self._sidebar_link_is_active or self._sidebar_link_aria_current:
                self.sidebar_current_links.append(
                    {
                        "href": self._sidebar_link_href,
                        "label": label,
                        "is_active": self._sidebar_link_is_active,
                        "aria_current": self._sidebar_link_aria_current,
                    }
                )
            self._sidebar_link_href = None
            self._sidebar_link_text = []
            self._sidebar_link_is_active = False
            self._sidebar_link_aria_current = ""

        if tag == "a" and self._sidebar_profile_link is not None:
            self.sidebar_profile_links.append(
                {
                    **self._sidebar_profile_link,
                    "label": " ".join("".join(self._sidebar_profile_link_text).split()),
                }
            )
            self._sidebar_profile_link = None
            self._sidebar_profile_link_text = []

        if tag == "a" and self._sidebar_topic_link is not None:
            self.sidebar_topic_links.append(
                {
                    **self._sidebar_topic_link,
                    "label": " ".join("".join(self._sidebar_topic_link_text).split()),
                }
            )
            self._sidebar_topic_link = None
            self._sidebar_topic_link_text = []

        if tag == "a" and self._footer_link_href is not None:
            self.footer_links.append(
                {
                    "href": self._footer_link_href,
                    "label": " ".join("".join(self._footer_link_text).split()),
                    "aria_label": self._footer_link_aria_label,
                    "target": self._footer_link_target,
                    "rel": self._footer_link_rel,
                    "type": self._footer_link_type,
                }
            )
            self._footer_link_href = None
            self._footer_link_text = []
            self._footer_link_aria_label = ""
            self._footer_link_target = ""
            self._footer_link_rel = ""
            self._footer_link_type = ""

        if tag == "li" and self._sidebar_nav_item_active_stack:
            self._sidebar_nav_item_active_stack.pop()

        if self._heading_level is not None and tag == f"h{self._heading_level}":
            self.headings.append((self._heading_level, "".join(self._heading_text).strip()))
            self._heading_level = None
            self._heading_text = []

        if tag == "title":
            self._in_title = False

        if tag == "script" and self._in_json_ld:
            self.json_ld.append("".join(self._json_ld_text))
            self._in_json_ld = False

        if self._sidebar_depth:
            self._sidebar_depth -= 1

        if self._footer_depth:
            self._footer_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._link_attr is not None:
            self._link_text.append(data)
        if self._heading_level is not None:
            self._heading_text.append(data)
        if self._in_title:
            self.title += data
        if self._in_json_ld:
            self._json_ld_text.append(data)
        if self._sidebar_link_href is not None:
            self._sidebar_link_text.append(data)
        if self._sidebar_profile_link is not None:
            self._sidebar_profile_link_text.append(data)
        if self._sidebar_topic_link is not None:
            self._sidebar_topic_link_text.append(data)
        if self._footer_link_href is not None:
            self._footer_link_text.append(data)


class StrictLayoutParser(HTMLParser):
    def __init__(self, page_label: str) -> None:
        super().__init__()
        self.page_label = page_label
        self.stack: list[tuple[str, int, int]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in STRICT_LAYOUT_TAGS:
            line, column = self.getpos()
            self.stack.append((tag, line, column))

    def handle_endtag(self, tag: str) -> None:
        if tag not in STRICT_LAYOUT_TAGS:
            return

        line, column = self.getpos()
        if not self.stack:
            self.errors.append(f"{self.page_label}:{line}: unexpected closing </{tag}>")
            return

        open_tag, open_line, _open_column = self.stack[-1]
        if open_tag == tag:
            self.stack.pop()
            return

        open_tags = [item[0] for item in self.stack]
        if tag not in open_tags:
            self.errors.append(
                f"{self.page_label}:{line}: unexpected closing </{tag}> while <{open_tag}> from line {open_line} is open"
            )
            return

        self.errors.append(
            f"{self.page_label}:{line}: closing </{tag}> does not match open <{open_tag}> from line {open_line}"
        )
        while self.stack and self.stack[-1][0] != tag:
            self.stack.pop()
        if self.stack:
            self.stack.pop()

    def close(self) -> None:
        super().close()
        for tag, line, _column in reversed(self.stack):
            self.errors.append(f"{self.page_label}:{line}: unclosed <{tag}>")


class PublicationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, object]] = []
        self.book_card: dict[str, str] | None = None
        self.all_stat: int | None = None
        self.type_stats: dict[str, int] = {}
        self.publication_stat_links: list[dict[str, str]] = []
        self.venue_stats: dict[str, int] = {}
        self.tag_options: set[str] = set()
        self.type_options: set[str] = set()
        self.author_lines: list[dict[str, object]] = []
        self.scripts: list[str] = []
        self.filter_form_attrs: dict[str, str] | None = None
        self.filter_controls: dict[str, dict[str, str]] = {}
        self.active_tag_list_attrs: dict[str, str] | None = None
        self.tag_buttons: list[dict[str, str]] = []
        self.clear_filter_buttons: list[dict[str, str]] = []
        self.count_status_attrs: dict[str, str] | None = None
        self.publication_list_tag: str | None = None
        self.publication_list_attrs: dict[str, str] | None = None
        self.empty_states: list[dict[str, str]] = []
        self.venue_filter_buttons: list[dict[str, str]] = []
        self._current_card: dict[str, object] | None = None
        self._in_venue = False
        self._venue_text: list[str] = []
        self._current_stat: dict[str, object] | None = None
        self._current_venue_stat: dict[str, object] | None = None
        self._in_strong = False
        self._strong_text: list[str] = []
        self._in_type_select = False
        self._in_tag_select = False
        self._in_authors = False
        self._author_text: list[str] = []
        self._author_strongs: list[str] = []
        self._author_strong_depth = 0
        self._author_strong_text: list[str] = []
        self._in_publication_heading = False
        self._publication_heading_text: list[str] = []
        self._publication_tag_depth = 0
        self._publication_abstract_depth = 0
        self._publication_abstract_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "script" and attr.get("src"):
            self.scripts.append(attr["src"])

        if tag == "form" and "eg-publication-controls" in classes:
            self.filter_form_attrs = attr

        if tag == "select" and attr.get("id") == "publication-type-filter":
            self._in_type_select = True
            self.filter_controls["type"] = attr

        if tag == "input" and attr.get("id") == "publication-search-filter":
            self.filter_controls["search"] = attr

        if tag == "select" and attr.get("id") == "publication-tag-filter":
            self._in_tag_select = True
            self.filter_controls["tag"] = attr

        if tag == "div" and "eg-active-tag-list" in classes:
            self.active_tag_list_attrs = attr

        if tag == "button" and "eg-tag-button" in classes:
            self.tag_buttons.append(attr)

        if tag == "button" and "eg-clear-filters" in classes:
            self.clear_filter_buttons.append(attr)

        if tag == "div" and attr.get("id") == "publication-count-status":
            self.count_status_attrs = attr

        if attr.get("id") == "publication-list":
            self.publication_list_tag = tag
            self.publication_list_attrs = attr

        if tag == "p" and "eg-publication-empty" in classes:
            self.empty_states.append(attr)

        if tag == "article" and "eg-publication-card" in classes and "eg-book-card" in classes:
            self.book_card = {
                "id": attr.get("id", ""),
                "labelledby": attr.get("aria-labelledby", ""),
            }

        if tag == "article" and "eg-publication-card" in classes and "eg-book-card" not in classes:
            self._current_card = {
                "id": attr.get("id", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "heading_id": "",
                "title": "",
                "title_link": {},
                "role": attr.get("role", ""),
                "type": attr.get("data-type", ""),
                "tags": set(attr.get("data-tags", "").split()),
                "venue": "",
                "abstracts": 0,
                "abstract_text": "",
                "abstract_words": 0,
                "tag_groups": 0,
                "visible_tags": 0,
                "actions": 0,
            }
            self.cards.append(self._current_card)

        if self._current_card is not None:
            if tag == "h2":
                self._current_card["heading_id"] = attr.get("id", "")
                self._in_publication_heading = True
                self._publication_heading_text = []
            if self._in_publication_heading and tag == "a" and attr.get("href"):
                self._current_card["title_link"] = {
                    "href": attr.get("href", ""),
                    "type": attr.get("type", ""),
                    "aria_label": attr.get("aria-label", ""),
                }
            if tag == "details" and "eg-publication-abstract" in classes:
                self._current_card["abstracts"] = int(self._current_card["abstracts"]) + 1
                self._publication_abstract_depth = 1
                self._publication_abstract_text = []
            elif self._publication_abstract_depth:
                self._publication_abstract_depth += 1
            if tag == "div" and "eg-publication-tags" in classes:
                self._current_card["tag_groups"] = int(self._current_card["tag_groups"]) + 1
                self._publication_tag_depth = 1
            elif self._publication_tag_depth:
                self._publication_tag_depth += 1
            if self._publication_tag_depth and tag == "span":
                self._current_card["visible_tags"] = int(self._current_card["visible_tags"]) + 1
            if tag == "div" and "eg-publication-actions" in classes:
                self._current_card["actions"] = int(self._current_card["actions"]) + 1

        if tag in {"a", "article"} and "eg-publication-stat" in classes:
            self.publication_stat_links.append(attr)
            self._current_stat = {
                "all": attr.get("data-count-all") == "true",
                "type": attr.get("data-count-type", ""),
                "value": "",
            }

        if tag == "button" and "eg-venue-filter" in classes and attr.get("data-venue"):
            self.venue_filter_buttons.append(attr)
            self._current_venue_stat = {"venue": attr["data-venue"], "value": ""}

        if self._current_card is not None and tag == "p" and "eg-publication-venue" in classes:
            self._in_venue = True
            self._venue_text = []

        if tag == "p" and "eg-publication-authors" in classes:
            self._in_authors = True
            self._author_text = []
            self._author_strongs = []

        if self._in_authors and tag == "strong":
            self._author_strong_depth += 1
            self._author_strong_text = []

        if self._in_type_select and tag == "option":
            self.type_options.add(attr.get("value", ""))

        if self._in_tag_select and tag == "option":
            value = attr.get("value", "")
            if value and value != "all":
                self.tag_options.add(value)

        if tag == "strong" and (self._current_stat is not None or self._current_venue_stat is not None):
            self._in_strong = True
            self._strong_text = []

    def handle_endtag(self, tag: str) -> None:
        if self._publication_tag_depth:
            self._publication_tag_depth -= 1

        if self._publication_abstract_depth:
            self._publication_abstract_depth -= 1
            if self._publication_abstract_depth == 0 and self._current_card is not None:
                abstract_text = " ".join("".join(self._publication_abstract_text).split())
                self._current_card["abstract_text"] = abstract_text
                self._current_card["abstract_words"] = len(re.findall(r"[A-Za-zА-Яа-я0-9]+", abstract_text))
                self._publication_abstract_text = []

        if tag == "p" and self._in_venue:
            if self._current_card is not None:
                self._current_card["venue"] = "".join(self._venue_text).strip()
            self._in_venue = False
            self._venue_text = []

        if tag == "h2" and self._in_publication_heading:
            if self._current_card is not None:
                self._current_card["title"] = " ".join("".join(self._publication_heading_text).split())
            self._in_publication_heading = False
            self._publication_heading_text = []

        if tag == "strong" and self._author_strong_depth:
            self._author_strongs.append("".join(self._author_strong_text).strip())
            self._author_strong_depth -= 1
            self._author_strong_text = []

        if tag == "strong" and self._in_strong:
            value = "".join(self._strong_text).strip()
            if self._current_stat is not None:
                self._current_stat["value"] = value
            if self._current_venue_stat is not None:
                self._current_venue_stat["value"] = value
            self._in_strong = False
            self._strong_text = []

        if tag == "p" and self._in_authors:
            self.author_lines.append({
                "text": "".join(self._author_text).strip(),
                "strongs": list(self._author_strongs),
            })
            self._in_authors = False
            self._author_text = []
            self._author_strongs = []
            self._author_strong_depth = 0
            self._author_strong_text = []

        if tag in {"a", "article"} and self._current_stat is not None:
            value = parse_int(self._current_stat.get("value", ""))
            if value is not None:
                if self._current_stat.get("all"):
                    self.all_stat = value
                elif self._current_stat.get("type"):
                    self.type_stats[str(self._current_stat["type"])] = value
            self._current_stat = None

        if tag == "article" and self._current_card is not None:
            self._current_card = None

        if tag == "li" and self._current_venue_stat is not None:
            value = parse_int(self._current_venue_stat.get("value", ""))
            if value is not None:
                self.venue_stats[str(self._current_venue_stat["venue"])] = value
            self._current_venue_stat = None

        if tag == "select" and self._in_tag_select:
            self._in_tag_select = False

        if tag == "select" and self._in_type_select:
            self._in_type_select = False

    def handle_data(self, data: str) -> None:
        if self._in_venue:
            self._venue_text.append(data)
        if self._in_strong:
            self._strong_text.append(data)
        if self._in_authors:
            self._author_text.append(data)
        if self._author_strong_depth:
            self._author_strong_text.append(data)
        if self._in_publication_heading:
            self._publication_heading_text.append(data)
        if self._publication_abstract_depth:
            self._publication_abstract_text.append(data)


class ActivityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, object]] = []
        self.activity_lists: list[dict[str, str]] = []
        self.archive_lists: list[dict[str, str]] = []
        self.archive_details: list[dict[str, str]] = []
        self.overview_attrs: dict[str, str] | None = None
        self.overview_stat_attrs: list[dict[str, str]] = []
        self.overview_stats: dict[str, int] = {}
        self._current_card: dict[str, object] | None = None
        self._in_activity_number = False
        self._activity_number_text: list[str] = []
        self._in_activity_title = False
        self._activity_title_text: list[str] = []
        self._in_activity_meta = False
        self._activity_meta_text: list[str] = []
        self._current_stat_href: str | None = None
        self._in_stat_value = False
        self._stat_value_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "div" and "eg-activity-list" in classes:
            self.activity_lists.append(attr)

        if tag == "div" and "eg-activity-archive-list" in classes:
            self.archive_lists.append(attr)

        if tag == "details" and "eg-activity-archive" in classes:
            self.archive_details.append(attr)

        if tag == "section" and "eg-activity-overview" in classes:
            self.overview_attrs = attr

        if tag == "a" and "eg-activity-stat" in classes:
            self.overview_stat_attrs.append(attr)
            self._current_stat_href = attr.get("href", "")

        if tag == "strong" and self._current_stat_href:
            self._in_stat_value = True
            self._stat_value_text = []

        if tag == "article" and "eg-activity-card" in classes:
            self._current_card = {
                "id": attr.get("id", ""),
                "kind": attr.get("data-kind", ""),
                "role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "number": "",
                "title": "",
                "title_link": {},
                "heading_id": "",
                "actions": 0,
                "meta": [],
            }
            self.cards.append(self._current_card)

        if self._current_card is not None:
            if tag == "div" and "eg-activity-number" in classes:
                self._in_activity_number = True
                self._activity_number_text = []
            if tag == "h3":
                self._in_activity_title = True
                self._activity_title_text = []
                self._current_card["heading_id"] = attr.get("id", "")
            if self._in_activity_title and tag == "a" and attr.get("href"):
                self._current_card["title_link"] = {
                    "href": attr.get("href", ""),
                    "type": attr.get("type", ""),
                    "aria_label": attr.get("aria-label", ""),
                }
            if tag == "p" and "eg-activity-meta" in classes:
                self._in_activity_meta = True
                self._activity_meta_text = []
            if tag == "div" and "eg-activity-actions" in classes:
                self._current_card["actions"] = int(self._current_card["actions"]) + 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "strong" and self._in_stat_value:
            if self._current_stat_href:
                value = parse_int("".join(self._stat_value_text).strip())
                if value is not None:
                    self.overview_stats[self._current_stat_href] = value
            self._in_stat_value = False
            self._stat_value_text = []

        if tag == "a" and self._current_stat_href:
            self._current_stat_href = None

        if tag == "div" and self._in_activity_number:
            if self._current_card is not None:
                self._current_card["number"] = "".join(self._activity_number_text).strip()
            self._in_activity_number = False
            self._activity_number_text = []

        if tag == "h3" and self._in_activity_title:
            if self._current_card is not None:
                self._current_card["title"] = " ".join("".join(self._activity_title_text).split())
            self._in_activity_title = False
            self._activity_title_text = []

        if tag == "p" and self._in_activity_meta:
            if self._current_card is not None:
                meta = list(self._current_card["meta"])
                meta.append(" ".join("".join(self._activity_meta_text).split()))
                self._current_card["meta"] = meta
            self._in_activity_meta = False
            self._activity_meta_text = []

        if tag == "article" and self._current_card is not None:
            self._current_card = None

    def handle_data(self, data: str) -> None:
        if self._in_stat_value:
            self._stat_value_text.append(data)
        if self._in_activity_number:
            self._activity_number_text.append(data)
        if self._in_activity_title:
            self._activity_title_text.append(data)
        if self._in_activity_meta:
            self._activity_meta_text.append(data)


class NewsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, str]] = []
        self.news_list_attrs: dict[str, str] | None = None
        self.archive_list_attrs: dict[str, str] | None = None
        self.archive_details_attrs: dict[str, str] | None = None
        self._current_card: dict[str, str] | None = None
        self._in_title = False
        self._title_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "section" and "eg-news-list" in classes:
            self.news_list_attrs = attr

        if tag == "section" and "eg-news-archive-list" in classes:
            self.archive_list_attrs = attr

        if tag == "details" and "eg-news-archive" in classes:
            self.archive_details_attrs = attr

        if tag == "article" and "eg-news-card" in classes:
            self._current_card = {
                "id": attr.get("id", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "datetime": "",
                "title": "",
                "heading_id": "",
                "role": attr.get("role", ""),
            }
            self.cards.append(self._current_card)

        if self._current_card is not None:
            if tag == "time" and not self._current_card["datetime"]:
                self._current_card["datetime"] = attr.get("datetime", "")
            if tag == "h2" and "eg-news-title" in classes:
                self._in_title = True
                self._title_text = []
                self._current_card["heading_id"] = attr.get("id", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self._in_title:
            if self._current_card is not None:
                self._current_card["title"] = " ".join("".join(self._title_text).split())
            self._in_title = False
            self._title_text = []

        if tag == "article" and self._current_card is not None:
            self._current_card = None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_text.append(data)


class FeaturedNewsVenueParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.groups: list[dict[str, object]] = []
        self._in_featured_news = False
        self._featured_news_depth = 0
        self._in_venue_links = False
        self._venue_links_depth = 0
        self._current_group: dict[str, object] | None = None
        self._li_depth = 0
        self._in_venue_label = False
        self._venue_label_text: list[str] = []
        self._in_venue_count = False
        self._venue_count_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "article" and attr.get("id") == "news-2026-conference-acceptances":
            self._in_featured_news = True
            self._featured_news_depth = 1
        elif self._in_featured_news:
            self._featured_news_depth += 1

        if self._in_featured_news:
            if tag == "ul" and "eg-news-venue-links" in classes and not self._in_venue_links:
                self._in_venue_links = True
                self._venue_links_depth = 1
            elif self._in_venue_links:
                self._venue_links_depth += 1

        if self._in_venue_links:
            if tag == "li" and self._current_group is None:
                self._current_group = {"venue": "", "accent": attr.get("data-accent", ""), "hrefs": []}
                self._li_depth = 1
            elif self._current_group is not None:
                self._li_depth += 1

        if self._current_group is not None:
            if tag == "strong":
                self._in_venue_label = True
                self._venue_label_text = []
            if tag == "span" and "eg-news-venue-count" in classes:
                self._in_venue_count = True
                self._venue_count_text = []
            if tag == "a" and attr.get("href"):
                hrefs = self._current_group.get("hrefs", [])
                if isinstance(hrefs, list):
                    hrefs.append(attr["href"])
                    self._current_group["hrefs"] = hrefs

    def handle_endtag(self, tag: str) -> None:
        if tag == "strong" and self._in_venue_label:
            if self._current_group is not None:
                self._current_group["venue"] = " ".join("".join(self._venue_label_text).split())
            self._in_venue_label = False
            self._venue_label_text = []

        if tag == "span" and self._in_venue_count:
            if self._current_group is not None:
                self._current_group["count"] = " ".join("".join(self._venue_count_text).split())
            self._in_venue_count = False
            self._venue_count_text = []

        if self._current_group is not None and self._li_depth:
            closing_group = tag == "li" and self._li_depth == 1
            self._li_depth -= 1
            if closing_group:
                self.groups.append(self._current_group)
                self._current_group = None

        if self._in_venue_links and self._venue_links_depth:
            closing_venue_links = tag == "ul" and self._venue_links_depth == 1
            self._venue_links_depth -= 1
            if closing_venue_links:
                self._in_venue_links = False

        if self._in_featured_news and self._featured_news_depth:
            closing_featured_news = tag == "article" and self._featured_news_depth == 1
            self._featured_news_depth -= 1
            if closing_featured_news:
                self._in_featured_news = False

    def handle_data(self, data: str) -> None:
        if self._in_venue_label:
            self._venue_label_text.append(data)
        if self._in_venue_count:
            self._venue_count_text.append(data)


class AboutParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.service_cards: list[dict[str, str]] = []
        self.service_lists: list[dict[str, str]] = []
        self.list_cards: list[dict[str, str]] = []
        self.list_groups: list[dict[str, str]] = []
        self._current_card: dict[str, str] | None = None
        self._in_heading = False
        self._heading_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "div" and "eg-about-card-grid" in classes:
            self.service_lists.append(attr)

        if tag == "div" and "eg-about-list-grid" in classes:
            self.list_groups.append(attr)

        if tag in {"section", "article"} and "eg-about-card" in classes:
            self._current_card = {
                "type": "service",
                "id": attr.get("id", ""),
                "role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "kind": "",
                "title": "",
                "heading_id": "",
            }
            self.service_cards.append(self._current_card)

        if tag == "article" and "eg-about-list-card" in classes:
            self._current_card = {
                "type": "list",
                "id": attr.get("id", ""),
                "role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "kind": attr.get("data-kind", ""),
                "title": "",
                "heading_id": "",
            }
            self.list_cards.append(self._current_card)

        if self._current_card is not None and tag == "h3":
            self._current_card["heading_id"] = attr.get("id", "")
            self._in_heading = True
            self._heading_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._in_heading:
            if self._current_card is not None:
                self._current_card["title"] = " ".join("".join(self._heading_text).split())
            self._in_heading = False
            self._heading_text = []

        if tag in {"section", "article"} and self._current_card is not None:
            self._current_card = None

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_text.append(data)


class TeamParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.students: list[dict[str, object]] = []
        self.opportunities: list[dict[str, object]] = []
        self.student_lists: list[dict[str, str]] = []
        self.opportunity_lists: list[dict[str, str]] = []
        self.guideline_labels: list[str] = []
        self.application_guidelines: dict[str, str] = {}
        self._current_student: dict[str, object] | None = None
        self._current_opportunity: dict[str, object] | None = None
        self._in_student_role = False
        self._student_role_text: list[str] = []
        self._in_student_name = False
        self._student_name_text: list[str] = []
        self._in_opportunity_label = False
        self._opportunity_label_text: list[str] = []
        self._in_opportunity_title = False
        self._opportunity_title_text: list[str] = []
        self._opportunity_link_href = ""
        self._opportunity_link_text: list[str] = []
        self._in_meta_term = False
        self._meta_term_text: list[str] = []
        self._current_meta_label = ""
        self._in_meta_value = False
        self._meta_value_text: list[str] = []
        self._guideline_list_depth = 0
        self._in_guideline_label = False
        self._guideline_label_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "div" and "eg-student-grid" in classes:
            self.student_lists.append(attr)

        if (
            tag == "div" and "eg-team-grid" in classes
        ) or (
            tag == "ul" and "eg-opportunity-list" in classes
        ):
            self.opportunity_lists.append(attr)

        if tag == "article" and "eg-student-card" in classes:
            self._current_student = {
                "id": attr.get("id", ""),
                "accent": attr.get("data-accent", ""),
                "list_role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "role": "",
                "name": "",
                "heading_id": "",
                "meta": {},
                "time_datetimes": [],
                "links": [],
            }
            self.students.append(self._current_student)

        if (
            tag == "article" and "eg-opportunity-card" in classes
        ) or (
            tag == "li" and "eg-opportunity-item" in classes
        ):
            self._current_opportunity = {
                "id": attr.get("id", ""),
                "accent": attr.get("data-accent", ""),
                "list_role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "label": "",
                "title": "",
                "heading_id": "",
                "links": [],
                "link_actions": [],
            }
            self.opportunities.append(self._current_opportunity)

        if tag == "aside" and "eg-application-guidelines" in classes:
            self.application_guidelines = {
                "id": attr.get("id", ""),
                "labelledby": attr.get("aria-labelledby", ""),
            }

        if self._current_student is not None:
            if tag == "span" and "eg-student-role" in classes:
                self._in_student_role = True
                self._student_role_text = []
            if tag == "h3":
                self._in_student_name = True
                self._student_name_text = []
                self._current_student["heading_id"] = attr.get("id", "")
            if tag == "dt":
                self._in_meta_term = True
                self._meta_term_text = []
            if tag == "dd":
                self._in_meta_value = True
                self._meta_value_text = []
            if tag == "time" and attr.get("datetime"):
                self._current_student["time_datetimes"] = [
                    *self._current_student["time_datetimes"],
                    attr["datetime"],
                ]
            if tag == "a" and attr.get("href"):
                self._current_student["links"] = [*self._current_student["links"], attr["href"]]

        if self._current_opportunity is not None:
            if tag == "span" and "eg-opportunity-label" in classes:
                self._in_opportunity_label = True
                self._opportunity_label_text = []
            if tag == "h3":
                self._in_opportunity_title = True
                self._opportunity_title_text = []
                self._current_opportunity["heading_id"] = attr.get("id", "")
            if tag == "a" and attr.get("href"):
                self._current_opportunity["links"] = [*self._current_opportunity["links"], attr["href"]]
                self._opportunity_link_href = attr["href"]
                self._opportunity_link_text = []

        if tag == "ul" and "eg-guideline-list" in classes:
            self._guideline_list_depth = 1
        elif self._guideline_list_depth:
            self._guideline_list_depth += 1

        if self._guideline_list_depth and tag == "strong":
            self._in_guideline_label = True
            self._guideline_label_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._in_student_role:
            if self._current_student is not None:
                self._current_student["role"] = " ".join("".join(self._student_role_text).split())
            self._in_student_role = False
            self._student_role_text = []

        if tag == "h3" and self._in_student_name:
            if self._current_student is not None:
                self._current_student["name"] = " ".join("".join(self._student_name_text).split())
            self._in_student_name = False
            self._student_name_text = []

        if tag == "dt" and self._in_meta_term:
            self._current_meta_label = " ".join("".join(self._meta_term_text).split())
            self._in_meta_term = False
            self._meta_term_text = []

        if tag == "dd" and self._in_meta_value:
            if self._current_student is not None and self._current_meta_label:
                meta = dict(self._current_student["meta"])
                meta[self._current_meta_label] = " ".join("".join(self._meta_value_text).split())
                self._current_student["meta"] = meta
            self._in_meta_value = False
            self._meta_value_text = []

        if tag == "article" and self._current_student is not None:
            self._current_student = None
            self._current_meta_label = ""

        if tag == "span" and self._in_opportunity_label:
            if self._current_opportunity is not None:
                self._current_opportunity["label"] = " ".join("".join(self._opportunity_label_text).split())
            self._in_opportunity_label = False
            self._opportunity_label_text = []

        if tag == "h3" and self._in_opportunity_title:
            if self._current_opportunity is not None:
                self._current_opportunity["title"] = " ".join("".join(self._opportunity_title_text).split())
            self._in_opportunity_title = False
            self._opportunity_title_text = []

        if tag == "a" and self._opportunity_link_href:
            if self._current_opportunity is not None:
                actions = list(self._current_opportunity["link_actions"])
                actions.append(
                    {
                        "href": self._opportunity_link_href,
                        "text": " ".join("".join(self._opportunity_link_text).split()),
                    }
                )
                self._current_opportunity["link_actions"] = actions
            self._opportunity_link_href = ""
            self._opportunity_link_text = []

        if tag in {"article", "li"} and self._current_opportunity is not None:
            self._current_opportunity = None

        if tag == "strong" and self._in_guideline_label:
            self.guideline_labels.append(" ".join("".join(self._guideline_label_text).split()))
            self._in_guideline_label = False
            self._guideline_label_text = []

        if self._guideline_list_depth:
            self._guideline_list_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_student_role:
            self._student_role_text.append(data)
        if self._in_student_name:
            self._student_name_text.append(data)
        if self._in_opportunity_label:
            self._opportunity_label_text.append(data)
        if self._in_opportunity_title:
            self._opportunity_title_text.append(data)
        if self._opportunity_link_href:
            self._opportunity_link_text.append(data)
        if self._in_meta_term:
            self._meta_term_text.append(data)
        if self._in_meta_value:
            self._meta_value_text.append(data)
        if self._in_guideline_label:
            self._guideline_label_text.append(data)


class ResearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.focus_cards: list[dict[str, object]] = []
        self.focus_lists: list[dict[str, str]] = []
        self.about_lists: list[dict[str, str]] = []
        self.direction_cards: list[dict[str, str]] = []
        self.entry_links: list[tuple[str, str]] = []
        self._current_focus: dict[str, object] | None = None
        self._current_direction: dict[str, str] | None = None
        self._in_focus_label = False
        self._focus_label_text: list[str] = []
        self._in_focus_heading = False
        self._focus_heading_text: list[str] = []
        self._in_direction_heading = False
        self._direction_heading_text: list[str] = []
        self._research_links_depth = 0
        self._entry_link_href: str | None = None
        self._entry_link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "div" and "eg-focus-grid" in classes:
            self.focus_lists.append(attr)

        if tag == "div" and "eg-about-list-grid" in classes:
            self.about_lists.append(attr)

        if tag == "article" and "eg-focus-card" in classes:
            self._current_focus = {
                "id": attr.get("id", ""),
                "role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "accent": attr.get("data-accent", ""),
                "label": "",
                "heading": "",
                "heading_id": "",
                "paragraphs": 0,
                "links": [],
                "link_labels": [],
            }
            self.focus_cards.append(self._current_focus)

        if tag == "article" and "eg-about-list-card" in classes and attr.get("data-kind") == "research":
            self._current_direction = {
                "id": attr.get("id", ""),
                "role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "title": "",
                "heading_id": "",
                "links": [],
            }
            self.direction_cards.append(self._current_direction)

        if self._current_focus is not None:
            if tag == "span":
                self._in_focus_label = True
                self._focus_label_text = []
            if tag == "h2":
                self._in_focus_heading = True
                self._focus_heading_text = []
                self._current_focus["heading_id"] = attr.get("id", "")
            if tag == "p":
                self._current_focus["paragraphs"] = int(self._current_focus["paragraphs"]) + 1
            if tag == "a" and attr.get("href"):
                self._current_focus["links"] = [*self._current_focus["links"], attr["href"]]
                self._current_focus["link_labels"] = [
                    *self._current_focus["link_labels"],
                    attr.get("aria-label", ""),
                ]

        if self._current_direction is not None and tag == "h3":
            self._in_direction_heading = True
            self._direction_heading_text = []
            self._current_direction["heading_id"] = attr.get("id", "")
        if self._current_direction is not None and tag == "a" and attr.get("href"):
            self._current_direction["links"] = [*self._current_direction["links"], attr["href"]]

        if tag == "nav" and "eg-profile-links" in classes and attr.get("aria-label") == "Research links":
            self._research_links_depth = 1
        elif self._research_links_depth:
            self._research_links_depth += 1

        if self._research_links_depth and tag == "a" and attr.get("href"):
            self._entry_link_href = attr["href"]
            self._entry_link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._in_focus_label:
            if self._current_focus is not None:
                self._current_focus["label"] = " ".join("".join(self._focus_label_text).split())
            self._in_focus_label = False
            self._focus_label_text = []

        if tag == "h2" and self._in_focus_heading:
            if self._current_focus is not None:
                self._current_focus["heading"] = " ".join("".join(self._focus_heading_text).split())
            self._in_focus_heading = False
            self._focus_heading_text = []

        if tag == "article" and self._current_focus is not None:
            self._current_focus = None

        if tag == "h3" and self._in_direction_heading:
            if self._current_direction is not None:
                self._current_direction["title"] = " ".join("".join(self._direction_heading_text).split())
            self._in_direction_heading = False
            self._direction_heading_text = []

        if tag == "article" and self._current_direction is not None:
            self._current_direction = None

        if tag == "a" and self._entry_link_href is not None:
            self.entry_links.append((" ".join("".join(self._entry_link_text).split()), self._entry_link_href))
            self._entry_link_href = None
            self._entry_link_text = []

        if self._research_links_depth:
            self._research_links_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_focus_label:
            self._focus_label_text.append(data)
        if self._in_focus_heading:
            self._focus_heading_text.append(data)
        if self._entry_link_href is not None:
            self._entry_link_text.append(data)
        if self._in_direction_heading:
            self._direction_heading_text.append(data)


class TeachingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.course_cards: list[dict[str, object]] = []
        self.course_lists: list[dict[str, str]] = []
        self.resource_lists: list[dict[str, str]] = []
        self.update_lists: list[dict[str, str]] = []
        self.shortcuts: list[tuple[str, str]] = []
        self.resource_cards: list[dict[str, str]] = []
        self.update_cards: list[dict[str, str]] = []
        self._current_course: dict[str, object] | None = None
        self._in_course_title = False
        self._course_title_text: list[str] = []
        self._shortcuts_depth = 0
        self._shortcut_href: str | None = None
        self._shortcut_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "div" and "eg-course-list" in classes:
            self.course_lists.append(attr)

        if tag == "div" and "eg-course-resource-grid" in classes:
            self.resource_lists.append(attr)

        if tag == "div" and "eg-course-update-list" in classes:
            self.update_lists.append(attr)

        if tag == "article" and "eg-course-card" in classes:
            self._current_course = {
                "id": attr.get("id", ""),
                "accent": attr.get("data-accent", ""),
                "role": attr.get("role", ""),
                "labelledby": attr.get("aria-labelledby", ""),
                "title": "",
                "heading_id": "",
                "links": [],
            }
            self.course_cards.append(self._current_course)

        if self._current_course is not None:
            if tag == "h3":
                self._in_course_title = True
                self._course_title_text = []
                self._current_course["heading_id"] = attr.get("id", "")
            if tag == "a" and attr.get("href"):
                self._current_course["links"] = [*self._current_course["links"], attr["href"]]

        if tag == "nav" and "eg-course-shortcuts" in classes:
            self._shortcuts_depth = 1
        elif self._shortcuts_depth:
            self._shortcuts_depth += 1

        if self._shortcuts_depth and tag == "a" and attr.get("href"):
            self._shortcut_href = attr["href"]
            self._shortcut_text = []

        if tag == "article" and "eg-course-resource-card" in classes:
            self.resource_cards.append(
                {
                    "id": attr.get("id", ""),
                    "role": attr.get("role", ""),
                    "kind": attr.get("data-kind", ""),
                    "aria_label": attr.get("aria-label", ""),
                }
            )

        if tag == "article" and "eg-course-update-card" in classes:
            self.update_cards.append(
                {
                    "id": attr.get("id", ""),
                    "role": attr.get("role", ""),
                    "kind": "update",
                    "aria_label": attr.get("aria-label", ""),
                }
            )

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._in_course_title:
            if self._current_course is not None:
                self._current_course["title"] = " ".join("".join(self._course_title_text).split())
            self._in_course_title = False
            self._course_title_text = []

        if tag == "article" and self._current_course is not None:
            self._current_course = None

        if tag == "a" and self._shortcut_href is not None:
            self.shortcuts.append((" ".join("".join(self._shortcut_text).split()), self._shortcut_href))
            self._shortcut_href = None
            self._shortcut_text = []

        if self._shortcuts_depth:
            self._shortcuts_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_course_title:
            self._course_title_text.append(data)
        if self._shortcut_href is not None:
            self._shortcut_text.append(data)


def local_path(page: Path, href: str) -> Path:
    local = urlsplit(href).path
    return page.parent / unquote(local or page.name)


def local_fragment(href: str) -> str:
    return unquote(urlsplit(href).fragment)


def page_url(page: Path) -> str:
    return f"{SITE_URL}/" if page.name == "index.html" else f"{SITE_URL}/{page.name}"


def png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def duplicate_json_keys(raw: str) -> list[str]:
    duplicates: list[str] = []

    def collect_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                duplicates.append(key)
            else:
                seen.add(key)
        return dict(pairs)

    json.loads(raw, object_pairs_hook=collect_pairs)
    return duplicates


def iter_json_ld_nodes(data: object):
    if isinstance(data, dict):
        yield data
        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from iter_json_ld_nodes(item)
    elif isinstance(data, list):
        for item in data:
            yield from iter_json_ld_nodes(item)


def json_ld_has_type(node: dict[str, object], schema_type: str) -> bool:
    node_type = node.get("@type")
    if isinstance(node_type, list):
        return schema_type in node_type
    return node_type == schema_type


def parse_int(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def parse_leading_int(value: object) -> int | None:
    match = re.match(r"\s*(\d+)\b", str(value))
    if not match:
        return None
    return parse_int(match.group(1))


def compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_russian_archive_date(value: str) -> str | None:
    match = re.fullmatch(r"\s*(\d{1,2})\s+([А-Яа-яёЁ]+),\s*(\d{4})\s*", value)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = RUSSIAN_MONTHS.get(month_name.casefold())
    if month is None:
        return None
    return f"{year}-{month}-{int(day):02d}"


def expect_single_value(errors: list[str], page_label: Path, label: str, values: list[str], expected: str) -> None:
    if values != [expected]:
        errors.append(f"{page_label}: {label} should be {expected!r}, found {values!r}")


LEGACY_TEMPLATE_DIRECTORIES = (
    "assets/bootstrap",
    "assets/dropdown",
    "assets/mobirise",
    "assets/popper",
    "assets/smoothscroll",
    "assets/tether",
    "assets/touchswipe",
    "assets/web/assets/jquery",
    "assets/web/assets/mobirise-icons",
    "fonts/Rubik",
)

LEGACY_TEMPLATE_FILES = (
    "assets/images/hashes.json",
    "page6.html",
    "project 2.mobirise",
    "publish-hashes.json",
)

LEGACY_TEMPLATE_MARKERS = {
    "mobirise": "Mobirise reference",
    "mbr-": "Mobirise class prefix",
    "cid-": "Mobirise generated class prefix",
    "data-app-modern-menu": "Mobirise menu marker",
    "assets/bootstrap/": "Bootstrap asset reference",
    "assets/dropdown/": "Mobirise dropdown asset reference",
    "assets/mobirise/": "Mobirise asset reference",
    "assets/popper/": "Popper asset reference",
    "assets/smoothscroll/": "Smoothscroll asset reference",
    "assets/tether/": "Tether asset reference",
    "assets/touchswipe/": "Touchswipe asset reference",
    "assets/web/assets/jquery/": "jQuery asset reference",
    "assets/web/assets/mobirise-icons/": "Mobirise icon asset reference",
    "fonts/rubik/": "Legacy Rubik font reference",
    "page6.html": "old standalone book page reference",
    "project 2.mobirise": "Mobirise project file reference",
    "publish-hashes.json": "old export hash manifest reference",
    "assets/images/hashes.json": "old image hash manifest reference",
    "qa-screenshots/": "local QA screenshot reference",
}

STALE_COPY_PATTERNS = (
    (re.compile(r"\bwebsite generator description\b"), "old generated-page description"),
    (re.compile(r"\bsite builder description\b"), "old generated-page description"),
    (re.compile(r"\blorem ipsum\b"), "placeholder lorem ipsum copy"),
    (re.compile(r"\bcoming soon\b"), "unfinished coming-soon copy"),
    (re.compile(r"\btbd\b"), "unfinished TBD copy"),
    (re.compile(r"\bto be added\b"), "unfinished to-be-added copy"),
    (re.compile(r"\binterfolio\b"), "stale Interfolio application reference"),
    (re.compile(r"\bsite refresh\b"), "temporary site-refresh wording"),
    (re.compile(r"\bmoved during\b"), "temporary migration wording"),
)


def check_template_cleanup() -> list[str]:
    errors: list[str] = []

    for metadata_file in sorted(ROOT.rglob(".DS_Store")):
        errors.append(f"{metadata_file.relative_to(ROOT)}: local macOS metadata should be removed")

    for directory in LEGACY_TEMPLATE_DIRECTORIES:
        if (ROOT / directory).exists():
            errors.append(f"{directory}: legacy template directory should be removed")

    for legacy_file in LEGACY_TEMPLATE_FILES:
        if (ROOT / legacy_file).exists():
            errors.append(f"{legacy_file}: legacy template file should be removed")

    deployable_files = [
        *ROOT.glob("*.html"),
        *ROOT.glob("assets/theme/css/*.css"),
        *ROOT.glob("assets/theme/js/*.js"),
        ROOT / "robots.txt",
        ROOT / "sitemap.xml",
    ]

    for path in sorted(file for file in deployable_files if file.exists()):
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        if "\t" in raw_text:
            errors.append(f"{path.relative_to(ROOT)}: deployable source should use spaces instead of tabs")
        text = raw_text.lower()
        for marker, description in LEGACY_TEMPLATE_MARKERS.items():
            if marker in text:
                errors.append(f"{path.relative_to(ROOT)}: {description} {marker!r}")
        for marker in ("-----", "_____", "====="):
            if marker in text:
                errors.append(f"{path.relative_to(ROOT)}: old visible separator marker {marker!r}")
        for pattern, description in STALE_COPY_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: {description}")
        if path.suffix == ".css":
            for match in LETTER_SPACING_VALUE_PATTERN.finditer(text):
                value = " ".join(match.group(1).strip().split())
                if value not in {"0", "0 !important"}:
                    errors.append(f"{path.relative_to(ROOT)}: letter-spacing should stay 0, found {value!r}")
            for match in FONT_SIZE_VALUE_PATTERN.finditer(text):
                value = " ".join(match.group(1).strip().split())
                if VIEWPORT_FONT_UNIT_PATTERN.search(value):
                    errors.append(
                        f"{path.relative_to(ROOT)}: font-size should not use viewport units, found {value!r}"
                    )

    return errors


def check_site() -> list[str]:
    errors: list[str] = []
    html_files = sorted(ROOT.glob("*.html"))
    parsers: dict[str, PageParser] = {}

    social_card_path = ROOT / SOCIAL_CARD_IMAGE
    if not social_card_path.exists():
        errors.append(f"{SOCIAL_CARD_IMAGE}: social preview image is missing")
    else:
        expected_social_card_size = (int(SHARE_IMAGE_WIDTH), int(SHARE_IMAGE_HEIGHT))
        actual_social_card_size = png_dimensions(social_card_path)
        if actual_social_card_size != expected_social_card_size:
            errors.append(
                f"{SOCIAL_CARD_IMAGE}: expected PNG size {expected_social_card_size}, "
                f"found {actual_social_card_size!r}"
            )
    if not (ROOT / SOCIAL_CARD_SOURCE).exists():
        errors.append(f"{SOCIAL_CARD_SOURCE}: social preview source SVG is missing")

    for page in html_files:
        page_text = page.read_text(encoding="utf-8", errors="ignore")
        structure_parser = StrictLayoutParser(page.name)
        structure_parser.feed(page_text)
        structure_parser.close()
        errors.extend(structure_parser.errors)
        parser = PageParser()
        parser.feed(page_text)
        parsers[page.name] = parser

    baseline_sidebar = parsers.get("index.html").sidebar_links if "index.html" in parsers else []
    expected_current_links = {
        "index.html": ("index.html", "page"),
        "about.html": ("about.html", "page"),
        "research.html": ("research.html", "page"),
        "team.html": ("team.html", "page"),
        "publications.html": ("publications.html", "page"),
        "conferences.html": ("conferences.html#talks", "location"),
        "teaching.html": ("teaching.html", "page"),
        "amc2019.html": ("teaching.html", "location"),
        "pr_th.html": ("teaching.html", "location"),
    }

    for page in html_files:
        parser = parsers[page.name]
        page_label = page.relative_to(ROOT)
        ids = set(parser.ids)
        page_text = page.read_text(encoding="utf-8", errors="ignore")
        page_body = page_text.split("</head>", 1)[-1]
        has_inline_math = bool(INLINE_MATH_PATTERN.search(page_body))
        expected_breadcrumbs = EXPECTED_BREADCRUMBS.get(page.name)

        if expected_breadcrumbs is None:
            errors.append(f"{page_label}: missing expected breadcrumb definition in checker")
        elif page_text.count('"@type": "BreadcrumbList"') != 1:
            errors.append(f"{page_label}: expected exactly one BreadcrumbList structured data block")
        else:
            canonical_page_url = f"{SITE_URL}/" if page.name == "index.html" else f"{SITE_URL}/{page.name}"
            breadcrumb_text = page_text.split('"@type": "BreadcrumbList"', 1)[1].split("</script>", 1)[0]
            expected_breadcrumb_id = f'{canonical_page_url}#breadcrumb'
            if f'"@id": {json.dumps(expected_breadcrumb_id)}' not in breadcrumb_text:
                errors.append(f"{page_label}: breadcrumb block should use @id {expected_breadcrumb_id!r}")
            for position, (label, url) in enumerate(expected_breadcrumbs, start=1):
                breadcrumb_snippets = [
                    f'"position": {position}',
                    f'"name": {json.dumps(label, ensure_ascii=False)}',
                    f'"item": {json.dumps(url)}',
                ]
                for snippet in breadcrumb_snippets:
                    if snippet not in breadcrumb_text:
                        errors.append(f"{page_label}: breadcrumb is missing {snippet!r}")

        if '<div class="eg-page-heading">' in page_text:
            errors.append(f"{page_label}: page heading should use a semantic header element")
        if '<div class="eg-section-heading' in page_text:
            errors.append(f"{page_label}: section headings should use semantic header elements")

        if parser.skip_links != ["#main-content"]:
            errors.append(f"{page_label}: expected one skip link to #main-content, found {parser.skip_links!r}")

        if page.name in {"amc2019.html", "pr_th.html"}:
            if parser.html_attrs.get("lang") != "ru":
                errors.append(f"{page_label}: Russian course archive should declare html lang='ru'")
            if '"inLanguage": "ru"' not in page_text:
                errors.append(f"{page_label}: Russian course archive structured data should declare inLanguage='ru'")
            if '<a class="eg-skip-link" href="#main-content" lang="en">Skip to main content</a>' not in page_text:
                errors.append(f"{page_label}: English skip link should declare lang='en' on Russian pages")
            if (
                '<aside class="eg-sidebar" id="site-navigation" '
                'aria-label="Site profile and navigation" lang="en">'
            ) not in page_text:
                errors.append(f"{page_label}: English shared sidebar should declare lang='en' on Russian pages")
        elif parser.html_attrs.get("lang") != "en":
            errors.append(f"{page_label}: English pages should declare html lang='en'")

        if len(parser.main_attrs) != 1:
            errors.append(f"{page_label}: expected exactly one main element, found {len(parser.main_attrs)}")
        elif parser.main_attrs[0].get("id") != "main-content":
            errors.append(f"{page_label}: main element should have id='main-content'")

        if parser.site_footer_count != 1:
            errors.append(f"{page_label}: expected exactly one site footer, found {parser.site_footer_count}")
        elif parser.html_attrs.get("lang") == "ru" and parser.site_footer_attrs[0].get("lang") != "en":
            errors.append(f"{page_label}: English shared footer should declare lang='en' on Russian pages")

        for snippet in EXPECTED_PAGE_SECTION_LABELS.get(page.name, []):
            if snippet not in page_text:
                errors.append(f"{page_label}: missing page section label snippet {snippet!r}")

        expected_profile_preload = {
            "rel": "preload",
            "as": "image",
            "href": SIDEBAR_PHOTO,
            "type": "image/jpeg",
            "fetchpriority": "high",
        }
        if parser.image_preloads != [expected_profile_preload]:
            errors.append(f"{page_label}: expected shared profile image preload, found {parser.image_preloads!r}")

        expected_favicon = {
            "rel": "icon",
            "href": SITE_FAVICON,
            "type": "image/svg+xml",
        }
        if parser.icons != [expected_favicon]:
            errors.append(f"{page_label}: expected shared academic favicon, found {parser.icons!r}")

        for host in DISALLOWED_FONT_HOSTS:
            if host in page_text:
                errors.append(f"{page_label}: remove external Google font dependency {host!r}")
        if re.search(r"\b[Dd]istributed ML\b", page_text):
            errors.append(f"{page_label}: use 'Distributed Learning' or 'distributed learning' instead of the abbreviation")

        if len(parser.sidebar_landmarks) != 1:
            errors.append(f"{page_label}: expected exactly one sidebar landmark, found {parser.sidebar_landmarks!r}")
        else:
            sidebar_landmark = parser.sidebar_landmarks[0]
            if sidebar_landmark.get("tag") != "aside":
                errors.append(f"{page_label}: sidebar should use an aside landmark")
            if sidebar_landmark.get("id") != "site-navigation":
                errors.append(f"{page_label}: sidebar should keep id='site-navigation'")
            if "eg-sidebar" not in sidebar_landmark.get("class", "").split():
                errors.append(f"{page_label}: sidebar should keep the eg-sidebar class")
            if sidebar_landmark.get("aria-label") != "Site profile and navigation":
                errors.append(f"{page_label}: sidebar should have the shared accessible label")

        stylesheet_paths = {href.split("?", 1)[0] for href in parser.stylesheets}
        expected_stylesheet = f"{PRIMARY_STYLESHEET}?v={PRIMARY_STYLESHEET_VERSION}"
        if PRIMARY_STYLESHEET not in stylesheet_paths:
            errors.append(f"{page_label}: missing shared stylesheet {PRIMARY_STYLESHEET!r}")
        elif expected_stylesheet not in parser.stylesheets:
            errors.append(f"{page_label}: shared stylesheet should be versioned as {expected_stylesheet!r}")
        script_paths = {src.split("?", 1)[0] for src in parser.scripts}
        expected_shared_script = f"{SHARED_SCRIPT}?v={SHARED_SCRIPT_VERSION}"
        if SHARED_SCRIPT not in script_paths:
            errors.append(f"{page_label}: missing shared script {SHARED_SCRIPT!r}")
        elif expected_shared_script not in parser.scripts:
            errors.append(f"{page_label}: shared script should be versioned as {expected_shared_script!r}")

        if not parser.has_sidebar_photo:
            errors.append(f"{page_label}: missing sidebar photo")
        elif parser.sidebar_photos != [
            {
                "class": "eg-sidebar-photo",
                "src": SIDEBAR_PHOTO,
                "alt": "Eduard Gorbunov",
                "width": "104",
                "height": "104",
                "decoding": "async",
                "fetchpriority": "high",
            }
        ]:
            errors.append(f"{page_label}: sidebar photo differs from the shared profile image")

        if parser.head_profile_links != EXPECTED_HEAD_PROFILE_LINKS:
            errors.append(
                f"{page_label}: head rel='me' profile links should be "
                f"{EXPECTED_HEAD_PROFILE_LINKS!r}, found {parser.head_profile_links!r}"
            )

        if parser.sidebar_links != baseline_sidebar:
            errors.append(f"{page_label}: sidebar navigation differs from index.html")
        if SIDEBAR_CV_LINK_MARKUP not in page_text:
            errors.append(f"{page_label}: sidebar CV link should use contextual aria-label")
        if EXPECTED_SIDEBAR_AFFILIATION not in page_text:
            errors.append(f"{page_label}: sidebar affiliation should use stacked span markup")
        if "eg-sidebar-affiliation\">MBZUAI<br" in page_text:
            errors.append(f"{page_label}: sidebar affiliation should avoid br-based layout")
        if len(parser.sidebar_profile_containers) != 1:
            errors.append(
                f"{page_label}: expected exactly one sidebar profile link region, "
                f"found {parser.sidebar_profile_containers!r}"
            )
        else:
            profile_container = parser.sidebar_profile_containers[0]
            if profile_container.get("tag") != "div":
                errors.append(f"{page_label}: sidebar profile links should avoid nested nav landmarks")
            if profile_container.get("role") != "group":
                errors.append(f"{page_label}: sidebar profile links should keep role='group'")
            if profile_container.get("aria-label") != "Profile links":
                errors.append(f"{page_label}: sidebar profile links should keep aria-label='Profile links'")
        if parser.sidebar_profile_links != EXPECTED_SIDEBAR_PROFILE_LINKS:
            errors.append(f"{page_label}: sidebar profile links differ from the shared profile strip")
        if len(parser.sidebar_topic_containers) != 1:
            errors.append(
                f"{page_label}: expected exactly one sidebar research-topic link region, "
                f"found {parser.sidebar_topic_containers!r}"
            )
        else:
            topic_container = parser.sidebar_topic_containers[0]
            if topic_container.get("tag") != "div":
                errors.append(f"{page_label}: sidebar research-topic links should avoid nested nav landmarks")
            if topic_container.get("role") != "group":
                errors.append(f"{page_label}: sidebar research-topic links should keep role='group'")
            if topic_container.get("aria-label") != "Research focus links":
                errors.append(
                    f"{page_label}: sidebar research-topic links should keep aria-label='Research focus links'"
                )
        if parser.sidebar_topic_links != EXPECTED_SIDEBAR_TOPIC_LINKS:
            errors.append(f"{page_label}: sidebar research-topic links differ from the shared topic strip")

        if page.name == "404.html":
            if parser.sidebar_current_links:
                errors.append(f"{page_label}: 404 page should not mark a sidebar item current")
        else:
            if len(parser.sidebar_current_links) != 1:
                errors.append(
                    f"{page_label}: expected exactly one current sidebar link, found {parser.sidebar_current_links!r}"
                )
            else:
                current_link = parser.sidebar_current_links[0]
                expected_href, expected_aria_current = expected_current_links.get(page.name, (page.name, "page"))
                if current_link.get("href") != expected_href:
                    errors.append(
                        f"{page_label}: current sidebar link should be {expected_href!r}, found {current_link!r}"
                    )
                if not current_link.get("is_active"):
                    errors.append(f"{page_label}: current sidebar link is missing is-active state")
                if current_link.get("aria_current") != expected_aria_current:
                    errors.append(
                        f"{page_label}: current sidebar link should use "
                        f"aria-current={expected_aria_current!r}, found {current_link!r}"
                    )

        duplicates = sorted({identifier for identifier in parser.ids if parser.ids.count(identifier) > 1})
        if duplicates:
            errors.append(f"{page_label}: duplicate ids {duplicates}")

        title = parser.title.strip()
        expected_page_url = page_url(page)
        description_values = parser.meta_names.get("description", [])
        description = description_values[0] if len(description_values) == 1 else ""

        page_lang = parser.html_attrs.get("lang", "")
        expected_locale_by_lang = {"en": "en_US", "ru": "ru_RU"}
        expected_locale = expected_locale_by_lang.get(page_lang)
        expected_share_image_alt = SHARE_IMAGE_ALT_BY_LANG.get(page_lang, SHARE_IMAGE_ALT)
        if expected_locale is None:
            errors.append(f"{page_label}: html lang should be one of {sorted(expected_locale_by_lang)}")

        if not title:
            errors.append(f"{page_label}: missing <title>")
        if not parser.has_description:
            errors.append(f"{page_label}: missing meta description")

        expect_single_value(errors, page_label, "meta description", description_values, description)
        expect_single_value(errors, page_label, "meta author", parser.meta_names.get("author", []), "Eduard Gorbunov")
        expect_single_value(errors, page_label, "meta theme-color", parser.meta_names.get("theme-color", []), "#073b4c")
        expect_single_value(errors, page_label, "meta color-scheme", parser.meta_names.get("color-scheme", []), "light")
        expect_single_value(
            errors,
            page_label,
            "meta referrer",
            parser.meta_names.get("referrer", []),
            "strict-origin-when-cross-origin",
        )
        robots_values = parser.meta_names.get("robots", [])
        if page.name == "404.html":
            expect_single_value(errors, page_label, "meta robots", robots_values, "noindex, follow")
        else:
            expect_single_value(errors, page_label, "meta robots", robots_values, "index, follow")
        expect_single_value(errors, page_label, "og:title", parser.meta_properties.get("og:title", []), title)
        expect_single_value(errors, page_label, "og:description", parser.meta_properties.get("og:description", []), description)
        expect_single_value(errors, page_label, "og:type", parser.meta_properties.get("og:type", []), "website")
        expect_single_value(errors, page_label, "og:site_name", parser.meta_properties.get("og:site_name", []), "Eduard Gorbunov")
        if expected_locale:
            expect_single_value(errors, page_label, "og:locale", parser.meta_properties.get("og:locale", []), expected_locale)
        expect_single_value(errors, page_label, "og:image", parser.meta_properties.get("og:image", []), SHARE_IMAGE_URL)
        expect_single_value(
            errors,
            page_label,
            "og:image:secure_url",
            parser.meta_properties.get("og:image:secure_url", []),
            SHARE_IMAGE_URL,
        )
        expect_single_value(
            errors,
            page_label,
            "og:image:alt",
            parser.meta_properties.get("og:image:alt", []),
            expected_share_image_alt,
        )
        expect_single_value(errors, page_label, "og:image:width", parser.meta_properties.get("og:image:width", []), SHARE_IMAGE_WIDTH)
        expect_single_value(errors, page_label, "og:image:height", parser.meta_properties.get("og:image:height", []), SHARE_IMAGE_HEIGHT)
        expect_single_value(errors, page_label, "og:image:type", parser.meta_properties.get("og:image:type", []), SHARE_IMAGE_TYPE)
        expect_single_value(errors, page_label, "twitter:card", parser.meta_names.get("twitter:card", []), "summary_large_image")
        expect_single_value(errors, page_label, "twitter:title", parser.meta_names.get("twitter:title", []), title)
        expect_single_value(errors, page_label, "twitter:description", parser.meta_names.get("twitter:description", []), description)
        expect_single_value(errors, page_label, "twitter:image", parser.meta_names.get("twitter:image", []), SHARE_IMAGE_URL)
        expect_single_value(
            errors,
            page_label,
            "twitter:image:alt",
            parser.meta_names.get("twitter:image:alt", []),
            expected_share_image_alt,
        )

        if not parser.canonical_urls:
            errors.append(f"{page_label}: missing canonical link")
        elif parser.canonical_urls != [expected_page_url]:
            errors.append(f"{page_label}: canonical URL should be {expected_page_url!r}, found {parser.canonical_urls!r}")

        if parser.og_urls != [expected_page_url]:
            errors.append(f"{page_label}: og:url should be {expected_page_url!r}, found {parser.og_urls!r}")

        if has_inline_math:
            if "window.MathJax" not in page_text:
                errors.append(f"{page_label}: inline math present but MathJax configuration is missing")
            if MATHJAX_SCRIPT not in parser.scripts:
                errors.append(f"{page_label}: inline math present but MathJax script is missing")
            if MATHJAX_PRECONNECT not in parser.preconnects:
                errors.append(f"{page_label}: inline math present but MathJax CDN preconnect is missing")
        elif "window.MathJax" in page_text or MATHJAX_SCRIPT in parser.scripts or MATHJAX_PRECONNECT in parser.preconnects:
            errors.append(f"{page_label}: MathJax should only load on pages with inline math")

        h1_count = sum(1 for level, _ in parser.headings if level == 1)
        if h1_count != 1:
            errors.append(f"{page_label}: expected exactly one h1, found {h1_count}")

        previous_level = 0
        for level, text in parser.headings:
            if previous_level and level > previous_level + 1:
                errors.append(f"{page_label}: heading jump h{previous_level}->h{level} at {text!r}")
            previous_level = level

        for name, token in parser.aria_refs:
            if token not in ids:
                errors.append(f"{page_label}: {name} references missing id {token!r}")

        for image in parser.images:
            src = image.get("src", "")
            if "alt" not in image:
                errors.append(f"{page_label}: image missing alt text {src!r}")
            if not image.get("width") or not image.get("height"):
                errors.append(f"{page_label}: image missing width/height {src!r}")

        for time_attr in parser.times:
            datetime_value = time_attr.get("datetime", "")
            if not datetime_value:
                errors.append(f"{page_label}: time element is missing datetime")
            elif not TIME_DATETIME_PATTERN.fullmatch(datetime_value):
                errors.append(f"{page_label}: time datetime should use an ISO date or date-time, found {datetime_value!r}")

        json_ld_nodes: list[dict[str, object]] = []
        for raw in parser.json_ld:
            try:
                duplicate_keys = duplicate_json_keys(raw)
                json_ld_data = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{page_label}: invalid JSON-LD: {exc}")
            else:
                if duplicate_keys:
                    errors.append(f"{page_label}: JSON-LD contains duplicate keys {sorted(set(duplicate_keys))!r}")
                json_ld_nodes.extend(
                    node
                    for node in iter_json_ld_nodes(json_ld_data)
                    if isinstance(node, dict)
                )
        if not json_ld_nodes:
            errors.append(f"{page_label}: missing JSON-LD structured metadata")
        else:
            website_nodes = [
                node
                for node in json_ld_nodes
                if node.get("@id") == f"{SITE_URL}/#website" and json_ld_has_type(node, "WebSite")
            ]
            if not any(
                node.get("url") == f"{SITE_URL}/"
                and node.get("name") == "Eduard Gorbunov"
                and isinstance(node.get("publisher"), dict)
                and node["publisher"].get("@id") == f"{SITE_URL}/#person"
                for node in website_nodes
            ):
                errors.append(f"{page_label}: JSON-LD should define the shared WebSite identity")

            person_nodes = [
                node
                for node in json_ld_nodes
                if node.get("@id") == f"{SITE_URL}/#person" and json_ld_has_type(node, "Person")
            ]
            person_identity_complete = False
            for node in person_nodes:
                affiliation = node.get("affiliation")
                alumni_of = node.get("alumniOf")
                if (
                    node.get("name") == "Eduard Gorbunov"
                    and node.get("url") == f"{SITE_URL}/"
                    and node.get("image") == SIDEBAR_PHOTO_URL
                    and node.get("jobTitle") == "Assistant Professor of Statistics and Data Science"
                    and node.get("email") == "mailto:eduard.gorbunov@mbzuai.ac.ae"
                    and node.get("sameAs") == EXPECTED_PERSON_SAME_AS
                    and node.get("knowsAbout") == EXPECTED_PERSON_KNOWS_ABOUT
                    and isinstance(affiliation, dict)
                    and affiliation.get("@type") == "CollegeOrUniversity"
                    and affiliation.get("name") == "Mohamed bin Zayed University of Artificial Intelligence"
                    and affiliation.get("url") == "https://mbzuai.ac.ae/"
                    and isinstance(alumni_of, dict)
                    and alumni_of.get("@type") == "CollegeOrUniversity"
                    and alumni_of.get("name") == "Moscow Institute of Physics and Technology"
                    and alumni_of.get("url") == "https://mipt.ru/english/"
                ):
                    person_identity_complete = True
                    break
            if not person_identity_complete:
                errors.append(f"{page_label}: JSON-LD should define the enriched shared Person identity")

            url_nodes = [node for node in json_ld_nodes if node.get("url") == expected_page_url]
            if not url_nodes:
                errors.append(f"{page_label}: structured metadata should describe {expected_page_url!r}")
            elif not any(node.get("dateModified") == SITEMAP_LASTMOD for node in url_nodes):
                errors.append(f"{page_label}: structured metadata should use dateModified {SITEMAP_LASTMOD!r}")

        if FOOTER_UPDATED_TEXT not in page_text:
            errors.append(f"{page_label}: visible footer update date should match {SITEMAP_LASTMOD}")

        for asset in parser.assets:
            if asset.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            path = local_path(page, asset)
            if not path.exists():
                errors.append(f"{page_label}: missing asset {asset!r}")

        for link in parser.links:
            href = link.get("href", "")
            label = link.get("label", "").strip()
            rel = set(link.get("rel", "").split())
            href_lower = href.lower()
            href_without_fragment = href_lower.split("#", 1)[0]
            href_without_query = href_without_fragment.split("?", 1)[0]
            is_direct_pdf_link = (
                href_without_query.endswith(".pdf")
                or href_lower.startswith("https://arxiv.org/pdf/")
                or href_lower.startswith("http://arxiv.org/pdf/")
                or href_lower.startswith("https://openreview.net/pdf")
                or href_lower.startswith("http://openreview.net/pdf")
            )

            if link.get("target") == "_blank" and not {"noopener", "noreferrer"} <= rel:
                errors.append(f"{page_label}: new-tab link missing noopener/noreferrer {href!r}")

            if is_direct_pdf_link:
                if link.get("type") != "application/pdf":
                    errors.append(f"{page_label}: direct PDF link should declare type='application/pdf' {href!r}")

            if href.startswith(("http://", "https://")):
                if link.get("target") != "_blank":
                    errors.append(f"{page_label}: external link should open in a new tab {href!r}")
                if not {"noopener", "noreferrer"} <= rel:
                    errors.append(f"{page_label}: external link missing noopener/noreferrer {href!r}")
                if len(label) <= 8 and not link.get("aria-label"):
                    errors.append(
                        f"{page_label}: short external link {label!r} should use a contextual aria-label"
                    )
                continue

            if href.startswith(("mailto:", "tel:")):
                continue

            path_part = urlsplit(href).path
            fragment = local_fragment(href)
            if not path_part:
                if fragment and fragment not in ids:
                    errors.append(f"{page_label}: missing local anchor {href!r}")
                continue

            target_path = local_path(page, href)
            if not target_path.exists():
                errors.append(f"{page_label}: missing link target {href!r}")
                continue

            if fragment and target_path.suffix == ".html":
                target_parser = parsers.get(target_path.name)
                if target_parser and fragment not in set(target_parser.ids):
                    errors.append(f"{page_label}: missing target anchor {href!r}")

    return errors


def check_homepage_news() -> list[str]:
    errors: list[str] = []
    page = ROOT / "index.html"
    if not page.exists():
        errors.append("index.html: missing file")
        return errors

    page_text = page.read_text(encoding="utf-8", errors="ignore")
    parser = NewsParser()
    parser.feed(page_text)
    featured_venue_parser = FeaturedNewsVenueParser()
    featured_venue_parser.feed(page_text)

    required_news_schema = [
        '"@type": "CollectionPage"',
        '"@id": "https://eduardgorbunov.github.io/#news-page"',
        '"@id": "https://eduardgorbunov.github.io/#recent-news"',
        '"name": "Recent news updates"',
        '"numberOfItems": 5',
        '"itemListOrder": "https://schema.org/ItemListOrderDescending"',
        '"url": "https://eduardgorbunov.github.io/#news-2026-conference-acceptances"',
        '"url": "https://eduardgorbunov.github.io/#news-2025-dp-clipped-sgd"',
        '"url": "https://eduardgorbunov.github.io/#news-2025-iclr-icml-appointment"',
        '"url": "https://eduardgorbunov.github.io/#news-2024-neurips-preprint"',
        '"url": "https://eduardgorbunov.github.io/#news-2024-emnlp-findings"',
    ]
    for snippet in required_news_schema:
        if snippet not in page_text:
            errors.append(f"index.html: recent-news structured metadata should include {snippet!r}")

    required_person_schema = [
        '"@type": "Person"',
        '"@id": "https://eduardgorbunov.github.io/#person"',
        '"jobTitle": "Assistant Professor of Statistics and Data Science"',
        '"affiliation": {',
        '"name": "Mohamed bin Zayed University of Artificial Intelligence"',
        '"sameAs": [',
        '"alumniOf": {',
        '"name": "Moscow Institute of Physics and Technology"',
        '"knowsAbout": [',
    ]
    for snippet in required_person_schema:
        if snippet not in page_text:
            errors.append(f"index.html: person structured metadata should include {snippet!r}")

    required_snippets = [
        "2026 conference acceptances",
        "My collaborators and I had several papers accepted at 2026 conferences: one at AISTATS, one at ICLR, five at ICML, two at CPAL, and two at UAI.",
        "publications.html#pub-differentially-private-clipped-sgd",
        "publications.html#pub-last-iterate-clipped-sgd",
        "publications.html#pub-heavy-tailed-data-gradient-clipping",
        "publications.html#pub-lmo-optimizers-bounded-variance",
        "publications.html#pub-anchored-goma",
        "publications.html#pub-batch-size-conditional-gradient",
        "publications.html#pub-batch-noise-adaptivity-compression",
        "publications.html#pub-byzantine-l0-l1-smoothness",
        "publications.html#pub-federated-learning-friends",
        "publications.html#pub-byzantine-private-federated-optimization",
        "publications.html#pub-federated-distillation-trust",
        "Differentially Private Clipped-SGD",
        "High-Probability Bounds for the Last Iterate of Clipped SGD",
        "Optimization to Generalization under Heavy-Tailed Data",
        "Batch Noise, Adaptivity, and Compression under $(L_0,L_1)$-Smoothness",
        "Who to Trust? Federated Distillation",
        '<span class="eg-news-venue-count">5 papers</span>',
    ]
    for snippet in required_snippets:
        if snippet not in page_text:
            errors.append(f"index.html: featured news should include {snippet!r}")

    if "Eleven papers accepted to AISTATS" in page_text:
        errors.append("index.html: featured news headline should use compact academic wording")
    if "Accepted papers at AISTATS, ICLR, ICML, CPAL, and UAI 2026" in page_text:
        errors.append("index.html: featured news headline should avoid overlong venue lists")
    if "Recent joint works were accepted to 2026 venues" in page_text:
        errors.append("index.html: featured news lead should use polished conference wording")
    old_featured_labels = [
        ">differentially private Clipped-SGD<",
        ">last-iterate clipped SGD<",
        ">heavy-tailed data and clipping<",
        ">anchored GOMA<",
        ">federated distillation<",
    ]
    for label in old_featured_labels:
        if label in page_text:
            errors.append(f"index.html: featured news should use polished paper label instead of {label!r}")

    disallowed_news_phrases = {
        "Our new preprint studies": "first-person preprint wording",
        "Our work <a": "first-person paper wording",
        "I joined MBZUAI": "first-person appointment wording",
        "ICLR 2025, ICML 2025, new preprints": "note-like conference headline",
        "Promotion, conference updates": "informal appointment headline",
        "Promotion to Research Scientist": "informal appointment wording",
        ">Joined <a": "note-like appointment wording",
        "Started a postdoctoral researcher position": "fragment-like postdoctoral appointment wording",
    }
    for phrase, description in disallowed_news_phrases.items():
        if phrase in page_text:
            errors.append(f"index.html: news copy should avoid {description}")
    required_news_tone_phrases = [
        "A new preprint studies high-probability convergence with an arbitrary clipping level.",
        "I started as an Assistant Professor in the Department of Statistics and Data Science at MBZUAI on August 1, 2025.",
        "Research Scientist appointment, conference updates, and a new preprint",
        "I started as a Research Scientist at MBZUAI on April 1, 2024.",
        "The paper <a href=\"https://arxiv.org/abs/2406.12564\"",
        "I started as a postdoctoral researcher at <a href=\"https://mbzuai.ac.ae/\"",
    ]
    for phrase in required_news_tone_phrases:
        if phrase not in page_text:
            errors.append(f"index.html: news copy should use polished wording {phrase!r}")
    if "The appointment as Assistant Professor of Statistics and Data Science at MBZUAI started on August 1, 2025." in page_text:
        errors.append("index.html: appointment news item should use department-level role wording")
    compressed_home_description = (
        "News and research updates from Eduard Gorbunov, "
        "Assistant Professor of Statistics and Data Science at MBZUAI."
    )
    if compressed_home_description in page_text:
        errors.append("index.html: homepage metadata should use department-level role wording")

    expected_featured_venues = [
        "AISTATS 2026",
        "ICLR 2026",
        "ICML 2026",
        "CPAL 2026",
        "UAI 2026",
    ]
    featured_venues = [str(group.get("venue", "")) for group in featured_venue_parser.groups]
    if featured_venues != expected_featured_venues:
        errors.append(
            f"index.html: featured news venues should be {expected_featured_venues!r}, "
            f"found {featured_venues!r}"
        )
    expected_featured_accents = ["gold", "teal", "blue", "rose", "indigo"]
    featured_accents = [str(group.get("accent", "")) for group in featured_venue_parser.groups]
    if featured_accents != expected_featured_accents:
        errors.append(
            f"index.html: featured news venue accents should be {expected_featured_accents!r}, "
            f"found {featured_accents!r}"
        )
    featured_count_total = 0
    for group in featured_venue_parser.groups:
        venue = str(group.get("venue", ""))
        venue_count = parse_leading_int(group.get("count", ""))
        if venue_count is None:
            errors.append(f"index.html: featured news venue {venue!r} has invalid count {group.get('count', '')!r}")
            continue
        featured_count_total += venue_count
    if featured_count_total != 11:
        errors.append(
            "index.html: featured news accepted-paper count "
            f"should total 11, found {featured_count_total}"
        )

    publications_page = ROOT / "publications.html"
    if not publications_page.exists():
        errors.append("index.html: missing publications.html for featured news venue checks")
    else:
        publication_parser = PublicationParser()
        publication_parser.feed(publications_page.read_text(encoding="utf-8", errors="ignore"))
        publications_by_id = {
            str(card.get("id", "")): card
            for card in publication_parser.cards
        }
        for group in featured_venue_parser.groups:
            venue = str(group.get("venue", ""))
            hrefs_object = group.get("hrefs", [])
            hrefs = [str(href) for href in hrefs_object] if isinstance(hrefs_object, list) else []
            linked_ids: list[str] = []
            for href in hrefs:
                if not href.startswith("publications.html#"):
                    errors.append(f"index.html: featured news venue {venue!r} has non-publication link {href!r}")
                    continue
                linked_ids.append(href.split("#", 1)[1])

            expected_ids = [
                str(card.get("id", ""))
                for card in publication_parser.cards
                if str(card.get("type", "")) == "conference paper"
                and str(card.get("venue", "")).startswith(venue)
            ]
            expected_count = f"{len(expected_ids)} {'paper' if len(expected_ids) == 1 else 'papers'}"
            if str(group.get("count", "")) != expected_count:
                errors.append(
                    f"index.html: featured news venue {venue!r} should show count {expected_count!r}, "
                    f"found {group.get('count', '')!r}"
                )
            if venue in expected_featured_venues and linked_ids != expected_ids:
                errors.append(
                    f"index.html: featured news venue {venue!r} should link to {expected_ids!r}, "
                    f"found {linked_ids!r}"
                )

            for card_id in linked_ids:
                card = publications_by_id.get(card_id)
                if card is None:
                    errors.append(f"index.html: featured news links unknown publication {card_id!r}")
                elif not str(card.get("venue", "")).startswith(venue):
                    errors.append(
                        f"index.html: featured news links {card_id!r} under {venue!r}, "
                        f"but publication venue is {card.get('venue', '')!r}"
                    )

    required_news_sections = [
        '<nav class="eg-news-year-index eg-news-year-index-plain" aria-label="News by year">',
        '<section class="eg-news-list" role="list" aria-label="Recent news updates">',
        '<section class="eg-news-archive-list" role="list" aria-label="Archived news updates">',
    ]
    for snippet in required_news_sections:
        if page_text.count(snippet) != 1:
            errors.append(f"index.html: expected one semantic news collection {snippet!r}")
    generic_news_link_labels = {"view publications", "publications", "slides", "poster", "paper", "video"}
    news_card_blocks = re.findall(
        r'<article\b[^>]*class="eg-news-card[^"]*"[^>]*>(.*?)</article>',
        page_text,
        flags=re.DOTALL,
    )
    unlabeled_generic_news_links: list[str] = []
    for block in news_card_blocks:
        for attrs, label_html in re.findall(r"<a\s+([^>]*)>(.*?)</a>", block, flags=re.DOTALL):
            link_label = " ".join(re.sub(r"<[^>]+>", "", label_html).split())
            if link_label.lower() not in generic_news_link_labels:
                continue
            aria_match = re.search(r'aria-label="([^"]+)"', attrs)
            aria_label = unescape(aria_match.group(1)) if aria_match else ""
            if not aria_label or aria_label.lower() == link_label.lower():
                unlabeled_generic_news_links.append(link_label)
    if unlabeled_generic_news_links:
        errors.append(
            "index.html: generic news links should have contextual aria-labels "
            f"({unlabeled_generic_news_links[:5]!r})"
        )

    if parser.news_list_attrs is None or parser.news_list_attrs.get("role") != "list":
        errors.append("index.html: recent news collection should expose role='list'")
    if parser.archive_list_attrs is None or parser.archive_list_attrs.get("role") != "list":
        errors.append("index.html: archived news collection should expose role='list'")
    if parser.archive_details_attrs is None or parser.archive_details_attrs.get("role") != "listitem":
        errors.append("index.html: earlier-updates disclosure should be a list item in the recent news list")

    required_news_shortcuts = [
        '<details class="eg-news-archive" id="earlier-updates" role="listitem">',
    ]
    if "news updates from 2022-2026" in page_text:
        errors.append("index.html: news overview should avoid ledger-style date-range wording")
    if '<a href="publications.html" aria-label="Browse the complete publications list">Browse publications</a>' not in page_text:
        errors.append("index.html: featured news action should use 'Browse publications'")
    if "View publications" in page_text:
        errors.append("index.html: featured news action should avoid generic 'View publications' wording")
    for snippet in required_news_shortcuts:
        if snippet not in page_text:
            errors.append(f"index.html: missing compact news shortcut {snippet!r}")
    required_year_links = [
        '<a href="#news-2026-conference-acceptances">2026</a>',
        '<a href="#news-2025-dp-clipped-sgd">2025</a>',
        '<a href="#news-2024-neurips-preprint">2024</a>',
        '<a href="#news-2023-11-28-new-preprints-a-talk-and-neurips-2023-papers">2023</a>',
        '<a href="#earlier-updates">2022</a>',
    ]
    if '<span>Years</span>' not in page_text:
        errors.append("index.html: year index should have a compact visible label")
    if "5 archived" in page_text or "archived items" in page_text:
        errors.append("index.html: news archive labels should use visitor-facing update wording")
    for snippet in required_year_links:
        if snippet not in page_text:
            errors.append(f"index.html: missing news year-index link {snippet!r}")
    news_year_index = page_text.split('<nav class="eg-news-year-index eg-news-year-index-plain"', 1)[-1].split("</nav>", 1)[0]
    if news_year_index.count("<a ") != len(required_year_links):
        errors.append("index.html: news year index should contain one link per covered year")
    if 'class="eg-news-overview-card"' in page_text or 'class="eg-profile-links eg-news-shortcuts"' in page_text:
        errors.append("index.html: news page should avoid extra overview and shortcut cards")

    old_news_date_patterns = [
        r'<time datetime="\d{4}-\d{2}-\d{2}">\d{1,2} [A-Z][a-z]+,? \d{4}</time>',
        r'<time datetime="\d{4}-\d{2}-\d{2}">\d{1,2}-\d{1,2} [A-Z][a-z]+,? \d{4}</time>',
        r'<time datetime="\d{4}-\d{2}-\d{2}">\d{1,2} [A-Z][a-z]+ - \d{1,2} [A-Z][a-z]+,? \d{4}</time>',
    ]
    for pattern in old_news_date_patterns:
        if re.search(pattern, page_text):
            errors.append("index.html: news dates should use Month Day, Year display style")

    if len(parser.cards) < 10:
        errors.append(f"index.html: expected a substantive news archive, found {len(parser.cards)} cards")

    news_datetimes = [card["datetime"] for card in parser.cards if card["datetime"]]
    if news_datetimes != sorted(news_datetimes, reverse=True):
        errors.append("index.html: news cards should be ordered from newest to oldest")

    card_ids = [card["id"] for card in parser.cards]
    missing_card_ids = [index for index, card_id in enumerate(card_ids, start=1) if not card_id]
    duplicate_card_ids = sorted(card_id for card_id, count in Counter(card_ids).items() if card_id and count > 1)
    if missing_card_ids:
        errors.append(f"index.html: news cards missing ids {missing_card_ids}")
    if duplicate_card_ids:
        errors.append(f"index.html: duplicate news card ids {duplicate_card_ids}")

    for index, card in enumerate(parser.cards, start=1):
        card_id = card["id"]
        expected_title_id = f"{card_id}-title" if card_id else ""
        if not card["title"]:
            errors.append(f"index.html: news card {index} is missing a title")
        if not card["datetime"]:
            errors.append(f"index.html: news card {index} is missing a datetime")
        elif not TIME_DATETIME_PATTERN.fullmatch(card["datetime"]):
            errors.append(f"index.html: news card {index} has invalid datetime {card['datetime']!r}")
        if card["heading_id"] != expected_title_id:
            errors.append(
                f"index.html: news card {index} heading id should be {expected_title_id!r}, "
                f"found {card['heading_id']!r}"
            )
        if card["labelledby"] != expected_title_id:
            errors.append(
                f"index.html: news card {index} aria-labelledby should be {expected_title_id!r}, "
                f"found {card['labelledby']!r}"
            )
        if card.get("role") != "listitem":
            errors.append(f"index.html: news card {index} should expose role='listitem'")

    return errors


def check_publications() -> list[str]:
    errors: list[str] = []
    page = ROOT / "publications.html"
    if not page.exists():
        errors.append("publications.html: missing file")
        return errors

    page_text = page.read_text(encoding="utf-8", errors="ignore")
    if "</article><article" in page_text or re.search(r"</article>[ \t]+<article", page_text):
        errors.append("publications.html: publication cards should be separated by newlines in source")

    parser = PublicationParser()
    parser.feed(page_text)

    if "compact filters by venue type and topic" in page_text:
        errors.append("publications.html: page intro should avoid feature-description wording")
    required_publication_schema = [
        '"@type": "CollectionPage"',
        '"mainEntity": {',
        '"@type": "ItemList"',
        '"@id": "https://eduardgorbunov.github.io/publications.html#publication-list"',
        '"name": "Publication list"',
        '"itemListOrder": "https://schema.org/ItemListOrderDescending"',
        '"itemListElement": [',
        '"url": "https://eduardgorbunov.github.io/publications.html#pub-last-iterate-clipped-sgd"',
        '"url": "https://eduardgorbunov.github.io/publications.html#pub-heavy-tailed-data-gradient-clipping"',
        '"url": "https://eduardgorbunov.github.io/publications.html#pub-lmo-optimizers-bounded-variance"',
        '"url": "https://eduardgorbunov.github.io/publications.html#pub-anchored-goma"',
        '"url": "https://eduardgorbunov.github.io/publications.html#pub-last-iterate-convergence-of-adagrad-norm-for-convex-non-smooth-optimization"',
    ]
    for snippet in required_publication_schema:
        if snippet not in page_text:
            errors.append(f"publications.html: structured metadata should include {snippet!r}")
    required_publication_shortcuts = [
        '<section class="eg-publication-overview" id="publication-overview" aria-label="Publication overview" role="list">',
        '<section class="eg-conference-summary" id="major-ai-conferences" aria-label="My major AI conference paper counts">',
        '<div class="eg-conference-summary-header">',
        '<small>Where my papers appeared</small>',
        '<form class="eg-publication-controls" id="publication-filters" role="search" aria-label="Publication filters">',
        '<div class="eg-filter-heading">',
        '<h2 id="publication-filters-heading">Filter publications</h2>',
        '<span>Type · venue · topic · search</span>',
    ]
    for snippet in required_publication_shortcuts:
        if snippet not in page_text:
            errors.append(f"publications.html: missing compact publication shortcut {snippet!r}")
    if 'class="eg-profile-links eg-publication-shortcuts"' in page_text:
        errors.append("publications.html: publication page should avoid redundant shortcut buttons")
    if '<a href="#major-ai-conferences">AI conference counts</a>' in page_text:
        errors.append("publications.html: publication shortcut should avoid mechanical count wording")
    if '<a href="#publication-list">Publication list</a>' in page_text:
        errors.append("publications.html: publication list shortcut should use visitor-facing wording")
    publication_overview = page_text.split('<section class="eg-publication-overview"', 1)[-1].split("</section>", 1)[0]
    if publication_overview.count('class="eg-publication-stat"') != 5 or publication_overview.count('role="listitem"') != 5:
        errors.append("publications.html: all publication overview stats should expose role='listitem'")
    if '<article class="eg-publication-stat"' in publication_overview:
        errors.append("publications.html: publication overview stats should be linked cards, not passive articles")
    if "<span>reference work entries</span>" in publication_overview:
        errors.append("publications.html: publication overview should use concise reference-entry wording")
    expected_publication_stat_links = [
        ("all", "publications.html#publication-list"),
        ("conference", "publications.html?type=conference%20paper#publication-list"),
        ("journal", "publications.html?type=journal%20paper#publication-list"),
        ("preprint", "publications.html?type=arXiv%20preprint#publication-list"),
        ("reference", "publications.html?type=living%20reference%20work%20entry#publication-list"),
    ]
    actual_publication_stat_links = [
        (attrs.get("data-kind", ""), attrs.get("href", ""))
        for attrs in parser.publication_stat_links
    ]
    if actual_publication_stat_links != expected_publication_stat_links:
        errors.append(
            "publications.html: publication overview stat links should be "
            f"{expected_publication_stat_links!r}, found {actual_publication_stat_links!r}"
        )
    if '<span>Major AI conferences</span>' not in page_text:
        errors.append("publications.html: major AI counter should use the requested compact label")
    if '<span>My major AI conference papers</span>' in page_text:
        errors.append("publications.html: major AI counter should avoid the older paper-count title")
    if '<span>Major AI venues</span>' in page_text:
        errors.append("publications.html: major AI counter label should not use the vague 'venues' wording")
    if '<li data-venue=' in page_text:
        errors.append("publications.html: venue counters should use accessible filter buttons")
    expected_control_targets = set(PUBLICATION_FILTER_TARGETS.split())
    if "all publications</span>" in page_text or "eg-venue-reset" in page_text:
        errors.append("publications.html: major AI conference counter should not include an all-publications tile")
    expected_venues = ["NeurIPS", "ICML", "AISTATS", "ICLR", "UAI", "CPAL", "COLT", "EMNLP"]
    actual_venue_buttons = [attrs.get("data-venue", "") for attrs in parser.venue_filter_buttons]
    if actual_venue_buttons != expected_venues:
        errors.append(f"publications.html: venue filter buttons should be {expected_venues!r}, found {actual_venue_buttons!r}")
    expected_venue_accents = ["blue", "teal", "blue", "teal", "blue", "teal", "blue", "teal"]
    actual_venue_accents = [attrs.get("data-accent", "") for attrs in parser.venue_filter_buttons]
    if actual_venue_accents != expected_venue_accents:
        errors.append(
            f"publications.html: venue filter buttons should use accents {expected_venue_accents!r}, "
            f"found {actual_venue_accents!r}"
        )
    for attrs in parser.venue_filter_buttons:
        venue = attrs.get("data-venue", "")
        if attrs.get("type") != "button":
            errors.append(f"publications.html: {venue} venue filter should be type='button'")
        if attrs.get("aria-label") != f"Show {venue} conference papers":
            errors.append(f"publications.html: {venue} venue filter should have a descriptive aria-label")
        if attrs.get("aria-pressed") != "false":
            errors.append(f"publications.html: {venue} venue filter should start with aria-pressed='false'")
        venue_targets = set(attrs.get("aria-controls", "").split())
        if venue_targets != expected_control_targets:
            errors.append(
                f"publications.html: {venue} venue filter should control publication list, count status, and filter summary"
            )
    if 'class="eg-publication-actions eg-book-actions"' not in page_text:
        errors.append("publications.html: book card actions should reuse publication action styling")
    required_book_labels = [
        '<section class="eg-book-section" id="book" aria-labelledby="book-heading">',
        '<h2 id="book-heading"><a href="https://books.mipt.ru/book/301236"',
        '>Stochastic Processes</a></h2>',
        '<div class="eg-publication-meta"><span>Book</span><span class="eg-publication-status-badge">Published</span><span>2019</span></div>',
        "Published by MIPT Books; arXiv version 1907.01060.",
        'aria-label="Open Book page for Stochastic Processes">Book page</a>',
    ]
    for snippet in required_book_labels:
        if snippet not in page_text:
            errors.append(f"publications.html: book section should be labelled by its title {snippet!r}")
    publication_action_blocks = re.findall(
        r'<div class="eg-publication-actions(?: [^"]*)?">(.*?)</div>',
        page_text,
        flags=re.DOTALL,
    )
    publication_action_link_count = 0
    poorly_named_publication_actions: list[str] = []
    for block in publication_action_blocks:
        for attrs, label_html in re.findall(r"<a\s+([^>]*)>(.*?)</a>", block, flags=re.DOTALL):
            publication_action_link_count += 1
            link_label = re.sub(r"<[^>]+>", "", label_html).strip()
            aria_match = re.search(r'aria-label="([^"]+)"', attrs)
            aria_label = unescape(aria_match.group(1)) if aria_match else ""
            if not re.fullmatch(r"Open .+ for .+", aria_label):
                poorly_named_publication_actions.append(link_label or attrs)
    if publication_action_link_count == 0:
        errors.append("publications.html: publication action links should be present")
    if poorly_named_publication_actions:
        errors.append(
            "publications.html: every publication action link should have a contextual aria-label "
            f"like 'Open PDF for Title' ({poorly_named_publication_actions[:5]!r})"
        )
    required_book_metadata = [
        '"@type": "Book"',
        '"@id": "https://eduardgorbunov.github.io/publications.html#book-stochastic-processes"',
        '"name": "Stochastic Processes"',
        '"url": "https://books.mipt.ru/book/301236"',
        '"datePublished": "2019"',
        '"@id": "https://eduardgorbunov.github.io/#person"',
        '"name": "MIPT Books"',
        '"sameAs": "https://arxiv.org/abs/1907.01060"',
        '"contentUrl": "https://arxiv.org/pdf/1907.01060.pdf"',
        '"encodingFormat": "application/pdf"',
    ]
    for snippet in required_book_metadata:
        if snippet not in page_text:
            errors.append(f"publications.html: Book JSON-LD should include {snippet!r}")
    if "Lecture Notes on Stochastic Processes" in page_text:
        errors.append("publications.html: book card should not foreground lecture-notes wording")
    publication_type_badge_count = page_text.count('class="eg-publication-type-badge"')
    if publication_type_badge_count != len(parser.cards):
        errors.append(
            "publications.html: every publication card should expose an explicit publication type badge "
            f"({publication_type_badge_count} badges for {len(parser.cards)} cards)"
        )
    if parser.book_card != {"id": "book-stochastic-processes", "labelledby": "book-heading"}:
        errors.append(
            "publications.html: book card should use id 'book-stochastic-processes' "
            f"and aria-labelledby 'book-heading', found {parser.book_card!r}"
        )

    if parser.filter_form_attrs is None:
        errors.append("publications.html: publication filters should use a semantic form")
    else:
        if parser.filter_form_attrs.get("role") != "search":
            errors.append("publications.html: publication filter form should use role='search'")
        if parser.filter_form_attrs.get("aria-label") != "Publication filters":
            errors.append("publications.html: publication filter form should keep the shared accessible label")

    expected_filter_script = f"{PUBLICATION_FILTER_SCRIPT}?v={PUBLICATION_FILTER_SCRIPT_VERSION}"
    if PUBLICATION_FILTER_SCRIPT not in {src.split("?", 1)[0] for src in parser.scripts}:
        errors.append("publications.html: missing publication filter script")
    elif expected_filter_script not in parser.scripts:
        errors.append(f"publications.html: publication filter script should be versioned as {expected_filter_script!r}")

    expected_type_options = {"all", "conference paper", "journal paper", "arXiv preprint", "living reference work entry"}
    if parser.type_options != expected_type_options:
        errors.append(f"publications.html: unexpected publication type options {sorted(parser.type_options)}")

    expected_control_labels = {
        "type": "Filter publications by type",
        "search": "Search publications by title, author, venue, or topic tag",
        "tag": "Add a publication topic tag filter",
    }
    for control_name in ("type", "search", "tag"):
        attrs = parser.filter_controls.get(control_name)
        if not attrs:
            errors.append(f"publications.html: missing {control_name} publication filter control")
            continue
        aria_targets = set(attrs.get("aria-controls", "").split())
        if aria_targets != expected_control_targets:
            errors.append(f"publications.html: {control_name} filter should control publication list, count status, and filter summary")
        if attrs.get("aria-label") != expected_control_labels[control_name]:
            errors.append(f"publications.html: {control_name} filter should use aria-label {expected_control_labels[control_name]!r}")

    tag_attrs = parser.filter_controls.get("tag", {})
    if tag_attrs and tag_attrs.get("aria-describedby") != "selected-topic-tags topic-tag-help":
        errors.append("publications.html: tag filter should describe selected topic tags and hidden helper text")
    if '<p id="topic-tag-help" class="eg-visually-hidden">Use the tag menu to add filters. Activate a selected topic chip to remove that filter.</p>' not in page_text:
        errors.append("publications.html: missing hidden topic tag filter helper text")

    if parser.active_tag_list_attrs is None:
        errors.append("publications.html: missing selected topic tag status")
    else:
        expected_active_tag_attrs = {
            "id": "selected-topic-tags",
            "role": "status",
            "aria-live": "polite",
            "aria-atomic": "true",
            "aria-label": "Selected topic tags",
        }
        for name, value in expected_active_tag_attrs.items():
            if parser.active_tag_list_attrs.get(name) != value:
                errors.append(f"publications.html: selected topic tag status should have {name}={value!r}")

    search_attrs = parser.filter_controls.get("search", {})
    if search_attrs and search_attrs.get("type") != "search":
        errors.append("publications.html: search filter should use input type='search'")
    if search_attrs and search_attrs.get("placeholder") != "Title, author, venue, topic":
        errors.append("publications.html: search filter should advertise title, author, venue, and topic search")
    if search_attrs and search_attrs.get("autocomplete") != "off":
        errors.append("publications.html: search filter should disable autocomplete")
    if search_attrs and search_attrs.get("enterkeyhint") != "search":
        errors.append("publications.html: search filter should request a search keyboard action")
    if search_attrs and search_attrs.get("spellcheck") != "false":
        errors.append("publications.html: search filter should disable spellcheck for names and venues")

    if len(parser.clear_filter_buttons) != 1:
        errors.append(f"publications.html: expected one clear-filter button, found {len(parser.clear_filter_buttons)}")
    else:
        clear_attrs = parser.clear_filter_buttons[0]
        clear_targets = set(clear_attrs.get("aria-controls", "").split())
        if clear_targets != expected_control_targets:
            errors.append("publications.html: clear-filter button should control publication list, count status, and filter summary")
        if "disabled" not in clear_attrs:
            errors.append("publications.html: clear-filter button should be disabled until a filter is active")
        if "hidden" not in clear_attrs:
            errors.append("publications.html: clear-filter button should be hidden until a filter is active")
        if not clear_attrs.get("aria-label"):
            errors.append("publications.html: clear-filter button should have an aria-label")

    if parser.count_status_attrs is None:
        errors.append("publications.html: missing publication count status")
    elif parser.count_status_attrs.get("role") != "status" or parser.count_status_attrs.get("aria-live") != "polite":
        errors.append("publications.html: publication count status should be polite live status text")
    if '<div id="publication-filter-summary" class="eg-publication-filter-summary" role="status" aria-live="polite" aria-atomic="true">No filters applied.</div>' not in page_text:
        errors.append("publications.html: missing polite active-filter summary status")
    expected_noscript = (
        '<noscript><p class="eg-publication-filter-summary eg-publication-noscript">'
        'Publication filters require JavaScript; the complete publication list remains visible below.'
        '</p></noscript>'
    )
    if expected_noscript not in page_text:
        errors.append("publications.html: missing no-JavaScript fallback note for publication filters")
    if parser.count_status_attrs and parser.count_status_attrs.get("aria-atomic") != "true":
        errors.append("publications.html: publication count status should be atomic")
    required_publication_legend = [
        '<div class="eg-publication-legend" aria-label="Publication notation">',
        '<span><strong>Bold</strong>&nbsp;highlights my name</span>',
        '<span><sup>*</sup> equal contribution</span>',
        '<span><sup>†</sup> shared senior authorship</span>',
        '<button type="button" class="eg-abstract-toggle" aria-controls="publication-list" aria-pressed="false">Expand abstracts</button>',
    ]
    for snippet in required_publication_legend:
        if snippet not in page_text:
            errors.append(f"publications.html: publication notation legend should include {snippet!r}")

    if parser.publication_list_attrs is None:
        errors.append("publications.html: missing publication list container")
    else:
        if parser.publication_list_tag != "section":
            errors.append("publications.html: publication results should use a labelled section")
        if parser.publication_list_attrs.get("role") != "list":
            errors.append("publications.html: publication results should expose role='list'")
        if parser.publication_list_attrs.get("aria-label") != "Publication results":
            errors.append("publications.html: publication results should have aria-label='Publication results'")
        expected_results_description = "publication-filter-summary publication-count-status"
        if parser.publication_list_attrs.get("aria-describedby") != expected_results_description:
            errors.append(
                "publications.html: publication results should be described by "
                f"{expected_results_description!r}"
            )

    if len(parser.empty_states) != 1:
        errors.append(f"publications.html: expected one empty publication filter state, found {len(parser.empty_states)}")
    elif "hidden" not in parser.empty_states[0]:
        errors.append("publications.html: empty publication filter state should be hidden by default")

    if parser.all_stat != len(parser.cards):
        errors.append(f"publications.html: total counter {parser.all_stat!r} does not match {len(parser.cards)} cards")
    expected_item_count = f'"numberOfItems": {len(parser.cards)}'
    if expected_item_count not in page_text:
        errors.append(f"publications.html: ItemList metadata should use {expected_item_count!r}")

    card_ids = [str(card.get("id", "")) for card in parser.cards]
    missing_card_ids = [index for index, card_id in enumerate(card_ids, start=1) if not card_id]
    duplicate_card_ids = sorted(card_id for card_id, count in Counter(card_ids).items() if card_id and count > 1)
    if missing_card_ids:
        errors.append(f"publications.html: publication cards missing ids {missing_card_ids}")
    if duplicate_card_ids:
        errors.append(f"publications.html: duplicate publication card ids {duplicate_card_ids}")

    type_counts = Counter(str(card.get("type", "")) for card in parser.cards)
    for publication_type, displayed_count in sorted(parser.type_stats.items()):
        actual_count = type_counts[publication_type]
        if displayed_count != actual_count:
            errors.append(
                f"publications.html: {publication_type!r} counter {displayed_count} does not match {actual_count} cards"
            )

    card_tags = {tag for card in parser.cards for tag in card.get("tags", set()) if tag}
    missing_options = sorted(card_tags - parser.tag_options)
    unused_options = sorted(parser.tag_options - card_tags)
    if missing_options:
        errors.append(f"publications.html: tags missing filter options {missing_options}")
    if unused_options:
        errors.append(f"publications.html: unused tag filter options {unused_options}")
    convex_card_ids = {
        str(card.get("id", ""))
        for card in parser.cards
        if "convex-optimization" in card.get("tags", set())
    }
    expected_convex_publications = {
        "pub-last-iterate-clipped-sgd",
        "pub-heavy-tailed-data-gradient-clipping",
        "pub-last-iterate-convergence-of-adagrad-norm-for-convex-non-smooth-optimization",
        "pub-differentially-private-clipped-sgd",
        "pub-convergence-of-clipped-sgd-for-convex-l0-l1-smooth-optimization-with-heavy",
        "pub-linear-convergence-rate-in-convex-setup-is-possible-gradient-descent-method-variants",
        "pub-methods-for-convex-l0-l1-smooth-optimization-clipping-acceleration-and-adaptivity",
        "pub-clipping-improves-adam-norm-and-adagrad-norm-when-the-noise-is-heavy",
        "pub-median-clipping-for-zeroth-order-non-smooth-convex-optimization-and-multi-armed",
        "pub-accelerated-zeroth-order-method-for-non-smooth-stochastic-convex-optimization-problem-with",
        "pub-high-probability-convergence-for-composite-and-distributed-stochastic-minimization-and-variational-inequalities",
        "pub-intermediate-gradient-methods-with-relative-inexactness",
        "pub-unified-analysis-of-sgd-type-methods",
        "pub-byzantine-robust-loopless-stochastic-variance-reduced-gradient",
        "pub-high-probability-bounds-for-stochastic-optimization-and-variational-inequalities-the-case-of",
        "pub-randomized-gradient-free-methods-in-convex-optimization",
        "pub-distributed-methods-with-absolute-compression-and-error-compensation",
        "pub-high-probability-complexity-bounds-for-non-smooth-stochastic-optimization-with-heavy-tailed",
        "pub-recent-theoretical-advances-in-decentralized-distributed-convex-optimization",
        "pub-local-sgd-unified-theory-and-new-efficient-methods",
        "pub-linearly-converging-error-compensated-sgd",
        "pub-stochastic-optimization-with-heavy-tailed-noise-via-accelerated-gradient-clipping",
        "pub-derivative-free-method-for-decentralized-distributed-non-smooth-optimization",
        "pub-optimal-decentralized-distributed-algorithms-for-stochastic-convex-optimization",
        "pub-a-stochastic-derivative-free-optimization-method-with-momentum",
        "pub-a-unified-theory-of-sgd-variance-reduction-sampling-quantization-and-coordinate-descent",
        "pub-on-primal-dual-approach-for-distributed-stochastic-convex-optimization-over-networks",
        "pub-stochastic-three-points-method-for-unconstrained-smooth-minimization",
        "pub-distributed-learning-with-compressed-gradient-differences",
        "pub-optimal-tensor-methods-in-smooth-convex-and-uniformly-convex-optimization",
        "pub-an-accelerated-directional-derivative-method-for-smooth-stochastic-convex-optimization",
        "pub-an-accelerated-method-for-derivative-free-smooth-stochastic-convex-optimization",
        "pub-accelerated-directional-search-with-non-euclidean-prox-structure",
    }
    missing_convex_publications = sorted(expected_convex_publications - convex_card_ids)
    if missing_convex_publications:
        errors.append(
            "publications.html: convex optimization tag missing from expected papers "
            f"{missing_convex_publications}"
        )
    if len(convex_card_ids) < 30:
        errors.append(
            "publications.html: convex optimization tag should cover many convex papers "
            f"(found {len(convex_card_ids)})"
        )
    expected_tag_labels = {
        "stochastic-optimization": "Stochastic optimization",
        "stochastic-gradient-descent": "Stochastic gradient descent",
        "convex-optimization": "Convex optimization",
        "min-max-variational-inequalities": "Min-max/variational inequalities",
        "last-iterate-convergence": "Last-iterate convergence",
        "probability-and-concentration": "Probability and concentration",
        "distributed-learning": "Distributed learning",
        "federated-learning": "Federated learning",
        "communication-compression": "Communication compression",
        "decentralized-optimization": "Decentralized optimization",
        "local-steps-random-reshuffling": "Local steps/random reshuffling",
        "low-rank-fine-tuning": "Low-rank fine-tuning",
        "high-probability-bounds": "High-probability bounds",
        "heavy-tailed-noise": "Heavy-tailed noise",
        "gradient-clipping": "Gradient clipping",
        "generalized-smoothness": "Generalized smoothness",
        "byzantine-robustness": "Byzantine robustness",
        "differential-privacy": "Differential privacy",
        "adaptive-methods": "Adaptive methods",
        "variance-reduction": "Variance reduction",
        "conditional-gradient-lmo-methods": "Conditional gradient/LMO methods",
        "derivative-free-zeroth-order-methods": "Derivative-free/zeroth-order methods",
        "higher-order-methods": "Higher-order methods",
        "coordinate-descent-type-methods": "Coordinate descent type methods",
        "inexact-oracles": "Inexact oracles",
    }
    for tag_value, tag_label in expected_tag_labels.items():
        option_markup = f'<option value="{tag_value}">{tag_label}</option>'
        if option_markup not in page_text:
            errors.append(f"publications.html: topic tag option should be labelled {tag_label!r}")
    if parser.tag_buttons:
        errors.append("publications.html: quick topic buttons should stay removed to keep the filter card compact")
    if 'class="eg-tag-controls"' in page_text or "Popular topic tag filters" in page_text:
        errors.append("publications.html: popular topic tag rail should stay removed")

    for index, card in enumerate(parser.cards, start=1):
        card_label = str(card.get("id") or f"card {index}")
        tag_count = len(set(card.get("tags", set())))
        expected_title_id = f"{card_label}-title" if card_label.startswith("pub-") else ""
        if not str(card.get("id", "")).startswith("pub-"):
            errors.append(f"publications.html: {card_label} should use a stable pub-* id")
        if expected_title_id and card.get("heading_id") != expected_title_id:
            errors.append(f"publications.html: {card_label} title heading should use id {expected_title_id!r}")
        if expected_title_id and card.get("labelledby") != expected_title_id:
            errors.append(f"publications.html: {card_label} card should be labelled by its title heading")
        title = str(card.get("title", "")).strip()
        title_link = card.get("title_link", {})
        if not title:
            errors.append(f"publications.html: {card_label} title heading should contain visible text")
        if not isinstance(title_link, dict) or not title_link.get("href"):
            errors.append(f"publications.html: {card_label} title should link to a paper page or PDF")
        else:
            expected_title_label = (
                "Open PDF for " if title_link.get("type") == "application/pdf" else "Open paper page for "
            ) + title
            if title_link.get("aria_label") != expected_title_label:
                errors.append(
                    f"publications.html: {card_label} title link should use aria-label {expected_title_label!r}"
                )
        if card.get("role") != "listitem":
            errors.append(f"publications.html: {card_label} should expose role='listitem'")
        if not card.get("type"):
            errors.append(f"publications.html: {card_label} is missing data-type")
        if tag_count == 0:
            errors.append(f"publications.html: {card_label} is missing data-tags")
        if card.get("abstracts") != 1:
            errors.append(f"publications.html: {card_label} should have exactly one abstract block")
        if int(card.get("abstract_words", 0)) < 25:
            errors.append(f"publications.html: {card_label} abstract should contain substantive paper text")
        abstract_text = str(card.get("abstract_text", "")).lower()
        for stale_abstract_marker in ("abstract unavailable", "abstract to be added", "coming soon", "tbd"):
            if stale_abstract_marker in abstract_text:
                errors.append(f"publications.html: {card_label} abstract contains placeholder text")
        if "{\\em" in abstract_text or "\\em " in abstract_text:
            errors.append(f"publications.html: {card_label} abstract should use HTML emphasis, not raw TeX emphasis")
        if " -- " in abstract_text:
            errors.append(f"publications.html: {card_label} abstract should use rendered dashes, not raw double hyphens")
        if "method -- is" in abstract_text:
            errors.append(f"publications.html: {card_label} abstract should not contain the raw dash phrase 'method -- is'")
        if "polyak-ł ojasiewicz" in abstract_text:
            errors.append(f"publications.html: {card_label} abstract should not split Polyak-Łojasiewicz")
        if card.get("tag_groups") != 1:
            errors.append(f"publications.html: {card_label} should have exactly one visible tag group")
        if card.get("visible_tags") != tag_count:
            errors.append(f"publications.html: {card_label} visible tag count does not match data-tags")
        if card.get("actions") != 1:
            errors.append(f"publications.html: {card_label} should have exactly one action row")

    for venue, displayed_count in sorted(parser.venue_stats.items()):
        actual_count = sum(
            1
            for card in parser.cards
            if card.get("type") == "conference paper"
            and venue in str(card.get("venue", ""))
            and "workshop" not in str(card.get("venue", "")).lower()
            and "short version" not in str(card.get("venue", "")).lower()
        )
        if displayed_count != actual_count:
            errors.append(f"publications.html: {venue} counter {displayed_count} does not match {actual_count} cards")

    for index, line in enumerate(parser.author_lines, start=1):
        author_text = str(line.get("text", ""))
        author_strongs = {str(value).strip() for value in line.get("strongs", [])}
        if "Eduard Gorbunov" in author_text and "Eduard Gorbunov" not in author_strongs:
            errors.append(f"publications.html: author line {index} does not highlight Eduard Gorbunov")

    return errors



def check_activities() -> list[str]:
    errors: list[str] = []
    page = ROOT / "conferences.html"
    if not page.exists():
        errors.append("conferences.html: missing file")
        return errors

    page_text = page.read_text(encoding="utf-8", errors="ignore")
    parser = ActivityParser()
    parser.feed(page_text)

    required_intro_phrases = [
        "Invited talks, seminars, conference presentations, posters, slides, and videos by Eduard Gorbunov.",
    ]
    for phrase in required_intro_phrases:
        if phrase not in page_text:
            errors.append(f"conferences.html: page intro should include {phrase!r}")
    required_activity_schema = [
        '"@type": "CollectionPage"',
        '"mainEntity": [',
        '"@id": "https://eduardgorbunov.github.io/conferences.html#talks"',
        '"name": "Talks and seminars"',
        '"@id": "https://eduardgorbunov.github.io/conferences.html#posters"',
        '"name": "Posters and presentation materials"',
        '"itemListOrder": "https://schema.org/ItemListOrderDescending"',
        '"itemListElement": [',
    ]
    for snippet in required_activity_schema:
        if snippet not in page_text:
            errors.append(f"conferences.html: structured metadata should include {snippet!r}")

    required_section_labels = {
        '<section class="eg-activity-page" id="talks" aria-labelledby="talks-heading">': "talks section label",
        '<h1 id="talks-heading">Talks and posters</h1>': "talks heading id",
        '<h2 id="talks-list-heading">Invited talks, conference talks, and seminars</h2>': "talk list heading id",
        '<section class="eg-activity-page" id="posters" aria-labelledby="posters-heading">': "posters section label",
        '<h2 id="posters-heading">Conference posters and presentation materials</h2>': "posters heading id",
    }
    for snippet, description in required_section_labels.items():
        if snippet not in page_text:
            errors.append(f"conferences.html: missing {description}")

    if 'class="eg-profile-links eg-activity-shortcuts"' in page_text:
        errors.append("conferences.html: talks page should avoid redundant shortcut buttons")
    if '<a href="#talks">Recent talks</a>' in page_text or 'class="eg-activity-stat" href="#talks"' in page_text:
        errors.append("conferences.html: talks shortcuts should jump to the talks list heading, not the page top")
    if 'class="eg-activity-stat"' in page_text or 'class="eg-activity-materials"' in page_text:
        errors.append("conferences.html: talks page should avoid duplicate overview/index cards")
    required_archive_anchors = [
        '<details class="eg-activity-archive" id="archived-talks" role="listitem">',
        '<details class="eg-activity-archive eg-activity-archive-posters" id="archived-posters" role="listitem">',
    ]
    for anchor in required_archive_anchors:
        if anchor not in page_text:
            errors.append(f"conferences.html: missing archive anchor {anchor!r}")

    expected_activity_list_labels = ["Talks and seminars", "Posters and presentation materials"]
    actual_activity_list_labels = [attrs.get("aria-label", "") for attrs in parser.activity_lists]
    if actual_activity_list_labels != expected_activity_list_labels:
        errors.append(
            "conferences.html: activity lists should expose labels "
            f"{expected_activity_list_labels!r}, found {actual_activity_list_labels!r}"
        )
    for attrs in parser.activity_lists:
        if attrs.get("role", "") != "list":
            errors.append("conferences.html: current activity lists should use role='list'")

    expected_archive_list_labels = ["Archived talks and seminars", "Archived posters and presentation materials"]
    actual_archive_list_labels = [attrs.get("aria-label", "") for attrs in parser.archive_lists]
    if actual_archive_list_labels != expected_archive_list_labels:
        errors.append(
            "conferences.html: archive activity lists should expose labels "
            f"{expected_archive_list_labels!r}, found {actual_archive_list_labels!r}"
        )
    for attrs in parser.archive_lists:
        if attrs.get("role", "") != "list":
            errors.append("conferences.html: archived activity lists should use role='list'")

    expected_archive_ids = ["archived-talks", "archived-posters"]
    actual_archive_ids = [attrs.get("id", "") for attrs in parser.archive_details]
    if actual_archive_ids != expected_archive_ids:
        errors.append(
            f"conferences.html: archive details should be {expected_archive_ids!r}, found {actual_archive_ids!r}"
        )
    for attrs in parser.archive_details:
        if attrs.get("role", "") != "listitem":
            errors.append("conferences.html: archive details should use role='listitem'")

    kind_counts = Counter(str(card.get("kind", "")) for card in parser.cards)
    expected_schema_counts = {
        "talk": f'"numberOfItems": {kind_counts["talk"]}',
        "poster": f'"numberOfItems": {kind_counts["poster"]}',
    }
    for kind, snippet in expected_schema_counts.items():
        if snippet not in page_text:
            errors.append(f"conferences.html: {kind} ItemList metadata should use {snippet!r}")
    slide_link_count = page_text.count(">Slides<") + page_text.count(">Talk slides<")
    video_link_count = page_text.count(">Video<")
    if "poster presentations" not in page_text:
        errors.append("conferences.html: page copy should use 'poster presentations'")
    if "<span>posters and materials</span>" in page_text or "<span>Earlier posters and materials</span>" in page_text:
        errors.append("conferences.html: visible poster labels should avoid the vague 'posters and materials' phrase")
    if "<span>Earlier poster presentations</span>" not in page_text:
        errors.append("conferences.html: poster archive should use 'Earlier poster presentations'")
    activity_action_blocks = re.findall(
        r'<div class="eg-activity-actions">(.*?)</div>',
        page_text,
        flags=re.DOTALL,
    )
    activity_action_link_count = 0
    poorly_named_activity_actions: list[str] = []
    for block in activity_action_blocks:
        for attrs, label_html in re.findall(r"<a\s+([^>]*)>(.*?)</a>", block, flags=re.DOTALL):
            activity_action_link_count += 1
            link_label = re.sub(r"<[^>]+>", "", label_html).strip()
            aria_match = re.search(r'aria-label="([^"]+)"', attrs)
            aria_label = unescape(aria_match.group(1)) if aria_match else ""
            if not re.fullmatch(r"Open .+ for .+", aria_label):
                poorly_named_activity_actions.append(link_label or attrs)
    if activity_action_link_count == 0:
        errors.append("conferences.html: activity action links should be present")
    if poorly_named_activity_actions:
        errors.append(
            "conferences.html: every talk/poster action link should have a contextual aria-label "
            f"like 'Open Slides for Title' ({poorly_named_activity_actions[:5]!r})"
        )
    required_activity_detail_link_labels = [
        '<a href="https://ismp2018.sciencesconf.org/data/bookRoomAssingment.pdf" type="application/pdf" target="_blank" rel="noopener noreferrer" aria-label="Open ISMP 2018 talk assignment PDF">Talk</a>',
        '<a href="https://vcc.kaust.edu.sa/Pages/Home.aspx" target="_blank" rel="noopener noreferrer" aria-label="Open KAUST Visual Computing Center website">KAUST</a>',
    ]
    for snippet in required_activity_detail_link_labels:
        if snippet not in page_text:
            errors.append(f"conferences.html: short activity detail link should use contextual label {snippet!r}")

    unexpected_kinds = sorted(kind for kind in kind_counts if kind not in {"talk", "poster"})
    if unexpected_kinds:
        errors.append(f"conferences.html: unexpected activity card kinds {unexpected_kinds}")

    cards_by_kind: dict[str, list[dict[str, object]]] = {"talk": [], "poster": []}
    for index, card in enumerate(parser.cards, start=1):
        kind = str(card.get("kind", ""))
        card_id = str(card.get("id", ""))
        number_text = str(card.get("number", ""))
        title = str(card.get("title", ""))
        title_link = card.get("title_link", {})
        labelledby = str(card.get("labelledby", ""))
        role = str(card.get("role", ""))
        heading_id = str(card.get("heading_id", ""))
        actions = int(card.get("actions", 0))
        meta_lines = [str(line) for line in card.get("meta", [])]
        card_label = f"activity card {index}"
        number = parse_int(number_text.removeprefix("#"))
        expected_card_id = f"{kind}-{number}" if kind in {"talk", "poster"} and number is not None else ""
        expected_title_id = f"{kind}-{number}-title" if kind in {"talk", "poster"} and number is not None else ""

        if kind in cards_by_kind:
            cards_by_kind[kind].append(card)
        if not title:
            errors.append(f"conferences.html: {card_label} is missing a title")
        if isinstance(title_link, dict) and title_link.get("href"):
            if title_link.get("type") == "application/pdf":
                expected_title_link_label = f"Open {kind} PDF for {title}"
            elif kind == "poster":
                expected_title_link_label = f"Open poster page for {title}"
            else:
                expected_title_link_label = f"Open event page for {title}"
            if title_link.get("aria_label") != expected_title_link_label:
                errors.append(
                    f"conferences.html: {card_label} title link should use aria-label "
                    f"{expected_title_link_label!r}"
                )
        if number is None:
            errors.append(f"conferences.html: {card_label} has invalid number {number_text!r}")
        if card_id != expected_card_id:
            errors.append(f"conferences.html: {card_label} id should be {expected_card_id!r}, found {card_id!r}")
        if heading_id != expected_title_id:
            errors.append(f"conferences.html: {card_label} heading id should be {expected_title_id!r}, found {heading_id!r}")
        if labelledby != expected_title_id:
            errors.append(f"conferences.html: {card_label} aria-labelledby should be {expected_title_id!r}, found {labelledby!r}")
        if role != "listitem":
            errors.append(f"conferences.html: {card_label} should use role='listitem'")
        if actions != 1:
            errors.append(f"conferences.html: {card_label} should have exactly one action row")
        duplicate_meta = sorted(line for line, count in Counter(meta_lines).items() if line and count > 1)
        if duplicate_meta:
            errors.append(f"conferences.html: {card_label} has duplicate metadata lines {duplicate_meta!r}")

    for kind, cards in cards_by_kind.items():
        numbers = [parse_int(str(card.get("number", "")).removeprefix("#")) for card in cards]
        expected_numbers = list(range(len(cards), 0, -1))
        if numbers != expected_numbers:
            errors.append(f"conferences.html: {kind} card numbers should descend {expected_numbers}, found {numbers}")

    if page_text.count('"@type": "CreativeWork"') < 10:
        errors.append("conferences.html: structured metadata should expose latest talks and posters as CreativeWork entries")
    for kind, cards in cards_by_kind.items():
        for position, card in enumerate(cards[:5], start=1):
            title = str(card.get("title", ""))
            card_id = str(card.get("id", ""))
            required_activity_metadata = [
                f'"position": {position}',
                '"item": {',
                '"@type": "CreativeWork"',
                f'"name": {json.dumps(title, ensure_ascii=False)}',
                f'"url": "{SITE_URL}/conferences.html#{card_id}"',
            ]
            for snippet in required_activity_metadata:
                if snippet not in page_text:
                    errors.append(
                        f"conferences.html: latest {kind} metadata for {card_id!r} should include {snippet!r}"
                    )

    return errors


def check_research() -> list[str]:
    errors: list[str] = []
    page = ROOT / "research.html"
    if not page.exists():
        errors.append("research.html: missing file")
        return errors

    page_text = page.read_text(encoding="utf-8", errors="ignore")
    parser = ResearchParser()
    parser.feed(page_text)
    publications_page = ROOT / "publications.html"
    publication_parser = PublicationParser()
    if publications_page.exists():
        publication_parser.feed(publications_page.read_text(encoding="utf-8", errors="ignore"))
    else:
        errors.append("research.html: cannot verify research counts because publications.html is missing")

    def publication_count(tag: str | None) -> int:
        if tag is None:
            return len(publication_parser.cards)
        return sum(1 for card in publication_parser.cards if tag in set(card.get("tags", set())))

    if "higher-order structure" in page_text:
        errors.append("research.html: generalized-smoothness theme should not use vague higher-order wording")
    if "L<sub>" in page_text:
        errors.append("research.html: generalized-smoothness notation should use LaTeX, not HTML subscript tags")
    if "non-standard smoothness assumptions" not in page_text:
        errors.append("research.html: generalized-smoothness theme should mention non-standard smoothness assumptions")
    research_lead = (
        "My research interests are in reliable optimization methods for modern machine learning, "
        "especially stochastic methods, distributed systems, robustness, "
        "privacy, and variational inequalities."
    )
    if research_lead not in page_text:
        errors.append("research.html: lead paragraph should use personal research-focus wording")
    if "For my complete filterable list of papers, see" not in page_text:
        errors.append("research.html: page heading should include a lightweight publications/talks note")
    if "Compact view of the recurring themes" in page_text:
        errors.append("research.html: research map intro should avoid scaffolding-like phrasing")
    if "I organize my work around connected themes" not in page_text:
        errors.append("research.html: research map intro should use personal connected-theme wording")
    if "A concise guide to the assumptions, methods, and systems themes that organize the publication list." in page_text:
        errors.append("research.html: research map intro should avoid verbose guide wording")
    removed_direction_snippets = [
        'id="research-directions"',
        "Current directions",
        "A common thread in my current work is optimization theory",
        'data-kind="research"',
        "direction-heavy-tailed-noise",
        "direction-federated-decentralized-optimization",
        "direction-robustness-privacy",
        "direction-variational-inequalities",
    ]
    for snippet in removed_direction_snippets:
        if snippet in page_text:
            errors.append(f"research.html: removed current-directions block should stay absent: {snippet!r}")
    if "Research entry points" in page_text or ">Entry points</a>" in page_text:
        errors.append("research.html: final research links section should avoid internal 'entry points' wording")
    required_schema_snippets = [
        '"@type": "CollectionPage"',
        '"@id": "https://eduardgorbunov.github.io/research.html#webpage"',
        '"author": {\n      "@id": "https://eduardgorbunov.github.io/#person"\n    }',
        '"Generalized smoothness"',
    ]
    for snippet in required_schema_snippets:
        if snippet not in page_text:
            errors.append(f"research.html: structured metadata should include {snippet!r}")
    required_section_labels = {
        '<section class="eg-research-focus" id="research" aria-labelledby="research-heading">': "research section label",
        '<h1 id="research-heading">Research</h1>': "research heading id",
        '<section class="eg-research-map" id="research-map" aria-labelledby="research-map-heading">': "research map section label",
        '<h2 id="research-map-heading">Research map</h2>': "research map heading id",
        '<section class="eg-about-section" id="representative-papers" aria-labelledby="representative-papers-heading">': "representative papers section label",
        '<h2 id="representative-papers-heading">Representative papers</h2>': "representative papers heading id",
    }
    for snippet, description in required_section_labels.items():
        if snippet not in page_text:
            errors.append(f"research.html: missing {description}")

    expected_focus_list_labels = ["Research focus areas"]
    actual_focus_list_labels = [attrs.get("aria-label", "") for attrs in parser.focus_lists]
    if actual_focus_list_labels != expected_focus_list_labels:
        errors.append(
            "research.html: focus-card list should expose labels "
            f"{expected_focus_list_labels!r}, found {actual_focus_list_labels!r}"
        )
    for attrs in parser.focus_lists:
        if attrs.get("role", "") != "list":
            errors.append("research.html: focus-card container should use role='list'")

    expected_about_list_labels = ["Representative papers"]
    actual_about_list_labels = [attrs.get("aria-label", "") for attrs in parser.about_lists]
    if actual_about_list_labels != expected_about_list_labels:
        errors.append(
            "research.html: research list groups should expose labels "
            f"{expected_about_list_labels!r}, found {actual_about_list_labels!r}"
        )
    for attrs in parser.about_lists:
        if attrs.get("role", "") != "list":
            errors.append("research.html: research list groups should use role='list'")

    if 'class="eg-profile-links eg-research-shortcuts"' in page_text:
        errors.append("research.html: research page should avoid redundant shortcut buttons")
    if 'class="eg-research-snapshot"' in page_text or 'class="eg-research-venue-strip"' in page_text:
        errors.append("research.html: research page should avoid duplicate stat/counter cards")

    if '<div class="eg-research-map-grid" role="list" aria-label="Research topic map">' not in page_text:
        errors.append("research.html: research map should expose a labelled list")
    research_map = page_text.split('id="research-map"', 1)[-1].split('<div class="eg-focus-grid"', 1)[0]
    expected_map_cards = [
        (
            "research-map-optimization",
            "teal",
            "Optimization theory",
            [
                "publications.html?tag=stochastic-optimization#publication-list",
                "publications.html?tag=convex-optimization#publication-list",
                "publications.html?tag=min-max-variational-inequalities#publication-list",
            ],
        ),
        (
            "research-map-distributed",
            "blue",
            "Distributed learning",
            [
                "publications.html?tag=federated-learning#publication-list",
                "publications.html?tag=communication-compression#publication-list",
                "publications.html?tag=decentralized-optimization#publication-list",
            ],
        ),
        (
            "research-map-reliability",
            "gold",
            "Reliability and trust",
            [
                "publications.html?tag=heavy-tailed-noise#publication-list",
                "publications.html?tag=high-probability-bounds#publication-list",
                "publications.html?tag=byzantine-robustness#publication-list",
            ],
        ),
        (
            "research-map-methods",
            "rose",
            "Modern smoothness and adaptivity",
            [
                "publications.html?tag=gradient-clipping#publication-list",
                "publications.html?tag=generalized-smoothness#publication-list",
                "publications.html?tag=adaptive-methods#publication-list",
            ],
        ),
    ]
    if research_map.count('class="eg-research-map-card"') != len(expected_map_cards):
        errors.append("research.html: research map should contain four compact topic cards")
    if research_map.count('role="listitem"') != len(expected_map_cards):
        errors.append("research.html: research map cards should expose role='listitem'")
    for card_id, accent, title, hrefs in expected_map_cards:
        heading_id = f"{card_id}-heading"
        required_parts = [
            f'id="{card_id}" data-accent="{accent}" role="listitem" aria-labelledby="{heading_id}"',
            f'<h3 id="{heading_id}">{title}</h3>',
        ]
        for part in required_parts:
            if part not in research_map:
                errors.append(f"research.html: research map card {card_id!r} should include {part!r}")
        for href in hrefs:
            if f'href="{href}"' not in research_map:
                errors.append(f"research.html: research map card {card_id!r} should link to {href!r}")

    representative_section = page_text.split('id="representative-papers"', 1)[-1].split('id="research-entry-points"', 1)[0]
    if representative_section.count('data-kind="paper"') != len(EXPECTED_RESEARCH_REPRESENTATIVE_PAPERS):
        errors.append(
            "research.html: representative papers should use "
            f"{len(EXPECTED_RESEARCH_REPRESENTATIVE_PAPERS)} data-kind='paper' cards"
        )
    if representative_section.count('role="listitem"') != len(EXPECTED_RESEARCH_REPRESENTATIVE_PAPERS):
        errors.append(
            "research.html: representative papers should expose "
            f"{len(EXPECTED_RESEARCH_REPRESENTATIVE_PAPERS)} role='listitem' cards"
        )
    for card_id, href in EXPECTED_RESEARCH_REPRESENTATIVE_PAPERS:
        if f'id="{card_id}"' not in representative_section:
            errors.append(f"research.html: missing representative paper card {card_id!r}")
        if f'href="{href}"' not in representative_section:
            errors.append(f"research.html: representative paper card {card_id!r} should link to {href!r}")
    expected_representative_link_labels = {
        "publications.html#pub-last-iterate-clipped-sgd":
            "Open representative paper: High-probability bounds for the last iterate of clipped SGD",
        "publications.html#pub-high-probability-convergence-for-composite-and-distributed-stochastic-minimization-and-variational-inequalities":
            "Open representative paper: High-probability convergence for composite and distributed optimization",
        "publications.html#pub-methods-for-convex-l0-l1-smooth-optimization-clipping-acceleration-and-adaptivity":
            "Open representative paper: Methods for convex $(L_0,L_1)$-smooth optimization",
        "publications.html#pub-byzantine-tolerant-methods-for-distributed-variational-inequalities":
            "Open representative paper: Byzantine-tolerant methods for distributed variational inequalities",
    }
    for href in expected_representative_link_labels:
        if f'<a href="{href}">' not in representative_section:
            errors.append(f"research.html: representative paper title should link to {href!r}")
    if ">View paper</a>" in representative_section:
        errors.append("research.html: representative paper actions should use 'Open paper'")

    if ">Related papers</a>" in page_text:
        errors.append("research.html: focus-card action text should use a direct verb")
    if ">Browse papers</a>" in page_text:
        errors.append("research.html: focus cards should avoid redundant browse-paper buttons")

    expected_accents = ["teal", "blue", "gold", "rose"]
    actual_accents = [str(card.get("accent", "")) for card in parser.focus_cards]
    if actual_accents != expected_accents:
        errors.append(f"research.html: focus-card accents should be {expected_accents!r}, found {actual_accents!r}")

    expected_focus_ids = [
        "focus-stochastic-optimization",
        "focus-distributed-learning",
        "focus-variational-inequalities",
        "focus-generalized-smoothness",
    ]
    actual_focus_ids = [str(card.get("id", "")) for card in parser.focus_cards]
    if actual_focus_ids != expected_focus_ids:
        errors.append(f"research.html: focus-card ids should be {expected_focus_ids!r}, found {actual_focus_ids!r}")

    for index, card in enumerate(parser.focus_cards, start=1):
        card_id = str(card.get("id", ""))
        expected_title_id = f"{card_id}-title" if card_id else ""
        if not str(card.get("heading", "")):
            errors.append(f"research.html: focus card {index} is missing a heading")
        if str(card.get("heading_id", "")) != expected_title_id:
            errors.append(
                f"research.html: focus card {index} heading id should be {expected_title_id!r}, "
                f"found {card.get('heading_id')!r}"
            )
        if str(card.get("labelledby", "")) != expected_title_id:
            errors.append(
                f"research.html: focus card {index} aria-labelledby should be {expected_title_id!r}, "
                f"found {card.get('labelledby')!r}"
            )
        if str(card.get("role", "")) != "listitem":
            errors.append(f"research.html: focus card {index} should use role='listitem'")
        if int(card.get("paragraphs", 0)) != 1:
            errors.append(f"research.html: focus card {index} should have exactly one description paragraph")
        if list(card.get("links", [])):
            errors.append(f"research.html: focus card {index} should avoid redundant action links")

    if parser.direction_cards:
        errors.append("research.html: current direction cards should be removed")

    return errors


def check_about() -> list[str]:
    errors: list[str] = []
    page = ROOT / "about.html"
    if not page.exists():
        errors.append("about.html: missing file")
        return errors

    page_text = page.read_text(encoding="utf-8", errors="ignore")
    parser = PageParser()
    parser.feed(page_text)
    about_parser = AboutParser()
    about_parser.feed(page_text)

    required_current_position = [
        "Aug 2025 - present",
        "Assistant Professor, Department of Statistics and Data Science, MBZUAI",
        "Tenure-track faculty appointment in the Department of Statistics and Data Science.",
    ]
    for snippet in required_current_position:
        if snippet not in page_text:
            errors.append(f"about.html: missing current appointment detail {snippet!r}")
    polished_about_lead = (
        "I am a tenure-track Assistant Professor in the Department of Statistics and Data Science at "
    )
    if polished_about_lead not in page_text:
        errors.append("about.html: intro should use department-level faculty wording")
    if "I am a tenure-track Assistant Professor of Statistics and Data Science at " in page_text:
        errors.append("about.html: intro should avoid compressed faculty-title wording")
    if '<h3 id="appointment-mbzuai-assistant-professor-title">Assistant Professor of Statistics and Data Science, MBZUAI</h3>' in page_text:
        errors.append("about.html: current appointment heading should use department-level wording")
    polished_previous_position = (
        "Before my faculty appointment, I held Research Scientist and Postdoctoral Fellow positions at MBZUAI"
    )
    if polished_previous_position not in page_text:
        errors.append("about.html: intro should use polished previous-position wording")
    if "Previously, I was a research scientist and postdoctoral fellow" in page_text:
        errors.append("about.html: intro should avoid casual previous-position wording")
    required_schema_snippets = [
        '"@type": "ProfilePage"',
        '"@id": "https://eduardgorbunov.github.io/about.html#webpage"',
        '"mainEntity": {',
        '"@type": "Person"',
        '"@id": "https://eduardgorbunov.github.io/#person"',
        '"jobTitle": "Assistant Professor of Statistics and Data Science"',
        '"affiliation": {',
        '"name": "Mohamed bin Zayed University of Artificial Intelligence"',
        '"email": "mailto:eduard.gorbunov@mbzuai.ac.ae"',
        '"sameAs": [',
        '"alumniOf": {',
        '"name": "Moscow Institute of Physics and Technology"',
        '"knowsAbout": [',
    ]
    for snippet in required_schema_snippets:
        if snippet not in page_text:
            errors.append(f"about.html: structured metadata should include {snippet!r}")
    required_section_labels = {
        '<section class="eg-about-intro" id="about" aria-labelledby="about-heading">': "about intro section label",
        '<h1 id="about-heading">About me</h1>': "about heading id",
        '<section class="eg-about-details" id="service" aria-labelledby="service-heading">': "service section label",
        '<h2 id="service-heading">Selected service and recognition</h2>': "service heading id",
        '<article class="eg-about-card eg-about-card-awards" id="about-card-selected-awards" role="listitem" aria-labelledby="selected-awards-heading">': "awards card label",
        '<h3 id="selected-awards-heading">Selected awards</h3>': "awards card heading id",
        '<article class="eg-about-card eg-about-card-editorial" id="about-card-editorial-service" role="listitem" aria-labelledby="editorial-service-heading">': "editorial card label",
        '<h3 id="editorial-service-heading">Editorial service</h3>': "editorial card heading id",
        '<article class="eg-about-card eg-about-card-conference" id="about-card-conference-service" role="listitem" aria-labelledby="conference-service-heading">': "conference card label",
        '<h3 id="conference-service-heading">Conference service</h3>': "conference card heading id",
        '<section class="eg-about-section" id="education" aria-labelledby="education-heading">': "education section label",
        '<h2 id="education-heading">Academic training</h2>': "education heading id",
        '<section class="eg-about-section" id="appointments" aria-labelledby="appointments-heading">': "appointments section label",
        '<h2 id="appointments-heading">Research and teaching appointments</h2>': "appointments heading id",
    }
    for snippet, description in required_section_labels.items():
        if snippet not in page_text:
            errors.append(f"about.html: missing {description}")
    old_service_heading_case = (
        ">Selected Awards</h3>",
        ">Editorial Service</h3>",
        ">Conference Service</h3>",
    )
    if any(heading in page_text for heading in old_service_heading_case):
        errors.append("about.html: service card headings should use sentence-style capitalization")
    about_research_lead = (
        "My research interests are in stochastic optimization for machine learning, "
        "including distributed and federated training, derivative-free methods, "
        "variational inequalities, robustness, privacy, and high-probability guarantees."
    )
    if about_research_lead not in page_text:
        errors.append("about.html: intro should use personal research-focus wording")
    if "selected reviewer recognitions" in page_text:
        errors.append("about.html: service section should use concrete reviewer-awards wording")
    if 'class="eg-about-snapshot"' in page_text:
        errors.append("about.html: about page should avoid redundant snapshot cards")
    if '<nav class="eg-profile-links" aria-label="Profile links">' not in page_text:
        errors.append("about.html: intro profile links should use a labelled navigation landmark")
    if 'class="eg-profile-links eg-about-shortcuts"' in page_text:
        errors.append("about.html: about page should avoid redundant section shortcut buttons")
    required_defense_links = [
        '<a href="assets/files/PhD_defense.pdf" type="application/pdf" target="_blank" rel="noopener noreferrer" aria-label="Open PhD defense slides">Slides</a>',
        '<a href="https://youtu.be/HKVp2oNedi4" target="_blank" rel="noopener noreferrer" aria-label="Open PhD defense video">Video</a>',
    ]
    for snippet in required_defense_links:
        if snippet not in page_text:
            errors.append(f"about.html: PhD defense links should use contextual labels {snippet!r}")
    if ">video</a>" in page_text:
        errors.append("about.html: PhD defense video link should use title-case 'Video'")
    if "since 2024" not in page_text:
        errors.append("about.html: editorial service should use polished 'since 2024' wording")
    if "from 2024" in page_text:
        errors.append("about.html: editorial service should not use informal 'from 2024' wording")
    if 'id="appointments"' not in page_text:
        errors.append("about.html: appointments section should use the appointments anchor")
    if "previous-positions" in page_text:
        errors.append("about.html: appointments section should not use stale previous-positions anchor")
    if 'class="eg-appointment-summary"' in page_text:
        errors.append("about.html: appointments should use the detailed list without duplicate summary cards")
    required_service_link_labels = [
        '<a href="https://neurips.cc/" target="_blank" rel="noopener noreferrer" aria-label="Open NeurIPS website">NeurIPS</a>',
        '<a href="https://iclr.cc/" target="_blank" rel="noopener noreferrer" aria-label="Open ICLR website">ICLR</a>',
        '<a href="https://icml.cc/" target="_blank" rel="noopener noreferrer" aria-label="Open ICML website">ICML</a>',
        '<a href="https://icomp.cc/" target="_blank" rel="noopener noreferrer" aria-label="Open ICOMP website">ICOMP</a>',
    ]
    for snippet in required_service_link_labels:
        if snippet not in page_text:
            errors.append(f"about.html: service venue link should use contextual label {snippet!r}")

    service_list_labels = [attrs.get("aria-label", "") for attrs in about_parser.service_lists]
    if service_list_labels != ["Selected service and recognition"]:
        errors.append(
            "about.html: service card list should expose label "
            f"'Selected service and recognition', found {service_list_labels!r}"
        )
    for attrs in about_parser.service_lists:
        if attrs.get("role", "") != "list":
            errors.append("about.html: service card grid should use role='list'")

    about_list_labels = [attrs.get("aria-label", "") for attrs in about_parser.list_groups]
    expected_about_list_labels = ["Academic training", "Research and teaching appointments"]
    if about_list_labels != expected_about_list_labels:
        errors.append(
            "about.html: education/appointment lists should expose labels "
            f"{expected_about_list_labels!r}, found {about_list_labels!r}"
        )
    for attrs in about_parser.list_groups:
        if attrs.get("role", "") != "list":
            errors.append("about.html: education/appointment list containers should use role='list'")

    service_card_ids = [card["id"] for card in about_parser.service_cards]
    expected_service_card_ids = [
        "about-card-selected-awards",
        "about-card-editorial-service",
        "about-card-conference-service",
    ]
    if service_card_ids != expected_service_card_ids:
        errors.append(f"about.html: service card ids should be {expected_service_card_ids!r}, found {service_card_ids!r}")
    for card in about_parser.service_cards:
        if not card["title"]:
            errors.append(f"about.html: service card {card.get('id')!r} is missing a title")
        if card.get("role") != "listitem":
            errors.append(f"about.html: service card {card.get('id')!r} should use role='listitem'")
        if not card["labelledby"]:
            errors.append(f"about.html: service card {card.get('id')!r} is missing aria-labelledby")
        if card["heading_id"] != card["labelledby"]:
            errors.append(
                f"about.html: service card {card.get('id')!r} heading id should match aria-labelledby, "
                f"found {card['heading_id']!r} and {card['labelledby']!r}"
            )

    list_card_ids = [card["id"] for card in about_parser.list_cards]
    missing_list_card_ids = [index for index, card_id in enumerate(list_card_ids, start=1) if not card_id]
    duplicate_list_card_ids = sorted(card_id for card_id, count in Counter(list_card_ids).items() if card_id and count > 1)
    if missing_list_card_ids:
        errors.append(f"about.html: education/appointment cards missing ids {missing_list_card_ids}")
    if duplicate_list_card_ids:
        errors.append(f"about.html: duplicate education/appointment card ids {duplicate_list_card_ids}")

    list_kinds = Counter(card["kind"] for card in about_parser.list_cards)
    if list_kinds.get("education") != 3:
        errors.append(f"about.html: expected 3 education cards, found {list_kinds.get('education', 0)}")
    if list_kinds.get("position") != 13:
        errors.append(f"about.html: expected 13 appointment cards, found {list_kinds.get('position', 0)}")

    for index, card in enumerate(about_parser.list_cards, start=1):
        expected_title_id = f"{card['id']}-title" if card["id"] else ""
        if not card["title"]:
            errors.append(f"about.html: education/appointment card {index} is missing a title")
        if card["heading_id"] != expected_title_id:
            errors.append(
                f"about.html: education/appointment card {index} heading id should be {expected_title_id!r}, "
                f"found {card['heading_id']!r}"
            )
        if card["labelledby"] != expected_title_id:
            errors.append(
                f"about.html: education/appointment card {index} aria-labelledby should be {expected_title_id!r}, "
                f"found {card['labelledby']!r}"
            )
        if card.get("role") != "listitem":
            errors.append(f"about.html: education/appointment card {index} should use role='listitem'")

    expected_identity_links = {
        "https://scholar.google.com/citations?user=QPVriwoAAAAJ&hl=en",
        "https://www.researchgate.net/profile/Eduard_Gorbunov",
        "https://arxiv.org/search/math?searchtype=author&query=Gorbunov%2C+E",
        "https://x.com/ed_gorbunov",
    }
    for href in expected_identity_links:
        matching_links = [
            link
            for link in parser.links
            if link.get("href", "").replace("&amp;", "&") == href
        ]
        if not matching_links:
            errors.append(f"about.html: missing identity profile link {href!r}")
            continue
        if not any("me" in link.get("rel", "").split() for link in matching_links):
            errors.append(f"about.html: identity profile link should use rel='me' {href!r}")
    required_intro_links = [
        '<a href="https://scholar.google.com/citations?user=QPVriwoAAAAJ&amp;hl=en" target="_blank" rel="me noopener noreferrer" aria-label="Google Scholar profile">Google Scholar</a>',
        '<a href="https://www.researchgate.net/profile/Eduard_Gorbunov" target="_blank" rel="me noopener noreferrer" aria-label="ResearchGate profile">ResearchGate</a>',
        '<a href="https://arxiv.org/search/math?searchtype=author&amp;query=Gorbunov%2C+E" target="_blank" rel="me noopener noreferrer" aria-label="arXiv author profile">arXiv</a>',
        '<a href="https://x.com/ed_gorbunov" target="_blank" rel="me noopener noreferrer" aria-label="X profile">X</a>',
        '<a href="mailto:eduard.gorbunov@mbzuai.ac.ae" aria-label="Email Eduard Gorbunov">Email</a>',
        '<a href="assets/files/CV.pdf" type="application/pdf" target="_blank" rel="noopener noreferrer" aria-label="Open academic CV PDF">CV</a>',
        '<a href="research.html">Research</a>',
        '<a href="publications.html">Publications</a>',
        '<a href="team.html">Team</a>',
    ]
    for link_markup in required_intro_links:
        if link_markup not in page_text:
            errors.append(f"about.html: profile links should include {link_markup!r}")

    appointment_list_text = page_text.split(
        '<div class="eg-about-list-grid" role="list" aria-label="Research and teaching appointments">',
        1,
    )[-1]
    current_index = appointment_list_text.find("Assistant Professor, Department of Statistics and Data Science, MBZUAI")
    research_scientist_index = appointment_list_text.find("Research Scientist, MBZUAI")
    if current_index == -1 or research_scientist_index == -1 or current_index > research_scientist_index:
        errors.append("about.html: current appointment should appear before previous appointments")

    return errors


def check_team() -> list[str]:
    errors: list[str] = []
    page = ROOT / "team.html"
    if not page.exists():
        errors.append("team.html: missing file")
        return errors

    page_text = page.read_text(encoding="utf-8", errors="ignore")
    parser = TeamParser()
    parser.feed(page_text)

    lowered_text = page_text.lower()
    for pattern, label in TEAM_DISALLOWED_PATTERNS:
        if pattern.search(lowered_text):
            errors.append(f"team.html: application text should avoid {label}")
    if "join-group" in lowered_text:
        errors.append("team.html: opportunities section should use a neutral section anchor")
    if "the group's research areas" in lowered_text:
        errors.append("team.html: opportunities intro should avoid group-centric phrasing")
    if "the group welcomes postdoctoral" in lowered_text:
        errors.append("team.html: opportunities intro should avoid group-as-subject phrasing")
    if "application emails" in lowered_text:
        errors.append("team.html: application guidelines should avoid email-centric labelling")
    if "opportunity paths" in lowered_text or "application checklist items" in lowered_text:
        errors.append("team.html: compact team overview should avoid mechanical summary labels")
    if "Application checklist" not in page_text:
        errors.append("team.html: application guidelines should be labelled 'Application checklist'")
    if 'id="opportunities-heading"' not in page_text or 'aria-labelledby="opportunities-heading"' not in page_text:
        errors.append("team.html: opportunities section should be labelled by opportunities-heading")
    if 'class="eg-profile-links eg-team-shortcuts"' in page_text or 'class="eg-team-overview"' in page_text:
        errors.append("team.html: team page should avoid extra shortcut and overview cards")
    if 'class="eg-team-section" id="msc-students" aria-labelledby="msc-students-heading"' not in page_text:
        errors.append("team.html: MSc students section should expose the msc-students anchor")
    if 'class="eg-team-section eg-opportunities-section" id="opportunities"' not in page_text:
        errors.append("team.html: opportunities section should use the refined opportunities layout")
    if '<ul class="eg-opportunity-list" role="list" aria-label="Research opportunities">' not in page_text:
        errors.append("team.html: opportunities should use a compact list instead of cards")
    expected_student_list_labels = ["MSc students"]
    actual_student_list_labels = [attrs.get("aria-label", "") for attrs in parser.student_lists]
    if actual_student_list_labels != expected_student_list_labels:
        errors.append(
            "team.html: student list should expose labels "
            f"{expected_student_list_labels!r}, found {actual_student_list_labels!r}"
        )
    for attrs in parser.student_lists:
        if attrs.get("role", "") != "list":
            errors.append("team.html: student list container should use role='list'")
    expected_opportunity_list_labels = ["Research opportunities"]
    actual_opportunity_list_labels = [attrs.get("aria-label", "") for attrs in parser.opportunity_lists]
    if actual_opportunity_list_labels != expected_opportunity_list_labels:
        errors.append(
            "team.html: opportunity list should expose labels "
            f"{expected_opportunity_list_labels!r}, found {actual_opportunity_list_labels!r}"
        )
    for attrs in parser.opportunity_lists:
        if attrs.get("role", "") != "list":
            errors.append("team.html: opportunity list container should use role='list'")
    if '<h2 id="opportunities-heading">Research opportunities</h2>' not in page_text:
        errors.append("team.html: opportunities section should use neutral 'Research opportunities' heading")
    if '<h2 id="application-guidelines-heading">What to include</h2>' not in page_text:
        errors.append("team.html: application checklist should use a direct 'What to include' heading")
    if '<ul class="eg-guideline-list" aria-label="Checklist items">' not in page_text:
        errors.append("team.html: application checklist items should use a concise accessible label")
    if "If you are interested in working with me, please write a specific email and, for degree programs, also follow the official MBZUAI application process." not in page_text:
        errors.append("team.html: opportunities section should use direct email-and-application guidance")
    if "Prospective postdoctoral researchers, PhD students, MSc students, and visiting students can use the guidance below." in page_text:
        errors.append("team.html: opportunities section should avoid conversational guidance wording")
    if "Guidance for prospective postdoctoral researchers, PhD students, MSc students, and visiting students is provided below." in page_text:
        errors.append("team.html: opportunities section should avoid provided-below wording")
    if "Information for prospective postdoctoral researchers, PhD students, MSc students, and visiting students is listed below." in page_text:
        errors.append("team.html: opportunities section should avoid placeholder-like listed-below wording")
    if "MSc applicants interested in optimization or machine learning should submit the official MBZUAI application and are welcome to also email me." not in page_text:
        errors.append("team.html: MSc opportunity copy should mention email contact")
    if "When writing to me, please keep the message specific and include the following information." not in page_text:
        errors.append("team.html: application checklist should use specific email guidance")
    if "Your Name" in page_text or "%20Your%20Name" in page_text:
        errors.append("team.html: application subject placeholders should use neutral 'Applicant Name' wording")
    required_subject_line_example = (
        'Use a clear title such as "PhD application - Applicant Name" or '
        '"MSc inquiry - Applicant Name".'
    )
    if required_subject_line_example not in page_text:
        errors.append("team.html: application checklist should show neutral subject-line examples")
    required_page_phrases = [
        "<title>Research team | Eduard Gorbunov</title>",
        '"@type": "CollectionPage"',
        '"mainEntity": {',
        '"@type": "ItemList"',
        '"@id": "https://eduardgorbunov.github.io/team.html#msc-students"',
        '"name": "MSc students"',
        '"itemListOrder": "https://schema.org/ItemListOrderAscending"',
        '<h1 id="team-heading">Research team</h1>',
        "Eduard Gorbunov's research team, MSc students, and supervision opportunities at MBZUAI.",
    ]
    for phrase in required_page_phrases:
        if phrase not in page_text:
            errors.append(f"team.html: page framing should include {phrase!r}")

    expected_names = [student["name"] for student in EXPECTED_MSC_STUDENTS]
    actual_names = [str(student.get("name", "")) for student in parser.students]
    expected_item_count = f'"numberOfItems": {len(EXPECTED_MSC_STUDENTS)}'
    if expected_item_count not in page_text:
        errors.append(f"team.html: MSc student ItemList metadata should use {expected_item_count!r}")
    if '"itemListElement": [' not in page_text:
        errors.append("team.html: MSc student ItemList metadata should include itemListElement entries")
    student_metadata = page_text.split('"@id": "https://eduardgorbunov.github.io/team.html#msc-students"', 1)[-1]
    student_metadata = student_metadata.split("</script>", 1)[0]
    if student_metadata.count('"@type": "Person"') != len(EXPECTED_MSC_STUDENTS):
        errors.append("team.html: MSc student metadata should expose each student as a Person entry")
    if actual_names != expected_names:
        errors.append(f"team.html: MSc students should be {expected_names!r}, found {actual_names!r}")
    if actual_names != sorted(actual_names, key=str.casefold):
        errors.append(f"team.html: MSc students should be sorted alphabetically, found {actual_names!r}")

    expected_student_accents = ["blue", "teal", "gold", "rose"]
    actual_student_accents = [str(card.get("accent", "")) for card in parser.students]
    if actual_student_accents != expected_student_accents:
        errors.append(
            f"team.html: student cards should use accents {expected_student_accents!r}, "
            f"found {actual_student_accents!r}"
        )

    for index, (expected, actual) in enumerate(zip(EXPECTED_MSC_STUDENTS, parser.students), start=1):
        name = expected["name"]
        links = set(str(link) for link in actual.get("links", []))
        meta = dict(actual.get("meta", {}))
        time_datetimes = list(actual.get("time_datetimes", []))
        expected_card_id = "student-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        expected_heading_id = f"{expected_card_id}-heading"
        required_student_schema = [
            f'"position": {index}',
            '"item": {',
            '"@type": "Person"',
            f'"name": "{name}"',
            f'"url": "https://eduardgorbunov.github.io/team.html#{expected_card_id}"',
            '"affiliation": {',
            '"@type": "CollegeOrUniversity"',
            '"name": "MBZUAI"',
            '"url": "https://mbzuai.ac.ae/"',
            f'"description": "MSc student at MBZUAI, {expected["period"]}."',
        ]
        for snippet in required_student_schema:
            if snippet not in page_text:
                errors.append(f"team.html: MSc student metadata for {name} should include {snippet!r}")

        if actual.get("role") != "MSc student":
            errors.append(f"team.html: {name} should have role 'MSc student'")
        if actual.get("id") != expected_card_id:
            errors.append(f"team.html: {name} card should use id {expected_card_id!r}")
        if actual.get("heading_id") != expected_heading_id:
            errors.append(f"team.html: {name} heading should use id {expected_heading_id!r}")
        if actual.get("labelledby") != expected_heading_id:
            errors.append(f"team.html: {name} card should be labelled by its heading")
        if actual.get("list_role") != "listitem":
            errors.append(f"team.html: {name} card should use role='listitem'")
        if meta.get("Institution") != expected["institution"]:
            errors.append(f"team.html: {name} should list institution {expected['institution']!r}")
        if meta.get("Period") != expected["period"]:
            errors.append(f"team.html: {name} should list period {expected['period']!r}")
        if time_datetimes != [expected["datetime"]]:
            errors.append(f"team.html: {name} should use datetime {expected['datetime']!r}")

        profile = expected["profile"]
        if profile and profile not in links:
            errors.append(f"team.html: {name} is missing profile link {profile!r}")
        if profile and f'"sameAs": "{profile}"' not in page_text:
            errors.append(f"team.html: MSc student metadata for {name} should include sameAs profile {profile!r}")
        if not profile and links:
            errors.append(f"team.html: {name} should not have a profile link")

        co_supervisor = expected["co_supervisor"]
        if co_supervisor:
            if "Co-supervisor" not in meta:
                errors.append(f"team.html: {name} is missing co-supervisor metadata")
            if co_supervisor not in links:
                errors.append(f"team.html: {name} is missing co-supervisor link {co_supervisor!r}")
            expected_wide_meta = f'<div class="eg-student-meta-wide"><dt>Co-supervisor</dt><dd><a href="{co_supervisor}"'
            if expected_wide_meta not in page_text:
                errors.append(f"team.html: {name} co-supervisor metadata should use eg-student-meta-wide")
        elif "Co-supervisor" in meta:
            errors.append(f"team.html: {name} should not list a co-supervisor")

    expected_opportunity_labels = ["Postdoc", "PhD", "Visiting", "MSc"]
    opportunity_labels = [str(card.get("label", "")) for card in parser.opportunities]
    if opportunity_labels != expected_opportunity_labels:
        errors.append(
            f"team.html: opportunity labels should be {expected_opportunity_labels!r}, found {opportunity_labels!r}"
        )
    expected_opportunity_accents = ["teal", "blue", "gold", "rose"]
    actual_opportunity_accents = [str(card.get("accent", "")) for card in parser.opportunities]
    if actual_opportunity_accents != expected_opportunity_accents:
        errors.append(
            f"team.html: opportunity entries should use accents {expected_opportunity_accents!r}, "
            f"found {actual_opportunity_accents!r}"
        )

    for card in parser.opportunities:
        label = str(card.get("label", ""))
        title = str(card.get("title", ""))
        expected_heading_id = {
            "Postdoc": "opportunity-postdoc-heading",
            "PhD": "opportunity-phd-heading",
            "Visiting": "opportunity-visiting-heading",
            "MSc": "opportunity-msc-heading",
        }.get(label, "")
        expected_title = {
            "Postdoc": "Prospective postdoctoral researchers",
            "PhD": "Prospective PhD students",
            "Visiting": "Visiting students",
            "MSc": "Prospective MSc students",
        }.get(label, "")
        expected_mailto_subject = {
            "Postdoc": "subject=Postdoc%20application%20-%20Applicant%20Name",
            "PhD": "subject=PhD%20application%20-%20Applicant%20Name",
            "Visiting": "subject=Visiting%20student%20application%20-%20Applicant%20Name",
            "MSc": "subject=MSc%20inquiry%20-%20Applicant%20Name",
        }.get(label, "")
        expected_card_id = expected_heading_id.removesuffix("-heading") if expected_heading_id else ""
        links = [str(link) for link in card.get("links", [])]
        link_actions = [
            {str(key): str(value) for key, value in action.items()}
            for action in card.get("link_actions", [])
            if isinstance(action, dict)
        ]
        mailto_labels = [
            action.get("text", "")
            for action in link_actions
            if action.get("href", "").startswith("mailto:eduard.gorbunov@mbzuai.ac.ae")
        ]
        if not title:
            errors.append(f"team.html: {label or 'opportunity'} card is missing a title")
        elif expected_title and title != expected_title:
            errors.append(f"team.html: {label} card title should be {expected_title!r}, found {title!r}")
        if expected_card_id and card.get("id") != expected_card_id:
            errors.append(f"team.html: {label} card should use id {expected_card_id!r}")
        if expected_heading_id and card.get("heading_id") != expected_heading_id:
            errors.append(f"team.html: {label} card heading should use id {expected_heading_id!r}")
        if expected_heading_id and card.get("labelledby") != expected_heading_id:
            errors.append(f"team.html: {label} card should be labelled by its heading")
        if card.get("list_role") != "listitem":
            errors.append(f"team.html: {label or 'opportunity'} card should use role='listitem'")
        if not any(link.startswith("mailto:eduard.gorbunov@mbzuai.ac.ae") for link in links):
            errors.append(f"team.html: {label or 'opportunity'} card is missing an email action")
        if expected_mailto_subject and not any(expected_mailto_subject in link for link in links):
            errors.append(f"team.html: {label} email action should use Applicant Name subject template")
        if mailto_labels != ["Email inquiry"]:
            errors.append(f"team.html: {label or 'opportunity'} email action should be labelled 'Email inquiry'")
        if label in {"PhD", "MSc"} and not any("mbzuai.ac.ae/study/" in link for link in links):
            errors.append(f"team.html: {label} card is missing MBZUAI admissions link")
        if label in {"PhD", "MSc"} and not any(
            action.get("href", "").startswith("https://mbzuai.ac.ae/study/")
            and action.get("text", "") == "MBZUAI admissions"
            for action in link_actions
        ):
            errors.append(f"team.html: {label} admissions action should be labelled 'MBZUAI admissions'")

    expected_guidelines = ["Subject line", "Motivation", "Background", "Documents", "Research alignment"]
    if parser.application_guidelines.get("id") != "application-guidelines":
        errors.append("team.html: application guidelines should use id 'application-guidelines'")
    if parser.application_guidelines.get("labelledby") != "application-guidelines-heading":
        errors.append("team.html: application guidelines should be labelled by application-guidelines-heading")
    if parser.guideline_labels != expected_guidelines:
        errors.append(f"team.html: guideline labels should be {expected_guidelines!r}, found {parser.guideline_labels!r}")

    return errors


def check_teaching() -> list[str]:
    errors: list[str] = []
    teaching_page = ROOT / "teaching.html"
    if not teaching_page.exists():
        errors.append("teaching.html: missing file")
        return errors

    teaching_text = teaching_page.read_text(encoding="utf-8", errors="ignore")
    teaching_parser = TeachingParser()
    teaching_parser.feed(teaching_text)
    teaching_links = {link for card in teaching_parser.course_cards for link in card.get("links", [])}

    required_page_phrases = [
        "Courses I have created, teaching roles, and course archives",
        "Courses I have created, teaching roles, and course archives by Eduard Gorbunov.",
    ]
    for phrase in required_page_phrases:
        if phrase not in teaching_text:
            errors.append(f"teaching.html: missing professional teaching page wording {phrase!r}")
    stale_teaching_intro = (
        "Courses created, teaching roles, and archived course resources",
        "Courses, teaching roles, and archived course materials",
    )
    if any(phrase in teaching_text for phrase in stale_teaching_intro):
        errors.append("teaching.html: teaching intro should use concise course-archive wording")

    required_schema_topics = [
        '"about": [',
        '"optimization"',
        '"distributed learning"',
        '"algorithms"',
        '"probability"',
        '"teaching materials"',
    ]
    for topic in required_schema_topics:
        if topic not in teaching_text:
            errors.append(f"teaching.html: structured metadata should include {topic!r}")

    required_teaching_labels = [
        '<section class="eg-teaching-section" id="courses-created" aria-labelledby="courses-created-heading">',
        '<h2 id="courses-created-heading">Courses created</h2>',
        '<section class="eg-teaching-section" id="teaching-assistant-roles" aria-labelledby="teaching-assistant-roles-heading">',
        '<h2 id="teaching-assistant-roles-heading">Teaching assistantships</h2>',
    ]
    for snippet in required_teaching_labels:
        if snippet not in teaching_text:
            errors.append(f"teaching.html: teaching section should be labelled by visible heading {snippet!r}")
    if "Teaching assistant roles" in teaching_text or "teaching assistant roles" in teaching_text:
        errors.append("teaching.html: teaching assistant labels should use academic assistantship wording")
    removed_teaching_blocks = [
        'class="eg-teaching-overview"',
        'class="eg-teaching-materials"',
        'eg-teaching-shortcuts',
    ]
    for snippet in removed_teaching_blocks:
        if snippet in teaching_text:
            errors.append(f"teaching.html: removed heavy teaching control should stay absent: {snippet!r}")

    expected_course_list_labels = ["Courses created", "Teaching assistantships"]
    actual_course_list_labels = [attrs.get("aria-label", "") for attrs in teaching_parser.course_lists]
    if actual_course_list_labels != expected_course_list_labels:
        errors.append(
            "teaching.html: course card lists should expose labels "
            f"{expected_course_list_labels!r}, found {actual_course_list_labels!r}"
        )
    for attrs in teaching_parser.course_lists:
        if attrs.get("role", "") != "list":
            errors.append("teaching.html: course card containers should use role='list'")

    courses_created_marker = (
        '<section class="eg-teaching-section" id="courses-created" aria-labelledby="courses-created-heading">'
    )
    assistant_roles_marker = (
        '<section class="eg-teaching-section" id="teaching-assistant-roles" '
        'aria-labelledby="teaching-assistant-roles-heading">'
    )
    created_course_count = 0
    assistant_role_count = 0
    if courses_created_marker in teaching_text and assistant_roles_marker in teaching_text:
        created_section = teaching_text.split(courses_created_marker, 1)[1].split(assistant_roles_marker, 1)[0]
        assistant_section = teaching_text.split(assistant_roles_marker, 1)[1].split("</main>", 1)[0]
        created_course_count = created_section.count('<article class="eg-course-card"')
        assistant_role_count = assistant_section.count('<article class="eg-course-card"')

    required_teaching_metadata = [
        '"mainEntity": [',
        '"@type": "ItemList"',
        '"@id": "https://eduardgorbunov.github.io/teaching.html#courses-created"',
        '"name": "Courses created"',
        f'"numberOfItems": {created_course_count}',
        '"@id": "https://eduardgorbunov.github.io/teaching.html#teaching-assistant-roles"',
        '"name": "Teaching assistantships"',
        f'"numberOfItems": {assistant_role_count}',
        '"itemListOrder": "https://schema.org/ItemListUnordered"',
        '"itemListElement": [',
    ]
    for snippet in required_teaching_metadata:
        if snippet not in teaching_text:
            errors.append(f"teaching.html: structured metadata should include {snippet!r}")

    if '<span class="eg-course-role">TA</span>' in teaching_text:
        errors.append("teaching.html: course role labels should avoid the shorthand 'TA'")
    if teaching_text.count('<span class="eg-course-role">Teaching assistant</span>') != 4:
        errors.append("teaching.html: teaching assistant course cards should use expanded role labels")
    expected_course_accents = ["teal", "blue", "teal", "blue", "gold", "rose"]
    actual_course_accents = [str(card.get("accent", "")) for card in teaching_parser.course_cards]
    if actual_course_accents != expected_course_accents:
        errors.append(
            f"teaching.html: course cards should use accents {expected_course_accents!r}, "
            f"found {actual_course_accents!r}"
        )

    for archive_page in EXPECTED_COURSE_ARCHIVES:
        if archive_page not in teaching_links:
            errors.append(f"teaching.html: missing archived course link {archive_page!r}")
    generic_course_link_labels = {
        "course venue",
        "mipt",
        "mbzuai",
        "course page",
        "google drive",
        "news page",
        "lecture playlist",
    }
    course_card_blocks = re.findall(
        r'<article class="eg-course-card"[^>]*>(.*?)</article>',
        teaching_text,
        flags=re.DOTALL,
    )
    unlabeled_generic_course_links: list[str] = []
    for block in course_card_blocks:
        for attrs, label_html in re.findall(r"<a\s+([^>]*)>(.*?)</a>", block, flags=re.DOTALL):
            link_label = " ".join(re.sub(r"<[^>]+>", "", label_html).split())
            if link_label.lower() not in generic_course_link_labels:
                continue
            aria_match = re.search(r'aria-label="([^"]+)"', attrs)
            aria_label = unescape(aria_match.group(1)) if aria_match else ""
            if not aria_label or aria_label.lower() == link_label.lower():
                unlabeled_generic_course_links.append(link_label)
    if unlabeled_generic_course_links:
        errors.append(
            "teaching.html: generic course-card links should have contextual aria-labels "
            f"({unlabeled_generic_course_links[:5]!r})"
        )

    course_card_ids = [str(card.get("id", "")) for card in teaching_parser.course_cards]
    missing_course_card_ids = [
        index for index, card_id in enumerate(course_card_ids, start=1) if not card_id
    ]
    duplicate_course_card_ids = sorted(
        card_id for card_id, count in Counter(course_card_ids).items() if card_id and count > 1
    )
    if missing_course_card_ids:
        errors.append(f"teaching.html: course cards missing ids {missing_course_card_ids}")
    if duplicate_course_card_ids:
        errors.append(f"teaching.html: duplicate course card ids {duplicate_course_card_ids}")

    for card_id in course_card_ids:
        if not card_id:
            continue
        structured_course_url = f'"url": "{SITE_URL}/teaching.html#{card_id}"'
        if teaching_text.count(structured_course_url) != 1:
            errors.append(
                f"teaching.html: course card {card_id!r} should have exactly one structured metadata URL"
            )

    for index, card in enumerate(teaching_parser.course_cards, start=1):
        card_id = str(card.get("id", ""))
        expected_title_id = f"{card_id}-title" if card_id else ""
        if not str(card.get("title", "")):
            errors.append(f"teaching.html: course card {index} is missing a title")
        if card.get("heading_id") != expected_title_id:
            errors.append(
                f"teaching.html: course card {index} heading id should be {expected_title_id!r}, "
                f"found {card.get('heading_id')!r}"
            )
        if card.get("labelledby") != expected_title_id:
            errors.append(
                f"teaching.html: course card {index} aria-labelledby should be {expected_title_id!r}, "
                f"found {card.get('labelledby')!r}"
            )
        if card.get("role") != "listitem":
            errors.append(f"teaching.html: course card {index} should use role='listitem'")

    for archive_page, expected in EXPECTED_COURSE_ARCHIVES.items():
        page = ROOT / archive_page
        if not page.exists():
            errors.append(f"{archive_page}: missing course archive page")
            continue

        page_text = page.read_text(encoding="utf-8", errors="ignore")
        parser = TeachingParser()
        parser.feed(page_text)
        english_archive_aria_labels = [
            'aria-label="Archive note"',
            'aria-label="Course summary"',
            'aria-label="Course page shortcuts"',
            'aria-label="Seminar materials"',
            'aria-label="Homework materials"',
            'aria-label="Optional homework materials"',
            'aria-label="Course news archive"',
            'aria-label="Algorithms and Models of Computation 2019:',
            'aria-label="Probability Theory 2018:',
        ]
        for snippet in english_archive_aria_labels:
            if snippet in page_text:
                errors.append(f"{archive_page}: Russian course content should not use English aria-label snippet {snippet!r}")
        english_archive_summary_snippets = [
            "<strong>Teaching assistant</strong>",
            "<strong>Spring 2019</strong>",
            "<strong>Fall 2018</strong>",
            "<strong>12 seminars · 9 homework sheets</strong>",
            "<strong>14 seminars · 10 optional homework sheets</strong>",
            "Консультация перед midterm",
            "консультации перед midterm",
            "Успехов на midterm",
            ">December 2018<",
        ]
        for snippet in english_archive_summary_snippets:
            if snippet in page_text:
                errors.append(f"{archive_page}: Russian course summary should not use English snippet {snippet!r}")
        if re.search(r'<div class="eg-course-update-body">.*?<br\s*/?>', page_text, flags=re.DOTALL):
            errors.append(f"{archive_page}: course update bodies should use paragraph markup instead of br separators")

        required_archive_labels = [
            '<section class="eg-course-panel" id="seminars" aria-labelledby="seminars-heading">',
            '<h2 id="seminars-heading">Семинары</h2>',
            '<section class="eg-course-panel" id="course-news" aria-labelledby="course-news-heading">',
            '<h2 id="course-news-heading">Новости</h2>',
        ]
        if archive_page == "amc2019.html":
            required_archive_labels.extend(
                [
                    '<section class="eg-course-panel" id="homework" aria-labelledby="homework-heading">',
                    '<h2 id="homework-heading">Домашние задания</h2>',
                ]
            )
        if archive_page == "pr_th.html":
            required_archive_labels.extend(
                [
                    '<section class="eg-course-panel" id="optional-homework" aria-labelledby="optional-homework-heading">',
                    '<h2 id="optional-homework-heading">Необязательные ДЗ</h2>',
                ]
            )
        for snippet in required_archive_labels:
            if snippet not in page_text:
                errors.append(f"{archive_page}: course panel should be labelled by visible heading {snippet!r}")

        required_archive_notice = [
            '<aside class="eg-course-archive-note" aria-label="Архивная заметка">',
            "<strong>Архив курса</strong>",
            "<span>Материалы сохранены для справки; расписание, дедлайны и объявления относятся к прошедшему семестру.</span>",
        ]
        for snippet in required_archive_notice:
            if snippet not in page_text:
                errors.append(f"{archive_page}: missing historical archive notice {snippet!r}")
        if page_text.count('class="eg-course-archive-note"') != 1:
            errors.append(f"{archive_page}: should include exactly one historical archive notice")

        if not parser.shortcuts:
            errors.append(f"{archive_page}: missing course shortcut navigation")
        elif parser.shortcuts[0] != (expected["return_label"], "teaching.html"):
            errors.append(
                f"{archive_page}: first shortcut should return to teaching page, found {parser.shortcuts[0]!r}"
            )

        shortcut_hrefs = {href for _, href in parser.shortcuts}
        missing_shortcuts = sorted(expected["required_shortcuts"] - shortcut_hrefs)
        if missing_shortcuts:
            errors.append(f"{archive_page}: missing course shortcuts {missing_shortcuts}")
        shortcut_markup = page_text.split('<nav class="eg-course-shortcuts"', 1)[-1].split("</nav>", 1)[0]
        unlabeled_download_shortcuts: list[str] = []
        for attrs, label in re.findall(r"<a ([^>]*)>(Google Drive|Теор\. минимум \d|Канон\. задание \d)</a>", shortcut_markup):
            if 'target="_blank"' not in attrs:
                continue
            if label == "Google Drive":
                expected_aria_prefix = 'aria-label="Открыть Google Drive: '
            else:
                expected_aria_prefix = f'aria-label="Открыть PDF: {label}"'
            if expected_aria_prefix not in attrs:
                unlabeled_download_shortcuts.append(label)
        if unlabeled_download_shortcuts:
            errors.append(
                f"{archive_page}: course download shortcuts need contextual aria-labels "
                f"{unlabeled_download_shortcuts!r}"
            )

        if not parser.resource_cards:
            errors.append(f"{archive_page}: expected archived course resource cards")
        if not parser.update_cards:
            errors.append(f"{archive_page}: expected archived course update cards")

        expected_archive_cards = {
            "amc2019.html": {
                "prefix": "amc2019-",
                "label_prefix": "Алгоритмы и модели вычислений, 2019:",
                "resource_list_labels": ["Материалы семинаров", "Домашние задания"],
                "resources": 21,
                "resource_times": 9,
                "pdf_links": 21,
                "solution_links": 0,
                "updates": 13,
                "summary": [
                    "<strong>Семинарист</strong>",
                    "<strong>ФУПМ, МФТИ</strong>",
                    "<strong>весна 2019</strong>",
                    "<strong>12 семинаров · 9 домашних заданий</strong>",
                ],
            },
            "pr_th.html": {
                "prefix": "pr-th-",
                "label_prefix": "Теория вероятностей, 2018:",
                "resource_list_labels": ["Материалы семинаров", "Необязательные домашние задания"],
                "resources": 24,
                "resource_times": 23,
                "pdf_links": 10,
                "solution_links": 25,
                "updates": 14,
                "summary": [
                    "<strong>Семинарист</strong>",
                    "<strong>ФУПМ, МФТИ</strong>",
                    "<strong>осень 2018</strong>",
                    "<strong>14 семинаров · 10 необязательных домашних заданий</strong>",
                ],
            },
        }[archive_page]

        actual_resource_list_labels = [attrs.get("aria-label", "") for attrs in parser.resource_lists]
        if actual_resource_list_labels != expected_archive_cards["resource_list_labels"]:
            errors.append(
                f"{archive_page}: resource lists should expose labels "
                f"{expected_archive_cards['resource_list_labels']!r}, found {actual_resource_list_labels!r}"
            )
        for attrs in parser.resource_lists:
            if attrs.get("role", "") != "list":
                errors.append(f"{archive_page}: resource list containers should use role='list'")

        actual_update_list_labels = [attrs.get("aria-label", "") for attrs in parser.update_lists]
        if actual_update_list_labels != ["Архив новостей курса"]:
            errors.append(
                f"{archive_page}: update lists should expose ['Архив новостей курса'], "
                f"found {actual_update_list_labels!r}"
            )
        for attrs in parser.update_lists:
            if attrs.get("role", "") != "list":
                errors.append(f"{archive_page}: update list containers should use role='list'")

        if '<section class="eg-course-summary" aria-label="Краткая информация о курсе" role="list">' not in page_text:
            errors.append(f"{archive_page}: missing compact course summary")
        if '<nav class="eg-course-shortcuts" aria-label="Навигация по странице курса">' not in page_text:
            errors.append(f"{archive_page}: course shortcut navigation should use a Russian aria-label")
        course_summary = page_text.split('<section class="eg-course-summary"', 1)[-1].split("</section>", 1)[0]
        if "<span>Организация</span>" not in course_summary:
            errors.append(f"{archive_page}: course summary should label ФУПМ/МФТИ as the organization")
        if "<span>Курс</span>" in course_summary:
            errors.append(f"{archive_page}: course summary should not label ФУПМ/МФТИ as the course")
        if course_summary.count("role=\"listitem\"") != 4:
            errors.append(f"{archive_page}: all compact course summary cards should expose role='listitem'")
        expected_summary_accents = ["teal", "blue", "gold", "rose"]
        actual_summary_accents = re.findall(r'<article data-accent="([^"]+)" role="listitem">', course_summary)
        if actual_summary_accents != expected_summary_accents:
            errors.append(
                f"{archive_page}: course summary cards should use accents "
                f"{expected_summary_accents!r}, found {actual_summary_accents!r}"
            )
        for snippet in expected_archive_cards["summary"]:
            if snippet not in page_text:
                errors.append(f"{archive_page}: course summary is missing {snippet!r}")

        if len(parser.resource_cards) != expected_archive_cards["resources"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['resources']} resource cards, "
                f"found {len(parser.resource_cards)}"
            )
        if len(parser.update_cards) != expected_archive_cards["updates"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['updates']} update cards, "
                f"found {len(parser.update_cards)}"
            )
        update_date_matches = re.findall(
            r'<time datetime="([^"]+)" class="eg-course-update-date">([^<]+)</time>',
            page_text,
        )
        if len(update_date_matches) != expected_archive_cards["updates"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['updates']} course update dates, "
                f"found {len(update_date_matches)}"
            )
        invalid_update_dates = []
        mismatched_update_dates = []
        for datetime_value, visible_date in update_date_matches:
            if not TIME_DATETIME_PATTERN.fullmatch(datetime_value):
                invalid_update_dates.append(datetime_value)
                continue
            expected_datetime = parse_russian_archive_date(visible_date)
            if expected_datetime is None:
                invalid_update_dates.append(visible_date)
            elif expected_datetime != datetime_value:
                mismatched_update_dates.append(
                    f"{visible_date} -> {datetime_value}, expected {expected_datetime}"
                )
        if invalid_update_dates:
            errors.append(f"{archive_page}: invalid course update datetime values {invalid_update_dates!r}")
        if mismatched_update_dates:
            errors.append(f"{archive_page}: mismatched course update dates {mismatched_update_dates!r}")
        if re.search(
            r'<article[^>]*class="eg-course-resource-card"[^>]*>\s*<div class="eg-course-resource-body"',
            page_text,
        ):
            errors.append(f"{archive_page}: resource cards should use structured headings, dates, and action rows")
        resource_card_blocks = re.findall(
            r'<article[^>]*class="eg-course-resource-card"[^>]*>.*?</article>',
            page_text,
            flags=re.DOTALL,
        )
        resource_card_markup = "\n".join(resource_card_blocks)
        plain_resource_date_spans = re.findall(
            r"<span>(?:23:00 )?\d{2}\.\d{2}\.\d{4}</span>",
            resource_card_markup,
        )
        if plain_resource_date_spans:
            errors.append(f"{archive_page}: resource dates and deadlines should use semantic time elements")
        resource_time_matches = re.findall(
            r'<time datetime="([^"]+)">([^<]+)</time>',
            resource_card_markup,
        )
        if len(resource_time_matches) != expected_archive_cards["resource_times"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['resource_times']} semantic resource dates, "
                f"found {len(resource_time_matches)}"
            )
        invalid_resource_times = []
        mismatched_resource_times = []
        for datetime_value, visible_date in resource_time_matches:
            if not COURSE_RESOURCE_DATETIME_PATTERN.fullmatch(datetime_value):
                invalid_resource_times.append(datetime_value)
                continue
            deadline_match = re.fullmatch(r"23:00 (\d{2})\.(\d{2})\.(\d{4})", visible_date)
            date_match = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", visible_date)
            if deadline_match:
                day, month, year = deadline_match.groups()
                expected_datetime = f"{year}-{month}-{day}T23:00"
            elif date_match:
                day, month, year = date_match.groups()
                expected_datetime = f"{year}-{month}-{day}"
            else:
                invalid_resource_times.append(visible_date)
                continue
            if datetime_value != expected_datetime:
                mismatched_resource_times.append(
                    f"{visible_date} -> {datetime_value}, expected {expected_datetime}"
                )
        if invalid_resource_times:
            errors.append(f"{archive_page}: invalid resource datetime values {invalid_resource_times!r}")
        if mismatched_resource_times:
            errors.append(f"{archive_page}: mismatched resource dates {mismatched_resource_times!r}")
        archive_artifact_patterns = [
            (r"Выкладываю<a", "missing space before archive update link"),
            (r"семинаров </a>и", "stray space inside archive update link text"),
            (r"задававать", "archive typo in question wording"),
            (r"отменятется", "archive typo in cancellation wording"),
            (r"<strong>\s*</strong>", "empty archive formatting tag"),
            (r"<strong>\[[^\]]+\]", "archive update date should use a time element"),
        ]
        for pattern, description in archive_artifact_patterns:
            if re.search(pattern, page_text):
                errors.append(f"{archive_page}: {description}")
        action_row_count = page_text.count('<div class="eg-course-resource-actions">')
        if action_row_count != expected_archive_cards["resources"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['resources']} resource action rows, "
                f"found {action_row_count}"
            )
        pdf_action_attrs = re.findall(
            r'<div class="eg-course-resource-actions"><a ([^>]*)>PDF</a></div>',
            page_text,
        )
        if len(pdf_action_attrs) != expected_archive_cards["pdf_links"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['pdf_links']} compact PDF action links, "
                f"found {len(pdf_action_attrs)}"
            )
        unlabeled_pdf_actions = [
            attrs for attrs in pdf_action_attrs if 'aria-label="Открыть PDF: ' not in attrs
        ]
        if unlabeled_pdf_actions:
            errors.append(f"{archive_page}: compact PDF action links should have contextual Russian aria-labels")
        solution_action_links = re.findall(r"<a ([^>]*)>(Без решений|С решениями)</a>", page_text)
        if len(solution_action_links) != expected_archive_cards["solution_links"]:
            errors.append(
                f"{archive_page}: expected {expected_archive_cards['solution_links']} solution-version links, "
                f"found {len(solution_action_links)}"
            )
        unlabeled_solution_actions = []
        for attrs, label in solution_action_links:
            expected_prefix = (
                'aria-label="Открыть PDF без решений: '
                if label == "Без решений"
                else 'aria-label="Открыть PDF с решениями: '
            )
            if expected_prefix not in attrs:
                unlabeled_solution_actions.append(label)
        if unlabeled_solution_actions:
            errors.append(
                f"{archive_page}: seminar solution-version links should have contextual Russian aria-labels"
            )
        if archive_page == "pr_th.html":
            if "??.12.2018" in page_text:
                errors.append(f"{archive_page}: unknown seminar date should be written professionally")

        archive_cards = [*parser.resource_cards, *parser.update_cards]
        archive_card_ids = [card["id"] for card in archive_cards]
        missing_archive_ids = [index for index, card_id in enumerate(archive_card_ids, start=1) if not card_id]
        duplicate_archive_ids = sorted(
            card_id for card_id, count in Counter(archive_card_ids).items() if card_id and count > 1
        )
        if missing_archive_ids:
            errors.append(f"{archive_page}: archive cards missing ids {missing_archive_ids}")
        if duplicate_archive_ids:
            errors.append(f"{archive_page}: duplicate archive card ids {duplicate_archive_ids}")

        for index, card in enumerate(archive_cards, start=1):
            card_id = card["id"]
            label = card["aria_label"]
            if card.get("role") != "listitem":
                errors.append(f"{archive_page}: archive card {index} should use role='listitem'")
            if card_id and not card_id.startswith(expected_archive_cards["prefix"]):
                errors.append(
                    f"{archive_page}: archive card {index} id should start with "
                    f"{expected_archive_cards['prefix']!r}, found {card_id!r}"
                )
            if not label:
                errors.append(f"{archive_page}: archive card {index} is missing aria-label")
            elif not label.startswith(expected_archive_cards["label_prefix"]):
                errors.append(
                    f"{archive_page}: archive card {index} aria-label should start with "
                    f"{expected_archive_cards['label_prefix']!r}, found {label!r}"
                )
            if "eg-course-update-card" in page_text and ": update " in label:
                errors.append(f"{archive_page}: archive card {index} aria-label should use polished Update wording")
            if label.endswith(": ") or "homework " in label.lower():
                errors.append(f"{archive_page}: archive card {index} aria-label should be specific and polished")

    return errors


def check_shared_behavior() -> list[str]:
    errors: list[str] = []
    script = ROOT / SHARED_SCRIPT

    if not script.exists():
        errors.append(f"{SHARED_SCRIPT}: missing shared script")
        return errors

    text = script.read_text(encoding="utf-8", errors="ignore")
    expected_snippets = {
        'window.addEventListener("hashchange", markActiveNavigation)': "hash navigation active state",
        'window.addEventListener("popstate", markActiveNavigation)': "back/forward navigation active state",
        "window.history.pushState": "same-page hash history",
        "focusAnchorTarget(target)": "focus management for in-page navigation",
        "target.focus({ preventScroll: true })": "non-scrolling target focus",
        'cardSelector: ".eg-publication-card"': "contextual publication action labels",
        'linkSelector: ".eg-publication-actions a"': "publication action label selector",
        'cardSelector: ".eg-news-card"': "contextual news action labels",
        'linkSelector: ".eg-news-actions-inline a, .eg-news-paper-links a"': "news action label selector",
        "compactNewsArchiveAbstracts()": "compact archived news abstracts",
        ".eg-news-archive-list .eg-news-abstract": "archived news abstract selector",
    }

    for snippet, description in expected_snippets.items():
        if snippet not in text:
            errors.append(f"{SHARED_SCRIPT}: missing {description}")

    return errors


def check_publication_filter_behavior() -> list[str]:
    errors: list[str] = []
    script = ROOT / PUBLICATION_FILTER_SCRIPT

    if not script.exists():
        errors.append(f"{PUBLICATION_FILTER_SCRIPT}: missing publication filter script")
        return errors

    text = script.read_text(encoding="utf-8", errors="ignore")
    expected_snippets = {
        "function readFilterParams()": "reusable query-string filter reader",
        "new URLSearchParams(window.location.search)": "query-string filter initialization",
        'params.getAll("tag")': "multiple topic tag URL parameters",
        'params.get("tags")': "legacy grouped topic tag URL parameter",
        "function validTagsFromParams(params)": "valid topic tag URL filtering",
        "return hasOption(tagFilter, tag);": "invalid topic tag URL filtering",
        'var selectedInitialType = params.get("type");': "initial publication type URL parameter",
        'var selectedInitialSearch = params.get("q");': "initial publication search URL parameter",
        'typeFilter.value = selectedInitialType && hasOption(typeFilter, selectedInitialType) ? selectedInitialType : "all";': "validated initial publication type filter application",
        "searchFilter.value = normalizeSearch(selectedInitialSearch);": "normalized initial publication search filter application",
        "function applyUrlState(syncMode)": "shareable URL filter state restoration",
        'window.addEventListener("popstate", function () {': "publication filter back/forward handling",
        "applyUrlState(false);": "publication filter popstate restoration",
        'applyUrlState("replace");': "canonical initial publication filter state",
        'var filterForm = document.querySelector(".eg-publication-controls");': "publication filter form binding",
        'var filterSummary = document.getElementById("publication-filter-summary");': "active filter summary binding",
        'filterForm.addEventListener("submit", function (event)': "publication filter form submit handling",
        "event.preventDefault();": "publication filter form submit prevention",
        'params.set("type", typeFilter.value)': "publication type URL sync",
        'params.set("q", normalizeSearch(searchFilter.value))': "search URL sync",
        'params.append("tag", tag)': "topic tag URL sync",
        'var shouldPush = mode === "push" && window.history.pushState && nextUrl !== currentUrl;': "intentional publication filter history push",
        'window.history[shouldPush ? "pushState" : "replaceState"](null, "", nextUrl);': "publication filter history sync mode",
        "function resetFilters(syncMode)": "shared publication filter reset",
        "function updateFilterSummary(selectedType, selectedActiveTags, searchQuery)": "active filter summary updater",
        '"Active filters: " + parts.join("; ") + "."': "active filter summary text",
        '"No filters applied."': "default filter summary text",
        "function abstractDetails(visibleOnly)": "visible-result abstract collection",
        'var card = item.closest ? item.closest(".eg-publication-card") : null;': "abstract toggle card lookup",
        "return card && !card.hidden;": "abstract toggle limited to visible publications",
        "var details = abstractDetails(true);": "visible abstracts used for toggle state",
        'event.key === "Escape"': "Escape key publication filter reset",
        'resetFilters("push")': "publication filter reset invocation",
        'applyFilters("replace")': "typing-friendly publication search URL sync",
        'applyFilters("push")': "shareable publication filter URL history entries",
        "clearButton.hidden = !hasActiveFilter;": "clear button visible only for active filters",
        'clearButton.classList.toggle("is-available", hasActiveFilter);': "clear button active-state class",
        'button.setAttribute("aria-pressed", active ? "true" : "false")': "venue filter pressed state",
        'activeTagList.classList.toggle("is-empty", !tags.length);': "compact empty selected-topic state",
        'emptyState.className = "eg-visually-hidden";': "hidden empty selected-topic status",
        'chip.setAttribute("aria-label", "Remove topic tag " + labelForTag(tag))': "active tag removal label",
        f'chip.setAttribute("aria-controls", "{PUBLICATION_FILTER_TARGETS}")': "active tag removal control targets",
        "card.hidden = !show": "publication visibility state",
        'empty.hidden = visible !== 0': "empty filter result state",
        'count.textContent = String(visible)': "visible publication count",
        "updateFilterSummary(selectedType, selectedActiveTags, searchQuery)": "active filter summary refresh",
        "updateAbstractToggleState();\n    if (syncMode) {": "abstract toggle refresh after filtering",
        "function applyVenueFilter(venueName)": "venue filter shortcut handler",
        'typeFilter.value = "conference paper"': "venue filter type selection",
        "searchFilter.value = venueName": "venue filter search selection",
        'button.addEventListener("click", function () {\n      applyVenueFilter(button.getAttribute("data-venue"));': "venue filter click handling",
        'button.classList.toggle("is-active", active)': "venue filter active state",
        "updatePublicationSummaries()": "publication summary counters",
        "enhanceActionLabels()": "publication action labels",
        'var abstractToggle = document.querySelector(".eg-abstract-toggle");': "publication abstract expand-collapse binding",
        "enhanceAbstractLabels()": "publication abstract labels",
        "return details.filter(function (item)": "publication abstract details collection",
        "function updateAbstractDisclosureState(details)": "publication abstract expanded-state updater",
        "function updateAbstractToggleState()": "publication abstract toggle-state updater",
        "function setAllAbstracts(open)": "publication bulk abstract toggle",
        'summary.setAttribute("aria-expanded", details.open ? "true" : "false")': "publication abstract expanded-state sync",
        'details.addEventListener("toggle", function () {': "publication abstract toggle-state listener",
        'abstractToggle.addEventListener("click", function () {': "publication abstract toggle click handling",
        'abstractToggle.textContent = allOpen ? "Collapse abstracts" : "Expand abstracts";': "publication abstract toggle label update",
        "window.MathJax.typesetPromise(details);": "bulk abstract math typesetting",
        "enhanceAbstractStates()": "publication abstract state enhancement",
    }

    for snippet, description in expected_snippets.items():
        if snippet not in text:
            errors.append(f"{PUBLICATION_FILTER_SCRIPT}: missing {description}")

    return errors


def check_theme_styles() -> list[str]:
    errors: list[str] = []
    stylesheet = ROOT / PRIMARY_STYLESHEET

    if not stylesheet.exists():
        errors.append(f"{PRIMARY_STYLESHEET}: missing shared theme stylesheet")
        return errors

    text = stylesheet.read_text(encoding="utf-8", errors="ignore")
    required_snippets = {
        "@media (max-width: 520px)": "narrow phone breakpoint",
        "grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));": "wrapped mobile sidebar navigation",
        "overflow-x: visible !important;": "mobile sidebar nav without clipped scrolling",
        ".eg-publication-card:target": "publication target highlight",
        ".eg-news-card:target": "news-card deep-link target highlight",
        ".eg-activity-card:target": "activity-card deep-link target highlight",
        ".eg-course-card:target": "course-card deep-link target highlight",
        ".eg-course-resource-card:target": "course-resource deep-link target highlight",
        "content-visibility: auto;\n  contain-intrinsic-size: auto 260px;": "long-list card rendering hints",
        "main > section[id],\n.eg-about-section[id]": "nested about-section deep-link scroll offset",
        "--eg-publication-anchor-offset: 24px;": "base publication deep-link anchor offset",
        "--eg-publication-anchor-offset: 326px;": "desktop sticky-filter publication anchor offset",
        ".eg-publication-list,\n.eg-publication-card[id]": "publication-list deep-link scroll offset",
        ".eg-news-card[id],\n.eg-activity-card[id],": "shared deep-link card scroll margins",
        ".eg-publication-list,\n  .eg-publication-card[id],\n  .eg-news-card[id],": "mobile publication-list deep-link offset",
        "main > section[id],\n  .eg-about-section[id]": "mobile nested about-section deep-link offset",
        ".eg-publication-type-badge": "explicit publication type badge styling hook",
        ".eg-book-card .eg-publication-status-badge": "explicit book publication status badge",
        ".eg-publication-filter-summary": "active publication filter summary styling",
        ".eg-publication-legend": "publication notation legend styling",
        ".eg-publication-legend sup": "publication notation marker styling",
        ".eg-abstract-toggle": "publication abstract expand-collapse control styling",
        '.eg-abstract-toggle[aria-pressed="true"]': "active publication abstract toggle styling",
        ".eg-publication-abstract summary::after": "publication abstract show-hide state chip",
        'content: "Show";': "publication abstract closed-state label",
        ".eg-publication-abstract[open] summary::after": "publication abstract open-state chip",
        'content: "Hide";': "publication abstract open-state label",
        ".eg-publication-shortcuts": "compact publication shortcut spacing",
        ".eg-filter-heading {\n  align-items: center;\n  border-bottom: 1px solid rgba(23, 79, 76, 0.1);": "publication filter panel heading",
        ".eg-filter-heading h2 {\n  color: var(--eg-ink);\n  font-size: 1.02rem;": "publication filter heading title",
        ".eg-filter-heading span {\n  color: var(--eg-teal);\n  font-size: 0.72rem;": "publication filter scope label",
        ".eg-tag-control {\n  align-items: end;\n  column-gap: 10px;": "compact publication topic selector row",
        ".eg-publication-overview {\n  display: grid;\n  gap: 8px;": "compact publication overview spacing",
        "grid-template-columns: repeat(5, minmax(116px, 1fr));": "stable publication overview card columns",
        "max-width: 980px;": "contained publication overview width",
        ".eg-publication-stat {\n  --eg-stat-accent: var(--eg-teal);\n  align-items: center;": "linked publication overview cards",
        ".eg-publication-stat[data-kind=\"all\"]": "distinct all-publications overview accent",
        "background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-stat-accent) 5%, #ffffff) 100%);": "subtle publication overview card tint",
        ".eg-publication-stat strong {\n  align-items: center;\n  background: color-mix(in srgb, var(--eg-stat-accent) 9%, #ffffff);": "publication overview count badge",
        ".eg-publication-stat:hover,\n.eg-publication-stat:focus": "publication overview hover focus styling",
        ".eg-publication-stat {\n    min-height: 76px;\n    padding: 10px 11px;\n  }": "phone compact publication overview cards",
        ".eg-publication-stat strong {\n    flex-basis: 38px;\n    font-size: 1.34rem;\n    height: 38px;": "phone compact publication overview count badge",
        ".eg-active-tag-list.is-empty": "compact empty topic tag state",
        ".eg-clear-filters[hidden]": "hidden clear-filter control styling",
        ".eg-conference-summary {\n  align-items: stretch;\n  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-blue-soft) 52%, #ffffff) 100%);": "structured major-conference counter panel",
        "border-left: 4px solid rgba(35, 79, 134, 0.38);": "major-conference counter accent edge",
        "grid-template-columns: minmax(148px, 0.72fr) minmax(0, 2.8fr);": "major-conference counter directory layout",
        ".eg-conference-summary-header {\n  align-items: center;\n  border-right: 1px solid rgba(35, 79, 134, 0.13);": "major-conference counter header",
        ".eg-conference-summary-header small": "major-conference counter subtitle",
        ".eg-conference-summary ul {\n  display: grid;\n  gap: 6px;\n  grid-template-columns: repeat(auto-fit, minmax(76px, 1fr));": "major-conference venue filter grid",
        ".eg-venue-filter {\n  align-items: flex-start;": "clickable major-conference venue filters",
        "--eg-venue-filter-accent": "explicit venue filter accent variable",
        "font-size: 0.72rem;\n  font-weight: 850;\n  gap: 2px;\n  line-height: 1.12;\n  min-height: 42px;\n  padding: 6px 8px;": "compact major-conference filter buttons",
        ".eg-venue-filter[data-accent=\"teal\"]": "teal venue filter accent variant",
        ".eg-venue-filter.is-active": "active major-conference venue filter styling",
        ".eg-conference-summary {\n    border-left-width: 3px;\n    gap: 7px;": "phone compact major-conference counter",
        ".eg-conference-summary ul {\n    gap: 5px;\n    grid-template-columns: repeat(2, minmax(0, 1fr));": "phone major-conference venue filter grid",
        ".eg-news-abstract-disclosure": "compact archived news abstract disclosure",
        "--eg-indigo: #5b568f;": "fifth accent color for featured news",
        ".eg-news-card-featured .eg-news-venue-links li[data-accent=\"indigo\"]": "explicit featured-news venue accent",
        ".eg-news-venue-count": "compact featured-news venue counts",
        ".eg-news-year-index.eg-news-year-index-plain {\n  align-items: center;\n  background: transparent;": "lightweight news year rail",
        "border-left: 3px solid rgba(23, 79, 76, 0.24);": "subtle news year rail accent",
        ".eg-news-year-index.eg-news-year-index-plain > span": "plain news year label styling",
        ".eg-news-year-index.eg-news-year-index-plain a {\n  background: transparent;\n  border: 0;": "plain news year links",
        ".eg-news-year-index.eg-news-year-index-plain a:hover,\n.eg-news-year-index.eg-news-year-index-plain a:focus": "plain news year hover state",
        ".eg-news-year-index.eg-news-year-index-plain {\n    display: flex;\n    gap: 7px 11px;": "phone plain news year rail",
        ".eg-activity-shortcuts": "compact activity shortcut spacing",
        ".eg-activity-overview {\n  display: grid;\n  gap: 9px;\n  grid-template-columns: repeat(2, minmax(0, 1fr));\n  margin: -8px 0 13px;": "compact activity overview spacing",
        "--eg-activity-stat-accent": "activity overview accent variable",
        ".eg-activity-stat {\n  --eg-activity-stat-accent: var(--eg-blue);\n  align-items: center;": "linked activity overview cards",
        "background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-activity-stat-accent) 5%, #ffffff) 100%);": "subtle activity overview card tint",
        ".eg-activity-stat strong {\n  align-items: center;\n  background: color-mix(in srgb, var(--eg-activity-stat-accent) 9%, #ffffff);": "activity overview count badge",
        ".eg-activity-stat[data-accent=\"teal\"]": "activity overview teal accent variant",
        ".eg-activity-overview {\n    gap: 8px;\n    margin-bottom: 12px;\n  }": "phone compact activity overview spacing",
        ".eg-activity-stat strong {\n    flex-basis: 38px;\n    font-size: 1.34rem;\n    height: 38px;": "phone compact activity overview count badge",
        ".eg-activity-materials {\n  align-items: stretch;\n  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-blue-soft) 56%, #ffffff) 100%);": "polished activity quick-index panel",
        "border-left: 4px solid rgba(35, 79, 134, 0.38);": "activity quick-index accent edge",
        "grid-template-columns: minmax(112px, 0.62fr) repeat(4, minmax(0, 1fr));": "desktop activity quick-index grid",
        "--eg-activity-material-accent": "activity materials accent variable",
        ".eg-activity-materials small {\n  color: var(--eg-muted);\n  font-size: 0.72rem;\n  font-weight: 820;": "compact activity quick-index labels",
        ".eg-activity-materials a[data-accent=\"rose\"]": "activity materials rose accent variant",
        ".eg-activity-materials {\n    align-items: stretch;\n    border-left-width: 3px;\n    display: grid;": "phone activity materials compact accent edge",
        "grid-template-columns: repeat(2, minmax(0, 1fr));\n    padding: 8px;": "phone activity materials grid",
        ".eg-activity-materials > span {\n    border-right: 0;\n    grid-column: 1 / -1;": "phone activity materials header reset",
        ".eg-activity-card {\n    gap: 9px;\n    padding: 15px 17px;": "phone compact activity card spacing",
        ".eg-activity-number {\n    align-items: center;\n    display: inline-flex;": "phone inline activity number badge",
        ".eg-teaching-shortcuts": "compact teaching shortcut spacing",
        ".eg-teaching-stat {\n  --eg-teaching-stat-accent: var(--eg-teal);\n  align-items: center;": "linked teaching overview cards",
        "background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-teaching-stat-accent) 5%, #ffffff) 100%);": "subtle teaching overview card tint",
        ".eg-teaching-stat strong {\n  align-items: center;\n  background: color-mix(in srgb, var(--eg-teaching-stat-accent) 9%, #ffffff);": "teaching overview number badge",
        ".eg-teaching-stat:hover,\n.eg-teaching-stat:focus": "teaching overview hover focus styling",
        ".eg-teaching-materials {\n  align-items: stretch;\n  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-teal-soft) 58%, #ffffff) 100%);": "compact teaching materials overview styling",
        "border-left: 4px solid color-mix(in srgb, var(--eg-teal) 64%, transparent);": "teaching materials accent edge",
        "grid-template-columns: minmax(118px, 0.72fr) repeat(4, minmax(0, 1fr));": "desktop teaching materials directory grid",
        "--eg-teaching-material-accent": "teaching materials accent variable",
        ".eg-teaching-materials a[data-accent=\"rose\"]": "teaching materials rose accent variant",
        ".eg-teaching-materials {\n    align-items: stretch;\n    border-left-width: 3px;\n    display: grid;": "phone teaching materials compact accent edge",
        "grid-template-columns: repeat(2, minmax(0, 1fr));\n    padding: 8px;": "phone teaching materials grid",
        ".eg-teaching-materials > span {\n    border-right: 0;\n    grid-column: 1 / -1;": "phone teaching materials header reset",
        ".eg-teaching-materials a {\n    align-items: flex-start;\n    flex-direction: column;": "phone teaching material tile stacking",
        ".eg-teaching-materials small,\n  .eg-teaching-materials strong": "phone teaching material label blocks",
        ".eg-about-snapshot": "compact about profile snapshot styling",
        ".eg-about-snapshot a": "about profile snapshot CV link styling",
        ".eg-about-snapshot a[data-accent=\"blue\"]": "about snapshot blue accent variant",
        ".eg-about-snapshot a[data-accent=\"gold\"]": "about snapshot gold accent variant",
        ".eg-about-snapshot a[data-accent=\"rose\"]": "about snapshot rose accent variant",
        "--eg-about-snapshot-accent": "about snapshot accent variable",
        ".eg-appointment-summary": "compact appointment timeline summary styling",
        "--eg-appointment-accent": "appointment timeline accent variable",
        ".eg-appointment-summary a[data-accent=\"rose\"]": "appointment timeline rose accent variant",
        ".eg-appointment-summary strong {\n  color: var(--eg-appointment-accent);": "appointment timeline date styling",
        ".eg-appointment-summary {\n    gap: 7px;\n    margin-bottom: 12px;\n  }": "phone compact appointment timeline summary",
        ".eg-research-snapshot": "compact research snapshot styling",
        ".eg-research-snapshot a[data-accent=\"gold\"]": "research snapshot accent variant",
        ".eg-research-snapshot strong": "research snapshot count styling",
        ".eg-research-snapshot {\n    gap: 8px;\n    grid-template-columns: repeat(2, minmax(0, 1fr));\n    margin-bottom: 14px;\n  }": "phone compact research snapshot",
        ".eg-research-venue-strip {\n  align-items: stretch;\n  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-blue-soft) 52%, #ffffff) 100%);": "compact research major-conference counter styling",
        "border-left: 4px solid rgba(35, 79, 134, 0.38);\n  border-radius: 6px;\n  box-shadow: 0 8px 18px rgba(27, 36, 53, 0.04);\n  display: grid;": "structured research major-conference strip layout",
        "grid-template-columns: minmax(150px, 0.72fr) repeat(4, minmax(0, 1fr));": "desktop research major-conference directory grid",
        ".eg-research-venue-header {\n  align-items: center;\n  border-right: 1px solid rgba(35, 79, 134, 0.13);": "research major-conference counter header",
        ".eg-research-venue-header small": "research major-conference counter subtitle",
        "--eg-venue-accent": "research major-conference accent variable",
        ".eg-research-venue-strip a[data-accent=\"teal\"]": "research major-conference teal accent variant",
        ".eg-research-venue-strip {\n    border-left-width: 3px;\n    gap: 6px;": "phone compact research major-conference strip",
        ".eg-research-venue-header {\n    border-right: 0;\n    gap: 2px;": "phone stacked research major-conference header",
        ".eg-research-venue-strip a {\n    min-height: 40px;\n    padding: 7px 9px;\n  }": "phone compact research major-conference links",
        ".eg-research-map": "compact research topic map styling",
        ".eg-research-map-grid": "research topic map grid",
        "--eg-research-map-accent": "research map accent variable",
        ".eg-research-map-card[data-accent=\"rose\"]": "research map rose accent variant",
        ".eg-research-map-card a:hover,\n.eg-research-map-card a:focus": "research map link hover focus styling",
        ".eg-research-map-grid {\n    gap: 8px;\n    grid-template-columns: 1fr;\n  }": "phone compact research map grid",
        ".eg-research-map {\n  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-teal-soft) 42%, #ffffff) 100%);": "compact research map panel",
        "border-left: 5px solid rgba(27, 111, 104, 0.38);": "research map panel accent edge",
        ".eg-research-map-card {\n  --eg-research-map-accent: var(--eg-teal);\n  background: rgba(255, 255, 255, 0.74);": "lightweight research map topic cards",
        ".eg-research-map-card a {\n  color: var(--eg-ink) !important;\n  display: inline-flex;\n  font-size: 0.86rem;": "compact research map topic links",
        ".eg-research-map-card {\n    border-radius: 5px;\n    padding: 10px 11px 10px 13px;\n  }": "phone compact research map cards",
        ".eg-profile-links .eg-link-count": "research entry-point count styling",
        ".eg-student-meta-wide": "explicit wide student metadata cell",
        "--eg-student-accent": "explicit student card accent variable",
        ".eg-student-card {\n  --eg-student-accent: var(--eg-blue);\n  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--eg-student-accent) 4%, #ffffff) 100%) !important;": "lightly tinted student cards",
        ".eg-student-meta div {\n  align-content: start;\n  background: color-mix(in srgb, var(--eg-student-accent) 7%, #ffffff);": "compact accent-aware student metadata cells",
        ".eg-student-card[data-accent=\"rose\"]": "student card rose accent variant",
        ".eg-student-role {\n  color: var(--eg-student-accent);": "student role accent styling",
        ".eg-opportunity-list {\n  border-top: 1px solid rgba(17, 73, 72, 0.13);": "lightweight opportunity list",
        ".eg-opportunity-item {\n  --eg-opportunity-accent: var(--eg-teal);": "accent-aware opportunity entries",
        "grid-template-columns: minmax(0, 1fr) auto;": "desktop opportunity list columns",
        ".eg-opportunity-item[data-accent=\"rose\"]": "opportunity list rose accent variant",
        ".eg-opportunity-item .eg-opportunity-label": "compact opportunity labels",
        ".eg-opportunity-item > a,\n.eg-opportunity-item .eg-opportunity-actions a": "inline opportunity actions",
        ".eg-opportunity-item {\n    gap: 9px;\n    grid-template-columns: 1fr;": "phone opportunity list stacking",
        ".eg-guideline-list {\n  color: #465665;\n  display: grid;\n  gap: 7px;\n  grid-template-columns: repeat(2, minmax(0, 1fr));": "compact two-column application checklist",
        ".eg-guideline-list {\n    grid-template-columns: 1fr;\n  }": "phone-stacked application checklist",
        ".eg-course-card {\n  --eg-course-accent: var(--eg-teal);\n  align-content: start;": "compact teaching course card layout",
        "grid-template-rows: auto auto auto minmax(34px, 1fr) auto;": "compact teaching course card content rows",
        ".eg-course-card .eg-course-role {\n  background: color-mix(in srgb, var(--eg-course-accent) 9%, #ffffff);": "accent badge teaching course roles",
        ".eg-course-card {\n    gap: 7px;\n    padding: 15px 17px;": "tablet compact teaching course cards",
        ".eg-teaching-section .eg-course-list {\n  gap: 12px;": "compact teaching course list spacing",
        ".eg-course-card[data-accent=\"rose\"]": "teaching course card rose accent variant",
        ".eg-course-summary": "compact archived course summary styling",
        ".eg-course-summary article": "archived course summary cards",
        "background: color-mix(in srgb, var(--eg-course-summary-accent) 4%, var(--eg-paper));": "flat tinted archived course summary cards",
        "box-shadow: none;\n  display: grid;\n  gap: 3px;\n  padding: 10px 12px;": "dense archived course summary cards",
        "--eg-course-summary-accent": "archived course summary accent variable",
        ".eg-course-summary article[data-accent=\"rose\"]": "archived course summary rose accent variant",
        ".eg-course-summary strong {\n  color: var(--eg-course-summary-accent);": "course summary accented values",
        ".eg-course-archive-note": "historical course archive notice styling",
        "border-left: 3px solid var(--eg-gold);": "subtle course archive notice accent",
        ".eg-course-shortcuts {\n  display: flex;\n  flex-wrap: wrap;\n  gap: 7px;\n  margin: 0 0 22px;": "compact course shortcut rail",
        ".eg-course-archive-note + .eg-course-summary": "course archive notice summary spacing",
        ".eg-course-archive-note {\n    align-items: start;\n    display: grid;": "phone course archive notice stacking",
        ".eg-course-resource-actions": "archived course resource action rows",
        ".eg-course-resource-card {\n  border-top: 4px solid var(--eg-teal) !important;\n  display: grid;": "denser archived course resource cards",
        ".eg-course-resource-card > time": "semantic archived course date styling",
        ".eg-course-update-card {\n  border-left: 4px solid var(--eg-gold) !important;\n  padding: 14px 18px;": "denser archived course update cards",
        ".eg-course-update-date": "archived course update date styling",
        ".eg-course-update-body p + p": "archived course update paragraph spacing",
        ".eg-course-summary {\n    grid-template-columns: repeat(2, minmax(0, 1fr));": "tablet course summary layout",
        ".eg-course-summary {\n    grid-template-columns: 1fr;\n    margin-bottom: 14px;": "phone course summary layout",
        ".eg-filter-row-primary {\n    grid-template-columns: 1fr;\n  }": "phone-stacked publication search controls",
        ".eg-sidebar .eg-sidebar-profiles": "sidebar profile link strip",
        ".eg-sidebar .eg-sidebar-affiliation span": "stacked sidebar affiliation lines",
        ".eg-sidebar .eg-sidebar-profile-link": "sidebar profile link styling",
        ".eg-sidebar .eg-sidebar-topic-link": "clickable sidebar research-topic styling",
        ".eg-sidebar .eg-sidebar-topic-link:hover,\n.eg-sidebar .eg-sidebar-topic-link:focus": "sidebar research-topic hover styling",
        "background: rgba(255, 255, 255, 0.78);\n  border: 1px solid rgba(27, 36, 53, 0.1);\n  border-left: 5px solid rgba(27, 111, 104, 0.42);": "professional footer panel",
        ".eg-footer-main p {\n  color: #465665;\n  flex: 1 1 360px;": "flexible footer identity text",
        ".eg-footer-links {\n  align-content: flex-start;\n  display: grid;": "structured footer link groups",
        ".eg-footer-link-group {\n  display: flex;\n  flex-wrap: wrap;\n  gap: 6px;": "footer grouped link clusters",
        ".eg-footer-link-group {\n    justify-content: flex-start;\n  }": "phone footer group alignment",
        ".eg-footer-note {\n  color: var(--eg-muted);\n  font-size: 0.82rem;\n  font-weight: 650;\n  margin: 10px 0 0;\n  padding-left: 25px;\n}": "aligned footer update note",
        "line-height: 1.1;\n  margin: 0 0 12px;\n  text-wrap: balance;": "balanced page heading wrapping",
        ".eg-news-title {\n  color: var(--eg-blue) !important;\n  font-size: 1.22rem;\n  font-weight: 900;\n  line-height: 1.3;\n  margin: 0 0 9px;\n  text-wrap: balance;\n}": "balanced news title wrapping",
        ".eg-news-paper-links a {\n  background: transparent;\n  border: 0;": "plain featured-news paper links",
        "line-height: 1.28;\n  max-width: 100%;\n  overflow-wrap: anywhere;\n  padding: 0 0 2px;": "long featured-news paper-link wrapping",
        ".eg-news-card-featured .eg-news-venue-links li {\n    background: transparent;\n    border-color: color-mix(in srgb, var(--eg-news-row-accent) 60%, transparent);\n    border-radius: 0;": "mobile lightweight featured-news venue rows",
        ".eg-news-paper-links {\n    display: flex;\n    flex-wrap: wrap;\n    gap: 4px 6px;\n  }": "mobile featured-news paper link spacing",
        ".eg-news-card-featured .eg-news-paper-links {\n    display: grid;\n    gap: 3px;\n  }": "mobile featured-news compact paper list",
        ".eg-news-card-featured .eg-news-paper-links a {\n    background: transparent;\n    border: 0;\n    border-left: 2px solid": "mobile featured-news paper list links",
        ".eg-news-paper-links a + a::before {\n    content: none;\n  }": "mobile featured-news links without inline separators",
        "@media print": "print stylesheet",
        "@page {\n    margin: 16mm;\n  }": "print page margins",
        ".eg-news-card,\n  .eg-news-year-index a,": "print coverage for news cards",
        ".eg-research-snapshot a,\n  .eg-research-venue-strip a,\n  .eg-research-map-card,": "print coverage for research cards",
        ".eg-publication-abstract > *:not(summary)": "print-expanded publication abstracts",
        ".eg-publication-abstract summary,\n  .eg-news-archive summary,": "print-hidden disclosure summaries",
        "content-visibility: visible;\n    contain-intrinsic-size: auto;": "print-visible long-list cards",
        'content: " (" attr(href) ")";': "print external URL hints",
        "@media (prefers-contrast: more)": "high-contrast user preference mode",
        ".eg-error-next-steps": "404 recommended recovery tile styling",
        "--eg-error-step-accent": "404 recovery tile accent variable",
        ".eg-error-next-steps a[data-accent=\"rose\"]": "404 recovery tile rose accent variant",
        ".eg-error-next-steps {\n    grid-template-columns: 1fr;\n  }": "phone stacked 404 recovery tiles",
        "outline-width: 4px;": "high-contrast focus outline",
        "text-decoration-thickness: 0.11em;": "high-contrast link underline thickness",
        ".eg-student-card,\n  .eg-note-card {\n    border-color: rgba(27, 36, 53, 0.28);": "high-contrast card boundaries",
        "@media (forced-colors: active)": "forced-colors accessibility mode",
        "outline: 2px solid Highlight;": "forced-colors focus outline",
        ".eg-error-primary-actions a,\n  .eg-error-links a,": "forced-colors 404 recovery link styling",
        "border: 1px solid ButtonText;": "forced-colors button borders",
        "color: HighlightText !important;": "forced-colors active state text",
    }

    for snippet, description in required_snippets.items():
        if snippet not in text:
            errors.append(f"{PRIMARY_STYLESHEET}: missing {description}")

    disallowed_positional_accent_selectors = [
        ".eg-conference-summary li:nth-child",
        ".eg-news-card-featured .eg-news-venue-links li:nth-child",
        ".eg-publication-meta span:nth-child(2)",
        ".eg-student-meta div:last-child:nth-child",
        ".eg-student-card:nth-child",
        ".eg-opportunity-item:nth-child",
        ".eg-course-card:nth-child",
    ]
    for selector in disallowed_positional_accent_selectors:
        if selector in text:
            errors.append(f"{PRIMARY_STYLESHEET}: card accents should use data-accent, not {selector}")

    return errors


def check_support_files() -> list[str]:
    errors: list[str] = []
    sitemap = ROOT / "sitemap.xml"
    robots = ROOT / "robots.txt"
    nojekyll = ROOT / NOJEKYLL_MARKER
    readme = ROOT / README_FILE
    gitignore = ROOT / GITIGNORE_FILE

    if not nojekyll.is_file():
        errors.append(f"{NOJEKYLL_MARKER}: missing GitHub Pages static-site marker")

    if not gitignore.exists():
        errors.append(f"{GITIGNORE_FILE}: missing local-artifact ignore rules")
    else:
        ignored_patterns = {
            line.strip()
            for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for pattern in EXPECTED_GITIGNORE_PATTERNS:
            if pattern not in ignored_patterns:
                errors.append(f"{GITIGNORE_FILE}: should ignore local artifact pattern {pattern!r}")

    if not readme.exists():
        errors.append(f"{README_FILE}: missing maintenance notes for the static website")
    else:
        readme_text = readme.read_text(encoding="utf-8", errors="ignore")
        required_readme_phrases = [
            "Static GitHub Pages website for Eduard Gorbunov.",
            "independent of generated-builder assets",
            "There is no build step",
            "python3 -m http.server 8000",
            "assets/theme/css/modern-academic.css",
            "Content conventions:",
            "Use explicit semantic hooks such as `data-accent`, `eg-publication-type-badge`, and `eg-student-meta-wide`",
            'Mark direct PDF links, including local files, arXiv PDFs, publisher PDFs, and OpenReview PDFs, with `type="application/pdf"`',
            "Keep `assets/images/eg-social-card.png` at 1200x630 for social previews",
            "Preserve accessibility and print polish: keep skip links, focus-visible states, reduced-motion support, high-contrast/forced-colors modes, and print-expanded abstracts/disclosures working after layout changes.",
            "Bump the stylesheet or script query-string version in every page, and in `scripts/check-site.py`, after changing shared CSS or JavaScript.",
            "python3 scripts/check-site.py",
            "node --check assets/theme/js/script.js",
            "node --check assets/theme/js/publication-filters.js",
            "strict layout-tag nesting",
        ]
        for phrase in required_readme_phrases:
            if phrase not in readme_text:
                errors.append(f"{README_FILE}: maintenance notes should include {phrase!r}")
        for phrase in ("Mobirise", "mbr-", "cid-", "data-app-modern-menu"):
            if phrase in readme_text:
                errors.append(f"{README_FILE}: maintenance notes should avoid old-builder marker {phrase!r}")

    for page in sorted(ROOT.glob("*.html")):
        page_text = page.read_text(encoding="utf-8", errors="ignore")
        for snippet in DISALLOWED_RSS_SNIPPETS:
            if snippet in page_text:
                errors.append(f"{page.name}: should not include RSS reference {snippet!r}")

        parser = PageParser()
        parser.feed(page_text)
        footer_links = [(link.get("label", ""), link.get("href", "")) for link in parser.footer_links]
        if footer_links != EXPECTED_FOOTER_LINKS:
            errors.append(f"{page.name}: footer links should be {EXPECTED_FOOTER_LINKS!r}, found {footer_links!r}")
        expected_footer_groups = [
            '<div class="eg-footer-link-group" aria-label="Contact and profiles">',
            '<div class="eg-footer-link-group" aria-label="Site sections">',
            '<div class="eg-footer-link-group" aria-label="Documents">',
        ]
        if page_text.count('class="eg-footer-link-group"') != len(expected_footer_groups):
            errors.append(f"{page.name}: footer links should be split into {len(expected_footer_groups)} groups")
        for footer_group in expected_footer_groups:
            if footer_group not in page_text:
                errors.append(f"{page.name}: missing grouped footer section {footer_group!r}")
        if FOOTER_ROLE_TEXT not in page_text:
            errors.append(f"{page.name}: footer role should use department-level wording")
        if OLD_FOOTER_ROLE_TEXT in page_text:
            errors.append(f"{page.name}: footer role should avoid compressed title wording")

        for footer_label, expected_aria_label in FOOTER_CONTEXTUAL_ARIA_LABELS.items():
            labelled_footer_links = [link for link in parser.footer_links if link.get("label") == footer_label]
            if labelled_footer_links and labelled_footer_links[0].get("aria_label") != expected_aria_label:
                errors.append(
                    f"{page.name}: footer {footer_label} link should use aria-label {expected_aria_label!r}"
                )

        for profile_label in sorted(FOOTER_PROFILE_LINK_LABELS):
            profile_links = [link for link in parser.footer_links if link.get("label") == profile_label]
            if len(profile_links) != 1:
                errors.append(f"{page.name}: expected exactly one footer {profile_label} link")
                continue
            profile_link = profile_links[0]
            if profile_link.get("target") != "_blank":
                errors.append(f"{page.name}: footer {profile_label} link should open in a new tab")
            if set(str(profile_link.get("rel", "")).split()) != {"me", "noopener", "noreferrer"}:
                errors.append(f"{page.name}: footer {profile_label} link should use rel='me noopener noreferrer'")

        cv_links = [link for link in parser.footer_links if link.get("label") == "CV"]
        if len(cv_links) != 1:
            errors.append(f"{page.name}: expected exactly one footer CV link")
        else:
            cv_link = cv_links[0]
            if cv_link.get("target") != "_blank":
                errors.append(f"{page.name}: footer CV link should open in a new tab")
            if set(str(cv_link.get("rel", "")).split()) != {"noopener", "noreferrer"}:
                errors.append(f"{page.name}: footer CV link should keep noopener/noreferrer")
            if cv_link.get("type") != "application/pdf":
                errors.append(f"{page.name}: footer CV link should declare type='application/pdf'")

    if not sitemap.exists():
        errors.append("sitemap.xml: missing file")
        return errors

    try:
        tree = ElementTree.parse(sitemap)
    except ElementTree.ParseError as exc:
        errors.append(f"sitemap.xml: invalid XML: {exc}")
        return errors

    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs: list[str] = []
    for url_node in tree.findall(".//sm:url", namespace):
        loc_node = url_node.find("sm:loc", namespace)
        lastmod_node = url_node.find("sm:lastmod", namespace)
        priority_node = url_node.find("sm:priority", namespace)

        if loc_node is None or not loc_node.text or not loc_node.text.strip():
            errors.append("sitemap.xml: URL entry is missing loc")
            continue

        loc = loc_node.text.strip()
        locs.append(loc)

        lastmod = lastmod_node.text.strip() if lastmod_node is not None and lastmod_node.text else ""
        if lastmod != SITEMAP_LASTMOD:
            errors.append(f"sitemap.xml: {loc} should use lastmod {SITEMAP_LASTMOD!r}")

        priority = priority_node.text.strip() if priority_node is not None and priority_node.text else ""
        try:
            priority_value = float(priority)
        except ValueError:
            errors.append(f"sitemap.xml: {loc} has invalid priority {priority!r}")
        else:
            if not 0 <= priority_value <= 1:
                errors.append(f"sitemap.xml: {loc} priority should be between 0 and 1")
    loc_set = set(locs)

    public_html = sorted(path for path in ROOT.glob("*.html") if path.name != "404.html")
    expected = {page_url(path) for path in public_html}

    for url in sorted(expected - loc_set):
        errors.append(f"sitemap.xml: missing public page {url}")

    for url in sorted(loc_set - expected):
        errors.append(f"sitemap.xml: unknown or non-public page {url}")

    for url in locs:
        if not url.startswith(f"{SITE_URL}/"):
            errors.append(f"sitemap.xml: unexpected domain {url}")
            continue
        relative = url.removeprefix(f"{SITE_URL}/") or "index.html"
        if not (ROOT / relative).exists():
            errors.append(f"sitemap.xml: URL target does not exist {url}")

    if not robots.exists():
        errors.append("robots.txt: missing file")
    else:
        robots_text = robots.read_text(encoding="utf-8", errors="ignore")
        if f"Sitemap: {SITE_URL}/sitemap.xml" not in robots_text:
            errors.append("robots.txt: missing sitemap declaration")

    return errors


def main() -> int:
    errors = (
        check_template_cleanup()
        + check_site()
        + check_homepage_news()
        + check_publications()
        + check_activities()
        + check_research()
        + check_about()
        + check_team()
        + check_teaching()
        + check_shared_behavior()
        + check_publication_filter_behavior()
        + check_theme_styles()
        + check_support_files()
    )
    if errors:
        print("\n".join(errors))
        return 1

    print("Static site checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
