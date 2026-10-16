"""MeetMate - Meeting-to-Action-Items Agent  (run:  python -m streamlit run app.py)"""
import os
import tempfile
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
import bruno
import db
import export
import extract
import face_auth as fa
import teacher
import theme

st.set_page_config(page_title="MeetMate", page_icon="🎓", layout="wide")
theme.apply()
db.init()
PIN = os.getenv("APP_PIN", "1234")
SAMPLE = (Path(__file__).parent / "sample_meeting.txt").read_text(encoding="utf-8")
ENROLL_PHOTOS = 5

st.session_state.setdefault("fur", "Golden")
st.session_state.setdefault("acc", "Graduation cap")


# ------------------------------------------------------------------ Bruno (sidebar)
def bruno_panel(state):
    """Bruno in the sidebar: a tip for what to do now, a customizer, and an 'Ask Bruno' problem box."""
    with st.sidebar:
        text, mood = bruno.tip(state)
        asked = st.session_state.get("bruno_q", "").strip()
        if asked:
            text, mood = bruno.answer(asked, state)
        components.html(bruno.html(st.session_state.fur, st.session_state.acc, text, mood), height=330)
        st.text_input("🐾 Ask Bruno about a problem", key="bruno_q", placeholder="e.g. my camera is black")
        with st.expander("🎨 Customize Bruno"):
            st.selectbox("Fur colour", list(bruno.FURS), key="fur")
            st.selectbox("Accessory", bruno.ACCESSORIES, key="acc")


# ------------------------------------------------------------------ face unlock (browser camera)
def lock_screen():
    theme.hero("🔒 MeetMate", "Your meeting notes are private. Unlock with your face.",
               ["Face unlock", "Speech to text", "Smart tasks", "Talking teacher"])
    t1, t2, t3 = st.tabs(["😀 Face unlock", "➕ Enroll my face", "🔑 PIN backup"])
    with t1:
        if not fa.has_model():
            st.info("No face is enrolled yet. Open the 'Enroll my face' tab first.")
        else:
            st.markdown("<div class='stepbox'>Take a photo. If it is really you, the app opens.</div>", unsafe_allow_html=True)
            pic = st.camera_input("Look at the camera", key="unlock_cam")
            if pic:
                res = fa.recognize(fa.decode(pic.getvalue()))
                who = fa.best_match(res)
                if who:
                    st.session_state.user = who
                    st.rerun()
                st.error("Face not recognised." if res else "I can't see a face. Move closer and add light.")
    with t2:
        shots = st.session_state.setdefault("enroll_shots", [])
        name = st.text_input("Your name")
        admin = st.text_input("Admin PIN (needed because someone is already enrolled)", type="password") if fa.has_model() else ""
        st.markdown(f"<div class='stepbox'>Take <b>{ENROLL_PHOTOS} photos</b>. Turn your head a little each time "
                    "(straight, left, right, up, down). Good light on your face helps a lot.</div>", unsafe_allow_html=True)
        st.progress(min(len(shots) / ENROLL_PHOTOS, 1.0), text=f"Photos taken: {len(shots)} / {ENROLL_PHOTOS}")
        if len(shots) < ENROLL_PHOTOS:
            pic = st.camera_input(f"Photo {len(shots) + 1}", key=f"enroll_cam_{len(shots)}")
            if pic:
                _, boxes = fa.detect_faces(fa.decode(pic.getvalue()))
                if boxes:
                    shots.append(pic.getvalue())
                    st.rerun()
                st.warning("No face found in that photo. Press 'Clear photo' and try again with more light.")
        cols = st.columns(2)
        if cols[0].button("💾 Save my face", type="primary", disabled=len(shots) < ENROLL_PHOTOS):
            if not name.strip():
                st.warning("Type your name first.")
            elif fa.has_model() and admin != PIN:
                st.error("Wrong admin PIN.")
            else:
                n = fa.enroll(name, [fa.decode(b) for b in shots])
                st.session_state.enroll_shots = []
                st.success(f"Saved! {n} photos learned for {name.strip()}. Open the Face unlock tab.")
        if cols[1].button("🔄 Start over"):
            st.session_state.enroll_shots = []
            st.rerun()
    with t3:
        p = st.text_input("PIN", type="password")
        if st.button("Unlock with PIN"):
            if p == PIN:
                st.session_state.user = "Guest"
                st.rerun()
            else:
                st.error("Wrong PIN.")


if "user" not in st.session_state:
    bruno_panel({"locked": True, "has_faces": fa.has_model()})
    lock_screen()
    st.stop()


# ---------------------------------------------------------------------- helpers
@st.cache_resource(show_spinner=False)
def _transcriber(size):
    import transcribe
    return transcribe


