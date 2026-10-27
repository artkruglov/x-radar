// Set globalThis.__XRADAR_LIST_IDS to configured, successfully collected list IDs first.
(() => {
  const ids = globalThis.__XRADAR_LIST_IDS;
  if (!Array.isArray(ids) || !ids.length || ids.some(id => typeof id !== 'string' || !/^\d+$/.test(id))) {
    throw new Error('Set __XRADAR_LIST_IDS to an array of configured numeric list IDs');
  }
  const posts = ids.flatMap(id => {
    const raw = localStorage.getItem('__xradar_' + id);
    if (raw === null) throw new Error('Missing collection for configured list');
    return JSON.parse(raw);
  });
  const bytes = new TextEncoder().encode(posts.map(post => JSON.stringify(post)).join('\n'));
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return '#' + btoa(binary);
})();
