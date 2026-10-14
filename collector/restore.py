"""Restore previous public Pages data without a cache or Git commit."""
import json
import os
import re
import urllib.error
from collect import ROOT, MAX_JSON, request, validate_payload

def main():
    repo = os.environ.get('RICO_REPOSITORY', '')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository identity')
    owner, name = repo.split('/')
    prefix = '' if name.lower() == f'{owner.lower()}.github.io' else f'/{name}'
    base = f'https://{owner.lower()}.github.io{prefix}/data'
    # One current file and up to two known snapshots; no retries or cache.
    target = ROOT / 'site/data/news.json'
    try:
        raw = request(f'{base}/news.json', MAX_JSON)
        payload = json.loads(raw)
        validate_payload(payload)
    except (ValueError, OSError, urllib.error.URLError) as error:
        print(f'Previous deployment unavailable; using checked-in seed: {type(error).__name__}')
        return
    target.write_bytes(raw)
    history = target.parent / 'history'
    history.mkdir(exist_ok=True)
    for file in history.glob('*.json'):
        file.unlink()
    for key in payload.get('history_keys', [])[:2]:
        if not re.fullmatch(r'\d{14,24}', key):
            continue
        try:
            raw = request(f'{base}/history/{key}.json', MAX_JSON)
            validate_payload(json.loads(raw))
            (history / f'{key}.json').write_bytes(raw)
        except (ValueError, OSError, urllib.error.URLError):
            print(f'History unavailable: {key}')

if __name__ == '__main__':
    main()
