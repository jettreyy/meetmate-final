"""Bruno - the friendly guide dog of MeetMate.

* Draws a customizable cartoon dog (fur colour + accessory) that can talk (browser voice).
* Gives a smart tip that depends on what is happening in the app.
* Answers "my problem" questions: built-in troubleshooting FAQ, and Claude if an API key exists.
"""
import re
import json
import extract

FURS = {"Golden": "#E8B04A", "Chocolate": "#9A6240", "Cloud white": "#F3EFE8", "Midnight": "#4A4A63"}
ACCESSORIES = ["Graduation cap", "Glasses", "Headphones", "Bow tie", "None"]


def _shade(hex_color, f):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


def _accessory_svg(acc):
    if acc == "Graduation cap":
        return ('<polygon points="100,18 152,38 100,58 48,38" fill="#23233a"/>'
                '<rect x="76" y="44" width="48" height="14" rx="4" fill="#33334f"/>'
                '<line x1="100" y1="38" x2="146" y2="44" stroke="#f5c542" stroke-width="3"/>'
                '<line x1="146" y1="44" x2="146" y2="66" stroke="#f5c542" stroke-width="3"/>'
                '<circle cx="146" cy="68" r="5" fill="#f5c542"/>')
    if acc == "Glasses":
        return ('<g fill="#ffffff22" stroke="#1d1d2b" stroke-width="3.5"><circle cx="76" cy="86" r="15"/>'
                '<circle cx="124" cy="86" r="15"/><line x1="91" y1="86" x2="109" y2="86"/></g>')
    if acc == "Headphones":
        return ('<path d="M42 84 Q100 -8 158 84" stroke="#3a3a55" stroke-width="8" fill="none" stroke-linecap="round"/>'
                '<rect x="32" y="72" width="18" height="36" rx="8" fill="#8b5cf6"/>'
                '<rect x="150" y="72" width="18" height="36" rx="8" fill="#8b5cf6"/>')
    if acc == "Bow tie":
        return ('<polygon points="100,170 74,156 74,184" fill="#e63946"/><polygon points="100,170 126,156 126,184" fill="#e63946"/>'
                '<circle cx="100" cy="170" r="7" fill="#b92d38"/>')
    return ""


def _mouth(mood):
    if mood == "oops":
        return '<path d="M86 134 Q100 122 114 134" stroke="#5a2330" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    if mood == "think":
        return '<path d="M88 130 Q100 134 112 128" stroke="#5a2330" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    return '<path d="M82 124 Q100 144 118 124" stroke="#5a2330" stroke-width="3.5" fill="none" stroke-linecap="round"/>'


def _brows(mood):
    if mood == "oops":
        return ('<path d="M62 70 Q74 78 88 72" stroke="#00000066" stroke-width="4" fill="none" stroke-linecap="round"/>'
                '<path d="M112 72 Q126 78 138 70" stroke="#00000066" stroke-width="4" fill="none" stroke-linecap="round"/>')
    if mood == "think":
        return ('<path d="M62 70 Q74 64 88 70" stroke="#00000066" stroke-width="4" fill="none" stroke-linecap="round"/>'
                '<path d="M112 62 Q126 58 138 66" stroke="#00000066" stroke-width="4" fill="none" stroke-linecap="round"/>')
    return ""


