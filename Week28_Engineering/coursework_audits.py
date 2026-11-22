"""Generate and validate the additional Week 28 coursework audits.

Run from Week28_Engineering:
    python coursework_audits.py --embedding minilm

The held-out benchmark is untouched. Boundary questions use a separate fixture.
"""
import argparse
import csv
import json
import re
from pathlib import Path

from benchmark import STAGES, load_queries, measure, summarize
from conflict_detection import apply_conflict_detection
from retrieval import CHUNK_CONFIGS, ROOT, ChunkConfig, Index, Source, load_sources, make_embedder


def write_csv(path, rows):
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def duplicate_percent(index):
    total = sum(chunk.end - chunk.start for chunk in index.chunks.values())
    covered = {}
    for chunk in index.chunks.values():
        covered.setdefault(chunk.source_id, []).append((chunk.start, chunk.end))
    unique = 0
    for spans in covered.values():
        right = -1
        for left, end in sorted(spans):
            unique += max(0, end - max(left, right))
            right = max(right, end)
    return round(100 * (1 - unique / total), 3) if total else 0.0


def write_report_updates(output, overlap_rows, boundary_rows, rescue_rows, rerank_rows, conflict_result):
    report_path = output / "Retrieval_Optimization_Report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        report = report.replace(
            "This is a simulated support client. Its search has to find the right manual passage even when two devices share an error code, or when a customer describes a problem in their own words.",
            "The public requirement reference is LlamaIndex issue #19370 (created 2025-07-09), a report that RAG folder filtering can expose content from unselected paths. This project maps that problem to trusted-source filtering, provenance, and auditable retrieval traces. The author did not commission this project. AX-17/AX-18 documents are synthetic benchmark fixtures, not a real client corpus. See `real_client_requirement.md` for source, original requirement summary, client problem, and acceptance criteria.")
        sections = [
            "\n## Overlap cost audit\n\nThe controlled comparison holds chunk size at 32 words and varies overlap only. See `overlap_cost_audit.md` and `.csv`.\n",
            "\n## Chunk boundary failure lab\n\nA separate 12-question known-evidence fixture covers headings, table header/row, code/explanation, multi-fact boundaries, long sections, overlap rescue, and section-aware rescue. It does not replace the 24 held-out benchmark. See `chunk_boundary_failure_lab.md` and `.csv`.\n",
            "\n## Reranker case inspection\n\nR2 and R3 are compared with the same candidate set. Case-level measured rank movements are in `reranker_case_analysis.md`; category counts below five are explicitly reported rather than fabricated. Human inspection is still required for the listed explanations.\n",
            "\n## Retriever rescue cases\n\nPer-query sparse, dense, and hybrid outcomes, including exclusive rescues and hybrid misses, are in `retriever_rescue_analysis.md`.\n",
            "\n## Trusted-source conflict detection\n\nThe separate AX-17 conflict fixture has two equally authoritative trusted manuals stating 20 MB and 40 MB. The audit must return `conflicting_evidence` with both citations when precedence cannot distinguish them. See `conflict_detection.json`.\n",
        ]
        for section in sections:
            if section.splitlines()[1].strip() not in report:
                report += section
        report_path.write_text(report, encoding="utf-8")


