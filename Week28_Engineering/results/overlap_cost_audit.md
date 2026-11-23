# Overlap Cost Audit

All runs use 32-word fixed chunks; only overlap changes.

| Config | Overlap | Chunk count | Duplicate % | Recall@5 | MRR@5 | Context tokens |
|---|---:|---:|---:|---:|---:|---:|
| fixed32_overlap0 | 0 | 20 | 0.000 | 0.8750 | 0.6250 | 151.4 |
| fixed32_overlap8 | 8 | 24 | 21.879 | 0.8750 | 0.5625 | 156.2 |
| fixed32_overlap16 | 16 | 33 | 45.105 | 1.0000 | 0.7083 | 159.1 |
| fixed32_overlap24 | 24 | 61 | 70.833 | 1.0000 | 0.6667 | 160.0 |

On these eight development questions, overlap 16 reaches Recall@5=1.0; 24 adds no recall, reduces MRR, and raises index duplication and context cost. This is a corpus-specific saturation point, not a universal overlap recommendation. Sizes and context cost use regex words, not model/BPE tokens. Duplicate % measures indexed character coverage.
