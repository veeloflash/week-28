# Reranker case analysis

Original held-out rank changes: {'Improved': 2, 'Degraded': 0}. Diagnostic stress rank changes: {'Improved': 8, 'Degraded': 5}. Current set produced fewer than five degraded cases on the held-out set. S01–S10 are additional adversarial ticket-context cases selected for five improvements and five degradations with MiniLM. All pairs assert identical R2/R3 candidate lists. Ranks refer to the first fully supporting candidate across the whole shortlist; ranks >5 are misses at the evaluation cutoff.

| Query | Before | After | Change | Recall before/after | Why |
|---|---:|---:|---|---|---|
| Q10: Which indicator confirms recovery on AX-17 firmware 2.2? | 2 | 1 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| Q21: When will someone see the ticket I sent on Saturday? | 2 | 1 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S01: I already resolved AX-17 ERR-4021 network cable disconnected. Separately, What should I do for ERR-4022 on AX-17? | 3 | 2 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S02: I already resolved AX-17 ERR-4021 network cable disconnected. Separately, What should I do for ERR-4021 on AX-18? | 3 | 2 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S03: The ticket was tagged AX-17 firmware 2.1 recovery Power 10 seconds, but my actual question is: What does send_logs() do on AX-17? | 2 | 1 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S04: The ticket was tagged AX-17 firmware 2.1 recovery Power 10 seconds, but my actual question is: What is AX-17's maximum upload size? | 2 | 1 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S05: I already resolved AX-17 firmware 2.1 recovery Power 10 seconds. Separately, I forgot my password. How can I get back into my account? | 2 | 1 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S06: I already resolved AX-17 firmware 2.2 recovery Power 5 seconds. Separately, What should I do for ERR-4021 on AX-18? | 3 | 4 | Degraded | 1.0/1.0 | The scorer rewards identifiers and lexical matches in already-resolved ticket context; it does not understand the focus after Separately/actual question. |
| S07: The ticket was tagged AX-18 ERR-4021 temperature sensor failed, but my actual question is: What does send_logs() do on AX-17? | 1 | 2 | Degraded | 1.0/1.0 | The scorer rewards identifiers and lexical matches in already-resolved ticket context; it does not understand the focus after Separately/actual question. |
| S08: I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, What is AX-17's maximum upload size? | 1 | 2 | Degraded | 1.0/1.0 | The scorer rewards identifiers and lexical matches in already-resolved ticket context; it does not understand the focus after Separately/actual question. |
| S09: I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, I forgot my password. How can I get back into my account? | 2 | 5 | Degraded | 1.0/1.0 | The scorer rewards identifiers and lexical matches in already-resolved ticket context; it does not understand the focus after Separately/actual question. |
| S10: I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, My AX-17 turns on but the screen stays dark. What should I reconnect? | 3 | 4 | Degraded | 1.0/1.0 | The scorer rewards identifiers and lexical matches in already-resolved ticket context; it does not understand the focus after Separately/actual question. |
| S11: I already resolved AX-17 battery charging steady amber green. Separately, What should I do for ERR-4022 on AX-17? | 3 | 2 | Improved | 1.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S12: I already resolved AX-17 password account token expired login. Separately, What should I do for ERR-4021 on AX-18? | 6 | 5 | Improved | 0.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |
| S13: I already resolved AX-18 upload 40 MB. Separately, ax17 err 4021 cabel unpluged, fix? | 7 | 3 | Improved | 0.0/1.0 | Identifier and query-term features promote the supporting passage within the fixed shortlist. |

## Inspection of five improved and five degraded stress cases

These are agent-authored inspections of actual evidence and score traces. No independent human sign-off is claimed. The deterministic scorer has not been tuned to these cases.

### S01: 3 → 2

I already resolved AX-17 ERR-4021 network cable disconnected. Separately, What should I do for ERR-4022 on AX-17?

Expected supporting quote: [['ax17', 'On the AX-17, ERR-4022 means the account token expired. Sign out and then sign in again to get a fresh token.']]

Supporting passage after reranking: ax17 / AX-17 login errors; dense=0.5773, BM25=3.0374, rerank=0.8976038545442409; matched identifiers=['ax-17', 'err-4022']; lexical matches=['ax-17', 'err-4022']. Citation: manuals/ax17.md:6-7.

First result after reranking: ax17 / AX-17 network errors; dense=0.8637, BM25=11.8094, rerank=1.3412849405177212; matched identifiers=['ax-17', 'err-4021']; lexical matches=['ax-17', 'cable', 'disconnected', 'err-4021', 'network']. Citation: manuals/ax17.md:3-4.

The correct login passage gains rank, but the old network issue still ranks first because its context has more lexical matches.

The relevant passage gains rank through the displayed exact/lexical matches. Residual distraction can still prevent rank 1; an improvement is not perfect intent understanding.

### S02: 3 → 2

I already resolved AX-17 ERR-4021 network cable disconnected. Separately, What should I do for ERR-4021 on AX-18?

Expected supporting quote: [['ax18', 'On the AX-18, ERR-4021 means the temperature sensor failed. Turn off the unit and contact support for service.']]

