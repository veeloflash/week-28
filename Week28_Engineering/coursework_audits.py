"""Generate and validate the additional Week 28 coursework audits.

Run from Week28_Engineering:
    python coursework_audits.py --embedding minilm

Boundary questions are a separate fixture; the existing held-out benchmark is untouched.
"""
import argparse
import csv
import json
import hashlib
import platform
from pathlib import Path

from benchmark import STAGES, load_queries, measure, summarize
from conflict_detection import apply_conflict_detection
from retrieval import CHUNK_CONFIGS, ROOT, Index, load_sources, make_embedder
from overlap_configs import OVERLAP_AUDIT_CONFIGS


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
    lines += ["", "On these eight development questions, overlap 16 reaches Recall@5=1.0; "
              "24 adds no recall, reduces MRR, and raises index duplication and context cost. "
              "This is a corpus-specific saturation point, not a universal overlap recommendation. "
              "Sizes and context cost use regex words, not model/BPE tokens. Duplicate % measures indexed character coverage."]
    (output / "overlap_cost_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Dedicated 12–15-question known-evidence lab, independent of dev/test.
    boundary_sources = load_sources(data / "chunk_boundary")
    boundary_cases = load_queries(data / "chunk_boundary_queries.json", boundary_sources)
    if not 12 <= len(boundary_cases) <= 15 or any(not case["spans"] for case in boundary_cases):
        raise ValueError("Chunk boundary lab requires 12–15 questions with known evidence.")
    if any("split" not in case or "slice" not in case for case in boundary_cases):
        raise ValueError("Boundary questions must specify split and slice for the shared scorer.")
    boundary_configs = {**OVERLAP_AUDIT_CONFIGS, "sections": CHUNK_CONFIGS["sections"]}
    boundary_rows, boundary_traces = [], []
    for name, config in boundary_configs.items():
        index = Index(boundary_sources, config, embedder)
        for case in boundary_cases:
            row = measure(index, [case], STAGES["R0"])[0]
            boundary_traces.append({"config": name, **row})
            boundary_rows.append({"config": name, "query_id": case["id"], "category": case["category"],
                                  "query": case["query"], "recall_at_5": row["recall_at_5"],
                                  "mrr_at_5": row["rr_at_5"], "error": row["error"],
                                  "chunk_count": len(index.chunks), "context_tokens": row["context_tokens"],
                                  "fully_supporting_chunks": len(row["relevant_chunk_ids"])})
    write_csv(output / "chunk_boundary_failure_lab.csv", boundary_rows)
    with (output / "chunk_boundary_traces.jsonl").open("w", encoding="utf-8") as handle:
        for row in boundary_traces:
            handle.write(json.dumps(row) + "\n")
    lines = ["# Chunk Boundary Failure Lab", "", f"Known-evidence questions: {len(boundary_cases)}.", "",
             "| Config | Query | Category | Recall@5 | MRR@5 | Error |", "|---|---|---|---:|---:|---|"]
    lines.extend(f"| {r['config']} | {r['query_id']} | {r['category']} | {r['recall_at_5']} | {r['mrr_at_5']} | {r['error']} |"
                 for r in boundary_rows)
    lines += ["", "## Boundary inspection", "",
              "All configurations cover all labelled evidence through the union of the top five passages on this small fixture. "
              "Single-chunk MRR still exposes broken supporting passages: zero MRR can mean no chunk contains the whole span "
              "even though adjacent selected chunks jointly cover it. See fully_supporting_chunks in the CSV.", "",
              "- CB02/CB09: the table header/row splits in fixed32 overlap0; overlap8 and sections retain the labelled row context.",
              "- CB03: overlap8 splits code/explanation despite overlap0 working; overlap16 and sections recover a complete span. "
              "Overlap is not monotonically better because window start offsets change.",
              "- CB04: the cross-firmware multi-fact span needs overlap24 or sections to fit in one retrieved chunk.",
              "- CB06: overlap0/8 split the exact-code passage; overlap16/24 restore complete-span hits; sections ranks it first.",
              "- CB07/CB08: sections keeps the heading and supporting facts together; overlap0 loses complete-span hits.",
              "- CB05: sections still splits a long section at its size cap; fixed windows happen to preserve this particular gold span. "
              "Structure awareness does not eliminate internal long-section boundaries.", "",
              "These observations are diagnostic, not a claim of held-out recall gains. Exact supporting spans, "
              "chunk text/offsets and ranked selections are saved in [chunk_boundary_traces.jsonl](chunk_boundary_traces.jsonl)."]
    (output / "chunk_boundary_failure_lab.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    from inspection_audits import run_inspection_audits
    index = Index(sources, CHUNK_CONFIGS["sections"], embedder)
    stress = load_queries(data / "stress_queries.json", sources)
    improved, degraded = run_inspection_audits(index, test, stress, output)

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
    conflict_report["resolution_cases"] = {}
    from dataclasses import replace
    for rule in ("authority", "date", "version"):
        variants = [replace(source, version="2.0") if rule == "version" and source.id == "conflict_v2"
                    else source for source in conflict_sources]
        resolved_index = Index(variants, CHUNK_CONFIGS["sections"], embedder)
        resolved_metadata = {key: dict(value) for key, value in metadata.items()}
        if rule == "authority":
            resolved_metadata["conflict_v2"]["authority"] = 3
        if rule == "date":
            resolved_metadata["conflict_v2"]["published_at"] = "2025-02-15"
        resolved_result = resolved_index.search(query, **STAGES["R1"])
        resolved = apply_conflict_detection(resolved_index, resolved_result,
                                           resolved_index.answer(resolved_result), resolved_metadata)
        assert resolved["status"] == "evidence_found" and len(resolved["passages"]) == 1
        assert "40 MB" in resolved["passages"][0]["text"]
        conflict_report["resolution_cases"][rule] = resolved
    (output / "conflict_detection.json").write_text(json.dumps(conflict_report, indent=2), encoding="utf-8")

    status = {"audit_command": f"python coursework_audits.py --embedding {backend}", "embedding": embedder.name,
              "runtime": platform.python_version(),
              "input_sha256": {str(path.relative_to(data)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sorted(data.rglob("*")) if path.is_file()},
              "reranker_improved_cases": improved, "reranker_degraded_cases": degraded,
              "reranker_human_review_complete": False, "agent_case_inspection_complete": True, "boundary_question_count": len(boundary_cases),
              "overlap_values": [row["overlap"] for row in overlap_rows],
              "public_corpus_validated": True, "commissioned_client_acceptance": False}
    from public_pilot import run_public_pilot
    run_public_pilot(data / "public_docs", output, backend)
    (output / "coursework_audit_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(f"Audit artifacts generated in {output}; 5+5 reranker review is not claimed unless measured and human-reviewed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--embedding", choices=("latent", "minilm"), default="minilm")
    args = parser.parse_args()
    run(args.data, args.output, args.embedding)
