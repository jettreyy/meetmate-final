"""Exports: CSV (Excel), Markdown notes, ICS calendar file."""
import io
import csv
import uuid
import datetime as dt


def tasks_to_csv(tasks):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Done", "Task", "Owner", "Deadline", "Priority", "Meeting"])
    for t in tasks:
        w.writerow(["yes" if t.get("done") else "no", t["task"], t["owner"], t["deadline"], t["priority"], t.get("meeting", "")])
    return buf.getvalue()


def meeting_to_markdown(m, tasks):
    out = [f"# {m['title']}", f"*Date: {m['meeting_date']}  |  Attendees: {', '.join(m['attendees']) or '-'}*", "",
           "## Summary", m["summary"], "", "## Key points"]
    out += [f"- {p}" for p in m["key_points"]]
    out += ["", "## Decisions"] + ([f"- {d}" for d in m["decisions"]] or ["- (none)"])
    out += ["", "## Action items", "", "| Done | Task | Owner | Deadline | Priority |", "|---|---|---|---|---|"]
    for t in tasks:
        out.append(f"| {'[x]' if t['done'] else '[ ]'} | {t['task']} | {t['owner']} | {t['deadline'] or '-'} | {t['priority']} |")
    return "\n".join(out) + "\n"


def tasks_to_ics(tasks, title="MeetMate"):
    """All-day calendar events for every task that has a deadline. Import into Google/Outlook calendar."""
    now = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MeetMate//EN"]
    for t in tasks:
        if not t.get("deadline"):
            continue
        try:
            d = dt.date.fromisoformat(t["deadline"])
        except ValueError:
            continue
        summary = f"{t['task']} ({t['owner']})".replace("\n", " ").replace(",", "\\,").replace(";", "\\;")
        lines += ["BEGIN:VEVENT", f"UID:{uuid.uuid4()}@meetmate", f"DTSTAMP:{now}",
                  f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + dt.timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{summary}", f"DESCRIPTION:From meeting: {title}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
