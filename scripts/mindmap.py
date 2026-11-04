"""The shared mindmap template is the exact car-cost Markmap appearance and config.

Legacy article pages are left unchanged. New pages must supply mindmap.md.
When JSDelivr is unreachable, an interactive SVG fallback retains the same
lavender/dark container styling without changing the online Markmap look.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OLD_ARTICLES = frozenset({
    'ai-code-review-release-workflow', 'car-cost',
    'how-much-to-be-financially-free', 'nobel-expectations', 'wealth-tips',
})

# The following CSS is copied from pages/car-cost/index.html, including
# the original lavender gradient, dark-mode gradient and fixed 680px height.
# Only panel width/padding are adapted to the new reading shell so the canvas
# has the same original 824px usable desktop width.
STYLE = r'''<style id="yano-car-cost-mindmap-style">
#panel-mindmap{max-width:880px;padding:20px 28px 40px}
.mindmap-wrap{
  background:linear-gradient(135deg,#f6f4ff 0%,#edeaff 100%);
  border-radius:var(--radius-md,8px);
  padding:20px 0;
  overflow:hidden;
  height:680px;
  position:relative;
}
[data-theme="dark"] .mindmap-wrap{
  background:linear-gradient(135deg,#16131f 0%,#0f0d18 100%);
}
.mindmap-wrap .markmap{width:100%;height:100%}

/* Full-screen controls; original car-cost canvas and Markmap settings stay unchanged. */
#panel-mindmap .mindmap-fullscreen-btn{
  position:absolute;right:14px;top:14px;z-index:5;
  display:inline-flex;align-items:center;gap:6px;
  background:var(--bg,#fff);color:var(--fg,#37352f);
  border:1px solid var(--line,#e9e9e7);border-radius:6px;
  padding:7px 12px;font-size:12px;font-weight:550;line-height:1.45;
  box-shadow:0 2px 8px #0000000b;cursor:pointer;
}
#panel-mindmap .mindmap-fullscreen-btn:hover{background:var(--surface,#f7f7f5)}
#panel-mindmap .mindmap-fullscreen-btn:focus-visible{outline:2px solid var(--accent,#2383e2);outline-offset:2px}
#panel-mindmap .mindmap-wrap:fullscreen,
#panel-mindmap .mindmap-wrap.is-fullscreen{
  position:fixed!important;inset:0!important;width:100vw!important;
  height:100vh!important;height:100dvh!important;max-height:none!important;
  padding:0!important;margin:0!important;border-radius:0!important;
  z-index:2147483640!important;
}
#panel-mindmap .mindmap-wrap:fullscreen .mindmap-fullscreen-btn,
#panel-mindmap .mindmap-wrap.is-fullscreen .mindmap-fullscreen-btn{
  right:max(18px,env(safe-area-inset-right));
  top:max(18px,env(safe-area-inset-top));
}
body.mindmap-fullscreen-open{overflow:hidden!important}

[data-theme="dark"] .mindmap-wrap .markmap{--markmap-text-color:#ffffff;--markmap-circle-open-bg:#666;--markmap-code-bg:#2a2a2a;--markmap-code-color:#ddd}
@media(max-width:860px){#panel-mindmap{padding:16px 18px 32px}}
</style>'''

# EXACT same three CDN URLs used by car-cost (not pinned to alternate
# versions; those had caused our previous page to show the SVG fallback).
LIBS = '''<script src="https://cdn.jsdelivr.net/npm/d3/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-lib/dist/browser/index.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-view/dist/browser/index.min.js"></script>'''

SCRIPT = r'''<script id="yano-car-cost-mindmap-init">
(() => {
  'use strict';
  const panel = document.querySelector('[data-panel="mindmap"]');
  const svgEl = panel?.querySelector('#markmap-svg');
  const data = document.getElementById('yano-mindmap-data');
  if (!panel || !svgEl || !data) return;
  const MINDMAP_MD = JSON.parse(data.textContent);
  let instance = null, fallback = null, started = false;
  const colors = ['#7c5cfc','#0ea5e9','#f59e0b','#22c55e','#ef4444','#8b5cf6'];
  const wrap = svgEl.closest('.mindmap-wrap');
  const fullscreenBtn = wrap?.querySelector('[data-mindmap-fullscreen]');
  const isFullscreen = () => document.fullscreenElement === wrap || wrap.classList.contains('is-fullscreen');
  function fitAfterResize(){
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!isVisible()) return;
      if(instance) instance.fit();
      else fallback?.fit();
    }));
  }
  function syncFullscreen(){
    const active=isFullscreen();
    if(fullscreenBtn){
      fullscreenBtn.textContent=active?'退出全屏':'全屏';
      fullscreenBtn.setAttribute('aria-label',active?'退出思维导图全屏':'全屏查看思维导图');
      fullscreenBtn.setAttribute('title',active?'退出全屏':'全屏查看思维导图');
      fullscreenBtn.setAttribute('aria-pressed',String(active));
    }
    document.body.classList.toggle('mindmap-fullscreen-open',wrap.classList.contains('is-fullscreen'));
    fitAfterResize();
  }
  async function toggleFullscreen(){
    if(isFullscreen()){
      if(document.fullscreenElement===wrap && document.exitFullscreen){
        try{await document.exitFullscreen()}catch(e){console.warn('退出原生全屏失败',e)}
      }
      wrap.classList.remove('is-fullscreen');
    }else{
      let entered=false;
      if(typeof wrap.requestFullscreen==='function'){
        try{await wrap.requestFullscreen();entered=true}catch(e){/* iOS or restricted browsing context: use CSS overlay. */}
      }
      if(!entered)wrap.classList.add('is-fullscreen');
    }
    syncFullscreen();
  }
  fullscreenBtn?.addEventListener('click', event => {
    event.preventDefault();event.stopPropagation();
    void toggleFullscreen();
  });
  document.addEventListener('fullscreenchange',syncFullscreen);
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape' && wrap.classList.contains('is-fullscreen')){
      wrap.classList.remove('is-fullscreen');syncFullscreen();
    }
  });
  window.addEventListener('resize',()=>{if(isFullscreen())fitAfterResize()});
  function isVisible(){return !panel.hidden && getComputedStyle(panel).display !== 'none';}
  function renderMindmap(){
    if (!isVisible()) return;
    if (started) { if(instance)requestAnimationFrame(()=>instance.fit()); return; }
    started = true;
    try {
      if (window.markmap?.Transformer && window.markmap?.Markmap) {
        // This create() config is taken verbatim from car-cost/index.html.
        const { Transformer, Markmap } = window.markmap;
        const transformer = new Transformer();
        const { root } = transformer.transform(MINDMAP_MD);
        instance = Markmap.create(svgEl, {
          autoFit: true,
          color: (node) => {
            const colors = ['#7c5cfc','#0ea5e9','#f59e0b','#22c55e','#ef4444','#8b5cf6'];
            return colors[node.state?.depth % colors.length] || '#7c5cfc';
          },
          duration: 500,
          maxWidth: 300,
          paddingX: 16,
          scrollForPan: true,
        }, root);
        requestAnimationFrame(() => instance.fit());
        return;
      }
    } catch (error) { console.warn('Markmap failed, using offline SVG map', error); }
    fallback = buildOfflineMap(MINDMAP_MD,svgEl,colors);
  }
  function buildOfflineMap(source, el, palette){
    const NS='http://www.w3.org/2000/svg';
    const node=(tag,attrs,content)=>{
      const e=document.createElementNS(NS,tag);
      for(const [key,value] of Object.entries(attrs||{})) e.setAttribute(key,String(value));
      if(content!==undefined)e.textContent=content;
      return e;
    };
    const stack=[], nodes=[];
    for (const line of source.split(/\r?\n/)) {
      const m=/^(#{1,6})\s+(.+)$/.exec(line.trim());if(!m)continue;
      const n={text:m[2],level:m[1].length,children:[],closed:false};
      while(stack.length&&stack[stack.length-1].level>=n.level)stack.pop();
      if(stack.length)stack[stack.length-1].children.push(n);
      else nodes.push(n);
      stack.push(n);
    }
    if(nodes.length!==1){el.setAttribute('aria-label','思维导图结构无效');return {fit(){},expand(){}};}
    const root=nodes[0]; let view=null, defaultView=null, pointer=null;
    const draw=()=>{
      el.replaceChildren();let leaf=0,maxDepth=0;
      const place=(n,depth,branch)=>{
        n.depth=depth;n.branch=branch;n.x=depth*295+32;
        maxDepth=Math.max(maxDepth,depth);
        const sub=n.closed?[]:n.children;
        sub.forEach((c,i)=>place(c,depth+1,depth===0?i:branch));
        n.y=sub.length?(sub[0].y+sub[sub.length-1].y)/2:leaf++*49+52;
        n.width=Math.min(280,Math.max(100,[...n.text].length*14+20));
      };
      place(root,0,0);
      const height=Math.max(380,leaf*49+100),width=Math.max(890,(maxDepth+1)*295+70);
      defaultView={x:0,y:0,w:width,h:height};
      if(!view)view={...defaultView};
      const edges=node('g',{'fill':'none','stroke-width':2.0,'stroke-opacity':0.7});
      const labels=node('g',{});
      const visit=n=>{
        const color=palette[n.branch%palette.length];
        for(const c of (n.closed?[]:n.children)) {
          const endX=c.x-8,startX=n.x+n.width-8;
          const curve=node('path',{d:`M ${startX} ${n.y+7} C ${startX+68} ${n.y+7}, ${endX-72} ${c.y+7}, ${endX} ${c.y+7}`,stroke:palette[c.branch%palette.length]});
          edges.append(curve);visit(c);
        }
        const g=node('g',{'class':'yano-fallback-node',tabindex:n.children.length?'0':'-1','role':'treeitem'});
        const text=node('text',{x:n.x,y:n.y,'font-weight':n.depth<2?650:450},n.text);
        const underline=node('path',{d:`M ${n.x} ${n.y+7} h ${Math.max(60,n.width-24)}`,stroke:color,'stroke-width':n.depth===0?3:1.7,opacity:0.92});
        g.append(text,underline);
        if(n.children.length){
          const bubble=node('circle',{cx:n.x+n.width-8,cy:n.y+5,r:7,fill:'var(--surface, #f7f7f5)',stroke:color,'stroke-width':1.6});
          const sign=node('text',{x:n.x+n.width-8,y:n.y+9,'text-anchor':'middle','font-size':12,'font-weight':650},n.closed?'+':'−');
          g.append(bubble,sign);
          const toggle=()=>{n.closed=!n.closed;view=null;draw()};
          g.addEventListener('click',e=>{e.stopPropagation();toggle()});
          g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle()}});
        }
        labels.append(g);
      };
      visit(root);el.append(edges,labels);updateView();
    };
    const updateView=()=>{if(view)el.setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`)};
    el.addEventListener('wheel',e=>{
      e.preventDefault();const rect=el.getBoundingClientRect();if(!rect.width||!rect.height)return;
      const px=(e.clientX-rect.left)/rect.width,py=(e.clientY-rect.top)/rect.height;
      const scale=e.deltaY>0?1.16:0.86,ow=view.w,oh=view.h;
      view.w=Math.max(240,Math.min(9000,view.w*scale));view.h=oh*(view.w/ow);
      view.x+=(ow-view.w)*px;view.y+=(oh-view.h)*py;updateView();
    },{passive:false});
    el.addEventListener('pointerdown',e=>{
      if(e.target.closest('.yano-fallback-node'))return;
      pointer={id:e.pointerId,x:e.clientX,y:e.clientY,ox:view.x,oy:view.y};el.setPointerCapture(e.pointerId);
    });
    el.addEventListener('pointermove',e=>{
      if(!pointer||pointer.id!==e.pointerId)return;
      const rect=el.getBoundingClientRect();
      view.x=pointer.ox-(e.clientX-pointer.x)*view.w/rect.width;
      view.y=pointer.oy-(e.clientY-pointer.y)*view.h/rect.height;updateView();
    });
    el.addEventListener('pointerup',()=>{pointer=null});
    el.addEventListener('pointercancel',()=>{pointer=null});
    draw();
    return {fit(){view={...defaultView};updateView()},expand(){
      const walk=n=>{n.closed=false;n.children.forEach(walk)};walk(root);view=null;draw();
    }};
  }
  // The original car-cost initializes at parse end, but the new reading
  // shell defaults to the transcript tab. Initialize on first visible open
  // so Markmap autofit measures the real width instead of a hidden SVG.
  document.addEventListener('click', event => {
    if (event.target.closest('[data-tab="mindmap"]')) setTimeout(renderMindmap,0);
  });
  new MutationObserver(() => {
    if (isVisible()) setTimeout(renderMindmap,0);
  }).observe(panel,{attributes:true,attributeFilter:['hidden','class','style']});
  if (document.readyState==='complete') renderMindmap();
  else window.addEventListener('load',renderMindmap);
})();
</script>'''

def validate_outline(markdown: str, path: Path | str = '<mindmap>') -> None:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if len(lines) < 5 or not lines[0].startswith('# '):
        raise ValueError(f'{path}: mindmap.md must start with # root and include branches')
    prev = roots = branches = 0
    for line in lines:
        found = re.fullmatch(r'(#{1,6})\s+(.+)', line)
        if not found:
            raise ValueError(f'{path}: only Markdown headings are supported: {line[:50]}')
        depth, label = len(found[1]), found[2]
        if depth > prev + 1 or len(label) > 100:
            raise ValueError(f'{path}: invalid hierarchy or long node: {line[:50]}')
        if depth == 1: roots += 1
        if depth == 2: branches += 1
        prev = depth
    if roots != 1 or branches < 2:
        raise ValueError(f'{path}: need one root and at least two level-2 branches')


def inject_mindmap(html_doc: str, markdown: str, path: Path | str = '<page>') -> str:
    validate_outline(markdown, path)
    if 'id="yano-car-cost-mindmap-init"' in html_doc:
        return html_doc

    # Migrate pages already built with the now-removed approximate template.
    # Old custom toolbar/fallback and pinned CDN scripts MUST NOT survive.
    if 'id="yano-shared-mindmap-init"' in html_doc:
        html_doc = re.sub(r'<script\s+id="yano-shared-mindmap-init">.*?</script>\s*','',html_doc,flags=re.S)
        html_doc = re.sub(r'<style\s+id="yano-shared-mindmap-style">.*?</style>\s*','',html_doc,flags=re.S)
        html_doc = re.sub(r'<script\s+defer\s+src="https://cdn\.jsdelivr\.net/npm/(?:d3@7|markmap-lib@0\.18\.12|markmap-view@0\.18\.12)/[^"]+"></script>\s*','',html_doc)

    pattern = re.compile(r'<section\b(?=[^>]*\bdata-panel=["\']mindmap["\'])[^>]*>.*?</section>',re.S|re.I)
    matches = list(pattern.finditer(html_doc))
    if len(matches) != 1:
        raise ValueError(f'{path}: expected exactly one mindmap section, found {len(matches)}')
    original_tag = re.match(r'<section\b[^>]*>',matches[0].group(0),re.I).group(0)
    payload = json.dumps(markdown,ensure_ascii=False).replace('<','\\u003c')
    # The visible subtree below is exactly car-cost's Mindmap markup.
    panel = (original_tag + '<div class="mindmap-wrap"><button type="button" class="mindmap-fullscreen-btn" data-mindmap-fullscreen aria-label="全屏查看思维导图" aria-pressed="false" title="全屏查看思维导图">全屏</button><svg class="markmap" id="markmap-svg"></svg></div>'
             '<script type="application/json" id="yano-mindmap-data">' + payload + '</script>'
             '</section>')
    html_doc = html_doc[:matches[0].start()]+panel+html_doc[matches[0].end():]
    if html_doc.count('</head>')!=1 or html_doc.count('</body>')!=1:
        raise ValueError(f'{path}: HTML head/body insertion anchors missing')
    html_doc=html_doc.replace('</head>',LIBS+'\n'+STYLE+'\n</head>',1)
    html_doc=html_doc.replace('</body>',SCRIPT+'\n</body>',1)
    return html_doc