def _svg(fur, acc, mood):
    ear = _shade(fur, 0.62)
    body = _shade(fur, 0.95)
    return f"""
<svg id="dog" viewBox="0 0 200 205" width="150" height="150" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="100" cy="198" rx="62" ry="34" fill="{body}"/>
  <ellipse cx="46" cy="84" rx="22" ry="42" fill="{ear}" transform="rotate(14 46 84)"/>
  <ellipse cx="154" cy="84" rx="22" ry="42" fill="{ear}" transform="rotate(-14 154 84)"/>
  <ellipse cx="100" cy="95" rx="58" ry="55" fill="{fur}"/>
  <ellipse cx="100" cy="120" rx="32" ry="24" fill="#fff4e4"/>
  {_brows(mood)}
  <circle cx="76" cy="86" r="7.5" fill="#1d1d2b"/><circle cx="124" cy="86" r="7.5" fill="#1d1d2b"/>
  <circle cx="78.5" cy="83.5" r="2.5" fill="#fff"/><circle cx="126.5" cy="83.5" r="2.5" fill="#fff"/>
  <circle cx="64" cy="108" r="8" fill="#ff8fa3" opacity=".45"/><circle cx="136" cy="108" r="8" fill="#ff8fa3" opacity=".45"/>
  <ellipse cx="100" cy="106" rx="11" ry="7.5" fill="#25252f"/><ellipse cx="97" cy="104" rx="3.5" ry="1.8" fill="#ffffff88"/>
  <line x1="100" y1="112" x2="100" y2="121" stroke="#5a2330" stroke-width="3"/>
  {_mouth(mood)}
  <ellipse id="open" cx="100" cy="132" rx="11" ry="0.1" fill="#7a1f2b"/>
  {_accessory_svg(acc)}
</svg>"""


TEMPLATE = """
<style>
 body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:transparent}
 .row{display:flex;flex-direction:column;align-items:center}
 .bob{animation:bob 2.6s ease-in-out infinite}
 @keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
 .bubble{position:relative;background:#fff;color:#22223b;border-radius:16px;padding:11px 14px;font-size:13.5px;line-height:1.45;
         margin-top:6px;box-shadow:0 6px 18px #0004;max-width:230px}
 .bubble:before{content:"";position:absolute;top:-8px;left:50%;margin-left:-8px;border:8px solid transparent;border-top:0;border-bottom-color:#fff}
 .name{font-weight:700;color:#8b5cf6;font-size:12px;letter-spacing:.5px;margin-bottom:3px}
 button{margin-top:8px;border:0;border-radius:999px;padding:6px 14px;background:linear-gradient(120deg,#6d3df5,#0ea5b7);color:#fff;font-size:12.5px;cursor:pointer}
</style>
<div class="row">
  <div class="bob">__SVG__</div>
  <div class="bubble"><div class="name">BRUNO</div><span id="t"></span></div>
  <button onclick="say()">&#128266; Hear Bruno</button>
</div>
<script>
const text = __TEXT__;
document.getElementById('t').textContent = text;
const open = document.getElementById('open'); let timer = null;
function say(){
  const s = window.speechSynthesis; if(!s) return; s.cancel();
  const u = new SpeechSynthesisUtterance(text); u.rate = 1.05; u.pitch = 0.75;
  const v = s.getVoices().find(x=>/en/i.test(x.lang) && /male|david|mark|ravi|google uk english male/i.test(x.name)) || s.getVoices().find(x=>/^en/i.test(x.lang));
  if(v) u.voice = v;
  u.onstart = ()=>{ clearInterval(timer); timer = setInterval(()=>open.setAttribute('ry', 2+Math.random()*8), 110); };
  u.onend = u.onerror = ()=>{ clearInterval(timer); open.setAttribute('ry', 0.1); };
  s.speak(u);
}
</script>
"""


def html(fur_name, accessory, text, mood="happy"):
    fur = FURS.get(fur_name, FURS["Golden"])
    payload = json.dumps(text).replace("</", "<\\/")
    return TEMPLATE.replace("__SVG__", _svg(fur, accessory, mood)).replace("__TEXT__", payload)


