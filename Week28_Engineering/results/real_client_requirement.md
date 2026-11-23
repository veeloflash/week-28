# Public client requirement and acceptance mapping

## Source

- **Source URL:** https://github.com/run-llama/llama_index/issues/19370
- **Date:** 2025-07-09 (GitHub issue creation date)
- **Source type:** Public, open-source project issue. The author did not commission this Week 28 project.
- **Original requirement (short excerpt):** “The retriever should strictly limit retrieved chunks to the subset of documents whose `relative_path` values match those in `odata_filters`.” The issue also reports that unselected-folder passages appeared in answers and asks how to apply large-scale filtering without OData recursion limits. The linked issue is the source of truth for the full original report and reproduction.

## Client problem

A RAG application's user-selected folder/source scope must be a hard boundary: evidence outside the selected set must not reach the answer stage. Search quality and citations are not sufficient if filtering silently exposes unselected content.

## Acceptance criteria mapped to this prototype

1. `allowed_sources` is a hard source-ID allowlist applied before sparse/dense ranking and RRF. `None` means all trusted sources; an empty list means no sources; unknown IDs fail with HTTP 400. This is separate from trusted/untrusted filtering.
2. The answer stage rechecks that cited chunks belong to the selected source set; passages retain source identity and line-based citations.
3. Retrieval traces expose the allowed source set, candidates and selected passages for auditing.
4. On three real CPython documentation files, every returned/cited source must be within the selected set, including queries whose supporting passage is in an excluded document. The [public pilot](public_corpus_validation.md) passes 90 such checks; the [JSON](public_corpus_validation.json) lists all source combinations.

## Scope and evidence limitation

This work implements the public requirement's local source-isolation property and validates it on real public documentation. It does **not** claim to fix Azure AI Search's `odata_filters` integration, its recursion limits, or to be a commissioned client delivery. AX-17/AX-18 documents remain synthetic controlled-benchmark fixtures. The CPython pilot is a small public-document validation, not a production client corpus, 50k-path scale test, or evidence of acceptance by the issue author.

The source and issue creation date were verified on 2026-11-23. The original requirement is scoped to Azure/LlamaIndex; the local mapping above is our derived acceptance specification. See [snapshots and provenance](../data/public_docs/provenance.json) for the independent real-document pilot.
