#!/usr/bin/env python3
"""Build SonoCalming's 8-language, thumbnail-first, static video galleries.

Runs offline after the YouTube catalogue refresh, with no AI, translation API,
API key or new network dependency. Video detail pages remain English only.
Never removes/renames legacy pages, app-support, privacy or download URLs.
Idempotent, including sitemaps and cross-site language links.
"""
from __future__ import annotations

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONO = ROOT / 'SonoCalming'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sono_gallery_translations import PAGE, LANG_NAMES  # noqa: E402

BASE = 'https://www.amlcreation.ch/SonoCalming/'
LOCALES = ('en','fr','de','es','it','pt','ru','ja')
CATS = (
    ('rain-sounds.html', '🌧️', 'Rain Sounds'),
    ('japanese-bedroom.html', '🏮', 'Japanese Bedroom'),
    ('black-screen.html', '⬛', 'Black Screen'),
    ('cozy-ambience.html', '🔥', 'Cozy Ambience'),
    ('music.html', '🎹', 'Relaxing Music'),
    ('music-nature.html', '🌿', 'Music & Nature'),
    ('rain-piano.html', '🌧️', 'Rain & Piano'),
    ('nature-sounds.html', '🌲', 'Nature Sounds'),
    ('blue-room.html', '🛋️', 'Blue Room'),
    ('noise-household.html', '🌙', 'Noise & Household'),
)
CATMAP = {f:(emoji, name) for f, emoji, name in CATS}
NEW_EN = {'cozy-ambience.html','nature-sounds.html','blue-room.html','noise-household.html'}
CURRENT_EN = set(CATMAP) - NEW_EN
LANG_START = '<!-- SONO GALLERY LANG START -->'
LANG_END = '<!-- SONO GALLERY LANG END -->'
GALLERY_START = '<!-- SONO GALLERY START -->'
GALLERY_END = '<!-- SONO GALLERY END -->'
HOME_START = '<!-- SONO GALLERY HOME START -->'
HOME_END = '<!-- SONO GALLERY HOME END -->'
SM = 'http://www.sitemaps.org/schemas/sitemap/0.9'
XHTML = 'http://www.w3.org/1999/xhtml'
ET.register_namespace('', SM)
ET.register_namespace('xhtml', XHTML)
VIDEO_ID = re.compile(r'^[\w-]{11}$', re.ASCII)

