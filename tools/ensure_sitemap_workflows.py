#!/usr/bin/env python3
"""Safely merge sitemap refresh into the two EXISTING GitHub Pages workflows.

Do not replace complete workflow files from an archive. Verify both workflow
patterns before writing, so local customizations and timings are preserved.
This patch is idempotent and does not alter any privacy or marketing URL.
"""
from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/'.github/workflows'
UPDATES={}


def sono(path:Path)->str:
    original=path.read_text('utf-8');out=original
    marker='      - name: Commit only changed SonoCalming files'
    if marker not in out:raise RuntimeError(f'Unexpected SonoCalming workflow; no files changed: {path}')
    if '- name: Refresh global canonical and language sitemaps' not in out:
        out=out.replace(marker,'      - name: Refresh global canonical and language sitemaps\n        run: python3 tools/update_sitemaps.py\n\n'+marker,1)
    old='git add index.html fr/index.html'
    new='git add sitemap.xml sitemap-pages.xml sitemap-sections.xml Games/sitemap.xml lumenmine/sitemap.xml \\\n            Somnifox/sitemap.xml MahjongCastle/sitemap.xml ZenCircle/sitemap.xml \\\n            index.html fr/index.html'
    if old in out:
        out=out.replace(old,new,1)
    elif 'git add sitemap.xml sitemap-pages.xml sitemap-sections.xml Games/sitemap.xml' not in out:
        raise RuntimeError(f'Unexpected staging command in SonoCalming workflow: {path}')
    return out


def stores(path:Path)->str:
    original=path.read_text('utf-8');out=original
    marker='      - name: Save refreshed information'
    if marker not in out:raise RuntimeError(f'Unexpected Games workflow; no files changed: {path}')
    if '- name: Rebuild XML sitemaps from canonical site pages' not in out:
        out=out.replace(marker,'      - name: Rebuild XML sitemaps from canonical site pages\n        run: python3 tools/update_sitemaps.py\n'+marker,1)
    old='git add Games/store-data.json Games/*.html'
    new='git add Games/store-data.json Games/*.html sitemap.xml sitemap-pages.xml sitemap-sections.xml \\\n            Games/sitemap.xml lumenmine/sitemap.xml Somnifox/sitemap.xml \\\n            MahjongCastle/sitemap.xml ZenCircle/sitemap.xml'
    if 'git add Games/store-data.json Games/*.html sitemap.xml sitemap-pages.xml' in out:
        pass  # Already patched; avoid replacing a prefix of the new command.
    elif old in out:
        out=out.replace(old,new,1)
    else:
        raise RuntimeError(f'Unexpected staging command in Games workflow: {path}')
    return out


def main()->None:
    targets=(WORKFLOWS/'sonocalming-latest.yml',WORKFLOWS/'update-game-stats.yml')
    if not all(path.is_file() for path in targets):
        raise RuntimeError('Missing a required workflow, no workflow was changed')
    updates={targets[0]:sono(targets[0]), targets[1]:stores(targets[1])}
    changed=0
    for path,content in updates.items():
        if path.read_text('utf-8') != content:
            path.write_text(content,encoding='utf-8');changed+=1
    print(f'Sitemap refresh in GitHub workflows: {changed} file(s) changed')

if __name__=='__main__':
    main()
