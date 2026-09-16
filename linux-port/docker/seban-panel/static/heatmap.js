(() => {
  const map = document.getElementById('heatmap');
  if (!map) return;
  const mapSelect = document.getElementById('heat-map'), typeSelect = document.getElementById('heat-kind');
  const captions = {21:'Chunjo M1',23:'Chunjo M2',24:'Chunjo M3 — Waryong',25:'Kolay Maymun Zindanı',61:'Sohan Dağı',64:'Ork Vadisi',63:'Yongbi Çölü',104:'Örümcek Zindanı V1',108:'Orta Maymun Zindanı',109:'Zor Maymun Zindanı',65:'Hwang Tapınağı',71:'Örümcek Zindanı V2',4:'Shinsoo M3 — Jungrang',44:'Jinno M3 — Imha',5:'Shinsoo Maymun Zindanı',45:'Jinno Maymun Zindanı',1:'Shinsoo M1 — Yongan',3:'Shinsoo M2 — Jayang',41:'Jinno M1 — Pyongmoo',43:'Jinno M2 — Bakra',67:'Orman',68:'Kızıl Orman',66:'Şeytan Kulesi'};
  const backgrounds = {21:'chunjo-m1',23:'chunjo-m2',24:'guild-map-02',25:'easy-monkey',61:'mount-sohan',64:'orc-valley',63:'yongbi-desert',104:'spider-dungeon-v1',108:'medium-monkey',109:'hard-monkey',65:'hwang-temple',71:'spider-dungeon-v1',4:'shinsoo-guild',44:'jinno-guild',5:'easy-monkey',45:'easy-monkey',1:'shinsoo-m1',3:'shinsoo-m2',41:'jinno-m1',43:'jinno-m2',67:'trent-forest',68:'trent02-red-forest',66:'deviltower'};
  async function render(){
    const data = await fetch('/api/heat-events?type='+encodeURIComponent(typeSelect.value),{cache:'no-store'}).then(r=>r.json());
    const index=Number(mapSelect.value), bound=data.bounds[String(index)]||data.bounds[index];
    const extension = (index === 108 || index === 109) ? 'webp' : 'png';
    map.dataset.mapIndex=String(index); map.style.backgroundImage=`linear-gradient(#00000030,#00000030),url('/static/maps/${backgrounds[index]}.${extension}')`;
    map.querySelectorAll('.heat-point').forEach(e=>e.remove());
    const events=data.events.filter(e=>e.map_index===index); document.getElementById('heat-count').textContent=events.length+' olay / 24 sa'; document.getElementById('heat-caption').textContent=captions[index];
    events.forEach(e=>{const p=document.createElement('i');p.className='heat-point';p.style.left=Math.max(1,Math.min(99,(e.x-bound[0])/bound[2]*100))+'%';p.style.top=Math.max(1,Math.min(99,(e.y-bound[1])/bound[3]*100))+'%';p.title=(e.name||'Olay')+' · '+e.time;map.appendChild(p)});
  }
  [mapSelect,typeSelect].forEach(x=>x.addEventListener('input',()=>render().catch(()=>{})));render().catch(()=>{document.getElementById('heat-count').textContent='Veri yok';});
})();
