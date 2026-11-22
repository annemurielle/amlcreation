#!/usr/bin/env python3
"""Offline SEO deployment guard: no dependencies or access to Google required.

Checks the REAL published HTML/site-map sources, without claiming Google
indexation or remote HTTP status. Excludes verification and redirect pages
from the list of independently indexable pages.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, unquote, urlparse
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.amlcreation.ch/'
PUBLIC_HOST='www.amlcreation.ch'
IGNORE={'yandex_4b60be54e1aa17aa.html'}
SM='http://www.sitemaps.org/schemas/sitemap/0.9'

class Scan(HTMLParser):
    def __init__(self,markup:str):
        super().__init__(convert_charrefs=True)
        self.title=''; self.lang=None; self.description=None; self.canonical=None; self.noindex=False
        self.hrefs=[];self.hreflangs={};self.jsonlds=[];self._title=False;self._json=False;self._buf=[]
        self.feed(markup)
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='html':self.lang=d.get('lang')
        if tag=='title':self._title=True
        if tag=='meta':
            if d.get('name','').lower()=='description':self.description=d.get('content')
            if d.get('name','').lower()=='robots' and 'noindex' in d.get('content','').lower():self.noindex=True
        if tag=='link':
            if 'canonical' in (d.get('rel') or '').lower().split():self.canonical=d.get('href')
            if d.get('hreflang'):self.hreflangs[d['hreflang']]=d.get('href')
        if tag in ('a','img','script','link','iframe','video','source'):
            for key in ('href','src'):
                if d.get(key):self.hrefs.append(d[key])
        if tag=='script' and d.get('type','').lower()=='application/ld+json':
            self._json=True;self._buf=[]
    def handle_endtag(self,tag):
        if tag=='title':self._title=False
        if tag=='script' and self._json:
            self.jsonlds.append(''.join(self._buf));self._json=False;self._buf=[]
    def handle_data(self,data):
        if self._title:self.title+=data
        if self._json:self._buf.append(data)

def url_of(file:Path)->str:
    rel=file.relative_to(ROOT).as_posix()
    return BASE+(rel[:-len('index.html')] if rel.endswith('index.html') else rel)

def site_path(url:str)->Path|None:
    parsed=urlparse(url)
    if parsed.hostname not in ('amlcreation.ch',PUBLIC_HOST):return None
    rel=unquote(parsed.path).lstrip('/')
    return (ROOT/rel/'index.html') if (ROOT/rel).is_dir() else (ROOT/rel)

def scan_json(tree,place:str,issues:list[str],count:Counter)->None:
    if isinstance(tree,list):
        for item in tree:scan_json(item,place,issues,count)
    elif isinstance(tree,dict):
        types=tree.get('@type')
        if isinstance(types,str):types=[types]
        for kind in types or []:
            if kind=='VideoObject':
                count['videos']+=1
                for key in ('name','description','thumbnailUrl','uploadDate'):
                    if not tree.get(key):issues.append(place+': VideoObject missing '+key)
                stamp=tree.get('uploadDate')
                if stamp:
                    try:
                        dt=datetime.fromisoformat(str(stamp).replace('Z','+00:00'))
                        if dt.tzinfo is None:raise ValueError('timezone missing')
                    except ValueError:issues.append(place+': invalid VideoObject uploadDate '+str(stamp))
                if not (tree.get('embedUrl') or tree.get('contentUrl')):
                    issues.append(place+': VideoObject missing video playback URL')
            if kind in ('SoftwareApplication','MobileApplication'):
                rating=tree.get('aggregateRating') or tree.get('review')
                offer=tree.get('offers')
                if not rating or not isinstance(offer,dict) or offer.get('price') is None:
                    issues.append(place+': noneligible SoftwareApplication, needs verified rating and price')
            if kind=='BreadcrumbList':
                count['breadcrumbs']+=1
                for crumb in tree.get('itemListElement',[]):
                    if not crumb.get('name') or not crumb.get('position'):
                        issues.append(place+': BreadcrumbList item missing name or position')
        for key,val in tree.items():
            if key!='@context':scan_json(val,place,issues,count)

def main()->int:
    files=sorted(p for p in ROOT.rglob('*.html') if 'venv' not in p.parts)
    issues=[];counts=Counter();canonical=set();duplicate=set();noncanonical=set();scanned={}
    for file in files:
        rel=file.relative_to(ROOT).as_posix();url=url_of(file)
        if rel in IGNORE:continue
        s=Scan(file.read_text(encoding='utf-8',errors='replace'))
        scanned[url]=s
        counts['html_pages']+=1
        if not s.title.strip():issues.append(rel+': missing <title>')
        if not s.lang:issues.append(rel+': missing html lang')
        if not s.description and rel not in ('MahjongCastle/index.html',):issues.append(rel+': missing meta description')
        if not s.noindex:
            if not s.canonical:issues.append(rel+': missing canonical')
            elif not s.canonical.startswith(BASE):issues.append(rel+': canonical must be absolute and on current site')
            elif not site_path(s.canonical).is_file():issues.append(rel+': missing canonical target')
            elif s.canonical==url:canonical.add(url)
            else:noncanonical.add(url)
        if s.hreflangs and s.canonical==url and url not in s.hreflangs.values():
            issues.append(rel+': hreflang does not include its own canonical URL')
        for language,alternate in s.hreflangs.items():
            target=site_path(alternate or '')
            if target is not None and not target.is_file():
                issues.append(rel+': missing hreflang target: '+str(alternate))
            if alternate==url and language != 'x-default' and s.lang.lower()!=language.lower():
                issues.append(rel+f': html lang {s.lang} contradicts self hreflang {language}')
        for href in s.hrefs:
            if href.startswith(('#','mailto:','tel:','javascript:','data:')):continue
            target=site_path(urljoin(url,href))
            if target is not None and not target.is_file():
                issues.append(rel+': broken local link/asset '+href[:180])
        for js in s.jsonlds:
            try:tree=json.loads(js)
            except ValueError as exc:issues.append(rel+': malformed JSON-LD '+str(exc));continue
            scan_json(tree,rel,issues,counts)
    # A sitemap index must enumerate only real XML files; a URL sitemap must
    # contain only existing canonical self-indexable pages.
    urls=set(); visited_xml=set()
    def walk_sitemap(path:Path):
        if path in visited_xml:return
        visited_xml.add(path)
        try:doc=ET.parse(path).getroot()
        except (OSError,ET.ParseError) as exc:issues.append('Sitemap not parseable '+str(path)+': '+str(exc));return
        if doc.tag==f'{{{SM}}}sitemapindex':
            for node in doc.findall(f'{{{SM}}}sitemap/{{{SM}}}loc'):
                target=site_path(node.text or '')
                if target is None or not target.is_file():issues.append('Missing sitemap '+str(node.text))
                else:walk_sitemap(target)
        elif doc.tag==f'{{{SM}}}urlset':
            for node in doc.findall(f'{{{SM}}}url/{{{SM}}}loc'):
                value=node.text or ''
                urls.add(value)
                if value not in canonical:issues.append('Noncanonical, missing or noindex URL in sitemap '+value)
        else:issues.append('Unexpected sitemap XML root '+str(path))
    walk_sitemap(ROOT/'sitemap.xml')
    if canonical-urls:issues.append(f'{len(canonical-urls)} canonical pages absent from sitemap; first: '+str(sorted(canonical-urls)[:5]))
    counts['canonical_indexable']=len(canonical)
    counts['sitemap_unique_urls']=len(urls)
    counts['canonical_aliases']=len(noncanonical)
    counts['sitemaps_xml']=len(visited_xml)
    if issues:
        print(f'SEO AUDIT FAILED: {len(issues)} issue(s).')
        for issue in issues[:45]:print('ERROR:',issue)
    else:print('SEO AUDIT PASSED (offline structural checks).')
    for key,value in sorted(counts.items()):print(f'  {key}: {value}')
    return 1 if issues else 0

if __name__=='__main__':sys.exit(main())
