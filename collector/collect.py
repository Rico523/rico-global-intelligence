"""Bounded, standard-library RSS/Atom collector. No article bodies or AI."""
import concurrent.futures
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import time
import ssl
import sys
import signal
import os
import fcntl
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
MAX_ITEMS = 600
MAX_JSON = 1_000_000
MAX_FEED = 2_000_000
TIMEOUT = 10
USER_AGENT = 'RicoGlobalIntelligence/1.0 (personal RSS reader)'
# Markers are country reference points, never an alleged event location.
PLACES = {
 'Japan': (36, 138, ['japan', 'japanese']),
 'China': (35, 105, ['china', 'chinese']),
 'Taiwan': (23.7, 121, ['taiwan']),
 'South Korea': (36, 128, ['south korea']),
 'North Korea': (40, 127, ['north korea']),
 'India': (22, 79, ['india', 'indian']),
 'Singapore': (1.35, 103.82, ['singapore']),
 'Indonesia': (-2, 118, ['indonesia']),
 'Malaysia': (4, 102, ['malaysia']),
 'Thailand': (15, 101, ['thailand']),
 'Vietnam': (16, 108, ['vietnam']),
 'Philippines': (12, 122, ['philippines']),
 'Myanmar': (21, 96, ['myanmar']),
 'United States': (39, -98, ['united states', 'u.s.', 'usa']),
 'United Kingdom': (54, -2, ['united kingdom', 'britain', 'british', 'uk', 'u.k.']),
 'France': (47, 2, ['france', 'french']),
 'Germany': (51, 10, ['germany', 'german']),
 'Ukraine': (49, 32, ['ukraine', 'ukrainian']),
 'Russia': (60, 90, ['russia', 'russian']),
 'Israel': (31, 35, ['israel', 'israeli']),
 'Palestine': (31.9, 35.2, ['palestine', 'palestinian', 'gaza']),
 'Iran': (32, 54, ['iran', 'iranian']),
 'Lebanon': (34, 36, ['lebanon']),
 'Australia': (-25, 134, ['australia', 'australian']),
 'Brazil': (-14, -52, ['brazil', 'brazilian']),
 'South Africa': (-29, 25, ['south africa']),
 'Canada': (57, -106, ['canada', 'canadian']),
}
REGIONS = {'Asia': ['asia', 'asian'], 'Southeast Asia': ['southeast asia', 'asean'],
           'Europe': ['europe', 'european'], 'Middle East': ['middle east'],
           'Africa': ['africa', 'african']}
KEYWORDS = {
 'energy': ['oil', 'gas', 'energy', 'opec', 'electricity'],
 'trade': ['tariff', 'tariffs', 'trade', 'supply chain', 'shipping', 'export', 'exports', 'import', 'imports'],
 'technology': ['artificial intelligence', 'ai', 'technology', 'chip', 'chips', 'cyber', 'nasa'],
 'economy': ['inflation', 'economy', 'bank', 'banks', 'market', 'markets', 'finance', 'interest rate'],
 'politics': ['election', 'elections', 'war', 'military', 'diplomacy', 'sanction', 'sanctions', 'minister', 'ministers'],
}

def stamp():
    return dt.datetime.now(UTC).isoformat().replace('+00:00', 'Z')

def matches(text, terms):
    return any(re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', text, re.I) for w in terms)

def geography(title):
    countries = [name for name, (_, _, words) in PLACES.items() if matches(title, words)]
    if re.search(r'(?<!\w)US(?!\w)', title) and 'United States' not in countries:
        countries.append('United States')
    regions = [name for name, words in REGIONS.items() if matches(title, words)]
    # Cross-border stories have no single inferred coordinate.
    location = None
    if len(countries) == 1:
        lat, lon, _ = PLACES[countries[0]]
        location = {'lat': lat, 'lon': lon, 'kind': 'country_reference', 'label': countries[0]}
    return countries, regions, location

def category(title, default):
    return next((key for key, words in KEYWORDS.items() if matches(title, words)), default)

def date_value(value):
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try:
            parsed = dt.datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    if parsed.tzinfo is None:
        return None  # A timezone-less date is not an asserted UTC date.
    return parsed.astimezone(UTC)

def safe_url(value):
    try:
        parts = urllib.parse.urlsplit(value.strip())
    except (ValueError, AttributeError):
        return None
    if parts.scheme not in ('https', 'http') or not parts.hostname or parts.username or parts.password:
        return None
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.startswith('utm_') and k not in ('fbclid', 'gclid')]
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, urllib.parse.urlencode(query), ''))

