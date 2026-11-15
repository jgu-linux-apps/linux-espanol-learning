"""Profile użytkowników: osobny postęp, ustawienia osobiste i dane „O mnie” dla każdej osoby.
Wspólne dla wszystkich profili (silniki, modele, klucz API, ustawienia bota/mowy) są trzymane osobno."""
import json
import os
import re
import shutil
import threading

from .paths import USER_DATA, DB_PATH

REG = os.path.join(USER_DATA, "profiles.json")
SHARED_FILE = os.path.join(USER_DATA, "shared.json")
PROFILES_DIR = os.path.join(USER_DATA, "profiles")
DEFAULT_ID = "default"

# ustawienia „maszynowe” — wspólne dla wszystkich profili
SHARED_KEYS = {"whisper", "cuda", "setup_offered", "bot_backend", "ollama_url", "ollama_model",
               "ollama_managed", "claude_model", "bot_silence"}

_lock = threading.RLock()


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load():
    with _lock:
        reg = _read(REG, None)
        if not reg or not reg.get("profiles"):
            from .i18n import system_lang
            lang = system_lang()
            reg = {"active": DEFAULT_ID,
                   "profiles": [{"id": DEFAULT_ID, "name": "Główny" if lang == "pl" else "Main", "lang": lang}]}
            _write(REG, reg)
        if reg["active"] not in [p["id"] for p in reg["profiles"]]:
            reg["active"] = reg["profiles"][0]["id"]
        return reg


def all_profiles():
    return load()["profiles"]


def active_id():
    return load()["active"]


def active():
    reg = load()
    return next(p for p in reg["profiles"] if p["id"] == reg["active"])


def db_path(pid):
    if pid == DEFAULT_ID:
        return DB_PATH                      # zachowuje dotychczasowy postęp
    d = os.path.join(PROFILES_DIR, pid)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "postep.db")


def set_active(pid):
    with _lock:
        reg = load()
        if pid in [p["id"] for p in reg["profiles"]]:
            reg["active"] = pid
            _write(REG, reg)


def add(name, lang=None):
    with _lock:
        reg = load()
        base = re.sub(r"[^a-z0-9]+", "-", name.lower().encode("ascii", "ignore").decode()).strip("-") or "profil"
        pid, n = base, 2
        ids = {p["id"] for p in reg["profiles"]}
        while pid in ids or pid == DEFAULT_ID:
            pid, n = f"{base}-{n}", n + 1
        entry = {"id": pid, "name": name.strip()[:30] or "Profil"}
        if lang:
            entry["lang"] = lang
        reg["profiles"].append(entry)
        _write(REG, reg)
        return pid


def rename(pid, name):
    with _lock:
        reg = load()
        for p in reg["profiles"]:
            if p["id"] == pid:
                p["name"] = name.strip()[:30] or p["name"]
        _write(REG, reg)


def set_lang(pid, lang):
    with _lock:
        reg = load()
        for p in reg["profiles"]:
            if p["id"] == pid:
                p["lang"] = lang
        _write(REG, reg)


def delete(pid):
    """Usuwa profil (nie główny, nie ostatni) razem z jego postępem."""
    with _lock:
        reg = load()
        if pid == DEFAULT_ID or len(reg["profiles"]) < 2:
            return False
        reg["profiles"] = [p for p in reg["profiles"] if p["id"] != pid]
        if reg["active"] == pid:
            reg["active"] = reg["profiles"][0]["id"]
        _write(REG, reg)
        shutil.rmtree(os.path.join(PROFILES_DIR, pid), ignore_errors=True)
        return True


# ---- wspólne ustawienia
_MISSING = object()


def shared_get(k, default=_MISSING):
    with _lock:
        return _read(SHARED_FILE, {}).get(k, default)


def shared_set(k, v):
    with _lock:
        d = _read(SHARED_FILE, {})
        d[k] = v
        _write(SHARED_FILE, d)


def migrate_shared():
    """Jednorazowo: wspólne ustawienia z dotychczasowej bazy (przed profilami) → plik shared.json."""
    if os.path.exists(SHARED_FILE) or not os.path.exists(DB_PATH):
        return
    try:
        import sqlite3
        con = sqlite3.connect(DB_PATH)
        data = {}
        for k, v in con.execute("SELECT k, v FROM settings"):
            if k in SHARED_KEYS:
                data[k] = json.loads(v)
        con.close()
        _write(SHARED_FILE, data)
    except Exception:  # noqa
        pass


DEFAULT_NAMES = {"pl": "Główny", "en": "Main"}


def display_name(p):
    """The default profile's name follows the profile's course language until someone renames it."""
    name = (p or {}).get("name", "")
    if name in DEFAULT_NAMES.values():
        from .i18n import profile_lang
        return DEFAULT_NAMES.get(profile_lang(p), name)
    return name
