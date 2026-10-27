#!/usr/bin/env python3
"""Generate one image via OpenRouter's images endpoint (default model: openai/gpt-image-2.5-sunburst).
Usage: genimg.py <out.png> "<prompt>" [--size 1024x1536] [--model openai/gpt-image-2.5-sunburst]
Key: $OPENROUTER_API_KEY. Prints cost. Image models in OpenRouter that are image-only (like Sunburst)
reject /chat/completions — this script uses /api/v1/images."""
import json, urllib.request, base64, sys, os, argparse
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('prompt')
ap.add_argument('--size', default='1024x1536'); ap.add_argument('--model', default=os.environ.get('XRADAR_IMAGE_MODEL', 'openai/gpt-image-2.5-sunburst'))
a = ap.parse_args()
key = os.environ.get('OPENROUTER_API_KEY') or sys.exit('set OPENROUTER_API_KEY')
body = {"model": a.model, "prompt": a.prompt, "n": 1, "size": a.size, "quality": "high"}
req = urllib.request.Request('https://openrouter.ai/api/v1/images', data=json.dumps(body).encode(),
      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=600))
except Exception as e:
    sys.exit(f"ERR {getattr(e, 'read', lambda: b'')()[:400]}")
d = r['data'][0]
if d.get('b64_json'): open(a.out, 'wb').write(base64.b64decode(d['b64_json']))
elif d.get('url', '').startswith('data:'): open(a.out, 'wb').write(base64.b64decode(d['url'].split(',', 1)[1]))
else: urllib.request.urlretrieve(d['url'], a.out)
print(a.out, 'cost', r.get('usage', {}).get('cost'))
