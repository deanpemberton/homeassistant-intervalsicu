/* Keep dashboard DOM nodes attached during telemetry refreshes (mobile scroll stability). */
function fantailStableHTML(target, html) {
  html=String(html??'');
  if(target.__fantailHTML===html)return html;
  const template=document.createElement('template');template.innerHTML=html;
  const key=n=>n.nodeType===1?(n.id||n.getAttribute('data-entity')||n.getAttribute('data-id')||n.getAttribute('data-info')||''):'';
  const same=(a,b)=>a&&a.nodeType===b.nodeType&&(a.nodeType!==1||(a.localName===b.localName&&a.namespaceURI===b.namespaceURI&&key(a)===key(b)));
  function sync(parent,wanted){
    let current=parent.firstChild;
    for(const fresh of Array.from(wanted.childNodes)){
      if(!same(current,fresh)){
        const found=key(fresh)?Array.from(parent.childNodes).find(n=>same(n,fresh)):null;
        if(found){parent.insertBefore(found,current);current=found;}
        else {const inserted=fresh.cloneNode(true);parent.insertBefore(inserted,current);continue;}
      }
      if(current.nodeType===1){
        for(const attr of Array.from(current.attributes))if(!fresh.hasAttribute(attr.name)&&!(current.localName==='details'&&attr.name==='open'))current.removeAttribute(attr.name);
        for(const attr of Array.from(fresh.attributes))if(current.getAttribute(attr.name)!==attr.value)current.setAttribute(attr.name,attr.value);
        // Preserve expanded disclosures and live form controls during background updates.
        if(current.localName==='input'&&current.getRootNode().activeElement!==current){current.value=fresh.value;current.checked=fresh.checked;}
        sync(current,fresh);
      }else if(current.nodeValue!==fresh.nodeValue)current.nodeValue=fresh.nodeValue;
      current=current.nextSibling;
    }
    while(current){const next=current.nextSibling;parent.removeChild(current);current=next;}
  }
  sync(target,template.content);target.__fantailHTML=html;return html;
}



