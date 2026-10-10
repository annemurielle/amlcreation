#!/usr/bin/env python3
"""Append ONLY new long SonoCalming uploads to the existing static catalogue.

Existing HTML video pages and their URLs are NEVER regenerated or deleted.
The 321 legacy records are kept intact. Uses the same YouTube API feed as the
homepage and (optionally) the Blue Room YouTube playlist membership list.
Standard Python library only, designed for GitHub Actions.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1] / 'SonoCalming'
BASE = 'https://www.amlcreation.ch/SonoCalming/'
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
MINIMUM_SECONDS = 3600
MAX_DESCRIPTION = 480
BLUE_PLAYLIST_ID = 'PLmwaBBNoGCMnkHFBGY6le5UDn0SBe8aXF'


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def extract_description(source: str) -> str:
    result = re.sub(r'\s+', ' ', source or '').strip()
    if not result:
        return 'Discover a long-form soundscape from SonoCalming, available to watch on YouTube.'
    return result[:MAX_DESCRIPTION].rsplit(' ', 1)[0] + '…' if len(result) > MAX_DESCRIPTION else result


def meta_description(title: str, source: str) -> str:
    """No newly authored sensitive efficacy claims; preserve useful real video info."""
    value = extract_description(source)
    value = re.sub(r'\b(?:healing|relief|therapy|cure|treatment)\b', '', value, flags=re.I)
    value = re.sub(r'\s+', ' ', value).strip()
    if not value:
        value = f'Listen to {title} on SonoCalming.'
    return value[:154].rsplit(' ', 1)[0].strip(' ,.;:-') + ('…' if len(value) > 154 else '')


def iso_duration(seconds: int) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    return 'PT' + (f'{hours}H' if hours else '') + (f'{minutes}M' if minutes else '') + (f'{sec}S' if sec or not (hours or minutes) else '')


def duration_label(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h: parts.append(f'{h} hr')
    if m: parts.append(f'{m} min')
    if s and h == 0: parts.append(f'{s} sec')
    return ' '.join(parts) or '0 sec'


def classify(title: str, description: str, blue_playlist: bool = False) -> str:
    """Explicit black-screen/Japanese formats win over generic household keywords."""
    t = (title or '').lower()
    d = (description or '').lower()
    if re.search(r'black\s*screen|screen\s*off|dark\s*screen', t):
        return 'Black Screen'
    if re.search(r'japanese\s*(?:bedroom|room)|japan(?:ese)?\s*rain\s*room', t):
        return 'Japanese Bedroom'
    if (blue_playlist or re.search(r'blue\s*(?:room|bedroom|kitchen|bathroom|apartment)', t)
          or (re.search(r'dishwasher|washing machine|laundry room|fridge|refrigerator|shower|room fan', t)
              and not re.search(r'black\s*screen|screen\s*off', t))):
        return 'Blue Room'
    if re.search(r'piano|music|melod(?:y|ies)|handpan|ambient music', t):
        if re.search(r'rain|river|forest|bird|nature|water|ocean|wave|stream', t):
            return 'Music & Nature'
        return 'Relaxing Music'
    if re.search(r'fireplace|crackling fire|cozy (?:room|cabin|ambience|autumn|winter)|cottage', t):
        return 'Cozy Ambience'
    if re.search(r'rain|thunder|drizzle|downpour', t):
        return 'Rain Sounds'
    if re.search(r'river|forest|bird|nature|waterfall|stream|ocean|wave|wind', t):
        return 'Nature Sounds'
    if re.search(r'pink noise|brown noise|white noise|fan|appliance|household|hum', t):
        return 'Noise & Household'
    return 'Other Calm Videos'


def normalize_new(v: dict, blue_ids: set[str]) -> dict | None:
    ident = v.get('id')
    if not isinstance(ident, str) or not VIDEO_ID.fullmatch(ident): return None
    try:
        secs = int(v.get('durationSeconds', 0))
    except (ValueError, TypeError): return None
    if secs < MINIMUM_SECONDS: return None
    try:
        date = datetime.fromisoformat(v['publishedAt'].replace('Z', '+00:00'))
    except (ValueError, TypeError, KeyError): return None
    if date > datetime.now(timezone.utc): return None
    title = str(v.get('title') or '').strip()
    if not title: return None
    desc = extract_description(v.get('description') or '')
    return dict(id=ident,title=title, date=date.date().isoformat(),
                publishedAt=v['publishedAt'], duration=iso_duration(secs),
                durationSeconds=secs, durationLabel=duration_label(secs),
                cat=classify(title, desc, ident in blue_ids), description=desc, short=False)


def make_card(v: dict) -> str:
    ident, title, cat = v['id'], esc(v['title']), esc(v['cat'])
    label = esc(v['durationLabel'])
    blue_attribute = ' data-blue-room="true"' if v["cat"] == "Blue Room" else ""
    return (f'<article class="libraryCard" data-title="{esc(v["title"].lower())}" data-cat="{cat}" '
            f'data-year="{v["date"][:4]}" data-type="long" data-id="{ident}"'
            f'{blue_attribute}>'
            f'<button class="mediaPreview js-player" type="button" data-video="{ident}" '
            f'aria-label="Play preview: {title}"><img src="https://i.ytimg.com/vi/{ident}/hqdefault.jpg" '
            f'alt="Preview of {title}" loading="lazy" decoding="async" width="480" height="360"/>'
            f'<span class="playCircle" aria-hidden="true">▶</span></button>'
            f'<div class="libraryCopy"><span class="videoMeta">{cat} · {label}</span>'
            f'<h2><a href="videos/{ident}.html">{title}</a></h2><p>{v["date"]}</p>'
            f'<a class="textlink" href="videos/{ident}.html">Video details and YouTube link →</a>'
            f'</div></article>')


def make_page(v: dict, sample: str, catalogue: list[dict]) -> str:
    """Create a new detail page matching the site's CSS and established URL shape."""
    header_m = re.search(r'<header\b.*?</header>', sample, flags=re.S)
    footer_m = re.search(r'<footer\b.*?</footer>', sample, flags=re.S)
    if not header_m or not footer_m:
        raise ValueError('Existing detail page template is missing its header or footer')
    header, footer = header_m.group(), footer_m.group()
    ident, title, cat = v['id'], v['title'], v['cat']
    desc = extract_description(v['description'])
    seo = meta_description(title, desc)
    canonical = BASE + 'videos/' + ident + '.html'
    thumb = f'https://i.ytimg.com/vi/{ident}/hqdefault.jpg'
    embed = f'https://www.youtube.com/embed/{ident}'
    youtube = f'https://www.youtube.com/watch?v={ident}'
    route = {
        'Black Screen': ('../black-screen.html', 'Black Screen'),
        'Japanese Bedroom': ('../japanese-bedroom.html', 'Japanese Bedroom'),
        'Music & Nature': ('../music-nature.html', 'Music & Nature'),
        'Relaxing Music': ('../music.html', 'Relaxing Music'),
        'Rain Sounds': ('../rain-sounds.html', 'Rain Sounds'),
        'Blue Room': ('../playlists.html#blue-room', 'Blue Room'),
        'Cozy Ambience': ('../rain-sounds.html', 'Cozy Ambience'),
    }.get(cat, ('../videos.html', cat))
    # Related links use original catalogue records, without changing any existing page.
    related = [item for item in catalogue if item['id'] != ident and item.get('cat') == cat][:3]
    if len(related) < 3:
        related += [item for item in catalogue if item['id'] != ident and item not in related][:3-len(related)]
    cards = []
    for item in related:
        i = item['id']; t = esc(item['title'])
        cards.append(f'<article class="watchCard"><a class="watchThumb" href="{i}.html"><img '
                     f'src="https://i.ytimg.com/vi/{i}/hqdefault.jpg" alt="Video preview: {t}" '
                     'width="480" height="360" loading="lazy" decoding="async"/></a><div>'
                     f'<span class="videoMeta">{esc(item.get("cat", "SonoCalming"))}</span>'
                     f'<h3><a href="{i}.html">{t}</a></h3>'
                     f'<a class="textlink" href="{i}.html">Watch video →</a></div></article>')
    ld = {
        '@context':'https://schema.org','@type':'VideoObject','name':title,
        'description':seo, 'thumbnailUrl':[thumb], 'uploadDate':v['date'],
        'duration':v['duration'], 'embedUrl':embed,'url':canonical,
        'potentialAction':{'@type':'WatchAction','target':youtube},
        'publisher':{'@type':'Organization','name':'SonoCalming',
                     'url':'https://www.youtube.com/channel/UCGXypunMB75x599kvbSAuqw'}
    }
    crumbs = {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
        {'@type':'ListItem','position':1,'name':'SonoCalming','item':BASE},
        {'@type':'ListItem','position':2,'name':'All Videos','item':BASE+'videos.html'},
        {'@type':'ListItem','position':3,'name':title,'item':canonical}]}
    def jsonld(value: dict) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<','\\u003c')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title[:64])} | SonoCalming</title><meta name="description" content="{esc(seo)}"/>
