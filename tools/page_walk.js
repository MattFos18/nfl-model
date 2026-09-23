// Render every tab and sub-view of web/index.html in Chromium and report console errors, page errors, and any
// view whose text contains "undefined", "NaN" or "[object", or is nearly empty. Prints one JSON object.
// Usage: node tools/page_walk.js [path-to-index.html] [chromium executable]
const path = require('path');
const { chromium } = require('playwright');
const file = path.resolve(process.argv[2] || 'web/index.html');
const exe = process.argv[3] || process.env.CHROMIUM_PATH;
(async () => {
  const b = await chromium.launch(exe ? { executablePath: exe } : {});
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/CERT|net::/.test(m.text())) errs.push('console: ' + m.text()); });
  await p.goto('file://' + file); await p.waitForTimeout(1500);
  const views = [['week', null], ['rank', null], ['teamsec', 'overview'], ['teamsec', 'roster'], ['teamsec', 'players'], ['playersec', null], ['results', 'backtest'], ['results', 'live'], ['model', 'analysis'], ['model', 'inputsx'], ['model', 'how'], ['model', 'dict'], ['model', 'log'], ['model', 'decisions'], ['model', 'defs']];
  const out = { views: {}, errors: errs, bad: [] };
  for (const [tab, sub] of views) {
    const name = tab + (sub ? '/' + sub : '');
    try {
      await p.click(`button[data-tab="${tab}"]`); await p.waitForTimeout(300);
      if (sub) { const s = await p.$(`nav.sub button[data-sub="${sub}"]:visible`); if (!s) { out.bad.push(name + ': sub-view button missing'); continue; } await s.click(); await p.waitForTimeout(400); }
      const txt = await p.evaluate(() => document.body.innerText);
      const n = (txt.match(/undefined|NaN|\[object/g) || []).length;
      out.views[name] = { chars: txt.length, undefined: n };
      if (n > 0) out.bad.push(name + `: ${n} undefined/NaN`); if (txt.length < 200) out.bad.push(name + ': empty');
    } catch (e) { out.bad.push(name + ': ' + e.message.slice(0, 80)); }
  }
  await p.click('button[data-tab="week"]'); await p.waitForTimeout(200);
  const btns = await p.$$('article.gcard button'); for (const bt of btns.slice(0, 3)) { try { await bt.click(); await p.waitForTimeout(150); } catch (e) {} }
  out.cards = await p.$$eval('article.gcard', els => els.length);
  out.ok = errs.length === 0 && out.bad.length === 0 && out.cards > 0;
  console.log(JSON.stringify(out)); await b.close(); process.exit(out.ok ? 0 : 1);
})();
