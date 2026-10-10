#!/usr/bin/env python3
"""Refresh public store metadata and static HTML, without keys or dependencies.

Google Play's public markup is not a guaranteed API. If it changes or a request
fails, retain the last verified snapshot and its original verification date.
Apple ratings refer to the configured storefront, not a worldwide average.
Store ratings are deliberately never copied into search review JSON-LD.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
from urllib.request import Request, urlopen

VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
STORE_TEXT = json.loads(Path(__file__).with_name('game-store-translations.json').read_text())

class Node:
    def __init__(self,tag='',attrs=None,parent=None):
        self.tag,self.attrs,self.parent,self.children = tag,dict(attrs or []),parent,[]
    def text(self):
        return ''.join(c if isinstance(c,str) else c.text() for c in self.children)
    def all(self):
        yield self
        for c in self.children:
            if isinstance(c,Node):yield from c.all()
    def cls(self,name):return name in self.attrs.get('class','').split()

class Document(HTMLParser):
    def __init__(self,markup):
        super().__init__(convert_charrefs=True);self.root=Node('document');self.stack=[self.root];self.feed(markup)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs,self.stack[-1]);self.stack[-1].children.append(n)
        if tag not in VOID:self.stack.append(n)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)

def fetch(url):
    request=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; AMLCreationStoreMetadata/1.0)','Accept-Language':'en-US,en;q=0.9'})
    with urlopen(request,timeout=25) as response:
        return response.read().decode('utf-8')

def applications(doc):
    for node in doc.root.all():
        if node.tag=='script' and node.attrs.get('type')=='application/ld+json':
            try:data=json.loads(node.text())
            except (ValueError,TypeError):continue
            values=data if isinstance(data,list) else [data]
            for item in values:
                if isinstance(item,dict):
                    if item.get('@type') in ['SoftwareApplication','MobileApplication']:yield item
                    for x in item.get('@graph',[]):
                        if x.get('@type') in ['SoftwareApplication','MobileApplication']:yield x

def excerpt(text):
    words=text.split()
    return ' '.join(words[:6])+('…' if len(words)>6 else '')

def parse_google(markup,package,url,checked):
    doc=Document(markup);app=next(applications(doc),None)
    if not app or package not in app.get('url',''):raise ValueError('No matching Google Play application metadata')
    result={'store':'Google Play','url':url,'updatedAt':checked,'region':'US','language':'en','name':app['name']}
    agg=app.get('aggregateRating',{})
    try:
        rating=float(agg['ratingValue']);count=int(agg['ratingCount'])
        if 0<rating<=5 and count>0:result.update(rating=rating,ratingCount=count)
    except (KeyError,ValueError,TypeError):pass
    visible=' '.join(doc.root.text().split())
    m=re.search(r'([\d.,]+[KMB]?\+)\s*Downloads',visible)
    if m:result['downloads']=m.group(1)
    reviews=[]
    for node in doc.root.all():
        if not node.cls('h3YV2d'):continue
        text=' '.join(node.text().split())
        if not text:continue
        container=node.parent
        # Find the nearby rating and date belonging to this exact displayed review.
        for _ in range(5):
            if not container:break
            if any(x.cls('bp9Aid') for x in container.all()):break
            container=container.parent
        item={'excerpt':excerpt(text),'url':url}
        if container:
            date=next((x.text() for x in container.all() if x.cls('bp9Aid')),None)
            if date:item['date']=date
            stars=next((x.attrs.get('aria-label','') for x in container.all() if x.cls('iXRFPc')),None)
            m=re.search(r'Rated ([1-5]) stars',stars or '')
            if m:item['rating']=int(m.group(1))
        reviews.append(item)
        if len(reviews)==2:break
    result['reviews']=reviews
    return result

def parse_apple(markup,apple_id,url,checked):
    doc=Document(markup);app=next(applications(doc),None)
    if not app:raise ValueError('No App Store application metadata')
    result={'store':'App Store','url':url,'updatedAt':checked,'region':'US','language':'en','name':app['name']}
    agg=app.get('aggregateRating',{})
    try:
        rating=float(agg['ratingValue']);count=int(agg.get('ratingCount',agg.get('reviewCount',0)))
        if 0<rating<=5 and count>0:result.update(rating=rating,ratingCount=count)
    except (KeyError,ValueError,TypeError):pass
    return result

def render(app,lang='en',show_reviews=True):
    if isinstance(lang,bool):lang='fr' if lang else 'en'
    labels=STORE_TEXT.get(lang,STORE_TEXT['en'])
    def label(key):return escape(labels[key])
    stores=app.get('stores',{});parts=[]
    title=label('store-title')
    for platform in ['android','ios']:
        store=stores.get(platform)
        if not store:continue
        parts.append('<article class="store-stat"><h3>'+escape(store['store'])+'</h3>')
        if store.get('rating'):
            parts.append('<p class="stat-value">'+f'{store["rating"]:.1f}'+' <span aria-hidden="true">★</span><span class="stat-meta"> / 5</span></p><p class="stat-meta">'+format(store['ratingCount'],',')+' '+label('ratings')+'</p>')
        else:parts.append('<p class="store-empty">'+label('empty')+'</p>')
        if store.get('downloads'):
            parts.append('<p class="stat-value">'+escape(store['downloads'])+'</p><p class="stat-meta">'+label('threshold')+'</p>')
        date=store['updatedAt'][:10]
        parts.append('<p class="stat-meta">'+label('checked')+' '+escape(date)+' · '+label('region')+'</p><a class="stat-store-link" href="'+escape(store['url'],quote=True)+'" target="_blank" rel="noopener noreferrer">'+label('store-link')+'</a></article>')
    if not parts:return ''
    result='<section class="store-stats" id="store-stats"><h2>'+title+'</h2><div class="store-stat-grid">'+''.join(parts)+'</div>'
    # Only short, attributed public excerpts, in the store's displayed order.
    reviews=stores.get('android',{}).get('reviews',[]) if show_reviews else []
    if reviews:
        result+='<h3 style="margin-top:24px">'+label('review-heading')+'</h3><div class="store-reviews">'
        for rev in reviews:
            result+='<blockquote class="store-review"><p>“'+escape(rev['excerpt'])+'”</p><cite>Google Play'+(' · '+str(rev['rating'])+'/5' if rev.get('rating') else '')+(' · '+escape(rev['date']) if rev.get('date') else '')+'</cite></blockquote>'
        result+='</div>'
    result+='<p class="stats-note">'+label('store-note')+(' '+label('review-note') if reviews else '')+'</p></section>'
    return result

def update_html(root,data):
    config=json.loads((root/'scripts/game-store-config.json').read_text())
    updated=0
    for key,app in data['apps'].items():
        for name in config[key]['pages']:
            path=root/'Games'/name
            if not path.exists():continue
            markup=path.read_text()
            match=re.search(r'<html\b[^>]*\blang=["\x27]([^"\x27]+)',markup)
            lang=match.group(1) if match else 'en'
            pattern=r'<!-- STORE_STATS_START:'+re.escape(key)+r' -->.*?<!-- STORE_STATS_END:'+re.escape(key)+r' -->'
            new='<!-- STORE_STATS_START:'+key+' -->\n'+render(app,lang,lang=='en')+'\n<!-- STORE_STATS_END:'+key+' -->'
            markup,count=re.subn(pattern,lambda _:new,markup,flags=re.S)
            if count:path.write_text(markup);updated+=1
    return updated

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--cache-dir',type=Path);parser.add_argument('--only',nargs='*');args=parser.parse_args()
    root=args.root;config=json.loads((root/'scripts/game-store-config.json').read_text());path=root/'Games/store-data.json'
    data=json.loads(path.read_text()) if path.exists() else {'version':1,'apps':{}}
    checked=datetime.now(timezone.utc).isoformat(timespec='seconds')
    tasks=[]
    for key,cfg in config.items():
        if args.only and key not in args.only:continue
        for platform in ['android','ios']:
            ident=cfg.get(platform)
            if ident:tasks.append((key,platform,ident))
    def run(task):
        key,platform,ident=task
        url=('https://play.google.com/store/apps/details?id='+ident+'&hl=en&gl=US') if platform=='android' else ('https://apps.apple.com/us/app/id'+ident)
        try:
            cache=args.cache_dir/(key+'-'+platform+'.html') if args.cache_dir else None
            markup=cache.read_text() if cache and cache.exists() else fetch(url)
            if cache and not cache.exists():cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(markup)
            fn=parse_google if platform=='android' else parse_apple
            return key,platform,fn(markup,ident,url,checked),None
        except Exception as error:return key,platform,None,str(error)
    failures=[];success=0
    for key,platform,result,error in ThreadPoolExecutor(max_workers=6).map(run,tasks):
        if error:
            failures.append(key+' / '+platform+': '+error);continue
        success+=1
        app=data['apps'].setdefault(key,{'name':config[key]['name'],'stores':{}})
        app['stores'][platform]=result
    if success:
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
        print('Updated '+str(success)+' store snapshots and '+str(update_html(root,data))+' pages.')
    for error in failures:print('Retained last verified data: '+error,file=sys.stderr)
    if not success:raise SystemExit('No store snapshots could be verified; no files changed.')

if __name__=='__main__':main()
