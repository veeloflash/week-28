"""Generate and validate the additional Week 28 coursework audits.

Run from Week28_Engineering:
    python coursework_audits.py --embedding minilm

The held-out benchmark is untouched. Boundary questions use a separate fixture.
"""
import argparse
import csv
import json
from pathlib import Path

from benchmark import STAGES, load_queries, measure, summarize
from conflict_detection import apply_conflict_detection
from retrieval import CHUNK_CONFIGS, ROOT, ChunkConfig, Index, load_sources, make_embedder


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


def run(data, output, backend):
    sources = load_sources(data)
    cases = load_queries(data / "queries.json", sources)
    dev = [case for case in cases if case["split"] == "dev"]
    test = [case for case in cases if case["split"] == "test"]
    embedder = make_embedder(sources, backend)
    output.mkdir(parents=True, exist_ok=True)

    # Overlap cost audit: same 32-word chunk size; only overlap changes.
    overlap_rows = []
    for overlap in (0, 8, 16, 24):
        index = Index(sources, ChunkConfig("fixed", 32, overlap), embedder)
        stats = summarize(measure(index, dev, STAGES["R0"]))
        overlap_rows.append({"config": f"fixed32_overlap{overlap}", "chunk_size": 32,
                             "overlap": overlap, "chunk_count": len(index.chunks),
                             "duplicate_percent": duplicate_percent(index),
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

    # Dedicated 12–15-question lab; separate from existing dev/test questions.
    boundary_sources = load_sources(data / "chunk_boundary")
    boundary_cases = load_queries(data / "chunk_boundary_queries.json", boundary_sources)
    if not 12 <= len(boundary_cases) <= 15:
        raise ValueError("Chunk boundary lab must contain 12–15 known-evidence questions.")
    configurations = {
        "fixed32_overlap0": ChunkConfig("fixed", 32, 0),
        "fixed32_overlap8": ChunkConfig("fixed", 32, 8),
        "fixed32_overlap16": ChunkConfig("fixed", 32, 16),
        "fixed32_overlap24": ChunkConfig("fixed", 32, 24),
        "sections": CHUNK_CONFIGS["sections"],
    }
    boundary_rows = []
    for name, config in configurations.items():
        index = Index(boundary_sources, config, embedder)
        for case in boundary_cases:
            row = measure(index, [case], STAGES["R0"])[0]
            boundary_rows.append({"config": name, "query_id": case["id"],
                                  "category": case["category"], "query": case["query"],
                                  "recall_at_5": row["recall_at_5"], "mrr_at_5": row["rr_at_5"],
                                  "error": row["error"], "chunk_count": len(index.chunks),
                                  "context_tokens": row["context_tokens"]})
    write_csv(output / "chunk_boundary_failure_lab.csv", boundary_rows)
    lines = ["# Chunk Boundary Failure Lab", "", f"Known-evidence questions: {len(boundary_cases)}.", "",
             "| Config | Query | Category | Recall@5 | MRR@5 | Error |", "|---|---|---|---:|---:|---|"]
    lines.extend(f"| {r['config']} | {r['query_id']} | {r['category']} | {r['recall_at_5']} | "
                 f"{r['mrr_at_5']} | {r['error']} |" for r in boundary_rows)
    (output / "chunk_boundary_failure_lab.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Per-query retriever rescues. Unanswerable questions are not called misses.
    index = Index(sources, CHUNK_CONFIGS["sections"], embedder)
    rescue_rows = []
    for case in test:
        outcomes = {method: measure(index, [case], {**STAGES["R1"], "method": method})[0]
                    for method in ("sparse", "dense", "hybrid")}
        if not case["spans"]:
            interpretation = "Unanswerable: abstention is expected; excluded from rescue/miss counts"
            sparse_ok = dense_ok = hybrid_ok = None
        else:
            sparse_ok = outcomes["sparse"]["complete"] is True
            dense_ok = outcomes["dense"]["complete"] is True
            hybrid_ok = outcomes["hybrid"]["complete"] is True
            if sparse_ok and not dense_ok:
                interpretation = "Sparse-only success: lexical/BM25 rescues dense miss"
            elif dense_ok and not sparse_ok:
                interpretation = "Dense-only success: semantic retrieval rescues sparse miss"
            elif not sparse_ok and not dense_ok and hybrid_ok:
                interpretation = "Hybrid rescues both individual retrievers"
            elif not hybrid_ok:
                interpretation = "Hybrid still misses at least one labelled evidence span"
            else:
                interpretation = "Both individual retrievers succeed; no exclusive rescue"
        rescue_rows.append({"query_id": case["id"], "query": case["query"],
                            "sparse_complete": sparse_ok, "dense_complete": dense_ok,
                            "hybrid_complete": hybrid_ok, "interpretation": interpretation})
    write_csv(output / "retriever_rescue_analysis.csv", rescue_rows)
    lines = ["# Sparse vs Dense Rescue Analysis", "",
             "| Query | Sparse | Dense | Hybrid | Interpretation |", "|---|---:|---:|---:|---|"]
    lines.extend(f"| {r['query_id']} — {r['query']} | {r['sparse_complete']} | {r['dense_complete']} | "
                 f"{r['hybrid_complete']} | {r['interpretation']} |" for r in rescue_rows)
    predicates = (
        ("Sparse rescues dense", lambda r: r["sparse_complete"] is True and r["dense_complete"] is False),
        ("Dense rescues sparse", lambda r: r["dense_complete"] is True and r["sparse_complete"] is False),
        ("Hybrid misses answerable evidence", lambda r: r["hybrid_complete"] is False),
    )
    for title, predicate in predicates:
        examples = [row["query_id"] for row in rescue_rows if predicate(row)]
        lines += ["", f"{title}: {', '.join(examples) if examples else 'No examples in this held-out set.'"]
    (output / "retriever_rescue_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Paired R2/R3 ranks, with candidate-set identity asserted for every query.
    rerank_rows = []
    for case in test:
        before = measure(index, [case], STAGES["R2"])[0]
        after = measure(index, [case], STAGES["R3"])[0]
        if before["retrieval"]["candidates"] != after["retrieval"]["candidates"]:
            raise AssertionError(f"R2/R3 candidate set differs for {case['id']}")
        if not case["spans"]:
            continue
        old_rank = next((rank for rank, cid in enumerate(before["retrieval"]["selected"], 1)
                         if cid in before["relevant_chunk_ids"]), None)
        new_rank = next((rank for rank, cid in enumerate(after["retrieval"]["selected"], 1)
                         if cid in after["relevant_chunk_ids"]), None)
        if old_rank != new_rank:
            change = "Improved" if new_rank is not None and (old_rank is None or new_rank < old_rank) else "Degraded"
            rerank_rows.append({"query_id": case["id"], "query": case["query"], "before_rank": old_rank,
                                "after_rank": new_rank, "change": change,
                                "why": "Measured relevant-chunk rank movement; inspect the paired trace and identifier/term matches."})
    write_csv(output / "reranker_case_analysis.csv", rerank_rows)
    improved = sum(row["change"] == "Improved" for row in rerank_rows)
    degraded = sum(row["change"] == "Degraded" for row in rerank_rows)
    lines = ["# Reranker Case Analysis", "", "R2/R3 candidate sets were checked for equality per answerable query.", "",
             f"Measured changed-rank cases: {len(rerank_rows)}; improved: {improved}; degraded: {degraded}.", "",
             "| Query | Before rank | After rank | Change | Why |", "|---|---:|---:|---|---|"]
    lines.extend(f"| {row['query_id']} — {row['query']} | {row['before_rank']} | {row['after_rank']} | "
                 f"{row['change']} | {row['why']} |" for row in rerank_rows)
    if improved < 5 or degraded < 5:
        lines += ["", f"Current set produced fewer than five cases in at least one category (improved={improved}, degraded={degraded}).",
                  "No cases were fabricated. Add difficult, evidence-grounded distractor/adversarial queries and rerun.",
                  "The automated why field is an inspection cue; it does not claim that a human has completed the required case review."]
    (output / "reranker_case_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Conflict lab: trusted same-product sources have equal authority/date/version.
    conflict_dir = data / "conflict_case"
    conflict_sources = load_sources(conflict_dir)
    conflict_index = Index(conflict_sources, CHUNK_CONFIGS["sections"], embedder)
    query = "What is the AX-17 upload limit?"
    result = conflict_index.search(query, **STAGES["R1"])
    answer = conflict_index.answer(result)
    metadata = json.loads((conflict_dir / "source_metadata.json").read_text(encoding="utf-8"))
    answer = apply_conflict_detection(conflict_index, result, answer, metadata)
    conflict_report = {"query": query, "status": answer["status"], "passages": answer["passages"],
                       "answer": answer["answer"], "expected_status": "conflicting_evidence"}
    if answer["status"] != "conflicting_evidence" or len(answer["passages"]) != 2:
        raise AssertionError("Conflict audit did not return both contradictory trusted citations.")
    (output / "conflict_detection.json").write_text(json.dumps(conflict_report, indent=2), encoding="utf-8")

    # Update the formal report, preserving baseline data and clearly distinguishing
    # a public requirement reference from a commissioned client engagement.
    report_path = output / "Retrieval_Optimization_Report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        old = ("This is a simulated support client. Its search has to find the right manual passage even when "
               "two devices share an error code, or when a customer describes a problem in their own words.")
        new = ("This is a public-requirement-aligned prototype, not a commissioned client delivery. It references "
               "LlamaIndex issue #19370 (created 2025-07-09), a public report about RAG folder filtering leaking "
               "unselected paths. The AX-17/AX-18 corpus is synthetic and remains a controlled test fixture; no real "
               "client corpus has been validated. See `real_client_requirement.md` for source, requirement summary, "
               "client problem, and acceptance criteria.")
        report = report.replace(old, new)
        sections = [
            ("## Overlap cost audit", "\n\n## Overlap cost audit\n\nSee `overlap_cost_audit.md` and `.csv`; all runs keep chunk size 32 and compare overlap 0, 8, 16, and 24.\n"),
            ("## Chunk boundary failure lab", "\n\n## Chunk boundary failure lab\n\nA separate 12-question labeled fixture measures heading/paragraph, table header/row, code/explanation, multi-fact, long-section, overlap-rescue, and section-aware cases. It does not replace the 24 held-out questions. See `chunk_boundary_failure_lab.md` and `.csv`.\n"),
            ("## Reranker case inspection", "\n\n## Reranker case inspection\n\nR2/R3 candidate-set equality is asserted per query. See `reranker_case_analysis.md`. The artifact reports measured case counts and explicitly leaves the 5+5 requirement pending if the corpus does not produce enough examples; automated notes are not human inspection.\n"),
            ("## Retriever rescue cases", "\n\n## Retriever rescue cases\n\nPer-query sparse, dense, and hybrid outcomes, including individual retriever rescues and hybrid misses, are in `retriever_rescue_analysis.md`. Unanswerable cases are excluded from miss counts.\n"),
            ("## Trusted-source conflict detection", "\n\n## Trusted-source conflict detection\n\nA separate two-manual AX-17 fixture checks contradictory trusted upload limits (20 MB vs 40 MB). Equal product, authority, publication date, and version precedence must produce `conflicting_evidence` and both citations. See `conflict_detection.json`.\n"),
        ]
        for heading, section in sections:
            if heading not in report:
                report += section
        report_path.write_text(report, encoding="utf-8")

    print(f"Generated audit artifacts in {output}. Human reranker review remains pending if the 5+5 minimum is not met.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--embedding", choices=("latent", "minilm"), default="minilm")
    args = parser.parse_args()
    run(args.data, args.output, args.embedding)
