# Retriever rescue analysis

All methods use sections, top-N=12, top-k=5, no expansion or reranker. True means all labelled spans are covered. None marks an unanswerable question.

Q rows are the original held-out set. S rows are deliberately selected diagnostic stress cases (see data/stress_protocol.md); these are not an unbiased evaluation.

| Query | Sparse | Dense | Hybrid | Gold ranks S/D/H | Interpretation |
|---|---|---|---|---|---|
| Q01: What should I do for ERR-4022 on AX-17? | True | True | True | 1/2/1 | All retrieve the span; no exclusive rescue. |
| Q02: What should I do for ERR-4021 on AX-18? | True | True | True | 1/3/1 | All retrieve the span; no exclusive rescue. |
| Q03: What does send_logs() do on AX-17? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q04: What is AX-17's maximum upload size? | True | True | True | 1/2/1 | All retrieve the span; no exclusive rescue. |
| Q05: I forgot my password. How can I get back into my account? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q06: My AX-17 turns on but the screen stays dark. What should I reconnect? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q07: Can I still open saved notes when I have no connection? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q08: Do I need internet to send my AX-17 notes to the cloud? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q09: How can I get the AX-17 diagnostic information out of the device? | True | True | True | 3/1/1 | All retrieve the span; no exclusive rescue. |
| Q10: Which indicator confirms recovery on AX-17 firmware 2.2? | True | True | True | 1/2/2 | All retrieve the span; no exclusive rescue. |
| Q11: How long do I hold Power for AX-17 recovery on firmware 2.1 versus 2.2? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q12: Can I return a working custom AX-17 within the regular return period? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q13: Can I return a standard AX-17 after 20 days? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q14: Does a factory reset preserve my local settings? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q15: ax17 err 4021 cabel unpluged, fix? | False | True | True | None/1/1 | Dense matches the paraphrase/noisy wording missed by BM25; RRF keeps semantic evidence in top five. |
| Q16: AX-17 blnk scren after boot, help? | True | True | True | 1/3/1 | All retrieve the span; no exclusive rescue. |
| Q17: AX-17 ERR-4021 always means factory reset, right? | True | True | True | 2/1/1 | All retrieve the span; no exclusive rescue. |
| Q18: Does ERR-4021 mean the same thing on AX-17 and AX-18? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q19: What is the AX-19 upload limit? | None | None | None | None/None/None | Unanswerable: no expected supporting span; do not count as a rescue. |
| Q20: How much free space does AX-17 need before installing an update? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q21: When will someone see the ticket I sent on Saturday? | False | True | True | None/1/2 | Dense matches the paraphrase/noisy wording missed by BM25; RRF keeps semantic evidence in top five. |
| Q22: What does ERR-9999 mean on AX-17? | None | None | None | None/None/None | Unanswerable: no expected supporting span; do not count as a rescue. |
| Q23: Who pays for postage after my return is approved? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| Q24: What does a steady amber light mean on my AX-17 charger? | True | True | True | 1/1/1 | All retrieve the span; no exclusive rescue. |
| S01: I already resolved AX-17 ERR-4021 network cable disconnected. Separately, What should I do for ERR-4022 on AX-17? | True | True | True | 4/3/3 | All retrieve the span; no exclusive rescue. |
| S02: I already resolved AX-17 ERR-4021 network cable disconnected. Separately, What should I do for ERR-4021 on AX-18? | True | True | True | 4/3/3 | All retrieve the span; no exclusive rescue. |
| S03: The ticket was tagged AX-17 firmware 2.1 recovery Power 10 seconds, but my actual question is: What does send_logs() do on AX-17? | True | True | True | 3/1/2 | All retrieve the span; no exclusive rescue. |
| S04: The ticket was tagged AX-17 firmware 2.1 recovery Power 10 seconds, but my actual question is: What is AX-17's maximum upload size? | True | True | True | 4/2/2 | All retrieve the span; no exclusive rescue. |
| S05: I already resolved AX-17 firmware 2.1 recovery Power 10 seconds. Separately, I forgot my password. How can I get back into my account? | True | True | True | 3/1/2 | All retrieve the span; no exclusive rescue. |
| S06: I already resolved AX-17 firmware 2.2 recovery Power 5 seconds. Separately, What should I do for ERR-4021 on AX-18? | True | True | True | 3/5/3 | All retrieve the span; no exclusive rescue. |
| S07: The ticket was tagged AX-18 ERR-4021 temperature sensor failed, but my actual question is: What does send_logs() do on AX-17? | True | True | True | 2/1/1 | All retrieve the span; no exclusive rescue. |
| S08: I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, What is AX-17's maximum upload size? | True | True | True | 3/1/1 | All retrieve the span; no exclusive rescue. |
| S09: I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, I forgot my password. How can I get back into my account? | True | True | True | 2/3/2 | All retrieve the span; no exclusive rescue. |
| S10: I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, My AX-17 turns on but the screen stays dark. What should I reconnect? | True | True | True | 2/5/3 | All retrieve the span; no exclusive rescue. |
| S11: I already resolved AX-17 battery charging steady amber green. Separately, What should I do for ERR-4022 on AX-17? | True | False | True | 3/6/3 | BM25 preserves exact query terms despite distracting context; RRF restores the evidence to top five. |
| S12: I already resolved AX-17 password account token expired login. Separately, What should I do for ERR-4021 on AX-18? | True | False | False | 5/6/6 | RRF cannot interpret which ticket context is irrelevant; combined ranks push gold below top five. Inspect candidate recall to distinguish a shortlist miss from a final cutoff miss. |
| S13: I already resolved AX-18 upload 40 MB. Separately, ax17 err 4021 cabel unpluged, fix? | False | True | False | None/3/7 | RRF cannot interpret which ticket context is irrelevant; combined ranks push gold below top five. Inspect candidate recall to distinguish a shortlist miss from a final cutoff miss. |

Q15 (misspelled cable/disconnected) and Q21 (Saturday versus next business day) show dense rescue on the held-out set. No held-out sparse-only rescue or answerable hybrid miss occurred. S11 supplies an exact-code BM25 rescue under distracting charging context; S12 and S13 show fusion failures. Neither is evidence that hybrid always dominates either input.

The full expected spans, candidate recall and per-hit scores are in [inspection_traces.jsonl](inspection_traces.jsonl). A gold rank beyond 5 is a real final-cutoff miss even if candidate recall is 1.0.
