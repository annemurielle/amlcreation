#!/usr/bin/env python3
"""Maintain SonoCalming's static on-site SEO without changing any video URLs.

Run after update_sonocalming_latest.py (which creates video pages). Safe to repeat:
existing hand-written descriptions stay untouched and unchanged pages are not rewritten.
Python standard library only, no YouTube API calls or credentials.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'SonoCalming'
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
BASE = 'https://www.amlcreation.ch/SonoCalming/'
GENERIC = {
    'Watch a gentle creative moment, including drawing, coloring, craft or everyday ASMR.',
    'Watch a short SonoCalming clip for a brief peaceful moment.',
    'Discover calm music alongside natural soundscapes and gentle visuals.',
    'Explore water, wind, birds, forest or other natural soundscapes.',
    'Enjoy relaxing background music for reading, studying, focus or quiet moments.',
    'Listen to rain ambience, rainfall and outdoor night sounds in this SonoCalming video.',
    'Listen with minimal visual distraction, using steady rain, noise or other dark-screen audio.',
    'Explore a quiet walk or travel scene with ambient sights and sounds.',
    'Settle into a warm, cozy ambience with soft environmental sounds.',
    'Discover another SonoCalming video in the complete channel archive.',
    'Enjoy a cozy nighttime Japanese bedroom with steady rain and a quiet indoor atmosphere.',
    'Listen to steady colored noise or household sounds for quiet background listening.',
}
# Only use information supported by the original title. Never infer a sound that
# isn't named, or claim every video has no music or thunder.
PHRASES = [
    (r'rain on (?:the )?(?:window|windows|glass|skylight)', 'rain on a window'),
    (r'rain on (?:the )?(?:roof|rooftop|car roof)', 'rain on a roof'),
    (r'rain on (?:the )?(?:leaves|leaf|foliage)', 'rain on leaves'),
    (r'rain on (?:a |the )?(?:tent)', 'rain on a tent'),
    (r'rain on (?:a |the )?(?:umbrella)', 'rain on an umbrella'),
    (r'(?:japanese bedroom|japanese room)', 'Japanese bedroom ambience'),
    (r'(?:heavy rain|downpour|torrential rain)', 'heavy rainfall'),
    (r'(?:gentle rain|soft rain|light rain|drizzle)', 'gentle rainfall'),
    (r'\b(?:rain|rainfall|rainy)\b', 'rain sounds'),
    (r'(?:thunderstorm|thunderclaps|thunder)', 'thunder sounds'),
    (r'(?:ocean waves|sea waves|waves)', 'ocean waves'),
    (r'(?:waterfall)', 'waterfall sounds'),
    (r'(?:river|stream|brook)', 'running water'),
    (r'(?:fireplace|crackling fire|campfire)', 'fireplace sounds'),
    (r'(?:dishwasher)', 'dishwasher ambience'),
    (r'(?:fan sound|fan noise|room fan)', 'fan sounds'),
    (r'(?:brown noise)', 'brown noise'),
    (r'(?:pink noise)', 'pink noise'),
    (r'(?:white noise)', 'white noise'),
    (r'(?:grey noise|gray noise)', 'grey noise'),
    (r'(?:piano)', 'piano music'),
    (r'(?:handpan)', 'handpan music'),
    (r'(?:lo-?fi)', 'lo-fi music'),
    (r'(?:jazz)', 'jazz music'),
    (r'(?:birdsong|bird[s]? chirping|birds)', 'birdsong'),
    (r'(?:forest|woodland)', 'forest ambience'),
    (r'(?:wind|breeze)', 'wind sounds'),
    (r'(?:coloring|colouring|color with me)', 'coloring'),
    (r'(?:watercolor|watercolour|painting)', 'watercolor painting'),
    (r'(?:asmr)', 'ASMR'),
]
CATEGORIES = {
    'Black Screen': ('black-screen.html', 'black-screen ambience'),
    'Japanese Bedroom': ('japanese-bedroom.html', 'Japanese bedroom rain'),
    'Rain Sounds': ('rain-sounds.html', 'rain soundscapes'),
    'Music & Nature': ('music-nature.html', 'music with nature sounds'),
    'Relaxing Music': ('music.html', 'relaxing music'),
    'Cozy Ambience': ('rain-sounds.html', 'cozy ambience'),
    'Blue Room': ('playlists.html', 'blue-room ambience'),
    'Noise & Household': ('black-screen.html', 'background noise and household ambience'),
    'Nature Sounds': ('playlists.html', 'nature ambience'),
    'Art & ASMR': ('videos.html', 'art and ASMR'),
    'Walks & Travel': ('videos.html', 'walks and travel'),
    'Shorts': ('videos.html', 'short clips'),
}
CATEGORY_SEO = {
    'rain-sounds.html': ('Rain Sounds for Sleeping: Window, Roof & Night Rain | SonoCalming',
                         'Listen to long rain sounds, from rain on windows and rooftops to leaves, Japanese bedrooms and cozy interiors. Explore SonoCalming rain videos.'),
    'black-screen.html': ('Black Screen Rain Sounds & Brown Noise | SonoCalming',
                          'Explore black screen rain, brown noise and steady nighttime ambience, with long videos and no distracting visuals. Choose a SonoCalming sound.'),
    'japanese-bedroom.html': ('Japanese Bedroom Rain Sounds at Night | SonoCalming',
                              'Explore long Japanese bedroom rain sounds, from rain on a window or roof to cozy nighttime rooms and gentle or heavy rainfall.'),
    'music-nature.html': ('Relaxing Piano with Rain & Nature Sounds | SonoCalming',
                          'Listen to relaxing piano with rain sounds, flowing water, birdsong and gentle nature ambience. Explore SonoCalming music and nature videos.'),
    'music.html': ('Relaxing Piano & Ambient Music for Reading | SonoCalming',
                   'Explore soft piano, ambient music and calm background music for reading, studying, focus and quiet moments on SonoCalming.'),
    'rain-piano.html': ('Rain and Piano Music for Reading & Quiet Nights | SonoCalming',
                        'Discover relaxing piano and rain sounds together, with long videos for reading, studying and peaceful evenings on SonoCalming.'),
    'playlists.html': ('SonoCalming Playlists: Rain, Black Screen & Piano Music',
                       'Browse SonoCalming playlists for long rain sounds, black screen audio, Japanese bedroom rain, soft piano and relaxing music with nature.'),
}


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def clean(text: str) -> str:
    text = re.sub(r'\s+', ' ', html.unescape(text)).strip()
    # Do not generate medical or efficacy claims in new SEO copy.
    text = re.sub(r'\b(?:healing|relief|therapy|cure|treatment)\b', '', text, flags=re.I)
    return re.sub(r'\s+', ' ', text).strip(' ,.-:')


def title_tag(title: str) -> str:
    # Preserve the complete descriptive title and proper names. Search engines
    # may shorten the result visually, but the HTML should remain accurate.
    title = clean(title)
    return f'{title} | SonoCalming' if title else 'SonoCalming Videos'


def duration_label(record: dict) -> str:
    duration = record.get('duration', '')
    m = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if m:
        h, mi, sec = (int(x or 0) for x in m.groups())
        if h: return f'{h}-hour' if not mi else f'{h}-hour {mi}-minute'
        if mi: return f'{mi}-minute'
        return f'{sec}-second'
    return 'long-form' if not record.get('short') else 'short'


def sounds(title: str) -> list[str]:
    title = clean(title).lower()
    result: list[str] = []
    for regex, desc in PHRASES:
        if desc == 'thunder sounds' and re.search(r'\bno thunder\b|\bwithout thunder\b', title, flags=re.I):
            continue
        if re.search(regex, title, flags=re.I) and desc not in result:
            result.append(desc)
    # Avoid generic rain if a more descriptive type of rain was found.
    if 'rain sounds' in result and any(x in result for x in ('rain on a window','rain on a roof','rain on leaves','rain on a tent or umbrella','Japanese bedroom ambience','heavy rainfall','gentle rainfall')):
        result.remove('rain sounds')
    if 'forest ambience' in result and 'rain on leaves' in result:
        result.remove('forest ambience')
    return result[:3]


def seo_description(record: dict) -> str:
    title = clean(record.get('title', ''))
    category = record.get('cat', 'SonoCalming')
    features = sounds(title)
    duration = duration_label(record)
    is_short = bool(record.get('short')) or duration.endswith('second')
    subject = ' and '.join(features[:2]) if features else CATEGORIES.get(category, ('','calm ambience'))[1]
    # Use the real video title when the category is too generic to describe
    # the actual subject. This avoids inventing rain, music or ASMR content.
    short_title = re.sub(r'#[\w]+', '', title).strip(' ,.-:|')
    if not short_title:
        short_title = title
    if category == 'Black Screen' or re.search(r'black screen|dark screen', title, re.I):
        sentence = f'Listen to {duration} {subject} with a dark screen on SonoCalming.'
    elif category == 'Japanese Bedroom':
        sentence = f'Explore {duration} {subject} in a cozy Japanese room on SonoCalming.'
    elif category == 'Shorts' or is_short:
        if features:
            sentence = f'Watch a short SonoCalming clip featuring {subject}.'
        else:
            sentence = f'Watch the SonoCalming short video: {short_title}.'
    elif category in {'Art & ASMR', 'Walks & Travel'}:
        if features:
            sentence = f'Watch this {duration} SonoCalming video featuring {subject}.'
        else:
            sentence = f'Watch {short_title}, a {duration} video on SonoCalming.'
    elif category in {'Music & Nature', 'Relaxing Music'}:
        sentence = f'Enjoy {duration} {subject} for reading, studying and quiet moments on SonoCalming.'
    elif category == 'Other Calm Videos':
        sentence = f'Explore {short_title}, a {duration} video on SonoCalming.'
    else:
        sentence = f'Listen to {duration} {subject} on SonoCalming for quiet moments and background listening.'
    details = []
    low = title.lower()
    if re.search(r'\bno music\b|\bwithout music\b',low): details.append('No music')
    if re.search(r'\bno thunder\b|\bwithout thunder\b',low): details.append('No thunder')
    if re.search(r'\bwith thunder\b|\bdistant thunder\b',low): details.append('Includes thunder')
    if details: sentence += ' ' + '; '.join(details) + '.'
    return sentence


def one_replace(s: str, pattern: str, repl, flags: int = 0) -> str:
    new, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        raise ValueError(f'Expected exactly one occurrence of {pattern[:70]}')
    return new


def update_video(path: Path, record: dict) -> bool:
    original = path.read_text(encoding='utf-8')
    page = original
    desc_match = re.search(r'<h2>About this video</h2><p>(.*?)</p>', page, re.S)
    if not desc_match: raise ValueError(f'{path}: missing video description')
    current_description = html.unescape(desc_match.group(1)).strip()
    generated = current_description in GENERIC
    if generated:
        desc = seo_description(record)
        page = page[:desc_match.start(1)] + esc(desc) + page[desc_match.end(1):]
    else:
        # Keep independently authored and detailed original descriptions intact.
        desc = None
    # Stop truncating title elements in the middle of words.
    page = one_replace(page, r'<title>.*?</title>', f'<title>{esc(title_tag(record["title"]))}</title>', re.S)
    if generated:
        new_meta = seo_description(record)
        for key, attr in [('description','name'),('og:description','property'),('twitter:description','name')]:
            pattern = r'(<meta\s+' + attr + r'="' + re.escape(key) + r'"\s+content=")[^"]*(")'
            page = one_replace(page, pattern, lambda m: m.group(1) + esc(new_meta) + m.group(2))
    # A video-specific page should identify its content as a video on social platforms.
    page = re.sub(r'(<meta property="og:type" content=")website(")', r'\1video.other\2', page, count=1)
    # Structured VideoObject description is aligned with visible information.
    def replace_video_ld(match: re.Match[str]) -> str:
        try: data = json.loads(match.group(2))
        except json.JSONDecodeError: return match.group(0)
        if data.get('@type') != 'VideoObject': return match.group(0)
        if generated: data['description'] = seo_description(record)
        data['name'] = record['title']
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + match.group(3)
    page = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)',replace_video_ld,page,flags=re.S)
    if page != original:
        path.write_text(page,encoding='utf-8')
        return True
    return False


def update_category_page(path: Path, title: str, description: str) -> bool:
    original = path.read_text(encoding='utf-8')
    page = original
    # Some category pages use content-before-name attribute ordering.
    page = one_replace(page,r'<title>.*?</title>',f'<title>{esc(title)}</title>',re.S)
    for field in ['description','og:description','twitter:description']:
        attr = 'name' if field in ('description','twitter:description') else 'property'
        pattern_a = r'(<meta\s+' + attr + r'="' + re.escape(field) + r'"\s+content=")[^"]*(")'
        pattern_b = r'(<meta\s+content=")[^"]*("\s+' + attr + r'="' + re.escape(field) + r'")'
        if re.search(pattern_a,page):page = one_replace(page,pattern_a,lambda m:m.group(1)+esc(description)+m.group(2))
        elif re.search(pattern_b,page):page = one_replace(page,pattern_b,lambda m:m.group(1)+esc(description)+m.group(2))
        else:raise ValueError(f'{path}: no {field} tag')
    for field in ['og:title','twitter:title']:
        attr = 'name' if field=='twitter:title' else 'property'
        pattern_a = r'(<meta\s+' + attr + r'="' + re.escape(field) + r'"\s+content=")[^"]*(")'
        pattern_b = r'(<meta\s+content=")[^"]*("\s+' + attr + r'="' + re.escape(field) + r'")'
        if re.search(pattern_a,page):page = one_replace(page,pattern_a,lambda m:m.group(1)+esc(title)+m.group(2))
        elif re.search(pattern_b,page):page = one_replace(page,pattern_b,lambda m:m.group(1)+esc(title)+m.group(2))
        else:raise ValueError(f'{path}: no {field} tag')
    page = re.sub(r'Browse all \d+ videos', 'Browse all videos', page)
    if page != original:
        path.write_text(page,encoding='utf-8');return True
    return False


def update_home(latest: dict) -> bool:
    path = ROOT / 'index.html'
    original = path.read_text(encoding='utf-8')
    page = original
    static_h1 = 'Rain Sounds for Sleeping, Black Screen &amp; Relaxing Music'
    # Stable H1 ensures a consistent search topic. Latest video name is H2 and
    # still updates in JavaScript (the existing id is preserved).
    if '<h1 id="latest-title">' in page:
        page = one_replace(page,r'<h1 id="latest-title">.*?</h1>',
            '<h1>' + static_h1 + '</h1>\n<h2 class="featuredVideoTitle" id="latest-title">Latest SonoCalming long video</h2>',re.S)
    if '.featuredVideoTitle{' not in page:
        css = '.latestHero .featuredVideoTitle{font-size:clamp(1.15rem,2vw,1.55rem);line-height:1.35;letter-spacing:-.01em;margin:0 0 16px;overflow-wrap:anywhere}\n'
        page = one_replace(page,r'</style>',css+'</style>')
    title = 'Rain Sounds for Sleeping, Black Screen & Relaxing Music | SonoCalming'
    description = ('Explore 8 to 10-hour rain sounds, Japanese bedroom rain, black screen ambience, '
                   'gentle piano and relaxing nature sounds on SonoCalming.')
    page = one_replace(page,r'<title>.*?</title>',f'<title>{esc(title)}</title>',re.S)
    for field in ['description','og:description','twitter:description','og:title','twitter:title']:
        attr='name' if field in ('description','twitter:description','twitter:title') else 'property'
        value=title if field.endswith('title') else description
        page = one_replace(page,r'(<meta\s+content=")[^"]*("\s+'+attr+'="'+field+r'")',
                           lambda m:m.group(1)+esc(value)+m.group(2))
    # Server-render a useful latest video name/date/description so search bots
    # and visitors without JS see real content instead of only placeholders.
    video_title = esc(latest['title'])
    page = one_replace(page,r'(<h2 class="featuredVideoTitle" id="latest-title">).*?(</h2>)',
                       lambda m:m.group(1)+video_title+m.group(2),re.S)
    video_date = latest.get('publishedAt','')[:10]
    video_date = datetime.fromisoformat(video_date).strftime('%B %d, %Y') if re.fullmatch(r'\d{4}-\d{2}-\d{2}',video_date) else ''
    meta = ' · '.join(x for x in (latest.get('durationLabel',''),video_date) if x)
    page = one_replace(page,r'(<p class="latestMeta" id="latest-meta">).*?(</p>)',
                       lambda m:m.group(1)+esc(meta)+m.group(2),re.S)
    text = clean(latest.get('description',''))[:250].rsplit(' ',1)[0].rstrip(' ,.;')
    if not text: text = 'Listen to the latest long SonoCalming soundscape.'
    page = one_replace(page,r'(<p class="lead" id="latest-description">).*?(</p>)',
                       lambda m:m.group(1)+esc(text)+m.group(2),re.S)
    link = f'https://www.youtube.com/watch?v={latest["id"]}'
    # Keep existing link and JS selection, but make the static fallback useful.
    page = one_replace(page,r'(<a class="btn primary" id="latest-youtube" href=")[^"]*("[^>]*>).*?(</a>)',
                       lambda m:m.group(1)+link+m.group(2)+'Watch on YouTube'+m.group(3),re.S)
    if page != original:
        path.write_text(page,encoding='utf-8');return True
    return False


def main() -> None:
    cat = json.loads((ROOT/'videos.json').read_text(encoding='utf-8'))
    current = json.loads((ROOT/'latest-videos.json').read_text(encoding='utf-8'))['videos']
    assert current and VIDEO_ID.fullmatch(current[0]['id'])
    count = 0
    for record in cat:
        ident = record['id']
        if not VIDEO_ID.fullmatch(ident):
            raise ValueError('Invalid video ID in catalogue')
        path = ROOT/'videos'/f'{ident}.html'
        if path.exists(): count += update_video(path,record)
        # Some old catalogue entries might not have a video page; never invent one.
    cats = sum(update_category_page(ROOT/name,*args) for name,args in CATEGORY_SEO.items())
    about = ROOT/'about.html'
    old = about.read_text(encoding='utf-8')
    new = re.sub(r'Browse all \d+ videos', 'Browse all videos', old)
    if new != old:
        about.write_text(new, encoding='utf-8')
        cats += 1
    home = update_home(current[0])
    print(f'SonoCalming SEO: {count} video page(s), {cats} category page(s), homepage changed: {home}.')


if __name__ == '__main__':main()
