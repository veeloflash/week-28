# Measured additional audit artifacts

The committed files were generated with MiniLM on 2026-11-23. From `Week28_Engineering`, run `python coursework_audits.py --embedding minilm` to reproduce:

- `results/overlap_cost_audit.csv` and `.md` — fixed 32-word chunks, overlap 0/8/16/24.
- `results/chunk_boundary_failure_lab.csv` and `.md` — 12 known-evidence boundary questions across five chunking configurations.
- `results/reranker_case_analysis.csv` and `.md` — measured paired R2/R3 evidence rank changes and candidate equality checks.
- `results/retriever_rescue_analysis.csv` and `.md` — per-query sparse, dense, and hybrid outcomes.
- `results/conflict_detection.json` — two trusted contradictory claims with citations, plus authority/date/version resolution cases.
- `results/public_corpus_validation.md` and `.json` — three real public documents, six queries and 90 source-scope checks.
- `results/coursework_audit_status.json` — backend, input hashes and review status.

See [completion checklist](completion_checklist.md). Five improved and five degraded stress cases now have actual paired measurements and agent-authored inspection. Independent human sign-off and commissioned-client acceptance remain unclaimed. No ranks were fabricated.
