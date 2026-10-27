// Offline browser fixture. Does not log in or make network calls.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const storage = new Map();
const article = {
  querySelector(selector) {
    const values = {
      'a[href*="/status/"]': { getAttribute: () => '/demo_builder/status/1001' },
      time: { getAttribute: () => '2026-10-20T12:00:00Z' },
      '[data-testid="socialContext"]': { innerText: '' },
      '[role="group"][aria-label]': { getAttribute: () => '2 replies, 3 reposts, 5 likes, 100 views' },
    };
    return values[selector] || null;
  },
  querySelectorAll(selector) {
    return selector === '[data-testid="tweetText"]' ? [{innerText:'Fictional workflow: проверка Unicode.'}] : [];
  },
};
const context = vm.createContext({
  location: { pathname:'/i/lists/100', hostname:'x.com' },
  document: { querySelectorAll: () => [article] },
  window: { scrollBy() {} },
  localStorage: { setItem: (k,v) => storage.set(k,v), getItem: k => storage.get(k) ?? null },
  Date, Map, TextEncoder,
  setTimeout: f => f(),
  btoa: s => Buffer.from(s, 'binary').toString('base64'),
});
(async () => {
  const code = fs.readFileSync(path.join(root,'radar/collector.js'),'utf8');
  const result = JSON.parse(await vm.runInContext(code, context));
  assert.equal(result.count, 1);
  context.__XRADAR_LIST_IDS = ['100'];
  const exported = vm.runInContext(fs.readFileSync(path.join(root,'radar/export.js'),'utf8'), context);
  const post = JSON.parse(Buffer.from(exported.slice(1),'base64').toString('utf8'));
  assert.equal(post.id, '1001');
  assert.equal(post.likes, 5);
  assert.equal(post.reposts, 3);
  assert.equal(post.replies, 2);
  assert.equal(post.views, 100);
  assert.match(post.text, /проверка Unicode/);
  context.__XRADAR_LIST_IDS = ['101'];
  assert.throws(() => vm.runInContext(fs.readFileSync(path.join(root,'radar/export.js'),'utf8'), context), /Missing collection/);
  console.log('collector/export: fictional DOM, metrics, Unicode and missing-list checks passed');
})().catch(error => {console.error(error); process.exitCode=1;});
