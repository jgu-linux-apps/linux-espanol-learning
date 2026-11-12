"""Trening błędów: ćwiczenia, w których się pomyliłeś, wracają aż do opanowania.

Cykl: błąd → wraca jutro → dobrze → za 3 dni → dobrze → za 7 dni → dobrze → opanowane (znika).
Pomyłka po drodze zaczyna cykl od nowa. Literówka nie przesuwa cyklu (wraca jutro).
Logika bez GTK — używana przez db.py i ekran Powtórki → Błędy.
"""
import hashlib
import json
import time

WRONG_DAYS = 1                 # po błędzie: jutro
OK_DAYS = {1: 3, 2: 7}         # po 1. i 2. poprawnej odpowiedzi z rzędu
DONE_STREAK = 3                # 3 poprawne z rzędu = opanowane
ROUND = 10                     # zadań w jednej rundzie

FIELDS = ("type", "q", "answers", "options", "hint", "audio", "shuffle", "source", "note")


def clean(ex):
    """Tylko pola potrzebne do odtworzenia ćwiczenia (JSON-owalne)."""
    out = {k: ex[k] for k in FIELDS if k in ex and ex[k] not in (None, "")}
    out["answers"] = [str(a) for a in (ex.get("answers") or [])]
    out["options"] = [str(o) for o in (ex.get("options") or [])]
    out.setdefault("type", "text")
    out.setdefault("q", "")
    return out


def key(ex):
    """Ten sam typ + pytanie + pierwsza odpowiedź = to samo zadanie (opcje wyboru mogą się losować)."""
    first = (ex.get("answers") or [""])[0]
    raw = json.dumps([ex.get("type", ""), ex.get("q", ""), first], ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def day_start(t):
    lt = time.localtime(t)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))


def due_after(days, now):
    """Początek dnia za `days` dni (zadanie jest „na dziś” od rana tamtego dnia)."""
    lt = time.localtime(now)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday + days, 0, 0, 0, 0, 0, -1))


def from_bot_fix(orig, ok, fix):
    """Poprawka Paco → zadanie „Popraw zdanie”. None, gdy nie ma czego poprawiać."""
    from .answers import norm
    orig, ok = (orig or "").strip(), (ok or "").strip()
    if not orig or not ok or norm(orig) == norm(ok):
        return None
    return dict(type="fix", q=orig, answers=[ok], options=[], note=(fix or "").strip(), source="bot")


def migrate_mistakes(db, course):
    """Jednorazowo: dotychczasowe błędy (tabela mistakes, tylko tekst) → trening.
    Dla błędów z lekcji odtwarza pełne ćwiczenie z treści kursu (dopasowanie po pytaniu i odpowiedzi)."""
    if db.get("drill_migrated"):
        return 0
    from .answers import norm
    rows = db.con.execute("SELECT source, q, given, expected, MAX(ts) ts FROM mistakes "
                          "GROUP BY source, q, expected ORDER BY ts").fetchall()
    cache = {}
    n = 0
    for r in rows:
        src, q, exp = r["source"] or "", r["q"] or "", r["expected"] or ""
        ex = None
        if src == "bot":
            ok, sep, fix = exp.partition(" — ")
            ex = from_bot_fix(q, ok if sep else "", fix if sep else exp)
        else:
            les = course.by_id.get(src) if course else None
            if les is not None:
                if src not in cache:
                    cache[src] = les.all_exercises()
                for cand in cache[src]:
                    if cand.get("q") == q and any(norm(a) == norm(exp) for a in cand.get("answers", [])):
                        ex = dict(cand)
                        break
            if ex is None and q and exp:
                ex = dict(type="text", q=q, answers=[exp], options=[], source=src)
        if ex:
            db.drill_add(ex, now=r["ts"] - WRONG_DAYS * 86400)   # termin = dziś: do zrobienia od razu
            n += 1
    db.set("drill_migrated", True)
    return n
