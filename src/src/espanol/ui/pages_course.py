"""Ekrany: Dzisiaj, Kurs, Lekcja."""
import random
import time
import urllib.parse

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

from .widgets import (label, rich_text, scrolled, page_box, card, SpeakButton, slow_button, clear, Ring, dot,
                      stars_for)
from .exercise import ExerciseRunner
from .pron import SpeakPractice
from ..content import POS_NAMES


def _greeting():
    h = time.localtime().tm_hour
    if h < 13:
        return "¡Buenos días!"
    if h < 20:
        return "¡Buenas tardes!"
    return "¡Buenas noches!"


def _bar(frac, width=180):
    """Pasek postępu z procentem obok."""
    frac = max(0.0, min(1.0, frac))
    box = Gtk.Box(spacing=8)
    box.set_valign(Gtk.Align.CENTER)
    pb = Gtk.ProgressBar()
    pb.set_fraction(frac)
    pb.set_size_request(width, -1)
    pb.set_valign(Gtk.Align.CENTER)
    pb.set_hexpand(True)
    box.pack_start(pb, True, True, 0)
    pct = label(f"{round(frac * 100)}%", wrap=False)
    pct.set_width_chars(4)
    pct.set_xalign(1.0)
    box.pack_start(pct, False, False, 0)
    return box


def _today_progress_table(self, done):
    app, course, db = self.app, self.app.course, self.app.db
    c = card(spacing=8)
    total = len(course.lessons)
    head = Gtk.Box(spacing=12)
    head.pack_start(label("Postęp kursu", "title2", wrap=False), False, False, 0)
    head.pack_end(_bar(len(done) / max(1, total), 260), False, False, 0)
    head.pack_end(label(f"Cały kurs: {len(done)}/{total} lekcji", "dim", wrap=False), False, False, 0)
    c.pack_start(head, False, False, 0)
    g = Gtk.Grid(column_spacing=18, row_spacing=6)
    for i, h in enumerate(["Dział", "Lekcje", "Postęp", "Śr. wynik lekcji", "Test działu"]):
        g.attach(label(f"<b>{h}</b>", markup=True, wrap=False), i, 0, 1, 1)
    r = 1
    for level in ("A1", "A2"):
        units = course.units(level)
        lv_all = sum(len(x) for x in units.values())
        lv_done = sum(1 for x in units.values() for l in x if l.id in done)
        lvl = label(f"<b>Poziom {level}</b>", markup=True, wrap=False)
        g.attach(lvl, 0, r, 1, 1)
        g.attach(label(f"{lv_done}/{lv_all}", wrap=False), 1, r, 1, 1)
        g.attach(_bar(lv_done / max(1, lv_all)), 2, r, 1, 1)
        best = db.best_test("exam", level)
        g.attach(label("", wrap=False), 3, r, 1, 1)
        g.attach(label(f"egzamin: {best}%" if best is not None else "egzamin: —", "dim", wrap=False), 4, r, 1, 1)
        r += 1
        for unit, lessons in sorted(units.items()):
            nd = [done[l.id]["best"] for l in lessons if l.id in done]
            title = course.unit_title(level, unit).split("—")[0].strip()
            lb = label(f"   {unit}. {title}", wrap=False)
            g.attach(lb, 0, r, 1, 1)
            g.attach(label(f"{len(nd)}/{len(lessons)}", "dim", wrap=False), 1, r, 1, 1)
            g.attach(_bar(len(nd) / max(1, len(lessons))), 2, r, 1, 1)
            g.attach(label(f"{round(sum(nd) / len(nd))}%" if nd else "—", "dim", wrap=False), 3, r, 1, 1)
            bt = db.best_test("unit", f"{level}-{unit}")
            g.attach(label(f"{bt}%" if bt is not None else "—", "dim", wrap=False), 4, r, 1, 1)
            r += 1
    c.pack_start(g, False, False, 0)
    st = db.card_stats()
    words = len(course.dictionary)
    wrow = Gtk.Box(spacing=12)
    wrow.pack_start(label(f"Słówka opanowane: {st['opanowane']} z {words} w słowniku", "dim", wrap=False),
                    False, False, 0)
    wrow.pack_end(_bar(st["opanowane"] / max(1, words), 260), False, False, 0)
    c.pack_start(wrow, False, False, 0)
    return c


# ====================================================================== DZISIAJ
_DAYS = ["pn", "wt", "śr", "cz", "pt", "so", "nd"]
_WEEKDAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
_MONTHS = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września",
           "października", "listopada", "grudnia"]
_TABS = ["intro", "vocab", "grammar", "ex", "speak"]
_TAB_SHORT = {"intro": "Dialog", "vocab": "Słówka", "grammar": "Gramatyka", "ex": "Ćwiczenia", "speak": "Mówienie"}
# ćwiczenie dnia w „Planie na dziś” — zmienia się codziennie
_DAILY = [("scenes", "Scenka z Paco", "mówienie · ok. 6 min", "face-smile-symbolic"),
          ("pron", "Laboratorium wymowy", "wymowa · ok. 5 min", "audio-input-microphone-symbolic"),
          ("dictation", "Dyktando", "słuchanie i pisanie · ok. 5 min", "document-edit-symbolic"),
          ("readings", "Czytanka", "czytanie · ok. 6 min", "x-office-document-symbolic")]


