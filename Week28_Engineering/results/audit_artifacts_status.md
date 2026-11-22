# Additional audit artifacts

From `Week28_Engineering`, run `python coursework_audits.py --embedding minilm` to generate these files from the actual corpus and fixtures:

- `results/overlap_cost_audit.csv` and `.md` — fixed 32-token chunks, overlap 0/8/16/24.
- `results/chunk_boundary_failure_lab.csv` and `.md` — 12 known-evidence boundary questions across five chunking configurations.
- `results/reranker_case_analysis.csv` and `.md` — measured paired R2/R3 evidence rank changes and candidate equality checks.
- `results/retriever_rescue_analysis.csv` and `.md` — per-query sparse, dense, and hybrid outcomes.
- `results/conflict_detection.json` — two trusted contradictory manual claims with citations.

These result files are generated artifacts and are not represented as measured until the command has run successfully. The reranker course requirement remains incomplete unless at least five improved and five degraded cases are available and human-inspected. No synthetic rank movement is fabricated to fill that quota.
