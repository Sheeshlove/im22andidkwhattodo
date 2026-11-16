import json,re
people=json.load(open('data.json'))['people']; wd=json.load(open('wd.json'))
def clean(n): return n.replace(' (Владимир Гундяев)','').replace('Сергей Борисович Иванов','Сергей Иванов').replace('Сергей Сергеевич Иванов','Сергей Иванов').replace('Андрей Гурьев-младший','Андрей Гурьев')
KW=re.compile(r'предпринимат|бизнесмен|миллиардер|политик|государственн|чиновник|министр|губернатор|военачальник|генерал|юрист|экономист|банкир|топ-менеджер|менеджер|руководител|президент|промышленник|олигарх|дипломат|патриарх|программист|финансист|ректор|журналист|телеведущ|медиа|депутат|сенатор|мэр|глава|директор|основатель|владелец|совладелец|инвестор|управлен|акционер|девелопер|изобретатель')
sel={}; review=[]
for p in people:
    cands=[c for c in wd.get(clean(p['name']),[])]
    # dedupe by item
    seen=set(); cs=[]
    for c in cands:
        if c['item'] in seen: continue
        seen.add(c['item']); cs.append(c)
    best=None
    if p['year']:
        m=[c for c in cs if c['birth'].isdigit() and abs(int(c['birth'])-p['year'])<=1]
        if m: best=sorted(m,key=lambda c:(not c['img'],not c['ruwiki']))[0]
        else:
            m=[c for c in cs if not c['birth'].isdigit() and KW.search(c['desc'] or '')]
            if m: best=m[0]; review.append((p['name'],p['year'],best['label'],best['desc'],'no-birth'))
            elif cs: review.append((p['name'],p['year'],'; '.join(f"{c['label']} {c['birth']} {c['desc']}" for c in cs[:3]),'','year-mismatch'))
    else:
        m=[c for c in cs if KW.search(c['desc'] or '')]
        if m: best=m[0]; review.append((p['name'],None,best['label'],best['desc'],'no-year'))
    if best: sel[p['name']]={'item':best['item'].rsplit('/',1)[1],'label':best['label'],'desc':best['desc'],'img':best['img'],'ruwiki':best['ruwiki'],'birth':best['birth']}
json.dump(sel,open('sel.json','w'),ensure_ascii=False,indent=0)
print('selected',len(sel),'with img',sum(1 for v in sel.values() if v['img']))
for r in review: print(r)
print('MISSING:',[p['name'] for p in people if p['name'] not in sel])
