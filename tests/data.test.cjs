const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { at, read, loadGraph, renderIndex } = require('./helpers.cjs');

const G = loadGraph();
const people = G.people;
const byName = new Map(people.map((p) => [p.name, p]));
const GROUPS = ['Петербургский круг', 'Силовики', 'Технократы и чиновники', 'Финансисты и трейдеры 90-х', 'Отраслевики', 'Новая экономика', 'Второе поколение', 'Спорт, культура и медиа'];
const RELIABILITY = ['высокая', 'средняя', 'низкая'];

test('index.html собран из шаблона и data/graph.json', () => {
  assert.equal(read('index.html'), renderIndex(), 'index.html устарел: пересоберите его из tools/template.html');
});

test('пять слоёв по сто человек и ядро из 98', () => {
  const byTier = [0, 1, 2, 3, 4].map((t) => people.filter((p) => p.tier === t).length);
  assert.deepEqual(byTier, [98, 100, 100, 100, 100]);
  assert.equal(people.length, 498);
});

test('имена уникальны', () => {
  assert.equal(byName.size, people.length);
});

test('у каждого человека известная группа, надёжность и текст карточки', () => {
  for (const p of people) {
    assert.ok(GROUPS.includes(p.group), `${p.name}: неизвестная группа ${p.group}`);
    assert.ok(RELIABILITY.includes(p.reliability), `${p.name}: надёжность ${p.reliability}`);
    assert.ok(p.now && p.now.length > 3, `${p.name}: пустое поле «Сейчас»`);
    assert.ok(p.year === null || (p.year > 1900 && p.year < 2010), `${p.name}: год ${p.year}`);
  }
});

test('участники узлов существуют', () => {
  for (const n of G.nodes) {
    assert.ok(n.members.length >= 1, `узел ${n.name} пуст`);
    for (const [m] of n.members) assert.ok(byName.has(m), `узел ${n.name}: нет человека ${m}`);
    const names = n.members.map((m) => m[0]);
    assert.equal(new Set(names).size, names.length, `узел ${n.name}: повтор участника`);
  }
});

test('прямые связи ведут к существующим людям и не повторяются', () => {
  const seen = new Set();
  for (const [a, b, label] of G.direct) {
    assert.ok(byName.has(a) && byName.has(b), `связь ${a} — ${b}`);
    assert.notEqual(a, b);
    assert.ok(label, `связь ${a} — ${b} без подписи`);
    const key = [a, b].sort().join('|');
    assert.ok(!seen.has(key), `повтор связи ${key}`);
    seen.add(key);
  }
});

test('фото: файл существует, это изображение, у него есть автор и лицензия', () => {
  const MAGIC = [[0xff, 0xd8, 0xff], [0x89, 0x50, 0x4e], [0x52, 0x49, 0x46]];
  for (const p of people.filter((x) => x.photo)) {
    const file = at(p.photo);
    assert.ok(fs.existsSync(file), `${p.name}: нет файла ${p.photo}`);
    const head = fs.readFileSync(file).subarray(0, 3);
    assert.ok(MAGIC.some((m) => m.every((b, i) => head[i] === b)), `${p.name}: ${p.photo} не изображение`);
    assert.ok(p.file, `${p.name}: нет имени файла на Commons`);
    assert.ok(p.license, `${p.name}: не указана лицензия`);
  }
});

test('в img/ нет файлов, на которые никто не ссылается', () => {
  const used = new Set(people.filter((p) => p.photo).map((p) => p.photo.replace(/^img\//, '')));
  const orphans = fs.readdirSync(at('img')).filter((f) => !used.has(f));
  assert.deepEqual(orphans, []);
});

test('векторы четвёртой сотни: восемь осей от 0 до 10, только у надёжных записей', () => {
  const labeled = people.filter((p) => p.vector);
  assert.equal(labeled.length, 79);
  for (const p of labeled) {
    const m = p.vector.match(/^`?A(\d+) B(\d+) C(\d+) D(\d+) E(\d+) F(\d+) G(\d+) H(\d+)`?$/);
    assert.ok(m, `${p.name}: вектор ${p.vector}`);
    for (const v of m.slice(1)) assert.ok(+v >= 0 && +v <= 10, `${p.name}: ${v}`);
    assert.notEqual(p.reliability, 'низкая', `${p.name}: вектор у записи с низкой надёжностью`);
    assert.ok(p.lesson, `${p.name}: нет урока для отчёта`);
  }
});

test('шаблон подключает ui-sdk, слой стилей и анкету', () => {
  const tpl = read('tools', 'template.html');
  assert.match(tpl, /<script type="module" src="https:\/\/ui-sdk\.dev\/web\.js"><\/script>/);
  assert.match(tpl, /<link rel="stylesheet" href="https:\/\/ui-sdk\.dev\/web\.css" \/>/);
  assert.match(tpl, /@layer ui-sdk;/);
  assert.match(tpl, /<script src="anketa\.js"><\/script>/);
  for (const f of ['fonts/AcariSans-Regular.ttf', 'fonts/AcariSans-Bold.ttf', 'fonts/Ambidexter_Regular.otf', 'anketa.js']) {
    assert.ok(fs.existsSync(at(f)), `нет файла ${f}`);
  }
});

test('досье, ручная привязка и фото дают ровно data/graph.json', { skip: require('node:child_process').spawnSync('python3', ['--version']).status !== 0 && 'нет python3' }, () => {
  const { execFileSync } = require('node:child_process');
  const os = require('node:os');
  const path = require('node:path');
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'elita-build-'));
  fs.copyFileSync(at('tools', 'mapping.py'), path.join(tmp, 'mapping.py'));
  fs.copyFileSync(at('data', 'photos.json'), path.join(tmp, 'photos.json'));
  execFileSync('python3', ['-I', at('tools', 'parse.py'), at('data', 'dosye-elita.md'), at('data', 'dosye-elita-tretya-sotnya.md'), at('data', 'dosye-elita-chetvyortaya-sotnya.md')], { cwd: tmp, stdio: 'pipe' });
  const log = execFileSync('python3', [at('tools', 'build.py')], { cwd: tmp, encoding: 'utf8' });
  assert.match(log, /^errors \[\]/m, 'ошибки привязки в tools/mapping.py');
  assert.equal(fs.readFileSync(path.join(tmp, 'data.json'), 'utf8'), read('data', 'graph.json'), 'data/graph.json устарел: запустите tools/rebuild.sh');
  fs.rmSync(tmp, { recursive: true, force: true });
});
