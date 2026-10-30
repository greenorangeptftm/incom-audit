#!/usr/bin/env python3
"""Static pre-launch audit of a built site directory. Usage: site_audit.py <dir> <base-url> [--external]"""
import sys, os, re, json, urllib.parse, urllib.request, ssl, datetime
from html.parser import HTMLParser
root = sys.argv[1].rstrip('/'); base = sys.argv[2].rstrip('/'); EXT = '--external' in sys.argv
bp = urllib.parse.urlparse(base).path.rstrip('/')
origin = base[:len(base)-len(bp)] if bp else base
TODAY = datetime.date.today()
pages = sorted(os.path.join(dp, f) for dp, dn, fn in os.walk(root) for f in fn if f.endswith('.html'))
HEAD = ('h1','h2','h3','h4','h5','h6')
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.title=''; s.in_title=False; s.metas=[]; s.links=[]; s.a=[]; s.imgs=[]; s.scripts=[]; s.ld=[]; s.in_ld=False; s.ld_buf=''
        s.heads=[]; s.cur=None; s.ids=[]; s.html_attrs={}; s.text=[]; s.skip=0; s.inputs=[]; s.labels=[]; s.buttons=[]; s.iframes=[]; s.sources=[]
        s.inline=0; s.body_seen=False; s.head_order=[]; s.label_depth=0; s.form_depth=0
    def handle_starttag(s,t,a):
        a=dict(a)
        if t=='html': s.html_attrs=a
        if t=='body': s.body_seen=True
        if 'id' in a: s.ids.append(a['id'])
        if any(k.startswith('on') for k in a): s.inline+=1
        if not s.body_seen and t in ('meta','title','link','script','style'): s.head_order.append((t,a))
        if t=='title': s.in_title=True
        elif t=='meta': s.metas.append(a)
        elif t=='link': s.links.append(a)
        elif t=='a': s.a.append(a)
        elif t=='img': s.imgs.append(a)
        elif t=='source': s.sources.append(a)
        elif t=='script':
            if a.get('type')=='application/ld+json': s.in_ld=True; s.ld_buf=''
            else: s.scripts.append(a)
            s.skip+=1
        elif t=='style': s.skip+=1
        elif t in HEAD: s.cur=[t,'']
        elif t in ('input','textarea','select'): a['_tag']=t; a['_inlabel']=s.label_depth>0; s.inputs.append(a)
        elif t=='label': s.labels.append(a); s.label_depth+=1
        elif t=='button': a['_inform']=s.form_depth>0; s.buttons.append(a)
        elif t=='iframe': s.iframes.append(a)
        elif t=='form': s.form_depth+=1
    def handle_startendtag(s,t,a):
        s.handle_starttag(t,a)
        if t in ('script','style'): s.skip-=1
    def handle_endtag(s,t):
        if t=='title': s.in_title=False
        elif t=='script':
            if s.in_ld: s.ld.append(s.ld_buf); s.in_ld=False
            s.skip-=1
        elif t=='style': s.skip-=1
        elif t=='label': s.label_depth-=1
        elif t=='form': s.form_depth-=1
        elif t in HEAD and s.cur: s.heads.append((s.cur[0],' '.join(s.cur[1].split()))); s.cur=None
    def handle_data(s,d):
        if s.in_title: s.title+=d
        if s.in_ld: s.ld_buf+=d
        elif s.skip<=0:
            s.text.append(d)
            if s.cur: s.cur[1]+=d
def url_of(path):
    rel=os.path.relpath(path,root).replace(os.sep,'/')
    if rel=='index.html': return bp+'/'
    if rel.endswith('/index.html'): return bp+'/'+rel[:-len('index.html')]
    return bp+'/'+rel
def fs_of(urlpath):
    """map a site path (no base) to a file, or None"""
    if bp and not (urlpath==bp or urlpath.startswith(bp+'/')): return None
    rel=urlpath[len(bp):].lstrip('/')
    cand=os.path.join(root,rel) if rel else root
    if os.path.isdir(cand): return os.path.join(cand,'index.html') if os.path.isfile(os.path.join(cand,'index.html')) else None
    if os.path.isfile(cand): return cand
    return None
docs={}
for p in pages:
    with open(p,encoding='utf-8') as f: raw=f.read()
    ps=P(); ps.feed(raw); docs[p]=(ps,raw)
