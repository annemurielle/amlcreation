#!/usr/bin/env python3
"""Offline pre-publication health checks for generated multilingual galleries."""
from __future__ import annotations
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SONO=ROOT/'SonoCalming'
BASE='https://www.amlcreation.ch/SonoCalming/'
LANGS=('en','fr','de','es','it','pt','ru','ja')
CATS=('rain-sounds','japanese-bedroom','black-screen','cozy-ambience','music','music-nature','rain-piano','nature-sounds','blue-room','noise-household')
SM='{http://www.sitemaps.org/schemas/sitemap/0.9}'

class Tags(HTMLParser):
    def __init__(self,source):
        super().__init__(convert_charrefs=True)
        self.links=[];self.cards=[];self.lang=''; self.feed(source)
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if tag=='link':self.links.append(data)
        if tag=='button' and 'sono-poster' in data.get('class',''):
            self.cards.append(data.get('data-video',''))
        if tag=='html':self.lang=data.get('lang','')

def run():
    catalog=json.loads((SONO/'videos.json').read_text(encoding='utf-8'))
    ids={v['id'] for v in catalog}
    original_pages=list((SONO/'videos').glob('*.html'))
    assert len(original_pages)>=300, 'Missing many English video detail pages'
    # Never replace the original searchable catalogue with category galleries.
    full_library=(SONO/'videos.html').read_text(encoding='utf-8')
    for key in ('id="librarySearch"', 'id="libraryCategory"',
                'id="libraryYear"', 'id="libraryType"', 'id="libraryGrid"'):
        assert key in full_library, f'Missing searchable library control: {key}'
    count=0
    pages=('index.html',*[x+'.html' for x in CATS],'about.html','playlists.html')
    for lang in LANGS:
        prefix=SONO if lang=='en' else SONO/lang
        for name in pages:
            p=prefix/name
            assert p.is_file(),f'Missing {p}'
            page_content=p.read_text(encoding='utf-8')
            tags=Tags(page_content)
            assert tags.lang==lang,(p,tags.lang)
            assert ('href="videos.html"' in page_content or
                    'href="/SonoCalming/videos.html"' in page_content), f'Full video search not accessible: {p}'
            expected=BASE+('' if lang=='en' else lang+'/')+('' if name=='index.html' else name)
            canon=[x.get('href') for x in tags.links if x.get('rel')=='canonical']
            assert canon==[expected],f'Wrong canonical: {p}: {canon}'
            alt={x.get('hreflang'):x.get('href') for x in tags.links if x.get('rel')=='alternate'}
            assert set(alt)==set(LANGS)|{'x-default'},f'Missing alternate language: {p}'
            assert alt['x-default']==BASE+('' if name=='index.html' else name)
            for code in LANGS:
                assert alt[code]==BASE+('' if code=='en' else code+'/')+('' if name=='index.html' else name),f'Invalid alternate {p} {code}'
            if name[:-5] in CATS:
                assert tags.cards,f'Empty category gallery: {p}'
            for id in tags.cards:
                assert id in ids,f'Unknown video ID {id} in {p}'
            count+=1
    # The i18n sitemap lists all translated pages, plus new English hubs.
    member=(SONO/'sitemap-languages.xml')
    sitem=ET.parse(member).getroot()
    urls=[x.text for x in sitem.findall(f'{SM}url/{SM}loc')]
    assert len(urls)==len(set(urls))==7*len(pages)+4,len(urls)
    for url in urls:
        assert url.startswith(BASE),url
        suffix=url[len(BASE):]
        local=SONO/suffix
        if not suffix or suffix.endswith('/'):
            local=local/'index.html'
        assert local.is_file(),f'Missing sitemap page {url}'
    index=ET.parse(ROOT/'sitemap.xml').getroot()
    top={n.text for n in index.findall(f'{SM}sitemap/{SM}loc')}
    assert BASE+'sitemap-languages.xml' in top,'Missing multilingual sitemap in root index'
    for lang in LANGS[1:]:
        page=(ROOT/lang/'index.html').read_text(encoding='utf-8')
        assert f'href="../SonoCalming/{lang}/"' in page,f'Wrong AML Creation link for {lang}'
    print(f'PASS: {count} language/section pages, {len(urls)} localized sitemap URLs, '
          f'{len(original_pages)} unchanged English video detail pages, eight-language AML navigation')

if __name__=='__main__':run()
