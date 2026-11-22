#!/usr/bin/env python3
"""Repair SonoCalming VideoObject uploadDate with REAL YouTube publication timestamps.

Run daily after update_sonocalming_latest.py and update_sonocalming_seo.py.
Uses YOUTUBE_API_KEY when present (GitHub Actions secret already used by the site).
When the API is unavailable, uses ONLY exact timestamps already stored locally.
Never creates a made-up publication hour or changes YouTube / page URLs.

Idempotent: do not rewrite HTML / timestamp cache if their content is unchanged.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SITE = Path(__file__).resolve().parents[1]
SONO = SITE / 'SonoCalming'
PAGES = SONO / 'videos'
CACHE = SONO / 'video-upload-dates.json'
CATALOGUE = SONO / 'videos.json'
LATEST = SONO / 'latest-videos.json'
CHANNEL_ID = 'UCGXypunMB75x599kvbSAuqw'
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
STAMP = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$')
SCRIPT = re.compile(r'(<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', re.I | re.S)
DATE_FIELD = re.compile(r'("uploadDate"\s*:\s*")([^"]*)(")')


def stamp(value: object) -> str | None:
    """Normalize *verified complete* ISO8601 timestamps to UTC Z."""
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None or dt.year < 2005:
            return None
        return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    except ValueError:
        return None


def load_cache() -> dict[str, str]:
    if not CACHE.is_file():
        return {}
    raw = json.loads(CACHE.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError('Unexpected video-upload-dates.json format')
    return {key: date for key, val in raw.items()
            if VIDEO_ID.fullmatch(key) and (date := stamp(val))}


def add_local_sources(dates: dict[str, str], valid_ids: set[str]) -> None:
    """Use exact dates carried by earlier YouTube API responses, never date-only fields."""
    if LATEST.is_file():
        raw = json.loads(LATEST.read_text(encoding='utf-8'))
        for row in raw.get('videos', []):
            ident = row.get('id')
            published = stamp(row.get('publishedAt'))
            if ident in valid_ids and published:
                dates[ident] = published
    if CATALOGUE.is_file():
        raw = json.loads(CATALOGUE.read_text(encoding='utf-8'))
        for row in raw:
            ident = row.get('id')
            published = stamp(row.get('publishedAt'))
            if ident in valid_ids and published and ident not in dates:
                dates[ident] = published


def api_batch(ids: list[str], api_key: str) -> dict[str, str]:
    params = urlencode({'part': 'snippet', 'id': ','.join(ids), 'key': api_key})
    request = Request('https://www.googleapis.com/youtube/v3/videos?' + params,
                      headers={'Accept': 'application/json',
                               'User-Agent': 'SonoCalming-video-date-fix/1.0'})
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as exc:
        # Do not show the request URL: it contains the API key.
        raise RuntimeError(f'YouTube API returned HTTP {exc.code}') from None
    except URLError as exc:
        raise RuntimeError('Could not contact YouTube API') from None
    if not isinstance(data.get('items'), list):
        raise RuntimeError('YouTube API did not return a video list')
    found = {}
    for item in data['items']:
        ident = item.get('id', '')
        snippet = item.get('snippet', {})
        if ident not in ids or snippet.get('channelId') != CHANNEL_ID:
            continue
        published = stamp(snippet.get('publishedAt'))
        if published:
            found[ident] = published
    return found


def video_date_from_html(path: Path) -> str | None:
    """Get current VideoObject uploadDate without changing other structured data."""
    body = path.read_text(encoding='utf-8')
    for match in SCRIPT.finditer(body):
        try:
            node = json.loads(match.group(2))
        except json.JSONDecodeError:
            continue
        if node.get('@type') == 'VideoObject':
            return node.get('uploadDate', '')
    return None


def replace_page(path: Path, date: str) -> bool:
    before = path.read_text(encoding='utf-8')
    saw_video = False
    def change(m: re.Match[str]) -> str:
        nonlocal saw_video
        try:
            node = json.loads(m.group(2))
        except json.JSONDecodeError:
            return m.group(0)
        if node.get('@type') != 'VideoObject':
            return m.group(0)
        saw_video = True
        if 'uploadDate' not in node:
            # Do not blindly replace unrelated script bodies.
            return m.group(0)
        new_json, matches = DATE_FIELD.subn(
            lambda f: f.group(1) + date + f.group(3), m.group(2), count=1)
        if matches != 1:
            return m.group(0)
        return m.group(1) + new_json + m.group(3)
    after = SCRIPT.sub(change, before)
    if not saw_video:
        return False
    if after != before:
        path.write_text(after, encoding='utf-8')
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description='Correct VideoObject uploadDate from real YouTube timestamps')
    parser.add_argument('--check', action='store_true', help='Audit only, do not modify files or call API')
    args = parser.parse_args()
    if not PAGES.is_dir():
        print(f'Cannot find video pages: {PAGES}', file=sys.stderr)
        return 2
    paths = {p.stem: p for p in PAGES.glob('*.html') if VIDEO_ID.fullmatch(p.stem)}
    if not paths:
        print('No SonoCalming video pages found.', file=sys.stderr)
        return 2
    current = {ident: video_date_from_html(path) for ident, path in paths.items()}
    invalid = sorted(ident for ident, date in current.items() if not stamp(date))
    print(f'VideoObject audit: {len(paths)} detail pages, '
          f'{len(paths)-len(invalid)} valid zoned dates, {len(invalid)} missing/invalid dates.')
    if args.check:
        if invalid:
            print('Examples needing correction:', ', '.join(invalid[:8]))
        return 0

    old_cache = load_cache()
    dates = dict(old_cache)
    add_local_sources(dates, set(paths))
    missing = [ident for ident in invalid if ident not in dates]
    api_key = os.environ.get('YOUTUBE_API_KEY', '').strip()
    failures = []
    if missing and api_key:
        for i in range(0, len(missing), 50):
            try:
                dates.update(api_batch(missing[i:i+50], api_key))
            except RuntimeError as exc:
                failures.append(str(exc))
                # Continue other batches; previous valid timestamps remain safe.
        print(f'YouTube metadata: attempted {len(missing)} missing date(s) '
              f'in {(len(missing)+49)//50} API request(s).')
    elif missing:
        print(f'No YOUTUBE_API_KEY locally: {len(missing)} date(s) will be '
              'fetched by GitHub Actions after installation.')

    # Do not include unverified IDs from outside this site's video pages.
    dates = {ident: dates[ident] for ident in sorted(paths) if ident in dates}
    count = 0
    for ident in invalid:
        published = dates.get(ident)
        if published and replace_page(paths[ident], published):
            count += 1
    if dates != old_cache:
        CACHE.write_text(json.dumps(dates, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    remaining = [ident for ident in invalid if ident not in dates]
    print(f'Corrected {count} VideoObject page(s); {len(remaining)} awaiting verified timestamps.')
    if failures:
        print('YouTube API warning:', '; '.join(sorted(set(failures))), file=sys.stderr)
    if remaining:
        print('Remaining IDs (first 12):', ', '.join(remaining[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
