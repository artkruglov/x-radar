// X Radar — сбор постов со страницы X-списка.
// Запускать через javascript_tool на открытой странице https://x.com/i/lists/<id>
// Сохраняет посты в localStorage и возвращает счётчик. Дедупликация — по полю id на стороне записи.
//
// Поля: id, list_id, author, ts, link, text, is_repost, reposted_by, quoted_author,
//        quoted_text, replies, reposts, likes, views, has_media, collected_at

(async () => {
  const listId = (location.pathname.match(/lists\/(\d+)/) || [])[1];
  if (!listId || location.hostname !== 'x.com') throw new Error('Open an X list page first');
  const num = (s) => {
    if (!s) return null;
    const m = String(s).replace(/,/g, '').match(/([\d.]+)\s*([KkMm])?/);
    if (!m) return null;
    let v = parseFloat(m[1]);
    if (/k/i.test(m[2] || '')) v *= 1e3;
    if (/m/i.test(m[2] || '')) v *= 1e6;
    return Math.round(v);
  };
  const parseMetrics = (label) => {
    // "3 replies, 6 likes, 420 views" / "1 reply, 79 views" / "4 replies, 15 likes, 4 bookmarks, 1888 views"
    const out = { replies: 0, reposts: 0, likes: 0, views: 0 };
    if (!label) return out;
    label.split(',').forEach((part) => {
      const p = part.trim().toLowerCase();
      if (/repl/.test(p)) out.replies = num(p) || 0;
      else if (/repost|retweet/.test(p)) out.reposts = num(p) || 0;
      else if (/like/.test(p)) out.likes = num(p) || 0;
      else if (/view/.test(p)) out.views = num(p) || 0;
    });
    return out;
  };
  const grab = () =>
    [...document.querySelectorAll('article[data-testid="tweet"]')].map((a) => {
      const link = a.querySelector('a[href*="/status/"]')?.getAttribute('href') || '';
      const id = (link.match(/status\/(\d+)/) || [])[1] || '';
      const author = (link.match(/^\/([^\/]+)\/status/) || [])[1] || '';
      const ts = a.querySelector('time')?.getAttribute('datetime') || '';
      const texts = [...a.querySelectorAll('[data-testid="tweetText"]')].map((t) => t.innerText);
      const text = texts[0] || '';
      const quoted_text = texts[1] || '';
      const social = a.querySelector('[data-testid="socialContext"]')?.innerText || '';
      const is_repost = /repost|retweet/i.test(social);
      const reposted_by = is_repost ? social.replace(/\s*(reposted|retweeted).*/i, '').trim() : '';
      // цитируемый автор: ссылка на профиль внутри вложенного блока после основного текста
      let quoted_author = '';
      if (quoted_text) {
        const inner = [...a.querySelectorAll('a[href^="/"]')]
          .map((x) => x.getAttribute('href'))
          .filter((h) => /^\/[A-Za-z0-9_]{1,15}$/.test(h) && h.slice(1) !== author);
        quoted_author = inner[0]?.slice(1) || '';
      }
      const grp = a.querySelector('[role="group"][aria-label]')?.getAttribute('aria-label') || '';
      const m = parseMetrics(grp);
      const has_media = !!a.querySelector('[data-testid="tweetPhoto"], video, [data-testid="card.wrapper"]');
      return { id, list_id: listId, author, ts, link: link ? 'https://x.com' + link : '', text, is_repost, reposted_by, quoted_author, quoted_text, ...m, has_media };
    });

  // Бюджет времени: инструмент javascript_tool обрывает выполнение через 45 с.
  // Ожидание загрузки ~5 с + не больше 25 итераций по ~1 с = укладываемся в ~32 с.
  const acc = new Map();
  let stall = 0, prev = 0;
  const t0 = Date.now();
  for (let i = 0; i < 25 && Date.now() - t0 < 27000; i++) {
    grab().forEach((p) => { if (p.id) acc.set(p.id, p); });
    if (acc.size === prev) { stall++; if (stall > 5) break; } else stall = 0;
    prev = acc.size;
    window.scrollBy(0, 1400);
    await new Promise((r) => setTimeout(r, 1000));
  }
  grab().forEach((p) => { if (p.id) acc.set(p.id, p); });
  const collected_at = new Date().toISOString();
  const posts = [...acc.values()].map((p) => ({ ...p, collected_at }));
  localStorage.setItem('__xradar_' + listId, JSON.stringify(posts));
  return JSON.stringify({ list_id: listId, count: posts.length });
})();