EXTRA = {
'en': {
'cozy-ambience.html': ('Cozy Rain & Fireplace Ambience Videos', 'Explore long fireplace sounds, cozy rain on windows and gentle indoor ambience. Choose a scene from the video gallery and play it here or on YouTube.'),
'nature-sounds.html': ('Forest, River, Ocean & Nature Sounds', 'Browse forest ambience, birds, gentle streams, ocean waves and other nature sounds from SonoCalming.'),
'blue-room.html': ('Cozy Blue Room & Household Sounds', 'Explore blue-room ambience, gentle appliances, fan sounds and rain heard from cozy indoor spaces.'),
'noise-household.html': ('Steady Noise & Household Ambience', 'Browse white, pink and brown noise, soft household sounds and other continuous audio videos.'),
},
'fr': {
'cozy-ambience.html': ('Pluie et cheminée : ambiances cosy', 'Explorez les longues vidéos de cheminée, de pluie sur les fenêtres et d’ambiances chaleureuses à l’intérieur.'),
'nature-sounds.html': ('Sons de la nature : forêt, rivière et océan', 'Découvrez les ambiances de forêt, les oiseaux, les cours d’eau et les vagues dans les vidéos SonoCalming.'),
'blue-room.html': ('Ambiances intérieures et chambre bleue', 'Explorez les sons de ventilateur, de pluie derrière la fenêtre et les bruits doux des pièces intérieures.'),
'noise-household.html': ('Bruits constants et sons de la maison', 'Découvrez les bruits blanc, rose et brun, les sons continus et les ambiances domestiques.'),
},
'de': {
'cozy-ambience.html': ('Gemütlicher Regen und Kaminfeuer', 'Entdecken Sie lange Videos mit Kaminfeuer, Regen am Fenster und ruhiger Wohnatmosphäre.'),
'nature-sounds.html': ('Naturgeräusche aus Wald, Fluss und Meer', 'Entdecken Sie Waldatmosphäre, Vogelstimmen, fließendes Wasser und Meereswellen.'),
'blue-room.html': ('Gemütliche Zimmer- und Haushaltsgeräusche', 'Hören Sie Ventilatoren, Regen am Fenster und gleichmäßige Geräusche aus Innenräumen.'),
'noise-household.html': ('Gleichmäßiges Rauschen und Haushaltsgeräusche', 'Finden Sie weißes, rosa und braunes Rauschen sowie gleichmäßige Alltagsgeräusche.'),
},
'es': {
'cozy-ambience.html': ('Lluvia acogedora y sonidos de chimenea', 'Explora vídeos largos de chimeneas, lluvia en las ventanas y ambientes cálidos de interior.'),
'nature-sounds.html': ('Sonidos de la naturaleza: bosque, río y mar', 'Encuentra ambientes de bosque, aves, agua corriente y olas del mar.'),
'blue-room.html': ('Ambientes interiores y habitaciones acogedoras', 'Escucha ventiladores, lluvia en las ventanas y suaves sonidos de espacios interiores.'),
'noise-household.html': ('Ruidos constantes y sonidos domésticos', 'Explora ruido blanco, rosa y marrón, sonidos continuos y ambientes domésticos.'),
},
'it': {
'cozy-ambience.html': ('Pioggia accogliente e suoni del camino', 'Esplora video lunghi con camini, pioggia alle finestre e atmosfere calde negli interni.'),
'nature-sounds.html': ('Suoni della natura: bosco, fiume e mare', 'Scopri atmosfere del bosco, canto degli uccelli, ruscelli e onde del mare.'),
'blue-room.html': ('Ambienti interni e stanze accoglienti', 'Ascolta ventilatori, pioggia alle finestre e suoni delicati degli spazi interni.'),
'noise-household.html': ('Rumori costanti e suoni domestici', 'Scopri rumore bianco, rosa e marrone e suoni continui dell’ambiente domestico.'),
},
'pt': {
'cozy-ambience.html': ('Chuva acolhedora e sons de lareira', 'Explore vídeos longos com lareira, chuva nas janelas e ambientes acolhedores dentro de casa.'),
'nature-sounds.html': ('Sons da natureza: floresta, rio e oceano', 'Descubra ambientes de floresta, pássaros, água corrente e ondas do mar.'),
'blue-room.html': ('Ambientes interiores e quartos acolhedores', 'Ouça ventoinhas, chuva nas janelas e sons suaves de espaços interiores.'),
'noise-household.html': ('Ruídos constantes e sons domésticos', 'Explore ruído branco, rosa e castanho, sons contínuos e ambientes domésticos.'),
},
'ru': {
'cozy-ambience.html': ('Уютный дождь и звуки камина', 'Смотрите длинные видео с камином, дождём за окном и уютной атмосферой помещений.'),
'nature-sounds.html': ('Звуки природы: лес, река и море', 'Слушайте атмосферу леса, пение птиц, журчание воды и морские волны.'),
'blue-room.html': ('Уютные комнаты и домашние звуки', 'Откройте для себя звуки вентилятора, дождя за окном и спокойную домашнюю атмосферу.'),
'noise-household.html': ('Ровный шум и домашние звуки', 'Слушайте белый, розовый и коричневый шум, постоянные звуки и домашнюю атмосферу.'),
},
'ja': {
'cozy-ambience.html': ('心地よい雨音と暖炉の環境音', '暖炉の音、窓に降る雨、温かな室内の雰囲気を楽しめる長時間動画を集めました。'),
'nature-sounds.html': ('森・川・海の自然音', '森の環境音、鳥の声、流れる水、波の音を集めたSonoCalmingの動画です。'),
'blue-room.html': ('居心地のよい室内と生活音', '扇風機、窓の雨音、落ち着いた部屋の環境音を楽しめます。'),
'noise-household.html': ('一定のノイズと生活音', 'ホワイトノイズ、ピンクノイズ、ブラウンノイズなど、一定の音を集めました。'),
}}

