#!/usr/bin/env python3
"""Build accurate, canonical AML Creation XML sitemaps from local public HTML.

- The homepage has eight real language variants and reciprocal hreflang entries.
- Each product-area sitemap contains only its own canonical, indexable pages.
- The dedicated SonoCalming video sitemaps are left intact and remain managed by
  update_sonocalming_catalogue.py, including VideoObject-specific metadata.
- No invented modification dates, artificial priority or changefreq tags.
- Never renames or removes existing HTML, support or privacy URLs.
- Offline, standard-library only, deterministic and safe to rerun in Actions.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.amlcreation.ch/'
SM_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
XHTML_NS = 'http://www.w3.org/1999/xhtml'
ET.register_namespace('', SM_NS)
ET.register_namespace('xhtml', XHTML_NS)
GROUPS = ('Games', 'lumenmine', 'Somnifox', 'MahjongCastle', 'ZenCircle')
LANGUAGES = ('en', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'ja')
PRIVACY_LANGUAGES = ('en','fr','de','es','it','pt','ru','ja','ko','nl','sv','no','tr','hi','zh')


class Metadata(HTMLParser):
    def __init__(self, markup: str):
        super().__init__(convert_charrefs=True)
        self.canonical = None
        self.noindex = False
        self.feed(markup)

    def handle_starttag(self, tag: str, attrs: list[tuple[str,str|None]]) -> None:
        data = dict(attrs)
        if tag == 'link' and 'canonical' in (data.get('rel') or '').lower().split():
            self.canonical = data.get('href')
        elif tag == 'meta' and (data.get('name') or '').lower() == 'robots':
            self.noindex = 'noindex' in (data.get('content') or '').lower()


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if path.name == 'index.html':
        rel = rel[:-len('index.html')]
    return SITE + rel


def publish(urlset: ET.Element, filename: str) -> None:
    ET.indent(urlset, space='  ')
    payload = ET.tostring(urlset, encoding='utf-8', xml_declaration=True).decode('utf-8') + '\n'
    path = ROOT/filename
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8') != payload:
        path.write_text(payload, encoding='utf-8')


def child(parent: ET.Element, name: str, value: str) -> ET.Element:
    element = ET.SubElement(parent,f'{{{SM_NS}}}{name}')
    element.text = value
    return element


def canonical_pages(directory: str) -> list[str]:
    output = set()
    for html in sorted((ROOT/directory).rglob('*.html')):
        if html.name.endswith('_x.html') or html.name.startswith('._'):
            continue
        url = url_for(html)
        metadata = Metadata(html.read_text(encoding='utf-8',errors='replace'))
        if metadata.noindex or not metadata.canonical:
            continue
        if urljoin(url, metadata.canonical) != url:
            continue
        output.add(url)
    return sorted(output)


def make_urlset(urls: list[str], dest: str, multilingual: bool = False) -> None:
    root = ET.Element(f'{{{SM_NS}}}urlset')
    alternatives = {'en':SITE}
    alternatives.update({lang:SITE+lang+'/' for lang in LANGUAGES if lang!='en'})
    alternatives['x-default'] = SITE
    for url in urls:
        item=ET.SubElement(root,f'{{{SM_NS}}}url')
        child(item,'loc',url)
        if multilingual:
            for lang,href in alternatives.items():
                ET.SubElement(item,f'{{{XHTML_NS}}}link',{
                    'rel':'alternate','hreflang':lang,'href':href})
    publish(root,dest)


def make_index(dest: str, members: list[str]) -> None:
    root = ET.Element(f'{{{SM_NS}}}sitemapindex')
    for member in members:
        item=ET.SubElement(root,f'{{{SM_NS}}}sitemap')
        child(item,'loc',SITE+member)
    publish(root,dest)


def main() -> None:
    home=[SITE]+[SITE+lang+'/' for lang in LANGUAGES if lang != 'en']
    for url in home:
        path=ROOT/('index.html' if url==SITE else url[len(SITE):]+'index.html')
        metadata=Metadata(path.read_text(encoding='utf-8'))
        if urljoin(url,metadata.canonical or '') != url:
            raise RuntimeError(f'Noncanonical homepage, cannot build hreflang sitemap: {path}')
    # The policy pages are indexable, localized legal documents. They are
    # intentionally independent from the homepage hreflang cluster.
    privacy = [SITE+'Policy-Confidentiality_'+lang+'.html' for lang in PRIVACY_LANGUAGES]
    privacy.append(SITE+'confidentiality-all.html')
    for url in privacy:
        path = ROOT/url[len(SITE):]
        metadata = Metadata(path.read_text(encoding='utf-8'))
        if metadata.noindex or metadata.canonical != url:
            raise RuntimeError(f'Noncanonical privacy page: {path}')
    root = ET.Element(f'{{{SM_NS}}}urlset')
    alternatives = {'en': SITE}
    alternatives.update({lang: SITE+lang+'/' for lang in LANGUAGES if lang!='en'})
    alternatives['x-default'] = SITE
    for url in home:
        item = ET.SubElement(root, f'{{{SM_NS}}}url')
        child(item, 'loc', url)
        for language, href in alternatives.items():
            ET.SubElement(item, f'{{{XHTML_NS}}}link', {'rel':'alternate','hreflang':language,'href':href})
    policy_alt = {lang:SITE+'Policy-Confidentiality_'+lang+'.html' for lang in PRIVACY_LANGUAGES}
    policy_alt['x-default'] = policy_alt['en']
    for url in privacy:
        item = ET.SubElement(root, f'{{{SM_NS}}}url')
        child(item, 'loc', url)
        if url in policy_alt.values():
            for language, href in policy_alt.items():
                ET.SubElement(item, f'{{{XHTML_NS}}}link', {'rel':'alternate','hreflang':language,'href':href})
    publish(root, 'sitemap-pages.xml')
    for directory in GROUPS:
        pages=canonical_pages(directory)
        if not pages:
            raise RuntimeError(f'No canonical pages found in {directory}')
        make_urlset(pages,directory+'/sitemap.xml')
        print(f'{directory}: {len(pages)} canonical HTML URLs')
    for filename in ('SonoCalming/sitemap.xml','SonoCalming/video-sitemap.xml','SonoCalming/sitemap-languages.xml'):
        if not (ROOT/filename).is_file():
            raise RuntimeError(f'Missing essential video sitemap: {filename}')
    make_index('sitemap-sections.xml',[d+'/sitemap.xml' for d in GROUPS])
    make_index('sitemap.xml',[
        'sitemap-pages.xml',
        *[d+'/sitemap.xml' for d in GROUPS],
        'SonoCalming/sitemap.xml',
        'SonoCalming/video-sitemap.xml',
        'SonoCalming/sitemap-languages.xml',
    ])
    print('Root sitemap index, 8 localized homepages, 15 privacy languages: OK')


if __name__ == '__main__':
    main()
