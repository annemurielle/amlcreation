#!/usr/bin/env python3
"""Safely merge video publication timestamp fix with current AML Creation scripts.

Does not overwrite scripts or HTML with an older copy. Safe to rerun.
"""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
GENERATOR = SITE / 'tools/update_sonocalming_catalogue.py'
WORKFLOW = SITE / '.github/workflows/sonocalming-latest.yml'


def new_source_generator(source: str) -> str:
    old = "'uploadDate':v['date']"
    new = "'uploadDate':v['publishedAt']"
    if old in source:
        source = source.replace(old, new)
    elif new not in source:
        raise RuntimeError('Catalogue generator uploadDate layout changed; manual review required')
    old_records = "('id','title','date','duration','cat','short')"
    new_records = "('id','title','date','publishedAt','duration','cat','short')"
    if old_records in source:
        source = source.replace(old_records, new_records)
    elif new_records not in source:
        raise RuntimeError('Catalogue generator new-record layout changed; manual review required')
    return source


def new_source_workflow(source: str) -> str:
    if 'run: python3 tools/fix_video_upload_dates.py' not in source:
        # Run *after* SEO so later JSON-LD rewrites never reintroduce date-only fields.
        anchors = [
            '      - name: Rebuild SonoCalming galleries in all 8 languages',
            '      - name: Refresh AML Creation homepage latest SonoCalming card',
            '      - name: Commit only changed SonoCalming files',
        ]
        anchor = next((a for a in anchors if a in source), None)
        if not anchor:
            raise RuntimeError('Workflow structure changed; manual review required')
        step = '''      - name: Correct VideoObject uploadDate using YouTube publication times
        env:
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
        run: python3 tools/fix_video_upload_dates.py

'''
        source = source.replace(anchor, step + anchor, 1)
    # Existing workflows stage SonoCalming/ but older ones stage only selected files.
    # Explicitly stage the verified timestamp cache without staging user backups.
    stage_anchor = '          if git diff --cached --quiet; then'
    if '          git add SonoCalming/video-upload-dates.json\n' not in source:
        if stage_anchor not in source:
            raise RuntimeError('Workflow staging layout changed; manual review required')
        source = source.replace(stage_anchor,
            '          git add SonoCalming/video-upload-dates.json\n' + stage_anchor, 1)
    return source


def main() -> None:
    if not GENERATOR.is_file() or not WORKFLOW.is_file():
        raise RuntimeError('Missing original catalogue script or SonoCalming workflow')
    # Validate BOTH changes before writing either file.
    original_gen = GENERATOR.read_text(encoding='utf-8')
    original_wf = WORKFLOW.read_text(encoding='utf-8')
    updated_gen = new_source_generator(original_gen)
    updated_wf = new_source_workflow(original_wf)
    for path, before, after in [(GENERATOR, original_gen, updated_gen),
                                (WORKFLOW, original_wf, updated_wf)]:
        if before != after:
            path.write_text(after, encoding='utf-8')
            print('Updated:', path.relative_to(SITE))
        else:
            print('Already correct:', path.relative_to(SITE))
    print('No privacy, support, game, or sitemap URL changed.')


if __name__ == '__main__':
    main()
