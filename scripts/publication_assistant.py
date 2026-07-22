#!/usr/bin/env python3
"""Human-reviewed publication discovery and deterministic site generation.

The current website remains a static site.  This helper moves publication
metadata into ``data/publications.json``, renders the existing publication
cards, and prepares reviewable proposals from scholarly metadata services.
It never publishes changes and never silently changes curated scholarly data.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS_PAGE = ROOT / "publications.html"
DATA_FILE = ROOT / "data" / "publications.json"
DATA_SCHEMA_FILE = ROOT / "data" / "publications.schema.json"
AUTOMATION_DIR = ROOT / "automation"
CACHE_DIR = ROOT / ".publication-cache"
REVIEW_REPORT = AUTOMATION_DIR / "publication-review.md"
NEWS_DRAFT = AUTOMATION_DIR / "publication-news-draft.md"
CHANGED_PUBLICATIONS = AUTOMATION_DIR / "changed-publications.json"
SITE_URL = "https://eduardgorbunov.github.io"

SCHEMA_VERSION = 1
TARGET_AUTHOR = "Eduard Gorbunov"
DEFAULT_CONTACT_EMAIL = "eduard.gorbunov@mbzuai.ac.ae"
GOOGLE_SCHOLAR_URL = "https://scholar.google.com/citations?user=QPVriwoAAAAJ&hl=en"
ARXIV_AUTHOR_QUERY = 'au:"Eduard Gorbunov"'
OPENALEX_AUTHOR_ID = "A5087594198"
ORCID_ID = "0000-0002-3370-4130"

REVIEW_APPROVED = "approved"
REVIEW_NEEDED = "needs-review"
REVIEW_STATUSES = {REVIEW_APPROVED, REVIEW_NEEDED}

PROTECTED_FIELDS = [
    "tags",
    "authorsHtml",
    "authorRelations",
    "contributionNotes",
    "distinctions",
    "representativeSelections",
    "news",
    "removal",
]

PUBLICATION_TYPES = [
    {"value": "conference paper", "label": "Conference paper", "kind": "conference"},
    {"value": "journal paper", "label": "Journal paper", "kind": "journal"},
    {"value": "arXiv preprint", "label": "arXiv preprint", "kind": "preprint"},
    {
        "value": "living reference work entry",
        "label": "Reference work entry",
        "kind": "reference",
    },
]

MARKER_TYPES = [
    {"value": "team", "label": "Team member", "short": "T"},
    {"value": "visitor", "label": "Visiting student", "short": "V"},
    {"value": "external-bsc", "label": "Externally mentored BSc student", "short": "EB"},
    {"value": "external-msc", "label": "Externally mentored MSc student", "short": "EM"},
    {"value": "external-phd", "label": "Externally mentored PhD student", "short": "EP"},
    {
        "value": "external-researcher",
        "label": "Externally mentored postdoc or research assistant",
        "short": "ER",
    },
]

TAG_GROUPS = [
    {
        "label": "Core problem areas",
        "options": [
            {"value": "stochastic-optimization", "label": "Stochastic optimization"},
            {"value": "stochastic-gradient-descent", "label": "Stochastic gradient descent"},
            {"value": "convex-optimization", "label": "Convex optimization"},
            {
                "value": "min-max-variational-inequalities",
                "label": "Min-max/variational inequalities",
            },
            {"value": "last-iterate-convergence", "label": "Last-iterate convergence"},
            {"value": "probability-and-concentration", "label": "Probability and concentration"},
        ],
    },
    {
        "label": "Distributed and federated learning",
        "options": [
            {"value": "distributed-learning", "label": "Distributed learning"},
            {"value": "federated-learning", "label": "Federated learning"},
            {"value": "communication-compression", "label": "Communication compression"},
            {"value": "decentralized-optimization", "label": "Decentralized optimization"},
            {"value": "local-steps", "label": "Local steps"},
            {"value": "random-reshuffling", "label": "Random reshuffling"},
            {"value": "low-rank-fine-tuning", "label": "Low-rank fine-tuning"},
        ],
    },
    {
        "label": "Robustness, privacy, and noise",
        "options": [
            {"value": "high-probability-bounds", "label": "High-probability bounds"},
            {"value": "heavy-tailed-noise", "label": "Heavy-tailed noise"},
            {"value": "gradient-clipping", "label": "Gradient clipping"},
            {"value": "generalized-smoothness", "label": "Generalized smoothness"},
            {"value": "byzantine-robustness", "label": "Byzantine robustness"},
            {"value": "differential-privacy", "label": "Differential privacy"},
        ],
    },
    {
        "label": "Methods and algorithmic tools",
        "options": [
            {"value": "adaptive-methods", "label": "Adaptive methods"},
            {"value": "variance-reduction", "label": "Variance reduction"},
            {
                "value": "conditional-gradient-lmo-methods",
                "label": "Conditional gradient/LMO methods",
            },
            {
                "value": "derivative-free-zeroth-order-methods",
                "label": "Derivative-free/zeroth-order methods",
            },
            {"value": "higher-order-methods", "label": "Higher-order methods"},
            {
                "value": "coordinate-descent-type-methods",
                "label": "Coordinate descent type methods",
            },
            {"value": "inexact-oracles", "label": "Inexact oracles"},
        ],
    },
]

MAJOR_VENUES = [
    {"name": "NeurIPS", "accent": "blue"},
    {"name": "ICML", "accent": "teal"},
    {"name": "AISTATS", "accent": "blue"},
    {"name": "ICLR", "accent": "teal"},
    {"name": "UAI", "accent": "blue"},
    {"name": "COLT", "accent": "blue"},
    {"name": "EMNLP", "accent": "teal"},
]

DISCOVERY_CLASSIFICATIONS = [
    "new paper",
    "published version found",
    "metadata update",
    "possible duplicate",
    "conflict",
]


class PublicationAssistantError(RuntimeError):
    """A user-facing automation error."""


class FirstTagParser(HTMLParser):
    """Parse attributes from one HTML element."""

    def __init__(self) -> None:
        super().__init__()
        self.tag = ""
        self.attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.tag:
            self.tag = tag
            self.attrs = {name: value or "" for name, value in attrs}


@dataclass
class Candidate:
    """Normalized record returned by an external metadata service."""

    title: str
    authors: list[str]
    abstract: str = ""
    published_date: str = ""
    publication_type: str = "arXiv preprint"
    venue: str = ""
    doi: str = ""
    arxiv: str = ""
    openalex: str = ""
    orcid_put_code: str = ""
    links: dict[str, str] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)

    def key(self) -> str:
        if self.doi:
            return f"doi:{normalize_doi(self.doi)}"
        if self.arxiv:
            return f"arxiv:{normalize_arxiv_id(self.arxiv)}"
        return f"title:{normalize_title(self.title)}"


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PublicationAssistantError(
            f"Missing {path.relative_to(ROOT)}. Run `python3 scripts/publication_assistant.py bootstrap`."
        ) from exc
    except json.JSONDecodeError as exc:
        raise PublicationAssistantError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_text(rendered, encoding="utf-8")


def strip_html(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_space(html.unescape(value))


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value: str) -> str:
    value = strip_html(value).lower()
    value = value.replace("–", "-").replace("—", "-").replace("‑", "-")
    value = re.sub(r"\$[^$]*\$", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def normalize_person(value: str) -> str:
    value = html.unescape(strip_html(value)).lower()
    value = re.sub(r"[^a-z]+", " ", value)
    return normalize_space(value)


def normalize_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    return value.removeprefix("doi:").strip()


def normalize_arxiv_id(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", value)
    value = value.removesuffix(".pdf")
    return re.sub(r"v\d+$", "", value)


def arxiv_id_from_doi(value: str) -> str:
    doi = normalize_doi(value)
    prefix = "10.48550/arxiv."
    return normalize_arxiv_id(doi[len(prefix) :]) if doi.startswith(prefix) else ""


def slugify(value: str, limit: int = 92) -> str:
    normalized = normalize_title(value).replace(" ", "-")
    return normalized[:limit].strip("-") or "publication"


def parse_start_tag(fragment: str) -> dict[str, str]:
    parser = FirstTagParser()
    parser.feed(fragment)
    return parser.attrs


def find_matching_tag_end(source: str, start: int, tag: str) -> int:
    pattern = re.compile(rf"</?{re.escape(tag)}\b[^>]*>", re.IGNORECASE)
    depth = 0
    for match in pattern.finditer(source, start):
        token = match.group(0)
        if token.startswith("</"):
            depth -= 1
            if depth == 0:
                return match.end()
        elif not token.rstrip().endswith("/>"):
            depth += 1
    raise PublicationAssistantError(f"Unclosed <{tag}> element in publications.html")


def extract_element(source: str, tag: str, class_name: str | None = None) -> str:
    class_fragment = rf'[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"' if class_name else "[^>]*"
    match = re.search(rf"<{tag}\b{class_fragment}[^>]*>", source, flags=re.IGNORECASE)
    if not match:
        raise PublicationAssistantError(f"Could not find <{tag}> with class {class_name!r}")
    return source[match.start() : find_matching_tag_end(source, match.start(), tag)]


def element_inner(fragment: str, tag: str) -> str:
    start = fragment.find(">")
    end = fragment.lower().rfind(f"</{tag.lower()}>")
    if start < 0 or end < 0:
        raise PublicationAssistantError(f"Malformed <{tag}> element")
    return fragment[start + 1 : end]


def iter_direct_articles(source: str) -> Iterator[str]:
    pattern = re.compile(r'<article\b[^>]*class="[^"]*\beg-publication-card\b[^"]*"[^>]*>')
    for match in pattern.finditer(source):
        attrs = parse_start_tag(match.group(0))
        if "eg-book-card" in attrs.get("class", "").split():
            continue
        yield source[match.start() : find_matching_tag_end(source, match.start(), "article")]


def iter_direct_article_entries(source: str) -> Iterator[tuple[str, str]]:
    pattern = re.compile(r'<article\b[^>]*class="[^"]*\beg-publication-card\b[^"]*"[^>]*>')
    for match in pattern.finditer(source):
        attrs = parse_start_tag(match.group(0))
        if "eg-book-card" in attrs.get("class", "").split():
            continue
        line_start = source.rfind("\n", 0, match.start()) + 1
        indent = source[line_start : match.start()]
        yield indent, source[match.start() : find_matching_tag_end(source, match.start(), "article")]


def extract_publication_region(page_text: str) -> tuple[int, int, str]:
    section_match = re.search(r'<section\b[^>]*id="publication-list"[^>]*>', page_text)
    if not section_match:
        raise PublicationAssistantError("Could not find #publication-list in publications.html")
    start = section_match.end()
    section_end = find_matching_tag_end(page_text, section_match.start(), "section")
    end = page_text.rfind("</section>", start, section_end)
    if end < start:
        raise PublicationAssistantError("Could not find the end of #publication-list")
    return start, end, page_text[start:end]


def parse_link(fragment: str) -> dict[str, str]:
    match = re.search(r"<a\b[^>]*>", fragment, flags=re.IGNORECASE)
    if not match:
        return {}
    attrs = parse_start_tag(match.group(0))
    close = fragment.lower().find("</a>", match.end())
    label_html = fragment[match.end() : close] if close >= 0 else ""
    return {
        "label": strip_html(label_html),
        "href": html.unescape(attrs.get("href", "")),
        "type": attrs.get("type", ""),
        "target": attrs.get("target", ""),
        "rel": attrs.get("rel", ""),
        "ariaLabel": html.unescape(attrs.get("aria-label", "")),
        "class": attrs.get("class", ""),
    }


def parse_actions(fragment: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for match in re.finditer(r"<a\b[^>]*>.*?</a>", fragment, flags=re.IGNORECASE | re.DOTALL):
        result.append(parse_link(match.group(0)))
    return result


def infer_identifiers(*values: str) -> dict[str, str]:
    identifiers = {"doi": "", "arxiv": "", "openalex": "", "orcid": ""}
    for value in values:
        decoded = html.unescape(value)
        doi_match = re.search(r"(?:doi\.org/|doi:\s*)(10\.\d{4,9}/[^\s\"<>]+)", decoded, flags=re.I)
        if doi_match:
            identifiers["doi"] = normalize_doi(doi_match.group(1).rstrip(".,;)"))
        arxiv_match = re.search(r"arxiv\.org/(?:abs|pdf)/([^?\s\"<>]+)", decoded, flags=re.I)
        if arxiv_match:
            identifiers["arxiv"] = normalize_arxiv_id(arxiv_match.group(1))
        openalex_match = re.search(r"openalex\.org/(W\d+)", decoded, flags=re.I)
        if openalex_match:
            identifiers["openalex"] = openalex_match.group(1).upper()
    return identifiers


def parse_authors_plain(authors_html: str) -> list[dict[str, Any]]:
    visible = re.sub(r'<span\b[^>]*class="[^"]*\beg-author-note\b[^"]*".*?</span>\s*</span>', "", authors_html, flags=re.DOTALL)
    visible = re.sub(r'<span\b[^>]*class="[^"]*\beg-author-note\b[^"]*".*?</span>', "", visible, flags=re.DOTALL)
    visible = re.sub(r"<sup\b[^>]*>.*?</sup>", "", visible, flags=re.DOTALL)
    plain = strip_html(visible)
    parts = [normalize_space(part) for part in re.split(r",\s*|\s+and\s+", plain) if normalize_space(part)]
    return [{"name": name, "isMe": normalize_person(name) == normalize_person(TARGET_AUTHOR)} for name in parts]


def parse_author_annotations(authors_html: str, authors: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach contribution and mentoring annotations to their authors."""
    enriched = copy.deepcopy(list(authors))
    positions: list[int] = []
    cursor = 0
    for author in enriched:
        name = str(author.get("name", ""))
        escaped_name = html.escape(name, quote=False)
        position = authors_html.find(escaped_name, cursor)
        if position < 0:
            position = authors_html.find(name, cursor)
        if position < 0:
            raise PublicationAssistantError(f"Could not locate author {name!r} in publication markup")
        positions.append(position)
        cursor = position + len(escaped_name)

    relation_pattern = re.compile(
        r"\beg-author-relation-(team|visitor|external-(?:bsc|msc|phd|researcher))\b"
    )
    marker_pattern = re.compile(
        r'<sup\b(?=[^>]*class="[^"]*\beg-author-marker\b)[^>]*>(.*?)</sup>',
        flags=re.DOTALL,
    )
    for index, author in enumerate(enriched):
        start = positions[index]
        end = positions[index + 1] if index + 1 < len(positions) else len(authors_html)
        segment = authors_html[start:end]
        author["markers"] = [strip_html(value) for value in marker_pattern.findall(segment)]
        author["relations"] = list(dict.fromkeys(relation_pattern.findall(segment)))
    return enriched


