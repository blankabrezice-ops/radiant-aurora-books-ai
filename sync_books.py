#!/usr/bin/env python3
"""Merge an explicitly approved JSON feed into the local book catalog.
Source must supply direct title, store, author, product URL, image URL.
No scraping or guessing from broad Amazon/Lulu searches.
"""
import json,os,re,sys,urllib.request,urllib.parse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=os.environ.get('RADIANT_BOOKS_FEED_URL','').strip()
AUTHOR=os.environ.get('RADIANT_AUTHOR','Radiant Aurora').strip().casefold()
if not SOURCE:
 print('No RADIANT_BOOKS_FEED_URL configured; existing catalog unchanged.')
 sys.exit(0)
if not SOURCE.startswith('https://'):
 sys.exit('Feed URL must use HTTPS')
with urllib.request.urlopen(urllib.request.Request(SOURCE,headers={'User-Agent':'RadiantAuroraCatalogSync/1.0'}),timeout=25) as r:
 data=r.read(2_000_001)
if len(data)>2_000_000:sys.exit('Feed too large')
incoming=json.loads(data)
if not isinstance(incoming,list):sys.exit('Feed must be a JSON array')
path=ROOT/'books.json'
books=json.loads(path.read_text(encoding='utf-8'))
if not isinstance(books,list):sys.exit('Invalid existing catalog')
def key(b):return (b.get('store','').casefold(),b.get('product_url','').strip())
existing={key(b) for b in books if b.get('product_url')}
count=0
for item in incoming:
 if not isinstance(item,dict):continue
 store=item.get('store','')
 title=item.get('title','')
 author=item.get('author','')
 link=item.get('product_url','')
 image=item.get('image','')
 if not all(isinstance(x,str) for x in [store,title,author,link,image]):continue
 if author.strip().casefold()!=AUTHOR:continue
 if store not in ('Lulu','Amazon'):continue
 parsed=urllib.parse.urlparse(link)
 host=(parsed.hostname or '').lower()
 if parsed.scheme!='https' or not (host=='lulu.com' or host.endswith('.lulu.com')) if store=='Lulu' else False:
  pass
 allowed=(host=='lulu.com' or host.endswith('.lulu.com')) if store=='Lulu' else (host=='amazon.com' or host.endswith('.amazon.com'))
 if parsed.scheme!='https' or not allowed:continue
 if not title.strip() or not image.startswith('https://'):continue
 k=(store.casefold(),link.strip())
 if k in existing:continue
 b={'title':title.strip(),'lang':item.get('lang','en'),'price':item.get('price',''),'format':item.get('format',''),'store':store,'image':image,'product_url':link,'author':author}
 books.append(b);existing.add(k);count+=1
if count:
 path.write_text(json.dumps(books,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Added {count} new verified books; total {len(books)}.')