ids_cache={p:set(d[0].ids) for p,d in docs.items()}
issues=[]; info=[]
def iss(page,msg): issues.append((os.path.relpath(page,root) if page else '-',msg))
titles={}; descs={}; externals={}
for p,(d,raw) in docs.items():
    u=url_of(p); page_url=origin+u; is404=os.path.basename(p)=='404.html'
    if 'http-equiv="refresh"' in raw:   # заглушка-редирект: проверяем только цель
        import re as _re
        m=_re.search(r'url=([^"]+)"', raw); tgt=urllib.parse.urljoin(page_url, m.group(1)) if m else ''
        if not tgt.startswith(origin) or fs_of(urllib.parse.urlparse(tgt).path) is None: iss(p,'redirect target missing: '+tgt)
        else: info.append((u,'redirect -> '+urllib.parse.urlparse(tgt).path))
        continue
    m={ (a.get('name') or a.get('property') or a.get('http-equiv') or ('charset' if 'charset' in a else '')).lower(): a.get('content','') for a in d.metas }
    if d.html_attrs.get('lang')!='ru': iss(p,'html lang != ru: %r'%d.html_attrs.get('lang'))
    if not any('charset' in a for a in d.metas): iss(p,'no meta charset')
    elif raw.find('charset')>1024: iss(p,'meta charset after first 1024 bytes')
    if 'viewport' not in m: iss(p,'no viewport')
    t=' '.join(d.title.split()); titles.setdefault(t,[]).append(u)
    if not t: iss(p,'empty <title>')
    elif len(t)>65: iss(p,'title long (%d): %s'%(len(t),t))
    ds=m.get('description','').strip(); descs.setdefault(ds,[]).append(u)
    if not ds: iss(p,'no meta description')
    elif len(ds)>165: iss(p,'description long (%d)'%len(ds))
    elif len(ds)<70: iss(p,'description short (%d): %s'%(len(ds),ds))
    rob=m.get('robots','')
    can=[a.get('href') for a in d.links if (a.get('rel') or '').lower()=='canonical']
    if not is404:
        if len(can)!=1: iss(p,'canonical count %d'%len(can))
        elif can[0]!=page_url: iss(p,'canonical %s != %s'%(can[0],page_url))
        for k in ('og:title','og:description','og:image','og:url','og:type','og:locale','twitter:card'):
            if k not in m: iss(p,'missing '+k)
        if m.get('og:url') and m.get('og:url')!=page_url: iss(p,'og:url %s != %s'%(m['og:url'],page_url))
        if m.get('og:image'):
            f=fs_of(urllib.parse.urlparse(m['og:image']).path) if m['og:image'].startswith(base) else None
            if not f: iss(p,'og:image not found locally: '+m['og:image'])
    h1=[h for h in d.heads if h[0]=='h1']
    if len(h1)!=1: iss(p,'h1 count %d: %s'%(len(h1),[h[1][:40] for h in h1]))
    prev=1
    for lvl,txt in d.heads:
        n=int(lvl[1])
        if n>prev+1: iss(p,'heading jump h%d -> %s (%s)'%(prev,lvl,txt[:50]))
        prev=n
    for h in d.heads:
        if not h[1]: iss(p,'empty heading '+h[0])
    dup=sorted({i for i in d.ids if d.ids.count(i)>1})
    if dup: iss(p,'duplicate ids: %s'%dup)
    if d.inline: iss(p,'inline on* handlers: %d'%d.inline)
    for ld in d.ld:
        try: data=json.loads(ld)
        except Exception as e: iss(p,'JSON-LD parse error: %s'%e); continue
        nodes=data.get('@graph',[data]) if isinstance(data,dict) else data
        types=[]
        def walk(n):
            if isinstance(n,dict):
                if '@type' in n: types.append(n['@type'] if isinstance(n['@type'],str) else '/'.join(n['@type']))
                for k,v in n.items():
                    if k in ('datePublished','dateModified') and isinstance(v,str):
                        try:
                            dt=datetime.date.fromisoformat(v[:10])
                            if dt>TODAY: iss(p,'%s in future: %s'%(k,v))
                        except Exception: iss(p,'bad date %s=%s'%(k,v))
                    if k in ('url','@id','image','logo','contentUrl') and isinstance(v,str) and v.startswith('http'):
                        if v.startswith(base) and not v.endswith('#') and '#' not in v:
                            if fs_of(urllib.parse.urlparse(v).path) is None and not v.rstrip('/')==base: iss(p,'JSON-LD %s not found: %s'%(k,v))
                        elif not v.startswith(base) and k in ('url','@id'): externals.setdefault(v,set()).add(u)
                    walk(v)
            elif isinstance(n,list):
                for x in n: walk(x)
        walk(nodes); info.append((u,'JSON-LD types: '+', '.join(types)))
    if not d.ld and not is404: iss(p,'no JSON-LD')
    for a in d.a:
        h=a.get('href')
        if h is None: iss(p,'<a> without href'); continue
        if h=='' or h=='#': iss(p,'empty/# href'); continue
        if h.startswith(('mailto:','tel:','javascript:')):
            if h.startswith('tel:') and not re.fullmatch(r'tel:\+7\d{10}',h): iss(p,'tel format: '+h)
            continue
        if a.get('target')=='_blank' and 'noopener' not in (a.get('rel') or ''): iss(p,'target=_blank without noopener: '+h)
        full=urllib.parse.urljoin(page_url,h)
        if full.startswith('http://'): iss(p,'http:// link: '+h)
        if full.startswith(base+'/') or full==base:
            pr=urllib.parse.urlparse(full); f=fs_of(pr.path)
            if f is None: iss(p,'broken internal link: '+h)
            else:
                if pr.fragment and pr.fragment not in ids_cache.get(f,set()): iss(p,'missing anchor #%s in %s'%(pr.fragment,os.path.relpath(f,root)))
                if not pr.path.endswith('/') and os.path.basename(f)=='index.html' and not pr.path.endswith('.html'): iss(p,'link without trailing slash: '+h)
        else: externals.setdefault(full,set()).add(u)
    for im in d.imgs:
        src=im.get('src',''); 
        if 'alt' not in im: iss(p,'img without alt attr: '+src)
        if not (im.get('width') and im.get('height')): iss(p,'img without width/height: '+src)
        for cand in [src]+[c.strip().split(' ')[0] for c in (im.get('srcset') or '').split(',') if c.strip()]:
            if cand and fs_of(urllib.parse.urlparse(urllib.parse.urljoin(page_url,cand)).path) is None: iss(p,'img file missing: '+cand)
        if im.get('srcset') and ' w' in im['srcset'] and not im.get('sizes'): iss(p,'srcset w-descriptors without sizes: '+src)
    for so in d.sources:
        for cand in ([] if 'data:' in (so.get('srcset') or '') else [c.strip().split(' ')[0] for c in (so.get('srcset') or '').split(',') if c.strip()]):
            if fs_of(urllib.parse.urlparse(urllib.parse.urljoin(page_url,cand)).path) is None: iss(p,'source file missing: '+cand)
    for l in d.links:
        h=l.get('href'); rel=(l.get('rel') or '').lower()
        if not h or h.startswith('http') and not h.startswith(base): 
            if h and h.startswith('http'): externals.setdefault(h,set()).add(u)
            continue
        if fs_of(urllib.parse.urlparse(urllib.parse.urljoin(page_url,h)).path) is None: iss(p,'<link rel=%s> file missing: %s'%(rel,h))
        if rel=='stylesheet' and '?v=' not in h: iss(p,'stylesheet without ?v=: '+h)
    for sc in d.scripts:
        s=sc.get('src')
        if not s: continue
        if s.startswith('http') and not s.startswith(base): externals.setdefault(s,set()).add(u); continue
        if fs_of(urllib.parse.urlparse(urllib.parse.urljoin(page_url,s)).path) is None: iss(p,'script missing: '+s)
        if '?v=' not in s: iss(p,'script without ?v=: '+s)
    lab_for={l.get('for') for l in d.labels if l.get('for')}
    for i in d.inputs:
        if i.get('type') in ('hidden','submit','button'): continue
        if not (i.get('id') in lab_for or i.get('aria-label') or i.get('aria-labelledby') or i['_inlabel']): iss(p,'form control without label: %s %s'%(i['_tag'],i.get('name') or i.get('id')))
    for b in d.buttons:
        if b['_inform'] and not b.get('type'): iss(p,'button in form without type')
    txt=''.join(d.text)
    yo=txt.count('ё')+txt.count('Ё')
    if yo and 'policy' not in p: iss(p,'letter ё in text: %d'%yo)
    if d.iframes: info.append((u,'iframes: %d'%len(d.iframes)))
    info.append((u,'robots=%s | title(%d) | desc(%d) | h1=%s'%(rob or '-',len(t),len(ds),h1[0][1][:60] if h1 else '-')))
