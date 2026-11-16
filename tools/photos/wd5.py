import json, subprocess, time, sys, re
UA='EliteGraphBuilder/1.0 (research project)'
people=json.load(open('data.json'))['people']; sel=json.load(open('sel.json'))
new=[p for p in people if p['tier']==3 and p['name'] not in sel]
KW=re.compile(r'предприним|бизнес|руковод|политик|государствен|министр|губернатор|директор|глав|банкир|менеджер|основател|владел|дириж|музе|режисс|продюс|учён|академ|ректор|депутат|сенатор|журнал|медиа|инвест|девелоп|страхов|военн|генерал|чиновник')
def query(vals):
    q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE {
  VALUES (?key ?name ?lim) { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit ?lim. ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5.
  OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth }
  OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
    for attempt in range(4):
        r=subprocess.run(['curl','-sS','-m','180','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(10*(attempt+1))
    return None
out={}
for i in range(0,len(new),3):
    batch=new[i:i+3]; vals=[]
    for p in batch:
        w=p['name'].split(); vals.append('("%s" "%s" "8")'%(p['name'],p['name'])); vals.append('("%s" "%s" "40")'%(p['name'],w[-1]))
    d=query(' '.join(vals))
    if not d: print('FAIL',i,file=sys.stderr); continue
    for b in d['results']['bindings']:
        g=lambda k: b.get(k,{}).get('value')
        out.setdefault(g('key'),[]).append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
    print(i+len(batch),'/',len(new),flush=True); time.sleep(3)
json.dump(out,open('wd5.json','w'),ensure_ascii=False,indent=0)
added=[]
for p in new:
    first=p['name'].split()[0]; seen=set(); cs=[]
    for c in out.get(p['name'],[]):
        if c['item'] in seen or first not in (c['label'] or ''): continue
        seen.add(c['item']); cs.append(c)
    if p['year']: m=[c for c in cs if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
    else: m=[c for c in cs if KW.search(c['desc'] or '')]
    if m:
        best=sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0]
        sel[p['name']]={'item':best['item'].rsplit('/',1)[1],'label':best['label'],'desc':best['desc'],'img':best['img'],'ruwiki':best['ruwiki'],'birth':best['birth']}
        added.append((p['name'],p['year'],best['label'],best['birth'],(best['desc'] or '')[:40],bool(best['img'])))
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
for a in added: print(a)
print('added',len(added),'missing',[p['name'] for p in new if p['name'] not in sel])
