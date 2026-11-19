#!/usr/bin/env python3
"""Fix return-to-AML Creation links according to each page's existing language.

Conservative in-place update of currently installed HTML, preserving local edits,
store ratings, the full design, YouTube content, and all existing public URLs.
No network calls, no extra Python dependencies; safe to run repeatedly.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {'fr','de','es','it','pt','ru','ja'}
LANG_RE = re.compile(r'<html\b[^>]*\blang\s*=\s*["\']([^"\']+)',re.I)
BACK_RE = re.compile(r'(<a\b[^>]*\bhref=)(["\'])\.\./\2([^>]*>\s*AML Creation(?:\s*↗)?\s*</a>)',re.I)


def lang_of(text: str, path: Path) -> str:
    match = LANG_RE.search(text)
    if not match:raise RuntimeError(f'Missing HTML language: {path}')
    return match.group(1).lower().split('-')[0]


def home(lang: str, prefix: str = '../') -> str:
    return prefix + (lang+'/' if lang in SUPPORTED else '')


def main() -> None:
    changes: dict[Path, str] = {}
    totals = {}

    n = 0
    for path in sorted((ROOT/'Games').glob('*.html')):
        old=path.read_text(encoding='utf-8')
        lang=lang_of(old,path)
        # Match only anchors explicitly labelled AML Creation, never game-card links.
        new,_=BACK_RE.subn(lambda m:m.group(1)+m.group(2)+home(lang)+m.group(2)+m.group(3),old)
        if new != old:
            changes[path]=new;n+=1
    totals['Games']=n

    n = 0
    for path in sorted((ROOT/'lumenmine').rglob('*.html')):
        old=path.read_text(encoding='utf-8')
        lang=lang_of(old,path)
        destination='https://www.amlcreation.ch/'+(lang+'/' if lang in SUPPORTED else '')
        # Only the existing AML Creation copyright footer link.
        pattern=r'(<a\s+href=["\'])https://www\.amlcreation\.ch/(?:fr/|de/|es/|it/|pt/|ru/|ja/)?(["\']>\s*©\s*2026 AML Creation\s*</a>)'
        new,count=re.subn(pattern,lambda m:m.group(1)+destination+m.group(2),old)
        if count!=1:raise RuntimeError(f'Expected exactly one AML copyright footer: {path}')
        if new != old:
            changes[path]=new;n+=1
    totals['Lumen Mine']=n

    for section in ('Somnifox','ZenCircle'):
        n=0
        for path in sorted((ROOT/section).glob('*.html')):
            if not path.name.startswith(('marketing_','support_')):continue
            old=path.read_text(encoding='utf-8')
            lang=lang_of(old,path)
            route=home(lang)
            marker='class="aml-creation-return"'
            if marker in old:
                # Update an earlier run's link if a page language was corrected later.
                pattern=r'(<p\s+class="aml-creation-return"[^>]*>\s*<a\s+href=")[^"]+("[^>]*>AML Creation ↗</a>\s*</p>)'
                new,count=re.subn(pattern,lambda m:m.group(1)+route+m.group(2),old)
                if count!=1:raise RuntimeError(f'Unrecognised existing return link: {path}')
            else:
                end=old.rfind('</footer>')
                if end<0:raise RuntimeError(f'Missing footer: {path}')
                marker_line=f'      <p class="aml-creation-return" style="margin-top:8px"><a href="{route}">AML Creation ↗</a></p>\n'
                new=old[:end]+marker_line+old[end:]
            if new != old:
                changes[path]=new;n+=1
        totals[section]=n
    for path,content in changes.items():
        path.write_text(content,encoding='utf-8')
    print('Localized AML Creation return links: '+', '.join(f'{name} {count}' for name,count in totals.items()))


if __name__=='__main__':
    main()