for t,us in titles.items():
    if len(us)>1: iss(None,'duplicate title %r on %s'%(t,us))
for ds,us in descs.items():
    if len(us)>1 and ds: iss(None,'duplicate description on %s'%us)
# sitemap & robots
sm=os.path.join(root,'sitemap.xml')
if os.path.isfile(sm):
    smx=open(sm,encoding='utf-8').read(); locs=re.findall(r'<loc>(.*?)</loc>',smx)
    want={origin+url_of(p) for p in pages if os.path.basename(p)!='404.html' and 'http-equiv="refresh"' not in docs[p][1] and 'name="robots" content="noindex, follow"' not in docs[p][1]}
    missing=want-set(locs); extra=set(locs)-want
    if missing: iss(None,'pages missing from sitemap: %s'%sorted(missing))
    if extra: iss(None,'sitemap entries without page: %s'%sorted(extra))
    for lm in re.findall(r'<lastmod>(.*?)</lastmod>',smx):
        try: datetime.date.fromisoformat(lm[:10])
        except Exception: iss(None,'bad lastmod '+lm)
    info.append(('sitemap','%d urls, %d with lastmod'%(len(locs),smx.count('<lastmod>'))))
else: iss(None,'no sitemap.xml')
rb=os.path.join(root,'robots.txt')
if os.path.isfile(rb):
    r=open(rb,encoding='utf-8').read(); info.append(('robots',r.strip().replace('\n',' | ')))
    if 'Sitemap:' not in r: iss(None,'robots.txt without Sitemap:')
    if base+'/sitemap.xml' not in r: iss(None,'robots Sitemap url != %s/sitemap.xml'%base)