def _btn(text, primary=False, cb=None, small=False):
    b = Gtk.Button(label=text)
    if primary:
        b.get_style_context().add_class("suggested-action")
    b.set_valign(Gtk.Align.CENTER)
    if cb:
        b.connect("clicked", lambda *_: cb())
    return b


def _current_lesson(app):
    """(lekcja, krok, czy_w_trakcie): ostatnio otwarta niedokończona albo następna z kursu."""
    db, course = app.db, app.course
    done = db.done_lessons()
    last = db.get("last_lesson")
    if last and last.get("id") in course.by_id and last["id"] not in done:
        return course.by_id[last["id"]], last.get("tab") or "intro", True
    nxt = course.next_lesson(set(done))
    return nxt, "intro", False


class TodayPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.refresh()

    def refresh(self):
        app, db, course = self.app, self.app.db, self.app.course
        clear(self.inner)
        b = self.inner
        done = db.done_lessons()

        # powitanie, data i tydzień nauki
        from .. import profiles
        name = profiles.active().get("name", "")
        hello = _greeting()
        if name and name != "Główny":
            hello = hello.rstrip("!") + f", {name}!"
        t = time.localtime()
        top = Gtk.Box(spacing=12)
        top.pack_start(label(hello, "hello", wrap=False), False, False, 0)
        dt = label(f"{_WEEKDAYS[t.tm_wday]}, {t.tm_mday} {_MONTHS[t.tm_mon - 1]}", "dim", wrap=False)
        dt.set_valign(Gtk.Align.END)
        dt.set_margin_bottom(3)
        top.pack_start(dt, False, False, 0)
        top.pack_end(self._week(), False, False, 0)
        b.pack_start(top, False, False, 0)

        if not done and not db.get("placement_offered"):
            pc = card(spacing=4)
            pr = Gtk.Box(spacing=12)
            pr.pack_start(label("Znasz już trochę hiszpańskiego? Zrób krótki test poziomujący, a podpowiem, "
                                "od której lekcji zacząć."), True, True, 0)
            pr.pack_start(_btn("Zrób test", True, app.open_placement), False, False, 0)
            pr.pack_start(_btn("Zaczynam od zera", cb=lambda: (db.set("placement_offered", True), self.refresh())),
                          False, False, 0)
            pc.pack_start(pr, False, False, 0)
            b.pack_start(pc, False, False, 0)

        b.pack_start(self._hero(done), False, False, 0)

        cols = Gtk.Grid(column_spacing=14, row_spacing=14)
        plan = self._plan(done)
        plan.set_hexpand(True)
        cols.attach(plan, 0, 0, 1, 1)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        right.set_size_request(380, -1)
        right.pack_start(self._reviews(), False, False, 0)
        w = self._word()
        if w:
            right.pack_start(w, False, False, 0)
        cols.attach(right, 1, 0, 1, 1)
        b.pack_start(cols, False, False, 0)

        if not app.speech.tts_available() or not app.speech.stt_available():
            n = card(spacing=4)
            n.get_style_context().add_class("notice")
            row = Gtk.Box(spacing=12)
            row.pack_start(label("🎙️ Nagrania i ocena wymowy potrzebują jednorazowo silnika mowy "
                                 "(ok. 0,3–0,7 GB). Potem wszystko działa offline.", "dim"), True, True, 0)
            row.pack_start(_btn("Zainstaluj", cb=app.open_setup), False, False, 0)
            n.pack_start(row, False, False, 0)
            b.pack_start(n, False, False, 0)
        self.show_all()

    def _week(self):
        """Bieżący tydzień: 🔥 dni z nauką, przerywane kółko = dziś jeszcze bez nauki."""
        import datetime
        act = {a["day"] for a in self.app.db.activity(14) if a["seconds"] >= 60 or a["items"] > 0}
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        box = Gtk.Box(spacing=6)
        for i in range(7):
            d = monday + datetime.timedelta(days=i)
            on = d.strftime("%Y-%m-%d") in act
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            dl = Gtk.Label(label="🔥" if on else ("·" if d == today else ""))
            dl.get_style_context().add_class("week")
            dl.get_style_context().add_class("week-on" if on else "week-today" if d == today else "week-off")
            col.pack_start(dl, False, False, 0)
            col.pack_start(label(_DAYS[i], "week-day", wrap=False, xalign=0.5), False, False, 0)
            box.pack_start(col, False, False, 0)
        return box

    def _hero(self, done):
        app, db, course = self.app, self.app.db, self.app.course
        c = card(spacing=6)
        row = Gtk.Box(spacing=24)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        les, tab, started = _current_lesson(app)
        if les:
            step = _TABS.index(tab) if tab in _TABS else 0
            col.pack_start(label(("KONTYNUUJ" if started else "NASTĘPNA LEKCJA") + f" · {les.level} · DZIAŁ {les.unit}",
                                 "kicker"), False, False, 0)
            col.pack_start(label(f"Lekcja {les.number}: {les.title.split('—')[0].strip()}", "hero-title"), False, False, 0)
            sub = les.title.split("—", 1)[1].strip() if "—" in les.title else " · ".join(les.goals[:2])
            col.pack_start(label(sub, "dim"), False, False, 0)
            pr = Gtk.Box(spacing=10)
            pb = Gtk.ProgressBar()
            pb.set_fraction(step / len(_TABS))
            pb.set_size_request(300, -1)
            pb.set_valign(Gtk.Align.CENTER)
            pr.pack_start(pb, False, False, 0)
            pr.pack_start(label(f"{step} z {len(_TABS)} części", "dim", wrap=False), False, False, 0)
            pr.set_margin_top(6)
            col.pack_start(pr, False, False, 0)
            btns = Gtk.Box(spacing=10)
            btns.set_margin_top(10)
            btns.pack_start(_btn("▶  Kontynuuj lekcję" if started else "▶  Zacznij lekcję", True,
                                 lambda: app.open_lesson(les.id, tab)), False, False, 0)
            due, new = db.count_due()
            if due + new:
                btns.pack_start(_btn("Szybka powtórka · 5 min", cb=lambda: app.open_review("cards")), False, False, 0)
            col.pack_start(btns, False, False, 0)
            level = les.level
        else:
            col.pack_start(label("CAŁY KURS UKOŃCZONY", "kicker"), False, False, 0)
            col.pack_start(label("¡Enhorabuena! 🎉", "hero-title"), False, False, 0)
            col.pack_start(label("Powtarzaj słówka, rób egzaminy próbne i czytaj czytanki.", "dim"), False, False, 0)
            level = "A2"
        row.pack_start(col, True, True, 0)

        # kółka: cel dzienny, seria, poziom
        goal = int(db.get("daily_goal", 10))
        got = db.today_seconds() / 60.0
        cur, best = db.streak()
        today_on = db.today_seconds() >= 60 or db.reviewed_today() > 0 or db.lessons_done_today() > 0
        units = course.units(level)
        lv_all = sum(len(x) for x in units.values())
        lv_done = sum(1 for x in units.values() for l in x if l.id in done)
        rings = Gtk.Box(spacing=18)
        for ring, cap in ((Ring(app, got / max(1, goal), int(min(got, 999)), f"/ {goal} min"), "Cel dzienny"),
                          (Ring(app, 1.0 if today_on else (0.5 if cur else 0.0), cur, "dni", "ring2"), "Seria 🔥"),
                          (Ring(app, lv_done / max(1, lv_all), f"{round(100 * lv_done / max(1, lv_all))}%", level, "ring3"),
                           f"Poziom {level}")):
            rc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            rc.pack_start(ring, False, False, 0)
            rc.pack_start(label(cap, "dim", wrap=False, xalign=0.5), False, False, 0)
            if cap.startswith("Seria") and best > 1:
                rc.set_tooltip_text(f"Rekord: {best} dni")
            rings.pack_start(rc, False, False, 0)
        row.pack_start(rings, False, False, 0)
        c.pack_start(row, False, False, 0)
        return c

    def _plan(self, done):
        """Plan na dziś: powtórka, lekcja, ćwiczenie dnia — odhaczane po kolei."""
        app, db = self.app, self.app.db
        c = card(spacing=0)
        head = Gtk.Box(spacing=8)
        head.set_margin_bottom(8)
        head.pack_start(label("PLAN NA DZIŚ", "kicker", wrap=False), False, False, 0)
        due, new = db.count_due()
        n_rev = due + min(new, int(db.get("new_per_day", 20)))
        les, tab, _st = _current_lesson(app)
        daily = _DAILY[time.localtime().tm_yday % len(_DAILY)]
        items = [
            ("Powtórka słówek", f"{n_rev} słówek · ok. {max(2, n_rev // 3)} min" if n_rev else "wszystko powtórzone",
             n_rev == 0, lambda: app.open_review("cards")),
            self._lesson_item(les, tab, db.lessons_done_today()),
            (daily[1], daily[2], False, lambda key=daily[0]: app.show_page(key)),
        ]
        n_done = sum(1 for it in items if it[2])
        head.pack_end(label(f"{n_done} z {len(items)} · ok. 20 min", "dim", wrap=False), False, False, 0)
        c.pack_start(head, False, False, 0)
        cur_set = False
        for i, (title, desc, is_done, cb) in enumerate(items):
            state = "done" if is_done else ("cur" if not cur_set else "todo")
            cur_set = cur_set or state == "cur"
            r = Gtk.Box(spacing=12)
            r.get_style_context().add_class("plan-row")
            r.pack_start(dot("▶" if state == "cur" else "", state), False, False, 0)
            tcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            esc = GLib.markup_escape_text(title)
            tcol.pack_start(label(f"<s>{esc}</s>" if is_done else f"<b>{esc}</b>", markup=True,
                                  cls="dim" if is_done else None), False, False, 0)
            tcol.pack_start(label(desc, "dim"), False, False, 0)
            r.pack_start(tcol, True, True, 0)
            if cb and not is_done:
                r.pack_start(_btn("Start", state == "cur", cb), False, False, 0)
            c.pack_start(r, False, False, 0)
        return c

    def _lesson_item(self, les, tab, done_today):
        """Punkt planu „lekcja”: zaliczony, gdy dziś ukończono lekcję (wtedy podpowiada następną)."""
        app = self.app
        if not les:
            return ("Kurs ukończony", "", True, None)
        short = f"Lekcja {les.number}: {les.title.split('—')[0].strip()}"
        if done_today:
            return (f"Lekcja ukończona dziś ({done_today})", f"następna: {short}", True, None)
        return (short, f"{_TAB_SHORT.get(tab, '')} · ok. 10 min", False, lambda: app.open_lesson(les.id, tab))

    def _reviews(self):
        app, db = self.app, self.app.db
        due, new = db.count_due()
        n = due + min(new, int(db.get("new_per_day", 20)))
        d_due, _d_total = db.drill_counts()
        c = card(spacing=4)
        row = Gtk.Box(spacing=10)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        col.pack_start(label("POWTÓRKI", "kicker", wrap=False), False, False, 0)
        num = Gtk.Box(spacing=8)
        num.pack_start(label(str(n), "stat-big", wrap=False), False, False, 0)
        sl = label("słówek dziś", "dim", wrap=False)
        sl.set_valign(Gtk.Align.END)
        sl.set_margin_bottom(5)
        num.pack_start(sl, False, False, 0)
        col.pack_start(num, False, False, 0)
        row.pack_start(col, True, True, 0)
        bb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        rv = _btn("Powtórz", True, lambda: app.open_review("cards"))
        rv.set_sensitive(n > 0)
        bb.pack_start(rv, False, False, 0)
        if d_due:
            bb.pack_start(_btn(f"Błędy ({d_due})", cb=lambda: app.open_review("drill")), False, False, 0)
        row.pack_start(bb, False, False, 0)
        c.pack_start(row, False, False, 0)
        hard = db.hardest(3)
        if hard:
            c.pack_start(label("Najtrudniejsze: <b>" + " · ".join(GLib.markup_escape_text(h) for h in hard) + "</b>",
                               "dim", markup=True), False, False, 0)
        return c

    def _word(self):
        words = [w for w in self.app.course.dictionary if w.get("ex_es")]
        if not words:
            return None
        w = random.Random(time.strftime("%Y%m%d")).choice(words)
        c = card(spacing=4)
        c.pack_start(label("SŁOWO DNIA", "kicker", wrap=False), False, False, 0)
        row = Gtk.Box(spacing=6)
        row.pack_start(label(w["es"], "big-es", wrap=False), False, False, 0)
        row.pack_start(SpeakButton(self.app, w["es"]), False, False, 0)
        c.pack_start(row, False, False, 0)
        c.pack_start(label(w["pl"], "dim"), False, False, 0)
        ex = Gtk.Box(spacing=6)
        ex.pack_start(label(f"{w['ex_es']} — {w['ex_pl']}", "dim"), True, True, 0)
        ex.pack_start(SpeakButton(self.app, w["ex_es"]), False, False, 0)
        c.pack_start(ex, False, False, 0)
        return c


