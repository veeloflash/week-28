"""Paired, trace-backed diagnostic cases; never used for selecting the default."""
import csv
import json

from benchmark import STAGES, measure
from retrieval import identifiers, tokens, STOP


def dump_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evidence_rank(row):
    relevant = set(row['relevant_chunk_ids'])
    ranks = [hit['final_rank'] for hit in row['retrieval']['trace']
             if hit['chunk']['id'] in relevant and hit['final_rank'] is not None]
    return min(ranks) if ranks else None


def hit_at(row, rank):
    return next((hit for hit in row['retrieval']['trace'] if hit['final_rank'] == rank), None)


def describe(hit, query):
    if hit is None:
        return 'No relevant evidence in the candidate set.'
    chunk = hit['chunk']
    terms = (set(tokens(query)) - STOP) & set(tokens(chunk['text']))
    exact = identifiers(query) & identifiers(chunk['text'])
    return (f"{chunk['source_id']} / {chunk['heading']}; dense={hit['dense_score']:.4f}, "
            f"BM25={hit['sparse_score']:.4f}, rerank={hit['rerank_score']}; "
            f"matched identifiers={sorted(exact)}; lexical matches={sorted(terms)}. "
            f"Citation: {chunk['path']}:{chunk['start_line']}-{chunk['end_line']}.")


