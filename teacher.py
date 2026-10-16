"""Animated teacher avatar: a cartoon teacher (SVG) that talks using the browser's built-in voice.
No installs, no API. The mouth moves while the voice speaks."""
import json

TEMPLATE = r"""
<style>
 body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:transparent}
 .wrap{display:flex;gap:16px;align-items:stretch;flex-wrap:wrap}
 .stage{flex:0 0 190px;text-align:center}
 .board{flex:1;min-width:260px;background:#1f4d3a;border:8px solid #8b5a2b;border-radius:10px;color:#f4f4e8;
        padding:18px;display:flex;flex-direction:column;justify-content:center;min-height:190px;font-size:19px;line-height:1.5}
 .board small{opacity:.6;margin-bottom:8px;display:block}
 .ctl{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
 button{border:0;border-radius:8px;padding:8px 14px;font-size:14px;cursor:pointer;background:#2e7d5b;color:#fff}
 button.alt{background:#555}
 .list{margin-top:12px;max-height:150px;overflow:auto;font-size:13px;color:#888}
 .list div{padding:3px 6px;border-radius:5px;cursor:pointer}
 .list div.on{background:#2e7d5b22;color:#2e7d5b;font-weight:600}
 @media(prefers-color-scheme:dark){.list{color:#aaa}}
</style>
<div class="wrap">
 <div class="stage">
  <svg viewBox="0 0 200 240" width="180">
    <rect x="45" y="150" width="110" height="90" rx="28" fill="#3b6ea5"/>
    <polygon points="100,150 90,170 100,215 110,170" fill="#c0392b"/>
    <rect x="86" y="128" width="28" height="28" rx="8" fill="#f1c9a5"/>
    <ellipse cx="100" cy="90" rx="52" ry="58" fill="#f1c9a5"/>
    <path d="M46 85 Q50 28 100 30 Q150 28 154 85 Q140 52 100 52 Q60 52 46 85Z" fill="#4a3426"/>
    <g fill="none" stroke="#222" stroke-width="3"><circle cx="78" cy="88" r="14"/><circle cx="122" cy="88" r="14"/><line x1="92" y1="88" x2="108" y2="88"/></g>
    <circle id="eL" cx="78" cy="88" r="4.5" fill="#222"/><circle id="eR" cx="122" cy="88" r="4.5" fill="#222"/>
    <path d="M66 70 Q78 64 90 70" stroke="#4a3426" stroke-width="4" fill="none"/><path d="M110 70 Q122 64 134 70" stroke="#4a3426" stroke-width="4" fill="none"/>
    <ellipse id="mouth" cx="100" cy="122" rx="14" ry="2.5" fill="#8b2e2e"/>
    <circle cx="66" cy="108" r="7" fill="#f4a6a0" opacity=".5"/><circle cx="134" cy="108" r="7" fill="#f4a6a0" opacity=".5"/>
  </svg>
  <div style="font-weight:600;font-size:14px">Teacher Meera</div>
 </div>
 <div style="flex:1;min-width:260px">
  <div class="board"><small id="count"></small><div id="line">Press Play, class is about to begin.</div></div>
  <div class="ctl">
   <button onclick="play()">&#9654; Play</button>
   <button class="alt" onclick="pauseIt()">&#10074;&#10074; Pause</button>
   <button class="alt" onclick="restart()">&#8635; Restart</button>
   <label style="font-size:13px;color:#888">Speed <input type="range" min="0.7" max="1.4" step="0.1" value="1" oninput="rate=+this.value"></label>
  </div>
  <div class="list" id="list"></div>
 </div>
</div>
<script>
const lines = __LINES__;
let i = 0, playing = false, rate = 1, talkTimer = null, voice = null;
const synth = window.speechSynthesis, mouth = document.getElementById('mouth');
const lineEl = document.getElementById('line'), countEl = document.getElementById('count'), listEl = document.getElementById('list');
function pickVoice(){ const v = synth.getVoices(); voice = v.find(x=>/en-(IN|GB|US)/i.test(x.lang) && /female|zira|heera|neerja|samantha|google/i.test(x.name)) || v.find(x=>/^en/i.test(x.lang)) || null; }
if (synth){ pickVoice(); synth.onvoiceschanged = pickVoice; }
lines.forEach((t,k)=>{ const d=document.createElement('div'); d.textContent=(k+1)+'. '+t; d.onclick=()=>{ i=k; play(); }; d.id='l'+k; listEl.appendChild(d); });
function talk(on){ clearInterval(talkTimer); if(on){ talkTimer=setInterval(()=>{ mouth.setAttribute('ry', 3+Math.random()*10); },110);} else mouth.setAttribute('ry', 2.5); }
function show(k){ lineEl.textContent = lines[k]; countEl.textContent = 'Lesson '+(k+1)+' of '+lines.length;
  document.querySelectorAll('.list div').forEach(d=>d.classList.remove('on')); const el=document.getElementById('l'+k); if(el){el.classList.add('on'); el.scrollIntoView({block:'nearest'});} }
function speak(){
  if (i >= lines.length){ playing=false; talk(false); lineEl.textContent='Class dismissed! Great job today.'; i=0; return; }
  show(i);
  if (!synth){ return; }
  synth.cancel();
  const u = new SpeechSynthesisUtterance(lines[i]); u.rate = rate; if (voice) u.voice = voice;
  u.onstart = ()=>talk(true);
  u.onend = ()=>{ talk(false); if (playing){ i++; setTimeout(speak, 350); } };
  u.onerror = ()=>{ talk(false); };
  synth.speak(u);
}
function play(){ playing = true; speak(); }
function pauseIt(){ playing = false; if (synth) synth.cancel(); talk(false); }
function restart(){ pauseIt(); i = 0; play(); }
setInterval(()=>{ const e=[document.getElementById('eL'),document.getElementById('eR')]; e.forEach(x=>x.setAttribute('r',0.8)); setTimeout(()=>e.forEach(x=>x.setAttribute('r',4.5)),130); }, 3500);
</script>
"""


def teacher_html(lines):
    payload = json.dumps(lines).replace("</", "<\\/")
    return TEMPLATE.replace("__LINES__", payload)
