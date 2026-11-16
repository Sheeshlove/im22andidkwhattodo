import json, subprocess, urllib.parse, time, sys, re, html
UA='EliteGraphBuilder/1.0 (research project)'
sel=json.load(open('sel.json'))
files={n:'File:'+urllib.parse.unquote(v['img'].rsplit('/',1)[1]) for n,v in sel.items() if v.get('img')}
try: cred=json.load(open('credits.json'))
except: cred={}
todo=sorted({f for f in files.values() if f not in cred})
for i in range(0,len(todo),40):
    batch=todo[i:i+40]
    for attempt in range(4):
        r=subprocess.run(['curl','-sS','-m','60','-A',UA,'-X','POST','https://commons.wikimedia.org/w/api.php','--data-urlencode','action=query','--data-urlencode','prop=imageinfo','--data-urlencode','iiprop=extmetadata','--data-urlencode','iiextmetadatafilter=Artist|LicenseShortName|Credit','--data-urlencode','format=json','--data-urlencode','titles='+'|'.join(batch)],capture_output=True,text=True)
        try: d=json.loads(r.stdout); break
        except Exception: print('retry',r.stdout[:100],file=sys.stderr); time.sleep(15*(attempt+1)); d=None
    if not d: continue
    norm={x['to']:x['from'] for x in d['query'].get('normalized',[])}
    for pg in d['query']['pages'].values():
        t=norm.get(pg['title'],pg['title']); md=(pg.get('imageinfo') or [{}])[0].get('extmetadata',{})
        strip=lambda s: html.unescape(re.sub('<[^>]+>','',s or '')).strip()
        cred[t]={'author':strip(md.get('Artist',{}).get('value'))[:120],'license':strip(md.get('LicenseShortName',{}).get('value'))}
    json.dump(cred,open('credits.json','w'),ensure_ascii=False,indent=0); print(i+len(batch),'/',len(todo),flush=True); time.sleep(2)
print(len(cred), sum(1 for v in cred.values() if v['license']))
