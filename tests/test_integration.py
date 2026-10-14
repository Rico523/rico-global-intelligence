import base64
import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from collector import collect as c
from collector import maintenance as m

class IntegrationTests(unittest.TestCase):
    def test_failure_preserves_previous_and_history_is_bounded(self):
        now=dt.datetime.now(c.UTC)
        item={'id':'1','title':'Japan energy policy','url':'https://example.org/a','source':'Test',
              'source_id':'test','category':'energy','published_at':now.isoformat(),
              'countries':['Japan'],'regions':[], 'location':{'lat':36,'lon':138,'label':'Japan','kind':'country_reference'}}
        source={'id':'test','name':'Test','url':'https://example.org/feed','category':'world'}
        with tempfile.TemporaryDirectory() as folder, patch.object(c,'ROOT',Path(folder)):
            root=Path(folder);(root/'config').mkdir();(root/'config/sources.json').write_text(json.dumps([source]))
            with patch.object(c,'fetch',return_value=([item],dict(source,ok=True,count=1))),patch('builtins.print'):
                self.assertEqual(c.main(),0)
            path=root/'site/data/news.json';success=json.loads(path.read_text())['last_success_at']
            for _ in range(4):
                with patch.object(c,'fetch',return_value=([],dict(source,ok=False,count=0,error='timeout'))),patch('builtins.print'):
                    self.assertEqual(c.main(),1)
            payload=json.loads(path.read_text());c.validate_payload(payload)
            self.assertEqual(len(payload['items']),1);self.assertEqual(payload['last_success_at'],success)
            self.assertEqual(payload['status'],'failed')
            self.assertEqual(len(list((path.parent/'history').glob('*.json'))),2)
            self.assertEqual(len(payload['history_keys']),2)
    def test_payload_rejects_invented_coordinate(self):
        payload=json.loads((c.ROOT/'site/data/news.json').read_text())
        item=next(n for n in payload['items'] if n.get('location'))
        item['location']['lat']=0
        with self.assertRaises(ValueError):c.validate_payload(payload)
    def test_maintenance_skips_recent_activity(self):
        now=dt.datetime.now(c.UTC).isoformat().replace('+00:00','Z')
        with patch.dict(os.environ,{'RICO_REPOSITORY':'owner/rico','GITHUB_TOKEN':'test-only'}),patch.object(m,'api',return_value=[{'commit':{'committer':{'date':now}}}]) as api,patch('builtins.print'):
            m.main()
        self.assertEqual(api.call_count,1)
    def test_maintenance_writes_only_small_file(self):
        old=(dt.datetime.now(c.UTC)-dt.timedelta(days=31)).isoformat().replace('+00:00','Z')
        with patch.dict(os.environ,{'RICO_REPOSITORY':'owner/rico','GITHUB_TOKEN':'test-only'}),patch.object(m,'api',side_effect=[[{'commit':{'committer':{'date':old}}}],{'sha':'existing'},{}]) as api,patch('builtins.print'):
            m.main()
        args=api.call_args.args;self.assertEqual(args[2],'contents/maintenance/automation.json')
        content=base64.b64decode(args[3]['content']);self.assertLess(len(content),100)
        self.assertNotIn(b'test-only',content)
    def test_workflow_safety(self):
        workflow=(c.ROOT/'.github/workflows/pages.yml').read_text()
        self.assertIn('ZERO_COST_CONFIRMED',workflow);self.assertIn('cancel-in-progress: false',workflow)
        self.assertIn('\n  schedule:',workflow);self.assertIn("cron: '17 0,12 * * *'",workflow);self.assertNotIn('git push',workflow)
        import re
        actions=re.findall(r'uses: ([^\n]+)',workflow)
        self.assertTrue(all(re.match(r'actions/[\w-]+@[0-9a-f]{40}',a) for a in actions))
        self.assertEqual(re.findall(r'runs-on: (\S+)',workflow),['ubuntu-24.04','ubuntu-24.04'])
        self.assertEqual(sum(map(int,re.findall(r'timeout-minutes: (\d+)',workflow))),5)

class BoundaryTests(unittest.TestCase):
    def test_parallel_local_run_is_refused(self):
        import fcntl, shutil, subprocess, sys
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'collector').mkdir()
            shutil.copy(c.__file__,root/'collector/collect.py')
            with (root/'.collector.lock').open('w') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                result=subprocess.run([sys.executable,str(root/'collector/collect.py')],capture_output=True,timeout=5)
            self.assertEqual(result.returncode,75)
            self.assertIn(b'already running',result.stderr)
    def test_https_redirect_cannot_downgrade(self):
        import urllib.request
        req=urllib.request.Request('https://example.org/rss')
        with self.assertRaises(ValueError):c.BoundedRedirect().redirect_request(req,None,301,'redirect',{},'http://example.org/rss')
    def test_malformed_url_is_skipped(self):
        self.assertIsNone(c.safe_url('https://[broken'))
    def test_land_coordinates_and_size(self):
        path=c.ROOT/'site/assets/land.json'
        self.assertLess(path.stat().st_size,100000)
        polygons=json.loads(path.read_text())
        self.assertGreater(len(polygons),100)
        self.assertTrue(all(-180<=lon<=180 and -90<=lat<=90 for poly in polygons for lon,lat in poly))