# ----------------------------------------------------------------- smart tips
def tip(state):
    """state: dict(locked, has_faces, n_meetings, n_tasks, n_unassigned, n_overdue). Returns (text, mood)."""
    if state.get("locked"):
        if not state.get("has_faces"):
            return ("Woof! I'm Bruno. First let's lock the app with your face. Open 'Enroll my face' and take 5 photos.", "happy")
        return ("Take a photo and I'll check it's you. No luck? Try the PIN tab, it's my backup trick!", "happy")
    if not state.get("n_meetings"):
        return ("Let's make your first notes! Pick 'Paste transcript', press Load sample meeting, then Make my notes.", "happy")
    if state.get("n_unassigned"):
        return (f"{state['n_unassigned']} task(s) have no owner. Fix the Owner column and press Save, then I'll be proud!", "think")
    if state.get("n_overdue"):
        return (f"Psst... {state['n_overdue']} task(s) are overdue. Time to chase them!", "oops")
    return ("Notes are ready! Open Teacher mode and let Teacher Meera explain them. Or ask the meeting a question.", "happy")


# ---------------------------------------------------------------- problem FAQ
FAQ = [
    (("camera", "webcam", "permission", "allow", "black", "blocked"),
     "Camera trouble? Click the camera/lock icon in the browser address bar and choose Allow. Close Zoom/Teams, then refresh the page."),
    (("recogni", "face", "unlock", "reject", "not me", "unknown", "match"),
     "Face not recognised? Sit facing a window or lamp, remove cap/mask, and enroll again taking photos from slightly different angles. The PIN tab always works."),
    (("pin", "password"), "The backup PIN is 1234 unless you set APP_PIN in your .env file or deployment secrets."),
    (("audio", "upload", "transcri", "whisper", "slow", "model", "speech"),
     "Speech is slow? Choose the 'tiny' speech model in the sidebar. The first run downloads the model once. Long recordings take time on a laptop CPU. For a quick test, use Paste transcript."),
    (("task", "owner", "unassigned", "missing", "no action", "deadline", "date"),
     "Tasks missing? The offline brain likes clear sentences like 'Rahul will finish the report by Friday'. Add an ANTHROPIC_API_KEY for much smarter extraction. You can also edit the table by hand and press Save."),
    (("voice", "sound", "teacher", "speak", "hear", "mute", "silent"),
     "No voice? Use Chrome or Edge, unmute the tab, and press Play. The voice comes from your browser, so it can sound different on different computers."),
    (("export", "csv", "excel", "calendar", "ics", "download", "markdown"),
     "Under the action items table you'll find 3 download buttons: CSV for Excel, Markdown notes, and a .ics file you can import into Google or Outlook Calendar."),
    (("api", "key", "claude", "anthropic", "smart"),
     "To switch on the smart brain, copy .env.example to .env, paste your ANTHROPIC_API_KEY, and restart the app. The sidebar will say 'Claude AI connected'."),
    (("attendance", "present", "absent", "group photo"),
     "Attendance works best with clear, front-facing faces in good light. Only people who enrolled their face can be recognised by name."),
    (("who are you", "your name", "bruno", "hello", "hey", "help"),
     "I'm Bruno, MeetMate's guide dog. Ask me about the camera, face unlock, audio, tasks, the teacher's voice, or exports!"),
]

APP_DESCRIPTION = (
    "MeetMate is a Streamlit app: face unlock (OpenCV), audio -> transcript (faster-whisper), notes + tasks with owner/deadline, "
    "export to CSV/Markdown/ICS, an animated talking Teacher, attendance by face, and Q&A on the meeting. Backup PIN exists.")


def answer(question, state=None):
    q = question.lower().strip()
    if not q:
        return "Woof! Ask me anything about MeetMate.", "happy"
    if q in ("hi", "hii", "hey", "yo", "hello"):
        q = "who are you"
    for keys, reply in FAQ:
        if any(re.search(r"\b" + re.escape(k), q) for k in keys):
            return reply, "think"
    if extract.llm_available():
        try:
            return extract._ask(
                "You are Bruno, a cheerful guide dog helping a student use the MeetMate app. " + APP_DESCRIPTION +
                " Answer in at most 3 short, friendly sentences. If unsure, say so.", question, 300), "think"
        except Exception:
            pass
    return ("Hmm, I'm not sure about that one. Try asking about: camera, face unlock, audio upload, tasks, teacher voice, or exports.", "oops")
