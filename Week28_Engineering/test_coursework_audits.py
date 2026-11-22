import json
import unittest
from unittest.mock import patch

from benchmark import load_queries
from conflict_detection import apply_conflict_detection
from retrieval import CHUNK_CONFIGS, Index, ROOT, load_sources, make_embedder


class CourseworkAuditFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.embedder = make_embedder([], "minilm")

    def test_boundary_lab_has_12_to_15_valid_known_evidence_queries(self):
        data = ROOT / "data"
        sources = load_sources(data / "chunk_boundary")
        cases = load_queries(data / "chunk_boundary_queries.json", sources)
        self.assertGreaterEqual(len(cases), 12)
        self.assertLessEqual(len(cases), 15)
        self.assertTrue(all(case["spans"] for case in cases))
        categories = {case["category"] for case in cases}
        self.assertTrue({"heading_paragraph", "table_header_row", "code_explanation",
                         "multi_fact_boundary", "long_section", "overlap_rescue",
                         "section_aware_rescue"} <= categories)

    def test_conflicting_trusted_upload_limits_return_both_citations(self):
        data = ROOT / "data" / "conflict_case"
        sources = load_sources(data)
        index = Index(sources, CHUNK_CONFIGS["sections"], self.embedder)
        from benchmark import STAGES
        query = "What is the AX-17 upload limit?"
        result = index.search(query, **STAGES["R1"])
        answer = index.answer(result)
        metadata = json.loads((data / "source_metadata.json").read_text(encoding="utf-8"))
        answer = apply_conflict_detection(index, result, answer, metadata)
        self.assertEqual(answer["status"], "conflicting_evidence")
        self.assertEqual(len(answer["passages"]), 2)
        self.assertTrue(all(passage.get("citation") for passage in answer["passages"]))

    def test_product_and_precedence_metadata_resolve_conflict(self):
        data = ROOT / "data" / "conflict_case"
        sources = load_sources(data)
        index = Index(sources, CHUNK_CONFIGS["sections"], self.embedder)
        from benchmark import STAGES
        query = "What is the AX-17 upload limit?"
        result = index.search(query, **STAGES["R1"])
        answer = index.answer(result)
        metadata = {"conflict_v1": {"product": "AX-17", "published_at": "2025-01-15", "authority": 1},
                    "conflict_v2": {"product": "AX-17", "published_at": "2025-02-15", "authority": 2}}
        answer = apply_conflict_detection(index, result, answer, metadata)
        self.assertEqual(answer["status"], "evidence_found")
        self.assertEqual(len(answer["passages"]), 1)
        self.assertIn("40 MB", answer["passages"][0]["text"])


if __name__ == "__main__":
    unittest.main()
