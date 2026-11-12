"""Kopia zapasowa postępu: eksport profilu do pliku .zip i import jako nowy profil."""
import json
import os
import shutil
import sqlite3
import tempfile
import time
import zipfile

from . import VERSION, profiles

APP = "linux-espanol-learning"
MAX_DB = 300 * 1024 * 1024
REQUIRED_TABLES = {"settings", "lessons", "cards", "reviews"}


def default_name(db):
    name = profiles.active()["name"]
    safe = "".join(c if c.isalnum() else "-" for c in name).strip("-") or "profil"
    return f"espanol-kopia-{safe}-{time.strftime('%Y-%m-%d')}.zip"


def export_profile(db, dest):
    """Zapisuje spójną kopię bazy bieżącego profilu do dest (.zip). Zwraca dest."""
    tmp = tempfile.mkdtemp(prefix="espanol-bk-")
    try:
        snap = os.path.join(tmp, "profile.sqlite")
        out = sqlite3.connect(snap)
        with db.lock:
            db.con.backup(out)
        out.close()
        meta = {"app": APP, "version": VERSION, "profile": profiles.active()["name"],
                "exported": time.strftime("%Y-%m-%d %H:%M:%S")}
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(snap, "profile.sqlite")
            z.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        return dest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def inspect(path):
    """Sprawdza plik kopii. Zwraca meta (dict) albo zgłasza ValueError z czytelnym komunikatem."""
    if not zipfile.is_zipfile(path):
        raise ValueError("To nie jest plik kopii zapasowej (.zip).")
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if not {"profile.sqlite", "meta.json"} <= names:
            raise ValueError("Plik nie wygląda na kopię z tej aplikacji.")
        if z.getinfo("profile.sqlite").file_size > MAX_DB:
            raise ValueError("Plik kopii jest zbyt duży.")
        try:
            meta = json.loads(z.read("meta.json").decode("utf-8"))
        except Exception:  # noqa
            raise ValueError("Uszkodzone dane kopii (meta.json).")
    if meta.get("app") != APP:
        raise ValueError("Ta kopia pochodzi z innej aplikacji.")
    return meta


def import_profile(path):
    """Importuje kopię jako NOWY profil (nic nie nadpisuje). Zwraca id nowego profilu."""
    meta = inspect(path)
    tmp = tempfile.mkdtemp(prefix="espanol-im-")
    try:
        with zipfile.ZipFile(path) as z:
            data = os.path.join(tmp, "profile.sqlite")
            with z.open("profile.sqlite") as src, open(data, "wb") as dst:
                shutil.copyfileobj(src, dst)
        con = sqlite3.connect(data)
        try:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Baza w kopii jest uszkodzona.")
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            con.close()
        if not REQUIRED_TABLES <= tables:
            raise ValueError("Kopia nie zawiera danych postępu.")
        name = f"{meta.get('profile', 'Profil')} (import)"
        pid = profiles.add(name)
        shutil.copyfile(data, profiles.db_path(pid))
        return pid
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
