import json, hashlib, urllib.parse, subprocess, sys, os, time, re
UA='EliteGraphBuilder/1.0 (research project)'
sel=json.load(open(sys.argv[1])); skip={'Владимир Воронин','Олег Новиков'}
def slug(n): 
    tr={'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
    return re.sub(r'[^a-z0-9]+','-',''.join(tr.get(c,c) for c in n.lower())).strip('-')
ok=0; fail=[]
for name,v in sel.items():
    if name in skip or not v.get('img'): continue
    out=f'img/{slug(name)}.jpg'
    if os.path.exists(out) and os.path.getsize(out)>500: ok+=1; continue
    fn=urllib.parse.unquote(v['img'].rsplit('/',1)[1]).replace(' ','_')
    h=hashlib.md5(fn.encode()).hexdigest(); q=urllib.parse.quote(fn)
    ext='.png' if fn.lower().endswith('.png') else '.jpg'
    url=f'https://commons.wikimedia.org/w/thumb.php?f={q}&w=160'
    for attempt in range(3):
        r=subprocess.run(['curl','-sS','-m','40','-L','-A',UA,'-o',out,'-w','%{http_code}',url],capture_output=True,text=True)
        if r.stdout=='200' and os.path.getsize(out)>500: ok+=1; break
        time.sleep(3*(attempt+1))
    else:
        fail.append((name,fn,r.stdout)); 
        if os.path.exists(out): os.remove(out)
    time.sleep(1.0)
print('ok',ok,'fail',fail)
