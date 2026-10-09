SONOCALMING WEBSITE | COMPLETE VIDEO CATALOGUE
Version 2026-10-09
=============================================

PUBLIC WEBSITE
https://www.amlcreation.ch/SonoCalming/

THIS VERSION INCLUDES
- 321 real, public SonoCalming YouTube videos (metadata read from the channel on 2026-10-09)
- One individual crawlable HTML watch page for every video: SonoCalming/videos/VIDEO_ID.html
- Full HTML catalogue: https://www.amlcreation.ch/SonoCalming/videos.html
- 321 click-to-play YouTube previews in the catalogue, searchable/filterable by title,
  category, year and video/Shorts. Thumbnail images use lazy loading.
- One genuine YouTube iframe on every dedicated video page, plus source link.
- Unique title, description, canonical, Open Graph and Twitter preview on each page.
- VideoObject and BreadcrumbList structured data on every individual video page.
- Correct sitemap index with a 331-URL page sitemap and a 321-video sitemap.
- 6 original main sound families in the existing navigation, plus All Videos.
- Link paths checked within the SonoCalming folder.

DEPLOY
Copy/replace the ENTIRE SonoCalming directory in your existing local repository:
/Users/largeram/_amlCreationGitHub/amlcreation/SonoCalming/

After you have placed the files yourself, use Git as usual:

cd "/Users/largeram/_amlCreationGitHub/amlcreation"
git add SonoCalming
git commit -m "Expand SonoCalming SEO library with 321 YouTube video pages"
BRANCH=$(git branch --show-current)
git pull --rebase origin "$BRANCH"
git push origin "$BRANCH"

BEWARE
A link to ../Somnifox/hero.jpg is intentionally kept in the home page,
matching the existing AML Creation repository. The file is located in the
sibling Somnifox folder, not within the SonoCalming ZIP. The public image
was checked at https://www.amlcreation.ch/Somnifox/hero.jpg.

SITEMAPS
Submit just this sitemap index in both Google Search Console and Bing:
https://www.amlcreation.ch/SonoCalming/sitemap-index.xml

This index includes BOTH:
https://www.amlcreation.ch/SonoCalming/sitemap.xml
https://www.amlcreation.ch/SonoCalming/video-sitemap.xml

robots.txt exists only at the website domain ROOT, not in SonoCalming.
Merge ROOT_ROBOTS_SNIPPET.txt into the root robots.txt if it isn't already there.

CONTENT & SEARCH GUIDANCE
- Music is not attributed to the channel owner as composer.
- A video sitemap must not have <video:duration> values above 28800 seconds;
  those values are omitted for long uploads. Exact duration remains in VideoObject.
- Videos are linked to their official YouTube upload IDs, not inferred IDs.
- The video list is a snapshot, new future videos need to be added to videos.tsv.
- On Google, discovery and indexing are not guaranteed: submit sitemap and
  monitor Video Indexing and Pages reports after deployment.

LOCALLY TEST
cd "/Users/largeram/_amlCreationGitHub/amlcreation/SonoCalming"
python3 -m http.server 8080

Open http://localhost:8080/ in a browser. YouTube embeds may report error 153
when testing pages through file:// instead of an HTTP/HTTPS site.

Future catalogue regeneration (optional)
The _maintenance directory includes build_sonocalming.py and videos.tsv.
For a new public video, add a TSV row with ID, date, ISO duration and title,
then run: python3 _maintenance/build_sonocalming.py
Python with beautifulsoup4 is required for this optional maintenance script.

EXTERNAL LINKS
YouTube videos are taken from the channel's own public video listing.
Known playlist URLs were retained from the previous version; not every playlist
could be verified remotely here. Entries with unknown playlist IDs still send
visitors to the channel's Playlists tab rather than inventing a URL.
