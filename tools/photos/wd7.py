import json, subprocess, time
UA='EliteGraphBuilder/1.0 (research project)'
sel=json.load(open('sel.json'))
want={'Дмитрий Ядров':'Дмитрий Викторович Ядров','Андрей Иващенко':'Иващенко, Андрей Александрович','Александр Ракшин':'Ракшин, Александр Фёдорович','Владимир Зотов':'Зотов, Владимир Федорович','Павел Маринычев':'Маринычев, Павел Алексеевич'}
vals=' '.join('("%s" "%s")'%(k,v) for k,v in want.items())
q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE { VALUES (?key ?name) { %s }
 SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit "5". ?item wikibase:apiOutputItem mwapi:item. }
 ?item wdt:P31 wd:Q5. OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth } OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
 OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> } SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
for a in range(4):
    r=subprocess.run(['curl','-sS','-m','180','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
    try: d=json.loads(r.stdout); break
    except Exception: time.sleep(10*(a+1)); d=None
for b in d['results']['bindings']:
    g=lambda k: b.get(k,{}).get('value'); k=g('key')
    if g('itemLabel')==want[k] and k not in sel:
        sel[k]={'item':g('item').rsplit('/',1)[1],'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'ruwiki':g('ruwiki'),'birth':(g('birth') or '')[:4]}
        print('added',k,bool(g('img')))
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
print('total',len(sel),'img',sum(1 for v in sel.values() if v['img']))
