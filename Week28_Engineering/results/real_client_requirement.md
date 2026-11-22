# Public client requirement and acceptance mapping

## Source

- **Source URL:** https://github.com/run-llama/llama_index/issues/19370
- **Date:** 2025-07-09 (GitHub issue creation date)
- **Source type:** Public, open-source project issue. The author did not commission this Week 28 project.
- **Original requirement (short excerpt):** “The retriever should strictly limit retrieved chunks to the subset of documents whose `relative_path` values match those in `odata_filters`.” The issue also reports that unselected-folder passages appeared in answers and asks how to apply large-scale filtering without OData recursion limits. The linked issue is the source of truth for the full original report and reproduction.

## Client problem

A RAG application's user-selected folder/source scope must be a hard boundary: evidence outside the selected set must not reach the answer stage. Search quality and citations are not sufficient if filtering silently exposes unselected content.

## Acceptance criteria mapped to this prototype

1. Trusted-source filtering excludes the untrusted forum fixture from normal retrieval and answers.
2. Returned evidence passages retain source identity and a line-based citation.
3. Retrieval traces record candidates and selected passages so provenance and filtering can be audited.
4. A real-corpus follow-up must assert that every returned source is in the caller's selected set. This criterion is not validated by the synthetic fixture.

## Scope and evidence limitation

This work maps the public requirement to local trusted-source filtering, provenance, and retrieval audits. It does **not** claim to fix Azure AI Search's `odata_filters` integration or to be a commissioned client delivery. AX-17/AX-18 documents are synthetic controlled-benchmark fixtures. No production client corpus or real-document validation is included yet.