UI = {
'en': dict(home='Home', rain='Rain', black='Black Screen', japanese='Japanese Bedroom', cozy='Cozy Ambience', music='Music', nature='Nature', other='More collections', youtube='Watch on YouTube', play='Play here', details='Video details (English)', video='videos', long='long videos', intro='Choose a thumbnail to start the official YouTube player here, or watch on YouTube.', series='Explore more sound collections', latest='Recently published long videos', visit='Visit the gallery', all='Complete English video library', subscribe='Subscribe', more='Explore galleries', prefix='Video preview:', today='Long-form sounds and gentle music'),
'fr': dict(home='Accueil', rain='Pluie', black='Écran noir', japanese='Chambre japonaise', cozy='Ambiance cosy', music='Musique', nature='Nature', other='Autres ambiances', youtube='Voir sur YouTube', play='Lire ici', details='Fiche vidéo (anglais)', video='vidéos', long='vidéos longues', intro='Choisissez une miniature pour lancer le lecteur officiel YouTube ici ou ouvrir la vidéo sur YouTube.', series='Explorer les autres ambiances', latest='Dernières vidéos longues', visit='Voir la galerie', all='Vidéothèque complète en anglais', subscribe='S’abonner', more='Explorer les galeries', prefix='Aperçu vidéo :', today='Sons de pluie et musique douce'),
'de': dict(home='Startseite', rain='Regen', black='Schwarzer Bildschirm', japanese='Japanisches Schlafzimmer', cozy='Gemütliche Atmosphäre', music='Musik', nature='Natur', other='Weitere Klänge', youtube='Auf YouTube ansehen', play='Hier abspielen', details='Videoseite (Englisch)', video='Videos', long='lange Videos', intro='Wählen Sie ein Vorschaubild, um den offiziellen YouTube-Player zu starten oder das Video auf YouTube anzusehen.', series='Weitere Klangwelten entdecken', latest='Neueste lange Videos', visit='Galerie ansehen', all='Vollständige Videothek (Englisch)', subscribe='Abonnieren', more='Galerien entdecken', prefix='Videovorschau:', today='Regengeräusche und sanfte Musik'),
'es': dict(home='Inicio', rain='Lluvia', black='Pantalla negra', japanese='Dormitorio japonés', cozy='Ambiente acogedor', music='Música', nature='Naturaleza', other='Más ambientes', youtube='Ver en YouTube', play='Reproducir aquí', details='Ficha del vídeo (inglés)', video='vídeos', long='vídeos largos', intro='Elige una miniatura para iniciar el reproductor oficial de YouTube aquí o ver el vídeo en YouTube.', series='Descubre más ambientes', latest='Últimos vídeos largos', visit='Ver galería', all='Biblioteca completa en inglés', subscribe='Suscribirse', more='Explorar galerías', prefix='Vista previa:', today='Sonidos de lluvia y música suave'),
'it': dict(home='Home', rain='Pioggia', black='Schermo nero', japanese='Camera giapponese', cozy='Atmosfera accogliente', music='Musica', nature='Natura', other='Altri ambienti', youtube='Guarda su YouTube', play='Riproduci qui', details='Scheda video (inglese)', video='video', long='video lunghi', intro='Scegli una miniatura per avviare qui il lettore ufficiale di YouTube o guardare il video su YouTube.', series='Scopri altre atmosfere', latest='Ultimi video lunghi', visit='Apri la galleria', all='Catalogo completo in inglese', subscribe='Iscriviti', more='Esplora le gallerie', prefix='Anteprima:', today='Suoni di pioggia e musica delicata'),
'pt': dict(home='Início', rain='Chuva', black='Ecrã preto', japanese='Quarto japonês', cozy='Ambiente acolhedor', music='Música', nature='Natureza', other='Outros ambientes', youtube='Ver no YouTube', play='Reproduzir aqui', details='Página do vídeo (inglês)', video='vídeos', long='vídeos longos', intro='Escolha uma miniatura para iniciar aqui o leitor oficial do YouTube ou ver o vídeo no YouTube.', series='Explorar outros ambientes', latest='Vídeos longos mais recentes', visit='Ver galeria', all='Biblioteca completa em inglês', subscribe='Subscrever', more='Explorar galerias', prefix='Pré-visualização:', today='Sons de chuva e música suave'),
'ru': dict(home='Главная', rain='Дождь', black='Чёрный экран', japanese='Японская спальня', cozy='Уютная атмосфера', music='Музыка', nature='Природа', other='Другие звуки', youtube='Смотреть на YouTube', play='Смотреть здесь', details='Страница видео (англ.)', video='видео', long='длинных видео', intro='Выберите обложку, чтобы запустить официальный проигрыватель YouTube здесь или открыть видео на YouTube.', series='Другие звуковые коллекции', latest='Новые длинные видео', visit='Открыть галерею', all='Полный каталог на английском', subscribe='Подписаться', more='Открыть галереи', prefix='Обложка видео:', today='Звуки дождя и мягкая музыка'),
'ja': dict(home='ホーム', rain='雨音', black='黒画面', japanese='日本の寝室', cozy='居心地のよい環境音', music='音楽', nature='自然', other='その他の音', youtube='YouTubeで見る', play='ここで再生', details='動画詳細（英語）', video='本の動画', long='本の長時間動画', intro='サムネイルを選ぶと公式YouTubeプレーヤーで再生できます。YouTubeでも視聴できます。', series='他の音のコレクション', latest='最近公開された長時間動画', visit='ギャラリーを見る', all='全動画一覧（英語）', subscribe='チャンネル登録', more='ギャラリーを見る', prefix='動画のサムネイル：', today='雨音とやさしい音楽'),
}


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def save(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding='utf-8') == content:
        return False
    path.write_text(content, encoding='utf-8')
    return True


def localized_url(file: str, lang: str) -> str:
    return BASE + ('' if lang == 'en' else lang + '/') + ('' if file == 'index.html' else file)


