"""Offline integration checks: only temporary data and fictional fixtures."""
import base64
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.data = self.base / 'data'
        config = {'paths': {'data_dir': 'data', 'lists': str(ROOT / 'examples/lists.json'), 'roster': str(ROOT / 'examples/roster.json'), 'tracks': str(ROOT / 'tracks.example.json')}}
        self.config = self.base / 'config.json'
        self.config.write_text(json.dumps(config))
        self.posts = (ROOT / 'examples/posts.jsonl').read_text()

    def run_script(self, name, *args, input='', success=True):
        result = subprocess.run([sys.executable, str(ROOT / 'radar' / name), *args, '--config', str(self.config)], input=input, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_ingest_deduplicates_array_and_jsonl(self):
        first = self.run_script('ingest.py', input=self.posts)
        self.assertIn('new=8', first.stdout)
        array = json.dumps([json.loads(line) for line in self.posts.splitlines()])
        second = self.run_script('ingest.py', input=array)
        self.assertIn('new=0 dup=8 total=8', second.stdout)
        self.assertEqual(len((self.data / 'posts.jsonl').read_text().splitlines()), 8)

    def test_invalid_input_preserves_database(self):
        self.run_script('ingest.py', input=self.posts)
        before = (self.data / 'posts.jsonl').read_bytes()
        self.run_script('ingest.py', input=self.posts + '{broken', success=False)
        self.run_script('ingest.py', input='[{"id":"invalid"}]', success=False)
        self.assertEqual((self.data / 'posts.jsonl').read_bytes(), before)

    def test_concurrent_ingest_keeps_one_copy(self):
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.run_script('ingest.py', input=self.posts), range(2)))
        self.assertEqual(len((self.data / 'posts.jsonl').read_text().splitlines()), 8)
        self.assertEqual(sum('new=8' in r.stdout for r in results), 1)

    def test_pull_accepts_wrapped_export_and_rejects_bad_base64(self):
        encoded = base64.b64encode(self.posts.encode()).decode()
        wrapped = json.dumps([{'type':'text', 'text':json.dumps('.' * 10 + '#' + encoded)}])
        self.assertIn('new=8', self.run_script('pull.py', input=wrapped).stdout)
        self.run_script('pull.py', input='not base64!', success=False)
        self.assertEqual(len((self.data / 'posts.jsonl').read_text().splitlines()), 8)

    def test_weekly_current_and_previous_windows(self):
        self.run_script('ingest.py', input=self.posts)
        result = self.run_script('weekly.py', '7', '--now', '2026-10-27T00:00:00Z', '--json')
        pack = json.loads(result.stdout)
        self.assertEqual(pack['volume']['posts'], 7)
        self.assertEqual(pack['volume']['posts_prev'], 1)
        self.assertTrue(all('example.com' in row['link'] for row in pack['top_posts']))
        self.assertIn('ПОЛНЫЙ МАТЕРИАЛ', self.run_script('weekly.py', '--now', '2026-10-27T00:00:00Z').stdout)
        self.run_script('weekly.py', '0', success=False)
        self.run_script('weekly.py', '--now', '2026-10-27', success=False)

    def test_labels_then_pick_and_invalid_labels(self):
        self.run_script('ingest.py', input=self.posts)
        labels = (ROOT / 'examples/labels.json').read_text()
        self.assertIn('записано 8', self.run_script('topics.py', 'write', input=labels).stdout)
        stats = self.run_script('topics.py', 'stats', '--from', '2026-10-20').stdout
        self.assertIn('неразмечено 0', stats)
        picks = self.run_script('topics.py', 'pick', '--track', 'WORK', '--full').stdout
        self.assertIn('https://example.com/posts/1005', picks)
        self.assertNotIn('https://example.com/posts/1002', picks)
        before = (self.data / 'topics.jsonl').read_bytes()
        self.run_script('topics.py', 'write', input='[{"link":"https://example.com/unknown","track":"CODE"}]', success=False)
        self.assertEqual((self.data / 'topics.jsonl').read_bytes(), before)

    def test_empty_database_is_valid(self):
        pack = json.loads(self.run_script('weekly.py', '--json').stdout)
        self.assertEqual(pack['volume']['posts'], 0)
        self.assertIn('неразмечено всего: 0', self.run_script('topics.py', 'dump').stdout)

    def test_scan_reads_list_numbers_from_fixture(self):
        script = ROOT / 'skills/tg-news-stories/scripts/radar_scan.py'
        result = subprocess.run([sys.executable, str(script), str(ROOT/'examples/posts.jsonl'), '--from','2026-10-20','--to','2026-10-26','--lists-file', str(ROOT/'examples/lists.json'),'--lists','7,10','--full'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('https://example.com/posts/1005', result.stdout)
        self.assertIn('# 1 posts matched', result.stdout)


if __name__ == '__main__':
    unittest.main()
