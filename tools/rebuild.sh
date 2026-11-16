#!/usr/bin/env bash
# Пересобирает data/graph.json и index.html из досье, ручной привязки и фото.
# Запуск из любой папки: tools/rebuild.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp "$ROOT/tools/mapping.py" "$TMP/"
cp "$ROOT/data/photos.json" "$TMP/"
cd "$TMP"
python3 -I "$ROOT/tools/parse.py" \
  "$ROOT/data/dosye-elita.md" \
  "$ROOT/data/dosye-elita-tretya-sotnya.md" \
  "$ROOT/data/dosye-elita-chetvyortaya-sotnya.md" > parse.log
python3 "$ROOT/tools/build.py" > build.log
head -1 parse.log; grep -E "^errors|^[0-9]" build.log | head -2
grep -q "^errors \[\]" build.log || { echo "Ошибки привязки:"; cat build.log; exit 1; }
cp data.json "$ROOT/data/graph.json"
python3 - "$ROOT" <<'PY'
import sys
root = sys.argv[1]
tpl = open(f'{root}/tools/template.html', encoding='utf-8').read()
data = open(f'{root}/data/graph.json', encoding='utf-8').read().replace('</', '<\\/')
open(f'{root}/index.html', 'w', encoding='utf-8').write(tpl.replace('__DATA__', data))
PY
echo "Готово: data/graph.json и index.html пересобраны."
