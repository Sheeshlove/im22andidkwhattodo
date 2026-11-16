import json, subprocess, time, sys, re
UA='EliteGraphBuilder/1.0 (research project)'
data=json.load(open('data.json'))['people']; sel=json.load(open('sel.json'))
only=sys.argv[1] if len(sys.argv)>1 else 'tier4'
people=[p for p in data if (p['tier']==4 if only=='tier4' else True) and not (sel.get(p['name']) or {}).get('img')]
SPECIAL={'Тимати (Тимур Юнусов)':(['Тимати','Тимур Юнусов'],'Тим'),'Митрополит Тихон (Шевкунов)':(['Тихон Шевкунов','Тихон (Шевкунов)'],'Тихон'),'Евгений Примаков-младший':(['Евгений Примаков','Примаков, Евгений Александрович'],'Евгений'),'Патриарх Кирилл (Владимир Гундяев)':(['Патриарх Кирилл','Кирилл (патриарх Московский)'],'Кирилл'),'Андрей Гурьев-младший':(['Андрей Андреевич Гурьев'],'Андрей'),'Сергей Борисович Иванов':(['Сергей Борисович Иванов'],'Сергей'),'Сергей Сергеевич Иванов':(['Сергей Сергеевич Иванов'],'Сергей')}
KW=re.compile(r'предприним|бизнес|руковод|политик|государствен|министр|директор|глав|банкир|менеджер|основател|владел|наследн|медиа|спорт|музык|режисс|актёр|актер|телеведущ|дипломат|депутат|сенатор|губернатор')
def run(vals,lim):
    q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE { VALUES (?key ?name) { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit "%d". ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5. OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth } OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> } SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%(vals,lim)
    for a in range(5):
        r=subprocess.run(['curl','-sS','-m','120','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: return json.loads(r.stdout)
        except Exception: print('retry',r.stdout[:80].replace('\n',' '),flush=True); time.sleep(10*(a+1))
def pick(p,cs):
    first=SPECIAL.get(p['name'],(None,p['name'].split()[0]))[1]; seen=set(); u=[]
    for c in cs:
        if c['item'] in seen or first not in (c['label'] or ''): continue
        seen.add(c['item']); u.append(c)
    if p['year']: m=[c for c in u if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
    else: m=[c for c in u if KW.search(c['desc'] or '') and (not c['birth'].isdigit() or int(c['birth'])>1940)]
    return sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0] if m else None
def search(plist,termf,lim,B):
    out={}
    for i in range(0,len(plist),B):
        batch=plist[i:i+B]; vals=' '.join('("%s" "%s")'%(p['name'],tm) for p in batch for tm in termf(p))
        d=run(vals,lim)
        if not d: print('FAIL batch',i,flush=True); continue
        for b in d['results']['bindings']:
            g=lambda k: b.get(k,{}).get('value')
            out.setdefault(g('key'),[]).append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
        print(i+len(batch),'/',len(plist),flush=True); time.sleep(4)
    return out
print('to search',len(people),flush=True)
o1=search(people,lambda p:SPECIAL.get(p['name'],([p['name']],))[0],6,4)
found={};
for p in people:
    b=pick(p,o1.get(p['name'],[]))
    if b: found[p['name']]=b
rest=[p for p in people if p['name'] not in found or not found[p['name']]['img']]
def t2(p):
    w=p['name'].replace('-младший','').split(); return [w[-1]+', '+w[0], w[-1]] if len(w)>=2 else [p['name']]
o2=search(rest,t2,25,2)
for p in rest:
    b=pick(p,o1.get(p['name'],[])+o2.get(p['name'],[]))
    if b and (b['img'] or p['name'] not in found): found[p['name']]=b
for n,b in found.items():
    old=sel.get(n)
    if old and old.get('img') : continue
    sel[n]={'item':b['item'].rsplit('/',1)[1],'label':b['label'],'desc':b['desc'],'img':b['img'],'ruwiki':b['ruwiki'],'birth':b['birth']}
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
for n,b in found.items(): print('FOUND',n,'|',b['label'],b['birth'],'|',(b['desc'] or '')[:45],'| img' if b['img'] else '| no-img')
print('found',len(found),'with img',sum(1 for b in found.values() if b['img']),'not found',[p['name'] for p in people if p['name'] not in found])
