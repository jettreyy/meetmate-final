# MeetMate - Meeting-to-Action-Items Agent

Audio in -> transcript -> summary, decisions, tasks (owner + deadline + priority) -> to-do list (CSV / Markdown / calendar .ics),
explained by an animated talking teacher, guided by Bruno the helper dog, locked behind face unlock.

## Run on Windows (VS Code terminal)
```
python -m venv venv
venv\Scripts\activate
python -m pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
python -m pip install -r requirements.txt
python check_setup.py
python -m streamlit run app.py
```
Optional: copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY` for the smart brain. Backup PIN = `APP_PIN` (default 1234).

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo (`.gitignore` already hides venv, data and .env).
2. share.streamlit.io -> Create app -> pick the repo, branch `main`, main file `app.py`.
3. Advanced settings -> Python 3.11, and paste secrets:
```
APP_PIN = "choose-a-pin"
```
4. Deploy, then share the `https://....streamlit.app` link.

## Files
| File | Job |
|---|---|
| app.py | the website (Streamlit) |
| bruno.py | Bruno the helper avatar + problem FAQ |
| theme.py + .streamlit/config.toml | colours and design |
| face_auth.py | face detection + unlock (OpenCV) |
| transcribe.py | audio -> text (faster-whisper) |
| extract.py | summary, tasks, deadlines, teacher lines, Q&A |
| teacher.py | talking teacher avatar |
| export.py | CSV, Markdown, ICS |
| db.py | SQLite storage |
| PROJECT_INFO.md | title, abstract, objectives for your report |