def render_meeting(mid, key):
    m = db.get_meeting(mid)
    if not m:
        st.info("Nothing here yet.")
        return
    st.subheader(m["title"])
    st.caption(f"{m['meeting_date']}  |  Attendees: {', '.join(m['attendees']) or '-'}  |  Engine: {m['engine']}")
    st.markdown("#### 📝 Summary")
    st.write(m["summary"] or "-")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📌 Key points")
        for p in m["key_points"]:
            st.markdown(f"- {p}")
    with c2:
        st.markdown("#### ✅ Decisions")
        for d in m["decisions"] or ["(none found)"]:
            st.markdown(f"- {d}")
    st.markdown("#### 🧾 Action items (edit anything, then Save)")
    cols = ["done", "task", "owner", "deadline", "priority"]
    rows = db.get_tasks(mid)
    df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
    df["done"] = df["done"].astype(bool)
    edited = st.data_editor(
        df, num_rows="dynamic", width="stretch", key=f"ed_{key}_{mid}", hide_index=True,
        column_config={"done": st.column_config.CheckboxColumn("Done"),
                       "priority": st.column_config.SelectboxColumn("Priority", options=["High", "Medium", "Low"]),
                       "deadline": st.column_config.TextColumn("Deadline", help="YYYY-MM-DD")})
    if st.button("💾 Save changes", key=f"sv_{key}_{mid}"):
        db.replace_tasks(mid, edited.to_dict("records"))
        st.success("Saved.")
    tasks = db.get_tasks(mid)
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇️ To-do list (CSV / Excel)", export.tasks_to_csv(tasks), f"todo_{mid}.csv", "text/csv", key=f"c_{key}_{mid}")
    d2.download_button("⬇️ Notes (Markdown)", export.meeting_to_markdown(m, tasks), f"notes_{mid}.md", key=f"m_{key}_{mid}")
    d3.download_button("⬇️ Calendar (.ics)", export.tasks_to_ics(tasks, m["title"]), f"tasks_{mid}.ics", "text/calendar", key=f"i_{key}_{mid}")
    with st.expander("Full transcript"):
        st.text(m["transcript"])


def meeting_picker(label, key):
    ms = db.list_meetings()
    if not ms:
        st.info("No meetings yet. Create one in the 'New meeting' tab.")
        return None
    ids = [m["id"] for m in ms]
    default = ids.index(st.session_state.get("current_id")) if st.session_state.get("current_id") in ids else 0
    return st.selectbox(label, ids, index=default, key=key,
                        format_func=lambda i: next(f"#{m['id']}  {m['title']}  ({m['meeting_date']})" for m in ms if m["id"] == i))


# ---------------------------------------------------------------------- sidebar + Bruno
all_tasks = db.get_tasks()
today = dt.date.today().isoformat()
open_tasks = [t for t in all_tasks if not t["done"]]
with st.sidebar:
    st.markdown(f"### 👋 Hi, {st.session_state.user}")
    st.success("🧠 Claude AI connected") if extract.llm_available() else st.warning("⚙️ Offline mode (rule-based brain)")
    whisper_size = st.selectbox("Speech model", ["tiny", "base", "small"], index=0,
                                help="tiny = fastest, small = most accurate. First use downloads the model once.")
    if st.button("🔒 Lock"):
        del st.session_state["user"]
        st.rerun()
    st.divider()
bruno_panel({"locked": False, "n_meetings": len(db.list_meetings()),
             "n_unassigned": sum(1 for t in open_tasks if t["owner"] in ("Unassigned", "")),
             "n_overdue": sum(1 for t in open_tasks if t["deadline"] and t["deadline"] < today)})

theme.hero("🎓 MeetMate", "Upload a meeting. Get neat notes, tasks with owners and deadlines, and a teacher who explains it all.",
           ["1 · Upload audio", "2 · Transcript", "3 · Notes & tasks", "4 · Teacher explains", "5 · Export to-do"])
tabs = st.tabs(["🎙️ New meeting", "👩‍🏫 Teacher mode", "📋 Task board", "🙋 Attendance", "💬 Ask the meeting", "🗂️ History"])

