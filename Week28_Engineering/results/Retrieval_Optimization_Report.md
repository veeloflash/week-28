# Retrieval Optimization Report

## Client and problem

This is a public-requirement-aligned prototype, not a commissioned client delivery. It references [LlamaIndex issue #19370](https://github.com/run-llama/llama_index/issues/19370), created 2025-07-09, a public report about RAG folder filtering leaking unselected paths. The AX-17/AX-18 corpus is synthetic and remains a controlled test fixture; no real client corpus has been validated. See `real_client_requirement.md` for source, requirement summary, client problem, and acceptance criteria.

## Corpus and method

I used four versioned Markdown documents, including one untrusted forum post. The baseline benchmark has eight development questions and 24 held-out questions. Evidence labels identify exact source spans so they remain valid when chunk IDs change. The dense backend is MiniLM ONNX, and the answer formatter is held constant.

R0 uses dense retrieval and fixed 32-word chunks. R1 uses the chunk configuration selected on development questions. R2 adds BM25 and RRF; R3 reranks the same candidate set; R4 adds guarded query expansion. Each stage retrieves 12 candidates and evaluates the top five.

## Chunk comparison on development questions

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| fixed32 | 0.875 | 0.625 | 0.875 | 4.837 | 5.526 | 151.4 |
| overlap32 | 0.875 | 0.562 | 0.875 | 4.490 | 5.019 | 156.2 |
| fixed64 | 1.000 | 0.792 | 1.000 | 4.712 | 5.330 | 285.6 |
| sections | 1.000 | 1.000 | 1.000 | 5.218 | 6.355 | 95.6 |

These are the original chunk-lab runs, not the new four-point overlap audit. The latter is produced by `coursework_audits.py` and recorded separately in `overlap_cost_audit.csv`/`.md` after running the audit.

## Held-out R0–R4 comparison

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| R0 | 0.864 | 0.636 | 0.864 | 4.908 | 5.876 | 156.2 |
| R1 | 1.000 | 0.871 | 1.000 | 3.849 | 5.107 | 96.2 |
| R2 | 1.000 | 0.955 | 1.000 | 4.778 | 6.621 | 100.9 |
| R3 | 1.000 | 1.000 | 1.000 | 5.336 | 6.567 | 102.6 |
| R4 | 1.000 | 1.000 | 1.000 | 6.175 | 10.320 | 102.6 |

Recall measures coverage of labeled evidence spans in the selected results, including coverage across adjacent chunks. MRR uses the first selected chunk containing a complete labeled span. Unanswerable questions are excluded from recall and MRR.

## Sparse versus dense on the selected chunk setup

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| sparse | 0.909 | 0.856 | 0.909 | 0.445 | 0.590 | 83.9 |
| dense | 1.000 | 0.871 | 1.000 | 4.620 | 6.193 | 96.2 |
| hybrid | 1.000 | 0.955 | 1.000 | 3.801 | 6.349 | 100.9 |

Per-query rescue examples and hybrid misses are generated in `retriever_rescue_analysis.md`; the aggregate metrics alone do not identify which retriever rescued a query.

## Expansion control

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| off | 1.000 | 1.000 | 1.000 | 5.336 | 6.567 | 102.6 |
| guarded | 1.000 | 1.000 | 1.000 | 6.175 | 10.320 | 102.6 |
| broad | 1.000 | 1.000 | 1.000 | 10.155 | 11.188 | 103.9 |

Guarded expansion preserves precise wording. The broad control adds generic wording and can remove syntax such as API parentheses. Traces record rewritten identifiers and recall changes.

## Security check: untrusted content

The existing security audit reports that the adversarial forum post can rank highly when unfiltered, while trusted filtering excludes it and the answer stage does not cite untrusted content. Trust comes from the source manifest, not search score.

## Trusted-source conflict detection

A separate trusted-source fixture contains two AX-17 manuals with conflicting upload limits (20 MB and 40 MB). The conflict handler scopes claims to product and compares source authority, publication date, and document version. Tied contradictory evidence returns `conflicting_evidence` with both citations; a unique precedence winner can be selected. The audit fixture tests this behavior. In the interactive app, conflict checking is activated when the selected data directory contains `source_metadata.json`.

## Chunk boundary failure lab

A dedicated 12-question known-evidence fixture covers heading/paragraph, table header/row, code/explanation, multi-fact boundaries, long sections, overlap rescue, and section-aware rescue. It is separate from the existing eight development and 24 held-out queries. Run `coursework_audits.py` to generate `chunk_boundary_failure_lab.csv` and `.md`.

## Reranker case inspection

R2 and R3 use the same candidates; the audit asserts equality per query. `reranker_case_analysis.md` lists measured changes. The requirement to inspect five improved and five degraded examples is not claimed complete unless the generated case set has at least five in each category and a person reviews them. If fewer are measured, add difficult evidence-grounded distractor queries rather than invent cases.

## Failure examples and recommendation

The original R0 trace includes boundary/partial-span misses such as Q03, Q09, and Q20. Full failure counts, spans, and traces remain in `benchmark.json` and `retrieval_traces.jsonl`.

The original baseline recommends R1 with section-aware chunks for a pilot, based on development evidence recall, complete coverage, MRR, and cost proxies. R3 reached held-out MRR@5 of 1.000, so it is worth separately evaluating when first-result ranking matters.

All reported baseline timings use a small synthetic English corpus on one machine with an already-built index. Retrieval latency excludes index build and API billing. This report does not claim production client acceptance or real-corpus validation.
