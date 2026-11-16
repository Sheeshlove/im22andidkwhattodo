import json, subprocess, time, sys
UA='EliteGraphBuilder/1.0 (research project)'
people=json.load(open('data.json'))['people']; sel=json.load(open('sel.json'))
sel.pop('Владимир Воронин',None); sel.pop('Олег Новиков',None)
missing=[p for p in people if p['name'] not in sel]
def parts(n):
    n=n.replace(' (Владимир Гундяев)','').replace('-младший','')
    w=n.split(); return w[0], w[-1]
out={}
for i in range(0,len(missing),3):
    batch=missing[i:i+3]
    vals=' '.join('("%s" "%s")'%(p['name'],parts(p['name'])[1]) for p in batch)
    q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE {
  VALUES (?key ?name) { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit "40". ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5.
  OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth }
  OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
    d=None
    for attempt in range(4):
        r=subprocess.run(['curl','-sS','-m','180','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: d=json.loads(r.stdout); break
        except Exception: print('retry',i,r.stdout[:150],file=sys.stderr); time.sleep(10*(attempt+1))
    if not d: continue
    for b in d['results']['bindings']:
        g=lambda k: b.get(k,{}).get('value')
        out.setdefault(g('key'),[]).append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
    print(i+len(batch),'/',len(missing),flush=True); time.sleep(4)
json.dump(out,open('wd3.json','w'),ensure_ascii=False,indent=0)
# merge with wd2 and select
wd2=json.load(open('wd2.json'))
for k,v in wd2.items(): out.setdefault(k,[]).extend(v)
added=[]
for p in missing:
    first,last=parts(p['name']); cs=out.get(p['name'],[])
    seen=set(); cands=[]
    for c in cs:
        if c['item'] in seen: continue
        seen.add(c['item'])
        lab=(c['label'] or '')
        if first not in lab: continue
        cands.append(c)
    best=None
    if p['year']:
        m=[c for c in cands if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
        if m: best=sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0]
    else:
        m=[c for c in cands if c['desc'] and ('предприним' in c['desc'] or 'бизнес' in c['desc'] or 'руковод' in c['desc'] or 'деятель' in c['desc'])]
        if m: best=m[0]
    if best:
        sel[p['name']]={'item':best['item'].rsplit('/',1)[1],'label':best['label'],'desc':best['desc'],'img':best['img'],'ruwiki':best['ruwiki'],'birth':best['birth']}
        added.append((p['name'],best['label'],best['birth'],bool(best['img'])))
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
print('added',len(added)); [print(a) for a in added]
print('still missing:',[p['name'] for p in people if p['name'] not in sel])
print('total',len(sel),'with img',sum(1 for v in sel.values() if v['img']))
