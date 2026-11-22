"""Teaching-level conflict detection for versioned retrieval evidence."""
import re

from retrieval import identifiers

UPLOAD_LIMIT = re.compile(r"uploads?\s+up\s+to\s+(\d+(?:\.\d+)?)\s*MB", re.I)


def _version_key(value):
    numbers = re.findall(r"\d+", value or "")
    return tuple(int(part) for part in numbers) or (0,)


def apply_conflict_detection(index, result, answer, source_metadata):
    """Resolve a uniquely newer/more authoritative claim, else surface conflict.

    The teaching rule scopes claims to the queried product, then orders sources
    by authority, publication date, and version. Contradictions tied at the top
    precedence are never silently resolved.
    """
    query_ids = identifiers(result.get("query", ""))
    products = {value.casefold() for value in query_ids if value.startswith("ax-")}
    if "upload" not in result.get("query", "").casefold() or not products:
        return answer

    claims = []
    for passage in answer.get("passages", []):
        source_id = passage.get("source_id")
        metadata = source_metadata.get(source_id, {})
        product = metadata.get("product", "")
        if product and product.casefold() not in products:
            continue
        chunk = index.chunks.get(passage.get("chunk_id"))
        if chunk is None or not chunk.trusted:
            continue
        for match in UPLOAD_LIMIT.finditer(passage.get("text", "")):
            claims.append({
                "value": float(match.group(1)),
                "passage": passage,
                "precedence": (int(metadata.get("authority", 0)),
                               metadata.get("published_at", ""),
                               _version_key(chunk.version)),
            })

    if len({claim["value"] for claim in claims}) < 2:
        return answer
    best = max(claim["precedence"] for claim in claims)
    winners = [claim for claim in claims if claim["precedence"] == best]
    if len({claim["value"] for claim in winners}) > 1:
        passages, seen = [], set()
        for claim in claims:
            passage = claim["passage"]
            key = (passage["source_id"], passage["chunk_id"])
            if key not in seen:
                passages.append(passage)
                seen.add(key)
        return {**answer, "status": "conflicting_evidence", "passages": passages,
                "answer": "Trusted sources disagree about the upload limit. Please review both cited passages."}

    selected, seen = [], set()
    for claim in winners:
        passage = claim["passage"]
        key = (passage["source_id"], passage["chunk_id"])
        if key not in seen:
            selected.append(passage)
            seen.add(key)
    return {**answer, "status": "evidence_found", "passages": selected,
            "answer": "\n\n".join(f"{item['text']}\n[{item['citation']}]" for item in selected),
            "conflict_resolution": "selected highest source authority, publication date, then version"}
