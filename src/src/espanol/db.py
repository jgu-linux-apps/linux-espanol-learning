"""Postęp nauki w SQLite."""
import json
import sqlite3
import threading
import time

from . import fsrs, profiles
from .i18n import _  # noqa: E402

SCHEMA = """
CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY, done_at REAL, score INTEGER, best INTEGER, attempts INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS cards (
    es TEXT PRIMARY KEY, pl TEXT, pos TEXT, lesson TEXT,
    state INTEGER DEFAULT 0, stability REAL, difficulty REAL, due REAL,
    last_review REAL, reps INTEGER DEFAULT 0, lapses INTEGER DEFAULT 0, added REAL);
CREATE TABLE IF NOT EXISTS reviews (ts REAL, es TEXT, grade INTEGER);
CREATE TABLE IF NOT EXISTS tests (ts REAL, kind TEXT, ref TEXT, score INTEGER, total INTEGER, details TEXT);
CREATE TABLE IF NOT EXISTS pron (ts REAL, target TEXT, heard TEXT, score INTEGER);
CREATE TABLE IF NOT EXISTS mistakes (ts REAL, source TEXT, q TEXT, given TEXT, expected TEXT);
CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, scenario TEXT, title TEXT, level TEXT,
    score INTEGER, turns TEXT, summary TEXT);
CREATE TABLE IF NOT EXISTS activity (day TEXT PRIMARY KEY, seconds INTEGER DEFAULT 0, items INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS drill (
    key TEXT PRIMARY KEY, ex TEXT, source TEXT, added REAL, due REAL,
    streak INTEGER DEFAULT 0, wrong INTEGER DEFAULT 1, last REAL);
"""


