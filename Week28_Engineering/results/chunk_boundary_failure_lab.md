# Chunk Boundary Failure Lab

Known-evidence questions: 12.

| Config | Query | Category | Recall@5 | MRR@5 | Error |
|---|---|---|---:|---:|---|
| fixed32_overlap0 | CB01 | heading_paragraph | 1.0 | 1.0 | ok |
| fixed32_overlap0 | CB02 | table_header_row | 1.0 | 0 | ok |
| fixed32_overlap0 | CB03 | code_explanation | 1.0 | 1.0 | ok |
| fixed32_overlap0 | CB04 | multi_fact_boundary | 1.0 | 0 | ok |
| fixed32_overlap0 | CB05 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap0 | CB06 | overlap_rescue | 1.0 | 0 | ok |
| fixed32_overlap0 | CB07 | section_aware_rescue | 1.0 | 0 | ok |
| fixed32_overlap0 | CB08 | heading_paragraph | 1.0 | 0 | ok |
| fixed32_overlap0 | CB09 | table_header_row | 1.0 | 0 | ok |
| fixed32_overlap0 | CB10 | code_explanation | 1.0 | 1.0 | ok |
| fixed32_overlap0 | CB11 | multi_fact_boundary | 1.0 | 1.0 | ok |
| fixed32_overlap0 | CB12 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB01 | heading_paragraph | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB02 | table_header_row | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB03 | code_explanation | 1.0 | 0 | ok |
| fixed32_overlap8 | CB04 | multi_fact_boundary | 1.0 | 0 | ok |
| fixed32_overlap8 | CB05 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB06 | overlap_rescue | 1.0 | 0 | ok |
| fixed32_overlap8 | CB07 | section_aware_rescue | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB08 | heading_paragraph | 1.0 | 0 | ok |
| fixed32_overlap8 | CB09 | table_header_row | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB10 | code_explanation | 1.0 | 0 | ok |
| fixed32_overlap8 | CB11 | multi_fact_boundary | 1.0 | 1.0 | ok |
| fixed32_overlap8 | CB12 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB01 | heading_paragraph | 1.0 | 0.5 | ok |
| fixed32_overlap16 | CB02 | table_header_row | 1.0 | 0.5 | ok |
| fixed32_overlap16 | CB03 | code_explanation | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB04 | multi_fact_boundary | 1.0 | 0 | ok |
| fixed32_overlap16 | CB05 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB06 | overlap_rescue | 1.0 | 0.3333333333333333 | ok |
| fixed32_overlap16 | CB07 | section_aware_rescue | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB08 | heading_paragraph | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB09 | table_header_row | 1.0 | 0.5 | ok |
| fixed32_overlap16 | CB10 | code_explanation | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB11 | multi_fact_boundary | 1.0 | 1.0 | ok |
| fixed32_overlap16 | CB12 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB01 | heading_paragraph | 1.0 | 0.3333333333333333 | ok |
| fixed32_overlap24 | CB02 | table_header_row | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB03 | code_explanation | 1.0 | 0.5 | ok |
| fixed32_overlap24 | CB04 | multi_fact_boundary | 1.0 | 0.5 | ok |
| fixed32_overlap24 | CB05 | long_section | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB06 | overlap_rescue | 1.0 | 0.2 | ok |
| fixed32_overlap24 | CB07 | section_aware_rescue | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB08 | heading_paragraph | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB09 | table_header_row | 1.0 | 0.5 | ok |
| fixed32_overlap24 | CB10 | code_explanation | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB11 | multi_fact_boundary | 1.0 | 1.0 | ok |
| fixed32_overlap24 | CB12 | long_section | 1.0 | 1.0 | ok |
| sections | CB01 | heading_paragraph | 1.0 | 1.0 | ok |
| sections | CB02 | table_header_row | 1.0 | 1.0 | ok |
| sections | CB03 | code_explanation | 1.0 | 1.0 | ok |
| sections | CB04 | multi_fact_boundary | 1.0 | 1.0 | ok |
| sections | CB05 | long_section | 1.0 | 0 | ok |
| sections | CB06 | overlap_rescue | 1.0 | 1.0 | ok |
| sections | CB07 | section_aware_rescue | 1.0 | 1.0 | ok |
| sections | CB08 | heading_paragraph | 1.0 | 1.0 | ok |
| sections | CB09 | table_header_row | 1.0 | 1.0 | ok |
| sections | CB10 | code_explanation | 1.0 | 1.0 | ok |
| sections | CB11 | multi_fact_boundary | 1.0 | 1.0 | ok |
| sections | CB12 | long_section | 1.0 | 1.0 | ok |

## Boundary inspection

All configurations cover all labelled evidence through the union of the top five passages on this small fixture. Single-chunk MRR still exposes broken supporting passages: zero MRR can mean no chunk contains the whole span even though adjacent selected chunks jointly cover it. See fully_supporting_chunks in the CSV.

- CB02/CB09: the table header/row splits in fixed32 overlap0; overlap8 and sections retain the labelled row context.
- CB03: overlap8 splits code/explanation despite overlap0 working; overlap16 and sections recover a complete span. Overlap is not monotonically better because window start offsets change.
- CB04: the cross-firmware multi-fact span needs overlap24 or sections to fit in one retrieved chunk.
- CB06: overlap0/8 split the exact-code passage; overlap16/24 restore complete-span hits; sections ranks it first.
- CB07/CB08: sections keeps the heading and supporting facts together; overlap0 loses complete-span hits.
- CB05: sections still splits a long section at its size cap; fixed windows happen to preserve this particular gold span. Structure awareness does not eliminate internal long-section boundaries.

These observations are diagnostic, not a claim of held-out recall gains. Exact supporting spans, chunk text/offsets and ranked selections are saved in [chunk_boundary_traces.jsonl](chunk_boundary_traces.jsonl).
