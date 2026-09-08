(() => {
  const map = document.getElementById('heatmap');
  if (!map) return;
  const mapSelect = document.getElementById('heat-map'), typeSelect = document.getElementById('heat-kind');
  const captions = {21:'Chunjo M1',23:'Chunjo M2',24:'Chunjo M3 — Waryong',25:'Łatwy Loch Małp',61:'Góra Sohan',64:'Dolina Orków',63:'Pustynia Yongbi',104:'Loch Pająków V1',108:'Loch Małp Normalny',109:'Loch Małp Trudny',65:'Świątynia Hwang'};
  const backgrounds = {21:'chunjo-m1',23:'chunjo-m2',24:'guild-map-02',25:'easy-monkey',61:'mount-sohan',64:'orc-valley',63:'yongbi-desert',104:'spider-dungeon-v1',108:'medium-monkey',109:'hard-monkey',65:'hwang-temple'};
  async function render(){
    const data = await fetch('/api/heat-events?type='+encodeURIComponent(typeSelect.value),{cache:'no-store'}).then(r=>r.json());
    const index=Number(mapSelect.value), bound=data.bounds[String(index)]||data.bounds[index];
    const extension = (index === 108 || index === 109) ? 'webp' : 'png';
    map.dataset.mapIndex=String(index); map.style.backgroundImage=`linear-gradient(#00000030,#00000030),url('/static/maps/${backgrounds[index]}.${extension}')`;
    map.querySelectorAll('.heat-point').forEach(e=>e.remove());
    const events=data.events.filter(e=>e.map_index===index); document.getElementById('heat-count').textContent=events.length+' zdarzeń / 24 h'; document.getElementById('heat-caption').textContent=captions[index];
    events.forEach(e=>{const p=document.createElement('i');p.className='heat-point';p.style.left=Math.max(1,Math.min(99,(e.x-bound[0])/bound[2]*100))+'%';p.style.top=Math.max(1,Math.min(99,(e.y-bound[1])/bound[3]*100))+'%';p.title=(e.name||'Zdarzenie')+' · '+e.time;map.appendChild(p)});
  }
  [mapSelect,typeSelect].forEach(x=>x.addEventListener('input',()=>render().catch(()=>{})));render().catch(()=>{document.getElementById('heat-count').textContent='Brak danych';});
})();
