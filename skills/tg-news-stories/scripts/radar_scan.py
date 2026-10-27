#!/usr/bin/env python3
"""Pick news candidates by date, optional list numbers and keywords; no API calls."""
import argparse
import json
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('posts')
parser.add_argument('--from', dest='start', required=True)
parser.add_argument('--to', dest='end', required=True)
parser.add_argument('--lists')
parser.add_argument('--lists-file', help='JSON with lists [{id,n,name}]')
parser.add_argument('--kw')
parser.add_argument('--top', type=int, default=40)
parser.add_argument('--full', action='store_true')
args = parser.parse_args()
if args.lists and not args.lists_file:
    parser.error('--lists requires --lists-file')
with open(args.lists_file, encoding='utf-8') if args.lists_file else open(__file__, encoding='utf-8') as source:
    mapping = {str(row['id']):str(row['n']) for row in json.load(source)['lists']} if args.lists_file else {}
want = set(args.lists.split(',')) if args.lists else None
pattern = re.compile(args.kw, re.I) if args.kw else None
rows, seen = [], set()
with open(args.posts, encoding='utf-8') as source:
    for line in source:
        if not line.strip():
            continue
        post = json.loads(line)
        if not args.start <= post['ts'][:10] <= args.end or post['link'] in seen:
            continue
        if want and mapping.get(str(post['list_id'])) not in want:
            continue
        if pattern and not pattern.search(post['text'] + ' ' + (post.get('quoted_text') or '')):
            continue
        seen.add(post['link'])
        rows.append(post)
rows.sort(key=lambda p: -(p.get('views') or 0))
for post in rows[:args.top]:
    text = post['text'].replace('\n', ' ')
    print(f"L{mapping.get(str(post['list_id']), '?')} {post['ts'][:10]} @{post['author']} | {text if args.full else text[:220]} | {post['link']}")
print(f'# {len(rows)} posts matched')