# ---------------------------------------------------------------- 1. new meeting
with tabs[0]:
    c1, c2 = st.columns(2)
    title = c1.text_input("Meeting title", "Weekly project sync")
    mdate = c2.date_input("Meeting date", dt.date.today())
    people = fa.list_users()
    sel = st.multiselect("Attendees (enrolled faces)", people, default=[u for u in [st.session_state.user] if u in people])
    extra = st.text_input("Other attendees (comma separated)", "Rahul, Priya, Anjali, Neha")
    attendees = sel + [x.strip() for x in extra.split(",") if x.strip() and x.strip() not in sel]

    mode = st.radio("Input", ["Upload audio / video", "Paste transcript (quick test)"], horizontal=True)
    transcript, upload = "", None
    if mode.startswith("Upload"):
        upload = st.file_uploader("Meeting recording", type=["wav", "mp3", "m4a", "mp4", "ogg", "flac", "webm"])
    else:
        if st.button("Load sample meeting"):
            st.session_state.pasted = SAMPLE
        transcript = st.text_area("Transcript", key="pasted", height=200)

    if st.button("🚀 Make my notes", type="primary"):
        if upload is not None:
            with st.spinner("Listening to the meeting... (first run downloads the speech model)"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(upload.name).suffix) as f:
                    f.write(upload.getbuffer())
                tr = _transcriber(whisper_size)
                segs, lang = tr.transcribe(f.name, whisper_size)
                os.unlink(f.name)
                transcript = tr.with_timestamps(segs)
        if not transcript.strip():
            st.warning("Give me an audio file or some transcript text first.")
        else:
            with st.spinner("Writing notes, finding tasks, preparing your teacher..."):
                result = extract.analyze(transcript, mdate, attendees)
                lesson = extract.teacher_lines(title, result)
                st.session_state.current_id = db.save_meeting(title, mdate, transcript, result, lesson, attendees)
            st.success("Done! Scroll down for your notes, or open Teacher mode.")
            st.balloons()
    if st.session_state.get("current_id"):
        st.divider()
        render_meeting(st.session_state.current_id, "new")

# ---------------------------------------------------------------- 2. teacher mode
with tabs[1]:
    mid = meeting_picker("Pick a meeting", "teacher_pick")
    if mid:
        m = db.get_meeting(mid)
        st.caption("Teacher Meera reads the notes out loud using your browser's voice. Click any line to jump to it.")
        components.html(teacher.teacher_html(m["lesson"]), height=470, scrolling=False)

# ---------------------------------------------------------------- 3. task board
with tabs[2]:
    if not all_tasks:
        st.info("No tasks yet.")
    else:
        tdf = pd.DataFrame(all_tasks)
        open_df = tdf[tdf["done"] == 0]
        overdue = open_df[(open_df["deadline"] != "") & (open_df["deadline"] < today)]
        a, b, c = st.columns(3)
        a.metric("Total tasks", len(tdf))
        b.metric("Completed", int(tdf["done"].sum()))
        c.metric("Overdue", len(overdue))
        st.markdown("##### Open tasks per person")
        if len(open_df):
            st.bar_chart(open_df.groupby("owner").size())
        who = st.multiselect("Filter by owner", sorted(tdf["owner"].unique()))
        view = open_df if not who else open_df[open_df["owner"].isin(who)]
        st.dataframe(view[["task", "owner", "deadline", "priority", "meeting"]], width="stretch", hide_index=True)
        st.download_button("⬇️ Download open tasks (CSV)", export.tasks_to_csv(view.to_dict("records")), "all_open_tasks.csv", "text/csv")

# ---------------------------------------------------------------- 4. attendance
with tabs[3]:
    st.write("Take a photo of the room. MeetMate finds every face and tells you who from your enrolled people is present.")
    shot = st.camera_input("Group photo") or st.file_uploader("...or upload a photo", type=["jpg", "jpeg", "png"])
    if shot is not None:
        img = fa.decode(shot.getvalue())
        res = fa.recognize(img)
        st.image(fa.draw(img.copy(), res), channels="BGR")
        present = sorted({n for _, n, _ in res if n != "Unknown"})
        st.metric("Faces detected", len(res))
        st.write("**Recognised:** " + (", ".join(present) or "nobody from the enrolled list"))
        st.write(f"**Not recognised:** {sum(1 for _, n, _ in res if n == 'Unknown')}")
        absent = [u for u in fa.list_users() if u not in present]
        if absent:
            st.write("**Absent:** " + ", ".join(absent))

# ---------------------------------------------------------------- 5. ask
with tabs[4]:
    mid = meeting_picker("Pick a meeting", "ask_pick")
    if mid:
        q = st.text_input("Ask anything, e.g. 'Who is doing the login page?' or 'When is the demo?'")
        if q:
            m = db.get_meeting(mid)
            st.write(extract.answer_question(q, m["transcript"], m))

# ---------------------------------------------------------------- 6. history
with tabs[5]:
    mid = meeting_picker("Open an old meeting", "hist_pick")
    if mid:
        render_meeting(mid, "hist")
