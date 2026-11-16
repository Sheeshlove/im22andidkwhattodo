import json, subprocess, time, sys
UA='EliteGraphBuilder/1.0 (research project)'
people={p['name']:p for p in json.load(open('data.json'))['people']}; sel=json.load(open('sel.json'))
Q={'Арас Агаларов':['Араз Агаларов','Aras Agalarov'],'Сергей Королёв':['Sergei Korolev','Королёв Сергей Борисович'],'Андрей Акимов':['Andrey Akimov','Andrei Akimov'],'Константин Николаев':['Konstantin Nikolaev','Николаев Константин Юрьевич'],'Игорь Бабаев':['Igor Babaev','Бабаев Игорь'],'Олег Мисерва':['Oleg Miserva','Мисерва'],'Татьяна Володина':['Tatyana Volodina','Володина Татьяна'],'Виктор Линник':['Viktor Linnik','Линник Виктор'],'Руслан Рахимкулов':['Ruslan Rakhimkulov','Рахимкулов'],'Тимур Рахимкулов':['Timur Rakhimkulov','Рахимкулов'],'Юрий Шамалов':['Yuri Shamalov','Шамалов Юрий'],'Андрей Патрушев':['Andrey Patrushev','Andrei Patrushev','Патрушев Андрей'],'Сергей Сергеевич Иванов':['Sergei Ivanov Sogaz','Иванов Сергей Сергеевич'],'Александр Савельев':['Alexander Savelyev','Савельев Александр Васильевич'],'Максим Шаскольский':['Maksim Shaskolsky','Шаскольский'],'Алан Лушников':['Alan Lushnikov','Лушников'],'Анастасия Ракова':['Anastasia Rakova','Ракова Анастасия'],'Владимир Воронин':['Vladimir Voronin FSK','Воронин Владимир Николаевич'],'Владислав Свиблов':['Vladislav Sviblov','Свиблов'],'Муса Бажаев':['Musa Bazhaev','Бажаев Муса'],'Вадим Швецов':['Vadim Shvetsov','Швецов Вадим'],'Олег Михасенко':['Oleg Mikhasenko','Михасенко'],'Сергей Судариков':['Sergey Sudarikov','Судариков'],'Кирилл Липа':['Kirill Lipa','Липа Кирилл'],'Александр Линник':['Alexander Linnik','Линник Александр'],'Дмитрий Алексеев':['Dmitry Alekseev','Алексеев Дмитрий Юрьевич'],'Николай Фартушняк':['Nikolay Fartushnyak','Фартушняк'],'Владимир Мельников':['Vladimir Melnikov','Мельников Владимир Владимирович'],'Роберт Мирзоян':['Robert Mirzoyan','Мирзоян Роберт'],'Олег Новиков':['Oleg Novikov','Новиков Олег Евгеньевич'],'Дмитрий Морозов':['Dmitry Morozov','Морозов Дмитрий Валентинович'],'Дмитрий Хотимский':['Dmitry Khotimsky','Хотимский'],'Кирилл Мордашов':['Kirill Mordashov','Мордашов Кирилл']}
out={}
items=[(k,v) for k,vs in Q.items() for v in vs]
for i in range(0,len(items),4):
    batch=items[i:i+4]
    vals=' '.join('("%s" "%s" "%s")'%(k,v,'en' if v[0].isascii() else 'ru') for k,v in batch)
    q='''SELECT ?key ?item ?itemLabel ?desc ?img ?birth ?ruwiki WHERE {
  VALUES (?key ?name ?lang) { %s }
  SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "EntitySearch"; mwapi:search ?name; mwapi:language ?lang; mwapi:limit "30". ?item wikibase:apiOutputItem mwapi:item. }
  ?item wdt:P31 wd:Q5.
  OPTIONAL { ?item wdt:P18 ?img } OPTIONAL { ?item wdt:P569 ?birth }
  OPTIONAL { ?item schema:description ?desc FILTER(LANG(?desc)="ru") }
  OPTIONAL { ?ruwiki schema:about ?item; schema:isPartOf <https://ru.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ru,en". } }'''%vals
    d=None
    for attempt in range(4):
        r=subprocess.run(['curl','-sS','-m','180','-A',UA,'-X','POST','https://query.wikidata.org/sparql','--data-urlencode','query='+q,'-H','Accept: application/sparql-results+json'],capture_output=True,text=True)
        try: d=json.loads(r.stdout); break
        except Exception: time.sleep(10*(attempt+1))
    if not d: print('FAILED batch',i,file=sys.stderr); continue
    for b in d['results']['bindings']:
        g=lambda k: b.get(k,{}).get('value')
        out.setdefault(g('key'),[]).append({'item':g('item'),'label':g('itemLabel'),'desc':g('desc'),'img':g('img'),'birth':(g('birth') or '')[:4],'ruwiki':g('ruwiki')})
    time.sleep(3)
json.dump(out,open('wd4.json','w'),ensure_ascii=False,indent=0)
for k,cs in out.items():
    p=people[k]; seen=set(); u=[]
    for c in cs:
        if c['item'] in seen: continue
        seen.add(c['item']); u.append(c)
    if p['year']: m=[c for c in u if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
    else: m=[c for c in u if c['desc'] and any(w in c['desc'] for w in ('предприним','бизнес','руковод','банкир','топ-менедж','владел'))]
    print(k,'=>',[(c['label'],c['birth'],(c['desc'] or '')[:40],bool(c['img'])) for c in m][:3] or 'none; raw:'+str([(c['label'],c['birth']) for c in u][:4]))
    if m:
        best=sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0]
        sel[k]={'item':best['item'].rsplit('/',1)[1],'label':best['label'],'desc':best['desc'],'img':best['img'],'ruwiki':best['ruwiki'],'birth':best['birth']}
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
print('total',len(sel),'with img',sum(1 for v in sel.values() if v['img']))