def run(data, output, backend):
    sources = load_sources(data)
    cases = load_queries(data / "queries.json", sources)
    dev = [case for case in cases if case["split"] == "dev"]
    test = [case for case in cases if case["split"] == "test"]
    embedder = make_embedder(sources, backend)
    output.mkdir(parents=True, exist_ok=True)

    overlap_rows = []
    for overlap in (0, 8, 16, 24):
        index = Index(sources, ChunkConfig("fixed", 32, overlap), embedder)
        metrics = summarize(measure(index, dev, STAGES["R0"]))
        overlap_rows.append({"config": f"fixed32_overlap{overlap}", "chunk_size": 32,
                             "overlap": overlap, "chunk_count": len(index.chunks),
                             "duplicate_percent": duplicate_percent(index),
                             "recall_at_5": metrics["recall_at_5"], "mrr_at_5": metrics["mrr_at_5"],
                             "context_tokens": metrics["context_tokens"], "p50_ms": metrics["p50_ms"],
                             "p95_ms": metrics["p95_ms"]})
    write_csv(output / "overlap_cost_audit.csv", overlap_rows)
    overlap_md = ["# Overlap Cost Audit", "", "All runs use 32-word fixed chunks; only overlap changes.", "",
                  "| Config | Overlap | Chunk count | Duplicate % | Recall@5 | MRR@5 | Context tokens |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
    overlap_md.extend(f"| {r['config']} | {r['overlap']} | {r['chunk_count']} | {r['duplicate_percent']:.3f} | "
                      f"{r['recall_at_5']:.4f} | {r['mrr_at_5']:.4f} | {r['context_tokens']:.1f} |"
                      for r in overlap_rows)
    (output / "overlap_cost_audit.md").write_text("\n".join(overlap_md) + "\n", encoding="utf-8")

    boundary_dir = data / "chunk_boundary"
    boundary_sources = load_sources(boundary_dir)
    boundary_cases = load_queries(data / "chunk_boundary_queries.json", boundary_sources)
    if not 12 <= len(boundary_cases) <= 15:
        raise ValueError("Chunk boundary lab must contain 12–15 known-evidence questions.")
    boundary_index_specs = {
        "fixed32_overlap0": ChunkConfig("fixed", 32, 0),
        "fixed32_overlap8": ChunkConfig("fixed", 32, 8),
        "fixed32_overlap16": ChunkConfig("fixed", 32, 16),
        "sections": CHUNK_CONFIGS["sections"],
    }
    boundary_rows = []
    for name, config in boundary_index_specs.items():
        index = Index(boundary_sources, config, embedder)
        for case in boundary_cases:
            row = measure(index, [case], STAGES["R0"])[0]
            boundary_rows.append({"config": name, "query_id": case["id"], "category": case["category"],
                                  "query": case["query"], "recall_at_5": row["recall_at_5"],
                                  "mrr_at_5": row["rr_at_5"], "error": row["error"],
                                  "chunk_count": len(index.chunks), "context_tokens": row["context_tokens"]})
    write_csv(output / "chunk_boundary_failure_lab.csv", boundary_rows)
    boundary_md = ["# Chunk Boundary Failure Lab", "", f"Known-evidence questions: {len(boundary_cases)}.", "",
                   "| Config | Query | Category | Recall@5 | MRR@5 | Error |", "|---|---|---|---:|---:|---|"]
    boundary_md.extend(f"| {r['config']} | {r['query_id']} | {r['category']} | {r['recall_at_5']} | "
                       f"{r['mrr_at_5']} | {r['error']} |" for r in boundary_rows)
    (output / "chunk_boundary_failure_lab.md").write_text("\n".join(boundary_md) + "\n", encoding="utf-8")

    index = Index(sources, CHUNK_CONFIGS["sections"], embedder)
    rescue_rows = []
    for case in test:
        outcomes = {method: measure(index, [case], {**STAGES["R1"], "method": method})[0]
                    for method in ("sparse", "dense", "hybrid")}
        sparse_ok = outcomes["sparse"]["complete"] is True
        dense_ok = outcomes["dense"]["complete"] is True
        hybrid_ok = outcomes["hybrid"]["complete"] is True
        if sparse_ok and not dense_ok:
            note = "Sparse-only success: lexical/BM25 rescue"
        elif dense_ok and not sparse_ok:
            note = "Dense-only success: semantic rescue"
        elif not sparse_ok and not dense_ok and hybrid_ok:
            note = "Hybrid rescues both individual retrievers"
        elif not hybrid_ok:
            note = "Hybrid still fails to retrieve all labelled evidence"
        else:
            note = "Both individual retrievers succeed; no exclusive rescue"
        rescue_rows.append({"query_id": case["id"], "query": case["query"],
                            "sparse_complete": sparse_ok, "dense_complete": dense_ok,
                            "hybrid_complete": hybrid_ok, "interpretation": note})
    write_csv(output / "retriever_rescue_analysis.csv", rescue_rows)
    rescue_md = ["# Sparse vs Dense Rescue Analysis", "",
                 "| Query | Sparse | Dense | Hybrid | Interpretation |", "|---|---:|---:|---:|---|"]
    rescue_md.extend(f"| {r['query_id']} — {r['query']} | {r['sparse_complete']} | {r['dense_complete']} | "
                     f"{r['hybrid_complete']} | {r['interpretation']} |" for r in rescue_rows)
    for category, label in (("Sparse-only success", "sparse_rescues_dense"),
                            ("Dense-only success", "dense_rescues_sparse"),
                            ("Hybrid miss", "hybrid_failures")):
        found = [r["query_id"] for r in rescue_rows if
                 (r["sparse_complete"] and not r["dense_complete"] if label == "sparse_rescues_dense" else
                  r["dense_complete"] and not r["sparse_complete"] if label == "dense_rescues_sparse" else
                  not r["hybrid_complete"])]
        rescue_md += ["", f"{category}: {', '.join(found) if found else 'No examples in this set.'"]
    (output / "retriever_rescue_analysis.md").write_text("\n".join(rescue_md) + "\n", encoding="utf-8")

    # Reranker case analysis: score evidence rank from measured selections.
    rerank_rows = []
    for case in test:
        before = measure(index, [case], STAGES["R2"])[0]
        after = measure(index, [case], STAGES["R3"])[0]
        if before["retrieval"]["candidates"] != after["retrieval"]["candidates"]:
            raise AssertionError(f"R2/R3 candidate set differs for {case['id']}")
        old_rank = next((rank for rank, cid in enumerate(before["retrieval"]["selected"], 1)
                         if cid in before["relevant_chunk_ids"]), None)
        new_rank = next((rank for rank, cid in enumerate(after["retrieval"]["selected"], 1)
                         if cid in after["relevant_chunk_ids"]), None)
        if old_rank != new_rank:
            change = "improved" if new_rank is not None and (old_rank is None or new_rank < old_rank) else "degraded"
            rerank_rows.append({"query_id": case["id"], "query": case["query"],
                                "before_rank": old_rank, "after_rank": new_rank, "change": change,
                                "why": "Measured relevant-chunk rank changed under controlled R3 reranking; inspect trace and query/chunk identifier overlap."})
    write_csv(output / "reranker_case_analysis.csv", rerank_rows)
    improved = sum(row["change"] == "improved" for row in rerank_rows)
    degraded = sum(row["change"] == "degraded" for row in rerank_rows)
    rerank_md = ["# Reranker Case Analysis", "", "R2/R3 candidate sets were checked for equality per query.", "",
                 f"Measured rank changes: {len(rerank_rows)}; improved: {improved}; degraded: {degraded}.", "",
                 "| Query | Before rank | After rank | Change | Why / inspection note |", "|---|---:|---:|---|---|"]
    rerank_md.extend(f"| {r['query_id']} — {r['query']} | {r['before_rank']} | {r['after_rank']} | {r['change']} | {r['why']} |"
                     for r in rerank_rows)
    if improved < 5 or degraded < 5:
        rerank_md += ["", f"Current measured benchmark produced fewer than five cases in at least one category "
                      f"(improved={improved}, degraded={degraded}). No cases were fabricated. Add and evaluate difficult, evidence-grounded distractor/adversarial queries before claiming the 5+5 inspection requirement is complete.",
                      "The why column is an automated inspection cue, not a claim that a human has completed review."]
    (output / "reranker_case_analysis.md").write_text("\n".join(rerank_md) + "\n", encoding="utf-8")

    conflict_dir = data / "conflict_case"
    conflict_sources = load_sources(conflict_dir)
    conflict_index = Index(conflict_sources, CHUNK_CONFIGS["sections"], embedder)
    conflict_query = "What is the AX-17 upload limit?"
    conflict_result = conflict_index.search(conflict_query, **STAGES["R1"])
    conflict_answer = conflict_index.answer(conflict_result)
    metadata = json.loads((conflict_dir / "source_metadata.json").read_text(encoding="utf-8"))
    conflict_answer = apply_conflict_detection(conflict_index, conflict_result, conflict_answer, metadata)
    conflict_report = {"query": conflict_query, "status": conflict_answer["status"],
                       "passages": conflict_answer["passages"], "answer": conflict_answer["answer"],
                       "expected_status": "conflicting_evidence"}
    if conflict_answer["status"] != "conflicting_evidence" or len(conflict_answer["passages"]) != 2:
        raise AssertionError("Conflict audit did not return both contradictory trusted citations.")
    (output / "conflict_detection.json").write_text(json.dumps(conflict_report, indent=2), encoding="utf-8")
    write_report_updates(output, overlap_rows, boundary_rows, rescue_rows, rerank_rows, conflict_report)
    print("Audit artifacts generated; reranker 5+5 requirement remains explicitly pending if the measured cases are insufficient.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--embedding", choices=("latent", "minilm"), default="minilm")
    args = parser.parse_args()
    run(args.data, args.output, args.embedding)
