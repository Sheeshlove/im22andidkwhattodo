import json, subprocess, time, sys
UA='EliteGraphBuilder/1.0 (research project)'
people={p['name']:p for p in json.load(open('data.json'))['people']}; sel=json.load(open('sel.json'))
for bad in ['Андрей Кондрашов','Владимир Зотов','Виктор Семёнов','Юрий Максимов','Александр Островский','Сергей Михайлов']: sel.pop(bad,None)
Q={'Борис Титов':'Борис Юрьевич Титов','Анна Попова':'Анна Юрьевна Попова','Игорь Комаров':'Игорь Анатольевич Комаров','Лариса Брычёва':'Лариса Игоревна Брычёва','Леонид Горнин':'Леонид Владимирович Горнин','Дмитрий Ядров':'Дмитрий Викторович Ядров','Владимир Христенко':'Владимир Викторович Христенко','Филипп Генс':'Филипп Георгиевич Генс','Алексей Крапивин':'Алексей Андреевич Крапивин','Максим Воробьёв':'Максим Юрьевич Воробьёв','Валерий Пономарёв':'Валерий Андреевич Пономарёв','Сергей Кудряшов':'Сергей Иванович Кудряшов','Александр Ручьёв':'Александр Валерьевич Ручьёв','Александр Чачава':'Александр Чачава','Андрей Иващенко':'Андрей Александрович Иващенко','Павел Титов':'Павел Борисович Титов','Андрей Симановский':'Андрей Моисеевич Симановский','Александр Ракшин':'Александр Фёдорович Ракшин','Светлана Баланова':'Светлана Баланова','Алексей Добашин':'Алексей Добашин','Назим Эфендиев':'Назим Эфендиев','Евгений Никитин':'Евгений Викторович Никитин','Андрей Кондрашов':'Андрей Олегович Кондрашов','Виктор Семёнов':'Виктор Александрович Семёнов','Юрий Максимов':'Юрий Максимов Positive','Александр Островский':'Александр Юрьевич Островский','Сергей Михайлов':'Сергей Игоревич Михайлов','Игорь Боровиков':'Игорь Петрович Боровиков','Леонид Гольдорт':'Леонид Гольдорт','Александр Харичев':'Александр Дмитриевич Харичев','Сергей Александровский':'Сергей Александровский Аэрофлот','Денис Фёдоров':'Денис Владимирович Фёдоров','Андрей Рюмин':'Андрей Валерьевич Рюмин','Фамил Садыгов':'Фамил Камиль оглы Садыгов','Леонид Фридлянд':'Леонид Фридлянд','Лариса Прокопьева':'Лариса Прокопьева Эвалар','Рустем Сультеев':'Рустем Сультеев','Владимир Зотов':'Владимир Фёдорович Зотов','Игорь Снегуров':'Игорь Снегуров','Владимир Пекарев':'Владимир Пекарев','Вадим Бадеха':'Вадим Бадеха','Александр Шевелёв':'Александр Шевелёв Северсталь','Павел Маринычев':'Павел Маринычев'}
out={}
items=list(Q.items())
def run(vals):
    q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE { VALUES (?key ?name) { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language "ru"; mwapi:limit "10". ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5. OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth } OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> } SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
    for a in range(4):
        r=subprocess.run(['curl','-sS','-m','180','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(10*(a+1))
for i in range(0,len(items),4):
    batch=items[i:i+4]; vals=[]
    for k,full in batch:
        w=full.split(); vals.append('("%s" "%s")'%(k,full))
        if len(w)==3: vals.append('("%s" "%s, %s %s")'%(k,w[2],w[0],w[1]))
    d=run(' '.join(vals))
    if not d: print('FAIL',i,file=sys.stderr); continue
    for b in d['results']['bindings']:
        g=lambda k: b.get(k,{}).get('value')
        out.setdefault(g('key'),[]).append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
    time.sleep(3)
for k,cs in out.items():
    p=people[k]; first=k.split()[0]; seen=set(); u=[]
    for c in cs:
        if c['item'] in seen or first not in (c['label'] or ''): continue
        seen.add(c['item']); u.append(c)
    if p['year']: m=[c for c in u if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
    else: m=[c for c in u if c['desc'] and any(w in c['desc'] for w in ('предприним','бизнес','руковод','основател','генеральн','директор','менедж')) and (not c['birth'].isdigit() or int(c['birth'])>1940)]
    print(k,'=>',[(c['label'],c['birth'],(c['desc'] or '')[:40],bool(c['img'])) for c in m][:2] or 'none; raw:'+str([(c['label'],c['birth']) for c in u][:3]))
    if m:
        best=sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0]
        sel[k]={'item':best['item'].rsplit('/',1)[1],'label':best['label'],'desc':best['desc'],'img':best['img'],'ruwiki':best['ruwiki'],'birth':best['birth']}
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
print('total',len(sel),'with img',sum(1 for v in sel.values() if v['img']))