else: iss(None,'no robots.txt')
for f in ('.nojekyll','404.html','favicon.ico','favicon.svg','apple-touch-icon.png'):
    if not os.path.exists(os.path.join(root,f)): iss(None,'missing root file '+f)
info.append(('root','CNAME present' if os.path.exists(os.path.join(root,'CNAME')) else 'no CNAME'))
mf=[l.get('href') for d,_ in docs.values() for l in d.links if (l.get('rel') or '')=='manifest']
if mf:
    f=fs_of(urllib.parse.urlparse(urllib.parse.urljoin(base+'/',mf[0])).path)
    if f:
        try:
            mj=json.load(open(f,encoding='utf-8')); info.append(('manifest','%s icons=%d start=%s'%(os.path.relpath(f,root),len(mj.get('icons',[])),mj.get('start_url'))))
            for ic in mj.get('icons',[]):
                if fs_of(urllib.parse.urlparse(urllib.parse.urljoin(base+'/',ic.get('src',''))).path) is None: iss(None,'manifest icon missing: '+ic.get('src',''))
        except Exception as e: iss(None,'manifest parse: %s'%e)
else: info.append(('manifest','no manifest link'))
if EXT:
    ctx=ssl.create_default_context()
    for url in sorted(externals):
        try:
            qurl=urllib.parse.quote(url,safe=':/?&=%,#+@')
            req=urllib.request.Request(qurl,method='HEAD',headers={'User-Agent':'Mozilla/5.0 (site-audit)'})
            with urllib.request.urlopen(req,timeout=12,context=ctx) as r: st=r.status
        except urllib.error.HTTPError as e:
            if e.code in (403,405):
                try:
                    req=urllib.request.Request(qurl,headers={'User-Agent':'Mozilla/5.0 (site-audit)'})
                    with urllib.request.urlopen(req,timeout=12,context=ctx) as r: st=r.status
                except Exception as e2: st='ERR %s'%e2
            else: st=e.code
        except Exception as e: st='ERR %s'%e
        info.append(('external','%s -> %s (on %s)'%(url,st,', '.join(sorted(externals[url]))[:80])))
print('== PAGES', len(pages)); 
for u,i in info: print('  [%s] %s'%(u,i))
print('== ISSUES', len(issues))
for pg,msg in issues: print('  %s: %s'%(pg,msg))