Supporting passage after reranking: ax18 / AX-18 sensor errors; dense=0.5880, BM25=3.8250, rerank=0.9154194096381617; matched identifiers=['ax-18', 'err-4021']; lexical matches=['ax-18', 'err-4021']. Citation: manuals/ax18.md:3-4.

First result after reranking: ax17 / AX-17 network errors; dense=0.8541, BM25=11.8094, rerank=1.3316694736413635; matched identifiers=['ax-17', 'err-4021']; lexical matches=['ax-17', 'cable', 'disconnected', 'err-4021', 'network']. Citation: manuals/ax17.md:3-4.

The correct AX-18 sensor passage gains rank, but the old AX-17 network passage still wins through its literal context matches.

The relevant passage gains rank through the displayed exact/lexical matches. Residual distraction can still prevent rank 1; an improvement is not perfect intent understanding.

### S03: 2 → 1

The ticket was tagged AX-17 firmware 2.1 recovery Power 10 seconds, but my actual question is: What does send_logs() do on AX-17?

Expected supporting quote: [['ax17', 'Use send_logs() to export diagnostic logs.']]

Supporting passage after reranking: ax17 / AX-17 diagnostics; dense=0.6397, BM25=6.6479, rerank=1.0725117072633892; matched identifiers=['ax-17', 'send_logs()']; lexical matches=['ax-17', 'send_logs', 'ticket']. Citation: manuals/ax17.md:27-28.

First result after reranking: ax17 / AX-17 diagnostics; dense=0.6397, BM25=6.6479, rerank=1.0725117072633892; matched identifiers=['ax-17', 'send_logs()']; lexical matches=['ax-17', 'send_logs', 'ticket']. Citation: manuals/ax17.md:27-28.

The unique function identifier send_logs() and ticket vocabulary outweigh the old recovery tag.

The relevant passage gains rank through the displayed exact/lexical matches. Residual distraction can still prevent rank 1; an improvement is not perfect intent understanding.

### S04: 2 → 1

The ticket was tagged AX-17 firmware 2.1 recovery Power 10 seconds, but my actual question is: What is AX-17's maximum upload size?

Expected supporting quote: [['ax17', 'The AX-17 accepts individual uploads up to 20 MB.']]

Supporting passage after reranking: ax17 / AX-17 upload; dense=0.7425, BM25=3.6013, rerank=1.1335200080061745; matched identifiers=['ax-17']; lexical matches=['ax-17', 'upload']. Citation: manuals/ax17.md:21-22.

First result after reranking: ax17 / AX-17 upload; dense=0.7425, BM25=3.6013, rerank=1.1335200080061745; matched identifiers=['ax-17']; lexical matches=['ax-17', 'upload']. Citation: manuals/ax17.md:21-22.

Product/upload terms and dense similarity promote the upload passage over the old firmware tag.

The relevant passage gains rank through the displayed exact/lexical matches. Residual distraction can still prevent rank 1; an improvement is not perfect intent understanding.

### S05: 2 → 1

I already resolved AX-17 firmware 2.1 recovery Power 10 seconds. Separately, I forgot my password. How can I get back into my account?

Expected supporting quote: [['ax17', 'Use the account recovery link to reset a forgotten password.']]

Supporting passage after reranking: ax17 / AX-17 password and reset; dense=0.7612, BM25=9.1526, rerank=1.2213984267627176; matched identifiers=['ax-17']; lexical matches=['account', 'ax-17', 'password', 'recovery']. Citation: manuals/ax17.md:9-10.

First result after reranking: ax17 / AX-17 password and reset; dense=0.7612, BM25=9.1526, rerank=1.2213984267627176; matched identifiers=['ax-17']; lexical matches=['account', 'ax-17', 'password', 'recovery']. Citation: manuals/ax17.md:9-10.

Account/password terms and recovery vocabulary promote the password passage over the old firmware issue.

The relevant passage gains rank through the displayed exact/lexical matches. Residual distraction can still prevent rank 1; an improvement is not perfect intent understanding.

### S06: 3 → 4

I already resolved AX-17 firmware 2.2 recovery Power 5 seconds. Separately, What should I do for ERR-4021 on AX-18?

Expected supporting quote: [['ax18', 'On the AX-18, ERR-4021 means the temperature sensor failed. Turn off the unit and contact support for service.']]

Supporting passage after reranking: ax18 / AX-18 sensor errors; dense=0.5425, BM25=3.8250, rerank=0.8504669049211511; matched identifiers=['ax-18', 'err-4021']; lexical matches=['ax-18', 'err-4021']. Citation: manuals/ax18.md:3-4.

First result after reranking: ax17 / AX-17 firmware 2.2 recovery; dense=0.7112, BM25=16.8961, rerank=1.1282270488473394; matched identifiers=['ax-17']; lexical matches=['2.2', '5', 'ax-17', 'firmware', 'power', 'recovery', 'seconds']. Citation: manuals/ax17.md:15-16.

The irrelevant recovery passage matches seven context terms, so the correct AX-18 error passage falls to fourth.

