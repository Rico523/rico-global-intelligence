"""Fixtures are synthetic test data, never published as news."""
import concurrent.futures
import datetime as dt
import json
import gzip
import io
import email.message
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from collector import collect as c

NOW=dt.datetime(2026,10,16,12,tzinfo=c.UTC)
SOURCE=dict(id='fixture',name='测试媒体',media='Fixture',language='zh',category='world',url='https://example.org/rss')

def xml(title,encoding='utf-8'):
    return (f'<?xml version="1.0" encoding="{encoding}"?><rss><channel><item><title>{title}</title>'
            '<link>https://example.org/article</link><pubDate>Fri, 16 Oct 2026 18:00:00 +0900</pubDate>'
            '</item></channel></rss>').encode(encoding)

class MultilingualTests(unittest.TestCase):
    def test_legacy_chinese_and_japanese_encodings(self):
        for title,encoding,language in [('中国金融新闻','gb18030','zh'),('日本の半導体輸出','shift_jis','ja'),('香港銀行新聞','big5','zh')]:
            with self.subTest(encoding=encoding):
                diagnostics={}
                item=c.parse_feed(xml(title,encoding),dict(SOURCE,language=language),NOW,diagnostics)[0]
                self.assertEqual(item['title'],title)
                self.assertEqual(item['language'],language)
                self.assertEqual(item['media'],'Fixture')
                self.assertEqual(item['published_at'],'2026-10-16T09:00:00Z')
                self.assertEqual(diagnostics['encoding'],encoding)

    def test_cjk_rules_and_cross_border_ambiguity(self):
        self.assertEqual(c.geography('印度尼西亚银行新闻')[0],['Indonesia'])
        self.assertIsNone(c.geography('印度与印度尼西亚贸易谈判')[2])
        self.assertEqual(c.geography('中国地方の大雨')[0],[])
        self.assertEqual(c.geography('中国と日本の貿易協定')[0],['Japan','China'])
        self.assertIsNone(c.geography('中国と日本の貿易協定')[2])
        self.assertEqual(c.geography('香港金融市场')[0],['Hong Kong'])
        self.assertEqual(c.category('日本の半導体輸出','world'),'trade')
        self.assertEqual(c.geography('タイヤメーカーが発表')[0],[])

    def test_utf16_entities_rejected(self):
        with self.assertRaises(ValueError):
            c.parse_feed('<?xml version="1.0" encoding="utf-16"?><!DOCTYPE rss><rss/>'.encode('utf-16'),SOURCE,NOW)

    def test_stale_and_invalid_dates_reported(self):
        diagnostics={}
        self.assertEqual(c.parse_feed(xml('旧新闻').replace(b'16 Oct 2026',b'01 Jan 2020'),SOURCE,NOW,diagnostics),[])
        self.assertEqual(diagnostics['stale_entries'],1)

    def test_host_robots_cached_and_concurrency_serialized(self):
        session=c.FetchSession()
        active=peak=0
        def request(url,limit,metadata=None):
            nonlocal active,peak
            active+=1;peak=max(peak,active)
            if metadata is not None:metadata['http_status']=200
            active-=1
            return b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else xml('中国金融新闻')
        with patch.object(c,'request',side_effect=request) as calls,patch.object(c.time,'sleep'):
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                list(pool.map(lambda suffix:session.read('https://example.org/'+suffix,20000,{}),['a','b']))
        self.assertEqual(sum(call.args[0].endswith('/robots.txt') for call in calls.call_args_list),1)
        self.assertEqual(peak,1)
        self.assertEqual(calls.call_count,3)

    def test_budget_exhaustion_makes_no_request(self):
        with patch.object(c,'request') as request:
            news,status=c.fetch(SOURCE,c.FetchSession(budget=0))
        request.assert_not_called();self.assertFalse(status['ok']);self.assertEqual(news,[])

    def test_html_robots_challenge_is_not_permission(self):
        with patch.object(c,'request',return_value=b'<html>Verify you are human</html>') as request:
            _,status=c.fetch(SOURCE)
        self.assertFalse(status['ok']);self.assertEqual(request.call_count,1)

    def test_gzip_response_and_decompression_limit(self):
        for content,limit,valid in [(b'User-agent: *\nAllow: /',300,True),(b'x'*10000,100,False)]:
            response=io.BytesIO(gzip.compress(content));response.status=200
            response.url='https://example.org/robots.txt'
            response.headers=email.message.Message();response.headers['Content-Encoding']='gzip'
            opener=SimpleNamespace(open=lambda *a,**k:response)
            with patch.object(c.urllib.request,'build_opener',return_value=opener):
                if valid:self.assertEqual(c.request(response.url,limit),content)
                else:
                    with self.assertRaises(ValueError):c.request(response.url,limit)

    def test_host_round_robin(self):
        sources=[dict(SOURCE,id=i,url=u) for i,u in [('a','https://one.example/a'),('b','https://one.example/b'),('c','https://two.example/c')]]
        self.assertEqual([s['id'] for s in c.interleave(sources)],['a','c','b'])

    def test_reject_body_or_member_excerpt_from_published_data(self):
        item=c.parse_feed(xml('中国金融新闻'),SOURCE,NOW)[0]
        payload=dict(status='ok',updated_at=NOW.isoformat(),sources=[],items=[dict(item,body='forbidden')])
        with self.assertRaises(ValueError):c.validate_payload(payload)

    def test_media_and_language_config_explicit_no_nna_collection(self):
        sources=json.loads((c.ROOT/'config/sources.json').read_text())
        self.assertEqual(set(s['language'] for s in sources),{'zh','ja','en'})
        self.assertTrue(all(s['media'] for s in sources))
        self.assertEqual(len(sources),len({s['url'] for s in sources}))
        self.assertFalse(any('nna.jp' in s['url'] for s in sources))
        for id in ['bbc-world','bbc-business','bbc-tech','bbc-asia','guardian-world','guardian-business','guardian-tech','guardian-energy','guardian-asia','aljazeera','dw','euronews']:
            self.assertTrue(any(s['id']==id and s['language']=='en' for s in sources),id)

    def test_nna_is_absent_from_public_site(self):
        self.assertFalse((c.ROOT/'site/assets/nna-markets.json').exists())
        for name in ['index.html','app.js','style.css']:
            self.assertNotIn('nna', (c.ROOT/'site'/name).read_text().lower())

    def test_pr_checks_cannot_deploy_or_write(self):
        workflow=(c.ROOT/'.github/workflows/source-check.yml').read_text()
        self.assertIn('pull_request:',workflow)
        self.assertNotIn('pull_request_target',workflow)
        self.assertNotIn('schedule:',workflow)
        self.assertNotIn('write',workflow)
        self.assertNotIn('upload-artifact',workflow)
        self.assertNotIn('deploy-pages',workflow)
        self.assertIn('timeout-minutes: 5',workflow)