def linksets(file: str) -> str:
    all_lang = ''.join(f'<link rel="alternate" hreflang="{x}" href="{esc(localized_url(file, x))}">\n' for x in LOCALES)
    return all_lang + f'<link rel="alternate" hreflang="x-default" href="{esc(localized_url(file,"en"))}">'


def language_switch(file: str, lang: str) -> str:
    links=[]
    for code in LOCALES:
        url='/SonoCalming/'+('' if code=='en' else code+'/')+('' if file=='index.html' else file)
        current=' aria-current="page"' if code==lang else ''
        links.append(f'<a href="{url}"{current}>{esc(LANG_NAMES[code])}</a>')
    return (f'<details class="gallery-lang"><summary aria-label="Language">'
            f'🌐 {esc(LANG_NAMES[lang])}</summary><div class="gallery-lang-links">'
            f'{"".join(links)}</div></details>')


def heading(file: str, lang: str) -> tuple[str,str]:
    if file in EXTRA.get(lang,{}): return EXTRA[lang][file]
    if lang != 'en': return PAGE[lang][file]
    titles = {'rain-sounds.html':('Rain sounds on windows, roofs & leaves','Explore all SonoCalming rain videos, from steady rainfall to rain on windows, rooftops and leaves.'),
              'japanese-bedroom.html':('Night rain in cozy Japanese bedrooms','Browse Japanese bedroom rain sounds at night, with rain against windows and roofs.'),
              'black-screen.html':('Black screen rain & steady sound videos','Browse long black screen videos, including rain, white noise and brown noise.'),
              'music.html':('Gentle piano & relaxing background music','Browse soothing piano, ambient music and other peaceful listening sessions.'),
              'music-nature.html':('Gentle music and nature sounds','Discover gentle music accompanied by rain, water, birdsong and natural ambience.'),
              'rain-piano.html':('Rain and soft piano music','Listen to gentle piano combined with rain sounds and cozy scenes.')}
    return titles[file]


def groups_for(v: dict) -> set[str]:
    name = str(v.get('title','')).casefold()
    cat = v.get('cat','')
    groups: set[str] = set()
    rain = bool(re.search(r'\brain(?:fall|y|drops?)?\b|\bdrizzle\b|\bthunder(?:storm)?\b|\bdownpour\b', name))
    music = cat in ('Music & Nature','Relaxing Music') or bool(re.search(r'\bpiano\b|\bhandpan\b|\bmusic\b|\bmelody\b',name))
    if rain and not music or cat == 'Rain Sounds': groups.add('rain-sounds.html')
    if cat == 'Japanese Bedroom' or re.search(r'japanese\s*(bedroom|room)|japan(?:ese)?\s*(?:night|rain)', name): groups.add('japanese-bedroom.html')
    if cat == 'Black Screen' or re.search(r'black\s*screen|dark\s*screen|screen\s*off', name): groups.add('black-screen.html')
    if cat == 'Cozy Ambience' or re.search(r'fireplace|crackling fire|cozy\s*(?:cabin|room|ambience|fire)|cottage',name): groups.add('cozy-ambience.html')
    if cat == 'Relaxing Music' or (music and cat!='Music & Nature'): groups.add('music.html')
    if cat == 'Music & Nature' or (music and re.search(r'rain|river|forest|bird|nature|waterfall|wave|sea',name)): groups.add('music-nature.html')
    if ('rain' in name or cat=='Music & Nature') and re.search(r'\bpiano\b',name): groups.add('rain-piano.html')
    if cat == 'Nature Sounds' or (not music and re.search(r'forest|waterfall|birdsong|ocean|sea waves|river|stream',name)): groups.add('nature-sounds.html')
    if cat == 'Blue Room' or v.get('blueRoom') or re.search(r'blue\s*(?:room|bedroom|apartment)',name): groups.add('blue-room.html')
    if cat == 'Noise & Household' or re.search(r'\b(?:white|pink|brown|gray|grey) noise\b|dishwasher|washing machine|fan sounds',name): groups.add('noise-household.html')
    return groups


def secs(duration: str) -> int:
    m = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', str(duration))
    if not m: return 0
    return 3600*int(m[1] or 0)+60*int(m[2] or 0)+int(m[3] or 0)


def items() -> list[dict]:
    data = json.loads((SONO/'videos.json').read_text(encoding='utf-8'))
    if not isinstance(data,list): raise ValueError('Expected a list in SonoCalming/videos.json')
    valid=[]
    for x in data:
        if not isinstance(x,dict) or x.get('short') or not VIDEO_ID.fullmatch(str(x.get('id',''))): continue
        if not (SONO/'videos'/f'{x["id"]}.html').exists(): continue
        x=dict(x)
        x['_seconds']=secs(x.get('duration',''))
        x['_long']=x['_seconds']>=3600
        x['_group']=groups_for(x)
        valid.append(x)
    # Prefer >=1 hour, then most recent within each group. Keep shorter catalogue videos at end.
    return sorted(valid,key=lambda x:(not x['_long'], -int(str(x.get('date','2000-01-01')).replace('-','') or '0'),x['id']))


