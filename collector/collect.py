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
import threading
import zlib
from collections import defaultdict, deque
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
WORKERS = 12
RUN_BUDGET = 125
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
# Conservative full names only: no ambiguous single-character country abbreviations.
CJK_PLACES = {
 'Japan':['日本'], 'China':['中国','中國'], 'Taiwan':['台湾','臺灣','台灣'],
 'Hong Kong':['香港'], 'South Korea':['韩国','韓國','韓国'], 'North Korea':['朝鲜','北朝鮮'],
 'India':['印度','インド政府'], 'Singapore':['新加坡','シンガポール'],
 'Indonesia':['印度尼西亚','印度尼西亞','印尼','インドネシア'],
 'Malaysia':['马来西亚','馬來西亞','マレーシア'], 'Thailand':['泰国','泰國','タイ政府'],
 'Vietnam':['越南','ベトナム'], 'Philippines':['菲律宾','菲律賓','フィリピン'],
 'Myanmar':['缅甸','緬甸','ミャンマー'], 'Cambodia':['柬埔寨','カンボジア'],
 'Laos':['老挝','寮國','ラオス'], 'United States':['美国','美國','米国'],
 'United Kingdom':['英国','英國'], 'France':['法国','法國','フランス'],
 'Germany':['德国','德國','ドイツ'], 'Ukraine':['乌克兰','烏克蘭','ウクライナ'],
 'Russia':['俄罗斯','俄羅斯','ロシア'], 'Iran':['伊朗','イラン'],
 'Australia':['澳大利亚','澳洲','オーストラリア'],
}
PLACES.update({'Hong Kong':(22.3,114.2,['hong kong']),
               'Cambodia':(12.6,104.9,['cambodia']), 'Laos':(19.9,102.5,['laos'])})
for place, words in CJK_PLACES.items():
    PLACES[place][2].extend(words)
REGIONS['Asia'] += ['亚洲','亞洲','アジア']
REGIONS['Southeast Asia'] += ['东南亚','東南亞','東南アジア','东盟','東協']
KEYWORDS['energy'] += ['能源','石油','天然气','天然氣','エネルギー','原油','電力']
KEYWORDS['trade'] += ['贸易','貿易','关税','關稅','関税','供应链','供應鏈','サプライチェーン','輸出','出口']
KEYWORDS['technology'] += ['科技','人工智能','人工智慧','半导体','半導體','半導体','技術','サイバー']
KEYWORDS['economy'] += ['经济','經濟','経済','金融','银行','銀行','通胀','通膨','インフレ','金利']
KEYWORDS['politics'] += ['选举','選舉','選挙','外交','战争','戰爭','戦争','大臣','制裁']

def stamp():
    return dt.datetime.now(UTC).isoformat().replace('+00:00', 'Z')

