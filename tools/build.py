import json, re, sys
sys.path.insert(0,'.')
from mapping import N, NEW_NODES
raw=json.load(open('raw.json'))
people={}
for tier,key in ((0,'core'),(1,'cand1'),(2,'cand2')):
    for p in raw[key]:
        p['id']=p['name']; people[p['name']]=p
nodes={n['name']:n for n in raw['nodes']}
for nm,(cat,desc,mem) in NEW_NODES.items():
    nodes[nm]={'name':nm,'cat':cat,'desc':desc,'members':[list(m) for m in mem]}
errors=[]
# core nodes_raw -> memberships (should already be in node members; verify)
member_set={(n['name'],m[0]) for n in nodes.values() for m in n['members']}
for p in raw['core']:
    for item in re.split(r';\s*', p.get('nodes_raw','').rstrip('.')):
        item=item.strip()
        if not item or 'общих узлов' in item: continue
        m=re.match(r'^(.*?)(?:\s*\((.*)\))?$', item); nm=m.group(1).strip(); role=m.group(2) or ''
        if nm not in nodes: errors.append(('node',p['name'],nm)); continue
        if (nm,p['name']) not in member_set:
            nodes[nm]['members'].append([p['name'],role]); member_set.add((nm,p['name']))
for p in raw['cand1']+raw['cand2']:
    ns,ds=N[p['num']]
    for nm,role in ns:
        if nm not in nodes: errors.append(('node',p['name'],nm)); continue
        if (nm,p['name']) not in member_set:
            nodes[nm]['members'].append([p['name'],role]); member_set.add((nm,p['name']))
direct=[list(d) for d in raw['direct']]
seen={frozenset(d[:2]) for d in direct}
for p in raw['cand1']+raw['cand2']:
    for other,label in N[p['num']][1]:
        if other not in people: errors.append(('person',p['name'],other)); continue
        k=frozenset((p['name'],other))
        if k in seen: continue
        seen.add(k); direct.append([p['name'],other,label])
for n in nodes.values():
    for m in n['members']:
        if m[0] not in people: errors.append(('member',n['name'],m[0]))
print('errors',errors)
for p in people.values():
    p.pop('nodes_raw',None); p.pop('direct_raw',None)
    p['reliability']=p.get('reliability','высокая').rstrip('.').split(',')[0]
out={'people':list(people.values()),'nodes':list(nodes.values()),'direct':direct,
     'generated':'2026-11-15'}
json.dump(out,open('data.json','w'),ensure_ascii=False)
print(len(people),len(nodes),len(direct), sum(len(n['members']) for n in nodes.values()))
print([ (n['name'],len(n['members'])) for n in nodes.values() if len(n['members'])<2])
