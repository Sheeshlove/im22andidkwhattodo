const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const at = (...p) => path.join(ROOT, ...p);
const read = (...p) => fs.readFileSync(at(...p), 'utf8');

function loadGraph() {
  return JSON.parse(read('data', 'graph.json'));
}

// index.html собирается из шаблона и data/graph.json одним заменой.
function renderIndex() {
  const tpl = read('tools', 'template.html');
  const data = read('data', 'graph.json').replace(/<\//g, '<\\/');
  return tpl.replace('__DATA__', () => data);
}

const PAGE_URL = 'file://' + at('index.html');

async function launch() {
  const { chromium } = require('playwright');
  return chromium.launch();
}

// Открывает страницу и собирает ошибки консоли и исключения.
async function openPage(browser, opts = {}) {
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, ...opts });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(PAGE_URL);
  await page.waitForFunction(() => window.Anketa && document.querySelectorAll('svg#graph g.n').length > 0, null, { timeout: 30000 });
  await page.waitForTimeout(300);
  return { page, errors };
}

module.exports = { ROOT, at, read, loadGraph, renderIndex, PAGE_URL, launch, openPage };
