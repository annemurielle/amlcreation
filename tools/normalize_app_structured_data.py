#!/usr/bin/env python3
"""Avoid ineligible SoftwareApplication rich-result declarations without faking ratings.

Google's SoftwareApplication rich results require an Offer price and a verified
review/rating. When either is absent, retain truthful structured data as
VideoGame (game) or CreativeWork (non-game). No invented reviews, prices, or
store ratings; rendered site content remains unchanged. Safe to rerun.
"""
from __future__ import annotations
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Games'
PAT=re.compile(r'(<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',re.I|re.S)

def valid_offer(node:dict)->bool:
    offer=node.get('offers')
    if isinstance(offer,list):return bool(offer) and all(isinstance(v,dict) and v.get('price') is not None for v in offer)
    return isinstance(offer,dict) and offer.get('price') is not None

def valid_rating(node:dict)->bool:
    rating=node.get('aggregateRating')
    if isinstance(rating,dict) and rating.get('ratingValue') is not None and (rating.get('ratingCount') or rating.get('reviewCount')):return True
    review=node.get('review')
    return bool(review)

def normalize(value:object)->int:
    edited=0
    if isinstance(value,list):
        for item in value:edited+=normalize(item)
    elif isinstance(value,dict):
        ty=value.get('@type')
        if ty in ('MobileApplication','SoftwareApplication') and not (valid_offer(value) and valid_rating(value)):
            category=value.get('applicationCategory')
            if category == 'GameApplication':
                # VideoGame has meaningful game metadata but Google doesn't
                # incorrectly treat it as an eligible Software App result.
                value['@type']='VideoGame'
            else:
                # For a non-game with no verified review, use general content
                # classification rather than advertising an ineligible app rich result.
                value['@type']='CreativeWork'
                installation=value.pop('installUrl',None)
                for k in ('operatingSystem','applicationCategory','screenshot'):
                    value.pop(k,None)
                if installation and 'sameAs' not in value:
                    value['sameAs']=installation
            edited+=1
        for k,v in value.items():
            if k!='@context':edited+=normalize(v)
    return edited

def fix(markup:str)->tuple[str,int]:
    modified=0
    def sub(m:re.Match)->str:
        nonlocal modified
        try:root=json.loads(m.group(2))
        except (ValueError,TypeError):return m.group(0)
        change=normalize(root)
        if not change:return m.group(0)
        modified+=change
        return m.group(1)+json.dumps(root,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+m.group(3)
    return PAT.sub(sub,markup),modified

def main()->None:
    changed=0;converted=0
    for html in sorted(SOURCE.glob('*.html')):
        old=html.read_text(encoding='utf-8')
        new,count=fix(old)
        if count:
            html.write_text(new,encoding='utf-8')
            changed+=1;converted+=count
    print(f'Game pages: {changed} pages updated, {converted} unverifiable app rich results converted to honest schema types.')

if __name__=='__main__':main()