def html_tag_names(fragment: str) -> set[str]:
    return {match.group(1).lower() for match in re.finditer(r"<(/?[a-z0-9]+)\b", fragment, flags=re.I)}


def bootstrap_record(article: str) -> dict[str, Any]:
    article_start = re.match(r"<article\b[^>]*>", article)
    if not article_start:
        raise PublicationAssistantError("Malformed publication card")
    attrs = parse_start_tag(article_start.group(0))
    meta = extract_element(article, "div", "eg-publication-meta")
    meta_items = re.findall(r"<span\b[^>]*>(.*?)</span>", element_inner(meta, "div"), flags=re.DOTALL)
    number_match = re.search(r"#(\d+)", strip_html(meta_items[0] if meta_items else ""))
    number = int(number_match.group(1)) if number_match else 0

    heading = extract_element(article, "h2")
    heading_attrs = parse_start_tag(heading[: heading.find(">") + 1])
    title_html = element_inner(heading, "h2")
    title_link = parse_link(title_html)
    link_match = re.search(r"<a\b[^>]*>(.*?)</a>", title_html, flags=re.DOTALL)
    title_content_html = link_match.group(1) if link_match else title_html

    authors = extract_element(article, "p", "eg-publication-authors")
    authors_html = element_inner(authors, "p")
    venue = extract_element(article, "p", "eg-publication-venue")
    venue_start = venue[: venue.find(">") + 1]
    venue_attrs = parse_start_tag(venue_start)
    venue_html = element_inner(venue, "p")

    details = extract_element(article, "details", "eg-publication-abstract")
    abstract_match = re.search(r"<p\b[^>]*>(.*)</p>\s*</details>", details, flags=re.DOTALL)
    abstract_html = abstract_match.group(1) if abstract_match else ""

    tags_element = extract_element(article, "div", "eg-publication-tags")
    visible_tags = [strip_html(item) for item in re.findall(r"<span\b[^>]*>(.*?)</span>", tags_element, flags=re.DOTALL)]
    tag_values = attrs.get("data-tags", "").split()

    actions_element = extract_element(article, "div", "eg-publication-actions")
    actions = parse_actions(actions_element)
    note_html = ""
    note_match = re.search(r'<p\b[^>]*class="[^"]*\beg-publication-note\b[^"]*"[^>]*>(.*?)</p>', article, flags=re.DOTALL)
    if note_match:
        note_html = note_match.group(1)

    identifiers = infer_identifiers(
        title_link.get("href", ""),
        " ".join(action.get("href", "") for action in actions),
        venue_html,
    )
    distinction_labels = re.findall(r"<strong\b[^>]*>(.*?)</strong>", venue_html, flags=re.DOTALL)
    award_actions = [action for action in actions if "award" in action.get("class", "").lower()]
    structured_authors = parse_author_annotations(authors_html, parse_authors_plain(authors_html))
    relations = sorted(
        {
            relation
            for author in structured_authors
            for relation in author.get("relations", [])
        }
    )
    contribution_notes = []
    if "eg-author-marker" in authors_html:
        contribution_notes.append("author markers preserved in authorsHtml")
    if "eg-author-note" in authors_html:
        contribution_notes.append(strip_html(authors_html.split('class="eg-author-note"', 1)[1]))

    return {
        "id": attrs.get("id", ""),
        "number": number,
        "type": attrs.get("data-type", ""),
        "typeLabel": strip_html(meta_items[1] if len(meta_items) > 1 else attrs.get("data-type", "")),
        "dateLabel": strip_html(meta_items[-1] if meta_items else ""),
        "onlineDate": "",
        "title": strip_html(title_content_html),
        "titleHtml": title_content_html.strip(),
        "titleLink": title_link,
        "authors": structured_authors,
        "authorsHtml": authors_html.strip(),
        "venue": strip_html(venue_html),
        "venueHtml": venue_html.strip(),
        "venueClasses": [value for value in venue_attrs.get("class", "").split() if value != "eg-publication-venue"],
        "abstract": strip_html(abstract_html),
        "abstractHtml": abstract_html.strip(),
        "noteHtml": note_html.strip(),
        "tags": tag_values,
        "tagLabels": visible_tags,
        "actions": actions,
        "identifiers": identifiers,
        "authorRelations": relations,
        "contributionNotes": contribution_notes,
        "distinctions": [strip_html(item) for item in distinction_labels] + [action["label"] for action in award_actions],
        "representativeSelections": [],
        "news": {"enabled": False, "customText": ""},
        "displayOverrides": ["titleHtml", "authorsHtml", "venueHtml", "abstractHtml", "noteHtml"],
        "review": {
            "status": REVIEW_APPROVED,
            "lastReviewed": utc_today(),
            "source": "current website",
        },
        "provenance": {
            "record": "current website",
            "title": "current website",
            "authors": "current website",
            "venue": "current website",
            "abstract": "current website",
            "tags": "manual",
            "authorRelations": "manual",
            "distinctions": "manual",
        },
        "pendingChanges": {},
        "sourceHtmlTags": sorted(html_tag_names(article)),
    }


