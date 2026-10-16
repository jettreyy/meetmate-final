"""Run this first:  python check_setup.py   -> tells you if everything is ready."""
import sys
ok = True
def check(name, fn):
    global ok
    try:
        print(f"[ OK ] {name}", fn() or "")
    except Exception as e:
        ok = False
        print(f"[FAIL] {name}: {e}")

def _cv():
    import cv2
    assert hasattr(cv2, "face"), "install opencv-contrib-python (not plain opencv-python)"
    return cv2.__version__
def _cascade():
    import face_auth as fa
    assert not fa._cascade.empty(), "face detector file missing: install opencv-contrib-python-headless==4.10.0.84"
    return "face detector loaded"
def _imp(m):
    return lambda: __import__(m).__name__

print("Python", sys.version.split()[0])
check("OpenCV + face module", _cv)
check("Face detector", _cascade)
for m in ["streamlit", "pandas", "faster_whisper", "anthropic", "dotenv"]:
    check(m, _imp(m))
print("\nAll good! Run:  streamlit run app.py" if ok else "\nFix the [FAIL] lines above, then run this again.")
