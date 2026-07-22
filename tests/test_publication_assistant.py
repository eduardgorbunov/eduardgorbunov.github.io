#!/usr/bin/env python3
"""Regression tests for the human-reviewed publication assistant."""

from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import publication_assistant as assistant  # noqa: E402


class PublicationAssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))

    def test_current_data_is_valid_and_deterministic(self) -> None:
        require_approved = os.environ.get("PUBLICATION_REVIEW_MODE") != "proposal"
        self.assertEqual([], assistant.validate_data(self.data, require_approved=require_approved))
        matches, diff = assistant.check_generated_page(self.data)
        self.assertTrue(matches, diff[:2000])

    def test_author_annotations_are_structured_and_consistent(self) -> None:
        for record in self.data["publications"]:
            structured_relations = {
                relation
                for author in record["authors"]
                for relation in author["relations"]
            }
            self.assertEqual(set(record["authorRelations"]), structured_relations, record["id"])

        mentored = next(
            item for item in self.data["publications"] if item["id"] == "pub-heavy-tailed-data-gradient-clipping"
        )
        self.assertEqual(["external-msc"], mentored["authors"][0]["relations"])
        self.assertEqual([], next(author for author in mentored["authors"] if author["isMe"])["relations"])

        senior = next(
            item for item in self.data["publications"] if item["id"] == "pub-batch-size-conditional-gradient"
        )
        self.assertEqual(
            ["Eduard Gorbunov", "Volkan Cevher"],
            [author["name"] for author in senior["authors"] if author["markers"] == ["†"]],
        )

    def test_identifier_normalization(self) -> None:
        self.assertEqual("10.1007/example", assistant.normalize_doi("https://doi.org/10.1007/EXAMPLE"))
        self.assertEqual("2607.14731", assistant.normalize_arxiv_id("https://arxiv.org/pdf/2607.14731v2.pdf"))
        self.assertEqual("2607.14731", assistant.arxiv_id_from_doi("10.48550/arXiv.2607.14731"))
        self.assertEqual("", assistant.arxiv_id_from_doi("10.1007/example"))

    def test_match_prefers_stable_identifiers(self) -> None:
        candidate = assistant.Candidate(
            title="A deliberately different display title",
            authors=["Eduard Gorbunov"],
            arxiv="2607.14731",
        )
        matches = assistant.find_candidate_matches(candidate, self.data["publications"])
        self.assertEqual("pub-whats-in-a-smoothness-constant-local-sgd", matches[0][0]["id"])
        self.assertEqual("arXiv ID", matches[0][1])

    def test_published_version_becomes_pending_review(self) -> None:
        data = copy.deepcopy(self.data)
        record = next(
            item
            for item in data["publications"]
            if item["id"] == "pub-convergence-of-clipped-sgd-for-convex-l0-l1-smooth-optimization-with-heavy"
        )
        protected_before = {field: copy.deepcopy(record.get(field)) for field in assistant.PROTECTED_FIELDS}
        candidate = assistant.Candidate(
            title=record["title"],
            authors=[author["name"] for author in record["authors"]],
            abstract=record["abstract"],
            published_date="2027-01-10",
            publication_type="journal paper",
            venue="Example Journal",
            doi="10.5555/example-doi",
            arxiv=record["identifiers"]["arxiv"],
            links={"doi": "https://doi.org/10.5555/example-doi"},
            sources={"record": "https://example.org/record"},
        )
        proposal = assistant.classify_candidate(candidate, data["publications"])
        self.assertEqual("published version found", proposal["classification"])
        changed = assistant.apply_proposals(data, [proposal])
        self.assertEqual([record["id"]], changed)
        self.assertEqual(assistant.REVIEW_NEEDED, record["review"]["status"])
        self.assertEqual("10.5555/example-doi", record["pendingChanges"]["identifiers"]["doi"])
        for field, value in protected_before.items():
            self.assertEqual(value, record.get(field), field)

    def test_new_record_keeps_manual_fields_empty_and_separates_topic_tags(self) -> None:
        data = copy.deepcopy(self.data)
        candidate = assistant.Candidate(
            title="Local SGD under Client Heterogeneity",
            authors=["Ada Student", "Eduard Gorbunov"],
            abstract=(
                "We study stochastic optimization with local SGD and local steps under heterogeneous client data. "
                "Our analysis gives convergence guarantees for distributed learning and federated optimization "
                "without assuming random reshuffling, and the experiments verify the resulting theory in detail."
            ),
            published_date="2026-07-22",
            publication_type="arXiv preprint",
            venue="arXiv preprint",
            arxiv="2607.99999",
            links={"arxiv": "https://arxiv.org/abs/2607.99999", "pdf": "https://arxiv.org/pdf/2607.99999"},
            sources={"record": "https://arxiv.org/abs/2607.99999"},
        )
        record = assistant.new_record_from_candidate(candidate, data)
        self.assertEqual(assistant.REVIEW_NEEDED, record["review"]["status"])
        self.assertIn("local-steps", record["tags"])
        self.assertNotIn("random-reshuffling", record["tags"])
        self.assertEqual([], record["authorRelations"])
        self.assertEqual([], record["distinctions"])
        self.assertFalse(record["news"]["enabled"])

    def test_incomplete_new_candidate_is_reported_but_not_added(self) -> None:
        data = copy.deepcopy(self.data)
        candidate = assistant.Candidate(
            title="A Possible Paper with Incomplete Metadata",
            authors=["Eduard Gorbunov"],
            publication_type="journal paper",
            doi="10.5555/incomplete",
            links={"doi": "https://doi.org/10.5555/incomplete"},
        )
        proposal = assistant.classify_candidate(candidate, data["publications"])
        self.assertEqual("conflict", proposal["classification"])
        self.assertIn("abstract", proposal["reason"])
        self.assertEqual([], assistant.apply_proposals(data, [proposal]))
        self.assertEqual(len(self.data["publications"]), len(data["publications"]))

    def test_initial_only_author_match_cannot_create_a_new_card(self) -> None:
        candidate = assistant.Candidate(
            title="An Unrelated Work by Another E. Gorbunov",
            authors=["E. Gorbunov", "Another Author"],
            abstract=(
                "This deliberately complete abstract contains enough words to pass ordinary metadata checks, "
                "but the abbreviated author identity is not strong enough to create a new publication record "
                "for this website without a human resolving the ambiguity first."
            ),
            publication_type="journal paper",
            venue="Example Journal",
            doi="10.5555/ambiguous-author",
            links={"doi": "https://doi.org/10.5555/ambiguous-author"},
        )
        proposal = assistant.classify_candidate(candidate, self.data["publications"])
        self.assertEqual("conflict", proposal["classification"])
        self.assertIn("Eduard Gorbunov", proposal["reason"])

    def test_author_identity_does_not_accept_an_unrelated_initial(self) -> None:
        self.assertTrue(assistant.candidate_has_target_author(["E. Gorbunov"]))
        self.assertTrue(assistant.candidate_has_target_author(["Gorbunov, Eduard"]))
        self.assertFalse(assistant.candidate_has_target_author(["V. E. Gorbunov"]))
        self.assertFalse(assistant.candidate_has_target_author(["Gorbunov V."]))
        self.assertFalse(assistant.candidate_has_target_author(["Gorbunov"]))

    def test_sparse_crossref_and_orcid_metadata_are_supported(self) -> None:
        self.assertEqual(
            assistant.crossref_date({"published": {"date-parts": [[2025, None, None]]}}),
            "2025-01-01",
        )
        payload = {
            "group": [
                {
                    "work-summary": [
                        {
                            "put-code": 42,
                            "title": {"title": {"value": "A complete scholarly title"}},
                            "journal-title": None,
                            "type": "preprint",
                            "publication-date": {"year": {"value": "2026"}},
                            "external-ids": {"external-id": []},
                        }
                    ]
                }
            ]
        }
        with mock.patch.object(assistant, "cached_request", return_value=json.dumps(payload).encode()):
            candidates = assistant.discover_orcid({"orcid": "0000-0002-3370-4130"})
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].venue, "")

    def test_discovery_identity_and_schema_are_explicit(self) -> None:
        self.assertEqual("./publications.schema.json", self.data["$schema"])
        self.assertEqual("A5087594198", self.data["author"]["openAlexAuthorId"])
        self.assertEqual("0000-0002-3370-4130", self.data["author"]["orcid"])
        self.assertTrue((ROOT / "data" / "publications.schema.json").is_file())

    def test_approval_drops_any_protected_pending_field(self) -> None:
        record = copy.deepcopy(self.data["publications"][0])
        original_tags = copy.deepcopy(record["tags"])
        original_authors_html = record["authorsHtml"]
        record["pendingChanges"] = {
            "venue": "A reviewed venue",
            "tags": ["differential-privacy"],
            "authorsHtml": "Unsafe automatic rewrite",
            "distinctions": ["Automatic award"],
        }
        assistant.apply_pending_changes(record)
        self.assertEqual("A reviewed venue", record["venue"])
        self.assertEqual(original_tags, record["tags"])
        self.assertEqual(original_authors_html, record["authorsHtml"])
        self.assertNotIn("Automatic award", record["distinctions"])


if __name__ == "__main__":
    unittest.main()
