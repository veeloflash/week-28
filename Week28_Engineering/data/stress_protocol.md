# Diagnostic stress protocol

The 24 original held-out questions and eight development questions are unchanged.
The 13 S questions are deliberately selected counterexamples, not a new held-out
benchmark. Their evidence labels inherit the active question's original supporting
spans. Prefixes explicitly describe resolved issues or old ticket tags, so those
prefix facts are distractors, not the answer to the active question.

Exploration used the 30 answerable original dev/test questions, ten context phrases
(recovery 2.1, recovery 2.2, AX-18 sensor, AX-17 network, returns/shipping,
charging, AX-18 upload, login, diagnostics, blank display), and three templates:

- `I already resolved {context}. Separately, {question}`
- `Do not answer about {context}. Instead: {question}`
- `The ticket was tagged {context}, but my actual question is: {question}`

This produced 900 exploratory variants. The first variant with rank improvement
for each of five distinct Q questions became S01–S05; the corresponding first
degradation variants became S06–S10. S11–S13 illustrate a sparse rescue and two
fusion failures found with the first template. This outcome-based selection must
not be used to report population improvement/degradation rates or tune defaults.
No retrieval scores, ranks, or evidence were fabricated. The saved 13 queries are
the reproducible diagnostic inputs; paired actual output traces are committed.

The case write-up is an agent inspection, not an independently signed human
review. An instructor/client can inspect the paired sources and scores before
providing that sign-off. No reranker parameters changed after this exploration.