def card(v: dict, lang: str) -> str:
    id = v['id']; title=esc(v['title']); text=UI[lang]
    h, rem = divmod(v['_seconds'], 3600); m = rem//60
    duration = f'{h}h {m:02d}m' if h else f'{m}m'
    details = f'<a href="/SonoCalming/videos/{id}.html">{esc(text["details"])}</a>' if lang=='en' else ''
    return f'''<article class="sono-video-card" id="video-{id}">
      <button type="button" class="sono-poster js-player" data-video="{id}" aria-label="{esc(text['play'])}: {title}">
        <img src="https://i.ytimg.com/vi/{id}/hqdefault.jpg" alt="{esc(text['prefix'])} {title}" loading="lazy" decoding="async" width="480" height="360">
        <span class="sono-play-badge" aria-hidden="true">▶</span></button>
      <div class="sono-video-info"><span class="sono-video-meta">{duration} · <time datetime="{esc(v.get('date',''))}">{esc(v.get('date',''))}</time></span>
      <h3>{title}</h3><div class="sono-video-actions"><a href="https://www.youtube.com/watch?v={id}" target="_blank" rel="noopener noreferrer">{esc(text['youtube'])}</a>{details}</div></div>
    </article>'''


def gallery_section(file: str, lang: str, videos: list[dict]) -> str:
    relevant=[v for v in videos if file in v['_group']]
    title, description=heading(file,lang)
    long_count=sum(v['_long'] for v in relevant)
    grid='\n'.join(card(v,lang) for v in relevant)
    t=UI[lang]
    return f'''<section class="section shell sono-gallery-section" id="gallery" aria-labelledby="gallery-title">
  <p class="eyebrow">{esc(CATMAP[file][1])} · SonoCalming</p>
  <h2 id="gallery-title">{esc(title)}</h2>
  <p class="lead">{esc(description)}</p>
  <p class="sono-gallery-count">{len(relevant)} {esc(t['video'])}, {long_count} {esc(t['long'])}. {esc(t['intro'])}</p>
  <div class="sono-video-grid">{grid}</div>
</section>'''


def chooser(lang: str, selected: str | None = None, short: bool=False) -> str:
    return '<div class="sono-chooser">'+''.join(
      f'<a class="sono-category-link{" is-active" if f==selected else ""}" href="/SonoCalming/{"" if lang=="en" else lang+"/"}{f}#gallery"><span>{emoji}</span> {esc(heading(f,lang)[0])}</a>'
      for f,emoji,_ in CATS)+'</div>'


def json_script(obj: dict) -> str:
    return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+'</script>'


def header(lang: str, file: str) -> str:
    t=UI[lang]
    skip={'en':'Skip to content','fr':'Aller au contenu','de':'Zum Inhalt','es':'Ir al contenido','it':'Vai al contenuto','pt':'Ir para o conteúdo','ru':'К содержимому','ja':'本文へ'}[lang]
    menu={'en':'Menu','fr':'Menu','de':'Menü','es':'Menú','it':'Menu','pt':'Menu','ru':'Меню','ja':'メニュー'}[lang]
    routes=[('rain-sounds.html',t['rain']),('japanese-bedroom.html',t['japanese']),('black-screen.html',t['black']),('cozy-ambience.html',t['cozy']),('music.html',t['music']),('nature-sounds.html',t['nature'])]
    prefix='/SonoCalming/' + ('' if lang=='en' else lang+'/')
    nav=''.join(f'<a href="{prefix}{f}">{esc(label)}</a>' for f,label in routes)
    return f'''<a class="skip" href="#main">{esc(skip)}</a><header><div class="shell nav">
      <a class="brand" href="{prefix}"><span class="drop">●</span><span><b>SonoCalming</b><small>{esc(t['today'])}</small></span></a>
      <button type="button" aria-controls="links" aria-expanded="false" id="menu">{esc(menu)}</button>
      <nav aria-label="Main navigation" id="links">{nav}<a class="pill" href="https://www.youtube.com/channel/UCGXypunMB75x599kvbSAuqw?sub_confirmation=1" rel="noopener" target="_blank">{esc(t['subscribe'])}</a></nav>
      {language_switch(file,lang)}</div></header>'''


