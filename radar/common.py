"""Shared settings. Relative paths resolve against the selected configuration file."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_config(path=None):
    source = Path(path or os.environ.get('XRADAR_CONFIG', ROOT / 'config.json')).expanduser().resolve()
    if not source.is_file():
        raise ValueError('Configuration missing. Copy config.example.json to config.json or pass --config.')
    settings = json.loads(source.read_text(encoding='utf-8'))
    for key in ('data_dir', 'lists', 'roster', 'tracks'):
        value = settings.get('paths', {}).get(key)
        if not value:
            raise ValueError(f'Configuration missing paths.{key}')
        settings['paths'][key] = (source.parent / Path(value).expanduser()).resolve()
    return settings


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_posts(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError('expected an object')
            rows.append(row)
        except (ValueError, TypeError) as error:
            raise ValueError(f'Invalid JSONL at line {number}: {error}') from None
    return rows