<meta name="robots" content="index,follow,max-image-preview:large,max-video-preview:-1,max-snippet:-1"/>
<link rel="canonical" href="{canonical}"/><link rel="icon" href="../favicon.svg" type="image/svg+xml"/>
<meta name="theme-color" content="#08131c"/><meta name="referrer" content="strict-origin-when-cross-origin"/>
<meta property="og:site_name" content="SonoCalming"/><meta property="og:type" content="video.other"/>
<meta property="og:title" content="{esc(title)}"/><meta property="og:description" content="{esc(seo)}"/>
<meta property="og:url" content="{canonical}"/><meta property="og:image" content="{thumb}"/>
<meta name="twitter:card" content="summary_large_image"/><meta name="twitter:title" content="{esc(title)}"/>
<meta name="twitter:description" content="{esc(seo)}"/><meta name="twitter:image" content="{thumb}"/>
<link rel="preconnect" href="https://www.youtube.com"/><link rel="preconnect" href="https://i.ytimg.com"/>
<link rel="stylesheet" href="../styles-20261009.css"/>
<script type="application/ld+json">{jsonld(ld)}</script><script type="application/ld+json">{jsonld(crumbs)}</script></head>
<body><a class="skip" href="#main">Skip to content</a>{header}<main id="main">
<section class="section shell"><p class="eyebrow">SonoCalming · {esc(cat)}</p><h1>{esc(title)}</h1>
<p class="lead">Published on {esc(v['date'])} · {esc(v['durationLabel'])}</p></section>
<section class="section shell detailLayout"><article>
<div class="video prominentVideo"><iframe src="{embed}?rel=0&amp;playsinline=1" loading="eager" title="Watch {esc(title)} on SonoCalming" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>
<div class="detailText"><h2>About this video</h2><p>{esc(desc)}</p>
<p>Duration: {esc(v['durationLabel'])}. Published on {esc(v['date'])}.</p>
<div class="actions"><a class="btn primary" href="{youtube}" target="_blank" rel="noopener noreferrer">Watch on YouTube ↗</a><a class="btn" href="../videos.html">Browse all videos</a></div>
<p class="note">Music, when present, belongs to its respective artists. Playback is provided through the official YouTube player.</p></div></article>
<aside class="detailAside"><h2>More to explore</h2><p>Keep listening to the same atmosphere or choose something different.</p>
<a class="textlink" href="{route[0]}">Explore {esc(route[1])} →</a><div class="relatedCards">{''.join(cards)}</div></aside></section>
</main>{footer}<script defer src="../site.js"></script></body></html>\n'''


def upsert_sitemaps(new: list[dict]) -> None:
    if not new: return
    today = datetime.now(timezone.utc).date().isoformat()
    normal_path = ROOT/'sitemap.xml'
    video_path = ROOT/'video-sitemap.xml'
    index_path = ROOT/'sitemap-index.xml'
    normal = normal_path.read_text(encoding='utf-8')
    video_xml = video_path.read_text(encoding='utf-8')
    for v in new:
        url = BASE + 'videos/' + v['id'] + '.html'
        if url not in normal:
            normal = normal.replace('</urlset>', f'  <url><loc>{xml_escape(url)}</loc><lastmod>{today}</lastmod></url>\n</urlset>')
        if url in video_xml: continue
        # Google restricts video:duration to 28800 seconds. Omit for 10h videos.
        dur = f'<video:duration>{v["durationSeconds"]}</video:duration>' if v['durationSeconds'] <= 28800 else ''
        snippet = (f'  <url><loc>{xml_escape(url)}</loc><video:video>'
                   f'<video:thumbnail_loc>https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg</video:thumbnail_loc>'
                   f'<video:title>{xml_escape(v["title"])}</video:title>'
                   f'<video:description>{xml_escape(meta_description(v["title"], v["description"]))}</video:description>'
                   f'<video:player_loc>https://www.youtube.com/embed/{v["id"]}</video:player_loc>'
                   f'<video:publication_date>{v["date"]}</video:publication_date>{dur}'
                   f'</video:video></url>\n')
        video_xml = video_xml.replace('</urlset>', snippet + '</urlset>')
    normal = re.sub(r'(<loc>'+re.escape(BASE+r'videos.html')+r'</loc>\s*<lastmod>)\d{4}-\d{2}-\d{2}', lambda m:m.group(1)+today, normal)
    normal_path.write_text(normal, encoding='utf-8')
    video_path.write_text(video_xml, encoding='utf-8')
    index = index_path.read_text(encoding='utf-8')
    index = re.sub(r'<lastmod>\d{4}-\d{2}-\d{2}</lastmod>', f'<lastmod>{today}</lastmod>', index)
    index_path.write_text(index, encoding='utf-8')


def apply_catalogue_updates(new: list[dict], blue_ids: set[str], all_items: list[dict]) -> bool:
    page_path = ROOT/'videos.html'
    original = page_path.read_text(encoding='utf-8')
    updated = original
    # Keep ALL existing cards untouched in place; one additional marker for Blue Room playlist filtering.
    for ident in blue_ids:
        if not VIDEO_ID.fullmatch(ident): continue
        rx = re.compile(r'(<article class="libraryCard"(?=[^>]*data-id="'+re.escape(ident)+r'")[^>]*)(>)')
        def tag(m: re.Match) -> str:
            if 'data-blue-room=' in m.group(1): return m.group(0)
            return m.group(1) + ' data-blue-room="true"' + m.group(2)
        updated = rx.sub(tag, updated, count=1)
    # A legacy video can retain its original category while appearing in the
    # additional Blue Room filter. Show the secondary membership visibly.
    for ident in blue_ids:
        if not VIDEO_ID.fullmatch(ident):
            continue
        rx = re.compile(r'(<article class="libraryCard"(?=[^>]*data-id="' + re.escape(ident) + r'")[^>]*>)(.*?)(</article>)', re.S)
        def add_label(m: re.Match) -> str:
            inside = m.group(2)
            if 'data-cat="Blue Room"' in m.group(1) or 'class="blueRoomLabel"' in inside:
                return m.group(0)
            inside = re.sub(r'(<span class="videoMeta">.*?)(</span>)',
                            lambda m: m.group(1) + ' <span class="blueRoomLabel">· Blue Room</span>' + m.group(2), inside, count=1, flags=re.S)
            return m.group(1) + inside + m.group(3)
        updated = rx.sub(add_label, updated, count=1)
    if new:
        sentinel = '<section class="section shell librarySection"><div id="libraryGrid" class="libraryGrid">'
        if sentinel not in updated: raise ValueError('Cannot find catalogue insertion point')
        updated = updated.replace(sentinel, sentinel + '\n' + '\n'.join(make_card(x) for x in new) + '\n', 1)
        # Only mutate dynamic catalogue numbers, never any previous video data.
        prev_count = len(all_items)-len(new)
        updated = updated.replace(f'with {prev_count} real videos', f'with {len(all_items)} real videos')
        updated = updated.replace(f'Explore {prev_count} public videos', f'Explore {len(all_items)} public videos')
        updated = updated.replace(f'Showing all {prev_count} videos', f'Showing all {len(all_items)} videos')
        updated = updated.replace(f'{prev_count} public videos', f'{len(all_items)} public videos')
        # CollectionPage JSON-LD lists all old and new entries in actual displayed order.
        ld_rx = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
        match = ld_rx.search(updated)
        if match:
            data = json.loads(match.group(2))
            if data.get('@type') == 'CollectionPage' and 'mainEntity' in data:
                listing = data['mainEntity']
                prior = listing.get('itemListElement', [])
                listing['itemListElement'] = ([{'@type':'ListItem','position':i+1,
                    'url':BASE+'videos/'+v['id']+'.html','name':v['title']} for i,v in enumerate(new)]
                    + [dict(item, position=i+1+len(new)) for i,item in enumerate(prior)])
                listing['numberOfItems'] = len(all_items)
                ld = json.dumps(data, ensure_ascii=False, separators=(',',':')).replace('<','\\u003c')
                updated = updated[:match.start(2)] + ld + updated[match.end(2):]
    # Keep the existing filter categories; add Blue Room and adjust counts.
    cat_counter = Counter(v.get('cat', '') for v in all_items)
    blue_count = sum(1 for v in all_items if v.get('blueRoom') or v.get('cat') == 'Blue Room' or v['id'] in blue_ids)
    opt_rx = re.compile(r'(<option value="([^"]+)">)([^<]+)(</option>)')
    def new_option(m: re.Match) -> str:
        category = html.unescape(m.group(2))
        if category in cat_counter or category == 'Blue Room':
            n = blue_count if category == 'Blue Room' else cat_counter[category]
            return m.group(1) + esc(category) + f' ({n})' + m.group(4)
        return m.group(0)
    # Replace ONLY options within Category filter, not year/format options.
    cat_sel = re.search(r'<select id="libraryCategory">.*?</select>', updated, re.S)
    if not cat_sel: raise ValueError('Category filter missing')
    select_text = opt_rx.sub(new_option, cat_sel.group(0))
    if 'value="Blue Room"' not in select_text:
        new_opt = f'<option value="Blue Room">Blue Room ({blue_count})</option>'
        anchor = re.search(r'<option value="Black Screen">.*?</option>', select_text)
        if anchor:
            select_text = select_text[:anchor.end()] + new_opt + select_text[anchor.end():]
        else:
            select_text = select_text.replace('<option value="all">All categories</option>', '<option value="all">All categories</option>' + new_opt)
    updated = updated[:cat_sel.start()] + select_text + updated[cat_sel.end():]
    years = re.search(r'<select id="libraryYear">.*?</select>', updated, re.S)
    if years:
        years_needed = sorted({v['date'][:4] for v in all_items}, reverse=True)
        original_year_select = years.group(0)
        for yr in years_needed:
            if f'value="{yr}"' not in original_year_select:
                original_year_select = original_year_select.replace('</select>', f'<option value="{yr}">{yr}</option></select>')
        updated = updated[:years.start()] + original_year_select + updated[years.end():]
    if updated != original:
        page_path.write_text(updated, encoding='utf-8')
        return True
    return False


def sync_catalogue(source: list[dict], blue_ids: set[str] | None = None) -> list[dict]:
    blue_ids = blue_ids or set()
    cat_file = ROOT/'videos.json'
    catalogue = json.loads(cat_file.read_text(encoding='utf-8'))
    existing = {x['id'] for x in catalogue}
    latest_existing = max((x['date'] for x in catalogue if x.get('date')), default='2000-01-01')
    # Add only NEW uploads; do not retroactively fill older missing video pages.
    candidates = []
    for video in source:
        v = normalize_new(video, blue_ids)
        if v and v['id'] not in existing and v['date'] >= latest_existing:
            candidates.append(v)
    new = sorted({v['id']:v for v in candidates}.values(),
                 key=lambda v:(v['publishedAt'],v['id']), reverse=True)
    for v in new:
        target = ROOT/'videos'/f'{v["id"]}.html'
        if target.exists():
            # Existing pages are sacrosanct; never regenerate them.
            continue
        sample = (ROOT/'videos'/f'{catalogue[0]["id"]}.html').read_text(encoding='utf-8')
        target.write_text(make_page(v, sample, catalogue), encoding='utf-8')
    if new:
        new_records = [{k:v[k] for k in ('id','title','date','duration','cat','short')} for v in new]
        catalogue = new_records + catalogue
    # Secondary Blue Room membership for all existing catalogue entries. This
    # does not overwrite their original category or regenerate their pages.
    membership_changed = False
    if blue_ids:
        for entry in catalogue:
            if entry['id'] in blue_ids and not entry.get('blueRoom'):
                entry['blueRoom'] = True
                membership_changed = True
    changed = apply_catalogue_updates(new, blue_ids, catalogue)
    if new or membership_changed:
        cat_file.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if new:
        upsert_sitemaps(new)
    print(f'Catalogue sync: {len(new)} new long video(s), total {len(catalogue)}, '
          f'filter updated: {changed}.')
    return new


if __name__ == '__main__':
    feed = json.loads((ROOT/'latest-videos.json').read_text(encoding='utf-8'))
    sync_catalogue(feed['videos'])