def bootstrap_data(page_text: str) -> dict[str, Any]:
    _, _, region = extract_publication_region(page_text)
    publications = []
    for source_indent, article in iter_direct_article_entries(region):
        record = bootstrap_record(article)
        record["sourceIndent"] = source_indent
        publications.append(record)
    publications.sort(key=lambda item: int(item["number"]), reverse=True)
    return {
        "$schema": "./publications.schema.json",
        "schemaVersion": SCHEMA_VERSION,
        "generatedFrom": "publications.html",
        "createdAt": utc_today(),
        "author": {
            "name": TARGET_AUTHOR,
            "email": DEFAULT_CONTACT_EMAIL,
            "googleScholar": GOOGLE_SCHOLAR_URL,
            "arxivQuery": ARXIV_AUTHOR_QUERY,
            "openAlexAuthorId": OPENALEX_AUTHOR_ID,
            "orcid": ORCID_ID,
        },
        "protectedFields": PROTECTED_FIELDS,
        "publicationTypes": PUBLICATION_TYPES,
        "markerTypes": MARKER_TYPES,
        "tagGroups": TAG_GROUPS,
        "majorVenues": MAJOR_VENUES,
        "publications": publications,
    }


def tag_label_map(data: dict[str, Any]) -> dict[str, str]:
    return {
        option["value"]: option["label"]
        for group in data.get("tagGroups", [])
        for option in group.get("options", [])
    }


