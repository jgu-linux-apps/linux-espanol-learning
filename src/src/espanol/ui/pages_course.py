"""Ekrany: Dzisiaj, Kurs, Lekcja."""
import random
import time
import urllib.parse

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import (label, rich_text, scrolled, page_box, card, SpeakButton, slow_button, clear)
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
class TodayPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.refresh()

    _progress_table = _today_progress_table

    def refresh(self):
        app, db, course = self.app, self.app.db, self.app.course
        clear(self.inner)
        b = self.inner
        done = db.done_lessons()
        due0, _new0 = db.count_due()
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hero.get_style_context().add_class("hero-banner")
        bd = label("DZISIAJ", "badge", wrap=False)
        bd.set_halign(Gtk.Align.START)
        hero.pack_start(bd, False, False, 0)
        hero.pack_start(label(_greeting() + " 👋", "hero"), False, False, 0)
        hero.pack_start(label(f"Ukończone lekcje: {len(done)} z {len(course.lessons)}  ·  "
                              f"słówek do powtórzenia dziś: {due0}"), False, False, 0)
        b.pack_start(hero, False, False, 0)

        if not done and not db.get("placement_offered"):
            pc = card(spacing=4)
            pr = Gtk.Box(spacing=12)
            pr.pack_start(label("Znasz już trochę hiszpańskiego? Zrób krótki test poziomujący, a podpowiem, "
                                "od której lekcji zacząć.", None), True, True, 0)
            pb = Gtk.Button(label="Zrób test")
            pb.get_style_context().add_class("suggested-action")
            pb.set_valign(Gtk.Align.CENTER)
            pb.connect("clicked", lambda *_: app.open_placement())
            nb = Gtk.Button(label="Zaczynam od zera")
            nb.set_valign(Gtk.Align.CENTER)
            nb.connect("clicked", lambda *_: (db.set("placement_offered", True), self.refresh()))
            pr.pack_start(pb, False, False, 0)
            pr.pack_start(nb, False, False, 0)
            pc.pack_start(pr, False, False, 0)
            b.pack_start(pc, False, False, 0)

        # seria + cel dzienny
        cur, best = db.streak()
        goal = int(db.get("daily_goal", 10))
        got = db.today_seconds() / 60.0
        gc = card(spacing=6)
        grow = Gtk.Box(spacing=16)
        fire = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        fire.pack_start(label(("🔥 " if cur else "") + str(cur), "stat-num", wrap=False), False, False, 0)
        fire.pack_start(label("dni z rzędu" if cur != 1 else "dzień z rzędu", "dim", wrap=False), False, False, 0)
        grow.pack_start(fire, False, False, 0)
        gcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        done_goal = got >= goal
        gcol.pack_start(label(f"Cel dzienny: {min(int(got), goal)} / {goal} min" + ("  ✔ zrobione!" if done_goal else ""),
                              "title2", wrap=False), False, False, 0)
        gcol.pack_start(_bar(got / max(1, goal), 320), False, False, 0)
        msg = ("Świetnie — dzisiejszy cel zaliczony." if done_goal else
               ("Zrób dziś choć chwilę nauki, żeby nie stracić serii." if cur and db.today_seconds() < 60
                else "Jeszcze trochę — każda minuta się liczy."))
        gcol.pack_start(label(msg + (f"  Rekord: {best} dni." if best > 1 else ""), "dim"), False, False, 0)
        grow.pack_start(gcol, True, True, 0)
        gc.pack_start(grow, False, False, 0)
        b.pack_start(gc, False, False, 0)

        if not app.speech.tts_available() or not app.speech.stt_available():
            c = card()
            c.pack_start(label("Dokończ instalację silnika mowy", "title2"), False, False, 0)
            c.pack_start(label("Nagrania wymowy i ocena Twojej wymowy działają po pobraniu głosów i modelu "
                               "rozpoznawania mowy (jednorazowo, ok. 0,3–0,7 GB). Wszystko działa potem offline."),
                         False, False, 0)
            btn = Gtk.Button(label="Zainstaluj teraz")
            btn.get_style_context().add_class("suggested-action")
            btn.set_halign(Gtk.Align.START)
            btn.connect("clicked", lambda *_: app.open_setup())
            c.pack_start(btn, False, False, 0)
            b.pack_start(c, False, False, 0)

        # kontynuuj
        last = db.get("last_lesson")
        if last and last.get("id") in course.by_id:
            les = course.by_id[last["id"]]
            tab = last.get("tab") or "intro"
            cc = card(spacing=6)
            row = Gtk.Box(spacing=12)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            col.pack_start(label("Kontynuuj, gdzie skończyłeś", "dim"), False, False, 0)
            col.pack_start(label(f"{les.level} · Lekcja {les.number}: {les.title}", "title2"), False, False, 0)
            state = "ukończona — możesz powtórzyć" if les.id in done else "w trakcie"
            col.pack_start(label(f"Krok: {LessonView.TAB_NAMES.get(tab, tab)}  ·  {state}", "dim"), False, False, 0)
            row.pack_start(col, True, True, 0)
            kb = Gtk.Button(label="▶  Kontynuuj")
            kb.get_style_context().add_class("suggested-action")
            kb.set_valign(Gtk.Align.CENTER)
            kb.connect("clicked", lambda *_: app.open_lesson(les.id, tab))
            row.pack_start(kb, False, False, 0)
            cc.pack_start(row, False, False, 0)
            b.pack_start(cc, False, False, 0)

        grid = Gtk.Grid(column_spacing=14, row_spacing=14, column_homogeneous=True)
        # następna lekcja
        nxt = course.next_lesson(set(done))
        c1 = card()
        c1.pack_start(label("Następna lekcja", "dim"), False, False, 0)
        if nxt:
            c1.pack_start(label(f"{nxt.level} · Lekcja {nxt.number}", "badge", wrap=False), False, False, 0)
            c1.pack_start(label(nxt.title, "title2"), False, False, 0)
            c1.pack_start(label(" · ".join(nxt.goals[:2]), "dim"), False, False, 0)
            bt = Gtk.Button(label="Zaczynamy  →")
            bt.get_style_context().add_class("suggested-action")
            bt.set_halign(Gtk.Align.START)
            bt.connect("clicked", lambda *_: app.open_lesson(nxt.id))
            c1.pack_end(bt, False, False, 0)
        else:
            c1.pack_start(label("¡Enhorabuena! Ukończyłeś cały kurs A1–A2. 🎉", "title2"), False, False, 0)
            c1.pack_start(label("Powtarzaj słówka, rób egzaminy próbne i czytaj czytanki.", "dim"), False, False, 0)
        grid.attach(c1, 0, 0, 1, 1)

        # powtórki
        due, new = db.count_due()
        c2 = card()
        c2.pack_start(label("Powtórki słówek", "dim"), False, False, 0)
        c2.pack_start(label(f"{due}", "stat-num", wrap=False), False, False, 0)
        c2.pack_start(label(f"do powtórzenia dziś · {min(new, db.get('new_per_day', 20))} nowych czeka", "dim"),
                      False, False, 0)
        bt2 = Gtk.Button(label="Powtarzaj")
        bt2.set_halign(Gtk.Align.START)
        bt2.set_sensitive(due + new > 0)
        bt2.connect("clicked", lambda *_: app.show_page("review"))
        c2.pack_end(bt2, False, False, 0)
        grid.attach(c2, 1, 0, 1, 1)
        b.pack_start(grid, False, False, 0)

        # postęp kursu
        b.pack_start(self._progress_table(done), False, False, 0)

        # słowo dnia
        words = [w for w in course.dictionary if w.get("ex_es")]
        if words:
            rnd = random.Random(time.strftime("%Y%m%d"))
            w = rnd.choice(words)
            c3 = card()
            c3.pack_start(label("Palabra del día — słowo dnia", "dim"), False, False, 0)
            row = Gtk.Box(spacing=6)
            row.pack_start(label(w["es"], "big-es", wrap=False), False, False, 0)
            row.pack_start(SpeakButton(app, w["es"]), False, False, 0)
            c3.pack_start(row, False, False, 0)
            c3.pack_start(label(w["pl"]), False, False, 0)
            row2 = Gtk.Box(spacing=6)
            row2.pack_start(label(f"{w['ex_es']} — {w['ex_pl']}", "dim"), True, True, 0)
            row2.pack_start(SpeakButton(app, w["ex_es"]), False, False, 0)
            c3.pack_start(row2, False, False, 0)
            b.pack_start(c3, False, False, 0)

        # aktywność
        act = db.activity(7)
        mins = sum(a["seconds"] for a in act) // 60
        st = db.card_stats()
        c4 = card()
        c4.pack_start(label("Ostatnie 7 dni", "dim"), False, False, 0)
        c4.pack_start(label(f"{mins} min nauki · {len(act)} dni aktywnych · "
                            f"{st['opanowane']} słów opanowanych · {st['total']} w powtórkach"), False, False, 0)
        b.pack_start(c4, False, False, 0)
        self.show_all()


