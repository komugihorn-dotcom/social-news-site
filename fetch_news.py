"""Fetch publicly available RSS headlines. Standard library only."""
import datetime as dt, email.utils, hashlib, html, json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

SEARCHES = [
    ('社会・政治', '政治 経済 日本'),
    ('地理・防災', '日本 地震 防災 気候 人口'),
    ('歴史・文化', '歴史 文化財 遺跡 世界遺産'),
    ('岩手・東北', '岩手 東北 地域 ニュース'),
    ('国際', '国際 社会 世界 平和'),
]
items = []
for label, query in SEARCHES:
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q':query,'hl':'ja','gl':'JP','ceid':'JP:ja'})
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'SocialStudiesNewsReader/1.0 (educational RSS reader)'})
        with urllib.request.urlopen(req,timeout=20) as res: raw=res.read(2_000_000)
        root=ET.fromstring(raw)
        for node in root.findall('./channel/item')[:20]:
            def get(name): return (node.findtext(name) or '').strip()
            title=html.unescape(get('title'))
            link=get('link')
            if not title or not link.startswith('http'): continue
            source=node.find('source')
            source_name=source.text if source is not None and source.text else label
            published=get('pubDate')
            try: date=email.utils.parsedate_to_datetime(published).strftime('%Y-%m-%d')
            except Exception: date=''
            description=re.sub('<[^>]*>',' ',html.unescape(get('description')))
            items.append({'id':hashlib.sha256(link.encode()).hexdigest()[:20],'title':title,'url':link,'source':source_name,'date':date,'description':description[:250]})
        print(label,'OK')
    except Exception as exc: print(label,'FAILED',str(exc))
unique={x['id']:x for x in items}
path=Path(__file__).with_name('news.json')
try:
    old=json.loads(path.read_text(encoding='utf-8'))
except (FileNotFoundError, json.JSONDecodeError):
    old={'items': []}
# Keep all previously collected articles; refresh metadata for repeat items.
archive={x['id']:x for x in old.get('items',[]) if x.get('id')}
archive.update(unique)
if unique:
    payload={'updated':dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST'),
             'items':sorted(archive.values(),key=lambda x:x.get('date') or '',reverse=True)}
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print('saved',len(payload['items']),'total articles;',len(unique),'fetched')
else:
    print('No new data; retaining previous news.json')
