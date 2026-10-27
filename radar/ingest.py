#!/usr/bin/env python3
"""Receive JSONL or a JSON array from stdin; append new post IDs once."""
import argparse
import fcntl
import json
import sys
from datetime import datetime, timezone
from common import load_config, read_posts


def validate(rows):
    if not isinstance(rows, list):
        raise ValueError('Expected a JSON array or JSONL')
    for number, post in enumerate(rows, 1):
        if not isinstance(post, dict):
            raise ValueError(f'Record {number}: expected an object')
        for field in ('id', 'list_id', 'author', 'ts', 'link', 'text'):
            if not isinstance(post.get(field), str) or not post[field].strip():
                raise ValueError(f'Record {number}: {field} must be a nonempty string')
        try:
            stamp = datetime.fromisoformat(post['ts'].replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise ValueError()
        except ValueError:
            raise ValueError(f'Record {number}: ts must include a timezone') from None
        for field in ('likes', 'replies', 'reposts', 'views'):
            value = post.get(field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f'Record {number}: {field} must be a nonnegative integer or null')
    return rows


def ingest(raw, settings):
    text = raw.strip()
    rows = json.loads(text) if text.startswith('[') else [json.loads(line) for line in text.splitlines() if line.strip()]
    validate(rows)  # Validate the entire input before touching the database.
    data = settings['paths']['data_dir']
    data.mkdir(parents=True, exist_ok=True)
    with (data / '.ingest.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        db = data / 'posts.jsonl'
        existing = {post['id'] for post in read_posts(db)}
        fresh = []
        for post in rows:
            if post['id'] not in existing:
                fresh.append(post)
                existing.add(post['id'])
        if fresh:
            payload = ''.join(json.dumps(post, ensure_ascii=False) + '\n' for post in fresh)
            with db.open('a', encoding='utf-8') as target:
                target.write(payload)
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        summary = f'{now} received={len(rows)} new={len(fresh)} dup={len(rows)-len(fresh)} total={len(existing)}'
        with (data / 'ingest.log').open('a', encoding='utf-8') as log:
            log.write(summary + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    args = parser.parse_args()
    try:
        print(ingest(sys.stdin.read(), load_config(args.config)))
    except (OSError, ValueError, KeyError) as error:
        sys.exit(str(error))
