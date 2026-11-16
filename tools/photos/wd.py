import json, subprocess, time, sys, urllib.parse
UA='EliteGraphBuilder/1.0 (research project)'
people=json.load(open('data.json'))['people']
def clean(n): return n.replace(' (Владимир Гундяев)','').replace('Сергей Борисович Иванов','Сергей Иванов').replace('Сергей Сергеевич Иванов','Сергей Иванов').replace('Андрей Гурьев-младший','Андрей Гурьев')
names=sorted({clean(p['name']) for p in people})
out={}
try: out=json.load(open('wd.json'))
except: pass
todo=[n for n in names if n not in out]
B=12
for i in range(0,len(todo),B):
    batch=todo[i:i+B]
    vals=' '.join('"%s"'%n.replace('"','') for n in batch)
    q='''SELECT ?name ?item ?itemLabel ?desc ?img ?birth ?enwiki ?ruwiki WHERE {
  VALUES ?name { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit "5". ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5.
  OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth }
  OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
    for attempt in range(4):
        r=subprocess.run(['curl','-sS','-m','180','-A',UA,'--get','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: d=json.loads(r.stdout); break
        except Exception as e:
            print('retry',i,r.stdout[:200],file=sys.stderr); time.sleep(10*(attempt+1)); d=None
    if d is None: continue
    for n in batch: out.setdefault(n,[])
    for b in d['results']['bindings']:
        g=lambda k: b.get(k,{}).get('value')
        out[g('name')].append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
    json.dump(out,open('wd.json','w'),ensure_ascii=False,indent=0)
    print(i+len(batch),'/',len(todo),flush=True); time.sleep(2)
