import re, json, sys
src = open(sys.argv[1], encoding='utf-8').read()
lines = src.split('\n')

def section(start_pat, end_pat):
    s = next(i for i,l in enumerate(lines) if re.match(start_pat, l))
    e = next((i for i,l in enumerate(lines) if i> s and re.match(end_pat, l)), len(lines))
    return lines[s:e]

GROUPS = ['Петербургский круг','Силовики','Технократы и чиновники','Финансисты и трейдеры 90-х','Отраслевики','Новая экономика','Второе поколение']

def parse_people(block, tier):
    people=[]; group=None; cur=None
    for l in block:
        m = re.match(r'^## (.+?) \(\d+\)', l)
        if m: group=m.group(1); continue
        m = re.match(r'^### (?:(\d+)\. )?(.+?) \((\d{4}|год рождения уточнить)\)\s*$', l)
        if m:
            cur={'name':m.group(2).strip(),'year':int(m.group(3)) if m.group(3).isdigit() else None,
                 'group':group,'tier':tier,'num':int(m.group(1)) if m.group(1) else None}
            people.append(cur); continue
        m = re.match(r'^- \*\*(.+?):\*\* (.*)$', l)
        if m and cur is not None:
            k,v=m.group(1),m.group(2).strip()
            key={'Сейчас':'now','В 18–25 лет':'youth','Взлёт':'rise','Точки пересечения':'nodes_raw','Прямые связи':'direct_raw',
                 'С кем пересекается':'skip','Куда подключить':'connect','Надёжность данных':'reliability'}.get(k.split(' (')[0])
            if key and key!='skip': cur[key]=v
    return people

core = parse_people(section(r'^# Часть 1\.', r'^# Часть 2\.'), 0)
cand1 = parse_people(section(r'^# Часть 3\.', r'^## Новые узлы, которые'), 1)
cand2 = parse_people(section(r'^# Часть 4\.', r'^## Новые узлы второго'), 2)
cand3=[]
if len(sys.argv)>2:
    lines3=open(sys.argv[2],encoding='utf-8').read().split('\n')
    e=next(i for i,l in enumerate(lines3) if l.startswith('## Новые узлы'))
    _L=lines; lines=lines3[:e]; cand3=parse_people(lines,3); lines=_L

# nodes
nodes=[]; cat=None; cur=None
for l in section(r'^# Часть 2\.', r'^## Прямые связи'):
    m=re.match(r'^## (.+?) \(\d+\)', l)
    if m: cat=m.group(1); continue
    m=re.match(r'^### (.+)$', l)
    if m: cur={'name':m.group(1).strip(),'cat':cat,'desc':'','members':[]}; nodes.append(cur); continue
    if cur is None: continue
    m=re.match(r'^- (.+?): (.+)$', l)
    if m: cur['members'].append([m.group(1).strip(), m.group(2).strip()]); continue
    if l.strip() and not l.startswith('#'): cur['desc']=(cur['desc']+' '+l.strip()).strip()

direct=[]
for l in section(r'^## Прямые связи', r'^# Часть 3\.'):
    m=re.match(r'^- (.+?) и (.+?): (.+)$', l)
    if m: direct.append([m.group(1).strip(), m.group(2).strip(), m.group(3).strip()])

json.dump({'core':core,'cand1':cand1,'cand2':cand2,'cand3':cand3,'nodes':nodes,'direct':direct}, open('raw.json','w'), ensure_ascii=False, indent=1)
print(len(core),len(cand1),len(cand2),len(cand3),len(nodes),len(direct))
names=set(p['name'] for p in core)
for n in nodes:
    for mem,_ in n['members']:
        if mem not in names: print('UNKNOWN member', n['name'], '->', mem)
for a,b,_ in direct:
    for x in (a,b):
        if x not in names: print('UNKNOWN direct', x)
# check core nodes_raw matches node names
nn=set(n['name'] for n in nodes)
for p in core:
    for item in re.split(r';\s*', p.get('nodes_raw','')):
        nm=re.sub(r'\s*\([^)]*\)\s*$','',item).strip()
        if nm and nm not in nn: print('UNKNOWN node in', p['name'], ':', nm)
