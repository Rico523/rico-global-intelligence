"""Real HTTP/robots/XML/date audit. Saves counts/status only, never feed bodies."""
import argparse
import concurrent.futures
from collections import Counter
import json
from pathlib import Path
import signal
import time
from collect import ROOT, FetchSession, WORKERS, fetch, interleave, merge, stamp, alarm_timeout

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    sources=json.loads((ROOT/'config/sources.json').read_text(encoding='utf-8'))
    started=time.monotonic();session=FetchSession();news=[];statuses=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for items,status in pool.map(lambda source:fetch(source,session),interleave(sources)):
            news.extend(items);statuses.append(status)
    successful=[s for s in statuses if s['ok']]
    # merge is deliberately bounded; report raw and deduplicated retained counts separately.
    retained=merge(news)
    report=dict(checked_at=stamp(),elapsed_seconds=round(time.monotonic()-started,2),
                configured_feeds=len(sources),configured_media=len({s['media'] for s in sources}),
                successful_feeds=len(successful),successful_media=len({s['media'] for s in successful}),
                feed_languages=dict(Counter(s['language'] for s in successful)),
                fetched_items=len(news),fetched_languages=dict(Counter(n['language'] for n in news)),
                retained_items=len(retained),retained_languages=dict(Counter(n['language'] for n in retained)),
                sources=sorted(statuses,key=lambda s:s['id']))
    encoded=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if len(encoded)>200000:raise ValueError('Audit report size limit')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_bytes(encoded)
    print(json.dumps({k:v for k,v in report.items() if k!='sources'},ensure_ascii=False,indent=2))
    for status in statuses:
        if not status['ok']:print(status['id'],status['error'])
    return 0 if len(successful)>=80 and len(report['feed_languages'])==3 else 1

if __name__=='__main__':
    signal.signal(signal.SIGALRM,alarm_timeout);signal.alarm(150)
    try:raise SystemExit(main())
    finally:signal.alarm(0)
