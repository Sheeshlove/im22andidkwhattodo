# Сборка схемы

```bash
python3 tools/parse.py data/dosye-elita.md   # досье -> raw.json
python3 tools/build.py                        # raw.json + mapping.py -> data.json
python3 - <<'PY'
d=open('data.json',encoding='utf-8').read().replace('</','<\\/')
open('index.html','w',encoding='utf-8').write(open('tools/template.html',encoding='utf-8').read().replace('__DATA__',d))
PY
```

`mapping.py` — ручная привязка поля «Куда подключить» каждого кандидата к узлам и прямым связям, плюс описания новых узлов. Чтобы добавить человека: карточка в досье в том же формате, строка в `mapping.py`, пересборка.
