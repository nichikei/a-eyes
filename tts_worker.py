# One-shot SAPI5 speak then exit. Forces Vietnamese if available.
import sys, re, time, pyttsx3

_MIN_MS_PER_CHAR = 18

def _pick_vi(e):
    # Prefer Microsoft An; else any VI-ish voice
    for v in e.getProperty("voices"):
        nm = (v.name or "").lower()
        if "microsoft an" in nm: return v.id
    for v in e.getProperty("voices"):
        nm = (v.name or "").lower()
        if "viet" in nm or "vietnam" in nm or "vi-" in nm or "(vi" in nm:
            return v.id
    return None

def _speak_once(e, text):
    e.say(text)
    t0 = time.time()
    e.runAndWait()
    return int((time.time() - t0) * 1000)

def main():
    text = " ".join(sys.argv[1:]).strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return 0
    e = pyttsx3.init(driverName="sapi5")
    vid = _pick_vi(e)
    if vid:
        try: e.setProperty("voice", vid)
        except Exception: pass
    e.setProperty("rate", 165)
    dur = _speak_once(e, text)
    exp = max(500, len(text) * _MIN_MS_PER_CHAR)
    # if suspiciously short (clipped), retry once with a slight separator change
    if dur < exp * 0.55:
        _speak_once(e, text.replace(" với ", " — với "))
    return 0

if __name__ == "__main__":
    sys.exit(main())