def parse_feed(raw, source, now=None):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('DTD/entity forbidden')
    root = ET.fromstring(raw)
    local = lambda tag: tag.rsplit('}', 1)[-1]
    if local(root.tag) not in ('rss', 'feed', 'RDF'):
        raise ValueError('Not RSS/Atom')
    entries = [e for e in root.iter() if local(e.tag) in ('item', 'entry')][:100]
    result = []
    now = now or dt.datetime.now(UTC)
    for entry in entries:
        fields = {}
        link = None
        for child in entry:
            name = local(child.tag)
            fields[name] = ''.join(child.itertext()).strip()
            if name == 'link' and (child.get('rel', 'alternate') == 'alternate'):
                candidate = child.get('href') or fields[name]
                link = safe_url(candidate)
        title = re.sub(r'<[^>]*>', '', html.unescape(fields.get('title', ''))).strip()[:500]
        published = date_value(fields.get('pubDate') or fields.get('published') or fields.get('date') or fields.get('updated', ''))
        if not title or not link or not published or published > now + dt.timedelta(minutes=10):
            continue
        if published < now - dt.timedelta(days=14):
            continue
        countries, regions, location = geography(title)
        result.append({'id': hashlib.sha256(link.encode()).hexdigest()[:20], 'title': title,
                       'url': link, 'source': source['name'], 'source_id': source['id'],
                       'published_at': published.isoformat().replace('+00:00', 'Z'),
                       'category': category(title, source['category']), 'countries': countries,
                       'regions': regions, 'location': location})
    return result

class BoundedRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 2
    max_repeats = 1

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != 'https':
            raise ValueError('Redirect must remain HTTPS')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def tls_context():
    # Python.org builds on macOS may lack their own CA bundle. Use the OS bundle.
    context = ssl.create_default_context()
    if sys.platform == 'darwin' and Path('/etc/ssl/cert.pem').exists():
        context.load_verify_locations('/etc/ssl/cert.pem')
    return context


def request(url, limit):
    start = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/plain'})
    opener = urllib.request.build_opener(BoundedRedirect(), urllib.request.HTTPSHandler(context=tls_context()))
    with opener.open(req, timeout=TIMEOUT) as response:
        chunks = bytearray()
        while len(chunks) <= limit:
            if time.monotonic() - start > TIMEOUT:
                raise TimeoutError('Response time limit')
            chunk = response.read(min(65536, limit + 1 - len(chunks)))
            if not chunk:
                return bytes(chunks)
            chunks.extend(chunk)
        raise ValueError('Response size limit')

def fetch(source):
    started = time.monotonic()
    status = {'id': source['id'], 'name': source['name'], 'url': source['url'], 'checked_at': stamp()}
    try:
        parts = urllib.parse.urlsplit(source['url'])
        if parts.scheme != 'https':
            raise ValueError('Feed must use HTTPS')
        robots_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, '/robots.txt', '', ''))
        try:
            robots = request(robots_url, 300000)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            robots = b''
        rules = urllib.robotparser.RobotFileParser()
        rules.parse(robots.decode('utf-8', 'replace').splitlines())
        if not rules.can_fetch(USER_AGENT, source['url']):
            raise ValueError('RSS access disallowed by robots.txt')
        delay = rules.crawl_delay(USER_AGENT) or 0
        if delay > 10:
            raise ValueError('Crawl delay exceeds bounded collection budget')
        if delay:
            time.sleep(delay)
        items = parse_feed(request(source['url'], MAX_FEED), source)
        if not items:
            raise ValueError('No valid dated items within 14 days')
        status.update(ok=True, count=len(items), error=None)
        return items, status
    except Exception as error:
        status.update(ok=False, count=0, error=f'{type(error).__name__}: {str(error)[:180]}')
        return [], status
    finally:
        status['duration_seconds'] = round(time.monotonic() - started, 2)

def merge(items, now=None):
    now = now or dt.datetime.now(UTC)
    urls, titles, result = set(), set(), []
    for item in sorted(items, key=lambda x: date_value(x['published_at']) or dt.datetime.min.replace(tzinfo=UTC), reverse=True):
        published = date_value(item['published_at'])
        if not published or not now - dt.timedelta(days=14) <= published <= now + dt.timedelta(minutes=10):
            continue
        title = re.sub(r'\W+', '', item['title'].casefold())
        if item['url'] in urls or title in titles:
            continue
        urls.add(item['url']); titles.add(title); result.append(item)
        if len(result) == MAX_ITEMS:
            break
    return result

