from retrieval import ChunkConfig

OVERLAP_AUDIT_CONFIGS = {
    f"fixed32_overlap{overlap}": ChunkConfig("fixed", 32, overlap)
    for overlap in (0, 8, 16, 24)
}
