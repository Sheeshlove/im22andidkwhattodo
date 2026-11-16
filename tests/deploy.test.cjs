// Проверка deploy/nginx.conf на настоящем nginx. Пропускается, если nginx не установлен.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync, spawnSync } = require('node:child_process');
const { ROOT, at } = require('./helpers.cjs');

const hasNginx = spawnSync('nginx', ['-v']).status === 0;
const PORT = 18089;
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'elita-nginx-'));
const conf = path.join(dir, 'nginx.conf');

test('конфиг nginx отдаёт сайт с правильными типами и закрывает служебные папки', { skip: !hasNginx && 'nginx не установлен' }, async (t) => {
  const site = fs.readFileSync(at('deploy', 'nginx.conf'), 'utf8')
    .replace(/\/var\/www\/elita/g, ROOT)
    .replace(/listen 80;/, `listen 127.0.0.1:${PORT};`)
    .replace(/\s*listen \[::\]:80;/, '');
  fs.writeFileSync(path.join(dir, 'site.conf'), site);
  fs.writeFileSync(conf, `worker_processes 1; pid ${dir}/nginx.pid; error_log ${dir}/error.log;
events {}
http { include /etc/nginx/mime.types; access_log off; client_body_temp_path ${dir}; proxy_temp_path ${dir}; fastcgi_temp_path ${dir}; uwsgi_temp_path ${dir}; scgi_temp_path ${dir}; include ${dir}/site.conf; }
`);
  execFileSync('nginx', ['-t', '-c', conf], { stdio: 'pipe' });
  execFileSync('nginx', ['-c', conf]);
  t.after(() => { try { execFileSync('nginx', ['-c', conf, '-s', 'stop']); } catch {} });
  await new Promise((r) => setTimeout(r, 500));

  const get = async (p, headers = {}) => {
    const res = await fetch(`http://127.0.0.1:${PORT}${p}`, { headers });
    const body = Buffer.from(await res.arrayBuffer());
    return { status: res.status, type: res.headers.get('content-type') || '', enc: res.headers.get('content-encoding'), cache: res.headers.get('cache-control'), size: body.length };
  };
  const photo = JSON.parse(fs.readFileSync(at('data', 'graph.json'), 'utf8')).people.find((p) => p.photo).photo;
  const cases = [
    ['/', 200, 'text/html'],
    ['/anketa.js', 200, 'application/javascript'],
    ['/fonts/AcariSans-Regular.ttf', 200, 'font/ttf'],
    ['/fonts/Ambidexter_Regular.otf', 200, 'font/otf'],
    ['/' + photo, 200, 'image/jpeg'],
    ['/tools/build.py', 404],
    ['/data/graph.json', 200, 'application/json'],
    ['/deploy/nginx.conf', 404],
    ['/tests/helpers.cjs', 404],
    ['/package.json', 200, 'application/json'],
    ['/.git/config', 404],
    ['/.agents/skills/ui-sdk/SKILL.md', 404],
    ['/AGENTS.md', 200]
  ];
  for (const [p, status, type] of cases) {
    const r = await get(p);
    assert.equal(r.status, status, `${p}: статус`);
    if (type) assert.ok(r.type.startsWith(type), `${p}: тип ${r.type}`);
  }
  const page = await get('/', { 'Accept-Encoding': 'gzip' });
  assert.equal(page.enc, 'gzip', 'страница должна сжиматься');
  assert.equal(page.cache, 'no-cache');
});