# ====================================================================== KURS
class CoursePage(Gtk.Box):
    LEVELS = {"A1": "Poziom początkujący — przetrwanie w codziennych sytuacjach",
              "A2": "Poziom podstawowy — przeszłość, przyszłość, opowiadanie, opinie"}

    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.level = None
        self.open_units = set()          # działy rozwinięte ręcznie
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.refresh()

    def _set_level(self, level):
        self.level = level
        self.refresh()

    def _toggle_unit(self, key):
        (self.open_units.discard if key in self.open_units else self.open_units.add)(key)
        self.refresh()

    def refresh(self):
        app, db, course = self.app, self.app.db, self.app.course
        clear(self.inner)
        done = db.done_lessons()
        cur, cur_tab, started = _current_lesson(app)
        if self.level is None:
            self.level = cur.level if cur else "A1"
        level = self.level

        head = Gtk.Box(spacing=14)
        head.pack_start(label("Kurs", "hero", wrap=False), False, False, 0)
        sw = Gtk.Box(spacing=4)
        sw.get_style_context().add_class("lvl-switch")
        for lv in ("A1", "A2"):
            units = course.units(lv)
            n_all = sum(len(u) for u in units.values())
            n_done = sum(1 for u in units.values() for l in u if l.id in done)
            bt = _btn(f"{lv} · {n_done}/{n_all}", lv == level, (lambda lv=lv: self._set_level(lv)))
            sw.pack_start(bt, False, False, 0)
        head.pack_start(sw, False, False, 0)
        head.pack_end(_btn(f"Egzamin próbny {level}", cb=lambda: app.start_exam(level)), False, False, 0)
        self.inner.pack_start(head, False, False, 0)
        self.inner.pack_start(label(f"{level} · {self.LEVELS[level]} · Hiszpania (castellano). Lekcje możesz robić "
                                    "w dowolnej kolejności, ale najlepiej po kolei.", "dim"), False, False, 0)

        for unit, lessons in sorted(course.units(level).items()):
            key = f"{level}-{unit}"
            nd = [done[l.id]["best"] for l in lessons if l.id in done]
            all_done = len(nd) == len(lessons)
            has_cur = cur is not None and any(l.id == cur.id for l in lessons)
            expanded = (has_cur and key not in self.open_units) or (not has_cur and key in self.open_units)
            c = card(spacing=8)
            uh = Gtk.Box(spacing=14)
            ring = Ring(app, 1.0 if all_done else len(nd) / max(1, len(lessons)),
                        "✓" if all_done else f"{len(nd)}/{len(lessons)}", "", "#16A34A" if all_done else "accent",
                        size=54, width=6)
            uh.pack_start(ring, False, False, 0)
            tcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            tcol.set_valign(Gtk.Align.CENTER)
            tcol.pack_start(label(f"Dział {unit}: {course.unit_title(level, unit)}", "title2"), False, False, 0)
            bt = db.best_test("unit", key)
            bits = [f"{len(nd)} z {len(lessons)} lekcji" if not all_done else f"{len(lessons)} lekcje"]
            if nd:
                bits.append(f"średnio {round(sum(nd) / len(nd))}%")
            if bt is not None:
                bits.append(f"test działu {bt}%")
            tcol.pack_start(label(" · ".join(bits), "dim"), False, False, 0)
            uh.pack_start(tcol, True, True, 0)
            uh.pack_end(_btn("Pokaż lekcje" if not expanded else "Zwiń", cb=lambda k=key: self._toggle_unit(k)),
                        False, False, 0)
            uh.pack_end(_btn("Test działu" + (f" · {bt}%" if bt is not None else ""),
                             cb=lambda lv=level, u=unit: app.start_unit_test(lv, u)), False, False, 0)
            c.pack_start(uh, False, False, 0)
            if expanded:
                c.pack_start(self._lessons(lessons, done, cur, cur_tab, started), False, False, 0)
            self.inner.pack_start(c, False, False, 0)
        self.show_all()

    def _lessons(self, lessons, done, cur, cur_tab, started):
        app = self.app
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(4)
        for les in lessons:
            d = done.get(les.id)
            if cur is not None and les.id == cur.id:
                cb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                cb.get_style_context().add_class("cur-lesson")
                r = Gtk.Box(spacing=12)
                r.pack_start(dot(str(les.number), "cur"), False, False, 0)
                tc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                tc.pack_start(label(f"<b>{les.number}. {GLib.markup_escape_text(les.title)}</b>", markup=True), False, False, 0)
                step = _TABS.index(cur_tab) if cur_tab in _TABS else 0
                tc.pack_start(label(f"{step} z {len(_TABS)} części" if started else "następna lekcja", "dim"), False, False, 0)
                r.pack_start(tc, True, True, 0)
                r.pack_start(_btn("▶  Kontynuuj" if started else "▶  Zacznij", True,
                                  lambda lid=les.id, t=cur_tab: app.open_lesson(lid, t)), False, False, 0)
                cb.pack_start(r, False, False, 0)
                parts = Gtk.Box(spacing=8)
                parts.set_margin_start(36)
                for i, tk in enumerate(_TABS):
                    st = "done" if started and i < step else ("cur" if i == step else "todo")
                    p = Gtk.Label(label=("✓ " if st == "done" else "▶ " if st == "cur" else "") + _TAB_SHORT[tk])
                    p.get_style_context().add_class("part")
                    if st != "todo":
                        p.get_style_context().add_class("part-" + st)
                    parts.pack_start(p, False, False, 0)
                cb.pack_start(parts, False, False, 0)
                box.pack_start(cb, False, False, 0)
                continue
            ev = Gtk.EventBox()
            ev.set_above_child(False)
            r = Gtk.Box(spacing=12)
            r.set_margin_start(10)
            r.set_margin_end(10)
            r.set_margin_top(5)
            r.set_margin_bottom(5)
            r.pack_start(dot(str(les.number), "done" if d else "todo"), False, False, 0)
            r.pack_start(label(f"{les.number}. {les.title}", None if d else "dim"), True, True, 0)
            if d:
                n = stars_for(d["best"])
                r.pack_start(label("★" * n, "stars", wrap=False), False, False, 0)
                if n < 3:
                    r.pack_start(label("★" * (3 - n), "stars-off", wrap=False), False, False, 0)
                sc = label(f"{d['best']}%", "score", wrap=False)
                sc.set_width_chars(5)
                sc.set_xalign(1.0)
                r.pack_start(sc, False, False, 0)
            ev.add(r)
            ev.set_tooltip_text("Otwórz lekcję")
            ev.connect("button-release-event", lambda _w, _e, lid=les.id: app.open_lesson(lid))
            ev.connect("realize", lambda w: w.get_window().set_cursor(
                Gdk.Cursor.new_from_name(w.get_display(), "pointer")))
            box.pack_start(ev, False, False, 0)
        return box


