# Retrieval Optimization Report

## Client and problem

This prototype addresses a real public source-isolation requirement documented in [LlamaIndex issue #19370](https://github.com/run-llama/llama_index/issues/19370). The source URL, date, original requirement, client problem and acceptance mapping are in [real_client_requirement.md](real_client_requirement.md). AX-17/AX-18 are synthetic fixtures for controlled ranking experiments; they are not client documents. The separate CPython public-document pilot validates local retrieval and allowed-source isolation. No commissioned engagement, Azure integration fix, or client acceptance is claimed.

## Corpus and method

I used 4 versioned Markdown documents, including one untrusted forum post. The benchmark has 8 development questions and 24 held-out questions. The evidence labels identify exact source spans so they still work when chunk IDs change. The dense backend was sentence-transformers/all-MiniLM-L6-v2 (quantized ONNX, 384 dimensions). The answer formatter stayed fixed.

R0 starts with dense retrieval and fixed 32-word chunks. R1 uses the chunk setup selected on development questions. R2 adds BM25 and RRF, R3 rescores the same candidate set with the controlled reranker, and R4 adds guarded query expansion. Each run keeps 12 candidates and evaluates the top 5.

## Chunk comparison on development questions

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| fixed32 | 0.875 | 0.625 | 0.875 | 2.352 | 2.702 | 151.4 |
| overlap32 | 0.875 | 0.562 | 0.875 | 2.421 | 3.843 | 156.2 |
| fixed64 | 1.000 | 0.792 | 1.000 | 2.191 | 3.486 | 285.6 |
| sections | 1.000 | 1.000 | 1.000 | 2.094 | 3.109 | 95.6 |

Chunk counts and indexed words for each setting are in `chunk_inventory.csv`. Overlapping character coverage in the selected context is recorded as the duplicate fraction.

## Held-out R0–R4 comparison

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| R0 | 0.864 | 0.636 | 0.864 | 2.177 | 3.290 | 156.2 |
| R1 | 1.000 | 0.871 | 1.000 | 2.714 | 4.952 | 96.2 |
| R2 | 1.000 | 0.955 | 1.000 | 3.207 | 5.278 | 100.9 |
| R3 | 1.000 | 1.000 | 1.000 | 2.291 | 2.818 | 102.6 |
| R4 | 1.000 | 1.000 | 1.000 | 2.778 | 4.450 | 102.6 |

Recall measures how many labelled evidence spans are covered by the selected chunks, including spans covered across adjacent chunks. MRR counts the first result that contains a complete labelled span. Chunk-ID Recall is reported separately. Unanswerable queries are excluded from recall and MRR.

## Sparse versus dense on the selected chunk setup

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| sparse | 0.909 | 0.856 | 0.909 | 0.193 | 0.306 | 83.9 |
| dense | 1.000 | 0.871 | 1.000 | 2.112 | 2.817 | 96.2 |
| hybrid | 1.000 | 0.955 | 1.000 | 2.602 | 3.601 | 100.9 |

## Expansion control

| Run | Evidence Recall@5 | MRR@5 | All evidence | P50 ms | P95 ms | Avg. context tokens |
|---|---:|---:|---:|---:|---:|---:|
| off | 1.000 | 1.000 | 1.000 | 2.291 | 2.818 | 102.6 |
| guarded | 1.000 | 1.000 | 1.000 | 2.778 | 4.450 | 102.6 |
| broad | 1.000 | 1.000 | 1.000 | 4.560 | 6.061 | 103.9 |

Guarded expansion leaves precise wording alone. The broad control adds generic wording and may drop syntax such as API parentheses. The traces record rewritten identifiers lost and every question where expansion reduced evidence recall. The original query remains a separate branch.

## Security check

- sparse_unfiltered: untrusted top-5 ranks [1]; untrusted excerpt cited: False.
- sparse_filtered: untrusted top-5 ranks []; untrusted excerpt cited: False.
- dense_unfiltered: untrusted top-5 ranks [1]; untrusted excerpt cited: False.
- dense_filtered: untrusted top-5 ranks []; untrusted excerpt cited: False.
- hybrid_unfiltered: untrusted top-5 ranks [1]; untrusted excerpt cited: False.
- hybrid_filtered: untrusted top-5 ranks []; untrusted excerpt cited: False.

Authority comes from the source manifest. Search score does not set trust. Identical chunks are deduplicated within each ranking. The answer stage excludes untrusted passages even when the audit deliberately disables the retrieval filter.

## Failure examples

- R0 Q03 (exact, partial_span_or_boundary): What does send_logs() do on AX-17? First result: AX-17 diagnostics.
- R0 Q09 (paraphrase, partial_span_or_boundary): How can I get the AX-17 diagnostic information out of the device? First result: AX-17 firmware 2.1 recovery.
- R0 Q20 (exact, partial_span_or_boundary): How much free space does AX-17 need before installing an update? First result: AX-17 battery and charging.

The full failure counts, slice scores and source spans are in `benchmark.json` and `retrieval_traces.jsonl`.

## Recommendation

I would start a pilot with **R1** and **sections**. This stage was selected on development evidence recall, complete coverage and MRR, with duplication and work as tie-breakers. Held-out evidence Recall@5 was 1.000 versus 0.864 for R0. MRR@5 was 0.871. It abstained on 2/2 unanswerable questions.

R3 reached MRR@5 of 1.000 on the held-out set, so I would also compare it with R1 in a fresh pilot where the first result matters. That observation did not change the development-based default.

These runs measure a small synthetic English corpus on one machine with an already-built index. The timing is retrieval only. Counts of embedding calls, lexical calls, scored pairs and indexed/context words are cost proxies. No API usage was billed. Evidence coverage does not measure whether a person found the quoted answer helpful. Before production I would test with independent real support queries, more unknown products and versions, and a wider set of malicious documents.

## Additional coursework evidence

The original dev/test selection above is unchanged by these separate diagnostic labs:

- [Overlap cost audit](overlap_cost_audit.md): size 32, overlap 0/8/16/24, duplication, ranking and context cost.
- [Chunk boundary lab](chunk_boundary_failure_lab.md): 12 labelled questions and boundary-specific analysis.
- [Reranker cases](reranker_case_analysis.md): five improved and five degraded stress cases with paired score inspection.
- [Retriever rescue cases](retriever_rescue_analysis.md): dense rescue, sparse rescue and hybrid failure examples.
- [Conflict detection](conflict_detection.json): ambiguous trusted claims and precedence-based resolution.
- [Public-document validation](public_corpus_validation.md): real documentation and source-scope isolation checks.
- [Completion checklist](completion_checklist.md): evidence for each requested correction and remaining external sign-offs.
