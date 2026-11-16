import json, subprocess, time, sys, re
UA='EliteGraphBuilder/1.0 (research project)'
people=[p for p in json.load(open('data.json'))['people'] if p['tier']==4]; sel=json.load(open('sel.json'))
SPECIAL={'Тимати (Тимур Юнусов)':(['Тимати','Тимур Юнусов'],'Тим'),'Митрополит Тихон (Шевкунов)':(['Тихон Шевкунов','Шевкунов'],'Тихон'),'Евгений Примаков-младший':(['Евгений Александрович Примаков','Примаков'],'Евгений')}
KW=re.compile(r'предприним|бизнес|руковод|политик|государствен|министр|директор|глав|банкир|менеджер|основател|владел|наследн|медиа')
def run(vals):
    q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE { VALUES (?key ?name ?lim) { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit ?lim. ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5. OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth } OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> } SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
    for a in range(5):
        r=subprocess.run(['curl','-sS','-m','180','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(12*(a+1))
out={}
for i in range(0,len(people),3):
    batch=people[i:i+3]; vals=[]
    for p in batch:
        terms,_=SPECIAL.get(p['name'],([p['name'],p['name'].split()[-1]],None))
        for j,tm in enumerate(terms): vals.append('("%s" "%s" "%s")'%(p['name'],tm,'8' if j==0 else '40'))
    d=run(' '.join(vals))
    if not d: print('FAIL',i,flush=True); continue
    for b in d['results']['bindings']:
        g=lambda k: b.get(k,{}).get('value')
        out.setdefault(g('key'),[]).append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
    print(i+len(batch),'/',len(people),flush=True); time.sleep(3)
json.dump(out,open('wd8.json','w'),ensure_ascii=False,indent=0)
added=[];miss=[]
for p in people:
    first=SPECIAL.get(p['name'],(None,p['name'].split()[0]))[1]; seen=set(); cs=[]
    for c in out.get(p['name'],[]):
        if c['item'] in seen or first not in (c['label'] or ''): continue
        seen.add(c['item']); cs.append(c)
    if p['year']: m=[c for c in cs if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
    else: m=[c for c in cs if KW.search(c['desc'] or '') and (not c['birth'].isdigit() or int(c['birth'])>1940)]
    if m:
        best=sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0]
        sel[p['name']]={'item':best['item'].rsplit('/',1)[1],'label':best['label'],'desc':best['desc'],'img':best['img'],'ruwiki':best['ruwiki'],'birth':best['birth']}
        added.append((p['name'],p['year'],best['label'],best['birth'],(best['desc'] or '')[:40],bool(best['img'])))
    else: miss.append(p['name'])
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
for a in added: print(a)
print('added',len(added),'with img',sum(1 for a in added if a[5]),'missing',miss)
