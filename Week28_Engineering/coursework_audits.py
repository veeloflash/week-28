"""Run the additional Week 28 coursework audits and write auditable artifacts.

From Week28_Engineering, run:
    python coursework_audits.py --embedding minilm

The script uses the existing benchmark helpers and writes CSV/Markdown artifacts
under results. It does not change the held-out query set or the R0-R4 baseline.
"""
import argparse
import csv
import json
from pathlib import Path

from benchmark import STAGES, average, load_queries, measure, summarize, table
from retrieval import CHUNK_CONFIGS, ROOT, ChunkConfig, Index, identifiers, load_sources, make_embedder


def write_csv(path, rows):
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(data, output, backend):
    sources = load_sources(data)
    dev = load_queries(data / "queries.json", sources)
    dev = [case for case in dev if case["split"] == "dev"]
    test = [case for case in load_queries(data / "queries.json", sources) if case["split"] == "test"]
    embedder = make_embedder(sources, backend)
    output.mkdir(parents=True, exist_ok=True)

    # Overlap audit: same fixed chunk size, only overlap varies.
    overlap_results = []
    for overlap in (0, 8, 16, 24):
        name = f"fixed32_overlap{overlap}"
        index = Index(sources, ChunkConfig("fixed", 32, overlap), embedder)
        rows = measure(index, dev, STAGES["R0"])
        summary = summarize(rows)
        summary.update({"config": name, "chunk_count": len(index.chunks), "chunk_size": 32,
                        "overlap": overlap})
        overlap_results.append(summary)
    write_csv(output / "overlap_cost_audit.csv", overlap_results)

    # Compare retriever outcomes per held-out query; candidates stay separate
    # for sparse/dense controls, making rescue attribution explicit.
    index = Index(sources, CHUNK_CONFIGS["sections"], embedder)
    rescue_rows = []
    for case in test:
        outcomes = {}
        for method in ("sparse", "dense", "hybrid"):
            row = measure(index, [case], {**STAGES["R1"], "method": method})[0]
            outcomes[method] = row
        sparse_ok = outcomes["sparse"]["recall_at_5"] == 1
        dense_ok = outcomes["dense"]["recall_at_5"] == 1
        hybrid_ok = outcomes["hybrid"]["recall_at_5"] == 1
        if sparse_ok and not dense_ok:
            interpretation = "sparse rescues dense"
        elif dense_ok and not sparse_ok:
            interpretation = "dense rescues sparse"
        elif not sparse_ok and not dense_ok and hybrid_ok:
            interpretation = "hybrid rescues both"
        elif not hybrid_ok:
            interpretation = "hybrid also misses evidence"
        else:
            interpretation = "both succeed; no exclusive rescue"
        rescue_rows.append({"query_id": case["id"], "query": case["query"],
                            "sparse_recall_at_5": outcomes["sparse"]["recall_at_5"],
                            "dense_recall_at_5": outcomes["dense"]["recall_at_5"],
                            "hybrid_recall_at_5": outcomes["hybrid"]["recall_at_5"],
                            "interpretation": interpretation})
    write_csv(output / "retriever_rescue_analysis.csv", rescue_rows)

    # Controlled reranker comparison uses the same query and candidate count;
    # report actual rank movement only, never invent a degraded example.
    rerank_rows = []
    for case in test:
        before = index.search(case["query"], **STAGES["R2"])
        after = index.search(case["query"], **STAGES["R3"])
        if before["candidates"] != after["candidates"]:
            raise AssertionError("R2/R3 candidate sets differ; comparison is invalid")
        before_row = next(row for row in measure(index, [case], STAGES["R2"]) if row["id"] == case["id"])
        after_row = next(row for row in measure(index, [case], STAGES["R3"]) if row["id"] == case["id"])
        def evidence_rank(result, expected):
            for rank, cid in enumerate(result["selected"], 1):
                chunk = index.chunks[cid]
                if any(chunk.source_id == source and chunk.start <= left and chunk.end >= right
                       for source, left, right in expected):
                    return rank
            return None
        old_rank = evidence_rank(before, case["spans"])
        new_rank = evidence_rank(after, case["spans"])
        if old_rank != new_rank:
            rerank_rows.append({"query_id": case["id"], "query": case["query"],
                                "before_rank": old_rank, "after_rank": new_rank,
                                "change": "improved" if new_rank is not None and
                                (old_rank is None or new_rank < old_rank) else "degraded",
                                "explanation": "Measured evidence rank movement; inspect the saved R2/R3 trace."})
    write_csv(output / "reranker_case_analysis.csv", rerank_rows)
    improved = sum(row["change"] == "improved" for row in rerank_rows)
    degraded = sum(row["change"] == "degraded" for row in rerank_rows)
    reranker_note = ["# Reranker case analysis", "",
                     f"Changed-rank cases: {len(rerank_rows)}; improved: {improved}; degraded: {degraded}.", "",
                     "Only measured cases are included. No cases are fabricated."]
    if improved < 5 or degraded < 5:
        reranker_note += ["", f"This benchmark produced fewer than five cases in at least one requested category "
                          f"(improved={improved}, degraded={degraded}). The requirement is not met by this run; "
                          "add difficult, evidence-grounded distractor/adversarial queries and rerun before claiming completion."]
    (output / "reranker_case_analysis.md").write_text("\n".join(reranker_note) + "\n", encoding="utf-8")

    overlap_table = ["# Overlap cost audit", "", "All runs use fixed 32-word chunks; only overlap changes.", "",
                     "| Overlap | Chunks | Duplicate fraction | Recall@5 | MRR@5 | Context tokens |",
                     "|---:|---:|---:|---:|---:|---:|"]
    for row in overlap_results:
        overlap_table.append(f"| {row['overlap']} | {row['chunk_count']} | {row['duplicate_fraction']:.4f} | "
                             f"{row['recall_at_5']:.4f} | {row['mrr_at_5']:.4f} | {row['context_tokens']:.1f} |")
    (output / "overlap_cost_audit.md").write_text("\n".join(overlap_table) + "\n", encoding="utf-8")

    rescue_md = ["# Sparse/dense/hybrid rescue analysis", "",
                 "| Query | Sparse | Dense | Hybrid | Interpretation |", "|---|---:|---:|---:|---|"]
    for row in rescue_rows:
        rescue_md.append(f"| {row['query_id']} | {row['sparse_recall_at_5']} | {row['dense_recall_at_5']} | "
                         f"{row['hybrid_recall_at_5']} | {row['interpretation']} |")
    (output / "retriever_rescue_analysis.md").write_text("\n".join(rescue_md) + "\n", encoding="utf-8")
    print(f"Wrote overlap, retriever-rescue, and reranker case audits to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--embedding", choices=("latent", "minilm"), default="minilm")
    args = parser.parse_args()
    run(args.data, args.output, args.embedding)