def encode_bounded(payload):
    while True:
        data = (json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
        if len(data) <= MAX_JSON:
            return data
        if not payload['items']:
            raise ValueError('Status metadata exceeds data limit')
        payload['items'].pop()

def validate_payload(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise ValueError('Invalid payload')
    if len(payload['items']) > MAX_ITEMS:
        raise ValueError('Too many items')
    if payload.get('status') not in ('ok', 'partial', 'failed') or not date_value(payload.get('updated_at', '')):
        raise ValueError('Invalid status timestamp')
    if not isinstance(payload.get('sources'), list) or len(payload['sources']) > 120:
        raise ValueError('Invalid source statuses')
    for item in payload['items']:
        if not all(isinstance(item.get(k), str) for k in ('id', 'title', 'url', 'source', 'source_id', 'category', 'published_at')):
            raise ValueError('Invalid item fields')
        if not safe_url(item['url']) or not date_value(item['published_at']):
            raise ValueError('Invalid item URL/date')
        if not all(isinstance(item.get(k), list) and all(isinstance(v, str) for v in item[k]) for k in ('countries', 'regions')):
            raise ValueError('Invalid geography')
        if item.get('location'):
            loc = item['location']
            if not isinstance(loc, dict):
                raise ValueError('Invalid location object')
            if len(item['countries']) != 1 or loc.get('label') != item['countries'][0] or loc.get('kind') != 'country_reference':
                raise ValueError('Unsubstantiated location')
            expected = PLACES.get(loc['label'])
            if not expected or (loc.get('lat'), loc.get('lon')) != expected[:2]:
                raise ValueError('Invalid country reference')


def alarm_timeout(signum, frame):
    print('150-second collection deadline exceeded; existing atomic data preserved', file=sys.stderr, flush=True)
    os._exit(124)


def main():
    sources = json.loads((ROOT / 'config/sources.json').read_text())
    if not 1 <= len(sources) <= 120 or len({s['id'] for s in sources}) != len(sources):
        raise ValueError('1–120 sources with unique IDs required')
    target = ROOT / 'site/data/news.json'
    previous = {'items': [], 'last_success_at': None}
    if target.exists():
        try:
            if target.stat().st_size > MAX_JSON:
                raise ValueError('Previous file too large')
            previous = json.loads(target.read_text())
            validate_payload(previous)
        except (ValueError, OSError) as error:
            print(f'Ignoring invalid prior data: {type(error).__name__}', file=sys.stderr)
            previous = {'items': [], 'last_success_at': None}
    collected, statuses = [], []
    # Four workers; two logical requests/source, each at most two redirects; no retry.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for items, status in pool.map(fetch, sources):
            collected.extend(items); statuses.append(status)
    success = any(s['ok'] for s in statuses)
    payload = {'updated_at': stamp(), 'last_success_at': stamp() if success else previous.get('last_success_at'),
               'status': 'ok' if all(s['ok'] for s in statuses) else 'partial' if success else 'failed',
               'sources': statuses, 'items': merge(collected + previous['items'])}
    # Never retain items from removed sources.
    allowed = {s['id'] for s in sources}
    defaults = {s['id']: s['category'] for s in sources}
    payload['items'] = [n for n in payload['items'] if n['source_id'] in allowed]
    # Recompute rule labels when rules improve.
    for item in payload['items']:
        item['countries'], item['regions'], item['location'] = geography(item['title'])
        item['category'] = category(item['title'], defaults[item['source_id']])
    data = encode_bounded(payload)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.tmp'); temp.write_bytes(data); temp.replace(target)
    # At most two prior snapshots; all capped at MAX_JSON. Not committed by workflow.
    history = target.parent / 'history'; history.mkdir(exist_ok=True)
    for old in sorted(history.glob('*.json'))[:-1]:
        old.unlink()
    if previous.get('updated_at'):
        key = re.sub(r'[^0-9]', '', previous['updated_at'])
        (history / f'{key}.json').write_bytes(encode_bounded(previous))
    payload['history_keys'] = [f.stem for f in sorted(history.glob('*.json'))]
    temp.write_bytes(encode_bounded(payload)); temp.replace(target)
    print(json.dumps({'items': len(payload['items']), 'bytes': len(data), 'status': payload['status'], 'sources': statuses}, ensure_ascii=False, indent=2))
    return 0 if success else 1

if __name__ == '__main__':
    signal.signal(signal.SIGALRM, alarm_timeout)
    signal.alarm(150)
    try:
        with (ROOT / '.collector.lock').open('w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print('Another collector is already running', file=sys.stderr)
                raise SystemExit(75)
            raise SystemExit(main())
    finally:
        signal.alarm(0)
