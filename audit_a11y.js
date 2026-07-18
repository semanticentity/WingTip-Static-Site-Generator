#!/usr/bin/env node
/**
 * Post-build accessibility gate: runs axe-core against every generated
 * HTML page in both color schemes and fails on any violation.
 *
 * Usage: node audit_a11y.js --output docs/site
 *
 * Requires playwright (with the chromium browser installed) and axe-core
 * to be resolvable, e.g.: npm install --no-save playwright axe-core &&
 * npx playwright install chromium
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('playwright');

const axePath = require.resolve('axe-core/axe.min.js');

function parseArgs() {
  const idx = process.argv.indexOf('--output');
  if (idx === -1 || !process.argv[idx + 1]) {
    console.error('Usage: node audit_a11y.js --output <site-dir>');
    process.exit(2);
  }
  return path.resolve(process.argv[idx + 1]);
}

function collectPages(dir, base) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...collectPages(full, base));
    else if (entry.name.endsWith('.html')) out.push(path.relative(base, full));
  }
  return out.sort();
}

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.woff2': 'font/woff2',
  '.txt': 'text/plain', '.xml': 'application/xml',
};

function serve(root) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      let file = path.join(root, urlPath);
      if (file.endsWith('/')) file += 'index.html';
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404); res.end('not found'); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
        res.end(data);
      });
    });
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

(async () => {
  const siteDir = parseArgs();
  const pages = collectPages(siteDir, siteDir);
  if (!pages.length) {
    console.error(`A11y audit: no HTML pages found in ${siteDir}`);
    process.exit(2);
  }

  const server = await serve(siteDir);
  const port = server.address().port;
  const browser = await chromium.launch();
  let violationCount = 0;
  let checkedPages = 0;

  for (const scheme of ['light', 'dark']) {
    const context = await browser.newContext({ colorScheme: scheme });
    const page = await context.newPage();
    for (const rel of pages) {
      await page.goto(`http://127.0.0.1:${port}/${rel.split(path.sep).join('/')}`, { waitUntil: 'load' });
      // Let the page's theme class land and CSS color transitions finish,
      // otherwise contrast is measured against mid-transition colors.
      await page.waitForTimeout(400);
      await page.addScriptTag({ path: axePath });
      const violations = await page.evaluate(async () => {
        const r = await axe.run(document, { resultTypes: ['violations'] });
        return r.violations.map(v => ({
          id: v.id, impact: v.impact, help: v.help,
          nodes: v.nodes.slice(0, 5).map(n => n.target.join(' ')),
          count: v.nodes.length,
        }));
      });
      checkedPages++;
      for (const v of violations) {
        violationCount += v.count;
        console.error(`FAIL [${v.impact}] ${rel} (${scheme}): ${v.id} — ${v.help} (${v.count} nodes)`);
        v.nodes.forEach(n => console.error(`      ${n}`));
      }
    }
    await context.close();
  }

  await browser.close();
  server.close();

  if (violationCount) {
    console.error(`A11y audit FAILED: ${violationCount} violation nodes across ${pages.length} pages (light+dark).`);
    process.exit(1);
  }
  console.log(`A11y audit passed: 0 axe-core violations across ${pages.length} pages in both color schemes (${checkedPages} page-scheme checks).`);
})().catch((e) => { console.error('A11y audit error:', e.message); process.exit(2); });
