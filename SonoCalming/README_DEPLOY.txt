SONOCALMING WEBSITE
===================
Target: https://www.amlcreation.ch/SonoCalming/

Copy the whole SonoCalming folder into:
/Users/largeram/_amlCreationGitHub/amlcreation/SonoCalming/

This version intentionally uses a darker media-first design than Somnifox. Somnifox is an app/product page, while SonoCalming is designed to push visitors quickly into long YouTube videos and playlists. The AML Creation family link remains in the footer and Somnifox is cross-linked.

SEO INCLUDED
- Focused landing pages for Rain, Japanese Bedroom, Black Screen and Rain + Piano
- Canonical URLs
- Meta descriptions
- Open Graph / Twitter previews
- Mobile responsive design
- Fast, dependency-free CSS/JS
- Standard sitemap.xml
- video-sitemap.xml for two verified recent videos
- Search Console and Bing verification placeholders in every HTML head
- No obsolete meta-keywords tag

WATCH-TIME DESIGN
- Featured 10-hour video above the fold
- Latest uploads player uses the automatic YouTube uploads playlist: UUGXypunMB75x599kvbSAuqw
- Black Screen page embeds the existing playlist: PLIAi4NigujQQ
- rel=0 keeps YouTube related recommendations constrained to the same channel context
- No autoplay, visitors choose to start playback

IMPORTANT
The Japanese Bedroom page currently uses video IDs xYtLErFwPuU and KgzJV9ef6_Y, because these were the two Japanese Bedroom videos present in the supplied channel analysis. If you want different episodes featured, replace only those IDs in japanese-bedroom.html and rain-sounds.html.

SEARCH CONSOLE / BING
Submit:
https://www.amlcreation.ch/SonoCalming/sitemap.xml
https://www.amlcreation.ch/SonoCalming/video-sitemap.xml

robots.txt works only at the DOMAIN ROOT. Merge the content of ROOT_ROBOTS_SNIPPET.txt into https://www.amlcreation.ch/robots.txt, do not upload it as /SonoCalming/robots.txt.

GIT AFTER COPYING
cd "/Users/largeram/_amlCreationGitHub/amlcreation"
git add -A
git commit -m "Add SonoCalming website"
BRANCH=$(git branch --show-current)
git pull --rebase origin "$BRANCH"
git push origin "$BRANCH"

LOCAL TESTING AND YOUTUBE ERROR 153
-----------------------------------
Do not judge YouTube embeds by double-clicking index.html as a file:// URL.
YouTube error 153 means the player did not receive an HTTP Referer or equivalent client identity.

Test the site through a small local HTTP server instead:

cd "/Users/largeram/_amlCreationGitHub/amlcreation/SonoCalming"
python3 -m http.server 8080

Then open:
http://localhost:8080/

The deployed HTTPS site should provide a normal Referer automatically.
The pages also declare strict-origin-when-cross-origin, the policy recommended by YouTube for embedded players.

WATCH-TIME STRATEGY
-------------------
The site cannot guarantee watch hours. It is designed to improve the chance of long sessions by:
- putting a 10-hour video above the fold
- prioritizing long-form videos instead of the automatic uploads feed
- using rel=0 so related videos shown after playback come from SonoCalming
- grouping visitors by strong intent pages: Rain, Japanese Bedroom, Black Screen, Rain + Piano
- linking directly to the full YouTube videos and relevant playlists
- keeping short art content out of the main long-form funnel

SEO NOTE FOR 10-HOUR VIDEOS
----------------------------
Google's VideoObject structured data can use ISO 8601 duration such as PT10H.
However, the optional <video:duration> field in a video sitemap accepts a maximum of 28,800 seconds (8 hours).
For the 10-hour videos in video-sitemap.xml, the duration field is therefore intentionally omitted.


V3 PLAYLIST + SEO UPDATE
------------------------
New public page:
https://www.amlcreation.ch/SonoCalming/playlists.html

New sitemap index:
https://www.amlcreation.ch/SonoCalming/sitemap-index.xml

Recommended submission in Google Search Console AND Bing Webmaster Tools:
https://www.amlcreation.ch/SonoCalming/sitemap-index.xml

The sitemap index references the normal page sitemap and the video sitemap.

The homepage now links prominently to playlists, and category pages cross-link to the playlist directory.
This is intended to send visitors into longer, related listening sessions rather than leaving them on a single isolated video.

See PLAYLISTS_AND_SEO.txt for direct playlist IDs and the newer playlist IDs that still need exact URLs if you want every card to open a specific YouTube playlist.


V5 NAVIGATION
-------------
Rain | Black Screen | Music + Nature | Relaxing Music | Playlists | About

New pages:
https://www.amlcreation.ch/SonoCalming/music-nature.html
https://www.amlcreation.ch/SonoCalming/music.html

Japanese Bedroom and Rain + Piano remain indexable child pages but are no longer separate top-menu items.

Submit:
https://www.amlcreation.ch/SonoCalming/sitemap-index.xml

V6 CONTENT CLEANUP
------------------
- Final menu: Rain | Black Screen | Music + Nature | Relaxing Music | Playlists | About
- Visitor-facing copy no longer discusses site navigation, indexing or search-engine organization.
- Each main family page uses one video preview only. Secondary playlists and subformats use text cards or buttons.
- Music + Nature features the older Rain & Piano Relaxation video fDHU56MFMdo to avoid repeating the homepage Rain + Piano feature.
- Homepage Somnifox cross-promotion now uses ../Somnifox/hero.jpg and links to both the App Store and the Somnifox website.
