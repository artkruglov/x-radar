#!/usr/bin/env python3
"""Decode a collector export from a file or stdin and feed it directly to ingest."""
import argparse
import base64
import json
import sys
from pathlib import Path
from common import load_config
from ingest import ingest


def decode(raw):
    text = raw.strip()
    # Accept a tool text block, a list of text blocks, or a quoted JS return value.
    for _ in range(4):
        try:
            value = json.loads(text)
        except ValueError:
            break
        if isinstance(value, list) and value and isinstance(value[0], dict) and 'text' in value[0]:
            text = value[0]['text']
        elif isinstance(value, dict) and 'text' in value:
            text = value['text']
        elif isinstance(value, str):
            text = value
        else:
            raise ValueError('Expected base64 export, not raw posts (use ingest.py for JSONL)')
    text = text.rsplit('#', 1)[-1]
    if not text.strip():
        raise ValueError('Empty collector export')
    return base64.b64decode(''.join(text.split()), validate=True).decode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', nargs='?', help='export file; otherwise read stdin')
    parser.add_argument('--config')
    args = parser.parse_args()
    try:
        raw = Path(args.file).read_text(encoding='utf-8') if args.file else sys.stdin.read()
        print(ingest(decode(raw), load_config(args.config)))
    except (ValueError, OSError, KeyError) as error:
        sys.exit(str(error))
