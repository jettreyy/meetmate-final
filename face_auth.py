"""Face detection + face unlock using OpenCV only (no dlib, easy on Windows).

Detector  : Haar cascade (ships inside OpenCV)
Recognizer: LBPH (needs opencv-contrib-python)
"""
import json
import shutil
import cv2
import numpy as np
from pathlib import Path

DATA = Path(__file__).parent / "data"
FACES = DATA / "faces"
MODEL = DATA / "face_model.yml"
LABELS = DATA / "labels.json"
SIZE = (200, 200)
THRESHOLD = 70.0  # LBPH: LOWER number = better match. Raise it if it rejects you, lower it if it accepts strangers.

_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_cache = {"rec": None, "labels": None, "mtime": None}


def open_cam():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShow = fastest on Windows
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    return cap


def detect_faces(bgr):
    """Returns (gray_image, [(x,y,w,h), ...])."""
    gray = cv2.equalizeHist(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
    faces = _cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))
    return gray, [tuple(int(v) for v in f) for f in faces]


def _crop(gray, box):
    x, y, w, h = box
    return cv2.resize(gray[y:y + h, x:x + w], SIZE)


def list_users():
    return sorted(p.name for p in FACES.iterdir() if p.is_dir()) if FACES.exists() else []


def decode(data):
    """bytes from st.camera_input / file_uploader -> OpenCV BGR image."""
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def best_match(results):
    """From recognize() results, the known person with the best (lowest) score, or None."""
    known = [r for r in results if r[1] != "Unknown"]
    return min(known, key=lambda r: r[2])[1] if known else None


def has_model():
    return MODEL.exists() and LABELS.exists()


def _augment(crop):
    """1 face crop -> ~8 variations (flip, brighter, darker, tilted). Helps recognition with just a few photos."""
    out = [crop, cv2.flip(crop, 1)]
    for a in (-8, 8):
        M = cv2.getRotationMatrix2D((SIZE[0] / 2, SIZE[1] / 2), a, 1.0)
        out.append(cv2.warpAffine(crop, M, SIZE, borderMode=cv2.BORDER_REPLICATE))
    out.append(cv2.convertScaleAbs(crop, alpha=1.0, beta=25))
    out.append(cv2.convertScaleAbs(crop, alpha=1.0, beta=-25))
    out.append(cv2.convertScaleAbs(crop, alpha=1.15, beta=0))
    out.append(cv2.convertScaleAbs(crop, alpha=0.85, beta=0))
    return out


def enroll(name, frames):
    """Save face crops (plus variations) from photos for `name`, then retrain. Returns number of PHOTOS that had a face."""
    name = name.strip()
    folder = FACES / name
    folder.mkdir(parents=True, exist_ok=True)
    n = len(list(folder.glob("*.png")))
    saved = 0
    for f in frames:
        gray, boxes = detect_faces(f)
        if not boxes:
            continue
        box = max(boxes, key=lambda b: b[2] * b[3])  # biggest face = the person at the camera
        for v in _augment(_crop(gray, box)):
            cv2.imwrite(str(folder / f"{n:04d}.png"), v)
            n += 1
        saved += 1
    if saved:
        train()
    return saved


def delete_user(name):
    shutil.rmtree(FACES / name, ignore_errors=True)
    if list_users():
        train()
    else:
        MODEL.unlink(missing_ok=True)
        LABELS.unlink(missing_ok=True)


def train():
    imgs, ids, labels = [], [], {}
    for i, user in enumerate(list_users()):
        labels[str(i)] = user
        for p in (FACES / user).glob("*.png"):
            img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                imgs.append(img)
                ids.append(i)
    if not imgs:
        return False
    rec = cv2.face.LBPHFaceRecognizer_create()
    rec.train(imgs, np.array(ids))
    DATA.mkdir(exist_ok=True)
    rec.write(str(MODEL))
    LABELS.write_text(json.dumps(labels))
    _cache["mtime"] = None
    return True


def _load():
    if not has_model():
        return None, None
    mt = MODEL.stat().st_mtime
    if _cache["mtime"] != mt:
        rec = cv2.face.LBPHFaceRecognizer_create()
        rec.read(str(MODEL))
        _cache.update(rec=rec, labels=json.loads(LABELS.read_text()), mtime=mt)
    return _cache["rec"], _cache["labels"]


def recognize(bgr):
    """Returns [(box, name_or_'Unknown', confidence), ...] for every face in the image."""
    gray, boxes = detect_faces(bgr)
    rec, labels = _load()
    out = []
    for box in boxes:
        if rec is None:
            out.append((box, "Unknown", 999.0))
            continue
        idx, conf = rec.predict(_crop(gray, box))
        name = labels.get(str(idx), "Unknown") if conf < THRESHOLD else "Unknown"
        out.append((box, name, float(conf)))
    return out


def draw(bgr, results):
    """Draw green boxes for known faces, red for unknown."""
    for (x, y, w, h), name, conf in results:
        color = (60, 180, 75) if name != "Unknown" else (60, 60, 230)
        cv2.rectangle(bgr, (x, y), (x + w, y + h), color, 2)
        cv2.putText(bgr, name, (x, max(y - 8, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return bgr
