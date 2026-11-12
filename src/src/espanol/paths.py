import os

APP_ID = "io.github.jgu.EspanolLearning"
APP_NAME = "Linux Español Learning"
PKG = "linux-espanol-learning"

HERE = os.path.dirname(os.path.abspath(__file__))
# Dane kursu: obok pakietu (instalacja .deb) lub w repozytorium (tryb deweloperski)
_cands = [os.path.join(HERE, "..", "data"),          # /usr/share/linux-espanol-learning/data
          os.path.join(HERE, "..", "..", "data"),    # repozytorium: src/espanol -> data
          f"/usr/share/{PKG}/data"]
DATA = next((os.path.abspath(p) for p in _cands if os.path.isdir(p)), _cands[0])

XDG_DATA = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
XDG_CACHE = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
XDG_CONFIG = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

USER_DATA = os.path.join(XDG_DATA, PKG)
VENV = os.path.join(USER_DATA, "engine")
VOICES = os.path.join(USER_DATA, "voices")
MODELS = os.path.join(USER_DATA, "whisper")
DB_PATH = os.path.join(USER_DATA, "postep.db")
CACHE = os.path.join(XDG_CACHE, PKG)
TTS_CACHE = os.path.join(CACHE, "tts")
REC_DIR = os.path.join(CACHE, "nagrania")

for _d in (USER_DATA, CACHE, TTS_CACHE, REC_DIR):
    os.makedirs(_d, exist_ok=True)