def relation_config_map(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {item["value"]: item for item in data.get("markerTypes", [])}


def render_attrs(attributes: dict[str, str], *, preferred_order: Sequence[str] = ()) -> str:
    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name in preferred_order:
        if name in attributes and attributes[name]:
            ordered.append((name, attributes[name]))
            seen.add(name)
    for name, value in attributes.items():
        if name not in seen and value:
            ordered.append((name, value))
    return " ".join(f'{name}="{escape_attr(value)}"' for name, value in ordered)


def escape_attr(value: str) -> str:
    """Escape a double-quoted HTML attribute without rewriting apostrophes."""
    return html.escape(value, quote=True).replace("&#x27;", "'")


def render_link(link: dict[str, str], label_html: str | None = None) -> str:
    attributes = {
        "class": link.get("class", ""),
        "href": link.get("href", ""),
        "type": link.get("type", ""),
        "target": link.get("target", ""),
        "rel": link.get("rel", ""),
        "aria-label": link.get("ariaLabel", ""),
    }
    attrs = render_attrs(
        attributes,
        preferred_order=("class", "href", "type", "target", "rel", "aria-label"),
    )
    label = label_html if label_html is not None else html.escape(link.get("label", ""))
    return f"<a {attrs}>{label}</a>"


def render_authors(record: dict[str, Any], data: dict[str, Any]) -> str:
    if record.get("authorsHtml"):
        return str(record["authorsHtml"])
    relation_types = relation_config_map(data)
    rendered: list[str] = []
    for author in record.get("authors", []):
        name = html.escape(str(author.get("name", "")))
        if author.get("isMe"):
            name = f"<strong>{name}</strong>"
        for marker in author.get("markers", []):
            name += f'<sup class="eg-author-marker" aria-hidden="true">{html.escape(str(marker))}</sup>'
        for relation in author.get("relations", []):
            config = relation_types.get(str(relation), {})
            label = config.get("label", str(relation))
            short = config.get("short", str(relation))
            name += (
                f'<sup class="eg-author-relation eg-author-relation-{escape_attr(str(relation))}" '
                f'title="{escape_attr(label)}" aria-label="{escape_attr(label)}">'
                f"{html.escape(short)}</sup>"
            )
        rendered.append(name)
    if len(rendered) == 2:
        return " and ".join(rendered)
    if len(rendered) > 2:
        return ", ".join(rendered[:-1]) + ", " + rendered[-1]
    return "".join(rendered)


def render_publication(record: dict[str, Any], data: dict[str, Any]) -> str:
    publication_id = str(record["id"])
    title_html = str(record.get("titleHtml") or html.escape(str(record["title"])))
    title_link = copy.deepcopy(record.get("titleLink") or {})
    if not title_link.get("href"):
        title_link = {
            "href": best_candidate_link(record),
            "target": "_blank",
            "rel": "noopener noreferrer",
            "ariaLabel": f"Open paper page for {record['title']}",
        }
    title_anchor = render_link(title_link, title_html)
    authors_html = render_authors(record, data)
    venue_html = str(record.get("venueHtml") or html.escape(str(record.get("venue", ""))))
    abstract_html = str(record.get("abstractHtml") or html.escape(str(record.get("abstract", ""))))
    note_html = str(record.get("noteHtml", ""))
    labels = tag_label_map(data)
    stored_labels = record.get("tagLabels", [])
    visible_labels = stored_labels if len(stored_labels) == len(record.get("tags", [])) else []
    tag_spans = "".join(
        f"<span>{html.escape(visible_labels[index] if visible_labels else labels.get(tag, tag.replace('-', ' ')))}</span>"
        for index, tag in enumerate(record.get("tags", []))
    )
    action_links = "".join(render_link(action) for action in record.get("actions", []))
    venue_classes = " ".join(record.get("venueClasses", []))
    venue_class_attr = "eg-publication-venue" + (f" {venue_classes}" if venue_classes else "")
    meta = (
        f'<div class="eg-publication-meta"><span>#{int(record["number"])}</span>'
        f'<span class="eg-publication-type-badge">{html.escape(str(record.get("typeLabel") or record["type"]))}</span>'
        f'<span>{html.escape(str(record.get("dateLabel", "")))}</span></div>'
    )
    note = f'\n  <p class="eg-publication-note">{note_html}</p>' if note_html else ""
    return (
        f'<article class="eg-publication-card" role="listitem" id="{escape_attr(publication_id)}" '
        f'aria-labelledby="{escape_attr(publication_id)}-title" '
        f'data-type="{escape_attr(str(record["type"]))}" '
        f'data-tags="{escape_attr(" ".join(record.get("tags", [])))}">\n'
        f"  {meta}\n"
        f'  <h2 id="{escape_attr(publication_id)}-title">{title_anchor}</h2>\n'
        f'  <p class="eg-publication-authors">{authors_html}</p>\n'
        f'  <p class="{escape_attr(venue_class_attr)}">{venue_html}</p>\n'
        '  <details class="eg-publication-abstract">\n'
        "    <summary>Abstract</summary>\n"
        f"    <p>{abstract_html}</p>\n"
        f"  </details>{note}\n"
        f'  <div class="eg-publication-tags">{tag_spans}</div>\n'
        f'  <div class="eg-publication-actions">{action_links}</div>\n'
        "</article>"
    )


def best_candidate_link(record: dict[str, Any]) -> str:
    identifiers = record.get("identifiers", {})
    if identifiers.get("doi"):
        return f"https://doi.org/{identifiers['doi']}"
    if identifiers.get("arxiv"):
        return f"https://arxiv.org/abs/{identifiers['arxiv']}"
    for action in record.get("actions", []):
        if action.get("href"):
            return str(action["href"])
    return f"publications.html#{record.get('id', '')}"


def replace_first_number_in_stat(page_text: str, selector_attr: str, value: str, count: int) -> str:
    pattern = re.compile(
        rf'(<a\b[^>]*{re.escape(selector_attr)}="{re.escape(value)}"[^>]*>\s*<strong>)\d+(</strong>)',
        flags=re.DOTALL,
    )
    updated, replacements = pattern.subn(rf"\g<1>{count}\2", page_text, count=1)
    if replacements != 1:
        raise PublicationAssistantError(f"Could not update publication counter for {selector_attr}={value}")
    return updated


def replace_all_stat(page_text: str, count: int) -> str:
    pattern = re.compile(r'(<a\b[^>]*data-count-all="true"[^>]*>\s*<strong>)\d+(</strong>)', re.DOTALL)
    updated, replacements = pattern.subn(rf"\g<1>{count}\2", page_text, count=1)
    if replacements != 1:
        raise PublicationAssistantError("Could not update the all-publications counter")
    return updated


def replace_venue_stat(page_text: str, venue: str, count: int) -> str:
    pattern = re.compile(
        rf'(<button\b[^>]*data-venue="{re.escape(venue)}"[^>]*>\s*<strong>)\d+(</strong>)',
        re.DOTALL,
    )
    updated, replacements = pattern.subn(rf"\g<1>{count}\2", page_text, count=1)
    if replacements != 1:
        raise PublicationAssistantError(f"Could not update major-venue counter for {venue}")
    return updated


def replace_select_options(page_text: str, select_id: str, options_html: str) -> str:
    pattern = re.compile(
        rf'(<select\b[^>]*id="{re.escape(select_id)}"[^>]*>).*?(</select>)',
        flags=re.DOTALL,
    )
    updated, replacements = pattern.subn(rf"\1\n{options_html}\n          \2", page_text, count=1)
    if replacements != 1:
        raise PublicationAssistantError(f"Could not update #{select_id} options")
    return updated


def render_tag_options(data: dict[str, Any]) -> str:
    lines = ['            <option value="all">Add a tag</option>']
    for group in data.get("tagGroups", []):
        lines.append(f'            <optgroup label="{html.escape(group["label"], quote=True)}">')
        for option in group.get("options", []):
            lines.append(
                f'              <option value="{html.escape(option["value"], quote=True)}">'
                f'{html.escape(option["label"])}</option>'
            )
        lines.append("            </optgroup>")
    return "\n".join(lines)


def render_marker_options(data: dict[str, Any]) -> str:
    lines = ['            <option value="all">All markers</option>']
    for marker in data.get("markerTypes", []):
        lines.append(
            f'            <option value="{html.escape(marker["value"], quote=True)}">'
            f'{html.escape(marker["label"])}</option>'
        )
    return "\n".join(lines)


def replace_json_array(source: str, marker_start: int, property_name: str, value: list[dict[str, Any]]) -> str:
    property_index = source.index(f'"{property_name}"', marker_start)
    array_start = source.index("[", property_index)
    depth = 0
    in_string = False
    escaped = False
    for index in range(array_start, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                rendered = json.dumps(value, ensure_ascii=False, indent=2)
                rendered = rendered.replace("\n", "\n        ")
                return source[:array_start] + rendered + source[index + 1 :]
    raise PublicationAssistantError(f"Could not find the end of JSON array {property_name}")


def update_collection_schema(page_text: str, publications: list[dict[str, Any]]) -> str:
    schema_marker = page_text.index('"@type": "CollectionPage"')
    schema_end = page_text.index("</script>", schema_marker)
    schema = page_text[schema_marker:schema_end]
    schema, replacements = re.subn(
        r'("numberOfItems"\s*:\s*)\d+',
        rf"\g<1>{len(publications)}",
        schema,
        count=1,
    )
    if replacements != 1:
        raise PublicationAssistantError("Could not update ItemList numberOfItems")
    page_text = page_text[:schema_marker] + schema + page_text[schema_end:]
    items = [
        {
            "@type": "ListItem",
            "position": position,
            "name": record["title"],
            "url": f"{SITE_URL}/publications.html#{record['id']}",
        }
        for position, record in enumerate(publications[:5], start=1)
    ]
    return replace_json_array(page_text, schema_marker, "itemListElement", items)


def conference_venue_count(publications: Sequence[dict[str, Any]], venue: str) -> int:
    return sum(
        1
        for record in publications
        if record.get("type") == "conference paper"
        and venue.lower() in str(record.get("venue", "")).lower()
        and "workshop" not in str(record.get("venue", "")).lower()
        and "short version" not in str(record.get("venue", "")).lower()
    )


def generate_page(data: dict[str, Any], current_page: str) -> str:
    publications = sorted(data.get("publications", []), key=lambda record: int(record["number"]), reverse=True)
    page_text = current_page
    start, end, current_region = extract_publication_region(page_text)
    closing_indent = current_region[current_region.rfind("\n") + 1 :]
    rendered_cards = [render_publication(record, data) for record in publications]
    cards = "\n" + str(publications[0].get("sourceIndent", "      ")) + rendered_cards[0]
    if len(rendered_cards) > 1:
        cards += "\n" + "\n".join(
            str(record.get("sourceIndent", "")) + rendered
            for record, rendered in zip(publications[1:], rendered_cards[1:])
        )
    cards += "\n" + closing_indent
    page_text = page_text[:start] + cards + page_text[end:]

    type_counts = Counter(str(record.get("type", "")) for record in publications)
    page_text = replace_all_stat(page_text, len(publications))
    for publication_type in data.get("publicationTypes", []):
        page_text = replace_first_number_in_stat(
            page_text,
            "data-count-type",
            publication_type["value"],
            type_counts[publication_type["value"]],
        )
    for venue in data.get("majorVenues", []):
        page_text = replace_venue_stat(
            page_text,
            venue["name"],
            conference_venue_count(publications, venue["name"]),
        )
    page_text = replace_select_options(page_text, "publication-tag-filter", render_tag_options(data))
    page_text = replace_select_options(page_text, "publication-marker-filter", render_marker_options(data))
    page_text = re.sub(
        r'(<span\b[^>]*id="publication-count"[^>]*>)\d+(</span>)',
        rf"\g<1>{len(publications)}\2",
        page_text,
        count=1,
    )
    return update_collection_schema(page_text, publications)


def validate_data(data: dict[str, Any], *, require_approved: bool = False) -> list[str]:
    errors: list[str] = []
    if data.get("$schema") != "./publications.schema.json":
        errors.append("$schema must point to ./publications.schema.json")
    if not DATA_SCHEMA_FILE.is_file():
        errors.append("data/publications.schema.json is required")
    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if data.get("protectedFields") != PROTECTED_FIELDS:
        errors.append("protectedFields must keep the reviewed automation boundary")

    types = {item["value"] for item in data.get("publicationTypes", [])}
    tag_labels = tag_label_map(data)
    relation_types = relation_config_map(data)
    publications = data.get("publications", [])
    ids: set[str] = set()
    numbers: set[int] = set()
    identifier_owners: dict[tuple[str, str], str] = {}
    title_owners: dict[str, str] = {}
    previous_number: int | None = None
    for index, record in enumerate(publications, start=1):
        label = str(record.get("id") or f"record {index}")
        publication_id = str(record.get("id", ""))
        if not publication_id.startswith("pub-"):
            errors.append(f"{label}: id must start with pub-")
        if publication_id in ids:
            errors.append(f"{label}: duplicate id")
        ids.add(publication_id)

        number = record.get("number")
        if not isinstance(number, int) or number <= 0:
            errors.append(f"{label}: number must be a positive integer")
        else:
            if number in numbers:
                errors.append(f"{label}: duplicate number #{number}")
            numbers.add(number)
            if previous_number is not None and number >= previous_number:
                errors.append(f"{label}: publications must be sorted newest first by number")
            previous_number = number

        if record.get("type") not in types:
            errors.append(f"{label}: unknown publication type {record.get('type')!r}")
        if not normalize_space(str(record.get("title", ""))):
            errors.append(f"{label}: title is required")
        normalized_title = normalize_title(str(record.get("title", "")))
        if normalized_title in title_owners:
            errors.append(f"{label}: duplicate normalized title also used by {title_owners[normalized_title]}")
        elif normalized_title:
            title_owners[normalized_title] = label
        if not record.get("authors"):
            errors.append(f"{label}: at least one structured author is required")
        if not any(author.get("isMe") for author in record.get("authors", [])):
            errors.append(f"{label}: the target author must be marked with isMe=true")
        if len(str(record.get("abstract", "")).split()) < 25:
            errors.append(f"{label}: abstract must contain at least 25 words")
        if not record.get("tags"):
            errors.append(f"{label}: at least one topic tag is required")
        for tag in record.get("tags", []):
            if tag not in tag_labels:
                errors.append(f"{label}: unknown topic tag {tag!r}")
        aggregate_relations = record.get("authorRelations", [])
        if not isinstance(aggregate_relations, list):
            errors.append(f"{label}: authorRelations must be a list")
            aggregate_relations = []
        for relation in aggregate_relations:
            if relation not in relation_types:
                errors.append(f"{label}: unknown author relation {relation!r}")
        structured_relations: set[str] = set()
        for author in record.get("authors", []):
            markers = author.get("markers")
            relations = author.get("relations")
            if not isinstance(markers, list):
                errors.append(f"{label}: author {author.get('name')!r} markers must be a list")
                markers = []
            if not isinstance(relations, list):
                errors.append(f"{label}: author {author.get('name')!r} relations must be a list")
                relations = []
            if any(not isinstance(marker, str) or not marker for marker in markers):
                errors.append(f"{label}: author {author.get('name')!r} has an invalid contribution marker")
            for relation in relations:
                if relation not in relation_types:
                    errors.append(f"{label}: unknown author relation {relation!r}")
                structured_relations.add(str(relation))
        if structured_relations != set(aggregate_relations):
            errors.append(f"{label}: authorRelations must match the relations assigned to individual authors")
        if not record.get("actions"):
            errors.append(f"{label}: at least one publication action is required")
        title_href = str(record.get("titleLink", {}).get("href", ""))
        if not title_href:
            errors.append(f"{label}: titleLink.href is required")
        elif not valid_link_target(title_href):
            errors.append(f"{label}: titleLink.href is not a valid web or local-file target")
        for action_index, action in enumerate(record.get("actions", []), start=1):
            href = str(action.get("href", ""))
            if not href:
                errors.append(f"{label}: action {action_index} has no href")
            elif not valid_link_target(href):
                errors.append(f"{label}: action {action_index} has an invalid href")

        review = record.get("review", {})
        if review.get("status") not in REVIEW_STATUSES:
            errors.append(f"{label}: review.status must be approved or needs-review")
        if require_approved and review.get("status") != REVIEW_APPROVED:
            errors.append(f"{label}: human review is required before merge")

        identifiers = record.get("identifiers", {})
        for kind in ("doi", "arxiv", "openalex", "orcid"):
            value = normalize_space(str(identifiers.get(kind, "")))
            if not value:
                continue
            normalized = normalize_doi(value) if kind == "doi" else normalize_arxiv_id(value) if kind == "arxiv" else value.lower()
            key = (kind, normalized)
            if key in identifier_owners:
                errors.append(f"{label}: duplicate {kind} identifier also used by {identifier_owners[key]}")
            identifier_owners[key] = label
        if not isinstance(record.get("provenance"), dict) or not record.get("provenance"):
            errors.append(f"{label}: provenance is required")

    if len(publications) != len(ids):
        errors.append("publication ids must be unique")
    return errors


def valid_link_target(value: str) -> bool:
    """Accept web URLs and safe repository-relative publication assets."""
    value = value.strip()
    if not value or value.startswith(("#", "/", "../")):
        return False
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme:
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    return not any(part in {"", ".", ".."} for part in Path(parsed.path).parts)


def check_generated_page(data: dict[str, Any]) -> tuple[bool, str]:
    current = PUBLICATIONS_PAGE.read_text(encoding="utf-8")
    generated = generate_page(data, current)
    if generated == current:
        return True, ""
    diff = "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile="publications.html",
            tofile="generated publications.html",
            n=2,
        )
    )
    return False, diff


