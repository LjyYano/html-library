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


ANKI_STYLE = r'''<style id="anki-tab-style">
.anki-page {--anki-ink:var(--fg,var(--fg1,#282734));--anki-muted:var(--fg-muted,var(--fg2,#696877));--anki-line:var(--line,var(--border,#e6e5ea));--anki-bg:var(--surface,var(--bg-surface,#fafafa));--anki-accent:var(--accent,#7657e9);color:var(--anki-ink);max-width:850px;margin:auto}
.anki-kicker{font-size:11px;font-weight:750;letter-spacing:1.1px;color:var(--anki-accent);margin-bottom:10px}.anki-title{font-size:24px;margin:0 0 9px;font-weight:750;letter-spacing:-.4px;line-height:1.4}
.anki-description{font-size:13px;line-height:1.8;color:var(--anki-muted);margin:0}.anki-hint{font-size:12px;line-height:1.8;color:var(--anki-muted);margin:9px 0 0}
.anki-controls{margin:20px 0 26px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}.anki-export{display:inline-flex;align-items:center;gap:6px;background:var(--anki-bg);color:var(--anki-ink);border:1px solid var(--anki-line);padding:9px 14px;border-radius:8px;font-size:12px;text-decoration:none;font-weight:650}.anki-export:hover{color:var(--anki-accent);border-color:var(--anki-accent)}.anki-count{font-size:12px;color:var(--anki-muted);margin-left:auto}
.anki-cards{display:flex;flex-direction:column;gap:11px}.anki-card{border:1px solid var(--anki-line);border-radius:11px;overflow:hidden}.anki-card summary{list-style:none;cursor:pointer;padding:18px 19px;outline:none}.anki-card summary::-webkit-details-marker{display:none}.anki-card summary:focus-visible{outline:2px solid var(--anki-accent);outline-offset:-2px}.anki-card[open] summary{border-bottom:1px solid var(--anki-line)}.anki-card summary:hover{background:var(--anki-bg)}
.anki-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px}.anki-card-no{font-size:11px;color:var(--anki-accent);font-weight:760}.anki-card-label{font-size:11px;color:var(--anki-muted)}.anki-card summary p{font-size:15px;line-height:1.85;margin:0;color:var(--anki-ink);font-weight:560}.anki-caret{display:inline-block;font-size:12px;color:var(--anki-muted);transition:transform .2s}.anki-card[open] .anki-caret{transform:rotate(180deg)}.anki-context{padding:18px 19px 19px;background:var(--anki-bg)}.anki-context h3{color:var(--anki-muted);font-size:11px;letter-spacing:.4px;font-weight:700;margin:0 0 9px}.anki-context p{font-size:13px;color:var(--anki-muted);line-height:1.9;margin:0}.anki-time{display:block;color:var(--anki-accent);margin-top:12px;font-size:11px;font-variant-numeric:tabular-nums}.anki-bottom-note{color:var(--anki-muted);font-size:11px;line-height:1.85;margin-top:21px}
@media(max-width:700px){.anki-controls{gap:8px}.anki-count{width:100%;margin-left:0}.anki-card summary{padding:15px}.anki-context{padding:15px}.anki-card summary p{font-size:14px}}
</style>'''


def export_anki_files(page_dir: Path, record: dict) -> None:
    cards = record['cards']
    lines = ['# ' + record.get('title', 'Anki 精选原句'), '',
             '> ' + record.get('source_note', ''), '',
             f'> 共 {len(cards)} 张，Basic（正面 / 背面）；忠实摘录，非问答卡。', '']
    tsv_lines = []
    for i, card in enumerate(cards, 1):
        title, front, back, stamp = (str(card[k]).strip() for k in ('title', 'front', 'back', 'time'))
        if not front or not back or not stamp:
            raise ValueError(f'Anki card {i} has an empty field')
        lines += [f'## {i}. {title}', '', '**正面（原句）**', '', '> ' + front, '',
                  '**背面（连续原文上下文）**', '', '> ' + back, '',
                  '*时间：' + stamp + '*', '', '---', '']
        # Two TAB-separated columns, UTF-8, no header. HTML escapes and <br> keep fields in one row.
        to_field = lambda x: html.escape(x, quote=True).replace('\t', ' ').replace('\n', '<br>')
        back_html = f'<div>{to_field(back)}</div><div>时间：{to_field(stamp)}</div>'
        tsv_lines.append(to_field(front) + '\t' + back_html)
    (page_dir / 'anki-cards.md').write_text('\n'.join(lines), encoding='utf-8')
    (page_dir / 'anki-import.tsv').write_text('\n'.join(tsv_lines) + '\n', encoding='utf-8')