def matches(text, terms):
    return any(w in text if re.search(r'[\u3040-\u30ff\u3400-\u9fff]', w)
               else re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', text, re.I) for w in terms)

def geography(title):
    countries = [name for name, (_, _, words) in PLACES.items()
                 if matches(title.replace('印度尼西亚', '').replace('印度尼西亞', '') if name == 'India'
                            else title.replace('中国地方', '').replace('中國地方', '') if name == 'China' else title, words)]
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

def parse_feed(raw, source, now=None, diagnostics=None):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('DTD/entity forbidden')
    encoding = re.search(br'<\?xml[^>]*encoding=[\"\x27]([^\"\x27]+)', raw[:250], re.I)
    encoding = encoding[1].decode('ascii') if encoding else 'utf-8-sig'
    # Expat cannot decode some multibyte legacy RSS encodings itself.
    text = raw.decode(encoding, 'strict') if not raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-16')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('DTD/entity forbidden')
    root = ET.fromstring(text)
    local = lambda tag: tag.rsplit('}', 1)[-1]
    if local(root.tag) not in ('rss', 'feed', 'RDF'):
        raise ValueError('Not RSS/Atom')
    entries = [e for e in root.iter() if local(e.tag) in ('item', 'entry')][:100]
    result = []
    invalid_dates = stale = future = 0
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
        if not published:
            invalid_dates += 1
        if published and published > now + dt.timedelta(minutes=10):
            future += 1
        if not title or not link or not published or published > now + dt.timedelta(minutes=10):
            continue
        if published < now - dt.timedelta(days=14):
            stale += 1
            continue
        countries, regions, location = geography(title)
        result.append({'id': hashlib.sha256(link.encode()).hexdigest()[:20], 'title': title,
                       'url': link, 'source': source['name'], 'source_id': source['id'],
                       'media': source.get('media', source['name']), 'language': source.get('language', 'en'),
                       'published_at': published.isoformat().replace('+00:00', 'Z'),
                       'category': category(title, source['category']), 'countries': countries,
                       'regions': regions, 'location': location})
    if diagnostics is not None:
        channel = next((e for e in root if local(e.tag) == 'channel'), root)
        feed_title = next((''.join(e.itertext()).strip() for e in channel if local(e.tag) == 'title'), '')
        diagnostics.update(format=local(root.tag), encoding=encoding, parsed_entries=len(entries),
                           invalid_dates=invalid_dates, stale_entries=stale, future_entries=future,
                           feed_title=feed_title[:200])
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


def request(url, limit, metadata=None):
    start = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/plain'})
    opener = urllib.request.build_opener(BoundedRedirect(), urllib.request.HTTPSHandler(context=tls_context()))
    with opener.open(req, timeout=TIMEOUT) as response:
        if metadata is not None:
            metadata.update(http_status=response.status, content_type=response.headers.get_content_type())
            metadata['effective_url'] = response.url
        chunks = bytearray()
        while len(chunks) <= limit:
            if time.monotonic() - start > TIMEOUT:
                raise TimeoutError('Response time limit')
            chunk = response.read(min(65536, limit + 1 - len(chunks)))
            if not chunk:
                raw = bytes(chunks)
                if response.headers.get('Content-Encoding', '').lower() == 'gzip' or raw.startswith(b'\x1f\x8b'):
                    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
                    raw = decoder.decompress(raw, limit + 1)
                    if len(raw) > limit or not decoder.eof or decoder.unused_data:
                        raise ValueError('Compressed response size/format limit')
                return raw
            chunks.extend(chunk)
        raise ValueError('Response size limit')

class FetchSession:
    """One robots request/origin/run; serialized host requests, no retry or login."""
    def __init__(self, budget=RUN_BUDGET):
        self.deadline = time.monotonic() + budget
        self.locks = defaultdict(threading.Lock)
        self.rules = {}
        self.last = {}
        self.guard = threading.Lock()

    def read(self, url, limit, metadata):
        origin = urllib.parse.urlsplit(url)._replace(path='', query='', fragment='').geturl()
        with self.guard:
            lock = self.locks[origin]
        with lock:
            if time.monotonic() + 2 * TIMEOUT + 2 >= self.deadline:
                raise TimeoutError('Run budget exhausted; source skipped')
            if origin not in self.rules:
                try:
                    raw = request(origin + '/robots.txt', 512000)
                    if re.search(br'captcha|cf-chl-|challenge-platform|verify you are human|access denied', raw.lower()):
                        raise ValueError('Robots response contains access challenge')
                    rules = urllib.robotparser.RobotFileParser()
                    # RFC 9309 2.3.1.5: use parseable rules, ignore other lines.
                    # Some official RSS hosts return a soft-404 HTML landing page here.
                    rules.parse(raw.decode('utf-8', 'strict').splitlines())
                    rules.rico_format = 'html' if raw.lstrip().startswith(b'<') else 'text'
                    self.rules[origin] = rules
                except urllib.error.HTTPError as error:
                    if error.code == 404:
                        rules = urllib.robotparser.RobotFileParser(); rules.parse([])
                        self.rules[origin] = rules
                    else:
                        self.rules[origin] = error
                except Exception as error:
                    self.rules[origin] = error
                self.last[origin] = time.monotonic()
            rules = self.rules[origin]
            if isinstance(rules, Exception):
                raise ValueError(f'Robots check failed: {type(rules).__name__}: {str(rules)[:100]}')
            metadata['robots_format'] = getattr(rules, 'rico_format', '404_missing')
            if not rules.can_fetch(USER_AGENT, url):
                raise ValueError('Access disallowed by robots.txt')
            delay = max(.5, rules.crawl_delay(USER_AGENT) or 0)
            rate = rules.request_rate(USER_AGENT)
            if rate:
                delay = max(delay, rate.seconds / rate.requests)
            if delay > 10:
                raise ValueError('Crawl delay exceeds bounded collection budget')
            wait = max(0, self.last.get(origin, 0) + delay - time.monotonic())
            if time.monotonic() + wait + TIMEOUT + 1 >= self.deadline:
                raise TimeoutError('Run budget exhausted; source skipped')
            time.sleep(wait)
            try:
                return request(url, limit, metadata)
            finally:
                self.last[origin] = time.monotonic()


def interleave(sources):
    hosts = defaultdict(deque)
    for source in sources:
        hosts[urllib.parse.urlsplit(source['url']).netloc].append(source)
    while any(hosts.values()):
        for queue in hosts.values():
            if queue:
                yield queue.popleft()


def fetch(source, session=None):
    started = time.monotonic()
    status = {'id': source['id'], 'name': source['name'], 'url': source['url'], 'checked_at': stamp(),
              'media': source.get('media', source['name']), 'language': source.get('language', 'en'),
              'http_status': None, 'parsed_entries': 0}
    try:
        parts = urllib.parse.urlsplit(source['url'])
        if parts.scheme != 'https':
            raise ValueError('Feed must use HTTPS')
        raw = (session or FetchSession()).read(source['url'], MAX_FEED, status)
        items = parse_feed(raw, source, diagnostics=status)
        if not items:
            raise ValueError('No valid dated items within 14 days')
        status.update(ok=True, count=len(items), error=None)
        status['newest_at'] = max(item['published_at'] for item in items)
        status['oldest_at'] = min(item['published_at'] for item in items)
        return items, status
    except Exception as error:
        if isinstance(error, urllib.error.HTTPError):
            status['http_status'] = error.code
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
        if set(item) - {'id','title','url','source','source_id','category','published_at',
                        'countries','regions','location','language','media'}:
            raise ValueError('Only public headline metadata may be published')
        if item.get('language', 'en') not in ('en','zh','ja'):
            raise ValueError('Invalid language')
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
    if len({s['url'] for s in sources}) != len(sources):
        raise ValueError('Duplicate feed URLs')
    if any(s.get('language', 'en') not in ('en', 'zh', 'ja') or
           not safe_url(s['url']) or urllib.parse.urlsplit(s['url']).scheme != 'https' or
           urllib.parse.urlsplit(s['url']).hostname in ('www.nna.jp','nna.jp') for s in sources):
        raise ValueError('Only supported public RSS languages/HTTPS feeds; NNA is excluded from this project')
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
    session = FetchSession()
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for items, status in pool.map(lambda source: fetch(source, session), interleave(sources)):
            collected.extend(items); statuses.append(status)
    success = any(s['ok'] for s in statuses)
    allowed = {s['id'] for s in sources}
    payload = {'updated_at': stamp(), 'last_success_at': stamp() if success else previous.get('last_success_at'),
               'status': 'ok' if all(s['ok'] for s in statuses) else 'partial' if success else 'failed',
               'sources': statuses, 'items': merge(collected + [n for n in previous['items'] if n['source_id'] in allowed])}
    # Never retain items from removed sources.
    allowed = {s['id'] for s in sources}
    defaults = {s['id']: s['category'] for s in sources}
    configs = {s['id']: s for s in sources}
    payload['items'] = [n for n in payload['items'] if n['source_id'] in allowed]
    # Recompute rule labels when rules improve.
    for item in payload['items']:
        item['countries'], item['regions'], item['location'] = geography(item['title'])
        item['category'] = category(item['title'], defaults[item['source_id']])
        source = configs[item['source_id']]
        item['language'] = source.get('language', 'en')
        item['media'] = source.get('media', source['name'])
    data = encode_bounded(payload)
    validate_payload(payload)
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
