# Собирает data/photos.json из sel.json, credits.json и файлов в img/. Запуск из папки с этими файлами.
import json, os, re, urllib.parse, sys
sel=json.load(open('sel.json')); cred=json.load(open('credits.json'))
names={p['name'] for p in json.load(open(sys.argv[1]))['people']}
def slug(n):
    tr={'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
    return re.sub(r'[^a-z0-9]+','-',''.join(tr.get(c,c) for c in n.lower())).strip('-')
MAGIC=(b'\xff\xd8\xff',b'\x89PN',b'RIF')
photos={}
for n,v in sel.items():
    if n not in names: continue
    e={'wd':v['item'],'wiki':v.get('ruwiki')}
    if v.get('img'):
        f='img/'+slug(n)+'.jpg'
        if os.path.exists(f) and os.path.getsize(f)>500 and open(f,'rb').read(3) in MAGIC:
            fn=urllib.parse.unquote(v['img'].rsplit('/',1)[1]); c=cred.get('File:'+fn,{})
            e.update({'photo':f,'file':fn,'author':c.get('author',''),'license':c.get('license','')})
    photos[n]=e
json.dump(photos,open('photos.json','w'),ensure_ascii=False,indent=0)
used={v['photo'][4:] for v in photos.values() if 'photo' in v}
print('people with photo',len(used),'| orphans',sorted(set(os.listdir('img'))-used))
