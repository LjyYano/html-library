#!/usr/bin/env python3
"""Generate a zero-dependency HTML bookshelf for GitHub Pages.

Put standalone HTML files anywhere under pages/. Optional article.json in the
same directory as index.html (or a <filename>.json beside a standalone .html)
overrides title, description, category, tags, and date.  Run:

    python3 scripts/build.py
"""
from __future__ import annotations

import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
DIST = ROOT / "dist"
SITE_NAME = "Yano · 阅读书架"
DEFAULT_DESCRIPTION = "收藏值得反复阅读的网页与知识卡片。"


class HTMLMetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.in_title = False
        self.description = ""

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "meta" and attr.get("name", "").lower() == "description":
            self.description = attr.get("content", "")

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self):
        return "".join(self.title_parts).strip()


def parse_article(f: Path) -> dict:
    parser = HTMLMetaParser()
    parser.feed(f.read_text(encoding="utf-8-sig", errors="replace"))
    relative = f.relative_to(PAGES).as_posix()
    meta_path = f.parent / "article.json" if f.name == "index.html" else f.with_suffix(".json")
    metadata = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else {}
    title = str(metadata.get("title") or parser.title or f.stem)
    description = str(metadata.get("description") or parser.description or DEFAULT_DESCRIPTION)
    category = str(metadata.get("category") or "未分类")
    tags = metadata.get("tags", [])
    tags = [str(x) for x in tags] if isinstance(tags, list) else []
    date = str(metadata.get("date") or "")
    if date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"{meta_path}: date must be YYYY-MM-DD")
    if date:
        dt.date.fromisoformat(date)
    url = relative[:-10] if relative.endswith("index.html") else relative
    return {
        "title": title,
        "description": description,
        "category": category,
        "tags": tags,
        "date": date,
        "source": str(metadata.get("source") or ""),
        "url": url,
    }


