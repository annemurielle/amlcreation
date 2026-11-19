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


def build_card(video: dict) -> str:
    vid = video["id"]
    title = html.escape(video["title"].strip(), quote=True)
    dt = datetime.fromisoformat(video["publishedAt"].replace("Z", "+00:00"))
    date_iso = dt.date().isoformat()
    date_label = dt.strftime("%d %b %Y").lstrip("0")
    duration = html.escape(str(video.get("durationLabel") or "Long-form ambience"), quote=True)
    video_url = f"SonoCalming/videos/{vid}.html"
    return f'''
          <article class="project-card sonocalming" aria-label="SonoCalming latest long video">
            <a class="image" href="{video_url}" aria-label="Watch the latest SonoCalming video: {title}">
              <img src="https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
                   alt="Thumbnail of {title}" loading="lazy" decoding="async" width="1280" height="720">
            </a>
            <div class="project-card-content">
              <div class="sonocalming-card-heading">
                <h3><a href="SonoCalming/">SonoCalming</a></h3>
                <span class="pill">{duration}</span>
              </div>
              <p class="sonocalming-tagline">Rain sounds, cozy ambience, black screen noise and gentle piano.</p>
              <div class="latest-video">
                <div class="latest-video-label">Latest long video <time datetime="{date_iso}">{date_label}</time></div>
                <a class="latest-video-title" href="{video_url}">{title}</a>
                <a class="latest-video-action" href="{video_url}">Explore this video &#8594;</a>
              </div>
            </div>
          </article>'''


def main() -> None:
    content = HOME.read_text(encoding="utf-8")
    if content.count(MARKER_START) != 1 or content.count(MARKER_END) != 1:
        raise RuntimeError("Homepage markers missing or duplicated; index.html unchanged")
    start = content.index(MARKER_START) + len(MARKER_START)
    end = content.index(MARKER_END)
    if start >= end:
        raise RuntimeError("Homepage marker order is wrong; index.html unchanged")
    video = video_data()
    fresh = content[:start] + "\n" + build_card(video) + "\n          " + content[end:]
    if fresh != content:
        HOME.write_text(fresh, encoding="utf-8")
        print("Updated AML homepage latest SonoCalming card:", video["id"])
    else:
        print("AML homepage latest SonoCalming card already current:", video["id"])


if __name__ == "__main__":
    main()