class DB:
    def __init__(self, path=None):
        profiles.migrate_shared()
        path = path or profiles.db_path(profiles.active_id())
        # silnik mowy czyta ustawienia z wątków w tle -> wspólne połączenie z blokadą
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.RLock()
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.con.commit()

    # ---- ustawienia ----
    def get(self, k, default=None):
        if k in profiles.SHARED_KEYS:
            v = profiles.shared_get(k, profiles._MISSING)
            if v is not profiles._MISSING:
                return v
        with self.lock:
            r = self.con.execute("SELECT v FROM settings WHERE k=?", (k,)).fetchone()
        return json.loads(r["v"]) if r else default

    def set(self, k, v):
        if k in profiles.SHARED_KEYS:
            profiles.shared_set(k, v)
            return
        with self.lock:
            self.con.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (k, json.dumps(v)))
            self.con.commit()

    # ---- lekcje ----
    def done_lessons(self):
        return {r["id"]: dict(r) for r in self.con.execute("SELECT * FROM lessons WHERE done_at IS NOT NULL")}

    def finish_lesson(self, lesson, score):
        now = time.time()
        r = self.con.execute("SELECT best, attempts FROM lessons WHERE id=?", (lesson.id,)).fetchone()
        best = max(score, r["best"] or 0) if r else score
        att = (r["attempts"] if r else 0) + 1
        self.con.execute("INSERT OR REPLACE INTO lessons VALUES (?,?,?,?,?)", (lesson.id, now, score, best, att))
        for v in lesson.vocab:
            self.con.execute(
                "INSERT OR IGNORE INTO cards (es, pl, pos, lesson, state, due, added) VALUES (?,?,?,?,0,?,?)",
                (v["es"], v["pl"], v["pos"], lesson.id, now, now))
        self.con.commit()
        self.log_activity(items=len(lesson.vocab))

    def mark_known(self, lesson):
        """Oznacza lekcję jako znaną (test poziomujący) — bez dodawania słówek do powtórek."""
        if self.con.execute("SELECT 1 FROM lessons WHERE id=?", (lesson.id,)).fetchone():
            return
        self.con.execute("INSERT INTO lessons VALUES (?,?,?,?,?)", (lesson.id, time.time(), 100, 100, 0))
        self.con.commit()

    def add_card(self, v):
        now = time.time()
        self.con.execute(
            "INSERT OR IGNORE INTO cards (es, pl, pos, lesson, state, due, added) VALUES (?,?,?,?,0,?,?)",
            (v["es"], v["pl"], v.get("pos", ""), v.get("lesson") or "słownik", now, now))
        self.con.commit()

    def has_card(self, es):
        return self.con.execute("SELECT 1 FROM cards WHERE es=?", (es,)).fetchone() is not None

    # ---- powtórki ----
    def due_cards(self, limit=200, new_limit=20):
        now = time.time()
        due = [dict(r) for r in self.con.execute(
            "SELECT * FROM cards WHERE state>0 AND due<=? ORDER BY due LIMIT ?", (now, limit))]
        new_today = self.new_reviewed_today()
        n = max(0, new_limit - new_today)
        new = [dict(r) for r in self.con.execute(
            "SELECT * FROM cards WHERE state=0 ORDER BY added, rowid LIMIT ?", (n,))]
        return due + new

    def new_reviewed_today(self):
        start = _day_start()
        return self.con.execute(
            "SELECT COUNT(DISTINCT r.es) FROM reviews r WHERE r.ts>=? AND r.es IN "
            "(SELECT es FROM cards WHERE reps<=3)", (start,)).fetchone()[0]

    def count_due(self):
        now = time.time()
        due = self.con.execute("SELECT COUNT(*) FROM cards WHERE state>0 AND due<=?", (now,)).fetchone()[0]
        new = self.con.execute("SELECT COUNT(*) FROM cards WHERE state=0").fetchone()[0]
        return due, new

    def grade(self, card, g):
        n = fsrs.review(card, g)
        self.con.execute(
            "UPDATE cards SET state=?, stability=?, difficulty=?, due=?, last_review=?, reps=?, lapses=? WHERE es=?",
            (n["state"], n["stability"], n["difficulty"], n["due"], n["last_review"], n["reps"],
             n.get("lapses") or 0, n["es"]))
        self.con.execute("INSERT INTO reviews VALUES (?,?,?)", (time.time(), card["es"], g))
        self.con.commit()
        self.log_activity(items=1)
        return n

    def hardest(self, n=3):
        """Najtrudniejsze słówka w powtórkach (najwięcej pomyłek, potem trudność) — na stronę „Dzisiaj”."""
        return [r["es"] for r in self.con.execute(
            "SELECT es FROM cards WHERE reps>0 ORDER BY lapses DESC, difficulty DESC LIMIT ?", (n,))]

    def reviewed_today(self):
        return self.con.execute("SELECT COUNT(*) FROM reviews WHERE ts>=?", (_day_start(),)).fetchone()[0]

    def lessons_done_today(self):
        return self.con.execute("SELECT COUNT(*) FROM lessons WHERE done_at>=?", (_day_start(),)).fetchone()[0]

    def card_stats(self):
        r = self.con.execute(
            "SELECT COUNT(*) total, SUM(state=0) nowe, SUM(state IN (1,3)) uczone, "
            "SUM(state=2 AND stability<21) powtarzane, SUM(state=2 AND stability>=21) opanowane FROM cards").fetchone()
        return {k: (r[k] or 0) for k in r.keys()}

    # ---- testy, wymowa, błędy ----
    def save_test(self, kind, ref, score, total, details=None):
        self.con.execute("INSERT INTO tests VALUES (?,?,?,?,?,?)",
                         (time.time(), kind, ref, score, total, json.dumps(details or {})))
        self.con.commit()

    def tests(self, kind=None):
        q = "SELECT * FROM tests" + (" WHERE kind=?" if kind else "") + " ORDER BY ts DESC"
        return [dict(r) for r in self.con.execute(q, (kind,) if kind else ())]

    def best_test(self, kind, ref):
        r = self.con.execute("SELECT MAX(100*score/total) b FROM tests WHERE kind=? AND ref=? AND total>0",
                             (kind, ref)).fetchone()
        return r["b"]

    def save_pron(self, target, heard, score):
        self.con.execute("INSERT INTO pron VALUES (?,?,?,?)", (time.time(), target, heard, score))
        self.con.commit()

    def pron_daily(self, days=30):
        """[(dzień, średni wynik, liczba prób)] z ostatnich dni."""
        since = time.time() - days * 86400
        return [(r["d"], r["a"], r["n"]) for r in self.con.execute(
            "SELECT strftime('%Y-%m-%d', ts, 'unixepoch', 'localtime') d, AVG(score) a, COUNT(*) n "
            "FROM pron WHERE ts>=? GROUP BY d ORDER BY d", (since,))]

    def pron_weak(self, n=6):
        """Zdania z najniższą średnią wynikiem (min. 2 próby, lub 1 gdy wynik < 60)."""
        return [(r["target"], r["a"], r["n"]) for r in self.con.execute(
            "SELECT target, AVG(score) a, COUNT(*) n FROM pron GROUP BY target "
            "HAVING (n>=2 OR a<60) AND a<90 ORDER BY a ASC LIMIT ?", (n,))]

    def pron_stats(self):
        r = self.con.execute("SELECT COUNT(*) n, AVG(score) avg FROM pron").fetchone()
        recent = self.con.execute("SELECT AVG(score) a FROM (SELECT score FROM pron ORDER BY ts DESC LIMIT 30)").fetchone()
        return r["n"], r["avg"], recent["a"]

    def save_mistake(self, source, q, given, expected):
        self.con.execute("INSERT INTO mistakes VALUES (?,?,?,?,?)", (time.time(), source, q, given, expected))
        self.con.commit()

    # ---- historia rozmów z botem ----
    def save_conversation(self, scenario, title, level, score, turns, summary):
        with self.lock:
            cur = self.con.execute(
                "INSERT INTO conversations (ts, scenario, title, level, score, turns, summary) VALUES (?,?,?,?,?,?,?)",
                (time.time(), scenario, title, level, score, json.dumps(turns, ensure_ascii=False),
                 json.dumps(summary, ensure_ascii=False)))
            self.con.commit()
            return cur.lastrowid

    def list_conversations(self, n=100):
        with self.lock:
            return [dict(r) for r in self.con.execute(
                "SELECT id, ts, scenario, title, level, score FROM conversations ORDER BY ts DESC LIMIT ?", (n,))]

    def get_conversation(self, cid):
        with self.lock:
            r = self.con.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["turns"] = json.loads(d["turns"])
        d["summary"] = json.loads(d["summary"])
        return d

    def delete_conversation(self, cid):
        with self.lock:
            self.con.execute("DELETE FROM conversations WHERE id=?", (cid,))
            self.con.commit()

    def recent_mistakes(self, n=50):
        return [dict(r) for r in self.con.execute("SELECT * FROM mistakes ORDER BY ts DESC LIMIT ?", (n,))]

    # ---- aktywność ----
    def log_activity(self, seconds=0, items=0):
        day = time.strftime("%Y-%m-%d")
        self.con.execute("INSERT OR IGNORE INTO activity VALUES (?,0,0)", (day,))
        self.con.execute("UPDATE activity SET seconds=seconds+?, items=items+? WHERE day=?", (seconds, items, day))
        self.con.commit()

    def activity(self, days=30):
        return [dict(r) for r in self.con.execute("SELECT * FROM activity ORDER BY day DESC LIMIT ?", (days,))]

    def today_seconds(self):
        r = self.con.execute("SELECT seconds FROM activity WHERE day=?", (time.strftime("%Y-%m-%d"),)).fetchone()
        return r["seconds"] if r else 0

    def streak(self):
        """(seria dni z nauką, najdłuższa seria). Dzień aktywny = min. 1 min nauki lub ukończone elementy."""
        rows = self.con.execute("SELECT day, seconds, items FROM activity").fetchall()
        active = {r["day"] for r in rows if r["seconds"] >= 60 or r["items"] > 0}
        import datetime
        day = datetime.date.today()
        if day.strftime("%Y-%m-%d") not in active:
            day -= datetime.timedelta(days=1)     # dziś jeszcze można podtrzymać serię
        cur = 0
        while day.strftime("%Y-%m-%d") in active:
            cur += 1
            day -= datetime.timedelta(days=1)
        best, run, prev = 0, 0, None
        for d in sorted(active):
            dt = datetime.date.fromisoformat(d)
            run = run + 1 if prev and (dt - prev).days == 1 else 1
            best, prev = max(best, run), dt
        return cur, max(best, cur)

    # ---- trening błędów (zakładka Powtórki → Błędy) ----
    def drill_add(self, ex, now=None):
        """Błędna odpowiedź: ćwiczenie trafia (lub wraca) do treningu, termin — jutro."""
        from . import drill
        now = now or time.time()
        item = drill.clean(ex)
        key = drill.key(item)
        due = drill.due_after(drill.WRONG_DAYS, now)
        with self.lock:
            r = self.con.execute("SELECT key FROM drill WHERE key=?", (key,)).fetchone()
            if r:
                self.con.execute("UPDATE drill SET streak=0, wrong=wrong+1, due=?, last=?, ex=? WHERE key=?",
                                 (due, now, json.dumps(item, ensure_ascii=False), key))
            else:
                self.con.execute("INSERT INTO drill VALUES (?,?,?,?,?,0,1,?)",
                                 (key, json.dumps(item, ensure_ascii=False), item.get("source", ""),
                                  now, due, now))
            self.con.commit()
        return key

    def drill_answer(self, key, result, now=None):
        """result: 'ok' | 'typo' | 'wrong'. Zwraca 'done' (opanowane i usunięte), 'next' lub 'again'."""
        from . import drill
        now = now or time.time()
        with self.lock:
            r = self.con.execute("SELECT streak FROM drill WHERE key=?", (key,)).fetchone()
            if not r:
                return "done"
            if result == "ok":
                streak = r["streak"] + 1
                if streak >= drill.DONE_STREAK:
                    self.con.execute("DELETE FROM drill WHERE key=?", (key,))
                    self.con.execute("INSERT OR REPLACE INTO settings VALUES ('drill_mastered', ?)",
                                     (json.dumps(self.get("drill_mastered", 0) + 1),))
                    self.con.commit()
                    return "done"
                self.con.execute("UPDATE drill SET streak=?, due=?, last=? WHERE key=?",
                                 (streak, drill.due_after(drill.OK_DAYS[streak], now), now, key))
                out = "next"
            elif result == "typo":
                self.con.execute("UPDATE drill SET due=?, last=? WHERE key=?",
                                 (drill.due_after(drill.WRONG_DAYS, now), now, key))
                out = "again"
            else:
                self.con.execute("UPDATE drill SET streak=0, wrong=wrong+1, due=?, last=? WHERE key=?",
                                 (drill.due_after(drill.WRONG_DAYS, now), now, key))
                out = "again"
            self.con.commit()
        return out

    def drill_due(self, limit=10, now=None):
        now = now or time.time()
        with self.lock:
            rows = self.con.execute("SELECT * FROM drill WHERE due<=? ORDER BY due, added LIMIT ?",
                                    (now, limit)).fetchall()
        return [dict(r, ex=json.loads(r["ex"])) for r in rows]

    def drill_all(self):
        with self.lock:
            rows = self.con.execute("SELECT * FROM drill ORDER BY due, added").fetchall()
        return [dict(r, ex=json.loads(r["ex"])) for r in rows]

    def drill_counts(self, now=None):
        """(do powtórki teraz, wszystkie w treningu)."""
        now = now or time.time()
        with self.lock:
            due = self.con.execute("SELECT COUNT(*) FROM drill WHERE due<=?", (now,)).fetchone()[0]
            total = self.con.execute("SELECT COUNT(*) FROM drill").fetchone()[0]
        return due, total

    def drill_delete(self, key):
        with self.lock:
            self.con.execute("DELETE FROM drill WHERE key=?", (key,))
            self.con.commit()

    def reset(self):
        for t in ("lessons", "cards", "reviews", "tests", "pron", "mistakes", "activity", "drill"):
            self.con.execute(f"DELETE FROM {t}")
        self.con.execute("DELETE FROM settings WHERE k='drill_mastered'")
        self.con.commit()


def _day_start():
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, -1))