def inject_anki(html_doc: str, record: dict, source_path: Path) -> str:
    if 'data-tab="anki"' in html_doc:
        return html_doc
    is_wealth = 'class="tab-list"' in html_doc and 'id="panel-notes"' in html_doc
    is_car = 'id="tabs"' in html_doc and 'data-panel="shownotes"' in html_doc
    if not (is_wealth or is_car):
        raise ValueError(f'{source_path}: anki.json exists but HTML does not use the supported tab layout')
    if is_wealth:
        tab_marker = '        <button type="button" class="tab" data-tab="notes"'
        panel_marker = '    <section class="panel" id="panel-notes"'
        tab = '<button type="button" class="tab" data-tab="anki" role="tab" aria-selected="false"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 10h10M7 14h6"/></svg>Anki</button>'
    else:
        tab_marker = '          <button class="tab" data-tab="shownotes"'
        panel_marker = '      <section class="panel" data-panel="shownotes"'
        tab = '<button class="tab" data-tab="anki"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 10h10M7 14h6"/></svg>Anki</button>'
    cards = record['cards']
    chunks = []
    for i, card in enumerate(cards, 1):
        front, back = html.escape(card['front']), html.escape(card['back'])
        title, tm = html.escape(card['title']), html.escape(card['time'])
        chunks.append(f'''<details class="anki-card"><summary><div class="anki-card-head"><span class="anki-card-no">{i:02d} · {title}</span><span class="anki-caret">⌄</span></div><p>{front}</p></summary><div class="anki-context"><h3>背面 · 连续原文上下文</h3><p>{back}</p><span class="anki-time">{tm}</span></div></details>''')
    section = f'''<section class="panel" id="panel-anki" data-panel="anki" role="tabpanel" aria-label="Anki 原句卡片"><div class="anki-page"><div class="anki-kicker">SPACED REPETITION / 原句卡片</div><h2 class="anki-title">Anki · 精选原句</h2><p class="anki-description">{html.escape(record.get('source_note',''))}</p><p class="anki-hint">正面保留原句，点击卡片查看连续上下文；不采用 AI 问答改写。</p><div class="anki-controls"><a class="anki-export" href="anki-import.tsv" download>↓ 导出 TSV（Basic）</a><a class="anki-export" href="anki-cards.md" download>↓ 导出 Markdown</a><span class="anki-count">精选 {len(cards)} 张</span></div><div class="anki-cards">{''.join(chunks)}</div><p class="anki-bottom-note">导入 Anki：笔记类型选择 Basic，分隔符选择 Tab，第一列正面、第二列背面，并启用 HTML 字段。卡片内容是来源文本摘录，不代表对所述观点进行了事实核验。</p></div></section>'''
    if html_doc.count(tab_marker) != 1 or html_doc.count(panel_marker) != 1:
        raise ValueError(f'{source_path}: Anki injection anchors missing or not unique')
    html_doc = html_doc.replace(tab_marker, tab+'\n'+tab_marker, 1)
    html_doc = html_doc.replace(panel_marker, section+'\n'+panel_marker, 1)
    html_doc = html_doc.replace('</head>', ANKI_STYLE+'\n</head>', 1)
    if is_wealth:
        html_doc = html_doc.replace("['summary','mindmap','keywords','highlights','notes'].includes(hash)", "['summary','mindmap','keywords','highlights','notes','anki'].includes(hash)", 1)
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
        dest.write_text(inject_anki(dest.read_text(encoding='utf-8'), record, src), encoding='utf-8')
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