def cached_request(
    url: str,
    *,
    accept: str,
    cache_name: str,
    cache_hours: int = 12,
    headers: dict[str, str] | None = None,
) -> bytes:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / cache_name
    if cache_path.exists() and time.time() - cache_path.stat().st_mtime < cache_hours * 3600:
        return cache_path.read_bytes()
    request_headers = {
        "Accept": accept,
        "User-Agent": f"EduardGorbunovPublicationAssistant/1.0 (mailto:{DEFAULT_CONTACT_EMAIL})",
    }
    request_headers.update(headers or {})
    request = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            body = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        if cache_path.exists():
            return cache_path.read_bytes()
        raise PublicationAssistantError(f"Could not retrieve {url}: {exc}") from exc
    cache_path.write_bytes(body)
    return body


def inverted_abstract_to_text(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, locations in index.items():
        for location in locations:
            positions.append((int(location), word))
    return normalize_space(" ".join(word for _, word in sorted(positions)))


def discover_arxiv(author: dict[str, Any]) -> list[Candidate]:
    query = author.get("arxivQuery") or ARXIV_AUTHOR_QUERY
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": 200,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    body = cached_request(
        f"https://export.arxiv.org/api/query?{params}",
        accept="application/atom+xml",
        cache_name="arxiv.xml",
    )
    root = ElementTree.fromstring(body)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    candidates: list[Candidate] = []
    for entry in root.findall("atom:entry", ns):
        title = normalize_space(entry.findtext("atom:title", default="", namespaces=ns))
        authors = [
            normalize_space(author_node.findtext("atom:name", default="", namespaces=ns))
            for author_node in entry.findall("atom:author", ns)
        ]
        if not title or not candidate_has_target_author(authors):
            continue
        entry_url = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id = normalize_arxiv_id(entry_url)
        links = {"arxiv": f"https://arxiv.org/abs/{arxiv_id}", "pdf": f"https://arxiv.org/pdf/{arxiv_id}"}
        doi = normalize_doi(entry.findtext("arxiv:doi", default="", namespaces=ns))
        if doi:
            links["doi"] = f"https://doi.org/{doi}"
        candidates.append(
            Candidate(
                title=title,
                authors=authors,
                abstract=normalize_space(entry.findtext("atom:summary", default="", namespaces=ns)),
                published_date=entry.findtext("atom:published", default="", namespaces=ns)[:10],
                publication_type="arXiv preprint",
                venue="arXiv preprint",
                doi=doi,
                arxiv=arxiv_id,
                links=links,
                sources={
                    "record": entry_url,
                    "title": entry_url,
                    "authors": entry_url,
                    "abstract": entry_url,
                    "date": entry_url,
                },
            )
        )
    return candidates


def crossref_publication_type(crossref_type: str) -> str:
    if crossref_type in {"journal-article", "posted-content", "journal"}:
        return "journal paper"
    if crossref_type in {"proceedings-article", "proceedings", "book-chapter"}:
        return "conference paper"
    if crossref_type in {"reference-entry", "reference-book"}:
        return "living reference work entry"
    return "journal paper"


def crossref_date(item: dict[str, Any]) -> str:
    for key in ("published-online", "published-print", "published", "issued", "created"):
        parts = item.get(key, {}).get("date-parts", [])
        if not parts:
            continue
        values = parts[0]
        if values:
            try:
                year = int(values[0])
                month = int(values[1]) if len(values) > 1 and values[1] is not None else 1
                day = int(values[2]) if len(values) > 2 and values[2] is not None else 1
                return date(year, month, day).isoformat()
            except (TypeError, ValueError):
                continue
    return ""


def discover_crossref(author: dict[str, Any]) -> list[Candidate]:
    params = urllib.parse.urlencode(
        {
            "query.author": author.get("name") or TARGET_AUTHOR,
            "rows": 250,
            "mailto": author.get("email") or DEFAULT_CONTACT_EMAIL,
            "select": "DOI,title,author,abstract,published,published-online,published-print,issued,created,type,container-title,URL,link",
        }
    )
    body = cached_request(
        f"https://api.crossref.org/works?{params}",
        accept="application/json",
        cache_name="crossref.json",
    )
    payload = json.loads(body)
    candidates: list[Candidate] = []
    for item in payload.get("message", {}).get("items", []):
        authors = [
            normalize_space(" ".join(part for part in (person.get("given", ""), person.get("family", "")) if part))
            for person in item.get("author", [])
        ]
        # Crossref's author search is intentionally broad and otherwise returns
        # many unrelated records attributed only to "E. Gorbunov".
        if not has_exact_target_author(authors):
            continue
        title = normalize_space(" ".join(item.get("title", [])))
        doi = normalize_doi(item.get("DOI", ""))
        if not title or not doi:
            continue
        venue = normalize_space("; ".join(item.get("container-title", [])))
        publication_type = crossref_publication_type(item.get("type", ""))
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf" and link.get("URL"):
                pdf_url = link["URL"]
                break
        record_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
        links = {"doi": f"https://doi.org/{doi}"}
        if pdf_url:
            links["pdf"] = pdf_url
        candidates.append(
            Candidate(
                title=title,
                authors=authors,
                abstract=strip_html(item.get("abstract", "")),
                published_date=crossref_date(item),
                publication_type=publication_type,
                venue=venue,
                doi=doi,
                links=links,
                sources={
                    "record": record_url,
                    "title": record_url,
                    "authors": record_url,
                    "abstract": record_url if item.get("abstract") else "",
                    "venue": record_url,
                    "date": record_url,
                },
            )
        )
    return candidates


def discover_openalex(author: dict[str, Any]) -> list[Candidate]:
    author_id = str(author.get("openAlexAuthorId", "")).strip()
    if not author_id:
        return []
    author_id = author_id.rsplit("/", 1)[-1]
    query = {
        "filter": f"authorships.author.id:{author_id}",
        "per-page": 200,
        "select": "id,doi,title,publication_date,type,authorships,primary_location,abstract_inverted_index,ids",
    }
    api_key = os.environ.get("OPENALEX_API_KEY", "").strip()
    if api_key:
        query["api_key"] = api_key
    params = urllib.parse.urlencode(query)
    body = cached_request(
        f"https://api.openalex.org/works?{params}",
        accept="application/json",
        cache_name="openalex.json",
    )
    payload = json.loads(body)
    candidates: list[Candidate] = []
    for item in payload.get("results", []):
        authors = [
            normalize_space(authorship.get("author", {}).get("display_name", ""))
            for authorship in item.get("authorships", [])
        ]
        if not candidate_has_target_author(authors):
            continue
        location = item.get("primary_location") or {}
        source = location.get("source") or {}
        venue = normalize_space(source.get("display_name", ""))
        doi = normalize_doi(item.get("doi") or "")
        arxiv_doi_id = arxiv_id_from_doi(doi)
        if arxiv_doi_id:
            doi = ""
        arxiv_id = ""
        for identifier in (item.get("ids") or {}).values():
            if "arxiv.org" in str(identifier):
                arxiv_id = normalize_arxiv_id(str(identifier))
                break
        arxiv_id = arxiv_id or arxiv_doi_id
        openalex_id = str(item.get("id", "")).rsplit("/", 1)[-1]
        links: dict[str, str] = {"openalex": str(item.get("id", ""))}
        if doi:
            links["doi"] = f"https://doi.org/{doi}"
        if arxiv_id:
            links["arxiv"] = f"https://arxiv.org/abs/{arxiv_id}"
            links["pdf"] = f"https://arxiv.org/pdf/{arxiv_id}"
        if location.get("landing_page_url"):
            links["venue"] = location["landing_page_url"]
        record_url = str(item.get("id", ""))
        publication_type = openalex_publication_type(str(item.get("type", "")))
        if arxiv_id and ("arxiv" in venue.lower() or arxiv_doi_id):
            publication_type = "arXiv preprint"
            venue = "arXiv preprint"
        candidates.append(
            Candidate(
                title=normalize_space(item.get("title", "")),
                authors=authors,
                abstract=inverted_abstract_to_text(item.get("abstract_inverted_index")),
                published_date=str(item.get("publication_date", "")),
                publication_type=publication_type,
                venue=venue,
                doi=doi,
                arxiv=arxiv_id,
                openalex=openalex_id,
                links=links,
                sources={
                    "record": record_url,
                    "title": record_url,
                    "authors": record_url,
                    "abstract": record_url if item.get("abstract_inverted_index") else "",
                    "venue": record_url,
                    "date": record_url,
                },
            )
        )
    return candidates


def openalex_publication_type(value: str) -> str:
    if value in {"article", "review", "editorial"}:
        return "journal paper"
    if value in {"proceedings-article", "book-chapter"}:
        return "conference paper"
    if value in {"reference-entry", "book"}:
        return "living reference work entry"
    return "arXiv preprint" if value == "preprint" else "journal paper"


