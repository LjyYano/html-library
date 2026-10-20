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
    now = dt.date.today().isoformat()
    cards = []
    for a in articles:
        tags = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in a["tags"][:3])
        date = html.escape(a["date"] or "未标注日期")
        cards.append(f'''<a class="article-card" href="{html.escape(a["url"], quote=True)}" data-category="{html.escape(a["category"], quote=True)}">
          <div class="card-top"><span class="eyebrow">{html.escape(a["category"])}</span><time>{date}</time></div>
          <h3>{html.escape(a["title"])}</h3>
          <p class="description">{html.escape(a["description"])}</p>
          <div class="card-bottom"><div class="tags">{tags}</div><span class="arrow" aria-hidden="true">↗</span></div>
        </a>''')

    categories = sorted({a["category"] for a in articles})
    cat_buttons = '<button class="chip selected" data-category="all" aria-pressed="true">全部 <span>'+str(len(articles))+'</span></button>'
    cat_buttons += "".join(f'<button class="chip" data-category="{html.escape(c, quote=True)}" aria-pressed="false">{html.escape(c)} <span>{sum(x["category"]==c for x in articles)}</span></button>' for c in categories)
    data = json.dumps(articles, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    return r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#f3f0fc" />
  <meta name="description" content="Yano 的网页阅读书架。收藏 AI 整理的完整文稿、交互式阅读页面和知识笔记。" />
  <title>Yano · 阅读书架</title>
  <style>
    :root { --bg:#f3f0fc; --surface:#fff; --fg:#252239; --muted:#737082; --border:#e7e3ef; --accent:#7252e5; --light:#ede7ff; --line:#eeeaf4; --shadow:0 6px 28px rgba(55,44,99,.055); --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif; }
    [data-theme="dark"]{--bg:#12101a;--surface:#201d2a;--fg:#f1eef9;--muted:#aba6b8;--border:#393348;--accent:#aa92ff;--light:#2f2940;--line:#342e41;--shadow:0 6px 28px rgba(0,0,0,.2)}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font);-webkit-font-smoothing:antialiased}
    body::before{content:"";pointer-events:none;position:fixed;z-index:-1;left:0;right:0;top:0;height:500px;background:radial-gradient(ellipse at 75% 5%,rgba(152,126,245,.16),transparent 61%)}
    a{text-decoration:none;color:inherit}button,input{font:inherit}button{cursor:pointer}
    a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
    .shell{max-width:1240px;margin:0 auto;min-height:100vh;padding:0 28px 64px}
    header{height:88px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
    .identity{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:750;letter-spacing:-.3px}
    .mark{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:var(--accent);box-shadow:0 6px 14px #8369d733;color:white}
    .mark svg{width:20px;height:20px}
    .nav{display:flex;align-items:center;gap:20px;color:var(--muted);font-size:13px;font-weight:550}.nav a:hover{color:var(--accent)}
    .icon-button{display:grid;place-items:center;border:1px solid var(--border);background:var(--surface);border-radius:11px;width:38px;height:38px;color:var(--muted)}
    .icon-button:hover{color:var(--accent)}.icon-button svg{height:17px;width:17px}
    .hero{padding:88px 0 65px;max-width:820px}
    .eyebrow{font-size:12px;font-weight:700;letter-spacing:1.4px;color:var(--accent)}
    .hero h1{font-size:clamp(38px,5.2vw,66px);line-height:1.12;letter-spacing:-2.5px;margin:20px 0 20px;font-weight:800}
    .hero h1 em{color:var(--accent);font-style:normal}
    .hero p{font-size:16px;line-height:1.9;max-width:580px;color:var(--muted);margin:0}
    .collection{background:var(--surface);border:1px solid var(--border);border-radius:22px;box-shadow:var(--shadow);padding:34px 36px 42px}
    .section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:23px}
    .section-head h2{font-size:25px;letter-spacing:-.6px;margin:6px 0 0}.count{font-size:12px;font-weight:600;color:var(--muted)}
    .toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;justify-content:space-between;margin-bottom:24px}
    .search{position:relative;max-width:420px;flex:1;min-width:215px}
    .search svg{width:18px;height:18px;position:absolute;left:15px;top:50%;transform:translateY(-50%);color:var(--muted)}
    .search input{height:44px;width:100%;padding:0 48px 0 43px;border:1px solid var(--border);background:var(--bg);color:var(--fg);border-radius:11px;outline:none;font-size:13px}
    .search input:focus{border-color:var(--accent)}.search kbd{position:absolute;right:12px;top:12px;font:11px var(--font);color:var(--muted);border:1px solid var(--border);border-radius:5px;padding:3px 5px}
    .chips{display:flex;flex-wrap:wrap;gap:7px}
    .chip{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--border);background:transparent;border-radius:9px;color:var(--muted);font-size:12px;padding:9px 12px}
    .chip.selected,.chip:hover{background:var(--light);color:var(--accent);border-color:transparent}.chip span{font-size:11px;opacity:.65}
    .articles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
    .article-card{min-height:230px;border:1px solid var(--border);border-radius:14px;padding:23px 23px 21px;display:flex;flex-direction:column;transition:transform .16s,box-shadow .16s,border-color .16s;background:var(--surface)}
    .article-card[hidden]{display:none}
    .article-card:hover{transform:translateY(-3px);box-shadow:0 12px 32px rgba(90,68,155,.1);border-color:var(--accent)}
    .card-top{display:flex;align-items:center;justify-content:space-between;gap:12px}.card-top .eyebrow{font-size:11px;letter-spacing:.5px}.card-top time{color:var(--muted);font-size:11px;white-space:nowrap}
    h3{font-size:19px;letter-spacing:-.45px;line-height:1.45;margin:18px 0 10px}
    .description{line-height:1.8;font-size:13px;color:var(--muted);margin:0 0 20px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .card-bottom{display:flex;align-items:center;justify-content:space-between;margin-top:auto;gap:12px}.tags{display:flex;flex-wrap:wrap;gap:6px}.tag{font-size:11px;border-radius:6px;padding:4px 8px;background:var(--bg);color:var(--muted)}
    .arrow{color:var(--accent);font-size:23px;line-height:1}
    .empty{display:none;text-align:center;padding:72px 15px;color:var(--muted);font-size:14px}
    footer{display:flex;justify-content:space-between;gap:12px;margin-top:32px;color:var(--muted);font-size:12px}
    footer a{color:var(--accent)}
    @media(max-width:800px){.shell{padding:0 15px 40px}header{height:72px}.nav{gap:12px}.hero{padding:62px 10px 48px}.hero h1{letter-spacing:-1.5px}.hero p{font-size:14px}.collection{padding:24px 17px;border-radius:17px}.section-head h2{font-size:22px}.articles{grid-template-columns:1fr}.article-card{min-height:200px}.toolbar{align-items:stretch}.search{max-width:none;flex-basis:100%}}
  </style>
</head>
<body>
<div class="shell">
  <header>
    <a class="identity" href="./" aria-label="返回阅读书架首页">
      <span class="mark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 6 9-3 9 3v14l-9-3-9 3V6Z"/><path d="m12 3 0 14"/></svg></span>
      <span>Yano <span style="color:var(--accent)">/</span> Library</span>
    </a>
    <nav class="nav">
      <a href="https://yano.blog" rel="noopener" target="_blank">Blog ↗</a>
      <a href="https://weekly.yano.blog" rel="noopener" target="_blank">Weekly ↗</a>
      <button id="theme-btn" class="icon-button" aria-label="切换深浅色模式" title="切换主题"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M20.4 15.5A8.7 8.7 0 0 1 8.5 3.6 8.8 8.8 0 1 0 20.4 15.5Z"/></svg></button>
    </nav>
  </header>
  <section class="hero">
    <span class="eyebrow">DIGITAL READING COLLECTION</span>
    <h1>收藏思考，<br><em>沉淀时间。</em></h1>
    <p>给值得反复阅读的内容，一个长期存放的地方。完整文稿、深度整理与交互式页面，随时打开，继续思考。</p>
  </section>
  <main class="collection">
    <div class="section-head"><div><span class="eyebrow">LIBRARY</span><h2>阅读档案</h2></div><span class="count" id="result-count">__TOTAL__ 篇文章</span></div>
    <div class="toolbar">
      <label class="search" aria-label="搜索阅读档案"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.4-4.4"/></svg><input id="q" type="search" placeholder="搜索标题、简介、标签..." autocomplete="off"><kbd>⌘ K</kbd></label>
      <div class="chips" id="categories">__CATEGORIES__</div>
    </div>
    <div class="articles" id="articles">__CARDS__</div>
    <div class="empty" id="empty">没有找到匹配内容，试试其他关键词。</div>
  </main>
  <footer><span>© Yano · HTML Library</span><span>Built with GitHub Pages · <a href="https://github.com/LjyYano" target="_blank" rel="noopener">GitHub ↗</a></span></footer>
</div>
<script>
const ARTICLES = __DATA__;
const cards = [...document.querySelectorAll('.article-card')];
const search = document.getElementById('q');
const buttons = [...document.querySelectorAll('.chip')];
const count = document.getElementById('result-count');
let category = 'all';
function filter() {
 const query = search.value.trim().toLocaleLowerCase();
 let shown = 0;
 cards.forEach((card, index) => {
  const a = ARTICLES[index];
  const haystack = [a.title, a.description, a.category, a.source, ...a.tags].join(' ').toLocaleLowerCase();
  const visible = (category === 'all' || a.category === category) && (!query || haystack.includes(query));
  card.hidden = !visible;
  if (visible) shown++;
 });
 count.textContent = shown + ' / ' + ARTICLES.length + ' 篇文章';
 document.getElementById('empty').style.display = shown ? 'none' : 'block';
}
buttons.forEach(button => button.addEventListener('click', () => {
 category = button.dataset.category;
 buttons.forEach(b => {b.classList.toggle('selected', b===button);b.setAttribute('aria-pressed', b===button ? 'true' : 'false');});
 filter();
}));
search.addEventListener('input',filter);
document.addEventListener('keydown', e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();search.focus();}});
const theme = localStorage.getItem('yano-library-theme') || 'light';
document.documentElement.setAttribute('data-theme',theme);
document.getElementById('theme-btn').addEventListener('click',()=>{
 const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light':'dark';
 document.documentElement.setAttribute('data-theme',next);
 localStorage.setItem('yano-library-theme',next);
});
filter();
</script>
</body>
</html>
'''.replace("__TOTAL__",str(len(articles))).replace("__CATEGORIES__",cat_buttons).replace("__CARDS__","\n".join(cards)).replace("__DATA__",data)


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    # Preserve all originals and their local assets without modifying HTML content.
    shutil.copytree(PAGES, DIST, dirs_exist_ok=True, ignore=shutil.ignore_patterns("article.json"))
    files = sorted(p for p in PAGES.rglob("*.html") if p.is_file())
    articles = [parse_article(p) for p in files]
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
