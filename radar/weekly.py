#!/usr/bin/env python3
"""X-радар — фактпак за период для еженедельного разбора.

    python3 weekly.py            # последние 7 дней
    python3 weekly.py 14         # последние 14 дней
    python3 weekly.py 7 --json   # машинно-читаемый вывод

Считает по data/posts.jsonl: объём по спискам и авторам, топ по вовлечённости,
кто кого репостит и цитирует (граф усиления), новые имена вне наших списков,
частотность @упоминаний и ключевых слов, сравнение с предыдущим периодом.
Интерпретацию не делает — это работа Claude поверх этого фактпака.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from common import load_config, read_json, read_posts

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('days', nargs='?', type=int, default=7)
parser.add_argument('--json', action='store_true')
parser.add_argument('--config')
parser.add_argument('--now', help='ISO date/time with timezone; useful for reproducible examples')
args = parser.parse_args()
if args.days <= 0:
    parser.error('days must be positive')
try:
    config = load_config(args.config)
    now = datetime.fromisoformat(args.now.replace('Z', '+00:00')) if args.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('--now must include a timezone')
except (ValueError, OSError) as error:
    parser.error(str(error))
DB = config['paths']['data_dir'] / 'posts.jsonl'
LISTS = config['paths']['lists']
ROSTER = config['paths']['roster']
days = args.days
as_json = args.json

since = now - timedelta(days=days)
prev_since = since - timedelta(days=days)

lists = {str(row['id']): row for row in read_json(LISTS)['lists']}
roster = {handle.lower() for handle in read_json(ROSTER)['handles']}
posts = read_posts(DB)

def ts(p):
    try:
        stamp = datetime.fromisoformat(p["ts"].replace("Z", "+00:00"))
        return stamp if stamp.tzinfo else None
    except Exception:
        return None

cur = [p for p in posts if (t := ts(p)) and since <= t <= now]
prev = [p for p in posts if (t := ts(p)) and prev_since <= t < since]

# Пост в списке от автора вне ростера — это репост участника списка, у которого X не отрисовал
# маркер "reposted". Считаем его усилением, а не авторством.
if roster:
    for p in cur + prev:
        if not p.get("is_repost") and p.get("author", "").lower() not in roster:
            p["is_repost"] = True
            p["reposted_by"] = p.get("reposted_by") or "(участник списка)"

def eng(p):
    return (p.get("likes") or 0) + 3 * (p.get("reposts") or 0) + 2 * (p.get("replies") or 0)

# --- объём
by_list = Counter(lists.get(p["list_id"], {}).get("name", p["list_id"]) for p in cur)
by_list_prev = Counter(lists.get(p["list_id"], {}).get("name", p["list_id"]) for p in prev)
by_author = Counter(p["author"] for p in cur if not p.get("is_repost"))
reposters = Counter(p["reposted_by"] for p in cur if p.get("is_repost") and p.get("reposted_by"))

# --- усиление: кто кого выносит наверх
amplified = Counter(p["author"] for p in cur if p.get("is_repost"))
quoted = Counter(p["quoted_author"] for p in cur if p.get("quoted_author"))
mentions = Counter()
for p in cur:
    for h in re.findall(r"@([A-Za-z0-9_]{2,15})", (p.get("text") or "") + " " + (p.get("quoted_text") or "")):
        mentions[h] += 1

outsiders = Counter()
for name, c in list(amplified.items()) + list(quoted.items()) + list(mentions.items()):
    if name and name.lower() not in roster:
        outsiders[name] += c

# --- ключевые слова (грубо): слова длиннее 4 букв, без стоп-слов
STOP = set("""about after again against being below between both could every first from have here into just
like more most much never only other over same should since some such than that their them then there these
they this those through under until very were what when where which while will with would your https http
that's it's don't doesn't there's what's i'm we're you're they're can't won't""".split())
words = Counter()
for p in cur:
    for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{4,}", (p.get("text") or "").lower()):
        if w not in STOP:
            words[w] += 1
words_prev = Counter()
for p in prev:
    for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{4,}", (p.get("text") or "").lower()):
        if w not in STOP:
            words_prev[w] += 1
rising = sorted(((w, c, words_prev.get(w, 0)) for w, c in words.items() if c >= 3),
                key=lambda x: (x[1] - x[2], x[1]), reverse=True)[:25]

# --- тишина: кто из ростера не написал ничего
silent = sorted(h for h in roster if h not in {a.lower() for a in by_author} and h not in {r.lower() for r in reposters})

top = sorted(cur, key=eng, reverse=True)[:20]

out = {
    "period": {"from": since.date().isoformat(), "to": now.date().isoformat(), "days": days},
    "volume": {"posts": len(cur), "posts_prev": len(prev), "originals": sum(1 for p in cur if not p.get("is_repost")),
               "reposts": sum(1 for p in cur if p.get("is_repost"))},
    "by_list": [{"list": k, "now": v, "prev": by_list_prev.get(k, 0)} for k, v in by_list.most_common()],
    "by_author": by_author.most_common(25),
    "reposters": reposters.most_common(15),
    "amplified_accounts": amplified.most_common(15),
    "quoted_accounts": quoted.most_common(15),
    "mentions": mentions.most_common(20),
    "outsiders_surfacing": outsiders.most_common(20),
    "rising_terms": rising,
    "silent_roster": silent,
    "top_posts": [{"author": p["author"], "via": p.get("reposted_by") or "", "eng": eng(p), "likes": p.get("likes"),
                   "reposts": p.get("reposts"), "views": p.get("views"), "list": lists.get(p["list_id"], {}).get("name", ""),
                   "ts": p["ts"][:10], "link": p["link"], "text": (p.get("text") or "")[:220].replace("\n", " "),
                   "quoted": (p.get("quoted_text") or "")[:160].replace("\n", " ")} for p in top],
}

if as_json:
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0)

print(f"# X-радар — фактпак {out['period']['from']} → {out['period']['to']} ({days} дн.)\n")
v = out["volume"]
print(f"Постов: {v['posts']} (пред. период: {v['posts_prev']}) · оригинальных {v['originals']} · репостов {v['reposts']}\n")
print("## По спискам (сейчас / пред.)")
for r in out["by_list"]:
    print(f"- {r['list']}: {r['now']} / {r['prev']}")
print("\n## Кто писал (оригиналы)")
print(", ".join(f"{a} {c}" for a, c in out["by_author"]))
print("\n## Кто репостил")
print(", ".join(f"{a} {c}" for a, c in out["reposters"]) or "—")
print("\n## Кого выносили наверх (репост/цитата)")
print("repost:", ", ".join(f"{a} {c}" for a, c in out["amplified_accounts"]) or "—")
print("quote: ", ", ".join(f"{a} {c}" for a, c in out["quoted_accounts"]) or "—")
print("\n## Новые имена вне наших списков (кандидаты)")
print(", ".join(f"{a} {c}" for a, c in out["outsiders_surfacing"]) or "—")
print("\n## Растущие термины (сейчас, пред.)")
print(", ".join(f"{w} {c}/{pc}" for w, c, pc in out["rising_terms"]) or "—")
print("\n## Молчали из ростера")
print(", ".join(out["silent_roster"]) or "—")
print("\n## Топ-20 по вовлечённости")
for p in out["top_posts"]:
    via = f" (via {p['via']})" if p["via"] else ""
    print(f"- [{p['eng']}] {p['author']}{via} · {p['list']} · {p['ts']}\n  {p['text']}")
    if p["quoted"]:
        print(f"  ↳ «{p['quoted']}»")
    print(f"  {p['link']}")

# --- полный материал: все посты периода по спискам, для написания дайджеста без обращения к базе
print("\n\n# ПОЛНЫЙ МАТЕРИАЛ ПО СПИСКАМ (все посты периода, хронологически)")
by_list_posts = defaultdict(list)
for p in cur:
    by_list_posts[p["list_id"]].append(p)
for lid, l in sorted(lists.items(), key=lambda kv: kv[1]["n"]):
    ps = sorted(by_list_posts.get(lid, []), key=lambda p: p["ts"])
    print(f"\n## {l['n']} · {l['name']} — {len(ps)} постов")
    if not ps:
        print("(пусто)")
        continue
    for p in ps:
        via = f" [RT by {p.get('reposted_by')}]" if p.get("is_repost") else ""
        text = (p.get("text") or "").replace("\n", " ").strip()
        q = (p.get("quoted_text") or "").replace("\n", " ").strip()
        qa = p.get("quoted_author") or ""
        print(f"- {p['ts'][:10]} @{p['author']}{via} · ♥{p.get('likes', 0)} 👁{p.get('views', 0)} · {p['link']}")
        print(f"  {text[:600]}")
        if q:
            print(f"  ↳ цитирует @{qa}: {q[:350]}")
