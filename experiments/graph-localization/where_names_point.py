import json, re
nb = json.load(open('localization.ipynb', encoding='utf-8'))
g = {}
for c in nb['cells']:
    if c['cell_type'] != 'code': continue
    src = ''.join(c['source'])
    if 'summary = pd.DataFrame' in src: break
    exec(src, g)
df, tasks, gold_rows, query_rows = g['df_loc'], g['tasks'], g['gold_rows'], g['query_rows']
load, snap, src_index, grep_hits = g['load_snapshot'], g['snapshot'], g['src_index'], g['grep_hits']
ev_ids = set(df[(df.n_gold > 0) & ((df.n_graph_q + df.n_src_q) > 0)].task)
cats, rows = {}, []
for t, gr, q in zip(tasks, gold_rows, query_rows):
    tid = t['instance_id']
    if tid not in ev_ids: continue
    s, idx = load(snap(t)), src_index[snap(t)]
    gold, files = gr['gold'], gr['gold_files']
    named = set(q['graph_queries']) | set(q['src_queries'])
    in_file = lambda n: any(n == m or n.startswith(m + '.') for m in files)
    # 1-hop / 2-hop over the call graph (both directions)
    hop1 = set().union(*[s['nbrs'].get(n, set()) for n in named]) if named else set()
    hop2 = set().union(*[s['nbrs'].get(n, set()) for n in hop1]) if hop1 else set()
    # names and gold in the same class (method of named class, or class of named method)
    same_class = any(gd.startswith(n + '.') or n.startswith(gd + '.') for gd in gold for n in named)
    # gold's own code mentions a named function (the gold function calls/uses it)
    gold_uses_named = any(re.search(r'\b' + re.escape(n.rsplit('.', 1)[-1]) + r'\b', idx.get(gd, '')) for gd in gold for n in named)
    named_code_mentions_gold = any(re.search(r'\b' + re.escape(gd.rsplit('.', 1)[-1]) + r'\b', idx.get(n, '') or s['text'].get(n, '')) for gd in gold for n in named)
    if named & gold: c = '1 names a gold function'
    elif same_class: c = '2 names its class / method of the same class'
    elif named_code_mentions_gold or (hop1 & gold): c = '3 named function calls gold (or is called by it)'
    elif gold_uses_named: c = '4 gold code mentions a named function'
    elif hop2 & gold: c = '5 two steps away in the call graph'
    elif any(in_file(n) for n in named): c = '6 same file, unrelated function'
    else: c = '7 elsewhere'
    cats.setdefault(c, []).append(tid)
    rows.append((tid, c, sorted(named)[:5], sorted(gold)[:3]))
print(len(rows), 'tasks')
for c in sorted(cats): print(f'{c}: {len(cats[c])}')
file_hit = sum(any(any(n == m or n.startswith(m + '.') for m in gr['gold_files']) for n in set(q['graph_queries']) | set(q['src_queries']))
               for t, gr, q in zip(tasks, gold_rows, query_rows) if t['instance_id'] in ev_ids)
print('names in a gold file:', file_hit)
print('names per task (median):', sorted(len(set(q['graph_queries']) | set(q['src_queries'])) for t, q in zip(tasks, query_rows) if t['instance_id'] in ev_ids)[31])
for r in rows:
    if not r[1].startswith('1'): print(r[1][:1], r[0], '| named:', r[2], '| gold:', r[3])