def render_home(articles: list[dict]) -> str:
    # Notion-like database table: one article per row, no banner or cards.
    rows = []
    for a in articles:
        tags = ''.join(f'<span class="tag">{html.escape(tag)}</span>' for tag in a['tags'][:4])
        date = html.escape(a['date'] or '—')
        desc = html.escape(a['description'], quote=True)
        href = html.escape(a['url'], quote=True)
        rows.append(f'''<tr class="record" tabindex="0" data-href="{href}">
          <td class="name-cell"><a class="document-link" href="{href}" title="{desc}"><svg class="doc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.45" aria-hidden="true"><path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v6h5M9 13h6M9 17h6"/></svg><span>{html.escape(a['title'])}</span></a></td>
          <td class="category-cell"><span class="category">{html.escape(a['category'])}</span></td>
          <td class="tags-cell"><div class="tag-set">{tags}</div></td>
          <td><span class="date">{date}</span></td>
        </tr>''')
    data = json.dumps(articles, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="description" content="Yano 的网页阅读书架。完整文稿、知识笔记与 Anki 原句卡片。" />
<meta name="theme-color" content="#ffffff" />
<title>阅读书架 · Yano</title>
<style>
:root {--bg:#fff;--fg:#37352f;--fg-muted:#9b9a97;--fg-secondary:#787774;--line:#e9e9e7;--hover:#f7f7f5;--search:#f7f7f5;--link:#37352f;--tag-bg:#f1f1ef;--tag-fg:#60605e;--select:#edf4ff;--accent:#2383e2;--font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif}
[data-theme="dark"] {--bg:#191919;--fg:#e3e3e1;--fg-muted:#999992;--fg-secondary:#aaa9a3;--line:#333330;--hover:#262626;--search:#252525;--link:#e3e3e1;--tag-bg:#33332f;--tag-fg:#c7c7bd;--select:#1e3447;--accent:#70aff0}
*{box-sizing:border-box}html{font-family:var(--font);-webkit-font-smoothing:antialiased}body{background:var(--bg);color:var(--fg);margin:0;font-size:14px;min-height:100vh}a{color:inherit;text-decoration:none}button,input{font:inherit}button{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible,tr:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.main{max-width:1160px;margin:0 auto;padding:46px 44px 100px}
.top{display:flex;align-items:center;justify-content:space-between;padding-bottom:32px}.brand{font-size:13px;font-weight:620;color:var(--fg-secondary);display:flex;align-items:center;gap:9px}.brand a:hover{color:var(--fg)}.brand .sep{color:var(--fg-muted)}.right-links{display:flex;align-items:center;gap:20px;font-size:12px;color:var(--fg-secondary)}.right-links a:hover{color:var(--fg)}
.theme{border:0;background:transparent;color:var(--fg-muted);display:flex;align-items:center;gap:4px;padding:5px 6px;border-radius:6px}.theme:hover{background:var(--hover);color:var(--fg)}.theme svg{height:16px;width:16px}
.header{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:13px 0 21px}
h1{font-size:28px;font-weight:725;line-height:1.3;letter-spacing:-.6px;margin:0}.count{color:var(--fg-muted);font-size:12px;margin-left:8px;font-weight:400}.tools{display:flex;gap:8px;align-items:center}.searchbox{display:flex;align-items:center;gap:7px;border:1px solid transparent;background:var(--search);border-radius:6px;padding:7px 10px;width:225px;max-width:40vw;color:var(--fg-secondary)}.searchbox:focus-within{border-color:var(--line)}.searchbox svg{height:15px;width:15px;flex-shrink:0}.searchbox input{border:0;outline:none;min-width:0;width:100%;background:transparent;color:var(--fg);font-size:12px}.searchbox input::placeholder{color:var(--fg-muted)}
.table-scroll{width:100%;overflow-x:auto}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:13px}thead th{color:var(--fg-secondary);font-size:12px;font-weight:450;text-align:left;padding:9px 12px;height:39px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);border-right:1px solid var(--line)}thead th:first-child{padding-left:9px}thead th:last-child{border-right:0}tbody td{height:43px;padding:7px 12px;vertical-align:middle;border-bottom:1px solid var(--line);border-right:1px solid var(--line);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}tbody td:first-child{padding-left:9px}tbody td:last-child{border-right:0}tbody tr:hover{background:var(--hover);cursor:pointer}tbody tr[hidden]{display:none}.name-col{width:46%}.category-col{width:16%}.tag-col{width:24%}.date-col{width:14%}
.document-link{display:flex;align-items:center;gap:8px;color:var(--link);font-size:13.5px;min-width:0}.document-link>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.doc-icon{height:17px;width:17px;flex-shrink:0;color:var(--fg-muted)}.record:hover .document-link>span{text-decoration:underline;text-decoration-color:#a8a8a4;text-underline-offset:2px}
.category{display:inline-flex;align-items:center;background:#e8f0fc;color:#3a6d9c;border-radius:4px;padding:2px 7px;font-size:11.5px;max-width:100%;overflow:hidden;text-overflow:ellipsis}[data-theme="dark"] .category{background:#23364a;color:#a3c4f4}.tag-set{display:flex;flex-wrap:nowrap;gap:5px;overflow:hidden}.tag{background:var(--tag-bg);color:var(--tag-fg);border-radius:4px;padding:2px 7px;font-size:11.5px;white-space:nowrap}.date{font-size:12px;color:var(--fg-secondary);font-variant-numeric:tabular-nums}
.empty{color:var(--fg-muted);padding:34px 8px;font-size:13px;display:none} .footer{margin-top:16px;color:var(--fg-muted);font-size:11px}
@media (max-width:750px){.main{padding:20px 18px 55px}.top{padding-bottom:28px}.right-links{gap:10px}.header{flex-direction:column;align-items:stretch;gap:15px}h1{font-size:25px}.searchbox{width:100%;max-width:none}.tools{width:100%}.name-col{width:64%}.date-col{width:36%}.category-col,.tag-col,th.category-header,th.tag-header,td.category-cell,td.tags-cell{display:none}.record td.name-cell{white-space:normal}.document-link>span{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.footer{font-size:11px}}
</style>
</head>
<body>
<main class="main">
  <nav class="top"><div class="brand"><a href="https://yano.blog" target="_blank" rel="noopener">Yano</a><span class="sep">/</span><span>阅读书架</span></div><div class="right-links"><a href="https://yano.blog" target="_blank" rel="noopener">博客 ↗</a><a href="https://weekly.yano.blog" target="_blank" rel="noopener">周刊 ↗</a><button type="button" class="theme" id="theme-switch" aria-label="切换深浅色"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 15.7A8.4 8.4 0 0 1 8.3 4 8.5 8.5 0 1 0 20 15.7Z" /></svg></button></div></nav>
  <div class="header"><h1>阅读书架 <span class="count" id="article-count">__TOTAL__</span></h1><div class="tools"><label class="searchbox"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m16 16 4 4"/></svg><input id="search" type="search" placeholder="搜索文章..." aria-label="搜索文章" autocomplete="off"/></label></div></div>
  <div class="table-scroll"><table aria-label="阅读文章表"><colgroup><col class="name-col"/><col class="category-col"/><col class="tag-col"/><col class="date-col"/></colgroup><thead><tr><th>名称</th><th class="category-header">分类</th><th class="tag-header">标签</th><th>日期</th></tr></thead><tbody id="table-body">__ROWS__</tbody></table></div>
  <div class="empty" id="empty">没有找到匹配的文章</div>
  <div class="footer" id="result-count">共 __TOTAL__ 篇</div>
</main>
<script>
const ARTICLES=__DATA__;
const rows=[...document.querySelectorAll('tr.record')];
const search=document.querySelector('#search');
function filter(){const q=search.value.trim().toLocaleLowerCase();let matched=0;rows.forEach((row,i)=>{const a=ARTICLES[i];const haystack=[a.title,a.description,a.category,a.source,...a.tags].join(' ').toLocaleLowerCase();const visible=!q||haystack.includes(q);row.hidden=!visible;if(visible)matched++});document.getElementById('empty').style.display=matched?'none':'block';document.getElementById('article-count').textContent=matched;document.getElementById('result-count').textContent='共 '+matched+' 篇';}
search.addEventListener('input',filter);
rows.forEach(row=>{row.addEventListener('click',e=>{if(!e.target.closest('a'))location.href=row.dataset.href});row.addEventListener('keydown',e=>{if(e.key==='Enter')location.href=row.dataset.href});});
document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();search.focus()}});
try{const pref=localStorage.getItem('yano-library-theme');if(pref==='dark')document.documentElement.dataset.theme='dark'}catch(e){}
document.getElementById('theme-switch').addEventListener('click',()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem('yano-library-theme',next)}catch(e){}});
filter();
</script>
</body></html>'''
    return (template.replace('__TOTAL__', str(len(articles)))
                    .replace('__ROWS__', '\n'.join(rows))
                    .replace('__DATA__', data))




# Shared, quiet Notion-style reading typography (applied only to known layouts).
NOTION_WEALTH_CSS = r'''<style id="notion-reading-theme">
:root{--bg:#fff;--card:#fff;--sidebar:#f7f7f5;--surface:#f7f7f5;--chip:#efefed;--fg:#37352f;--fg-muted:#787774;--fg-soft:#9b9a97;--line:#e9e9e7;--accent:#2383e2;--accent-strong:#1e6cbd;--accent-subtle:#edf4ff;--shadow:none;--shadow-lg:0 8px 28px #00000020;--article-size:16px;--radius:0;--font:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif}
[data-theme="dark"]{--bg:#191919;--card:#191919;--sidebar:#202020;--surface:#252525;--chip:#2c2c2c;--fg:#e4e4e2;--fg-muted:#aaa9a4;--fg-soft:#8c8b86;--line:#343434;--accent:#70aff0;--accent-strong:#89bded;--accent-subtle:#273a4c;--shadow:none}
body{background:var(--bg)}.page-wrap{max-width:1050px;margin:0 auto 30px;padding:0 23px}.site-card{border:0;box-shadow:none;border-radius:0}
.sidebar{padding-top:23px}.brand-icon{background:#ecebea;color:#55534e;box-shadow:none;border-radius:6px}[data-theme="dark"] .brand-icon{background:#333;color:#ddd}
.nav-kicker{font-size:11px;letter-spacing:0;font-weight:500}.primary-nav button{border-radius:5px;font-weight:500}.primary-nav button.active{background:var(--chip);color:var(--fg);font-weight:670}.toc-link{border-radius:5px}.toc-link.is-current{background:var(--chip);color:var(--fg)}.sidebar-status{display:none}
.hero{padding:50px 46px 27px;gap:0;border-bottom:0}.cover{display:none}.hero-eyebrow,.hero-description{display:none}.hero h1{font-size:32px;line-height:1.35;letter-spacing:-.035em;font-weight:730;margin:0 0 10px}.hero-footer{font-size:12px;color:var(--fg-muted);gap:12px}.hero-footer a{color:var(--fg-muted);font-weight:500}.hero-footer a:hover{color:var(--accent)}
.tabbar{padding:0 34px;border-top:1px solid var(--line);box-shadow:none}.tab-list{gap:8px}.tab{font-size:13px;padding:14px 11px 13px}.tab.active{font-weight:660;color:var(--fg);border-color:var(--fg)}
.panel{padding:31px 46px 64px}.panel-kicker{display:none}.panel-title{font-weight:730;font-size:24px}.panel-intro{display:none}
.article-toolbar{border-bottom:0;margin-bottom:22px;padding:0}.searchbox{background:var(--surface);border-color:transparent;border-radius:6px}.action,.font-control{border-radius:6px}.article-stats{display:none}
.article-body{max-width:760px;line-height:1.92;letter-spacing:0;font-weight:400}.article-body .article-title-original{display:none}.article-body h2{font-size:24px;line-height:1.4;margin:47px 0 18px;letter-spacing:-.025em;font-weight:730}.article-body h3{font-size:19px;line-height:1.45;margin:32px 0 17px;font-weight:680}.article-body p{margin-bottom:18px;line-height:1.92}.article-body strong{font-weight:700}
.article-body .notion-red{color:#d44b40;font-weight:680}.article-body .notion-callout{display:flex;gap:12px;align-items:flex-start;margin:23px 0 25px;padding:17px 19px;border-radius:5px;background:#f7f7f5;border:0}.article-body .notion-callout.warning{background:#fff6e5}[data-theme="dark"] .article-body .notion-callout{background:#292929}[data-theme="dark"] .article-body .notion-callout.warning{background:#342d21}
.notion-callout-icon{font-size:19px;line-height:1.6;flex:0 0 24px}.notion-callout-content{flex:1;min-width:0}.article-body .notion-callout p{margin:0;line-height:1.85}.article-body .notion-callout strong{font-weight:700}
.summary-hero{background:var(--surface);border:0;border-radius:6px}.summary-hero .eyebrow{color:var(--fg-muted)}.mistake,.milestone,.notes-callout{border-radius:6px;background:var(--surface)}.keyword-chip{border-radius:6px}.quote-card{border-radius:6px}.map-root{background:#4779ac;box-shadow:none;border-radius:7px}.mindmap-stage{border-radius:6px;background:var(--surface)}
.mobile-article-toc{background:var(--surface);border-radius:6px}
@media(max-width:850px){.page-wrap{margin:0 auto 25px;padding:0 9px}.hero{padding:30px 24px 20px}.hero h1{font-size:25px}.tabbar{padding:0 13px}.panel{padding:27px 24px 43px}.article-body h2{font-size:22px}.article-body h3{font-size:19px}}
@media(max-width:620px){.hero{padding:27px 16px 18px}.hero h1{font-size:23px}.panel{padding:22px 16px 38px}.article-body p{margin-bottom:17px}.article-body .notion-callout{padding:14px 13px;gap:9px}}
</style>'''

NOTION_CAR_CSS = r'''<style id="notion-reading-theme">
:root{--bg:#fff;--bg-card:#fff;--bg-sidebar:#f7f7f5;--bg-surface:#f7f7f5;--bg-hover:#efefed;--bg-press:#e9e9e7;--bg-chip:#f1f1ef;--border:#e9e9e7;--border-subtle:#eee;--fg1:#37352f;--fg2:#787774;--fg3:#9b9a97;--accent:#2383e2;--accent-hover:#1d6cba;--accent-subtle:#edf4ff;--shadow-md:none;--shadow-lg:0 8px 20px #00000015;--font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif}
[data-theme="dark"]{--bg:#191919;--bg-card:#191919;--bg-sidebar:#202020;--bg-surface:#262626;--bg-hover:#303030;--bg-press:#363636;--bg-chip:#333;--border:#343434;--border-subtle:#343434;--fg1:#e4e4e2;--fg2:#a4a39e;--fg3:#777;--accent:#70aff0;--accent-subtle:#273b4d;--shadow-md:none}
.app{background:var(--bg)}.sidebar{padding-top:22px}.logo{padding-bottom:23px}.logo-mark span{background:var(--fg2)}.nav-item{border-radius:5px}.nav-item.active{background:var(--bg-press)}.mini-player{display:none}.prev-next,.layout-toggle{display:none}
.content-card{width:100%;max-width:990px;margin:0 auto;border:0;box-shadow:none;border-radius:0}.episode-header{border-bottom:0;padding:50px 45px 30px}.episode-row{gap:0}.episode-cover{display:none}.episode-title{font-size:32px;letter-spacing:-.035em;font-weight:730;line-height:1.35}.meta-line{margin-bottom:12px}.podcast-row{margin:0}.podcast-name{font-size:12px;color:var(--fg2)}
.tabbar{padding:0 30px;border-top:1px solid var(--border)}.tab{font-size:13px;padding:14px 12px}.tab.active{color:var(--fg1);font-weight:700;border-color:var(--fg1)}
.panel{padding:32px 45px 54px}.section-title{letter-spacing:0;text-transform:none;font-size:12px}.summary-body,.shownotes p{font-size:15px;line-height:1.9}.highlight,.tip-box,.personal-thoughts{border-radius:6px}
.search-bar{background:var(--bg-surface);border:1px solid transparent;border-radius:6px;max-width:540px}.turn{padding:23px 0 26px;margin:0;border-bottom:1px solid var(--border)}.turn-head{gap:11px;align-items:center;margin-bottom:11px}.turn-ts{font-size:11px;color:var(--fg3)}.turn-topic{font-size:17px;letter-spacing:-.2px;color:var(--fg1);font-weight:700}.turn-body{font-size:15.5px;line-height:1.92;color:var(--fg1);padding:0;border-left:0;white-space:normal}.turn.active .turn-body{border-left:0}.turn-divider{display:none}.turn[data-i="5"] .turn-body{background:var(--bg-surface);padding:17px 20px;border-radius:5px}.notion-red{font-weight:680;color:#d44b40}.notion-strong{font-weight:700;color:var(--fg1)}
.tweaks-trigger{border-radius:9px}.tweaks{border-radius:9px}
@media(max-width:860px){.episode-header{padding:26px 22px 24px}.episode-title{font-size:24px}.panel{padding:22px 20px 40px}.tabbar{padding:0 10px}.turn{padding:20px 0}.turn-body{font-size:15px}.turn-topic{font-size:16px}}
</style>'''

NOTION_CAR_JS = r'''<script id="notion-car-transcript-enhancer">
(() => {
  const list = document.getElementById('transcript-list');
  if (!list) return;
  const red = [
    '买一辆20万的车会让财务自由推迟多久',
    '真正决定你晚几年的，是你选多贵的车',
    '拿某一年25%的收益去规划后面几十年',
    '上班能不能自由，不看工资多高，看储蓄率能不能过三成',
    '换车金这条批评是对的',
    '47岁自由，你还有21年健康的自由时间',
    '从10万升级到20万',
    '愿意为它多上几年班'
  ];
  const strong = [
    '晚了9.2年', '光是买车加上每十年换一次车',
    '3%不是悲观', '财务自由不是一个固定数字',
    '推迟时间从9.2年降到8.6年', '56岁才自由，只剩12年',
    '买什么档次', '小城市电车大约晚七年'
  ];
  const decorateText = (holder, phrases) => {
    const walker = document.createTreeWalker(holder, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) {
      if (node.parentElement?.closest('mark, .notion-red, .notion-strong')) continue;
      nodes.push(node);
    }
    nodes.forEach(textNode => {
      const value = textNode.nodeValue;
      const found = phrases.filter(p => value.includes(p.text)).map(p => ({...p, start:value.indexOf(p.text)}));
      if (!found.length) return;
      found.sort((a,b) => a.start - b.start || b.text.length - a.text.length);
      const frag=document.createDocumentFragment();
      let offset=0;
      for (const f of found) {
        if (f.start < offset) continue;
        frag.append(document.createTextNode(value.slice(offset,f.start)));
        const el = document.createElement(f.cls==='notion-red'?'strong':'strong');
        el.className=f.cls;
        el.textContent=f.text;
        frag.append(el);
        offset=f.start+f.text.length;
      }
      frag.append(document.createTextNode(value.slice(offset)));
      textNode.replaceWith(frag);
    });
  };
  function refresh() {
    [...list.querySelectorAll('.turn')].forEach(turn => {
      if (turn.dataset.notionEnhanced === 'yes') return;
      turn.dataset.notionEnhanced='yes';
      const i=Number(turn.dataset.i);
      const head=turn.querySelector('.turn-head');
      if (head && typeof OUTLINES !== 'undefined' && OUTLINES[i]) {
        const title=document.createElement('strong');
        title.className='turn-topic';
        title.textContent=OUTLINES[i].text;
        head.append(title);
      }
      const body=turn.querySelector('.turn-body');
      if (body) decorateText(body,[{text:red[i],cls:'notion-red'},{text:strong[i],cls:'notion-strong'}].filter(x=>x.text));
    });
  }
  new MutationObserver(refresh).observe(list,{childList:true});
  refresh();
})();
</script>'''

# Select few original paragraphs for Notion callouts. Text remains untouched.
WEALTH_CALLOUTS = (
    ('风是你的工资，洋流是积累的资产所产生的被动收入', 'idea', '💡'),
    ('当然，这是一个高度简化的数学模型', 'warning', '⚠'),
    ('数学模型的价值不是消除不确定性', 'idea', '💡'),
    ('不作为本身也是一种投资决策', 'idea', '📌'),
)
WEALTH_RED_WORDS = (
    '工作是财富积累的手段，而不是人生的目的',
    '可定价、可变现、可被动增值',
    '原始积累虽然困难，但并非遥不可及',
    '数学模型的价值不是消除不确定性',
    '不作为本身也是一种投资决策',
    '复利最大的优势来自时间',
)


def polish_document(html_doc: str, source_path: Path) -> str:
    is_wealth = 'class="tab-list"' in html_doc and 'id="panel-transcript"' in html_doc
    is_car = 'id="tabs"' in html_doc and 'data-panel="transcript"' in html_doc
    if is_wealth:
        # Presentation-only metadata, counters, and instructional descriptions; never remove article text.
        html_doc = re.sub(r'<div class="article-stats">.*?</div>', '', html_doc, count=1, flags=re.S)
        html_doc = re.sub(r'<span>约 [\d,]+ 字 · \d+ 个自然段</span>', '', html_doc, count=1)
        html_doc = re.sub(r'<footer class="article-footer">.*?</footer>', '', html_doc, count=1, flags=re.S)
        html_doc = re.sub(r'<p class="map-note">.*?</p>', '', html_doc, count=1, flags=re.S)
        html_doc = re.sub(r'<p class="fine-print">.*?</p>', '', html_doc, count=1, flags=re.S)
        html_doc = re.sub(r'<p class="panel-intro[^"]*">.*?</p>', '', html_doc, flags=re.S)
        html_doc = re.sub(r'<span class="quote-no">\d+ / \d+</span>', '', html_doc)
        html_doc = html_doc.replace('>全文可搜索</span>', '></span>').replace("'全文可搜索'", "''")
        html_doc = html_doc.replace('>完整文字版</span>', '></span>')
        html_doc = html_doc.replace('<small>点击下方目录可直达全文</small>', '')
        html_doc = html_doc.replace('<small>5 个主要章节</small>', '')
        # One paragraph, one original block: replacing only its markup, never text.
        ptag = re.compile(r'<p class="reading-paragraph" data-searchable="true">.*?</p>', re.S)
        counts={k:0 for k,_,_ in WEALTH_CALLOUTS}
        def paragraph_style(m):
            original=m.group(0)
            for key in WEALTH_RED_WORDS:
                if key in original:
                    original = original.replace(key, f'<span class="notion-red">{key}</span>')
            for key,kind,icon in WEALTH_CALLOUTS:
                if key in original:
                    counts[key]+=1
                    return (f'<aside class="notion-callout {kind}"><span class="notion-callout-icon" aria-hidden="true">{icon}</span>'
                            f'<div class="notion-callout-content">{original}</div></aside>')
            return original
        html_doc=ptag.sub(paragraph_style,html_doc)
        # Reproduce requested callouts, but keep compatibility with new articles missing specific paragraphs.
        if not all(v == 1 for v in counts.values()):
            print(f'[notice] {source_path}: callouts found {counts}')
        html_doc=html_doc.replace('</head>', NOTION_WEALTH_CSS+'\n</head>',1)
        return html_doc
    if is_car:
        html_doc=html_doc.replace('placeholder="Search transcript…"','placeholder="搜索文稿…"')
        for english,chinese in [('Summary','摘要'),('Mindmap','思维导图'),('Transcript','完整文稿'),('Keywords','关键词'),('Highlights','金句'),('Shownotes','笔记')]:
            html_doc=re.sub(r'(?<![a-zA-Z])'+english+r'(?=\s*</button>)',chinese,html_doc)
        html_doc=html_doc.replace('7 highlights · tap to save','精选金句')
        html_doc=html_doc.replace('Keywords mentioned in this episode','关键词')
        html_doc=html_doc.replace('</head>', NOTION_CAR_CSS+'\n</head>',1)
        html_doc=html_doc.replace('</body>', NOTION_CAR_JS+'\n</body>',1)
        return html_doc
    return html_doc


def stylize_quote(text: str, card: dict, mode: str = 'html') -> str:
    # Crucial: this only inserts style tags around exact substrings; it never changes the quote.
    decorations = []
    for kind in ('bold','red'):
        for phrase in card.get(kind,[]):
            if not isinstance(phrase,str) or not phrase:continue
            start=text.find(phrase)
            if start >= 0:
                decorations.append((start,start+len(phrase),kind))
    if not decorations:
        return html.escape(text,quote=True) if mode=='html' else text
    # Overlay markup by source character position so overlapping red/bold stays valid HTML.
    boundaries = sorted({0,len(text),*(pos for a,b,_ in decorations for pos in (a,b))})
    out=[]
    for left,right in zip(boundaries,boundaries[1:]):
        if left==right: continue
        state={kind for a,b,kind in decorations if a<=left and right<=b}
        part=html.escape(text[left:right],quote=True) if mode=='html' else text[left:right]
        if mode=='html':
            if 'red' in state:
                part=f'<strong style="color:#d44b40;font-weight:700">{part}</strong>'
            elif 'bold' in state:
                part=f'<strong>{part}</strong>'
        elif mode=='markdown':
            if 'red' in state:
                part=f'<span style="color:#d44b40;font-weight:700">{part}</span>'
            elif 'bold' in state:
                part=f'**{part}**'
        out.append(part)
    return ''.join(out)


ANKI_STYLE = r'''<style id="anki-tab-style">
.anki-page{--anki-ink:var(--fg,var(--fg1,#37352f));--anki-muted:var(--fg-muted,var(--fg2,#787774));--anki-line:var(--line,var(--border,#e9e9e7));--anki-bg:var(--surface,var(--bg-surface,#f7f7f5));--anki-accent:var(--accent,#2383e2);max-width:770px;margin:0 auto;color:var(--anki-ink)}
.anki-title{font-size:26px;line-height:1.35;font-weight:750;margin:4px 0 19px;letter-spacing:-.035em;color:var(--anki-ink)}
.anki-controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:28px}
.anki-export,.anki-copy-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;font-size:12px;font-weight:550;border:1px solid var(--anki-line);color:var(--anki-muted);background:transparent;border-radius:6px;padding:7px 11px;line-height:1.3;text-decoration:none;cursor:pointer;transition:background .14s,color .14s}
.anki-export:hover,.anki-copy-btn:hover{background:var(--anki-bg);color:var(--anki-ink)}.anki-copy-btn:focus-visible{outline:2px solid var(--anki-accent);outline-offset:2px}
.anki-copy-btn{white-space:nowrap;font-size:11.5px;padding:6px 10px}.anki-copy-btn svg{height:13px;width:13px;fill:none;stroke:currentColor;stroke-width:1.8}
.anki-cards{display:flex;flex-direction:column;gap:12px}
.anki-card{border:1px solid var(--anki-line);border-radius:7px;overflow:hidden;background:transparent}
.anki-card>summary{list-style:none;cursor:pointer;padding:20px 20px 19px}.anki-card>summary::-webkit-details-marker{display:none}.anki-card>summary:focus-visible{outline:2px solid var(--anki-accent);outline-offset:-2px}.anki-card>summary:hover{background:var(--anki-bg)}.anki-card[open]>summary{border-bottom:1px solid var(--anki-line)}
.anki-card-head{display:flex;justify-content:space-between;gap:14px;align-items:center;margin-bottom:13px}.anki-card-no{font-size:12px;color:var(--anki-muted);font-weight:570}.anki-card-actions{display:flex;align-items:center;gap:11px;margin-left:auto}
.anki-caret{color:var(--anki-muted);font-size:13px;transition:transform .18s}.anki-card[open] .anki-caret{transform:rotate(180deg)}
.anki-front{font-size:16px;line-height:1.9;color:var(--anki-ink);font-weight:450;margin:0}.anki-front strong,.anki-back strong{font-weight:700}.anki-front strong[style],.anki-back strong[style]{color:#d44b40!important}
.anki-context{padding:17px 20px 19px;background:var(--anki-bg)}.anki-back-head{display:flex;align-items:center;justify-content:space-between;gap:12px;color:var(--anki-muted);margin-bottom:11px}.anki-back-head h3{font-size:12px;font-weight:610;letter-spacing:0;margin:0}.anki-back{font-size:14px;line-height:1.95;color:var(--anki-ink);margin:0}.anki-time{display:block;color:var(--anki-muted);font-size:11px;margin-top:15px}
@media(max-width:700px){.anki-title{font-size:23px}.anki-card>summary{padding:15px}.anki-card-head{gap:8px}.anki-card-actions{gap:7px}.anki-front{font-size:15px}.anki-context{padding:15px}.anki-back{font-size:13.5px}}
</style>'''


def export_anki_files(page_dir: Path, record: dict) -> None:
    cards = record['cards']
    lines = ['# ' + record.get('title', 'Anki 精选原句'), '']
    tsv_lines = []
    for i, card in enumerate(cards, 1):
        title, front, back, stamp = (str(card[k]).strip() for k in ('title', 'front', 'back', 'time'))
        if not front or not back or not stamp:
            raise ValueError(f'Anki card {i} has an empty field')
        for mark in card.get('bold',[]) + card.get('red',[]):
            if mark not in front and mark not in back:
                raise ValueError(f'Anki card {i}: style fragment not found in original quoted text: {mark}')
        lines += [f'## {i}. {title}', '', '**正面**', '', '> ' + stylize_quote(front,card,'markdown'), '',
                  '**背面**', '', '> ' + stylize_quote(back,card,'markdown'), '',
                  '*时间：' + stamp + '*', '', '---', '']
        to_field = lambda x: x.replace('\t',' ').replace('\n','<br>')
        front_html=to_field(stylize_quote(front,card,'html'))
        back_html=to_field(stylize_quote(back,card,'html'))
        tsv_lines.append(front_html + '\t' + '<div>' + back_html + '</div><div style="color:#787774;font-size:12px">时间：'+html.escape(stamp)+'</div>')
    (page_dir / 'anki-cards.md').write_text('\n'.join(lines), encoding='utf-8')
    (page_dir / 'anki-import.tsv').write_text('\n'.join(tsv_lines) + '\n', encoding='utf-8')


ANKI_COPY_JS = r'''<script id="anki-rich-clipboard">
(() => {
  async function copyRich(fragment, text) {
    // HTML + text/plain payloads. Anki editor receives inline red/bold formatting.
    const rich = '<div style="font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Arial,sans-serif;font-size:15px;line-height:1.8;color:#37352f">'+fragment+'</div>';
    if (navigator.clipboard && window.ClipboardItem && window.isSecureContext) {
      try {
        const clip = new ClipboardItem({'text/html':new Blob([rich],{type:'text/html'}),'text/plain':new Blob([text],{type:'text/plain'})});
        await navigator.clipboard.write([clip]);
        return 'rich';
      } catch (e) { /* Next try legacy rich-copy fallback. */ }
    }
    const scratch=document.createElement('div');
    scratch.contentEditable='true';
    scratch.style.cssText='position:fixed;left:-10000px;top:0;opacity:0;';
    scratch.innerHTML=rich;
    document.body.append(scratch);
    const range=document.createRange(); range.selectNodeContents(scratch);
    const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range);
    let copied=false;
    try {copied=document.execCommand('copy')} catch(e){}
    sel.removeAllRanges();scratch.remove();
    if (copied) return 'rich';
    if (navigator.clipboard?.writeText) {await navigator.clipboard.writeText(text);return 'plain'}
    throw new Error('clipboard not available');
  }
  document.querySelectorAll('.anki-copy-btn').forEach(btn => {
    btn.addEventListener('click', async (event) => {
      event.preventDefault();event.stopPropagation();
      const card=btn.closest('.anki-card');
      const front=btn.dataset.copySide==='front';
      const node=card.querySelector(front?'.anki-front':'.anki-back');
      if(!node)return;
      const stamp=card.querySelector('.anki-time')?.textContent||'';
      const html=node.innerHTML+(front?'':'<div style="font-size:12px;color:#787774;margin-top:10px">时间：'+stamp+'</div>');
      const plain=node.textContent+(front?'':'\n时间：'+stamp);
      const label=btn.innerHTML;
      try {
        const mode=await copyRich(html,plain);
        btn.textContent=mode==='rich'?'已复制（含格式）':'已复制文字';
      } catch(e) {btn.textContent='复制失败';}
      window.setTimeout(()=>{btn.innerHTML=label},1600);
    });
  });
})();
</script>'''


def inject_anki(html_doc: str, record: dict, source_path: Path) -> str:
    if 'data-tab="anki"' in html_doc:
        return html_doc
    is_wealth = 'class="tab-list"' in html_doc and 'id="panel-notes"' in html_doc
    is_car = 'id="tabs"' in html_doc and 'data-panel="shownotes"' in html_doc
    if not (is_wealth or is_car):
        raise ValueError(f'{source_path}: anki.json exists but HTML does not use a supported tab layout')
    if is_wealth:
        tab_marker = '        <button type="button" class="tab" data-tab="notes"'
        panel_marker = '    <section class="panel" id="panel-notes"'
        tab = '<button type="button" class="tab" data-tab="anki" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 10h10M7 14h6"/></svg>Anki</button>'
    else:
        tab_marker = '          <button class="tab" data-tab="shownotes"'
        panel_marker = '      <section class="panel" data-panel="shownotes"'
        tab = '<button class="tab" data-tab="anki"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 10h10M7 14h6"/></svg>Anki</button>'
    chunks = []
    copy_icon='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>'
    for i, card in enumerate(record['cards'], 1):
        front, back = stylize_quote(card['front'],card), stylize_quote(card['back'],card)
        title, tm = html.escape(card['title']), html.escape(card['time'])
        chunks.append(f'''<details class="anki-card"><summary><div class="anki-card-head"><span class="anki-card-no">{i:02d} / {title}</span><span class="anki-card-actions"><button type="button" class="anki-copy-btn" data-copy-side="front" aria-label="复制第 {i} 张卡片正面">{copy_icon}复制正面</button><span class="anki-caret">⌄</span></span></div><p class="anki-front">{front}</p></summary><div class="anki-context"><div class="anki-back-head"><h3>上下文</h3><button type="button" class="anki-copy-btn" data-copy-side="back" aria-label="复制第 {i} 张卡片背面">{copy_icon}复制背面</button></div><p class="anki-back">{back}</p><span class="anki-time">{tm}</span></div></details>''')
    section=f'''<section class="panel" id="panel-anki" data-panel="anki" role="tabpanel" aria-label="Anki 卡片"><div class="anki-page"><h2 class="anki-title">Anki</h2><div class="anki-controls"><a class="anki-export" href="anki-import.tsv" download>↓ 导出 TSV</a><a class="anki-export" href="anki-cards.md" download>↓ 导出 Markdown</a></div><div class="anki-cards">{''.join(chunks)}</div></div></section>'''
    if html_doc.count(tab_marker) != 1 or html_doc.count(panel_marker) != 1:
        raise ValueError(f'{source_path}: Anki insertion anchors missing or not unique')
    html_doc = html_doc.replace(tab_marker, tab+'\n'+tab_marker, 1)
    html_doc = html_doc.replace(panel_marker, section+'\n'+panel_marker, 1)
    html_doc = html_doc.replace('</head>', ANKI_STYLE+'\n</head>', 1)
    html_doc = html_doc.replace('</body>', ANKI_COPY_JS+'\n</body>', 1)
    if is_wealth:
        html_doc=html_doc.replace("['summary','mindmap','keywords','highlights','notes'].includes(hash)","['summary','mindmap','keywords','highlights','notes','anki'].includes(hash)",1)
    return html_doc
def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    # Preserve all originals and their local assets without modifying HTML content.
    shutil.copytree(PAGES, DIST, dirs_exist_ok=True, ignore=shutil.ignore_patterns("article.json", "anki.json"))
    files = sorted(p for p in PAGES.rglob("*.html") if p.is_file())
    articles = [parse_article(p) for p in files]
    for src, article in zip(files, articles):
        card_path = src.parent / 'anki.json' if src.name == 'index.html' else src.with_suffix('.anki.json')
        if not card_path.exists():
            article['anki_count'] = 0
            continue
        record = json.loads(card_path.read_text(encoding='utf-8'))
        if not isinstance(record.get('cards'), list) or not record['cards']:
            raise ValueError(f'{card_path}: expected a nonempty cards array')
        article['anki_count'] = len(record['cards'])
        dest = DIST / src.relative_to(PAGES)
        export_anki_files(dest.parent, record)
        polished = polish_document(dest.read_text(encoding='utf-8'), src)
        dest.write_text(inject_anki(polished, record, src), encoding='utf-8')
    articles.sort(key=lambda a: (a["date"], a["title"]), reverse=True)
    (DIST / "index.html").write_text(render_home(articles), encoding="utf-8")
    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, DIST / "CNAME")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    (DIST / "articles.json").write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(articles)} article(s) in {DIST}")
    for article in articles:
        print(f" - {article['title']} -> /{article['url']}")


if __name__ == "__main__":
    main()
