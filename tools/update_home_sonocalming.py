#!/usr/bin/env python3
"""Refresh the homepage's SonoCalming card from the existing local YouTube JSON.

This script runs after update_sonocalming_latest.py in the GitHub workflow.
It changes only the marked block in index.html, no network calls or secrets.
The thumbnail and text live in separate stacked sections for readability.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = ROOT / "index.html"
LOCALIZED_HOMES = {lang: ROOT / lang / "index.html" for lang in ("fr", "de", "es", "it", "pt", "ru", "ja")}
LATEST = ROOT / "SonoCalming" / "latest-videos.json"
MARKER_START = "<!-- SONOCALMING_LATEST_START -->"
MARKER_END = "<!-- SONOCALMING_LATEST_END -->"
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")


def video_data() -> dict:
    data = json.loads(LATEST.read_text(encoding="utf-8"))
    entries = data.get("videos") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("latest-videos.json has no videos; keeping the previous card")
    candidates = []
    for video in entries:
        if not isinstance(video, dict):
            continue
        video_id = str(video.get("id", ""))
        title = str(video.get("title", "")).strip()
        published = str(video.get("publishedAt", ""))
        if not VIDEO_ID.fullmatch(video_id) or not title or not published:
            continue
        try:
            parsed = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            continue
        candidates.append((parsed, video))
    if not candidates:
        raise ValueError("No valid video ID/title/date in latest-videos.json")
    return max(candidates, key=lambda item: item[0])[1]


LOCALE_TEXT = {
    "en": ("Rain sounds, cozy ambience, black screen noise and gentle piano.", "Latest long video", "Explore this video →"),
    "fr": ("Pluie, ambiances cosy, écran noir et piano doux.", "Dernière vidéo longue", "Découvrir cette vidéo →"),
    "de": ("Regengeräusche, gemütliche Atmosphäre, schwarzer Bildschirm und sanftes Klavier.", "Neuestes langes Video", "Video entdecken →"),
    "es": ("Lluvia, ambientes acogedores, pantalla negra y piano suave.", "Último vídeo largo", "Ver este vídeo →"),
    "it": ("Pioggia, atmosfere accoglienti, schermo nero e pianoforte delicato.", "Ultimo video lungo", "Guarda questo video →"),
    "pt": ("Chuva, ambientes acolhedores, ecrã preto e piano suave.", "Vídeo longo mais recente", "Ver este vídeo →"),
    "ru": ("Дождь, уютная атмосфера, чёрный экран и мягкое фортепиано.", "Последнее длинное видео", "Смотреть видео →"),
    "ja": ("雨音、居心地のよい環境音、黒画面、やさしいピアノ。", "最新の長時間動画", "この動画を見る →"),
}


def build_card(video: dict, lang: str = "en") -> str:
    vid = video["id"]
    title = html.escape(video["title"].strip(), quote=True)
    dt = datetime.fromisoformat(video["publishedAt"].replace("Z", "+00:00"))
    date_iso = dt.date().isoformat()
    date_label = dt.strftime("%d %b %Y").lstrip("0")
    duration = html.escape(str(video.get("durationLabel") or "Long-form ambience"), quote=True)
    prefix = "../" if lang != "en" else ""
    video_url = f"{prefix}SonoCalming/videos/{vid}.html"
    home_url = prefix + "SonoCalming/"
    tagline, latest_label, action_label = (html.escape(s, quote=True) for s in LOCALE_TEXT[lang])
    if lang == "ja":
        date_label = f"{dt.year}年{dt.month}月{dt.day}日"
    elif lang != "en":
        date_label = dt.strftime("%d/%m/%Y")
    return f'''
          <article class="project-card sonocalming" aria-label="SonoCalming latest long video">
            <a class="image" href="{video_url}" aria-label="Watch the latest SonoCalming video: {title}">
              <img src="https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
                   alt="Thumbnail of {title}" loading="lazy" decoding="async" width="1280" height="720">
            </a>
            <div class="project-card-content">
              <div class="sonocalming-card-heading">
                <h3><a href="{home_url}">SonoCalming</a></h3>
                <span class="pill">{duration}</span>
              </div>
              <p class="sonocalming-tagline">{tagline}</p>
              <div class="latest-video">
                <div class="latest-video-label">{latest_label} <time datetime="{date_iso}">{date_label}</time></div>
                <a class="latest-video-title" href="{video_url}">{title}</a>
                <a class="latest-video-action" href="{video_url}">{action_label}</a>
              </div>
            </div>
          </article>'''


def main() -> None:
    video = video_data()
    # Validate every page before writing any of them to avoid partial updates.
    updates = {}
    for lang, path in (("en", HOME), *LOCALIZED_HOMES.items()):
        if not path.is_file():
            raise FileNotFoundError(f"Missing localized homepage: {path}")
        content = path.read_text(encoding="utf-8")
        if content.count(MARKER_START) != 1 or content.count(MARKER_END) != 1:
            raise RuntimeError(f"Homepage markers missing or duplicated: {path}")
        start = content.index(MARKER_START) + len(MARKER_START)
        end = content.index(MARKER_END)
        if start >= end:
            raise RuntimeError(f"Homepage marker order is invalid: {path}")
        fresh = content[:start] + "\n" + build_card(video, lang) + "\n          " + content[end:]
        if fresh != content:
            updates[path] = fresh
    for path, data in updates.items():
        path.write_text(data, encoding="utf-8")
    print(f"AML homepage SonoCalming latest {video['id']}: {len(updates)} language page(s) updated")


if __name__ == "__main__":
    main()