def run_inspection_audits(index, heldout, stress, output):
    paired, rescues, changes = [], [], []
    for case in heldout + stress:
        runs = {method: measure(index, [case], {**STAGES['R1'], 'method': method})[0]
                for method in ('sparse', 'dense', 'hybrid')}
        before = runs['hybrid']
        after = measure(index, [case], STAGES['R3'])[0]
        assert before['retrieval']['candidates'] == after['retrieval']['candidates']
        paired += [dict(stage=f'inspect_{method}', **row) for method, row in runs.items()]
        paired.append(dict(stage='inspect_rerank', **after))
        a, b, h = [runs[m]['complete'] for m in ('sparse', 'dense', 'hybrid')]
        if not case['spans']:
            why = 'Unanswerable: no expected supporting span; do not count as a rescue.'
        elif a and not b and h:
            why = 'BM25 preserves exact query terms despite distracting context; RRF restores the evidence to top five.'
        elif b and not a and h:
            why = 'Dense matches the paraphrase/noisy wording missed by BM25; RRF keeps semantic evidence in top five.'
        elif not h:
            why = ('RRF cannot interpret which ticket context is irrelevant; combined ranks push gold below top five. '
                   'Inspect candidate recall to distinguish a shortlist miss from a final cutoff miss.')
        else:
            why = 'All retrieve the span; no exclusive rescue.'
        rescues.append(dict(id=case['id'], split=case['split'], query=case['query'], sparse=a, dense=b, hybrid=h,
                            sparse_rank=evidence_rank(runs['sparse']), dense_rank=evidence_rank(runs['dense']),
                            hybrid_rank=evidence_rank(before), hybrid_candidate_recall=before['candidate_recall'],
                            hybrid_error=before['error'], interpretation=why))
        if not case['spans']:
            continue
        old, new = evidence_rank(before), evidence_rank(after)
        if old == new:
            continue
        change = 'Improved' if new is not None and (old is None or new < old) else 'Degraded'
        why = ('Identifier and query-term features promote the supporting passage within the fixed shortlist.'
               if change == 'Improved' else
               'The scorer rewards identifiers and lexical matches in already-resolved ticket context; '
               'it does not understand the focus after Separately/actual question.')
        changes.append(dict(id=case['id'], split=case['split'], query=case['query'], before_rank=old,
                            after_rank=new, change=change, before_recall=before['recall_at_5'],
                            after_recall=after['recall_at_5'], why=why))
    with (output / 'inspection_traces.jsonl').open('w', encoding='utf-8') as handle:
        for row in paired:
            handle.write(json.dumps(row) + '\n')
    dump_csv(output / 'retriever_rescue_analysis.csv', rescues)
    lines = ['# Retriever rescue analysis', '',
             'All methods use sections, top-N=12, top-k=5, no expansion or reranker. '
             'True means all labelled spans are covered. None marks an unanswerable question.', '',
             'Q rows are the original held-out set. S rows are deliberately selected diagnostic stress cases '
             '(see data/stress_protocol.md); these are not an unbiased evaluation.', '',
             '| Query | Sparse | Dense | Hybrid | Gold ranks S/D/H | Interpretation |',
             '|---|---|---|---|---|---|']
    for r in rescues:
        lines.append(f"| {r['id']}: {r['query']} | {r['sparse']} | {r['dense']} | {r['hybrid']} | "
                     f"{r['sparse_rank']}/{r['dense_rank']}/{r['hybrid_rank']} | {r['interpretation']} |")
    lines += ['', 'Q15 (misspelled cable/disconnected) and Q21 (Saturday versus next business day) '
              'show dense rescue on the held-out set. No held-out sparse-only rescue or answerable hybrid miss occurred. '
              'S11 supplies an exact-code BM25 rescue under distracting charging context; S12 and S13 show fusion failures. '
              'Neither is evidence that hybrid always dominates either input.', '',
              'The full expected spans, candidate recall and per-hit scores are in [inspection_traces.jsonl](inspection_traces.jsonl). '
              'A gold rank beyond 5 is a real final-cutoff miss even if candidate recall is 1.0.']
    (output / 'retriever_rescue_analysis.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    dump_csv(output / 'reranker_case_analysis.csv', changes)
    counts = {split: {kind: sum(r['split']==split and r['change']==kind for r in changes)
                      for kind in ('Improved','Degraded')} for split in ('test','stress')}
    lines = ['# Reranker case analysis', '',
             f"Original held-out rank changes: {counts['test']}. Diagnostic stress rank changes: {counts['stress']}. "
             + ('Current set produced fewer than five degraded cases on the held-out set. '
                if counts['test']['Degraded'] < 5 else '') +
             'S01–S10 are additional adversarial ticket-context cases selected for five improvements and five degradations with MiniLM. '
             'All pairs assert identical R2/R3 candidate lists. Ranks refer to the first fully supporting candidate '
             'across the whole shortlist; ranks >5 are misses at the evaluation cutoff.', '',
             '| Query | Before | After | Change | Recall before/after | Why |',
             '|---|---:|---:|---|---|---|']
    for r in changes:
        lines.append(f"| {r['id']}: {r['query']} | {r['before_rank']} | {r['after_rank']} | {r['change']} | "
                     f"{r['before_recall']}/{r['after_recall']} | {r['why']} |")
    lines += ['', '## Inspection of five improved and five degraded stress cases', '',
              'These are agent-authored inspections of actual evidence and score traces. '
              'No independent human sign-off is claimed. The deterministic scorer has not been tuned to these cases.', '']
    by_pair = {(r['id'],r['stage']):r for r in paired}
    for case in stress[:10]:
        before, after = by_pair[(case['id'],'inspect_hybrid')], by_pair[(case['id'],'inspect_rerank')]
        old, new = evidence_rank(before), evidence_rank(after)
        target = hit_at(after, new)
        leader = hit_at(after, 1)
        inspected = {
            'S01': 'The correct login passage gains rank, but the old network issue still ranks first because its context has more lexical matches.',
            'S02': 'The correct AX-18 sensor passage gains rank, but the old AX-17 network passage still wins through its literal context matches.',
            'S03': 'The unique function identifier send_logs() and ticket vocabulary outweigh the old recovery tag.',
            'S04': 'Product/upload terms and dense similarity promote the upload passage over the old firmware tag.',
            'S05': 'Account/password terms and recovery vocabulary promote the password passage over the old firmware issue.',
            'S06': 'The irrelevant recovery passage matches seven context terms, so the correct AX-18 error passage falls to fourth.',
            'S07': 'The old sensor passage matches five context terms and two identifiers, defeating the correct diagnostic function passage.',
            'S08': 'The old sensor passage wins on five context terms, while the upload passage matches only product/upload.',
            'S09': 'Password evidence contains AX-17, but only AX-18 appears in the old context; the wrong-product penalty further demotes the actual answer.',
            'S10': 'The old sensor issue dominates dense similarity and identifier features; dark-screen wording has fewer literal matches to blank-display evidence.',
        }[case['id']]
        lines += [f"### {case['id']}: {old} → {new}", '', case['query'], '',
                  f"Expected supporting quote: {case['evidence']}", '',
                  'Supporting passage after reranking: '+describe(target,case['query']), '',
                  'First result after reranking: '+describe(leader,case['query']), '', inspected, '',
                  ('The relevant passage gains rank through the displayed exact/lexical matches. '
                   'Residual distraction can still prevent rank 1; an improvement is not perfect intent understanding.'
                   if new is not None and (old is None or new < old) else
                   'The first-ranked passage concerns the resolved sensor/recovery issue instead of the requested answer. '
                   'Its overlapping context terms earn relevance bonuses. This exposes a scope/negation limitation; '
                   'raising identifier weights would reinforce the same failure.'), '']
    lines += ['Suggested follow-up: extract the active question or use an independently evaluated semantic reranker. '
              'Keep these stress cases separate from any future held-out test. '
              'These are retrieval-rank inspections: the answer guard also treats identifiers in the old context '
              'as required, and may abstain/drop the active answer despite complete retrieved evidence. '
              'The answer_covers_all fields in inspection_traces.jsonl expose this separate limitation.']
    (output / 'reranker_case_analysis.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return (sum(r['change']=='Improved' for r in changes), sum(r['change']=='Degraded' for r in changes))
