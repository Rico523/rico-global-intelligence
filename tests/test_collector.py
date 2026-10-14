import datetime as dt
import json
import unittest
from unittest.mock import patch
from collector import collect as c

NOW=dt.datetime(2026,10,12,12,tzinfo=c.UTC)
SOURCE={'id':'test','name':'Test','url':'https://example.org/rss','category':'world'}

def rss(title='Japan announces energy policy',url='https://example.org/a',date='Mon, 12 Oct 2026 10:00:00 GMT'):
    return f'<rss><channel><item><title>{title}</title><link>{url}</link><pubDate>{date}</pubDate></item></channel></rss>'.encode()

class CollectorTests(unittest.TestCase):
    def test_rss(self):
        n=c.parse_feed(rss(),SOURCE,NOW)[0]
        self.assertEqual(n['category'],'energy'); self.assertEqual(n['countries'],['Japan'])
        self.assertEqual(n['published_at'],'2026-10-12T10:00:00Z')
    def test_atom(self):
        raw=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Singapore trade</title><link href="https://example.org/a"/><published>2026-10-12T18:00:00+09:00</published></entry></feed>'
        n=c.parse_feed(raw,SOURCE,NOW)[0]
        self.assertEqual(n['published_at'],'2026-10-12T09:00:00Z');self.assertEqual(n['category'],'trade')
    def test_dates(self):
        self.assertIsNone(c.date_value('bad'));self.assertIsNone(c.date_value('2026-10-12T10:00:00'))
        self.assertEqual(c.parse_feed(rss(date='Wed, 14 Oct 2026 10:00:00 GMT'),SOURCE,NOW),[])
        self.assertEqual(c.parse_feed(rss(date='Mon, 01 Jun 2026 10:00:00 GMT'),SOURCE,NOW),[])
    def test_unsafe_url(self):
        self.assertEqual(c.parse_feed(rss(url='javascript:alert(1)'),SOURCE,NOW),[])
        self.assertIsNone(c.safe_url('https://user:pass@example.org/a'))
    def test_tracking(self):
        self.assertEqual(c.safe_url('https://example.org/a?utm_source=rss&amp;x=1#p'),'https://example.org/a?amp%3Bx=1')
        self.assertEqual(c.safe_url('https://example.org/a?utm_source=rss&x=1#p'),'https://example.org/a?x=1')
    def test_no_false_coordinate(self):
        self.assertIsNone(c.geography('Global technology outlook')[2])
        self.assertIsNone(c.geography('Japan and China talks')[2])
        self.assertEqual(c.geography('European markets')[1],['Europe'])
        self.assertEqual(c.geography('Indianapolis market')[0],[])
        self.assertEqual(c.geography('What this means for us')[0],[])
        self.assertEqual(c.geography('South American markets')[0],[])
        self.assertEqual(c.geography('US trade policy')[0],['United States'])
    def test_dedupe(self):
        n=c.parse_feed(rss(),SOURCE,NOW)[0]
        clone=dict(n,url='https://example.org/b',id='b')
        self.assertEqual(len(c.merge([n,n,clone],NOW)),1)
    def test_limits(self):
        n=c.parse_feed(rss(),SOURCE,NOW)[0]
        all_items=[dict(n,url=f'https://example.org/{i}',title=f'Unique news {i}') for i in range(700)]
        self.assertEqual(len(c.merge(all_items,NOW)),600)
        payload={'items':[dict(n,title='あ'*10000) for _ in range(100)]}
        raw=c.encode_bounded(payload)
        self.assertLessEqual(len(raw),c.MAX_JSON);self.assertLess(len(payload['items']),100)
    def test_xml_entities(self):
        with self.assertRaises(ValueError):c.parse_feed(b'<!DOCTYPE rss><rss/>',SOURCE,NOW)
    def test_failure_isolated(self):
        with patch.object(c,'request',side_effect=TimeoutError('timeout')):
            items,status=c.fetch(SOURCE)
        self.assertEqual(items,[]);self.assertFalse(status['ok']);self.assertIn('timeout',status['error'])
    def test_robots_disallowed(self):
        with patch.object(c,'request',return_value=b'User-agent: *\nDisallow: /rss') as request:
            items,status=c.fetch(SOURCE)
        self.assertFalse(status['ok']);self.assertEqual(request.call_count,1)
    def test_config(self):
        sources=json.loads((c.ROOT/'config/sources.json').read_text())
        self.assertTrue(10<=len(sources)<=15)
        self.assertEqual(len(sources),len({s['id'] for s in sources}))
        self.assertTrue(all(s['url'].startswith('https://') for s in sources))

if __name__=='__main__':unittest.main()
