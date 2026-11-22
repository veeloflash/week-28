# Public client requirement and acceptance mapping

## Source

- **Source URL:** https://github.com/run-llama/llama_index/issues/19370
- **Source date:** 2025-07-09 (issue creation date shown by GitHub)
- **Type:** Public open-source GitHub issue; not a private or commissioned client engagement.
- **Original requirement:** The issue author reports that a RAG application's Azure AI Search folder filter can return chunks from paths the user did not select. The author asks maintainers whether `odata_filters` is supported and how to strictly limit retrieval to selected paths without running into OData recursion limits. See the linked issue for the full original report, reproduction, and expected/actual behavior.

## Client problem represented

In a retrieval application, a user-selected scope must be a hard boundary: content outside the selected source set must not reach the answer stage. Retrieval quality and citations are not sufficient if filtering silently leaks unselected content.

## Acceptance criteria for this project

1. Search defaults to trusted sources and cannot cite the untrusted forum fixture.
2. Each returned evidence passage retains its source identity and line-based citation.
3. Evaluation records retrieved candidates and selected passages so filtering and provenance can be audited.
4. A future real-corpus validation should verify that every retrieved source belongs to an explicitly selected source set; the present AX-17/AX-18 corpus is a synthetic test fixture and does not establish this criterion for a real deployment.

## Scope and evidence limitation

The project implements a local trusted-source filter and provenance-aware answers. That is related to, but does not claim to resolve, the issue's Azure AI Search `odata_filters` behavior. The AX-17/AX-18 synthetic corpus remains a controlled benchmark fixture. No real customer documents, private data, or production client acceptance were supplied. This distinction prevents the public issue from being misrepresented as a commissioned project or as validation of Azure-specific filtering.
