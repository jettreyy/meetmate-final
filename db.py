"""Tiny SQLite storage: meetings + tasks."""
import json
import sqlite3
import datetime as dt
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "meetings.db"


def _conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS meetings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, meeting_date TEXT, created TEXT,
                transcript TEXT, summary TEXT, key_points TEXT,
                decisions TEXT, lesson TEXT, attendees TEXT, engine TEXT);
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER, task TEXT, owner TEXT,
                deadline TEXT, priority TEXT, done INTEGER DEFAULT 0);
            """
        )


def save_meeting(title, meeting_date, transcript, result, lesson, attendees):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO meetings(title,meeting_date,created,transcript,summary,key_points,decisions,lesson,attendees,engine)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (title, str(meeting_date), dt.datetime.now().isoformat(timespec="seconds"),
             transcript, result["summary"], json.dumps(result["key_points"]),
             json.dumps(result["decisions"]), json.dumps(lesson),
             json.dumps(attendees), result.get("engine", "")),
        )
        mid = cur.lastrowid
        for t in result["tasks"]:
            c.execute(
                "INSERT INTO tasks(meeting_id,task,owner,deadline,priority,done) VALUES(?,?,?,?,?,0)",
                (mid, t["task"], t["owner"], t["deadline"], t["priority"]),
            )
    return mid


def list_meetings():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT id,title,meeting_date FROM meetings ORDER BY id DESC")]


def get_meeting(mid):
    with _conn() as c:
        r = c.execute("SELECT * FROM meetings WHERE id=?", (mid,)).fetchone()
    if not r:
        return None
    m = dict(r)
    for k in ("key_points", "decisions", "lesson", "attendees"):
        m[k] = json.loads(m[k] or "[]")
    return m


def get_tasks(mid=None):
    q = "SELECT t.*, m.title AS meeting FROM tasks t JOIN meetings m ON m.id=t.meeting_id"
    args = ()
    if mid is not None:
        q += " WHERE t.meeting_id=?"
        args = (mid,)
    with _conn() as c:
        return [dict(r) for r in c.execute(q + " ORDER BY t.id", args)]


def replace_tasks(mid, rows):
    """Replace all tasks of a meeting with the edited rows."""
    with _conn() as c:
        c.execute("DELETE FROM tasks WHERE meeting_id=?", (mid,))
        for r in rows:
            if not str(r.get("task", "")).strip():
                continue
            c.execute(
                "INSERT INTO tasks(meeting_id,task,owner,deadline,priority,done) VALUES(?,?,?,?,?,?)",
                (mid, r["task"], r.get("owner", ""), r.get("deadline", ""),
                 r.get("priority", "Medium"), 1 if r.get("done") else 0),
            )
