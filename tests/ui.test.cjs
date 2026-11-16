// Сценарии в браузере: схема, поиск, путь, список, анкета, тема, телефон.
// Нужен интернет: d3 грузится с cdnjs.cloudflare.com, ui-sdk с ui-sdk.dev.
const test = require('node:test');
const assert = require('node:assert/strict');
const { launch, openPage, loadGraph } = require('./helpers.cjs');

const G = loadGraph();
let browser;
test.before(async () => { browser = await launch(); });
test.after(async () => { await browser?.close(); });

test('страница открывается без ошибок, по умолчанию видны ядро и первая сотня', async () => {
  const { page, errors } = await openPage(browser);
  const expected = G.people.filter((p) => p.tier <= 1).length;
  assert.match(await page.textContent('#stat'), new RegExp(`Показано: ${expected} человек`));
  assert.equal(await page.title(), 'Мне 22 года и я не знаю, что делать дальше');
  assert.equal(await page.evaluate(() => document.fonts.check('16px "Acari Sans"')), true);
  assert.deepEqual(errors, []);
  await page.close();
});

test('все пять слоёв показывают всех людей, восемь групп', async () => {
  const { page, errors } = await openPage(browser);
  for (const v of ['2', '3', '4']) await page.check(`.tier[value="${v}"]`);
  await page.waitForTimeout(500);
  assert.match(await page.textContent('#stat'), new RegExp(`Показано: ${G.people.length} человек`));
  assert.equal(await page.locator('#groupChips .chip').count(), 8);
  assert.deepEqual(errors, []);
  await page.close();
});

test('поиск открывает карточку с фото и подписью автора', async () => {
  const { page } = await openPage(browser);
  await page.fill('#q', 'Тимченко');
  await page.keyboard.press('Enter');
  await page.waitForSelector('#card.open');
  assert.match(await page.textContent('#cardBody h2'), /Геннадий Тимченко/);
  assert.equal(await page.locator('#card img.photo').count(), 1);
  assert.match(await page.textContent('#card .credit'), /Wikimedia Commons/);
  await page.close();
});

test('поиск человека из скрытого слоя сам включает этот слой', async () => {
  const { page } = await openPage(browser);
  await page.fill('#q', 'Мацуев');
  await page.keyboard.press('Enter');
  await page.waitForSelector('#card.open');
  assert.match(await page.textContent('#cardBody h2'), /Денис Мацуев/);
  assert.equal(await page.isChecked('.tier[value="4"]'), true);
  await page.close();
});

test('«Как связаны» находит путь между людьми из разных слоёв', async () => {
  const { page } = await openPage(browser);
  await page.fill('#pA', 'Роднина');
  await page.fill('#pB', 'Сечин');
  await page.click('#pathBtn');
  const res = await page.textContent('#pathRes');
  assert.match(res, /Ирина Роднина → Игорь Сечин: \d+ шаг/);
  await page.close();
});

test('список: все люди, фильтр по слою, переход к карточке на схеме', async () => {
  const { page } = await openPage(browser);
  await page.click('[data-tab=listView]');
  assert.equal(await page.locator('#tbl tbody tr').count(), G.people.length);
  await page.selectOption('#ltier', '4');
  assert.equal(await page.locator('#tbl tbody tr').count(), 100);
  await page.locator('#tbl td.name a').first().click();
  await page.waitForSelector('#card.open');
  assert.equal(await page.isVisible('#graphView'), true);
  await page.close();
});

test('анкета проходится кликами до результата из семи блоков', async () => {
  const { page, errors } = await openPage(browser);
  await page.click('[data-tab=quizView]');
  await page.click('[data-act=start]');
  for (let step = 0; step < 10; step++) {
    if (step < 9) {
      await page.click('[data-act=next]');
      assert.match(await page.textContent('#qerr'), /Ответьте на все вопросы/, 'без ответов дальше не пускает');
    }
    const groups = await page.evaluate(() => [...new Set([...document.querySelectorAll('#qform input[type=radio]')].map((i) => i.name))]);
    for (const [gi, g] of groups.entries()) {
      const opts = page.locator(`label.opt:has(input[name="${g}"])`);
      await opts.nth((gi + step) % (await opts.count())).click();
    }
    if (step === 9) await page.fill('#goalText', 'Руководить своей компанией');
    await page.click('[data-act=next]');
  }
  await page.waitForSelector('.result');
  assert.equal(await page.locator('.result .rs').count(), 7);
  assert.equal(await page.locator('.pcard').count(), 3);
  assert.ok((await page.locator('.result .adv').count()) >= 2);
  assert.match(await page.textContent('.result'), /Руководить своей компанией/);
  await page.locator('.pcard [data-graph]').first().click();
  await page.waitForSelector('#card.open');
  assert.deepEqual(errors, []);
  await page.close();
});

test('тёмная тема включается кнопкой и сохраняется после перезагрузки', async () => {
  const { page } = await openPage(browser, { colorScheme: 'light' });
  assert.equal(await page.getAttribute('html', 'data-theme'), 'light');
  await page.click('#themeBtn');
  assert.equal(await page.getAttribute('html', 'data-theme'), 'dark');
  await page.reload();
  assert.equal(await page.getAttribute('html', 'data-theme'), 'dark');
  await page.close();
});

test('на телефоне 375px нет горизонтальной прокрутки', async () => {
  for (const tab of ['graphView', 'listView', 'summaryView', 'quizView']) {
    const { page } = await openPage(browser, { viewport: { width: 375, height: 800 } });
    await page.click(`[data-tab=${tab}]`);
    await page.waitForTimeout(200);
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(over <= 0, `вкладка ${tab}: лишние ${over}px по ширине`);
    await page.close();
  }
});