# ====================================================================== LEKCJA
class LessonView(Gtk.Box):
    def __init__(self, app, lesson):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app, self.lesson = app, lesson
        self.started = time.time()

        head = Gtk.Box(spacing=10)
        for side in ("start", "end", "top"):
            getattr(head, f"set_margin_{side}")(16)
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        back.set_tooltip_text("Wróć do kursu")
        back.connect("clicked", lambda *_: app.show_page("course"))
        head.pack_start(back, False, False, 0)
        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tb.pack_start(label(f"{lesson.level} · Dział {lesson.unit} · Lekcja {lesson.number}", "dim"), False, False, 0)
        tb.pack_start(label(lesson.title, "hero"), False, False, 0)
        head.pack_start(tb, True, True, 0)
        self.pack_start(head, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        sw = Gtk.StackSwitcher()
        sw.set_stack(self.stack)
        sw.set_halign(Gtk.Align.CENTER)
        sw.set_margin_top(10)
        self.pack_start(sw, False, False, 0)
        self.pack_start(self.stack, True, True, 0)

        self.stack.add_titled(self._intro(), "intro", "1. Dialog")
        self.stack.add_titled(self._vocab(), "vocab", "2. Słownictwo")
        self.stack.add_titled(self._grammar(), "grammar", "3. Gramatyka")
        self.ex_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.stack.add_titled(self.ex_box, "ex", "4. Ćwiczenia")
        self.stack.add_titled(self._speaking(), "speak", "5. Mówienie")
        self._start_exercises()
        self.track = False
        self.stack.connect("notify::visible-child-name", self._remember)
        # tryb skupienia: przy ćwiczeniach znika menu boczne
        self.stack.connect("notify::visible-child-name",
                           lambda st, _p: app.set_focus_mode(st.get_visible_child_name() == "ex"))

    TAB_NAMES = {"intro": "1. Dialog", "vocab": "2. Słownictwo", "grammar": "3. Gramatyka",
                 "ex": "4. Ćwiczenia", "speak": "5. Mówienie"}

    def _remember(self, *_):
        if self.track:
            self.app.db.set("last_lesson", {"id": self.lesson.id, "tab": self.stack.get_visible_child_name(),
                                            "ts": time.time()})

    def _next_btn(self, target, text="Dalej  →"):
        b = Gtk.Button(label=text)
        b.get_style_context().add_class("suggested-action")
        b.set_halign(Gtk.Align.END)
        b.connect("clicked", lambda *_: self.stack.set_visible_child_name(target))
        return b

    # -- 1. dialog
    def _intro(self):
        les, app = self.lesson, self.app
        b = page_box()
        c = card()
        c.pack_start(label("W tej lekcji nauczysz się:", "title2"), False, False, 0)
        for g in les.goals:
            c.pack_start(label("•  " + g), False, False, 0)
        b.pack_start(c, False, False, 0)

        dc = card()
        top = Gtk.Box(spacing=8)
        top.pack_start(label("Dialog", "title2"), True, True, 0)
        play_all = Gtk.Button(label="▶  Odtwórz cały dialog")
        play_all.connect("clicked", lambda *_: app.say_sequence([es for _, es, _ in les.dialog]))
        top.pack_start(play_all, False, False, 0)
        self.show_tr = Gtk.CheckButton(label="Pokaż tłumaczenie")
        self.show_tr.set_active(True)
        top.pack_start(self.show_tr, False, False, 0)
        dc.pack_start(top, False, False, 0)
        self.tr_labels = []
        grid = Gtk.Grid(column_spacing=10, row_spacing=6)
        for i, (who, es, pl) in enumerate(les.dialog):
            grid.attach(label(who + ":" if who else "", "dim", wrap=False), 0, i * 2, 1, 1)
            row = Gtk.Box(spacing=4)
            row.pack_start(label(es, "mid-es", selectable=True), True, True, 0)
            row.pack_start(SpeakButton(app, es), False, False, 0)
            row.pack_start(slow_button(app, es), False, False, 0)
            grid.attach(row, 1, i * 2, 1, 1)
            tr = label(pl, "dim")
            grid.attach(tr, 1, i * 2 + 1, 1, 1)
            self.tr_labels.append(tr)
        dc.pack_start(grid, False, False, 0)
        self.show_tr.connect("toggled", lambda w: [t.set_visible(w.get_active()) for t in self.tr_labels])
        b.pack_start(dc, False, False, 0)

        if les.culture:
            cc = card()
            cc.pack_start(label("Ciekawostka", "title2"), False, False, 0)
            cc.pack_start(rich_text(les.culture), False, False, 0)
            b.pack_start(cc, False, False, 0)
        q = urllib.parse.quote(f"aprender español {les.title.split('—')[0].strip()} A1 A2")
        yt = Gtk.LinkButton.new_with_label(f"https://www.youtube.com/results?search_query={q}",
                                           "Szukaj filmów do tego tematu na YouTube")
        yt.set_halign(Gtk.Align.START)
        b.pack_start(yt, False, False, 0)
        b.pack_start(self._next_btn("vocab"), False, False, 0)
        return scrolled(b)

    # -- 2. słownictwo
    def _vocab(self):
        les, app = self.lesson, self.app
        b = page_box()
        top = Gtk.Box(spacing=8)
        top.pack_start(label(f"Nowe słowa ({len(les.vocab)})", "title2"), True, True, 0)
        pa = Gtk.Button(label="▶  Odtwórz wszystkie")
        pa.connect("clicked", lambda *_: app.say_sequence([v["es"] for v in les.vocab]))
        top.pack_start(pa, False, False, 0)
        b.pack_start(top, False, False, 0)
        c = card()
        grid = Gtk.Grid(column_spacing=12, row_spacing=8)
        for i, v in enumerate(les.vocab):
            grid.attach(SpeakButton(app, v["es"]), 0, i, 1, 1)
            es = label(v["es"], "mid-es", wrap=True)
            es.set_width_chars(18)
            grid.attach(es, 1, i, 1, 1)
            txt = v["pl"]
            if v.get("ex_es"):
                txt += f"\n<i>{GLib.markup_escape_text(v['ex_es'])}</i> — {GLib.markup_escape_text(v['ex_pl'])}"
                pl = label(GLib.markup_escape_text(v["pl"]) + txt[len(v["pl"]):], markup=True)
            else:
                pl = label(txt)
            pl.set_hexpand(True)
            grid.attach(pl, 2, i, 1, 1)
            grid.attach(label(POS_NAMES.get(v["pos"], v["pos"]), "dim", wrap=False), 3, i, 1, 1)
        c.pack_start(grid, False, False, 0)
        b.pack_start(c, False, False, 0)
        b.pack_start(label("Po ukończeniu lekcji wszystkie słowa trafią automatycznie do powtórek.", "dim"),
                     False, False, 0)
        b.pack_start(self._next_btn("grammar"), False, False, 0)
        return scrolled(b)

    # -- 3. gramatyka
    def _grammar(self):
        b = page_box()
        c = card()
        c.pack_start(rich_text(self.lesson.grammar), False, False, 0)
        b.pack_start(c, False, False, 0)
        tip = label("Wskazówka: tabele odmiany dowolnego czasownika znajdziesz w zakładce „Odmiana”.", "dim")
        b.pack_start(tip, False, False, 0)
        b.pack_start(self._next_btn("ex", "Do ćwiczeń  →"), False, False, 0)
        return scrolled(b)

    # -- 4. ćwiczenia
    def _start_exercises(self):
        clear(self.ex_box)
        rng = random.Random()
        authored = [dict(e, source=self.lesson.id) for e in self.lesson.exercises]
        auto = [e for e in self.lesson.all_exercises(rng) if e not in self.lesson.exercises]
        auto = [e for e in auto if e not in authored]
        extra = rng.sample(auto, min(len(auto), 8))
        items = authored + extra
        rng.shuffle(items)
        inner = page_box()
        inner.set_halign(Gtk.Align.CENTER)       # tryb skupienia: zadanie na środku, wygodna szerokość
        inner.set_size_request(880, -1)
        inner.pack_start(label(f"Ćwiczenia ({len(items)})", "title2"), False, False, 0)
        inner.pack_start(ExerciseRunner(self.app, items, self._finished, source=self.lesson.id), False, False, 0)
        self.ex_box.pack_start(scrolled(inner), True, True, 0)
        self.ex_box.show_all()

    def _finished(self, score, total, mistakes):
        pct = round(100 * score / max(1, total))
        self.app.db.finish_lesson(self.lesson, pct)
        self.app.db.log_activity(seconds=int(time.time() - self.started))
        self.started = time.time()
        clear(self.ex_box)
        b = page_box()
        c = card()
        c.pack_start(label(f"Wynik: {score} / {total}  ({pct}%)", "hero"), False, False, 0)
        msg = ("¡Fantástico! Świetna robota." if pct >= 90 else "¡Muy bien! Lekcja zaliczona." if pct >= 70
               else "Lekcja zapisana — warto ją powtórzyć, żeby utrwalić materiał.")
        c.pack_start(label(msg), False, False, 0)
        c.pack_start(label(f"{len(self.lesson.vocab)} słów dodano do powtórek.", "dim"), False, False, 0)
        if mistakes:
            c.pack_start(label("Do poprawy:", "title2"), False, False, 0)
            for m in mistakes[:12]:
                c.pack_start(label(f"•  {m['q']}  →  {m['expected']}"), False, False, 0)
        b.pack_start(c, False, False, 0)
        row = Gtk.Box(spacing=8)
        again = Gtk.Button(label="Powtórz ćwiczenia")
        again.connect("clicked", lambda *_: self._start_exercises())
        sp = Gtk.Button(label="Ćwicz mówienie  →")
        sp.get_style_context().add_class("suggested-action")
        sp.connect("clicked", lambda *_: self.stack.set_visible_child_name("speak"))
        row.pack_end(sp, False, False, 0)
        row.pack_end(again, False, False, 0)
        b.pack_start(row, False, False, 0)
        self.ex_box.pack_start(scrolled(b), True, True, 0)
        self.ex_box.show_all()
        self.app.refresh_all()

    # -- 5. mówienie
    def _speaking(self):
        les, app = self.lesson, self.app
        b = page_box()
        b.pack_start(label("Mówienie", "title2"), False, False, 0)
        b.pack_start(label("Posłuchaj zdania, nagraj się i porównaj. Najlepiej w słuchawkach z mikrofonem, "
                           "w cichym miejscu.", "dim"), False, False, 0)
        self.sp_items = [(es, pl) for _, es, pl in les.dialog if es]
        self.sp_idx = 0
        self.sp_holder = card()
        b.pack_start(self.sp_holder, False, False, 0)
        nav = Gtk.Box(spacing=8)
        self.sp_count = label("", "dim", wrap=False)
        prev = Gtk.Button(label="←  Poprzednie")
        prev.connect("clicked", lambda *_: self._sp_go(-1))
        nxt = Gtk.Button(label="Następne  →")
        nxt.connect("clicked", lambda *_: self._sp_go(1))
        self.sp_prev, self.sp_next, self.sp_nav = prev, nxt, nav
        nav.pack_start(self.sp_count, False, False, 0)
        nav.pack_end(nxt, False, False, 0)
        nav.pack_end(prev, False, False, 0)
        b.pack_start(nav, False, False, 0)
        self._sp_go(0)
        return scrolled(b)

    def _sp_finish(self):
        """Koniec części „Mówienie” — podsumowanie zamiast pętli."""
        app, les = self.app, self.lesson
        app.stop_audio()
        clear(self.sp_holder)
        self.sp_nav.hide()
        done = app.db.done_lessons()
        h = self.sp_holder
        row = Gtk.Box(spacing=8)
        if les.id in done:
            h.pack_start(label("✔ Lekcja ukończona — ¡enhorabuena!", "hero"), False, False, 0)
            h.pack_start(label(f"Wynik ćwiczeń: {done[les.id]['best']}%. Słówka z tej lekcji są już w powtórkach.",
                               "dim"), False, False, 0)
            nxt = app.course.next_lesson(set(done))
            if nxt:
                nb = Gtk.Button(label=f"Następna lekcja: {nxt.number}. {nxt.title}  →")
                nb.get_style_context().add_class("suggested-action")
                nb.connect("clicked", lambda *_: app.open_lesson(nxt.id))
                row.pack_end(nb, False, False, 0)
        else:
            h.pack_start(label("Mówienie zakończone", "hero"), False, False, 0)
            h.pack_start(label("Lekcja zostanie zaliczona po zrobieniu ćwiczeń (krok 4) — wtedy słówka trafią "
                               "do powtórek."), False, False, 0)
            eb = Gtk.Button(label="Przejdź do ćwiczeń  →")
            eb.get_style_context().add_class("suggested-action")
            eb.connect("clicked", lambda *_: self.stack.set_visible_child_name("ex"))
            row.pack_end(eb, False, False, 0)
        cb = Gtk.Button(label="Wróć do kursu")
        cb.connect("clicked", lambda *_: app.show_page("course"))
        row.pack_end(cb, False, False, 0)
        again = Gtk.Button(label="Ćwicz mówienie jeszcze raz")
        again.connect("clicked", lambda *_: (setattr(self, "sp_idx", 0), self.sp_nav.show(), self._sp_go(0)))
        row.pack_start(again, False, False, 0)
        h.pack_start(row, False, False, 0)
        h.show_all()
        self.sp_count.set_text("")

    def _sp_go(self, d):
        if self.sp_idx + d >= len(self.sp_items):
            self._sp_finish()
            return
        self.sp_idx = max(0, self.sp_idx + d)
        self.sp_prev.set_sensitive(self.sp_idx > 0)
        last = self.sp_idx == len(self.sp_items) - 1
        self.sp_next.set_label("Zakończ  ✔" if last else "Następne  →")
        ctx = self.sp_next.get_style_context()
        (ctx.add_class if last else ctx.remove_class)("suggested-action")
        clear(self.sp_holder)
        es, pl = self.sp_items[self.sp_idx]
        self.sp_holder.pack_start(SpeakPractice(self.app, es, pl), False, False, 0)
        self.sp_holder.show_all()
        self.sp_count.set_text(f"Zdanie {self.sp_idx + 1} z {len(self.sp_items)}")
