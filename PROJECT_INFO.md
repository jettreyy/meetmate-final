# Project information (copy into your report / PPT)

## Title
**MeetMate: An AI-Powered Meeting-to-Action-Items Agent with Face-Secured Access and an Interactive Virtual Teacher**

## Topic / domain
Artificial Intelligence: Natural Language Processing + Speech Recognition + Computer Vision (Human-Computer Interaction)

## Problem statement
After every meeting people forget who must do what and by when. Writing minutes by hand is slow, error-prone and the notes are boring to read.
Meeting recordings are also private, so access must be protected.

## Objectives
1. Convert meeting audio into an accurate text transcript.
2. Automatically extract summary, decisions and action items with owner, deadline and priority.
3. Export tasks as a to-do list (CSV), notes (Markdown) and calendar events (.ics).
4. Protect the notes with face-based authentication and mark attendance with face detection.
5. Make notes easy to understand through a talking virtual teacher and a helper avatar (Bruno).

## Abstract (short)
MeetMate is a web application that turns a meeting recording into structured, actionable notes. Speech is transcribed with the Whisper model.
An NLP engine (rule-based offline engine, or a large language model when an API key is available) extracts the summary, decisions and tasks,
and converts relative deadlines such as "next Monday" into calendar dates. Access is secured using face detection (Haar cascade) and
face recognition (LBPH). The notes can be explained by an animated virtual teacher using text-to-speech, and a guide avatar named Bruno helps
users solve problems. Results can be exported to CSV, Markdown and iCalendar.

## Modules
Authentication (face unlock + PIN) | Speech-to-text | Notes and task extraction | Teacher mode | Task board | Attendance by face | Question answering | Export | Bruno helper

## Technologies
Python, Streamlit, OpenCV (Haar cascade, LBPH), faster-whisper (Whisper), SQLite, Pandas, Claude API (optional), Web Speech API (browser text-to-speech)

## Limitations (say these yourself in the viva)
- Face unlock has no liveness check, so a printed photo may fool it.
- The offline engine uses rules and works best with clear sentences.
- Speech accuracy drops with noisy audio and strong accents on the small models.

## Future scope
Blink-based liveness detection, speaker identification (who said what), multi-language meetings, live meeting mode, Slack/Email integration.
