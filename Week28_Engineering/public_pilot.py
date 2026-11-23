"""Evaluate real public CPython documents and source-scope isolation offline."""
import hashlib
import json

from benchmark import STAGES, load_queries, measure, summarize
from retrieval import CHUNK_CONFIGS, Index, load_sources, make_embedder


def run_public_pilot(data, output, backend):
    sources = load_sources(data)
    provenance = json.loads((data / 'provenance.json').read_text(encoding='utf-8'))
    for entry in provenance:
        source = next(s for s in sources if s.id == entry['source_id'])
        assert hashlib.sha256((data / source.path).read_bytes()).hexdigest() == entry['sha256']
    cases = load_queries(data / 'queries.json', sources)
    index = Index(sources, CHUNK_CONFIGS['sections'], make_embedder(sources, backend))
    traces = []
    summary = {}
    for method in ('sparse','dense','hybrid'):
        rows = measure(index, cases, {**STAGES['R1'], 'method':method})
        summary[method] = summarize(rows)
        traces.extend(dict(stage='public_'+method, **row) for row in rows)
    scope = []
    # Real sources share pip/virtual-environment vocabulary; isolation must hold
    # even when the query's gold evidence belongs to an excluded source.
    for method in ('sparse','dense','hybrid'):
        for allowed in ([], ['ensurepip'], ['tutorial_venv'], ['venv'], ['venv','ensurepip']):
            for case in cases:
                result = index.search(case['query'], method=method, rerank=False,
                                      expansion='off', allowed_sources=allowed)
                answer = index.answer(result)
                returned = {hit['chunk']['source_id'] for hit in result['trace']}
                cited = {p['source_id'] for p in answer['passages']}
                assert returned <= set(allowed) and cited <= set(allowed)
                if not allowed:
                    assert result['trace'] == [] and answer['status'] == 'insufficient_evidence'
                scope.append(dict(query_id=case['id'],method=method,allowed_sources=allowed,
                                  returned_sources=sorted(returned),cited_sources=sorted(cited),passed=True))
    report = dict(backend=backend, source_count=len(sources),chunk_count=len(index.chunks),
                  query_count=len(cases),scores=summary,scope_checks=scope,
                  provenance=provenance,scope_leaks=0)
    (output/'public_corpus_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (output/'public_corpus_traces.jsonl').open('w',encoding='utf-8') as handle:
        for row in traces: handle.write(json.dumps(row)+'\n')
    lines=['# Real public-document pilot','',
           'Source: three PSF-licensed CPython 3.12.8 documentation files, captured on 2026-11-23. '
           'Original URLs and SHA-256 hashes are recorded in [provenance](../data/public_docs/provenance.json); '
           'the [license](../data/public_docs/LICENSE.txt) accompanies the snapshots. '
           'This is a small exploratory public-corpus pilot, not private client validation or an upstream Azure fix.','',
           f'Backend: {index.embedder.name}. {len(index.chunks)} chunks; {len(cases)} labelled questions; '
           'top-N=12, top-k=5, no reranking/expansion. Raw reStructuredText is used as supplied; '
           'the Markdown section detector falls back to 55-word windows. These limitations are part of the measured pilot.','',
           '| Method | Recall@5 | MRR@5 |','|---|---:|---:|']
    for method,r in summary.items():
        lines.append(f"| {method} | {r['recall_at_5']} | {r['mrr_at_5']} |")
    lines += ['',f'{len(scope)} source-scope checks passed with zero leaked sources, including empty scope '
              'and excluded-gold-document queries. Every trace and citation must remain within allowed_sources. '
              'This tests source isolation, not answer relevance: allowed but irrelevant passages may still appear. '
              'Source selection is an API caller constraint, not a replacement for authentication/authorization.','',
              'The scoped search is a local implementation of the isolation property described in '
              '[LlamaIndex issue #19370](https://github.com/run-llama/llama_index/issues/19370). '
              'It does not exercise Azure, OData limits, or a 50,000-path index.','',
              'See [full traces](public_corpus_traces.jsonl) and [machine-readable results](public_corpus_validation.json).']
    (output/'public_corpus_validation.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report
