"""The brain: transcript -> summary, decisions, tasks (owner + deadline + priority),
teacher-style lesson, and Q&A.

Two engines:
  * Claude (if ANTHROPIC_API_KEY is set)  -> smart
  * Offline rule-based engine            -> always works, no internet needed
"""
import os
import re
import json
import calendar
import datetime as dt
from collections import Counter

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")


def llm_available():
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _ask(system, user, max_tokens=2500):
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(model=MODEL, max_tokens=max_tokens, system=system,
                               messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in r.content if b.type == "text")


def _json_from(text):
    text = text.strip()
    s, e = text.find("{"), text.rfind("}")
    return json.loads(text[s:e + 1])


# ---------------------------------------------------------------- deadlines
WEEKDAYS = {n: i for i, n in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])}
MONTHS.update({"jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12})
_MON = "|".join(sorted(MONTHS, key=len, reverse=True))


def _safe_date(y, m, d, base):
    try:
        out = dt.date(y, m, d)
    except ValueError:
        return None
    if out < base - dt.timedelta(days=30):  # "15 Jan" said in December -> next year
        out = out.replace(year=out.year + 1)
    return out


def resolve_deadline(text, base):
    """Find a deadline phrase in `text` and return ISO date (YYYY-MM-DD) or ''."""
    t = text.lower()
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        d = _safe_date(int(m[1]), int(m[2]), int(m[3]), base)
        return d.isoformat() if d else ""
    m = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MON})\b", t)
    if m:
        d = _safe_date(base.year, MONTHS[m[2]], int(m[1]), base)
        return d.isoformat() if d else ""
    m = re.search(rf"\b({_MON})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", t)
    if m:
        d = _safe_date(base.year, MONTHS[m[1]], int(m[2]), base)
        return d.isoformat() if d else ""
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", t)
    if m:
        y = int(m[3]) if m[3] else base.year
        y += 2000 if y < 100 else 0
        d = _safe_date(y, int(m[2]), int(m[1]), base)
        return d.isoformat() if d else ""
    if "day after tomorrow" in t:
        return (base + dt.timedelta(days=2)).isoformat()
    if "tomorrow" in t:
        return (base + dt.timedelta(days=1)).isoformat()
    if re.search(r"\b(today|tonight|end of (the )?day|eod)\b", t):
        return base.isoformat()
    if "next week" in t:
        return (base + dt.timedelta(days=7)).isoformat()
    if re.search(r"\b(end of (the )?week|this week)\b", t):
        return (base + dt.timedelta(days=(4 - base.weekday()) % 7)).isoformat()
    if re.search(r"\bend of (the )?month\b", t):
        return dt.date(base.year, base.month, calendar.monthrange(base.year, base.month)[1]).isoformat()
    if "next month" in t:
        return (base + dt.timedelta(days=30)).isoformat()
    m = re.search(r"\b(" + "|".join(WEEKDAYS) + r")\b", t)
    if m:
        delta = (WEEKDAYS[m[1]] - base.weekday()) % 7 or 7
        return (base + dt.timedelta(days=delta)).isoformat()
    return ""


# ------------------------------------------------------------ offline engine
STOP = set("""a an the and or but if so to of in on at for with from by as is are was were be been it this that these those
i you we they he she them us our your their my me do does did have has had will would should could can may might must not no
yes ok okay just also then than there here what which who whom about into over after before up down out very really""".split())
ACTION = re.compile(r"\b(will|shall|should|must|need to|needs to|has to|have to|is going to|are going to|please|action item|"
                    r"responsible for|assigned to|due)\b", re.I)
DECISION = re.compile(r"\b(decided|agreed|finali[sz]ed|approved|settled|we(?:'ll| will) go with|resolved)\b", re.I)
NOT_NAMES = {"I", "We", "You", "They", "He", "She", "It", "This", "That", "Everyone", "Please", "There", "Who", "What",
             "Also", "Then", "Okay", "Ok", "So", "And", "But", "Yes", "No", "The", "My", "Our", "Next", "Today", "Tomorrow"}


def _sentences(text):
    text = re.sub(r"\[\d+:\d+\]", " ", text)
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.split()) >= 3]


def _owner(sentence, attendees):
    low = sentence.lower()
    best, pos = None, 10 ** 9
    for a in attendees:
        i = low.find(a.lower())
        if i != -1 and i < pos:
            best, pos = a, i
    if best:
        return best
    m = re.search(r"\b([A-Z][a-z]+)\b(?:,\s*you)?\s+(?:will|should|must|needs? to|has to|is going to|shall)\b", sentence)
    if m and m[1] not in NOT_NAMES:
        return m[1]
    if re.search(r"\b(everyone|everybody|all of us|team)\b", low):
        return "Everyone"
    if re.match(r"^\W*(?:and |so |ok(?:ay)?,? )?i (will|'ll|need to|should)\b", low):
        return "Speaker"
    return "Unassigned"


def _priority(s):
    low = s.lower()
    if re.search(r"\b(urgent|asap|critical|immediately|today|tomorrow|high priority)\b", low):
        return "High"
    if re.search(r"\b(when possible|later|eventually|if time|nice to have)\b", low):
        return "Low"
    return "Medium"


def _clean_task(s):
    s = re.sub(r"^(okay|ok|so|and|then|also)[, ]+", "", s.strip(), flags=re.I)
    s = s[:1].upper() + s[1:]
    return s[:160].rstrip(" .") 


def _rank(sents, k):
    freq = Counter(w for s in sents for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP and len(w) > 2)
    scored = []
    for i, s in enumerate(sents):
        words = [w for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP and len(w) > 2]
        scored.append((sum(freq[w] for w in words) / (len(words) ** 0.5 + 1), i))
    top = sorted(scored, reverse=True)[:k]
    return [sents[i] for _, i in sorted(top, key=lambda x: x[1])]


