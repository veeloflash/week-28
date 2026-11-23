# Real public-document pilot

Source: three PSF-licensed CPython 3.12.8 documentation files, captured on 2026-11-23. Original URLs and SHA-256 hashes are recorded in [provenance](../data/public_docs/provenance.json); the [license](../data/public_docs/LICENSE.txt) accompanies the snapshots. This is a small exploratory public-corpus pilot, not private client validation or an upstream Azure fix.

Backend: sentence-transformers/all-MiniLM-L6-v2 (quantized ONNX, 384 dimensions). 92 chunks; 6 labelled questions; top-N=12, top-k=5, no reranking/expansion. Raw reStructuredText is used as supplied; the Markdown section detector falls back to 55-word windows. These limitations are part of the measured pilot.

| Method | Recall@5 | MRR@5 |
|---|---:|---:|
| sparse | 1.0 | 0.7222 |
| dense | 1.0 | 0.5889 |
| hybrid | 1.0 | 0.8333 |

90 source-scope checks passed with zero leaked sources, including empty scope and excluded-gold-document queries. Every trace and citation must remain within allowed_sources. This tests source isolation, not answer relevance: allowed but irrelevant passages may still appear. Source selection is an API caller constraint, not a replacement for authentication/authorization.

The scoped search is a local implementation of the isolation property described in [LlamaIndex issue #19370](https://github.com/run-llama/llama_index/issues/19370). It does not exercise Azure, OData limits, or a 50,000-path index.

See [full traces](public_corpus_traces.jsonl) and [machine-readable results](public_corpus_validation.json).
