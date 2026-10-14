"""One tiny maintenance commit only after 30 days without commits; no news data."""
import base64
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request

PATH = 'maintenance/automation.json'

def api(repo, token, path, body=None):
    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/{path}',
        data=json.dumps(body).encode() if body else None,
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'RicoGlobalIntelligence',
                 'Content-Type': 'application/json'}, method='PUT' if body else 'GET')
    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError('API response limit')
        return json.loads(raw)

def main():
    repo, token = os.environ['RICO_REPOSITORY'], os.environ['GITHUB_TOKEN']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository')
    now = dt.datetime.now(dt.timezone.utc)
    latest = api(repo, token, 'commits?per_page=1')[0]
    last = dt.datetime.fromisoformat(latest['commit']['committer']['date'].replace('Z', '+00:00'))
    if now - last < dt.timedelta(days=30):
        print('Recent repository activity; no maintenance commit needed.')
        return
    sha = None
    try:
        sha = api(repo, token, f'contents/{PATH}')['sha']
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    content = json.dumps({'last_maintenance': now.date().isoformat()}, separators=(',', ':'))+'\n'
    body = {'message': 'chore: maintain scheduled publishing activity',
            'content': base64.b64encode(content.encode()).decode()}
    if sha:
        body['sha'] = sha
    api(repo, token, f'contents/{PATH}', body)
    print('One maintenance commit created; news data was not committed.')

if __name__ == '__main__':
    main()