def _offline_analyze(transcript, base, attendees):
    sents = _sentences(transcript)
    tasks, decisions, rest = [], [], []
    for s in sents:
        if DECISION.search(s):
            decisions.append(_clean_task(s))
        elif ACTION.search(s) and len(s.split()) >= 4:
            tasks.append({"task": _clean_task(s), "owner": _owner(s, attendees),
                          "deadline": resolve_deadline(s, base), "priority": _priority(s)})
        else:
            rest.append(s)
    # Summary: best sentences from the WHOLE meeting (skip greetings), so it also covers tasks and decisions
    pool = [x for x in sents if not re.match(r"^(okay|ok|so|hi|hello|good morning|welcome)\b.*(start|begin|sync|everyone)", x, re.I)] or sents
    return {"summary": " ".join(_rank(pool, 3)), "key_points": _rank(pool, 5),
            "decisions": decisions, "tasks": tasks, "engine": "Offline rule-based"}


# ------------------------------------------------------------------ Claude
def _llm_analyze(transcript, base, attendees):
    system = ("You turn meeting transcripts into clean notes. Reply with ONLY one JSON object, no markdown. "
              'Schema: {"summary": str (3-4 sentences), "key_points": [str], "decisions": [str], '
              '"tasks": [{"task": str (starts with a verb), "owner": str (a name, "Everyone" or "Unassigned"), '
              '"deadline": str (YYYY-MM-DD or ""), "priority": "High"|"Medium"|"Low"}]}. '
              "Never invent tasks that nobody mentioned.")
    user = (f"Meeting date: {base.isoformat()} ({base.strftime('%A')}). Resolve words like 'Friday' or 'tomorrow' "
            f"into real dates from that day.\nKnown attendees: {', '.join(attendees) or 'unknown'}\n\nTRANSCRIPT:\n{transcript}")
    data = _json_from(_ask(system, user))
    data["engine"] = f"Claude ({MODEL})"
    return data


def _normalize(data):
    tasks, seen = [], set()
    for t in data.get("tasks", []):
        text = str(t.get("task", "")).strip()
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        pr = str(t.get("priority", "Medium")).capitalize()
        tasks.append({"task": text, "owner": str(t.get("owner") or "Unassigned").strip(),
                      "deadline": str(t.get("deadline") or "").strip(),
                      "priority": pr if pr in ("High", "Medium", "Low") else "Medium"})
    return {"summary": str(data.get("summary", "")).strip(),
            "key_points": [str(x) for x in data.get("key_points", [])],
            "decisions": [str(x) for x in data.get("decisions", [])],
            "tasks": tasks, "engine": data.get("engine", "")}


def analyze(transcript, base, attendees):
    """Main entry point. Falls back to the offline engine if Claude is missing or fails."""
    if llm_available():
        try:
            return _normalize(_llm_analyze(transcript, base, attendees))
        except Exception as e:  # network, bad JSON, bad key ...
            out = _normalize(_offline_analyze(transcript, base, attendees))
            out["engine"] = f"Offline rule-based (Claude failed: {type(e).__name__})"
            return out
    return _normalize(_offline_analyze(transcript, base, attendees))


# ------------------------------------------------------------ teacher lesson
def teacher_lines(title, result):
    """A list of short spoken lines, as if a friendly teacher is explaining the meeting."""
    if llm_available():
        try:
            system = ("You are a warm, funny school teacher explaining meeting notes to students. Use very simple words "
                      "and one everyday analogy (like homework, football team, kitchen). Reply with ONLY JSON: "
                      '{"lines": [str]} with 10-14 lines, each under 28 words, spoken style, no emojis. '
                      "Start with a greeting, cover summary, decisions, each task (who/what/when), then end with a closing line.")
            data = _json_from(_ask(system, f"Meeting: {title}\n{json.dumps(result)}", 1800))
            lines = [str(x) for x in data.get("lines", []) if str(x).strip()]
            if lines:
                return lines
        except Exception:
            pass
    lines = [f"Good morning class! Today's lesson is about the meeting called {title}."]
    if result["summary"]:
        lines.append("First, the big picture. " + result["summary"])
    for d in result["decisions"][:3]:
        lines.append("Remember this decision, it is like a rule we all agreed on. " + d)
    if result["tasks"]:
        lines.append("Now for homework. Think of every task as an assignment with a name and a due date.")
    for t in result["tasks"][:8]:
        who = t["owner"] if t["owner"] not in ("Unassigned", "") else "Somebody, we still need to pick who,"
        due = f"It is due on {t['deadline']}." if t["deadline"] else "No due date yet."
        lines.append(f"{who}: {t['task']}. {due} Priority is {t['priority']}.")
    lines.append("Any questions? No? Wonderful. Class dismissed!")
    return lines


# --------------------------------------------------------------------- Q&A
def answer_question(question, transcript, result):
    if llm_available():
        try:
            return _ask("Answer the question using ONLY the meeting transcript. If the answer is not there, say so. Be brief.",
                        f"TRANSCRIPT:\n{transcript}\n\nQUESTION: {question}", 600)
        except Exception:
            pass
    q = {w for w in re.findall(r"[a-z']+", question.lower()) if w not in STOP and len(w) > 2}
    sents = _sentences(transcript)
    scored = sorted(((len(q & set(re.findall(r"[a-z']+", s.lower()))), s) for s in sents), reverse=True)
    best = [s for sc, s in scored[:3] if sc > 0]
    return ("Closest lines from the meeting:\n- " + "\n- ".join(best)) if best else "I could not find that in the meeting."
