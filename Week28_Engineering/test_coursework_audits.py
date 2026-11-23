import json
import unittest
from dataclasses import replace
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from benchmark import load_queries
from conflict_detection import apply_conflict_detection
from retrieval import CHUNK_CONFIGS, Index, ROOT, load_sources, make_embedder
from overlap_configs import OVERLAP_AUDIT_CONFIGS


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

    def test_conflict_product_date_version_and_scoped_generation(self):
        from app import SearchApp
        from benchmark import STAGES
        data = ROOT / 'data' / 'conflict_case'
        sources = load_sources(data)
        metadata = json.loads((data / 'source_metadata.json').read_text(encoding='utf-8'))
        query = 'What is the AX-17 attachment upload limit?'
        for rule in ('date', 'version', 'product'):
            variants = [replace(s, version='2.0') if rule=='version' and s.id=='conflict_v2' else s for s in sources]
            index = Index(variants, CHUNK_CONFIGS['sections'], self.embedder)
            result = index.search(query, **STAGES['R1'])
            changed = {key:dict(value) for key,value in metadata.items()}
            if rule == 'date': changed['conflict_v2']['published_at'] = '2025-02-15'
            if rule == 'product': changed['conflict_v1']['product'] = 'AX-18'
            answer = apply_conflict_detection(index, result, index.answer(result), changed)
            if rule == 'product':
                self.assertNotEqual(answer['status'], 'conflicting_evidence')
            else:
                self.assertEqual(len(answer['passages']), 1)
                self.assertIn('40 MB', answer['answer'])
        generator = unittest.mock.Mock(return_value='should never hide conflict')
        app = SearchApp(data, {'stage':'R1','r1_chunk':'sections'}, 'minilm', generator=generator)
        answer = app.search(query, generate=True)['answer']
        self.assertEqual(answer['status'], 'conflicting_evidence')
        self.assertIn('20 MB', answer['answer'])
        self.assertIn('40 MB', answer['answer'])
        self.assertTrue(all(p['citation'] in answer['answer'] for p in answer['passages']))
        generator.assert_not_called()
        self.assertEqual(app.search(query, allowed_sources=[])['answer']['status'], 'insufficient_evidence')

    def test_audit_command_completes_and_preserves_heldout(self):
        from coursework_audits import run
        golden = (ROOT/'data'/'queries.json').read_bytes()
        self.assertEqual({c.overlap for c in OVERLAP_AUDIT_CONFIGS.values()}, {0,8,16,24})
        with TemporaryDirectory() as tmp:
            output=Path(tmp)
            run(ROOT/'data', output, 'minilm')
            status=json.loads((output/'coursework_audit_status.json').read_text(encoding='utf-8'))
            self.assertGreaterEqual(status['reranker_improved_cases'],5)
            self.assertGreaterEqual(status['reranker_degraded_cases'],5)
            self.assertEqual(status['boundary_question_count'],12)
            public=json.loads((output/'public_corpus_validation.json').read_text(encoding='utf-8'))
            self.assertEqual(len(public['scope_checks']),90)
            self.assertEqual(public['scope_leaks'],0)
            self.assertTrue((output/'inspection_traces.jsonl').stat().st_size > 0)
        self.assertEqual((ROOT/'data'/'queries.json').read_bytes(), golden)


if __name__ == "__main__":
    unittest.main()
