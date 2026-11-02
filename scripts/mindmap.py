"""Standard Markmap-style mindmaps for reading pages (Markdown -> interactive SVG).

The page uses the same Markmap engine as car-cost when CDN assets are available,
and a dependency-free interactive SVG fallback for local/offline reading.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OLD_ARTICLES = frozenset({
    'ai-code-review-release-workflow', 'car-cost',
    'how-much-to-be-financially-free', 'nobel-expectations', 'wealth-tips',
})

STYLE = r'''<style id="yano-shared-mindmap-style">
.yano-mindmap-inner{max-width:1000px!important}
.yano-map-heading{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin:0 0 13px}
.yano-map-heading h2{font-size:21px;font-weight:690;margin:0}
.yano-map-actions{display:flex;gap:8px;align-items:center}
.yano-map-actions button{font:inherit;font-size:12px;color:var(--fg,var(--fg1,#37352f));background:transparent;border:1px solid var(--line,var(--border,#e9e9e7));border-radius:5px;padding:6px 12px;cursor:pointer}
.yano-map-actions button:hover{background:var(--surface,var(--bg-surface,#f7f7f5))}
.yano-map-stage{position:relative;overflow:hidden;height:620px;min-height:380px;background:var(--surface,var(--bg-surface,#f7f7f5));border:1px solid var(--line,var(--border,#e9e9e7));border-radius:8px}
.yano-map-stage>svg{width:100%;height:100%;display:block;touch-action:none;cursor:grab}
.yano-map-stage>svg:active{cursor:grabbing}
.yano-map-caption{color:var(--muted,var(--fg-muted,#787774));font-size:11px;margin:11px 0 0}
.yano-map-stage .markmap{--markmap-text-color:var(--fg,var(--fg1,#37352f));--markmap-circle-open-bg:#9b9a97}
[data-theme="dark"] .yano-map-stage .markmap{--markmap-text-color:#e5e5e5;--markmap-circle-open-bg:#aaa}
.yano-map-stage .yano-fallback-node text{fill:var(--fg,var(--fg1,#37352f));font-size:14px;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans CJK SC',sans-serif}
.yano-map-stage .yano-fallback-node{cursor:pointer}
@media(max-width:760px){.yano-map-stage{height:520px;min-height:350px}.yano-map-heading h2{font-size:19px}.yano-map-actions button{font-size:11px;padding:6px 9px}}
</style>'''

# These are the same Markmap browser libraries used by car-cost, pinned for stability.
LIBS = '''<script defer src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/markmap-lib@0.18.12/dist/browser/index.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/markmap-view@0.18.12/dist/browser/index.min.js"></script>'''

SCRIPT = r'''<script id="yano-shared-mindmap-init">
(() => {
  'use strict';
  const panel = document.querySelector('[data-panel="mindmap"]');
  const svg = panel?.querySelector('#markmap-svg');
  const data = document.getElementById('yano-mindmap-data');
  if (!panel || !svg || !data) return;
  const md = JSON.parse(data.textContent);
  const colors = ['#7c5cfc','#0ea5e9','#f59e0b','#22c55e','#ef4444','#8b5cf6'];
  let markmap = null, markmapRoot = null, fallback = null, started = false;
  const fitButton = panel.querySelector('[data-mindmap-fit]');
  const expandButton = panel.querySelector('[data-mindmap-expand]');
  function visible(){return !panel.hidden && getComputedStyle(panel).display !== 'none';}
  function fit(){if(markmap) markmap.fit(); else fallback?.fit();}
  function expand(){
    if (markmap && markmapRoot) {
      markmap.setData(markmapRoot,{initialExpandLevel:20}).then(() => markmap.fit());
    } else if (fallback) fallback.expand();
  }
  fitButton?.addEventListener('click',fit);
  expandButton?.addEventListener('click',expand);
  function init(){
    if (!visible()) return;
    if (started){window.requestAnimationFrame(fit);return;}
    started = true;
    try {
      if (window.markmap?.Transformer && window.markmap?.Markmap) {
        const {root} = new window.markmap.Transformer().transform(md);
        markmapRoot = root;
        markmap = window.markmap.Markmap.create(svg, {
          autoFit:false, duration:250, maxWidth:285, paddingX:16,
          initialExpandLevel:3, scrollForPan:true,
          color:node=>colors[Math.max(0,(node.state?.depth||1)-1)%colors.length]
        }, root);
        window.requestAnimationFrame(() => markmap.fit());
        return;
      }
    } catch (err) {console.warn('Markmap unavailable; using offline SVG fallback',err);}
    fallback = buildOfflineMap(md,svg,colors);
  }
  // Local-file reading still has a complete interactive SVG without CDNs.
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
      const n={text:m[2],level:m[1].length,children:[],closed:m[1].length>=3};
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
  // This is initialized only after its tab is displayed (a hidden SVG has zero size).
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-tab="mindmap"]'))setTimeout(init,0);
  });
  const watcher=new MutationObserver(()=>{if(visible())setTimeout(init,0)});
  watcher.observe(panel,{attributes:true,attributeFilter:['hidden','class','style']});
  window.addEventListener('load',init);
  if(document.readyState==='complete')init();
})();
</script>'''


def validate_outline(markdown: str, path: Path | str = '<mindmap>') -> None:
    lines=[line.strip() for line in markdown.splitlines() if line.strip()]
    if len(lines)<5 or not lines[0].startswith('# '):
        raise ValueError(f'{path}: mindmap.md must start with # root and include branches')
    prev=0;roots=0;branches=0
    for line in lines:
        found=re.fullmatch(r'(#{1,6})\s+(.+)',line)
        if not found:
            raise ValueError(f'{path}: only Markdown headings are supported: {line[:50]}')
        depth=len(found[1]); label=found[2]
        if depth>prev+1 or len(label)>100:
            raise ValueError(f'{path}: invalid hierarchy or long node: {line[:50]}')
        if depth==1:roots+=1
        if depth==2:branches+=1
        prev=depth
    if roots!=1 or branches<2:
        raise ValueError(f'{path}: need one root and at least two level-2 branches')


def inject_mindmap(html_doc: str, markdown: str, path: Path | str = '<page>') -> str:
    validate_outline(markdown, path)
    if 'id="yano-shared-mindmap-init"' in html_doc:
        return html_doc
    pattern=re.compile(r'<section\b(?=[^>]*\bdata-panel=["\']mindmap["\'])[^>]*>.*?</section>',re.S|re.I)
    matches=list(pattern.finditer(html_doc))
    if len(matches)!=1:
        raise ValueError(f'{path}: expected exactly one mindmap section, found {len(matches)}')
    original_tag=re.match(r'<section\b[^>]*>',matches[0].group(0),re.I).group(0)
    # Preserve existing tab state, ARIA and visibility attributes.
    payload=json.dumps(markdown,ensure_ascii=False).replace('<','\\u003c')
    panel=(original_tag+'<div class="panel-inner yano-mindmap-inner">'
           '<div class="yano-map-heading"><h2>思维导图</h2><div class="yano-map-actions">'
           '<button type="button" data-mindmap-fit>适应屏幕</button>'
           '<button type="button" data-mindmap-expand>全部展开</button></div></div>'
           '<div class="yano-map-stage"><svg class="markmap" id="markmap-svg" role="img" aria-label="交互式树状思维导图"></svg></div>'
           '<p class="yano-map-caption">点击节点展开或收起；拖动平移，滚轮或触控板缩放。</p>'
           f'<script type="application/json" id="yano-mindmap-data">{payload}</script>'
           '</div></section>')
    html_doc=html_doc[:matches[0].start()]+panel+html_doc[matches[0].end():]
    if html_doc.count('</head>')!=1 or html_doc.count('</body>')!=1:
        raise ValueError(f'{path}: HTML head/body insertion anchors missing')
    html_doc=html_doc.replace('</head>',LIBS+'\n'+STYLE+'\n</head>',1)
    html_doc=html_doc.replace('</body>',SCRIPT+'\n</body>',1)
    return html_doc