#!/usr/bin/env python3
"""Refresh the latest four >= 60-minute public SonoCalming uploads using the YouTube Data API.

The API key is read only from the YOUTUBE_API_KEY environment variable.
The generated JSON is safe to publish on a static website and contains no secrets.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CHANNEL_ID = "UCGXypunMB75x599kvbSAuqw"
UPLOADS_PLAYLIST = "UU" + CHANNEL_ID[2:]
OUTFILE = Path(__file__).resolve().parents[1] / "SonoCalming" / "latest-videos.json"
API_ROOT = "https://www.googleapis.com/youtube/v3/"
DURATION_RE = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
MINIMUM_DURATION = 60 * 60  # Shorts and short videos are NEVER included.
MAX_RESULTS = 4


def youtube_api(endpoint: str, api_key: str, **params: str | int) -> dict:
    query = urlencode({**params, "key": api_key})
    request = Request(
        f"{API_ROOT}{endpoint}?{query}",
        headers={"Accept": "application/json", "User-Agent": "SonoCalming-site-updater/1.0"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        # Prevent URL + secret API key from appearing in error logs.
        try:
            payload = json.loads(exc.read().decode("utf-8", errors="replace"))
            detail = payload.get("error", {}).get("message", "API request unsuccessful")
        except (ValueError, AttributeError):
            detail = "API request unsuccessful"
        raise RuntimeError(f"YouTube API error ({exc.code}): {detail}") from None
    except URLError as exc:
        raise RuntimeError(f"Network error accessing YouTube API: {exc.reason}") from None


def duration_seconds(value: str) -> int:
    match = DURATION_RE.fullmatch(value or "")
    if not match:
        return 0
    d, h, m, s = (int(part or 0) for part in match.groups())
    return d * 86400 + h * 3600 + m * 60 + s


def duration_label(seconds: int) -> str:
    h, remaining = divmod(seconds, 3600)
    m = remaining // 60
    return f"{h} hr" if not m else f"{h} hr {m} min"


def condensed_description(value: str) -> str:
    """Preserve useful original YouTube description, drop links/hashtag-only lines."""
    output = []
    for line in (value or "").splitlines():
        line = line.strip()
        if not line or line.startswith(("http://", "https://", "#", "▶", "🔔")):
            continue
        if re.match(r"^(?:subscribe|follow me|find me on|watch more)\b", line, re.I):
            continue
        output.append(line)
        if len(" ".join(output)) >= 480:
            break
    text = re.sub(r"\s+", " ", " ".join(output)).strip()
    if len(text) <= 480:
        return text
    return text[:479].rsplit(" ", 1)[0] + "…"


def normalize_video(video: dict) -> dict | None:
    video_id = video.get("id")
    if not isinstance(video_id, str) or not ID_RE.fullmatch(video_id):
        return None
    status = video.get("status", {})
    if status.get("privacyStatus") != "public":
        return None
    snippet = video.get("snippet", {})
    if snippet.get("channelId") != CHANNEL_ID:
        return None
    title = snippet.get("title", "").strip()
    published = snippet.get("publishedAt", "")
    if not title or not published:
        return None
    try:
        timestamp = datetime.fromisoformat(published.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timestamp > datetime.now(timezone.utc):
        return None
    seconds = duration_seconds(video.get("contentDetails", {}).get("duration", ""))
    if seconds < MINIMUM_DURATION:
        return None
    return {
        "id": video_id,
        "title": title,
        "description": condensed_description(snippet.get("description", "")),
        "publishedAt": published,
        "durationSeconds": seconds,
        "durationLabel": duration_label(seconds),
    }


def fetch_latest(api_key: str) -> list[dict]:
    selected: list[dict] = []
    seen: set[str] = set()
    next_page = ""
    # Search recent uploads, even when many recent uploads happen to be Shorts.
    for _ in range(4):
        params: dict[str, str | int] = {
            "part": "contentDetails",
            "playlistId": UPLOADS_PLAYLIST,
            "maxResults": 50,
        }
        if next_page:
            params["pageToken"] = next_page
        page = youtube_api("playlistItems", api_key, **params)
        ids = []
        for item in page.get("items", []):
            video_id = item.get("contentDetails", {}).get("videoId")
            if video_id and ID_RE.fullmatch(video_id) and video_id not in seen:
                ids.append(video_id)
                seen.add(video_id)
        if ids:
            videos_data = youtube_api("videos", api_key, part="snippet,contentDetails,status", id=",".join(ids))
            selected.extend(filter(None, (normalize_video(v) for v in videos_data.get("items", []))))
            selected.sort(key=lambda v: v["publishedAt"], reverse=True)
            if len(selected) >= MAX_RESULTS:
                break
        next_page = page.get("nextPageToken") or ""
        if not next_page:
            break
    # An error must not overwrite the previously working feed with zero videos.
    if len(selected) < MAX_RESULTS:
        raise RuntimeError(f"Found only {len(selected)} eligible public long videos among recent uploads; previous feed preserved")
    return selected[:MAX_RESULTS]


def main() -> int:
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("Missing secret YOUTUBE_API_KEY: configure it in GitHub Actions secrets.", file=sys.stderr)
        return 2
    try:
        videos = fetch_latest(api_key)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {"videos": videos}
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    previous = OUTFILE.read_text(encoding="utf-8") if OUTFILE.exists() else None
    if previous == data:
        print("No changes to the 4 latest long videos.")
        return 0
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(data, encoding="utf-8")
    print("Updated latest-videos.json for IDs:", ", ".join(v["id"] for v in videos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
