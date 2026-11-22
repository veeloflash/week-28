"""Generate and validate the additional Week 28 coursework audits.

Run from Week28_Engineering:
    python coursework_audits.py --embedding minilm

Boundary questions are a separate fixture; the existing held-out benchmark is untouched.
"""
import argparse
import csv
import json
from pathlib import Path

from benchmark import STAGES, load_queries, measure, summarize
from conflict_detection import apply_conflict_detection
from retrieval import CHUNK_CONFIGS, OVERLAP_AUDIT_CONFIGS, ROOT, Index, load_sources, make_embedder


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
    intervals = {}
    for chunk in index.chunks.values():
        intervals.setdefault(chunk.source_id, []).append((chunk.start, chunk.end))
    unique = 0
    for spans in intervals.values():
        right = -1
        for left, end in sorted(spans):
            unique += max(0, end - max(left, right))
            right = max(right, end)
    return round(100 * (1 - unique / total), 3) if total else 0.0


def write_case_report(path, title, rows, headers, row_formatter, note=None):
    lines = [f"# {title}", "", *headers]
    lines.extend(row_formatter(row) for row in rows)
    if note:
        lines.extend(["", note])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(data, output, backend):
    data, output = Path(data), Path(output)
    sources = load_sources(data)
    cases = load_queries(data / "queries.json", sources)
    dev = [case for case in cases if case["split"] == "dev"]
    test = [case for case in cases if case["split"] == "test"]
    embedder = make_embedder(sources, backend)
    output.mkdir(parents=True, exist_ok=True)

    # Same chunk size, only overlap varies. Keep these out of the baseline
    # CHUNK_CONFIGS so existing R0-R4 benchmark selection remains unchanged.
    overlap_rows = []
    for name, config in OVERLAP_AUDIT_CONFIGS.items():
        index = Index(sources, config, embedder)
        stats = summarize(measure(index, dev, STAGES["R0"]))
        overlap_rows.append({"config": name, "chunk_size": config.size, "overlap": config.overlap,
                             "chunk_count": len(index.chunks), "duplicate_percent": duplicate_percent(index),
                             "recall_at_5": stats["recall_at_5"], "mrr_at_5": stats["mrr_at_5"],
                             "context_tokens": stats["context_tokens"], "p50_ms": stats["p50_ms"],
                             "p95_ms": stats["p95_ms"]})
    write_csv(output / "overlap_cost_audit.csv", overlap_rows)
    lines = ["# Overlap Cost Audit", "", "All runs use 32-word fixed chunks; only overlap changes.", "",
             "| Config | Overlap | Chunk count | Duplicate % | Recall@5 | MRR@5 | Context tokens |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    lines.extend(f"| {r['config']} | {r['overlap']} | {r['chunk_count']} | {r['duplicate_percent']:.3f} | "
                 f"{r['recall_at_5']:.4f} | {r['mrr_at_5']:.4f} | {r['context_tokens']:.1f} |"
                 for r in overlap_rows)
    (output / "overlap_cost_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Dedicated 12–15-question known-evidence lab, independent of dev/test.
    boundary_sources = load_sources(data / "chunk_boundary")
    boundary_cases = load_queries(data / "chunk_boundary_queries.json", boundary_sources)
    if not 12 <= len(boundary_cases) <= 15 or any(not case["spans"] for case in boundary_cases):
        raise ValueError("Chunk boundary lab requires 12–15 questions with known evidence.")
    if any("split" not in case or "slice" not in case for case in boundary_cases):
        raise ValueError("Boundary questions must specify split and slice for the shared scorer.")
    boundary_configs = {**OVERLAP_AUDIT_CONFIGS, "sections": CHUNK_CONFIGS["sections"]}
    boundary_rows = []
    for name, config in boundary_configs.items():
        index = Index(boundary_sources, config, embedder)
        for case in boundary_cases:
            row = measure(index, [case], STAGES["R0"])[0]
            boundary_rows.append({"config": name, "query_id": case["id"], "category": case["category"],
                                  "query": case["query"], "recall_at_5": row["recall_at_5"],
                                  "mrr_at_5": row["rr_at_5"], "error": row["error"],
                                  "chunk_count": len(index.chunks), "context_tokens": row["context_tokens"]})
    write_csv(output / "chunk_boundary_failure_lab.csv", boundary_rows)
    lines = ["# Chunk Boundary Failure Lab", "", f"Known-evidence questions: {len(boundary_cases)}.", "",
             "| Config | Query | Category | Recall@5 | MRR@5 | Error |", "|---|---|---|---:|---:|---|"]
    lines.extend(f"| {r['config']} | {r['query_id']} | {r['category']} | {r['recall_at_5']} | {r['mrr_at_5']} | {r['error']} |"
                 for r in boundary_rows)
    (output / "chunk_boundary_failure_lab.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    index = Index(sources, CHUNK_CONFIGS["sections"], embedder)
    rescue_rows = []
    for case in test:
        outcomes = {method: measure(index, [case], {**STAGES["R1"], "method": method})[0]
                    for method in ("sparse", "dense", "hybrid")}
        if not case["spans"]:
            sparse_ok = dense_ok = hybrid_ok = None
            note = "Unanswerable: expected abstention; excluded from rescue/miss counts"
        else:
            sparse_ok = outcomes["sparse"]["complete"] is True
            dense_ok = outcomes["dense"]["complete"] is True
            hybrid_ok = outcomes["hybrid"]["complete"] is True
            if sparse_ok and not dense_ok:
                note = "Sparse-only success: lexical/BM25 rescues dense miss"
            elif dense_ok and not sparse_ok:
                note = "Dense-only success: semantic retrieval rescues sparse miss"
            elif not sparse_ok and not dense_ok and hybrid_ok:
                note = "Hybrid rescues both individual retrievers"
            elif not hybrid_ok:
                note = "Hybrid still misses at least one labelled evidence span"
            else:
                note = "Both individual retrievers succeed; no exclusive rescue"
        rescue_rows.append({"query_id": case["id"], "query": case["query"], "sparse_complete": sparse_ok,
                            "dense_complete": dense_ok, "hybrid_complete": hybrid_ok, "interpretation": note})
    write_csv(output / "retriever_rescue_analysis.csv", rescue_rows)
    lines = ["# Sparse vs Dense Rescue Analysis", "", "| Query | Sparse | Dense | Hybrid | Interpretation |",
             "|---|---:|---:|---:|---|"]
    lines.extend(f"| {r['query_id']} — {r['query']} | {r['sparse_complete']} | {r['dense_complete']} | "
                 f"{r['hybrid_complete']} | {r['interpretation']} |" for r in rescue_rows)
    for title, predicate in (
        ("Sparse rescues dense", lambda r: r["sparse_complete"] is True and r["dense_complete"] is False),
        ("Dense rescues sparse", lambda r: r["dense_complete"] is True and r["sparse_complete"] is False),
        ("Hybrid misses answerable evidence", lambda r: r["hybrid_complete"] is False),
    ):
        examples = [row["query_id"] for row in rescue_rows if predicate(row)]
        lines.append(f"\n{title}: {', '.join(examples) if examples else 'No examples in this held-out set.'}")
    (output / "retriever_rescue_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Use full reranked candidate ordering, not only top-5. Candidate sets must
    # be identical before the paired rank movement is attributed to reranking.
    rerank_rows = []
    for case in test:
        before = measure(index, [case], STAGES["R2"])[0]
        after = measure(index, [case], STAGES["R3"])[0]
        before_result, after_result = before["retrieval"], after["retrieval"]
        if before_result["candidates"] != after_result["candidates"]:
            raise AssertionError(f"R2/R3 candidate set differs for {case['id']}")
        if not case["spans"]:
            continue
        relevant = set(before["relevant_chunk_ids"])
        def evidence_rank(result):
            trace = sorted((entry for entry in result["trace"] if entry["chunk"]["id"] in relevant),
                           key=lambda entry: entry["final_rank"])
            return trace[0]["final_rank"] if trace else None
        old_rank, new_rank = evidence_rank(before_result), evidence_rank(after_result)
        if old_rank != new_rank:
            change = "Improved" if new_rank is not None and (old_rank is None or new_rank < old_rank) else "Degraded"
            rerank_rows.append({"query_id": case["id"], "query": case["query"], "before_rank": old_rank,
                                "after_rank": new_rank, "change": change,
                                "why": "Measured relevant candidate rank movement; inspect paired traces, exact identifiers, and query-term coverage."})
    write_csv(output / "reranker_case_analysis.csv", rerank_rows)
    improved = sum(row["change"] == "Improved" for row in rerank_rows)
    degraded = sum(row["change"] == "Degraded" for row in rerank_rows)
    lines = ["# Reranker Case Analysis", "", "R2/R3 candidate sets were checked for equality per answerable query.", "",
             f"Measured changed-rank cases: {len(rerank_rows)}; improved: {improved}; degraded: {degraded}.", "",
             "| Query | Before rank | After rank | Change | Why |", "|---|---:|---:|---|---|"]
    lines.extend(f"| {r['query_id']} — {r['query']} | {r['before_rank']} | {r['after_rank']} | {r['change']} | {r['why']} |"
                 for r in rerank_rows)
    if improved < 5 or degraded < 5:
        lines.extend(["", f"Current set produced fewer than five cases in at least one category (improved={improved}, degraded={degraded}).",
                      "No cases were fabricated. Add difficult, evidence-grounded distractor/adversarial queries and rerun.",
                      "Automated why text is an inspection cue, not completed human case review."])
    (output / "reranker_case_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    conflict_dir = data / "conflict_case"
    conflict_sources = load_sources(conflict_dir)
    conflict_index = Index(conflict_sources, CHUNK_CONFIGS["sections"], embedder)
    query = "What is the AX-17 upload limit?"
    result = conflict_index.search(query, **STAGES["R1"])
    answer = conflict_index.answer(result)
    metadata = json.loads((conflict_dir / "source_metadata.json").read_text(encoding="utf-8"))
    answer = apply_conflict_detection(conflict_index, result, answer, metadata)
    if answer["status"] != "conflicting_evidence" or len(answer["passages"]) != 2:
        raise AssertionError("Conflict audit did not return both contradictory trusted citations.")
    conflict_report = {"query": query, "status": answer["status"], "passages": answer["passages"],
                       "answer": answer["answer"], "expected_status": "conflicting_evidence"}
    (output / "conflict_detection.json").write_text(json.dumps(conflict_report, indent=2), encoding="utf-8")

    status = {"audit_command": "python coursework_audits.py --embedding minilm",
              "reranker_improved_cases": improved, "reranker_degraded_cases": degraded,
              "reranker_human_review_complete": False, "boundary_question_count": len(boundary_cases),
              "overlap_values": [row["overlap"] for row in overlap_rows],
              "real_client_corpus_validated": False}
    (output / "coursework_audit_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(f"Audit artifacts generated in {output}; 5+5 reranker review is not claimed unless measured and human-reviewed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--embedding", choices=("latent", "minilm"), default="minilm")
    args = parser.parse_args()
    run(args.data, args.output, args.embedding)