def discover_orcid(author: dict[str, Any]) -> list[Candidate]:
    orcid = str(author.get("orcid", "")).strip()
    if not orcid:
        return []
    token = os.environ.get("ORCID_ACCESS_TOKEN", "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    body = cached_request(
        f"https://pub.orcid.org/v3.0/{urllib.parse.quote(orcid, safe='-')}/works",
        accept="application/vnd.orcid+json",
        cache_name="orcid.json",
        headers=headers,
    )
    payload = json.loads(body)
    candidates: list[Candidate] = []
    for group in payload.get("group", []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        summary = summaries[0]
        title = normalize_space(summary.get("title", {}).get("title", {}).get("value", ""))
        if not title:
            continue
        external_ids = summary.get("external-ids", {}).get("external-id", [])
        doi = ""
        arxiv_id = ""
        for external in external_ids:
            id_type = str(external.get("external-id-type", "")).lower()
            value = str(external.get("external-id-value", ""))
            if id_type == "doi":
                doi = normalize_doi(value)
            elif id_type == "arxiv":
                arxiv_id = normalize_arxiv_id(value)
        publication_date = summary.get("publication-date") or {}
        year = (publication_date.get("year") or {}).get("value", "")
        month = (publication_date.get("month") or {}).get("value", "01")
        day = (publication_date.get("day") or {}).get("value", "01")
        published_date = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}" if year else ""
        put_code = str(summary.get("put-code", ""))
        record_url = f"https://orcid.org/{orcid}/work/{put_code}"
        links: dict[str, str] = {"orcid": record_url}
        if doi:
            links["doi"] = f"https://doi.org/{doi}"
        if arxiv_id:
            links["arxiv"] = f"https://arxiv.org/abs/{arxiv_id}"
        candidates.append(
            Candidate(
                title=title,
                authors=[TARGET_AUTHOR],
                published_date=published_date,
                publication_type=orcid_publication_type(summary.get("type", "")),
                venue=normalize_space((summary.get("journal-title") or {}).get("value", "")),
                doi=doi,
                arxiv=arxiv_id,
                orcid_put_code=put_code,
                links=links,
                sources={"record": record_url, "title": record_url, "date": record_url, "venue": record_url},
            )
        )
    return candidates


def orcid_publication_type(value: str) -> str:
    value = str(value).lower()
    if "conference" in value:
        return "conference paper"
    if "journal" in value or "article" in value:
        return "journal paper"
    return "arXiv preprint"


def candidate_has_target_author(authors: Sequence[str]) -> bool:
    for author in authors:
        normalized = normalize_person(author)
        parts = normalized.split()
        if "gorbunov" not in parts:
            continue
        given = [part for part in parts if part != "gorbunov"]
        if "eduard" in given or given == ["e"]:
            return True
    return False


def has_exact_target_author(authors: Sequence[str]) -> bool:
    """Require the full given name before creating a brand-new publication."""
    return any(
        "eduard" in normalize_person(author).split() and "gorbunov" in normalize_person(author).split()
        for author in authors
    )


def author_overlap(left: Sequence[str], right: Sequence[str]) -> float:
    left_names = {normalize_person(name) for name in left if normalize_person(name)}
    right_names = {normalize_person(name) for name in right if normalize_person(name)}
    if not left_names or not right_names:
        return 0.0
    return len(left_names & right_names) / max(1, min(len(left_names), len(right_names)))


def merge_candidates(candidates: Sequence[Candidate]) -> list[Candidate]:
    grouped: dict[str, Candidate] = {}
    for candidate in candidates:
        title_key = normalize_title(candidate.title)
        matching_key = ""
        for key, existing in grouped.items():
            if candidate.doi and existing.doi and normalize_doi(candidate.doi) == normalize_doi(existing.doi):
                matching_key = key
                break
            if candidate.arxiv and existing.arxiv and normalize_arxiv_id(candidate.arxiv) == normalize_arxiv_id(existing.arxiv):
                matching_key = key
                break
            if normalize_title(existing.title) == title_key:
                matching_key = key
                break
        if not matching_key:
            grouped[candidate.key()] = copy.deepcopy(candidate)
            continue
        existing = grouped[matching_key]
        existing.doi = existing.doi or candidate.doi
        existing.arxiv = existing.arxiv or candidate.arxiv
        existing.openalex = existing.openalex or candidate.openalex
        existing.orcid_put_code = existing.orcid_put_code or candidate.orcid_put_code
        if not existing.abstract or len(candidate.abstract) > len(existing.abstract):
            existing.abstract = candidate.abstract
        if candidate.publication_type != "arXiv preprint":
            existing.publication_type = candidate.publication_type
            existing.venue = candidate.venue or existing.venue
            existing.published_date = candidate.published_date or existing.published_date
        elif not existing.published_date:
            existing.published_date = candidate.published_date
        if len(candidate.authors) > len(existing.authors):
            existing.authors = candidate.authors
        existing.links.update({key: value for key, value in candidate.links.items() if value})
        existing.sources.update({key: value for key, value in candidate.sources.items() if value})
    return sorted(grouped.values(), key=lambda candidate: candidate.published_date or "", reverse=True)


def record_author_names(record: dict[str, Any]) -> list[str]:
    return [str(author.get("name", "")) for author in record.get("authors", [])]


def find_candidate_matches(candidate: Candidate, publications: Sequence[dict[str, Any]]) -> list[tuple[dict[str, Any], str, float]]:
    exact: list[tuple[dict[str, Any], str, float]] = []
    doi = normalize_doi(candidate.doi)
    arxiv_id = normalize_arxiv_id(candidate.arxiv)
    candidate_title = normalize_title(candidate.title)
    fuzzy: list[tuple[dict[str, Any], str, float]] = []
    for record in publications:
        identifiers = record.get("identifiers", {})
        if doi and normalize_doi(str(identifiers.get("doi", ""))) == doi:
            exact.append((record, "DOI", 1.0))
            continue
        if arxiv_id and normalize_arxiv_id(str(identifiers.get("arxiv", ""))) == arxiv_id:
            exact.append((record, "arXiv ID", 1.0))
            continue
        record_title = normalize_title(str(record.get("title", "")))
        overlap = author_overlap(candidate.authors, record_author_names(record))
        if record_title == candidate_title and overlap >= 0.5:
            exact.append((record, "normalized title and authors", 0.99))
            continue
        title_score = difflib.SequenceMatcher(None, candidate_title, record_title).ratio()
        if title_score >= 0.88 and overlap >= 0.5:
            fuzzy.append((record, "similar title and authors", title_score * 0.8 + overlap * 0.2))
    return exact or sorted(fuzzy, key=lambda item: item[2], reverse=True)


def classify_candidate(candidate: Candidate, publications: Sequence[dict[str, Any]]) -> dict[str, Any]:
    matches = find_candidate_matches(candidate, publications)
    if len(matches) > 1 and matches[0][2] == matches[1][2]:
        return {
            "classification": "conflict",
            "candidate": candidate,
            "matches": matches,
            "reason": "The candidate matches more than one current publication with equal confidence.",
        }
    if not matches:
        missing = new_candidate_requirements(candidate)
        if missing:
            return {
                "classification": "conflict",
                "candidate": candidate,
                "matches": [],
                "reason": "A possible new paper was found, but a valid card cannot be generated yet: "
                + "; ".join(missing)
                + ".",
            }
        return {
            "classification": "new paper",
            "candidate": candidate,
            "matches": [],
            "reason": "No DOI, arXiv ID, or sufficiently similar title-and-author match was found.",
        }
    record, reason, score = matches[0]
    if score < 0.94:
        return {
            "classification": "possible duplicate",
            "candidate": candidate,
            "matches": matches[:3],
            "reason": f"A similar record was found by {reason}, but confidence is only {score:.0%}.",
        }
    identifiers = record.get("identifiers", {})
    if candidate.doi and not identifiers.get("doi") and candidate.publication_type != "arXiv preprint":
        classification = "published version found"
        explanation = "A DOI-backed published record matches the current publication."
    else:
        proposed = proposed_automatic_changes(record, candidate)
        classification = "metadata update" if proposed else "metadata update"
        explanation = "The record matches; retrieved metadata can be compared with the current entry."
    return {
        "classification": classification,
        "candidate": candidate,
        "matches": matches[:3],
        "matchedRecord": record,
        "reason": explanation,
        "proposedChanges": proposed_automatic_changes(record, candidate),
    }


def new_candidate_requirements(candidate: Candidate) -> list[str]:
    """Return missing fields that require a human before a new card is created."""
    missing: list[str] = []
    if not normalize_space(candidate.title):
        missing.append("title is missing")
    if not candidate.authors or not has_exact_target_author(candidate.authors):
        missing.append("the complete author list is missing or does not include Eduard Gorbunov")
    if len(normalize_space(candidate.abstract).split()) < 25:
        missing.append("a substantive abstract is missing")
    if not candidate_title_link(candidate).get("href") or not candidate_actions(candidate):
        missing.append("a stable paper link is missing")
    if candidate.publication_type != "arXiv preprint" and not normalize_space(candidate.venue):
        missing.append("the publication venue is missing")
    return missing