# ====================================================================== KURS
class CoursePage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.refresh()

    def refresh(self):
        app = self.app
        clear(self.inner)
        done = app.db.done_lessons()
        self.inner.pack_start(label("Kurs hiszpańskiego — Hiszpania (castellano)", "hero"), False, False, 0)
        self.inner.pack_start(label("Poziomy według Europejskiego Systemu Opisu Kształcenia Językowego (CEFR). "
                                    "Lekcje możesz robić w dowolnej kolejności, ale najlepiej po kolei.", "dim"),
                              False, False, 0)
        for level, desc in (("A1", "Poziom początkujący — przetrwanie w codziennych sytuacjach"),
                            ("A2", "Poziom podstawowy — przeszłość, przyszłość, opowiadanie, opinie")):
            units = app.course.units(level)
            n_done = sum(1 for u in units.values() for l in u if l.id in done)
            n_all = sum(len(u) for u in units.values())
            head = Gtk.Box(spacing=10)
            head.set_margin_top(10)
            head.pack_start(label(f"Poziom {level}", "title2", wrap=False), False, False, 0)
            head.pack_start(label(f"{n_done}/{n_all}", "badge", wrap=False), False, False, 0)
            exam = Gtk.Button(label=f"Egzamin próbny {level}")
            exam.connect("clicked", lambda _b, lv=level: app.start_exam(lv))
            head.pack_end(exam, False, False, 0)
            self.inner.pack_start(head, False, False, 0)
            self.inner.pack_start(label(desc, "dim"), False, False, 0)
            for unit, lessons in sorted(units.items()):
                c = card(spacing=4)
                uh = Gtk.Box(spacing=8)
                uh.pack_start(label(f"Dział {unit}: {app.course.unit_title(level, unit)}", "title2"), True, True, 0)
                best = app.db.best_test("unit", f"{level}-{unit}")
                tb = Gtk.Button(label="Test działu" + (f" ({best}%)" if best is not None else ""))
                tb.connect("clicked", lambda _b, lv=level, u=unit: app.start_unit_test(lv, u))
                uh.pack_end(tb, False, False, 0)
                c.pack_start(uh, False, False, 0)
                lb = Gtk.ListBox()
                lb.set_selection_mode(Gtk.SelectionMode.NONE)
                for les in lessons:
                    row = Gtk.ListBoxRow()
                    hb = Gtk.Box(spacing=10)
                    hb.set_margin_top(6)
                    hb.set_margin_bottom(6)
                    d = done.get(les.id)
                    mark = label("✔" if d else "○", "lesson-done" if d else "dim", wrap=False)
                    hb.pack_start(mark, False, False, 0)
                    hb.pack_start(label(f"{les.number}. {les.title}", wrap=True), True, True, 0)
                    if d:
                        hb.pack_start(label(f"{d['best']}%", "dim", wrap=False), False, False, 0)
                    row.add(hb)
                    row.lesson_id = les.id
                    lb.add(row)
                lb.connect("row-activated", lambda _l, r: app.open_lesson(r.lesson_id))
                c.pack_start(lb, False, False, 0)
                self.inner.pack_start(c, False, False, 0)
        self.show_all()


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