The first-ranked passage concerns the resolved sensor/recovery issue instead of the requested answer. Its overlapping context terms earn relevance bonuses. This exposes a scope/negation limitation; raising identifier weights would reinforce the same failure.

### S07: 1 → 2

The ticket was tagged AX-18 ERR-4021 temperature sensor failed, but my actual question is: What does send_logs() do on AX-17?

Expected supporting quote: [['ax17', 'Use send_logs() to export diagnostic logs.']]

Supporting passage after reranking: ax17 / AX-17 diagnostics; dense=0.6431, BM25=6.6479, rerank=0.9413658177226292; matched identifiers=['ax-17', 'send_logs()']; lexical matches=['ax-17', 'send_logs', 'ticket']. Citation: manuals/ax17.md:27-28.

First result after reranking: ax18 / AX-18 sensor errors; dense=0.6240, BM25=13.7667, rerank=1.0025111182171897; matched identifiers=['ax-18', 'err-4021']; lexical matches=['ax-18', 'err-4021', 'failed', 'sensor', 'temperature']. Citation: manuals/ax18.md:3-4.

The old sensor passage matches five context terms and two identifiers, defeating the correct diagnostic function passage.

The first-ranked passage concerns the resolved sensor/recovery issue instead of the requested answer. Its overlapping context terms earn relevance bonuses. This exposes a scope/negation limitation; raising identifier weights would reinforce the same failure.

### S08: 1 → 2

I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, What is AX-17's maximum upload size?

Expected supporting quote: [['ax17', 'The AX-17 accepts individual uploads up to 20 MB.']]

Supporting passage after reranking: ax17 / AX-17 upload; dense=0.6845, BM25=3.6013, rerank=0.9003763602837688; matched identifiers=['ax-17']; lexical matches=['ax-17', 'upload']. Citation: manuals/ax17.md:21-22.

First result after reranking: ax18 / AX-18 sensor errors; dense=0.6306, BM25=13.7667, rerank=1.0557188328453118; matched identifiers=['ax-18', 'err-4021']; lexical matches=['ax-18', 'err-4021', 'failed', 'sensor', 'temperature']. Citation: manuals/ax18.md:3-4.

The old sensor passage wins on five context terms, while the upload passage matches only product/upload.

The first-ranked passage concerns the resolved sensor/recovery issue instead of the requested answer. Its overlapping context terms earn relevance bonuses. This exposes a scope/negation limitation; raising identifier weights would reinforce the same failure.

### S09: 2 → 5

I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, I forgot my password. How can I get back into my account?

Expected supporting quote: [['ax17', 'Use the account recovery link to reset a forgotten password.']]

Supporting passage after reranking: ax17 / AX-17 password and reset; dense=0.5878, BM25=6.2833, rerank=0.46720921409945804; matched identifiers=[]; lexical matches=['account', 'password']. Citation: manuals/ax17.md:9-10.

First result after reranking: ax18 / AX-18 sensor errors; dense=0.5900, BM25=13.7667, rerank=1.0991715039981118; matched identifiers=['ax-18', 'err-4021']; lexical matches=['ax-18', 'err-4021', 'failed', 'sensor', 'temperature']. Citation: manuals/ax18.md:3-4.

Password evidence contains AX-17, but only AX-18 appears in the old context; the wrong-product penalty further demotes the actual answer.

The first-ranked passage concerns the resolved sensor/recovery issue instead of the requested answer. Its overlapping context terms earn relevance bonuses. This exposes a scope/negation limitation; raising identifier weights would reinforce the same failure.

### S10: 3 → 4

I already resolved AX-18 ERR-4021 temperature sensor failed. Separately, My AX-17 turns on but the screen stays dark. What should I reconnect?

Expected supporting quote: [['ax17', 'If the display stays blank after boot, reconnect the display cable and restart the device once.']]

Supporting passage after reranking: ax17 / AX-17 blank display; dense=0.5450, BM25=6.1325, rerank=0.7835903708316383; matched identifiers=['ax-17']; lexical matches=['ax-17', 'reconnect', 'stays']. Citation: manuals/ax17.md:18-19.

First result after reranking: ax18 / AX-18 sensor errors; dense=0.7379, BM25=13.7667, rerank=1.1456346322453292; matched identifiers=['ax-18', 'err-4021']; lexical matches=['ax-18', 'err-4021', 'failed', 'sensor', 'temperature']. Citation: manuals/ax18.md:3-4.

The old sensor issue dominates dense similarity and identifier features; dark-screen wording has fewer literal matches to blank-display evidence.

The first-ranked passage concerns the resolved sensor/recovery issue instead of the requested answer. Its overlapping context terms earn relevance bonuses. This exposes a scope/negation limitation; raising identifier weights would reinforce the same failure.

Suggested follow-up: extract the active question or use an independently evaluated semantic reranker. Keep these stress cases separate from any future held-out test. These are retrieval-rank inspections: the answer guard also treats identifiers in the old context as required, and may abstain/drop the active answer despite complete retrieved evidence. The answer_covers_all fields in inspection_traces.jsonl expose this separate limitation.