def footer(lang: str) -> str:
    t=UI[lang]
    return f'''<footer><div class="shell foot"><div><b>SonoCalming</b><p>{esc(t['today'])}</p></div><div>
    <a href="/SonoCalming/{'' if lang=='en' else lang+'/'}">{esc(t['home'])}</a>
    <a href="/SonoCalming/videos.html">{esc(t['all'])}</a>
    <a href="https://www.youtube.com/channel/UCGXypunMB75x599kvbSAuqw" rel="noopener" target="_blank">YouTube</a>
    <a href="/{'' if lang=='en' else lang+'/'}">AML Creation</a></div></div></footer>'''


def template(file: str,lang: str,body: str,desc: str,title: str, schema: dict | None=None, thumbnail: str | None=None) -> str:
    canonical=localized_url(file,lang)
    css='../' if lang!='en' else ''
    structured=json_script(schema) if schema else ''
    social_img=(f'<meta property="og:image" content="https://i.ytimg.com/vi/{thumbnail}/hqdefault.jpg">'
                f'<meta name="twitter:image" content="https://i.ytimg.com/vi/{thumbnail}/hqdefault.jpg">') if thumbnail else ''
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | SonoCalming</title><meta name="description" content="{esc(desc[:250])}">
<meta name="robots" content="index,follow,max-image-preview:large,max-video-preview:-1">
<link rel="canonical" href="{esc(canonical)}">
{linksets(file)}
<link rel="icon" type="image/svg+xml" href="{css}favicon.svg"><link rel="stylesheet" href="{css}styles-20261009.css"><link rel="stylesheet" href="{css}gallery.css">
<meta name="theme-color" content="#08131c"><meta name="referrer" content="strict-origin-when-cross-origin"><meta property="og:type" content="website"><meta property="og:site_name" content="SonoCalming"><meta property="og:title" content="{esc(title)} | SonoCalming"><meta property="og:description" content="{esc(desc[:250])}"><meta property="og:url" content="{esc(canonical)}"><meta name="twitter:card" content="summary_large_image">
{social_img}
{structured}</head><body>{header(lang,file)}<main id="main">{body}</main>{footer(lang)}<script src="{css}site.js" defer></script></body></html>\n'''


def category_page(file: str,lang: str,videos: list[dict]) -> str:
    title,desc=heading(file,lang)
    relevant=[v for v in videos if file in v['_group']]
    schema={ '@context':'https://schema.org','@type':'CollectionPage','name':title, 'description':desc,
        'url':localized_url(file,lang),'mainEntity':{'@type':'ItemList','numberOfItems':len(relevant),
        'itemListElement':[{'@type':'ListItem','position':i+1,'url':BASE+'videos/'+v['id']+'.html','name':v['title']} for i,v in enumerate(relevant)]}}
    head=f'''<section class="page shell sono-gallery-hero"><p class="eyebrow">SonoCalming · {esc(CATMAP[file][1])}</p><h1>{esc(title)}</h1><p class="lead">{esc(desc)}</p>
      <p><a class="textlink" href="#gallery">{esc(UI[lang]['visit'])} ↓</a></p></section>'''
    body=head+gallery_section(file,lang,videos)+f'<section class="section shell"><h2>{esc(UI[lang]["series"])}</h2>{chooser(lang,file)}</section>'
    return template(file,lang,body,desc,title,schema, relevant[0]["id"] if relevant else None)


def home_page(lang: str,videos: list[dict]) -> str:
    title,desc=PAGE[lang]['index.html']
    recent=[v for v in videos if v['_long']][:6]
    grid=''.join(card(v,lang) for v in recent)
    t=UI[lang]
    body=f'''<section class="page shell sono-gallery-hero"><p class="eyebrow">SonoCalming</p><h1>{esc(title)}</h1><p class="lead">{esc(desc)}</p></section>
    <section class="section shell"><h2>{esc(t['more'])}</h2><p class="lead">{esc(t['intro'])}</p>{chooser(lang)}</section>
    <section class="section shell"><h2>{esc(t['latest'])}</h2><div class="sono-video-grid">{grid}</div></section>'''
    schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'description':desc,'url':localized_url('index.html',lang)}
    return template('index.html',lang,body,desc,title,schema, recent[0]['id'] if recent else None)


def hub_page(file: str,lang: str) -> str:
    title,desc=PAGE[lang][file]
    text=UI[lang]
    body=f'''<section class="page shell sono-gallery-hero"><p class="eyebrow">SonoCalming</p><h1>{esc(title)}</h1><p class="lead">{esc(desc)}</p></section>
    <section class="section shell"><h2>{esc(text['more'])}</h2>{chooser(lang)}</section>
    <section class="section shell"><p><a class="btn primary" href="/SonoCalming/videos.html">{esc(text['all'])}</a></p></section>'''
    return template(file,lang,body,desc,title)


def replace_marked(doc: str,start: str,end: str,block: str) -> str:
    pat=re.compile(re.escape(start)+r'.*?'+re.escape(end),re.S)
    body=start+'\n'+block+'\n'+end
    if start in doc:
        if doc.count(start)!=1 or doc.count(end)!=1: raise ValueError('Duplicate gallery markers')
        return pat.sub(lambda _:body,doc,count=1)
    return doc


def decorate_english(file: str,videos: list[dict]) -> bool:
    p=SONO/file
    source=p.read_text(encoding='utf-8')
    doc=source
    if LANG_START in doc:
        doc=replace_marked(doc,LANG_START,LANG_END,linksets(file)+'\n<link rel="stylesheet" href="gallery.css">')
    else:
        doc=doc.replace('</head>', LANG_START+'\n'+linksets(file)+'\n<link rel="stylesheet" href="gallery.css">\n'+LANG_END+'\n</head>',1)
    menu = language_switch(file,'en')
    if '<details class="gallery-lang"' not in doc:
        doc=doc.replace('</nav>', '</nav>'+menu,1)
    if file == 'index.html':
        doc=doc.replace('<a class="btn" href="videos.html">Browse all videos</a>', '<a class="btn" href="#galleries">Explore galleries</a>')
        block=f'<section class="section shell sono-home-chooser" id="galleries"><p class="eyebrow">All sound collections</p><h2>Explore every video gallery</h2><p class="lead">Browse thumbnails by sound, play directly here and open each original YouTube video.</p>{chooser("en")}</section>'
        if HOME_START in doc: doc=replace_marked(doc,HOME_START,HOME_END,block)
        else:
            idx=doc.find('<section class="section shell" id="families">')
            if idx < 0: raise ValueError('English homepage structure changed, cannot insert galleries')
            doc=doc[:idx]+HOME_START+'\n'+block+'\n'+HOME_END+'\n'+doc[idx:]
    if file in CURRENT_EN:
        section=gallery_section(file,'en',videos)
        if GALLERY_START in doc:
            doc=replace_marked(doc,GALLERY_START,GALLERY_END,section)
        else:
            match=re.search(r'<section\b[^>]*class="[^"]*\b(?:page|familyHero)\b[^"]*"[^>]*>.*?</section>',doc,re.S)
            if not match: raise ValueError(f'No intro section in English category page: {file}')
            end=match.end();doc=doc[:end]+'\n'+GALLERY_START+'\n'+section+'\n'+GALLERY_END+'\n'+doc[end:]
    return save(p,doc)


def set_english_sitemap() -> bool:
    """Append new English hubs and omit misleading legacy lastmod dates for dynamic galleries."""
    path=SONO/'sitemap.xml'
    tree=ET.parse(path)
    root=tree.getroot()
    urls={node.find(f'{{{SM}}}loc').text:node for node in root.findall(f'{{{SM}}}url')
          if node.find(f'{{{SM}}}loc') is not None}
    changed=False
    for file in NEW_EN:
        url=localized_url(file,'en')
        if url not in urls:
            node=ET.SubElement(root,f'{{{SM}}}url')
            ET.SubElement(node,f'{{{SM}}}loc').text=url
            changed=True
    # A category's visible gallery changes with new uploads; its old, hardcoded
    # 2026-10-09 modification date must not be presented as a verified timestamp.
    dynamic={localized_url(file,'en') for file in CATMAP}
    dynamic.add(localized_url('index.html','en'))
    for node in root.findall(f'{{{SM}}}url'):
        url_node=node.find(f'{{{SM}}}loc')
        if url_node is not None and url_node.text in dynamic:
            old=node.find(f'{{{SM}}}lastmod')
            if old is not None:
                node.remove(old)
                changed=True
    if not changed:return False
    ET.indent(tree,space=' ')
    return save(path,ET.tostring(root,encoding='utf-8',xml_declaration=True).decode('utf-8')+'\n')


def sitemap_i18n() -> bool:
    # The English legacy hub URLs remain in SonoCalming/sitemap.xml.
    # The English video-watch URLs remain in SonoCalming/video-sitemap.xml.
    root=ET.Element(f'{{{SM}}}urlset')
    files=('index.html', *CATMAP, 'about.html', 'playlists.html')
    for lang in LOCALES:
        for file in files:
            if lang=='en' and file not in NEW_EN: continue
            node=ET.SubElement(root,f'{{{SM}}}url')
            ET.SubElement(node,f'{{{SM}}}loc').text=localized_url(file,lang)
            for code in (*LOCALES,'x-default'):
                target='en' if code=='x-default' else code
                ET.SubElement(node,f'{{{XHTML}}}link',{'rel':'alternate','hreflang':code,'href':localized_url(file,target)})
    ET.indent(root,space=' ')
    content=ET.tostring(root,encoding='utf-8',xml_declaration=True).decode('utf-8')+'\n'
    return save(SONO/'sitemap-languages.xml',content)


def sitemap_sono_index() -> bool:
    """Keep the SonoCalming-local index aware of translated gallery URLs."""
    path=SONO/'sitemap-index.xml'
    tree=ET.parse(path)
    root=tree.getroot()
    existing={item.text for item in root.findall(f'{{{SM}}}sitemap/{{{SM}}}loc')}
    target=BASE+'sitemap-languages.xml'
    if target in existing:return False
    ET.SubElement(ET.SubElement(root,f'{{{SM}}}sitemap'),f'{{{SM}}}loc').text=target
    ET.indent(tree,space=' ')
    return save(path,ET.tostring(root,encoding='utf-8',xml_declaration=True).decode('utf-8')+'\n')


def lang_for_page(p: Path) -> str:
    rel=p.relative_to(ROOT)
    if len(rel.parts)>=2 and rel.parts[0] in LOCALES: return rel.parts[0]
    stem=p.stem
    if p.parent.name=='Games':
        if stem.endswith(('-fr','-de','-es','-it','-pt','-ru','-ja')): return stem.rsplit('-',1)[-1]
        if stem in ('jeux-IOS-android','tinyStory-Aide','Celestwald-aide','cats-in-the-box-aide'): return 'fr'
    match=re.search(r'[_-](fr|de|es|it|pt|ru|ja)$',stem)
    if match:return match[1]
    if p.parent.name=='lumenmine' or 'lumenmine' in rel.parts:
        for sub in rel.parts:
            if sub in LOCALES: return sub
            if sub in ('pt-br','pt-pt'):return 'pt'
    return 'en'


def relink_site(videos: list[dict]) -> int:
    by_id={v['id']:v for v in videos}
    updated=0
    for p in ROOT.rglob('*.html'):
        if 'SonoCalming' in p.relative_to(ROOT).parts or p.name.endswith('_x.html'):continue
        if any(x in p.parts for x in ('.git','__MACOSX')): continue
        raw=p.read_text(encoding='utf-8')
        if 'SonoCalming/' not in raw:continue
        lang=lang_for_page(p)
        if lang=='en': continue
        def change(m: re.Match) -> str:
            href=m.group(2)
            match=re.search(r'(SonoCalming/)(.*)$',href)
            if not match:return m.group(0)
            tail=match.group(2)
            if tail.startswith(tuple(x+'/' for x in LOCALES if x!='en')):return m.group(0)
            if tail.startswith('videos/') and tail.endswith('.html'):
                video_id=tail.split('/')[-1][:-5]
                v=by_id.get(video_id)
                route=preferred_category(v) if v else 'rain-sounds.html'
                tail=route+'#video-'+video_id if v and route in v['_group'] else route
            elif tail not in ('','index.html') and tail not in CATMAP:
                # Keep English-only detail and library URLs, not invented translated pages.
                return m.group(0)
            replacement=href[:match.start(2)]+lang+'/'+tail
            return m.group(1)+replacement+m.group(3)
        edited=re.sub(r'(<a\b[^>]*?\bhref=")([^"]+)(")',change,raw,flags=re.I)
        if save(p,edited):updated+=1
    return updated


def preferred_category(v:dict|None) -> str:
    if not v:return 'rain-sounds.html'
    cat=v.get('cat')
    routes={'Black Screen':'black-screen.html','Japanese Bedroom':'japanese-bedroom.html',
            'Rain Sounds':'rain-sounds.html','Cozy Ambience':'cozy-ambience.html',
            'Relaxing Music':'music.html','Music & Nature':'music-nature.html',
            'Nature Sounds':'nature-sounds.html','Blue Room':'blue-room.html','Noise & Household':'noise-household.html'}
    return routes.get(cat,'rain-sounds.html')


def main() -> None:
    videos=items()
    if not videos:raise RuntimeError('Cannot build galleries: no valid video records')
    changes=0
    for file in ('index.html',*CURRENT_EN,'playlists.html','about.html'):
        changes+=decorate_english(file,videos)
    for file in NEW_EN:
        changes+=save(SONO/file,category_page(file,'en',videos))
    for lang in LOCALES[1:]:
        changes+=save(SONO/lang/'index.html',home_page(lang,videos))
        for file in CATMAP:
            changes+=save(SONO/lang/file,category_page(file,lang,videos))
        for file in ('playlists.html','about.html'):
            changes+=save(SONO/lang/file,hub_page(file,lang))
    changes+=set_english_sitemap()
    changes+=sitemap_i18n()
    changes+=sitemap_sono_index()
    # Localized AML Creation pages link to the corresponding SonoCalming galleries.
    cross=relink_site(videos)
    print(f'SonoCalming galleries: {len(LOCALES)} languages, {len(CATMAP)} categories, {len(videos)} catalogue videos, {changes} pages/assets changed, {cross} cross-site pages updated')


if __name__=='__main__': main()