const TVSPORTS=[['strength','Strength','#ba9af8'],['swimming','Swimming','#8bc6ff'],['cycling','Cycling','#ffd16d'],['running','Running','#8bf2d4'],['other','Other','#95a5ba']];
const TVESC=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
class FantailTrainingVolume extends HTMLElement{
constructor(){super();this.attachShadow({mode:'open'});this._selected=null;this._signature='';}
setConfig(c){this.config=c;}
set hass(h){this._h=h;if(!this._built)this.build();if(!this.entity&&!this._discovering)this.discover();this.update();}
async discover(){this._discovering=true;try{const r=await this._h.callWS({type:'config/entity_registry/list'});this.athletes=r.filter(e=>e.platform==='intervals_icu'&&e.unique_id?.endsWith('_weekly_training')&&!e.disabled_by);this.entity=this.athletes.find(e=>e.config_entry_id===this.config.entry_id)?.entity_id||this.athletes[0]?.entity_id;this.update();}catch(e){}finally{setTimeout(()=>{this._discovering=false;},30000);}}
build(){this._built=true;this.shadowRoot.innerHTML=`<style>
:host{display:block;color:#edf5ff;font-family:var(--primary-font-family,Arial)}*{box-sizing:border-box}ha-card{background:linear-gradient(145deg,#10243d,#182f4c);border-radius:24px;border:1px solid #355472;padding:26px;color:#edf5ff}.top{display:flex;gap:12px;justify-content:space-between;flex-wrap:wrap}.muted,small{color:#b7c9dc}h1{margin:18px 0 5px;font-size:30px}h2{font-size:18px;margin:0 0 18px}a{color:#8bf2d4;text-decoration:none}.controls{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0}select,button{background:#203c5a;color:#edf5ff;border:1px solid #466788;border-radius:12px;padding:12px;font:inherit;cursor:pointer}.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.tile,.panel{background:#20364f;border:1px solid #365574;border-radius:18px;padding:18px}.tile{border-top:3px solid var(--accent)}.tile strong{display:block;font-size:27px;margin:12px 0}.tile p{margin:6px 0}.panels{display:grid;grid-template-columns:1.25fr 1fr;gap:16px;margin-top:18px}.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;margin-bottom:18px}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}.chart{height:230px;display:flex;align-items:flex-end;gap:9px}.column{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;cursor:pointer}.stack{display:flex;flex-direction:column-reverse;width:100%;max-width:50px;border-radius:5px;overflow:hidden;background:#314b68}.seg{min-height:0}.label{font-size:10px;margin-top:9px;color:#b7c9dc;white-space:nowrap}.barrow{margin:17px 0}.barhead{display:flex;justify-content:space-between;font-size:14px;gap:10px}.track{height:9px;background:#365472;border-radius:10px;margin-top:8px;overflow:hidden}.fill{height:100%;border-radius:10px}.notice{padding:18px;background:#20364f;border-radius:16px;margin-top:20px}.footer{font-size:12px;line-height:1.7;margin-top:20px}.total{font-size:17px;color:#8bf2d4;margin:14px 0}.status{font-size:12px;color:#b7c9dc}@media(max-width:850px){.tiles{grid-template-columns:repeat(2,1fr)}.panels{grid-template-columns:1fr}}@media(max-width:500px){ha-card{padding:16px;border-radius:18px}h1{font-size:25px}.tile{padding:13px}.tile strong{font-size:24px}.chart{gap:5px}.label{font-size:8px}select{max-width:100%}}
</style><ha-card><div class="top"><small>Fantail Family Home · Detail</small><nav><a href="/garmin-health/health">Garmin Health ↗</a> · <a href="/new-home/now">All dashboards ↗</a></nav></div><h1>Weekly training volume</h1><p class="muted">Completed training · Monday–Sunday</p><div class="controls"><select class="athlete" aria-label="Athlete"></select><select class="week" aria-label="Week"></select><button class="refresh">Refresh now</button></div><div class="status"></div><div class="content"></div><div class="footer">Intervals.icu is the source. Strength and swimming include session rests; running and cycling use moving time. Virtual cycling distance is identified separately. Current week is incomplete.</div></ha-card>`;
this.shadowRoot.querySelector('.week').onchange=e=>{this._selected=e.target.value;this._signature='';this.update();};
this.shadowRoot.querySelector('.athlete').onchange=e=>{this.entity=e.target.value;this._selected=null;this._signature='';this.update();};
this.shadowRoot.querySelector('.refresh').onclick=async()=>{if(!this.entity)return;const b=this.shadowRoot.querySelector('.refresh');b.disabled=true;try{await this._h.callService('homeassistant','update_entity',{entity_id:this.entity});}catch(e){this.shadowRoot.querySelector('.status').textContent='Refresh failed. Check the integration connection.';}finally{b.disabled=false;}};
}
update(){if(!this._h||!this._built)return;const s=this._h.states[this.entity],a=s?.attributes,history=a?.history;
const signature=JSON.stringify([this.entity,s?.state,a,this._selected]);if(signature===this._signature)return;this._signature=signature;
const status=this.shadowRoot.querySelector('.status'),content=this.shadowRoot.querySelector('.content');
if(!Array.isArray(history)||!history.length||['unavailable','unknown'].includes(s.state)){status.textContent='Awaiting the weekly-history extension';fantailStableHTML(content,'<div class="notice">The dashboard is ready. Restart Home Assistant to load the fork, then allow its first Intervals refresh. Failed API requests withhold totals rather than showing zeros.</div>');return;}
const athleteSelect=this.shadowRoot.querySelector('.athlete');fantailStableHTML(athleteSelect,(this.athletes||[{entity_id:this.entity}]).map(e=>'<option value="'+TVESC(e.entity_id)+'">'+TVESC(this._h.states[e.entity_id]?.attributes?.athlete_name||e.entity_id)+'</option>').join(''));athleteSelect.value=this.entity;
const chosen=history.find(w=>w.start===this._selected)||history.at(-1);this._selected=chosen.start;const prev=history[history.indexOf(chosen)-1];
const weekSelect=this.shadowRoot.querySelector('.week');fantailStableHTML(weekSelect,[...history].reverse().map(w=>'<option value="'+w.start+'">'+w.start+' – '+w.end+(w.partial?' · so far':'')+'</option>').join(''));weekSelect.value=chosen.start;
status.textContent='Last synced: '+(a.last_synced?new Date(a.last_synced).toLocaleString():'—')+' · '+(a.timezone||'')+' · '+(a.athlete_name||'');
const hours=v=>Number(v||0).toFixed(1),km=v=>Number(v||0).toFixed(1);
const tiles=TVSPORTS.slice(0,4).map(([key,name,color])=>{const v=chosen.sports[key];if(!v)return '';const old=prev?.sports?.[key];const diff=old?Number(v.hours)-Number(old.hours):null;return '<div class="tile" style="--accent:'+color+'"><small>'+name+'</small><strong>'+hours(v.hours)+' h</strong>'+(key==='strength'?'':'<strong>'+km(v.distance_km)+' km</strong>')+'<p>'+v.sessions+' sessions</p><small>'+(chosen.partial?'Week in progress':diff===null?'No prior week':(diff>=0?'+':'')+diff.toFixed(1)+' h vs prior week')+'</small>'+(key==='cycling'&&v.virtual_distance_m?'<p><small>'+km(v.virtual_distance_m/1000)+' km virtual · '+hours(v.indoor_seconds/3600)+' h indoor</small></p>':'')+((v.missing_duration||v.missing_distance)?'<p><small>Some measurements missing</small></p>':'')+'</div>';}).join('');
const maxH=Math.max(1,...history.map(w=>Number(w.hours)||0));
const legend=TVSPORTS.map(([key,name,color])=>'<span><i class="dot" style="background:'+color+'"></i>'+name+'</span>').join('');
const columns=history.map(w=>'<div class="column" data-week="'+w.start+'" title="'+w.start+': '+hours(w.hours)+' hours"><div class="stack" style="height:'+Math.max(1,(Number(w.hours)||0)/maxH*190)+'px;outline:'+(chosen.start===w.start?'2px solid #edf5ff':'none')+'">'+TVSPORTS.map(([key,name,color])=>'<div class="seg" style="background:'+color+';flex:'+Number(w.sports[key]?.hours||0)+'" title="'+name+': '+hours(w.sports[key]?.hours)+' h"></div>').join('')+'</div><span class="label">'+w.start.slice(5)+'</span></div>').join('');
const distances=['running','swimming','cycling'].map(key=>{const [,name,color]=TVSPORTS.find(v=>v[0]===key);const max=Math.max(1,...history.map(w=>Number(w.sports[key]?.distance_km)||0));return '<h2>'+name+' distance</h2>'+history.map(w=>{const n=Number(w.sports[key]?.distance_km)||0;return '<div class="barrow"><div class="barhead"><span>'+w.start+(w.partial?' · so far':'')+'</span><b>'+km(n)+' km</b></div><div class="track"><div class="fill" style="background:'+color+';width:'+n/max*100+'%"></div></div></div>';}).join('');}).join('');
fantailStableHTML(content,'<div class="total">'+hours(chosen.hours)+' total hours · '+chosen.sessions+' sessions'+(chosen.sports.other?.sessions?' · includes '+chosen.sports.other.sessions+' other-sport sessions':'')+'</div><div class="tiles">'+tiles+'</div><div class="panels"><section class="panel"><h2>12 weeks · training hours</h2><div class="legend">'+legend+'</div><div class="chart">'+columns+'</div><p class="muted">Tap a week to inspect its totals. Highest week: '+hours(maxH)+' h.</p></section><section class="panel">'+distances+'</section></div>');
this._signature=JSON.stringify([this.entity,s?.state,a,this._selected]);
content.querySelectorAll('[data-week]').forEach(el=>el.onclick=()=>{this._selected=el.dataset.week;this._signature='';this.update();});
}
getCardSize(){return 12;}
}
if(!customElements.get('fantail-training-volume-v1'))customElements.define('fantail-training-volume-v1',FantailTrainingVolume);
