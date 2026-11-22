# Week 28 Engineering

A local search app for product manuals with passage-level citations, hybrid retrieval, and reproducible evaluation.

## Run on Windows

Clone the repository and start the application from the project directory:

```powershell
git clone https://github.com/veeloflash/week-28.git
cd week-28\Week28_Engineering
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\fetch_model.ps1
.\run.ps1
```

Open [Manual Search](http://127.0.0.1:8028), then try **What should I do for ERR-4021 on AX-18?** The cited answer should point to the AX-18 service manual.

The model downloader verifies both downloaded files against pinned hashes. See [the pinned MiniLM model files](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/5641a7880f40ebf4035d05e60c5f9b7a9c272c84/onnx).

### Local development note

A saved local copy may include a prepared Python runtime and model. Those machine-specific files are optional and are not required by the clone-and-install instructions above.

## What the stages change

The app reads the source manifest and splits manuals into chunks with source IDs and line numbers. MiniLM ranks passages by meaning. Hybrid search adds BM25 keyword matching and reciprocal-rank fusion; later stages rerank the same candidate set and apply guarded query expansion. Answers include trusted source passages and citations.

| Stage | Change |
|---|---|
| R0 | Dense search over fixed 32-word chunks |
| R1 | Dense search over Markdown sections |
| R2 | Add BM25 and RRF |
| R3 | Rerank the same 12 candidates before keeping five |
| R4 | Add guarded query expansion |

## Results and audit status

The existing baseline uses eight development questions and 24 held-out questions. Result files live in [`Week28_Engineering/results/`](Week28_Engineering/results/):

- [Optimization report](Week28_Engineering/results/Retrieval_Optimization_Report.md)
- [Benchmark table](Week28_Engineering/results/benchmark.csv)
- [Chunk comparison](Week28_Engineering/results/chunk_comparison.csv)
- [Retrieval traces](Week28_Engineering/results/retrieval_traces.jsonl)
- [Security audit](Week28_Engineering/results/security.json)
- [Public requirement and acceptance mapping](Week28_Engineering/results/real_client_requirement.md)

The baseline reports Recall@5 of 0.864 for R0 and 1.000 for R1–R4, and MRR@5 of 1.000 for R3, on the synthetic corpus. This is a public-requirement-aligned prototype, not evidence of a commissioned client delivery or validation on real client documents.

Reproduce the existing baseline from the project directory:

```powershell
python -m unittest -v
python benchmark.py --output .\results-rerun
```

Run the additional coursework audits to generate the overlap, chunk-boundary, reranker, retriever-rescue, and conflict-detection artifacts:

```powershell
python coursework_audits.py --embedding minilm
```

The script writes result artifacts under `Week28_Engineering/results/`. Reranker 5-improved/5-degraded human inspection remains explicitly incomplete if the measured query set does not produce enough cases; no cases are fabricated.
