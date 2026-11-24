#!/usr/bin/env python3
"""Validate Lumen Mine gameplay VideoObject using VERIFIED YouTube metadata.

A Game can retain its video player without invalid Google video structured data.
If a valid ISO8601 publishedAt cannot be verified, omit VideoObject entirely.
Once YouTube Data API returns the genuine upload date, restore VideoObject for all
8 localized overview and marketing pages. Safe, idempotent, offline-friendly.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SITE = Path(__file__).resolve().parents[1]
LUMEN = SITE / 'lumenmine'
CACHE = LUMEN / 'video-metadata.json'
VIDEO_ID = '52k9xFLSzbw'
SCRIPT = re.compile(r'(<script\s+type=["\']application/ld\+json["\']\s*>)(.*?)(</script>)', re.I|re.S)
VIDEO_INFO = {
    '@type':'VideoObject',
    'name':'Lumen Mine gameplay Short',
    'description':'Short gameplay preview of Lumen Mine, a minesweeper puzzle adventure on Android and iOS.',
    'thumbnailUrl':'https://i.ytimg.com/vi/52k9xFLSzbw/hqdefault.jpg',
    'embedUrl':'https://www.youtube-nocookie.com/embed/52k9xFLSzbw',
    'url':'https://www.youtube.com/shorts/52k9xFLSzbw',
}

def normalize_date(timestamp: object) -> str | None:
    if not isinstance(timestamp,str) or not re.fullmatch(r'20\d{2}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)',timestamp):
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z','+00:00'))
        if not dt.tzinfo or dt > datetime.now(timezone.utc):return None
        return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    except (ValueError,TypeError):return None

def from_cache() -> str | None:
    try: metadata=json.loads(CACHE.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None
    if metadata.get('id') != VIDEO_ID or metadata.get('source') != 'YouTube Data API':return None
    return normalize_date(metadata.get('publishedAt'))

def fetch_date(key: str) -> str | None:
    params=urlencode({'part':'snippet','id':VIDEO_ID,'key':key})
    req=Request('https://www.googleapis.com/youtube/v3/videos?'+params,headers={'Accept':'application/json','User-Agent':'AML-Creation-SEO/1.0'})
    with urlopen(req,timeout=20) as response: data=json.load(response)
    for item in data.get('items',[]):
        if item.get('id') != VIDEO_ID:continue
        result=normalize_date(item.get('snippet',{}).get('publishedAt'))
        if result:return result
    return None

def fix_markup(html: str,date: str | None) -> tuple[str,int]:
    count=0
    def update(match:re.Match) -> str:
        nonlocal count
        try: value=json.loads(match.group(2))
        except json.JSONDecodeError:return match.group(0)
        if not isinstance(value,dict) or value.get('@type')!='VideoGame':return match.group(0)
        current=value.get('video')
        if not isinstance(current,dict) and not date:return match.group(0)
        if date:
            new_video={**VIDEO_INFO,'uploadDate':date}
            if current == new_video:return match.group(0)
            value['video']=new_video
        else:
            if not isinstance(current,dict) or normalize_date(current.get('uploadDate')):return match.group(0)
            value.pop('video',None)
        count+=1
        encoded=json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
        return match.group(1)+encoded+match.group(3)
    return SCRIPT.sub(update,html),count

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    date=from_cache()
    key=os.environ.get('YOUTUBE_API_KEY','').strip()
    if key and not args.check:
        try:
            published=fetch_date(key)
            if published:
                date=published
                CACHE.write_text(json.dumps({'id':VIDEO_ID,'publishedAt':date,'source':'YouTube Data API'},indent=2)+'\n',encoding='utf-8')
        except Exception as exc:
            print('YouTube metadata unavailable, safe fallback:',type(exc).__name__)
    pages=sorted(LUMEN.rglob('*.html'))
    changed=0; valid=0; invalid=0
    for path in pages:
        source=path.read_text(encoding='utf-8')
        result,count=fix_markup(source,date)
        if count:
            changed+=1
            if not args.check:path.write_text(result,encoding='utf-8')
        if '"@type":"VideoObject"' in result:
            valid+=1
        if '"@type": "VideoObject"' in result and not date:
            invalid+=1
    state=('verified video publication date available' if date else 'video structured data omitted until YouTube date is verified')
    print(f'Lumen Mine: {len(pages)} pages scanned, {changed} would change/changed, {state}.')
    return 0

if __name__=='__main__':raise SystemExit(main())