def iso_date_label(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = date.fromisoformat(value[:10])
        return f"{parsed:%B} {parsed.year}"
    except ValueError:
        return value[:10]


def make_action(label: str, href: str, title: str, *, content_type: str = "") -> dict[str, str]:
    return {
        "label": label,
        "href": href,
        "type": content_type,
        "target": "_blank",
        "rel": "noopener noreferrer",
        "ariaLabel": f"Open {label} for {title}",
        "class": "",
    }


def candidate_actions(candidate: Candidate) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if candidate.links.get("pdf"):
        actions.append(make_action("PDF", candidate.links["pdf"], candidate.title, content_type="application/pdf"))
    if candidate.arxiv:
        actions.append(make_action("arXiv", f"https://arxiv.org/abs/{candidate.arxiv}", candidate.title))
    if candidate.doi:
        actions.append(make_action("DOI", f"https://doi.org/{candidate.doi}", candidate.title))
    if candidate.links.get("venue"):
        actions.append(make_action("Venue", candidate.links["venue"], candidate.title))
    if candidate.openalex:
        actions.append(make_action("OpenAlex", f"https://openalex.org/{candidate.openalex}", candidate.title))
    if not actions:
        href = next((value for value in candidate.links.values() if value), "")
        if href:
            actions.append(make_action("Paper page", href, candidate.title))
    return actions


def candidate_title_link(candidate: Candidate) -> dict[str, str]:
    if candidate.doi:
        href = f"https://doi.org/{candidate.doi}"
        label = "published paper"
    elif candidate.arxiv:
        href = f"https://arxiv.org/abs/{candidate.arxiv}"
        label = "arXiv page"
    else:
        href = next((value for value in candidate.links.values() if value), "")
        label = "paper page"
    return {
        "label": candidate.title,
        "href": href,
        "type": "",
        "target": "_blank",
        "rel": "noopener noreferrer",
        "ariaLabel": f"Open {label} for {candidate.title}",
        "class": "",
    }


def proposed_automatic_changes(record: dict[str, Any], candidate: Candidate) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    current_identifiers = copy.deepcopy(record.get("identifiers", {}))
    proposed_identifiers = copy.deepcopy(current_identifiers)
    for key, value in {
        "doi": candidate.doi,
        "arxiv": candidate.arxiv,
    }.items():
        if value and not proposed_identifiers.get(key):
            proposed_identifiers[key] = value
    if proposed_identifiers != current_identifiers:
        changes["identifiers"] = proposed_identifiers
    if candidate.publication_type != "arXiv preprint" and record.get("type") == "arXiv preprint":
        changes["type"] = candidate.publication_type
        if candidate.venue:
            changes["venue"] = candidate.venue
            changes["venueHtml"] = html.escape(candidate.venue)
            changes["venueClasses"] = []
        if candidate.published_date:
            changes["onlineDate"] = candidate.published_date
            changes["dateLabel"] = iso_date_label(candidate.published_date)
        changes["titleLink"] = candidate_title_link(candidate)
        actions = candidate_actions(candidate)
        known_hrefs = {action.get("href") for action in actions}
        for action in record.get("actions", []):
            if action.get("href") not in known_hrefs:
                actions.append(action)
                known_hrefs.add(action.get("href"))
        if actions:
            changes["actions"] = actions
    elif candidate.doi and not current_identifiers.get("doi"):
        current_actions = copy.deepcopy(record.get("actions", []))
        if not any(
            normalize_doi(str(action.get("href", ""))) == normalize_doi(candidate.doi)
            for action in current_actions
        ):
            current_actions.append(make_action("DOI", f"https://doi.org/{candidate.doi}", candidate.title))
            changes["actions"] = current_actions
    if candidate.abstract and not record.get("abstract"):
        changes["abstract"] = candidate.abstract
        changes["abstractHtml"] = html.escape(candidate.abstract)
    return changes


TAG_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("stochastic-optimization", ("stochastic", "sgd", "gradient noise")),
    ("stochastic-gradient-descent", ("sgd", "stochastic gradient")),
    ("convex-optimization", ("convex", "conditional gradient")),
    ("min-max-variational-inequalities", ("min-max", "minimax", "variational inequal", "game")),
    ("last-iterate-convergence", ("last iterate", "last-iterate")),
    ("probability-and-concentration", ("concentration", "probability", "martingale")),
    ("distributed-learning", ("distributed", "decentralized", "federated", "client")),
    ("federated-learning", ("federated", "client")),
    ("communication-compression", ("compression", "compressed", "quantization", "communication")),
    ("decentralized-optimization", ("decentralized", "network")),
    ("local-steps", ("local sgd", "local step", "local update")),
    ("random-reshuffling", ("random reshuffl", "without replacement")),
    ("low-rank-fine-tuning", ("low-rank", "lora", "fine-tuning")),
    ("high-probability-bounds", ("high-probability", "high probability")),
    ("heavy-tailed-noise", ("heavy-tailed", "heavy tailed")),
    ("gradient-clipping", ("clipping", "clipped")),
    ("generalized-smoothness", ("generalized smooth", "l_0", "l0,l1", "l0 l1")),
    ("byzantine-robustness", ("byzantine", "malicious", "adversarial client")),
    ("differential-privacy", ("differential privacy", "private federated", "dp-sgd")),
    ("adaptive-methods", ("adaptive", "adagrad", "adam", "normalization")),
    ("variance-reduction", ("variance reduction", "variance-reduced", "svrg", "saga")),
    ("conditional-gradient-lmo-methods", ("conditional gradient", "linear minimization oracle", "lmo")),
    ("derivative-free-zeroth-order-methods", ("derivative-free", "zeroth-order", "zero-order")),
    ("higher-order-methods", ("second-order", "higher-order", "tensor method", "hessian", "jacobian")),
    ("coordinate-descent-type-methods", ("coordinate descent", "coordinate method")),
    ("inexact-oracles", ("inexact oracle", "inexactness", "approximate oracle")),
]


def infer_tags(candidate: Candidate) -> list[str]:
    haystack = normalize_space(f"{candidate.title} {candidate.abstract}").lower()
    tags = [tag for tag, terms in TAG_RULES if any(non_negated_term(haystack, term) for term in terms)]
    if not tags:
        tags.append("stochastic-optimization")
    return tags


def non_negated_term(haystack: str, term: str) -> bool:
    """Avoid proposing a tag when the abstract explicitly says it is absent."""
    start = 0
    while True:
        index = haystack.find(term, start)
        if index < 0:
            return False
        context = haystack[max(0, index - 70) : index]
        context = re.split(r"[.;:]", context)[-1]
        if not re.search(r"\b(?:without|not|no|does not|do not|doesn't|don't)\b", context):
            return True
        start = index + len(term)


def unique_publication_id(title: str, existing_ids: set[str]) -> str:
    base = f"pub-{slugify(title)}"
    publication_id = base
    suffix = 2
    while publication_id in existing_ids:
        publication_id = f"{base}-{suffix}"
        suffix += 1
    return publication_id


def new_record_from_candidate(candidate: Candidate, data: dict[str, Any]) -> dict[str, Any]:
    publications = data.get("publications", [])
    number = max((int(record.get("number", 0)) for record in publications), default=0) + 1
    publication_id = unique_publication_id(candidate.title, {str(record.get("id", "")) for record in publications})
    title_link = candidate_title_link(candidate)
    venue = candidate.venue or ("arXiv preprint" if candidate.publication_type == "arXiv preprint" else "Publication venue to review")
    authors = [
        {
            "name": name,
            "isMe": has_exact_target_author([name]),
            "markers": [],
            "relations": [],
        }
        for name in candidate.authors
    ]
    identifiers = {
        "doi": candidate.doi,
        "arxiv": candidate.arxiv,
        "openalex": candidate.openalex,
        "orcid": candidate.orcid_put_code,
    }
    return {
        "id": publication_id,
        "number": number,
        "type": candidate.publication_type,
        "dateLabel": iso_date_label(candidate.published_date),
        "onlineDate": candidate.published_date,
        "title": candidate.title,
        "titleHtml": "",
        "titleLink": title_link,
        "authors": authors,
        "authorsHtml": "",
        "venue": venue,
        "venueHtml": "",
        "venueClasses": ["eg-publication-venue-muted"] if candidate.publication_type == "arXiv preprint" else [],
        "abstract": candidate.abstract,
        "abstractHtml": "",
        "noteHtml": "",
        "tags": infer_tags(candidate),
        "tagLabels": [],
        "actions": candidate_actions(candidate),
        "identifiers": identifiers,
        "authorRelations": [],
        "contributionNotes": [],
        "distinctions": [],
        "representativeSelections": [],
        "news": {"enabled": False, "customText": ""},
        "displayOverrides": [],
        "review": {
            "status": REVIEW_NEEDED,
            "lastReviewed": "",
            "source": "publication assistant discovery",
        },
        "provenance": copy.deepcopy(candidate.sources),
        "pendingChanges": {},
        "sourceHtmlTags": [],
    }


def apply_proposals(data: dict[str, Any], proposals: Sequence[dict[str, Any]]) -> list[str]:
    changed_ids: list[str] = []
    publications = data.get("publications", [])
    for proposal in proposals:
        classification = proposal["classification"]
        candidate: Candidate = proposal["candidate"]
        if classification == "new paper":
            record = new_record_from_candidate(candidate, data)
            publications.append(record)
            changed_ids.append(record["id"])
        elif classification in {"published version found", "metadata update"}:
            record = proposal.get("matchedRecord")
            changes = proposal.get("proposedChanges", {})
            if record is not None and changes:
                record["pendingChanges"] = changes
                record["review"]["status"] = REVIEW_NEEDED
                record["review"]["source"] = "publication assistant proposal"
                record.setdefault("provenance", {}).update(candidate.sources)
                changed_ids.append(record["id"])
    publications.sort(key=lambda record: int(record["number"]), reverse=True)
    return changed_ids


def load_fixture_candidates(path: Path) -> list[Candidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Candidate(**item) for item in payload]


