# Eight-point completion checklist

Validated on 2026-11-23 using Python 3.12 and the pinned MiniLM model.

| Requested correction | Delivered evidence | Status / limit |
|---|---|---|
| 1. Real public requirement | [Requirement record](real_client_requirement.md), URL/date/excerpt/problem/acceptance mapping; selected-source API; [public CPython pilot](public_corpus_validation.md) | Public-task prototype and real-document pilot complete. No commissioned client or acceptance claimed. Azure integration/scalability outside scope. |
| 2. Three or more overlaps | [Overlap table](overlap_cost_audit.md), size=32, overlaps=0/8/16/24, counts/duplication/Recall/MRR/context | Measured. Recall plateaus at 16 while duplication rises at 24. |
| 3. 12–15 boundary questions | [12-query fixture](../data/chunk_boundary_queries.json), [lab and interpretation](chunk_boundary_failure_lab.md), [full traces](chunk_boundary_traces.jsonl) | Five configurations; all seven requested categories; original 24 held-out questions unchanged. |
| 4. Five improved + five degraded reranker cases | [Case inspection](reranker_case_analysis.md), [stress inputs](../data/stress_queries.json), [selection disclosure](../data/stress_protocol.md) | Five of each in S01–S10, actual equal-candidate runs, query-specific explanations. Agent-authored inspection; independent human sign-off remains unclaimed. Original held-out set: two improvements, zero degradations. |
| 5. Who rescues whom / hybrid failures | [Rescue analysis](retriever_rescue_analysis.md), [paired traces](inspection_traces.jsonl) | Q15/Q21 dense rescue; S11 sparse rescue; S12/S13 hybrid failures. Stress results separate from held-out metrics. |
| 6. Trusted-source conflict detection | [Conflict audit](conflict_detection.json), application integration and tests | Unresolved 20/40 MB claims return both citations; authority/date/version cases resolve; conflict suppresses optional generation and is visible in browser/CLI. Teaching rule for upload/attachment limits. |
| 7. README result links | [Root README](../../README.md) links into Week28_Engineering/results | All repository-relative Markdown links checked for existing targets. |
| 8. Portable run instructions | [Root README](../../README.md) clone/venv/install/download/run | No personal machine path in primary instructions; commands consistently use project venv. |

The original 24 held-out queries, four chunk configurations and R0–R4 selection
protocol are preserved. Neither stress diagnostics nor public pilot results
change the default. The complete suite passes **15 tests**, including HTTP API,
invalid inputs, source scope, conflict/generator behavior, audit-command execution
and preservation of the original benchmark inputs.
