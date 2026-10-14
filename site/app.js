'use strict';
const $ = id => document.getElementById(id);
const categories = {world:'全球',politics:'政治',economy:'经济金融',technology:'科技 / AI',asia:'亚洲',energy:'能源',trade:'贸易供应链'};
let items=[], filtered=[], shown=60, data;
const el=(tag,text,className)=>{const n=document.createElement(tag);n.textContent=text;if(className)n.className=className;return n;};
function safeLink(url){try{const u=new URL(url);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}}
function sourceLink(n){const a=el('a',n.source.startsWith('BBC ')?n.source.replace('BBC ','BBC News · '):n.source,'source-link');a.href=safeLink(n.url)||'#';a.target='_blank';a.rel='noopener noreferrer';return a;}
function render(){const q=$('search').value.trim().toLowerCase(),cat=$('category').value,country=$('country').value;
 filtered=items.filter(n=>(!cat||n.category===cat)&&(!country||(country==='unknown'?!n.countries.length&&!n.regions.length:[...n.countries,...n.regions].includes(country)))&&(!q||[n.title,n.source,...n.countries,...n.regions].join(' ').toLowerCase().includes(q)));
 $('count').textContent=`${filtered.length} 条`; $('news').replaceChildren();
 for(const n of filtered.slice(0,shown)){const article=el('article','','article'),meta=el('div','','meta');meta.append(el('span',categories[n.category]||n.category,'tag'),sourceLink(n),el('time',new Date(n.published_at).toLocaleString('zh-CN')));article.append(meta);const a=el('a',n.title);a.href=safeLink(n.url)||'#';a.target='_blank';a.rel='noopener noreferrer';article.append(a,el('div',[...n.countries,...n.regions].join(' · ')||'位置未确定','places'));$('news').append(article);}
 if(!filtered.length)$('news').append(el('p','没有符合条件的新闻。','empty'));
 $('more').hidden=filtered.length<=shown;draw();
}
for(const id of ['search','category','country'])$(id).addEventListener('input',()=>{shown=60;render();});
$('clear').onclick=()=>{for(const id of ['search','category','country'])$(id).value='';shown=60;render();};
$('more').onclick=()=>{shown+=60;render();};
const canvas=$('globe'),ctx=canvas.getContext('2d');let yaw=110,pitch=12,zoom=1,markers=[];
// Bundled Natural Earth 1:110m coastlines, public domain. No map service.
let land=[];
fetch('assets/land.json').then(r=>{if(!r.ok)throw new Error('Land unavailable');return r.json();}).then(outlines=>{land=outlines;draw();}).catch(()=>{$('mapped').textContent='海岸线读取失败';});
function project(lat,lon){const a=lat*Math.PI/180,b=(lon-yaw)*Math.PI/180,p=pitch*Math.PI/180;const x=Math.cos(a)*Math.sin(b), y=Math.sin(a)*Math.cos(p)-Math.cos(a)*Math.cos(b)*Math.sin(p),z=Math.sin(a)*Math.sin(p)+Math.cos(a)*Math.cos(b)*Math.cos(p);return {x:cx+x*radius,y:cy-y*radius,z};}
let cx=0,cy=0,radius=0;
function line(coords,color,width=1){ctx.beginPath();let open=false;for(const [lat,lon] of coords){const p=project(lat,lon);if(p.z<0){open=false;continue;}if(open)ctx.lineTo(p.x,p.y);else ctx.moveTo(p.x,p.y);open=true;}ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}
function draw(){const rect=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(rect.width*dpr);canvas.height=Math.round(rect.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);cx=rect.width/2;cy=rect.height/2;radius=Math.min(cx,cy)*.83*zoom;ctx.clearRect(0,0,rect.width,rect.height);const g=ctx.createRadialGradient(cx-radius*.4,cy-radius*.4,0,cx,cy,radius);g.addColorStop(0,'#142f43');g.addColorStop(1,'#0a1726');ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,radius,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#386076';ctx.stroke();ctx.save();ctx.clip();for(let lat=-60;lat<=60;lat+=30)line(Array.from({length:181},(_,i)=>[lat,i*2-180]),'#244355');for(let lon=-180;lon<180;lon+=30)line(Array.from({length:91},(_,i)=>[i*2-90,lon]),'#244355');for(const poly of land)line(poly.map(([lon,lat])=>[lat,lon]),'#6a9c9e',1.5);ctx.restore();const groups=new Map();for(const n of filtered){if(n.location){const l=n.location;const v=groups.get(l.label)||{...l,count:0};v.count++;groups.set(l.label,v);}}markers=[];for(const l of groups.values()){const p=project(l.lat,l.lon);if(p.z<.05)continue;ctx.fillStyle='#61e8d0';ctx.beginPath();ctx.arc(p.x,p.y,4+Math.min(4,Math.log2(l.count+1)),0,Math.PI*2);ctx.fill();ctx.fillStyle='#c7e2e7';ctx.font='10px -apple-system, sans-serif';ctx.fillText(rect.width>400?`${l.label} · ${l.count}`:String(l.count),p.x+10,p.y-7);markers.push({...p,label:l.label});}$('mapped').textContent=`${groups.size} 个国家参考标记`;}
let drag=null;
canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,ox:e.clientX,oy:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.moved||=Math.hypot(e.clientX-drag.ox,e.clientY-drag.oy)>5;yaw-=dx*.5;pitch=Math.max(-70,Math.min(70,pitch+dy*.4));drag.x=e.clientX;drag.y=e.clientY;draw();});
canvas.addEventListener('pointerup',e=>{if(drag&&!drag.moved){const r=canvas.getBoundingClientRect(),hit=markers.find(p=>Math.hypot(p.x-(e.clientX-r.left),p.y-(e.clientY-r.top))<16);if(hit){$('country').value=hit.label;shown=60;render();}}drag=null;});canvas.addEventListener('pointercancel',()=>{drag=null;});
canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();yaw+=e.key==='ArrowLeft'?-10:e.key==='ArrowRight'?10:0;pitch=Math.max(-70,Math.min(70,pitch+(e.key==='ArrowUp'?10:e.key==='ArrowDown'?-10:0)));draw();});
$('left').onclick=()=>{yaw-=20;draw();};$('right').onclick=()=>{yaw+=20;draw();};$('zoomOut').onclick=()=>{zoom=Math.max(.65,zoom-.1);draw();};$('zoomIn').onclick=()=>{zoom=Math.min(1.15,zoom+.1);draw();};$('reset').onclick=()=>{yaw=110;pitch=12;zoom=1;draw();};window.addEventListener('resize',draw);draw();
(async()=>{try{const response=await fetch('data/news.json',{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);data=await response.json();items=data.items;
 const success=data.sources.filter(s=>s.ok).length;const age=data.last_success_at?Date.now()-Date.parse(data.last_success_at):Infinity;
 $('health').textContent=`${age>86400000?'数据已过期 · ':''}${data.status==='ok'?'运行正常':data.status==='partial'?'部分来源失败':'采集失败'} · ${success}/${data.sources.length} 来源可用`;
 $('updated').textContent=`最近尝试 ${new Date(data.updated_at).toLocaleString('zh-CN')} · 最近成功 ${data.last_success_at?new Date(data.last_success_at).toLocaleString('zh-CN'):'尚无'}`;
 for(const [key,label] of Object.entries(categories)){const stat=el('div','','stat');stat.append(el('span',label),el('strong',items.filter(n=>n.category===key).length));$('stats').append(stat);const option=el('option',label);option.value=key;$('category').append(option);}
 for(const country of [...new Set(items.flatMap(n=>[...n.countries,...n.regions]))].sort()){const option=el('option',country);option.value=country;$('country').append(option);}
 for(const s of data.sources){const li=el('li',`${s.ok?'●':'○'} ${s.name} · ${s.ok?s.count+' 条':s.error}`,s.ok?'ok':'bad');$('sources').append(li);}render();
 }catch(error){$('health').textContent='数据读取失败';$('news').append(el('p','请通过本地 HTTP 服务访问，或检查数据文件。'+error.message,'empty'));}})();
