// Логика анкеты из anketa.js, сверка со спецификацией data/anketa-i-rekomendacii.md
// и изменениями из data/anketa-izmeneniya.md. Расчёт идёт в браузере, поэтому тесты открывают страницу.
const test = require('node:test');
const assert = require('node:assert/strict');
const { launch, openPage } = require('./helpers.cjs');

let browser, page;
test.before(async () => { browser = await launch(); ({ page } = await openPage(browser)); });
test.after(async () => { await browser?.close(); });

const ev = (fn, arg) => page.evaluate(fn, arg);

test('максимумы по осям совпадают с таблицей спецификации', async () => {
  const r = await ev(() => ({ max: window.Anketa.MAX, q: window.Anketa.Q.length }));
  assert.deepEqual(r.max, { A: 12, B: 15, C: 18, D: 18, E: 11, F: 18, G: 19, H: 26 });
  assert.equal(r.q, 31);
});

test('ответы начисляют баллы только на оси A–H', async () => {
  const bad = await ev(() => window.Anketa.Q.flatMap((q) => q.o.flatMap((o) => Object.keys(o.s).filter((k) => !'ABCDEFGH'.includes(k)).map((k) => q.id + ':' + k))));
  assert.deepEqual(bad, []);
});

test('по каждой оси достижим балл 10, у вопросов 22 и 26 нет нулевого ответа', async () => {
  const r = await ev(() => {
    const A = window.Anketa; const maxed = {};
    for (const ax of 'ABCDEFGH') {
      const ans = {};
      A.Q.forEach((q) => { let bi = 0; q.o.forEach((o, i) => { if ((o.s[ax] || 0) > (q.o[bi].s[ax] || 0)) bi = i; }); ans[q.id] = bi; });
      maxed[ax] = A.score(ans)[ax];
    }
    return { maxed, noZero: A.Q.filter((q) => !q.o.some((o) => !Object.keys(o.s).length)).map((q) => q.id) };
  });
  for (const ax of 'ABCDEFGH') assert.equal(r.maxed[ax], 10, `ось ${ax}`);
  assert.deepEqual(r.noZero, [22, 26]);
});

test('девять архетипов, у Мастера эталон из досье четвёртой сотни', async () => {
  const a = await ev(() => window.Anketa.ARCH.map((x) => [x.name, x.ref.join(' ')]));
  assert.equal(a.length, 9);
  assert.deepEqual(a.find((x) => x[0] === 'Мастер'), ['Мастер', '5 10 5 2 4 3 6 10']);
});

test('центрированное сходство воспроизводит расчёт досье для Родниной', async () => {
  const top = await ev(() => {
    const A = window.Anketa; const mean = [6.1, 6.3, 4.8, 2.8, 4.5, 5.4, 5.5, 7.5];
    const c = (v) => v.map((x, i) => x - mean[i]);
    const rod = [4, 10, 6, 1, 5, 4, 5, 10];
    return A.ARCH.map((a) => [a.name, Math.round(A.cos(c(rod), c(a.ref)) * 100)]).sort((x, y) => y[1] - x[1]).slice(0, 2);
  });
  assert.deepEqual(top, [['Мастер', 90], ['Отраслевик', 46]]);
});

test('база похожих людей: 109 размеченных, без низкой надёжности, все есть в данных', async () => {
  const r = await ev(() => {
    const A = window.Anketa;
    return { n: A.PV.length, missing: A.PV.filter((x) => !P.get(x.n)).map((x) => x.n), low: A.PV.filter((x) => P.get(x.n)?.reliability === 'низкая').map((x) => x.n), mean: A.MEAN };
  });
  assert.equal(r.n, 109);
  assert.deepEqual(r.missing, []);
  assert.deepEqual(r.low, []);
  r.mean.forEach((m) => assert.ok(m > 0 && m < 10));
});

test('пример из раздела 9: порядок архетипов и оси советов', async () => {
  const r = await ev(() => {
    const rep = window.Anketa.report({ A: 6, B: 2, C: 2, D: 7, E: 3, F: 0, G: 5, H: 5 }, { age: '18', occ: 'study', sphere: 'it', goal: 'company', town: 'mid' });
    return { arch: rep.top2.map((a) => a.name), weak: rep.weak.map((w) => w.ax), strong: rep.strong.map((s) => s.ax), fVariant: rep.weak.find((w) => w.ax === 'F')?.t, cVariant: rep.weak.find((w) => w.ax === 'C')?.t };
  });
  assert.deepEqual(r.arch, ['Основатель', 'Финансист']);
  assert.deepEqual(r.weak, ['C', 'G', 'F']);
  assert.deepEqual(r.strong, ['D']);
  assert.match(r.fVariant, /^Год в крупной структуре/, 'при цели «своя компания» нужен вариант F для компании');
  assert.match(r.cVariant, /^Вуз даёт партнёров/, 'студенту нужен вариант C про вуз');
});

test('правила отчёта соблюдаются на 400 случайных анкетах', async () => {
  const problems = await ev(() => {
    const A = window.Anketa; const out = [];
    let seed = 7; const rnd = (n) => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };
    const pick = (q) => q.v[rnd(q.v.length)];
    for (let k = 0; k < 400; k++) {
      const prof = Object.fromEntries(A.PROFILE.map((q) => [q.id, pick(q)]));
      const ans = Object.fromEntries(A.Q.map((q) => [q.id, rnd(q.o.length)]));
      const u = A.score(ans); const r = A.report(u, prof);
      const tag = JSON.stringify(prof) + ' ' + JSON.stringify(u);
      if (r.people.length !== 3) out.push('людей не 3: ' + tag);
      const groups = {}; r.people.forEach((x) => { const g = P.get(x.n).group; groups[g] = (groups[g] || 0) + 1; });
      if (Object.values(groups).some((c) => c > 2)) out.push('больше двух из одной группы: ' + tag);
      if (prof.town === 'small' && !r.people.some((x) => x.prov)) out.push('нет человека из провинции: ' + tag);
      if (r.weak.length > 3 || r.strong.length > 2) out.push('слишком много советов: ' + tag);
      for (const a of [...r.weak, ...r.strong]) {
        if (a.ex.length < 1 || a.ex.length > 2) out.push(`примеров ${a.ex.length}: ` + tag);
        if (!a.act) out.push('нет действия на 90 дней: ' + tag);
      }
      if (r.arch.some((a) => a.pct > 100)) out.push('близость больше 100: ' + tag);
      if (['freedom', 'expert'].includes(prof.goal) && r.weak.some((w) => w.ax === 'F')) out.push('совет по F противоречит цели: ' + tag);
      if (prof.age === 'u18') {
        const d = r.weak.find((w) => w.ax === 'D'); const g = r.weak.find((w) => w.ax === 'G');
        if (d && !/поделку/.test(d.t)) out.push('для младше 18 нужен мягкий совет по D: ' + tag);
        if (g && !/летняя школа/.test(g.t)) out.push('для младше 18 нужен мягкий совет по G: ' + tag);
      }
      const used = new Map(); const add = (n) => used.set(n, (used.get(n) || 0) + 1);
      r.people.forEach((x) => add(x.n)); [...r.weak, ...r.strong].forEach((a) => a.ex.forEach((e) => e.p.forEach(add))); r.sphPeople.forEach(add);
      const over = [...used].filter(([, c]) => c > 2);
      if (over.length) out.push('человек больше двух раз: ' + over.map((o) => o[0]).join(', ') + ' ' + tag);
      if (out.length > 10) break;
    }
    return out;
  });
  assert.deepEqual(problems, []);
});