def collect_candidates(data: dict[str, Any], fixture: Path | None = None) -> tuple[list[Candidate], list[str]]:
    if fixture:
        return load_fixture_candidates(fixture), []
    author = data.get("author", {})
    sources = [
        ("arXiv", discover_arxiv),
        ("Crossref", discover_crossref),
        ("OpenAlex", discover_openalex),
        ("ORCID", discover_orcid),
    ]
    candidates: list[Candidate] = []
    errors: list[str] = []
    for name, discoverer in sources:
        try:
            candidates.extend(discoverer(author))
        except (
            PublicationAssistantError,
            json.JSONDecodeError,
            ElementTree.ParseError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            errors.append(f"{name}: {exc}")
    return merge_candidates(candidates), errors


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def proposal_report(data: dict[str, Any], proposals: Sequence[dict[str, Any]], source_errors: Sequence[str]) -> str:
    counts = Counter(proposal["classification"] for proposal in proposals)
    lines = [
        "# Publication update review",
        "",
        f"Generated: {utc_today()}",
        "",
        "This report is a proposal, not a publication decision. No change reaches the live site until the pull request is reviewed and merged.",
        "",
        "## Summary",
        "",
    ]
    for classification in DISCOVERY_CLASSIFICATIONS:
        lines.append(f"- **{classification.title()}:** {counts[classification]}")
    lines.extend(
        [
            "",
            "## Protected information",
            "",
            "The assistant does not silently change topic tags, mentoring markers, contribution or senior-authorship notes, distinctions, representative-paper selections, news wording, or removals.",
            "",
            f"[Compare with Google Scholar manually]({data.get('author', {}).get('googleScholar', GOOGLE_SCHOLAR_URL)})",
            "",
        ]
    )
    if source_errors:
        lines.extend(["## Source warnings", ""])
        lines.extend(f"- {error}" for error in source_errors)
        lines.append("")
    lines.extend(["## Proposed records", ""])
    if not proposals:
        lines.append("No candidate records were returned.")
        lines.append("")
    for index, proposal in enumerate(proposals, start=1):
        candidate: Candidate = proposal["candidate"]
        lines.extend(
            [
                f"### {index}. {candidate.title}",
                "",
                f"- **Classification:** {proposal['classification']}",
                f"- **Reason:** {proposal['reason']}",
                f"- **Authors:** {', '.join(candidate.authors)}",
                f"- **Date:** {candidate.published_date or 'not supplied'}",
                f"- **Type / venue:** {candidate.publication_type} / {candidate.venue or 'not supplied'}",
                f"- **DOI:** {candidate.doi or 'not supplied'}",
                f"- **arXiv:** {candidate.arxiv or 'not supplied'}",
            ]
        )
        if proposal.get("matches"):
            lines.append(
                "- **Current match:** "
                + ", ".join(f"{match[0]['id']} ({match[1]}, {match[2]:.0%})" for match in proposal["matches"])
            )
        changes = proposal.get("proposedChanges") or {}
        if changes:
            lines.append(f"- **Pending fields:** {', '.join(sorted(changes))}")
        sources = sorted({value for value in candidate.sources.values() if value})
        if sources:
            lines.append("- **Sources:** " + ", ".join(f"[{index + 1}]({url})" for index, url in enumerate(sources)))
        lines.append("")
    lines.extend(
        [
            "## Review commands",
            "",
            "After correcting the structured data if needed, approve records explicitly:",
            "",
            "```bash",
            "python3 scripts/publication_assistant.py approve --id <publication-id> --apply-pending",
            "python3 scripts/publication_assistant.py generate",
            "python3 scripts/publication_assistant.py validate --require-approved",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def news_draft(proposals: Sequence[dict[str, Any]]) -> str:
    new_papers = [proposal["candidate"] for proposal in proposals if proposal["classification"] == "new paper"]
    lines = [
        "# Optional publication news draft",
        "",
        "This file is intentionally not inserted into the website. News wording remains a manual decision.",
        "",
    ]
    if not new_papers:
        lines.append("No new-paper news draft was generated.")
        lines.append("")
        return "\n".join(lines)
    for candidate in new_papers:
        link = candidate_title_link(candidate).get("href", "")
        lines.extend(
            [
                f"## New preprint: {candidate.title}",
                "",
                f"A new preprint, [{candidate.title}]({link}), is now available online.",
                "",
            ]
        )
    return "\n".join(lines)


def apply_pending_changes(record: dict[str, Any]) -> None:
    pending = copy.deepcopy(record.get("pendingChanges", {}))
    for protected in PROTECTED_FIELDS:
        pending.pop(protected, None)
    for key, value in pending.items():
        record[key] = value
    record["pendingChanges"] = {}


def command_bootstrap(args: argparse.Namespace) -> int:
    if DATA_FILE.exists() and not args.overwrite:
        raise PublicationAssistantError(
            f"{DATA_FILE.relative_to(ROOT)} already exists; use --overwrite only for an intentional re-import."
        )
    data = bootstrap_data(PUBLICATIONS_PAGE.read_text(encoding="utf-8"))
    errors = validate_data(data)
    if errors:
        raise PublicationAssistantError("The imported publication data is invalid:\n- " + "\n- ".join(errors))
    write_json(DATA_FILE, data)
    print(f"Imported {len(data['publications'])} publications into {DATA_FILE.relative_to(ROOT)}.")
    return 0


def command_generate(args: argparse.Namespace) -> int:
    data = read_json(DATA_FILE)
    errors = validate_data(data)
    if errors:
        raise PublicationAssistantError("Publication data validation failed:\n- " + "\n- ".join(errors))
    current = PUBLICATIONS_PAGE.read_text(encoding="utf-8")
    generated = generate_page(data, current)
    if args.check:
        if generated != current:
            print("publications.html is not synchronized with data/publications.json.", file=sys.stderr)
            diff = "".join(
                difflib.unified_diff(
                    current.splitlines(keepends=True),
                    generated.splitlines(keepends=True),
                    fromfile="publications.html",
                    tofile="generated publications.html",
                    n=2,
                )
            )
            print(diff[:12000], file=sys.stderr)
            return 1
        print("Publication rendering is deterministic and current.")
        return 0
    PUBLICATIONS_PAGE.write_text(generated, encoding="utf-8")
    print(f"Generated publications.html from {DATA_FILE.relative_to(ROOT)}.")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    data = read_json(DATA_FILE)
    errors = validate_data(data, require_approved=args.require_approved)
    if errors:
        print("Publication data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.generated:
        matches, diff = check_generated_page(data)
        if not matches:
            print("publications.html differs from the deterministic rendering.", file=sys.stderr)
            print(diff[:12000], file=sys.stderr)
            return 1
    print(f"Validated {len(data.get('publications', []))} publication records.")
    return 0


def command_discover(args: argparse.Namespace) -> int:
    data = read_json(DATA_FILE)
    candidates, source_errors = collect_candidates(data, args.fixture)
    proposals = [classify_candidate(candidate, data.get("publications", [])) for candidate in candidates]
    if args.only_changes:
        proposals = [
            proposal
            for proposal in proposals
            if proposal["classification"] != "metadata update" or proposal.get("proposedChanges")
        ]
    changed_ids: list[str] = []
    if args.apply:
        changed_ids = apply_proposals(data, proposals)
        if changed_ids:
            write_json(DATA_FILE, data)
            current = PUBLICATIONS_PAGE.read_text(encoding="utf-8")
            PUBLICATIONS_PAGE.write_text(generate_page(data, current), encoding="utf-8")
    AUTOMATION_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_REPORT.write_text(proposal_report(data, proposals, source_errors), encoding="utf-8")
    NEWS_DRAFT.write_text(news_draft(proposals), encoding="utf-8")
    write_json(
        CHANGED_PUBLICATIONS,
        {
            "generatedAt": utc_today(),
            "publicationIds": changed_ids,
            "proposalCount": len(proposals),
            "sourceErrors": source_errors,
        },
    )
    counts = Counter(proposal["classification"] for proposal in proposals)
    print(f"Reviewed {len(candidates)} discovered records; prepared {len(proposals)} proposals.")
    for classification in DISCOVERY_CLASSIFICATIONS:
        if counts[classification]:
            print(f"- {classification}: {counts[classification]}")
    if source_errors:
        print(f"- source warnings: {len(source_errors)}")
    if args.apply:
        print(f"Applied {len(changed_ids)} reviewable data changes; human approval is still required.")
    return 0


def command_approve(args: argparse.Namespace) -> int:
    data = read_json(DATA_FILE)
    requested = set(args.id)
    if "all" in requested:
        requested = {str(record.get("id", "")) for record in data.get("publications", []) if record.get("review", {}).get("status") == REVIEW_NEEDED}
    approved: list[str] = []
    for record in data.get("publications", []):
        if record.get("id") not in requested:
            continue
        if args.apply_pending:
            apply_pending_changes(record)
        record.setdefault("review", {})["status"] = REVIEW_APPROVED
        record["review"]["lastReviewed"] = utc_today()
        record["review"]["source"] = "human approval"
        approved.append(record["id"])
    missing = sorted(requested - set(approved))
    if missing:
        raise PublicationAssistantError(f"Unknown publication ids: {', '.join(missing)}")
    write_json(DATA_FILE, data)
    current = PUBLICATIONS_PAGE.read_text(encoding="utf-8")
    PUBLICATIONS_PAGE.write_text(generate_page(data, current), encoding="utf-8")
    print(f"Approved {len(approved)} publication record(s): {', '.join(approved)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Import the existing publication cards once")
    bootstrap.add_argument("--overwrite", action="store_true", help="Replace an existing canonical data file")
    bootstrap.set_defaults(func=command_bootstrap)

    generate = subparsers.add_parser("generate", help="Render publications.html from canonical data")
    generate.add_argument("--check", action="store_true", help="Fail if generated HTML differs from the current page")
    generate.set_defaults(func=command_generate)

    validate = subparsers.add_parser("validate", help="Validate canonical publication data")
    validate.add_argument("--require-approved", action="store_true", help="Fail when any record still needs human review")
    validate.add_argument("--generated", action="store_true", help="Also require deterministic HTML to be current")
    validate.set_defaults(func=command_validate)

    discover = subparsers.add_parser("discover", help="Discover and classify scholarly metadata changes")
    discover.add_argument("--apply", action="store_true", help="Add reviewable records and pending changes to canonical data")
    discover.add_argument("--only-changes", action="store_true", help="Omit unchanged matched metadata from the report")
    discover.add_argument("--fixture", type=Path, help="Use a local candidate fixture instead of network services")
    discover.set_defaults(func=command_discover)

    approve = subparsers.add_parser("approve", help="Explicitly approve reviewed records")
    approve.add_argument("--id", action="append", required=True, help="Publication id to approve; repeat or use 'all'")
    approve.add_argument("--apply-pending", action="store_true", help="Apply non-protected pending metadata before approval")
    approve.set_defaults(func=command_approve)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except PublicationAssistantError as exc:
        print(f"publication assistant: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
