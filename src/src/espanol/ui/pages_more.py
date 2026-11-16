"""Ekrany: Czytanki, Filmy, Testy, Statystyki, Ustawienia + kreator instalacji."""
import random
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import (label, rich_text, scrolled, page_box, card, SpeakButton, slow_button, clear)
from .exercise import ExerciseRunner
from .pron import SpeakPractice
from .. import speech
from ..i18n import _  # noqa: E402


# ====================================================================== CZYTANKI
class ReadingsPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.show_list()

    def show_list(self):
        clear(self.inner)
        self.inner.pack_start(label(_("Czytanki"), "hero"), False, False, 0)
        self.inner.pack_start(label(_("Krótkie teksty do każdego działu kursu — z nagraniem, tłumaczeniem, słowniczkiem "
                                    "i pytaniami sprawdzającymi zrozumienie."), "dim"), False, False, 0)
        for r in self.app.course.readings:
            m = r["meta"]
            c = card(spacing=4)
            h = Gtk.Box(spacing=8)
            h.pack_start(label(_('{} · Dział {}').format(m.get('level'), m.get('unit')), "badge", wrap=False), False, False, 0)
            h.pack_start(label(m.get("title", ""), "title2"), True, True, 0)
            best = self.app.db.best_test("reading", m.get("id"))
            if best is not None:
                h.pack_start(label(f"{best}%", "dim", wrap=False), False, False, 0)
            bt = Gtk.Button(label=_("Czytaj"))
            bt.connect("clicked", lambda _b, rr=r: self.open(rr))
            h.pack_end(bt, False, False, 0)
            c.pack_start(h, False, False, 0)
            c.pack_start(label(r["text"][:140] + "…", "dim"), False, False, 0)
            self.inner.pack_start(c, False, False, 0)
        self.inner.show_all()

    def open(self, r):
        app = self.app
        clear(self.inner)
        b = self.inner
        h = Gtk.Box(spacing=8)
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        back.connect("clicked", lambda *_a: self.show_list())
        h.pack_start(back, False, False, 0)
        h.pack_start(label(r["meta"].get("title", ""), "hero"), True, True, 0)
        b.pack_start(h, False, False, 0)
        ctl = Gtk.Box(spacing=8)
        paras = [p for p in r["text"].split("\n") if p.strip()]
        pa = Gtk.Button(label=_("▶  Przeczytaj na głos"))
        pa.connect("clicked", lambda *_a: app.say_sequence(paras))
        ctl.pack_start(pa, False, False, 0)
        stop = Gtk.Button(label="■  Stop")
        stop.connect("clicked", lambda *_a: app.stop_audio())
        ctl.pack_start(stop, False, False, 0)
        tr = Gtk.CheckButton(label=_("Pokaż tłumaczenie"))
        ctl.pack_start(tr, False, False, 0)
        b.pack_start(ctl, False, False, 0)
        c = card()
        tparas = [p for p in r["translation"].split("\n") if p.strip()]
        trl = []
        for i, p in enumerate(paras):
            row = Gtk.Box(spacing=4)
            row.pack_start(label(p, "mid-es", selectable=True), True, True, 0)
            row.pack_start(SpeakButton(app, p), False, False, 0)
            row.pack_start(slow_button(app, p), False, False, 0)
            c.pack_start(row, False, False, 0)
            if i < len(tparas):
                t = label(tparas[i], "dim")
                t.set_no_show_all(True)
                trl.append(t)
                c.pack_start(t, False, False, 0)
        tr.connect("toggled", lambda w: [t.set_visible(w.get_active()) for t in trl])
        b.pack_start(c, False, False, 0)
        if r["glossary"]:
            g = card(spacing=3)
            g.pack_start(label(_("Słowniczek"), "title2"), False, False, 0)
            for es, pl in r["glossary"]:
                row = Gtk.Box(spacing=6)
                row.pack_start(SpeakButton(app, es.split("/")[0]), False, False, 0)
                row.pack_start(label(f"<b>{GLib.markup_escape_text(es)}</b> — {GLib.markup_escape_text(pl)}",
                                     markup=True), True, True, 0)
                g.pack_start(row, False, False, 0)
            b.pack_start(g, False, False, 0)
        b.pack_start(label(_("Sprawdź, czy zrozumiałeś"), "title2"), False, False, 0)
        holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        b.pack_start(holder, False, False, 0)

        def finished(score, total, _m):
            app.db.save_test("reading", r["meta"].get("id"), score, total)
            clear(holder)
            holder.pack_start(label(_('Wynik: {}/{}').format(score, total), "title2"), False, False, 0)
            holder.show_all()
        qs = [dict(q, source="reading") for q in r["questions"]]
        holder.pack_start(ExerciseRunner(app, qs, finished, show_progress=False), False, False, 0)
        b.show_all()


# ====================================================================== FILMY
class VideosPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        b = page_box()
        b.pack_start(label(_("Filmy i słuchanie"), "hero"), False, False, 0)
        b.pack_start(label(_("Sprawdzone kanały i źródła z hiszpańskim. Linki otwierają się w przeglądarce — aplikacja "
                           "niczego nie pobiera. Najwięcej daje codzienne słuchanie materiałów, które rozumiesz "
                           "w ok. 70–90%."), "dim"), False, False, 0)
        group = None
        c = None
        for v in app.course.videos:
            if v["group"] != group:
                group = v["group"]
                b.pack_start(label(group, "title2"), False, False, 0)
                c = card(spacing=10)
                b.pack_start(c, False, False, 0)
            row = Gtk.Box(spacing=10)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            col.pack_start(label(f"<b>{GLib.markup_escape_text(v['title'])}</b>", markup=True), False, False, 0)
            col.pack_start(label(v["desc"], "dim"), False, False, 0)
            row.pack_start(col, True, True, 0)
            lb = Gtk.LinkButton.new_with_label(v["url"], _("Otwórz"))
            lb.set_valign(Gtk.Align.CENTER)
            row.pack_start(lb, False, False, 0)
            c.pack_start(row, False, False, 0)
        b.pack_start(label(_("Wskazówka: w każdej lekcji (zakładka „Dialog”) jest też link do wyszukiwania filmów na "
                           "temat tej lekcji."), "dim"), False, False, 0)
        self.pack_start(scrolled(b), True, True, 0)


# ====================================================================== TESTY
def build_unit_test(course, level, unit, n=15, rng=None):
    rng = rng or random.Random()
    pool = []
    for l in course.units(level).get(unit, []):
        pool += l.all_exercises(rng)
    authored = [e for e in pool if e["type"] in ("fill", "conj") or (e["type"] == "choice" and not e.get("audio"))]
    other = [e for e in pool if e not in authored]
    k1 = min(len(authored), n * 2 // 3)
    items = rng.sample(authored, k1) + rng.sample(other, min(len(other), n - k1))
    rng.shuffle(items)
    return items


def build_exam(course, level, rng=None):
    rng = rng or random.Random()
    lessons = [l for l in course.lessons if l.level == level]
    pool = []
    for l in lessons:
        pool += l.all_exercises(rng)
    vocab = [e for e in pool if e["type"] == "choice" and e.get("audio")]
    gram = [e for e in pool if e["type"] in ("fill", "conj") or (e["type"] == "choice" and not e.get("audio"))]
    trans = [e for e in pool if e["type"] in ("trans", "order") and _("Przetłumacz na hiszpański:") not in e["q"]]
    listen = [e for e in pool if e["type"] == "listen"]
    items = (rng.sample(vocab, min(8, len(vocab))) + rng.sample(gram, min(14, len(gram))) +
             rng.sample(trans, min(6, len(trans))) + rng.sample(listen, min(6, len(listen))))
    rng.shuffle(items)
    readings = [r for r in course.readings if r["meta"].get("level") == level]
    for r in rng.sample(readings, min(2, len(readings))):
        for q in r["questions"]:
            items.append(dict(q, context=r["text"], source="exam"))
    return items


class TestView(Gtk.Box):
    """Test działu / egzamin. Egzamin ma na końcu część „Mówienie”, jeśli jest model mowy."""

    def __init__(self, app, kind, ref, title, items, speaking=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app, self.kind, self.ref, self.title = app, kind, ref, title
        self.speaking = speaking or []
        self.started = time.time()
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        h = Gtk.Box(spacing=8)
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        back.connect("clicked", lambda *_a: app.show_page("tests"))
        h.pack_start(back, False, False, 0)
        h.pack_start(label(title, "hero"), True, True, 0)
        self.inner.pack_start(h, False, False, 0)
        self.inner.pack_start(label(_("Bez podpowiedzi i bez cofania. Powodzenia — ¡suerte!"), "dim"), False, False, 0)
        self.context = label("", "mid-es")
        self.ctx_card = card(self.context)
        self.ctx_card.set_no_show_all(True)
        self.inner.pack_start(self.ctx_card, False, False, 0)
        self.runner = ExerciseRunner(app, items, self._done, source=kind)
        self.inner.pack_start(self.runner, False, False, 0)
        self._hook_context()

    def _hook_context(self):
        orig = self.runner._show

        def show():
            i = self.runner.idx
            ctx = self.runner.items[i].get("context") if i < len(self.runner.items) else None
            if ctx:
                self.context.set_text(ctx)
                self.context.show()
                self.ctx_card.show()
            else:
                self.ctx_card.hide()
            orig()
        self.runner._show = show
        show()

    def _done(self, score, total, mistakes):
        self.score, self.total, self.mistakes = score, total, mistakes
        self.ctx_card.hide()
        if self.speaking and self.app.speech.stt_available():
            self._speak_part()
        else:
            self._summary(None)

    def _speak_part(self):
        clear(self.inner)
        self.inner.pack_start(label(_("Część ustna — mówienie"), "hero"), False, False, 0)
        self.inner.pack_start(label(_("Przeczytaj na głos 3 zdania. Liczy się zrozumiałość wymowy."), "dim"),
                              False, False, 0)
        self.sp_scores = []
        self.sp_i = 0
        self.sp_holder = card()
        self.inner.pack_start(self.sp_holder, False, False, 0)
        self.sp_next = Gtk.Button(label=_("Dalej  →"))
        self.sp_next.set_halign(Gtk.Align.END)
        self.sp_next.set_sensitive(False)
        self.sp_next.connect("clicked", lambda *_a: self._sp_advance())
        self.inner.pack_start(self.sp_next, False, False, 0)
        skip = Gtk.Button(label=_("Pomiń część ustną"))
        skip.set_halign(Gtk.Align.START)
        skip.connect("clicked", lambda *_a: self._summary(None))
        self.inner.pack_start(skip, False, False, 0)
        self._sp_show()

    def _sp_show(self):
        clear(self.sp_holder)
        es = self.speaking[self.sp_i]

        def scored(s):
            if len(self.sp_scores) <= self.sp_i:
                self.sp_scores.append(s)
            else:
                self.sp_scores[self.sp_i] = max(s, self.sp_scores[self.sp_i])
            self.sp_next.set_sensitive(True)
        self.sp_holder.pack_start(label(_('Zdanie {} z {}').format(self.sp_i + 1, len(self.speaking)), "dim"), False, False, 0)
        self.sp_holder.pack_start(SpeakPractice(self.app, es, on_scored=scored), False, False, 0)
        self.sp_next.set_sensitive(False)
        self.inner.show_all()

    def _sp_advance(self):
        self.sp_i += 1
        if self.sp_i >= len(self.speaking):
            self._summary(round(sum(self.sp_scores) / max(1, len(self.sp_scores))))
        else:
            self._sp_show()

    def _summary(self, speak_pct):
        pct = round(100 * self.score / max(1, self.total))
        self.app.db.save_test(self.kind, self.ref, self.score, self.total,
                              {"speaking": speak_pct, "mistakes": self.mistakes[:30]})
        self.app.db.log_activity(seconds=int(time.time() - self.started))
        clear(self.inner)
        c = card()
        c.pack_start(label(self.title, "dim"), False, False, 0)
        c.pack_start(label(_('Wynik: {} / {}  ({}%)').format(self.score, self.total, pct), "hero"), False, False, 0)
        if speak_pct is not None:
            c.pack_start(label(_('Część ustna: {}%').format(speak_pct), "title2"), False, False, 0)
        passed = pct >= 60
        c.pack_start(label((_("✔ Zaliczone — próg to 60%. ") if passed else _("✘ Jeszcze nie — próg to 60%. ")) +
                           (_("Świetnie!") if pct >= 85 else _("Powtórz lekcje, w których były błędy.") if not passed
                            else _("Dobrze, utrwal słabsze miejsca.")),
                           "ok-text" if passed else "bad-text"), False, False, 0)
        if self.mistakes:
            c.pack_start(label(_("Błędy:"), "title2"), False, False, 0)
            for m in self.mistakes[:20]:
                c.pack_start(label(f"•  {m['q']}  →  {m['expected']}"), False, False, 0)
        self.inner.pack_start(c, False, False, 0)
        bt = Gtk.Button(label=_("Wróć do testów"))
        bt.set_halign(Gtk.Align.END)
        bt.connect("clicked", lambda *_a: self.app.show_page("tests"))
        self.inner.pack_start(bt, False, False, 0)
        self.inner.show_all()
        self.app.refresh_all()


class TestsPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.refresh()

    def refresh(self):
        app = self.app
        clear(self.inner)
        b = self.inner
        b.pack_start(label(_("Testy i egzaminy"), "hero"), False, False, 0)
        b.pack_start(label(_("Test działu: 15 pytań z 4 lekcji. Egzamin próbny: ok. 40 pytań — słownictwo, gramatyka, "
                           "tłumaczenie, słuchanie, czytanie i część ustna. Próg zaliczenia: 60%."), "dim"),
                     False, False, 0)
        pc = card(spacing=4)
        pr = Gtk.Box(spacing=8)
        pcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pcol.pack_start(label(_("Test poziomujący"), "title2"), False, False, 0)
        pcol.pack_start(label(_("Znasz już trochę hiszpańskiego? Krótki test (ok. 20 pytań) podpowie, od której lekcji zacząć."), "dim"),
                        False, False, 0)
        pr.pack_start(pcol, True, True, 0)
        pb = Gtk.Button(label=_("Zrób test poziomujący"))
        pb.set_valign(Gtk.Align.CENTER)
        pb.connect("clicked", lambda *_a: app.open_placement())
        pr.pack_start(pb, False, False, 0)
        pc.pack_start(pr, False, False, 0)
        b.pack_start(pc, False, False, 0)
        for level in ("A1", "A2"):
            c = card(spacing=6)
            h = Gtk.Box(spacing=8)
            h.pack_start(label(_('Poziom {}').format(level), "title2"), True, True, 0)
            best = app.db.best_test("exam", level)
            ex = Gtk.Button(label=_('Egzamin próbny {}').format(level) + (f" — najlepszy: {best}%" if best is not None else ""))
            ex.get_style_context().add_class("suggested-action")
            ex.connect("clicked", lambda _b, lv=level: app.start_exam(lv))
            h.pack_end(ex, False, False, 0)
            c.pack_start(h, False, False, 0)
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_max_children_per_line(5)
            for unit in sorted(app.course.units(level)):
                bu = app.db.best_test("unit", f"{level}-{unit}")
                bt = Gtk.Button(label=_('Dział {}').format(unit) + (f"\n{bu}%" if bu is not None else "\n—"))
                bt.get_child().set_justify(Gtk.Justification.CENTER)
                bt.set_tooltip_text(app.course.unit_title(level, unit))
                bt.connect("clicked", lambda _b, lv=level, u=unit: app.start_unit_test(lv, u))
                flow.add(bt)
            c.pack_start(flow, False, False, 0)
            b.pack_start(c, False, False, 0)
        hist = app.db.tests()
        if hist:
            b.pack_start(label(_("Historia"), "title2"), False, False, 0)
            c = card(spacing=3)
            names = {"unit": _("Test działu"), "exam": _("Egzamin"), "reading": _("Czytanka")}
            for t in hist[:25]:
                when = time.strftime("%d.%m.%Y %H:%M", time.localtime(t["ts"]))
                pct = round(100 * t["score"] / max(1, t["total"]))
                c.pack_start(label(f"{when}   {names.get(t['kind'], t['kind'])} {t['ref']}   "
                                   f"{t['score']}/{t['total']} ({pct}%)"), False, False, 0)
            b.pack_start(c, False, False, 0)
        b.show_all()


# ====================================================================== STATYSTYKI
class StatsPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)

    def refresh(self):
        db, course = self.app.db, self.app.course
        clear(self.inner)
        b = self.inner
        b.pack_start(label(_("Statystyki"), "hero"), False, False, 0)
        done = db.done_lessons()
        st = db.card_stats()
        n, avg, recent = db.pron_stats()
        act = db.activity(30)
        grid = Gtk.Grid(column_spacing=14, row_spacing=14, column_homogeneous=True)
        tiles = [
            (_("Lekcje"), f"{len(done)}/{len(course.lessons)}"),
            (_("Słowa w powtórkach"), str(st["total"])),
            (_("Słowa opanowane"), str(st["opanowane"])),
            (_("Minuty nauki (30 dni)"), str(sum(a["seconds"] for a in act) // 60)),
            (_("Próby wymowy"), str(n)),
            (_("Śr. wymowa (ost. 30)"), f"{round(recent)}%" if recent is not None else "—"),
        ]
        for i, (t, v) in enumerate(tiles):
            c = card(spacing=2)
            c.pack_start(label(v, "stat-num", wrap=False), False, False, 0)
            c.pack_start(label(t, "dim"), False, False, 0)
            grid.attach(c, i % 3, i // 3, 1, 1)
        b.pack_start(grid, False, False, 0)

        b.pack_start(label(_("Aktywność — ostatnie 30 dni (minuty)"), "title2"), False, False, 0)
        data = {a["day"]: a["seconds"] / 60 for a in act}
        days = [time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400 * i)) for i in range(29, -1, -1)]
        vals = [data.get(d, 0) for d in days]
        da = Gtk.DrawingArea()
        da.set_size_request(-1, 150)

        def draw(w, cr):
            W, H = w.get_allocated_width(), w.get_allocated_height()
            mx = max(vals + [10])
            bw = W / len(vals)
            ctx = w.get_style_context()
            col = ctx.get_color(Gtk.StateFlags.NORMAL)
            cr.set_source_rgba(col.red, col.green, col.blue, 0.15)
            cr.rectangle(0, H - 18.5, W, 1)
            cr.fill()
            for i, v in enumerate(vals):
                h = (H - 24) * v / mx
                cr.set_source_rgba(0.85, 0.2, 0.25, 0.85)
                cr.rectangle(i * bw + 2, H - 19 - h, bw - 4, h)
                cr.fill()
            cr.set_source_rgba(col.red, col.green, col.blue, 0.6)
            cr.set_font_size(10)
            for i in (0, 10, 20, 29):
                cr.move_to(i * bw + 2, H - 4)
                cr.show_text(days[i][5:])
            cr.move_to(4, 12)
            cr.show_text(_('maks. {} min').format(round(mx)))
        da.connect("draw", draw)
        b.pack_start(card(da), False, False, 0)

        # wymowa w czasie
        pd = db.pron_daily(30)
        b.pack_start(label(_("Wymowa — średni wynik dnia (ostatnie 30 dni)"), "title2"), False, False, 0)
        if not pd:
            b.pack_start(card(label(_("Brak prób. Poćwicz w Laboratorium wymowy lub w Scenkach z Paco — "
                                    "wykres pojawi się po pierwszych ocenach."), "dim")), False, False, 0)
        else:
            import datetime
            t0 = datetime.date.today() - datetime.timedelta(days=29)
            byday = {d: (a, n) for d, a, n in pd}
            series = []
            for k in range(30):
                d = (t0 + datetime.timedelta(days=k)).strftime("%Y-%m-%d")
                series.append((d, *byday.get(d, (None, 0))))
            pa = Gtk.DrawingArea()
            pa.set_size_request(-1, 150)

            def pdraw(w, cr, series=series):
                col = w.get_style_context().get_color(Gtk.StateFlags.NORMAL)
                draw_pron_chart(cr, w.get_allocated_width(), w.get_allocated_height(), series,
                                (col.red, col.green, col.blue))
            pa.connect("draw", pdraw)
            b.pack_start(card(pa), False, False, 0)
            weak = db.pron_weak(6)
            if weak:
                wc = card(spacing=3)
                wc.pack_start(label(_("Najtrudniejsze zdania (do poćwiczenia)"), "dim"), False, False, 0)
                for tgt, a, n in weak:
                    row = Gtk.Box(spacing=8)
                    row.pack_start(label(f"{tgt}", "mid-es"), True, True, 0)
                    row.pack_start(label(f"{round(a)}% · {n}×", "dim", wrap=False), False, False, 0)
                    row.pack_start(SpeakButton(self.app, tgt), False, False, 0)
                    wc.pack_start(row, False, False, 0)
                b.pack_start(wc, False, False, 0)

        st_lbl = (_('Nowe: {}  ·  W nauce: {}  ·  Powtarzane: {}  ·  Opanowane (odstęp ≥ 21 dni): {}').format(st['nowe'], st['uczone'], st['powtarzane'], st['opanowane']))
        b.pack_start(label(_("Słówka"), "title2"), False, False, 0)
        b.pack_start(card(label(st_lbl)), False, False, 0)

        mist = db.recent_mistakes(15)
        if mist:
            b.pack_start(label(_("Ostatnie błędy — warto do nich wrócić"), "title2"), False, False, 0)
            d_due, d_total = db.drill_counts()
            if d_total:
                tr = Gtk.Box(spacing=10)
                tr.pack_start(label(_('W treningu błędów: {} (do powtórki teraz: {})').format(d_total, d_due), "dim"),
                              False, False, 0)
                tb = Gtk.Button(label=_("Otwórz trening"))
                tb.connect("clicked", lambda *_a: self.app.open_review("drill"))
                tr.pack_start(tb, False, False, 0)
                b.pack_start(tr, False, False, 0)
            c = card(spacing=3)
            for m in mist:
                c.pack_start(label(f"•  {m['q']}  →  {m['expected']}" +
                                   (f"   (Twoja odp.: {m['given']})" if m["given"] else "")), False, False, 0)
            b.pack_start(c, False, False, 0)
        b.show_all()


def draw_pron_chart(cr, W, H, series, rgb):
    """Wykres średniego wyniku wymowy dnia. series: [(dzień, średnia|None, n)] — 30 punktów."""
    r, g, b = rgb
    top, bot_ = 14, H - 20
    cr.set_font_size(10)
    for lvl in (50, 75, 100):
        y = bot_ - (bot_ - top) * lvl / 100
        cr.set_source_rgba(r, g, b, 0.12)
        cr.rectangle(0, y, W, 1)
        cr.fill()
        cr.set_source_rgba(r, g, b, 0.55)
        cr.move_to(2, y - 2)
        cr.show_text(f"{lvl}%")
    step = (W - 40) / max(1, len(series) - 1)
    pts = [(30 + k * step, bot_ - (bot_ - top) * a / 100) for k, (_d, a, _n) in enumerate(series) if a is not None]
    cr.set_source_rgba(0.18, 0.62, 0.27, 0.9)
    cr.set_line_width(2)
    for k, (x, y) in enumerate(pts):
        cr.line_to(x, y) if k else cr.move_to(x, y)
    cr.stroke()
    for x, y in pts:
        cr.arc(x, y, 3.2, 0, 6.3)
        cr.fill()
    cr.set_source_rgba(r, g, b, 0.6)
    for k in (0, 10, 20, len(series) - 1):
        cr.move_to(30 + k * step - 10, H - 5)
        cr.show_text(series[k][0][5:])


# ====================================================================== USTAWIENIA
TEST_PHRASE = "¡Hola! Buenos días. Me llamo Paco. ¿Cómo estás?"


_KEY_TIMER = {}


def _debounced_key(entry):
    """Zapis klucza API do schowka dopiero po chwili bez pisania (nie przy każdym znaku)."""
    from .. import bot as botmod
    old = _KEY_TIMER.pop("t", None)
    if old:
        GLib.source_remove(old)
    text = entry.get_text()

    def go():
        _KEY_TIMER.pop("t", None)
        botmod.save_api_key(text)
        return False
    _KEY_TIMER["t"] = GLib.timeout_add(700, go)


class _BackupMixin:
    def _msg(self, text, sec="", kind=Gtk.MessageType.INFO):
        d = Gtk.MessageDialog(transient_for=self.get_toplevel(), modal=True, message_type=kind,
                              buttons=Gtk.ButtonsType.OK, text=text)
        if sec:
            d.format_secondary_text(sec)
        d.run()
        d.destroy()

    def do_export(self):
        from .. import backup
        dlg = Gtk.FileChooserNative.new(_("Zapisz kopię zapasową"), self.get_toplevel(),
                                        Gtk.FileChooserAction.SAVE, _("Zapisz"), _("Anuluj"))
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_name(backup.default_name(self.app.db))
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            path = dlg.get_filename()
            if not path.lower().endswith(".zip"):
                path += ".zip"
            try:
                backup.export_profile(self.app.db, path)
                self._msg(_("Kopia zapisana"), path)
            except Exception as e:  # noqa
                self._msg(_("Nie udało się zapisać kopii"), str(e), Gtk.MessageType.ERROR)
        dlg.destroy()

    def do_import(self):
        from .. import backup
        dlg = Gtk.FileChooserNative.new(_("Wczytaj kopię zapasową"), self.get_toplevel(),
                                        Gtk.FileChooserAction.OPEN, _("Wczytaj"), _("Anuluj"))
        flt = Gtk.FileFilter()
        flt.set_name("Kopia zapasowa (.zip)")
        flt.add_pattern("*.zip")
        dlg.add_filter(flt)
        path = dlg.get_filename() if dlg.run() == Gtk.ResponseType.ACCEPT else None
        dlg.destroy()
        if not path:
            return
        try:
            meta = backup.inspect(path)
            pid = backup.import_profile(path)
        except Exception as e:  # noqa
            self._msg(_("Nie udało się wczytać kopii"), str(e), Gtk.MessageType.ERROR)
            return
        self._msg(_("Kopia wczytana"), _("Utworzono nowy profil „{} (import)”. Przełączam na niego.").format(
            meta.get('profile', _('Profil'))))
        self.app.switch_profile(pid)


class SettingsPage(_BackupMixin, Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.refresh()

    def refresh(self):
        app, db = self.app, self.app.db
        clear(self.inner)
        b = self.inner
        b.pack_start(label(_("Ustawienia"), "hero"), False, False, 0)

        # Głos
        c = card()
        c.pack_start(label(_("Głos i odtwarzanie"), "title2"), False, False, 0)
        g = Gtk.Grid(column_spacing=12, row_spacing=10)
        voice = Gtk.ComboBoxText()
        voice.append("m", _("Męski — Hiszpania (davefx)"))
        voice.append("f", _("Żeński — Hiszpania (sharvard)"))
        for k, (_n, _p, lab) in speech.EXTRA_VOICES.items():
            voice.append(k, lab + ("" if speech.voice_available(k) else _("  ⬇ pobierze się")))
        voice.set_active_id(db.get("voice", "m"))
        vstatus = label("", "dim")

        def voice_changed(w):
            key = w.get_active_id()
            if not key:
                return
            if speech.voice_available(key):
                db.set("voice", key)
                vstatus.set_text("")
                app.say(TEST_PHRASE)
                return
            vstatus.set_text(_("Pobieram głos… (kilkadziesiąt MB)"))
            w.set_sensitive(False)

            def done(ok, msg):
                w.set_sensitive(True)
                if ok:
                    db.set("voice", key)
                    vstatus.set_text(_("Głos pobrany ✔"))
                    app.say(TEST_PHRASE)
                else:
                    vstatus.set_text(_("Nie udało się pobrać głosu: ") + msg)
                    w.set_active_id(db.get("voice", "m"))
                return False
            speech.download_voice(key, lambda f: None, lambda ok, m: GLib.idle_add(done, ok, m))
        voice.connect("changed", voice_changed)
        g.attach(label(_("Głos lektora:"), wrap=False), 0, 0, 1, 1)
        vb = Gtk.Box(spacing=8)
        vb.pack_start(voice, False, False, 0)
        tb = Gtk.Button(label=_("▶ Posłuchaj"))
        tb.connect("clicked", lambda *_a: app.say(TEST_PHRASE))
        vb.pack_start(tb, False, False, 0)
        vb.pack_start(vstatus, False, False, 0)
        g.attach(vb, 1, 0, 1, 1)
        speed = Gtk.ComboBoxText()
        for v, t in (("1.0", _("Normalne tempo")), ("1.15", _("Trochę wolniej")), ("1.3", _("Wolno"))):
            speed.append(v, t)
        speed.set_active_id(str(db.get("tts_scale", 1.0)))
        if speed.get_active_id() is None:
            speed.set_active_id("1.0")
        speed.connect("changed", lambda w: db.set("tts_scale", float(w.get_active_id())))
        g.attach(label(_("Tempo mowy:"), wrap=False), 0, 1, 1, 1)
        g.attach(speed, 1, 1, 1, 1)
        auto = Gtk.Switch()
        auto.set_active(db.get("autoplay", True))
        auto.set_halign(Gtk.Align.START)
        auto.connect("notify::active", lambda w, _p: db.set("autoplay", w.get_active()))
        g.attach(label(_("Czytaj automatycznie odpowiedzi i fiszki:"), wrap=False), 0, 2, 1, 1)
        g.attach(auto, 1, 2, 1, 1)
        c.pack_start(g, False, False, 0)
        b.pack_start(c, False, False, 0)

        # Wygląd
        cw = card()
        cw.pack_start(label(_("Wygląd"), "title2"), False, False, 0)
        gw = Gtk.Grid(column_spacing=12, row_spacing=10)
        from . import themes
        th = Gtk.ComboBoxText()
        for k, (name, _l, _d) in themes.THEMES.items():
            th.append(k, name)
        th.set_active_id(db.get("color_theme", "system"))
        th.connect("changed", lambda w: (db.set("color_theme", w.get_active_id()), app.apply_theme()))
        gw.attach(label(_("Motyw kolorystyczny:"), wrap=False), 0, 0, 1, 1)
        gw.attach(th, 1, 0, 1, 1)
        md = Gtk.ComboBoxText()
        for k, name in themes.MODES.items():
            md.append(k, name)
        md.set_active_id(db.get("theme_mode", "auto"))
        md.connect("changed", lambda w: (db.set("theme_mode", w.get_active_id()), app.apply_theme()))
        gw.attach(label(_("Jasny / ciemny:"), wrap=False), 0, 1, 1, 1)
        gw.attach(md, 1, 1, 1, 1)
        cw.pack_start(gw, False, False, 0)
        cw.pack_start(label(_("Każdy motyw ma wersję jasną i ciemną. „Automatycznie” przełącza się razem z systemem."),
                            "dim"), False, False, 0)
        b.pack_start(cw, False, False, 0)

        # Bot
        from .. import bot as botmod
        from .bot_settings import BotSettings
        b.pack_start(BotSettings(app, _debounced_key), False, False, 0)

        # Cel dzienny
        cg = card()
        cg.pack_start(label(_("Cel dzienny i przypomnienia"), "title2"), False, False, 0)
        gg = Gtk.Grid(column_spacing=12, row_spacing=10)
        goal = Gtk.ComboBoxText()
        for m in (5, 10, 15, 20, 30, 45, 60):
            goal.append(str(m), _('{} minut dziennie').format(m))
        goal.set_active_id(str(db.get("daily_goal", 10)))
        if goal.get_active_id() is None:
            goal.set_active_id("10")
        goal.connect("changed", lambda w: db.set("daily_goal", int(w.get_active_id())))
        gg.attach(label(_("Cel nauki:"), wrap=False), 0, 0, 1, 1)
        gg.attach(goal, 1, 0, 1, 1)
        rem = Gtk.Switch()
        rem.set_active(bool(db.get("remind_on", True)))
        rem.set_halign(Gtk.Align.START)
        rem.connect("notify::active", lambda w, _p: db.set("remind_on", w.get_active()))
        gg.attach(label(_("Przypomnij, jeśli cel niezaliczony:"), wrap=False), 0, 1, 1, 1)
        gg.attach(rem, 1, 1, 1, 1)
        hour = Gtk.ComboBoxText()
        for hh in range(8, 23):
            hour.append(str(hh), f"{hh}:00")
        hour.set_active_id(str(db.get("remind_hour", 19)))
        hour.connect("changed", lambda w: db.set("remind_hour", int(w.get_active_id())))
        gg.attach(label(_("Godzina przypomnienia:"), wrap=False), 0, 2, 1, 1)
        gg.attach(hour, 1, 2, 1, 1)
        cg.pack_start(gg, False, False, 0)
        cg.pack_start(label(_("Przypomnienie to zwykłe powiadomienie systemowe — pojawia się, gdy aplikacja jest uruchomiona."), "dim"), False, False, 0)
        b.pack_start(cg, False, False, 0)

        # Kopia zapasowa
        ck = card()
        ck.pack_start(label(_("Kopia zapasowa postępu"), "title2"), False, False, 0)
        ck.pack_start(label(_("Zapisz cały postęp bieżącego profilu (lekcje, powtórki, wyniki, rozmowy, „O mnie”) "
                            "do jednego pliku .zip — np. żeby przenieść naukę na inny komputer. Import zawsze "
                            "tworzy nowy profil i niczego nie nadpisuje."), "dim"), False, False, 0)
        kr = Gtk.Box(spacing=8)
        eb = Gtk.Button(label=_("💾  Zapisz kopię…"))
        eb.connect("clicked", lambda *_a: self.do_export())
        ib2 = Gtk.Button(label=_("📂  Wczytaj kopię…"))
        ib2.connect("clicked", lambda *_a: self.do_import())
        kr.pack_start(eb, False, False, 0)
        kr.pack_start(ib2, False, False, 0)
        ck.pack_start(kr, False, False, 0)
        b.pack_start(ck, False, False, 0)

        # Powtórki
        c2 = card()
        c2.pack_start(label(_("Powtórki"), "title2"), False, False, 0)
        g2 = Gtk.Grid(column_spacing=12, row_spacing=10)
        adj = Gtk.Adjustment(value=db.get("new_per_day", 20), lower=5, upper=100, step_increment=5)
        sp = Gtk.SpinButton(adjustment=adj)
        sp.connect("value-changed", lambda w: db.set("new_per_day", int(w.get_value())))
        g2.attach(label(_("Nowych słów dziennie:"), wrap=False), 0, 0, 1, 1)
        g2.attach(sp, 1, 0, 1, 1)
        d = Gtk.ComboBoxText()
        d.append("mix", _("Na zmianę (ES→PL i PL→ES)"))
        d.append("es", _("Hiszpański → polski"))
        d.append("pl", _("Polski → hiszpański"))
        d.set_active_id(db.get("review_dir", "mix"))
        d.connect("changed", lambda w: db.set("review_dir", w.get_active_id()))
        g2.attach(label(_("Kierunek fiszek:"), wrap=False), 0, 1, 1, 1)
        g2.attach(d, 1, 1, 1, 1)
        c2.pack_start(g2, False, False, 0)
        b.pack_start(c2, False, False, 0)

        # Silnik mowy
        hw = speech.hardware()
        c3 = card()
        c3.pack_start(label(_("Silnik mowy (offline)"), "title2"), False, False, 0)
        tts_ok = speech.engine_installed() and speech.voices_installed()
        size = db.get("whisper", speech.recommend(hw))
        stt_ok = speech.engine_installed() and speech.whisper_ready(size)
        c3.pack_start(label(_('Synteza mowy (Piper, głosy z Hiszpanii): {}').format(_('✔ zainstalowana') if tts_ok else _('✘ brak'))),
                      False, False, 0)
        c3.pack_start(label(_('Rozpoznawanie mowy (Whisper, model „{}”): {}').format(size, _('✔ zainstalowane') if stt_ok else _('✘ brak'))), False, False, 0)
        g3 = Gtk.Grid(column_spacing=12, row_spacing=10)
        c3.pack_start(label(_("Model rozpoznawania mowy wybierasz w sekcji „Rozmowa z botem” powyżej."), "dim"),
                      False, False, 0)
        cuda = Gtk.CheckButton(label=_("Używaj karty NVIDIA (CUDA) — pobiera dodatkowo ok. 1 GB bibliotek"))
        cuda.set_active(db.get("cuda", False))
        cuda.set_sensitive(hw["nvidia"])
        if not hw["nvidia"]:
            cuda.set_tooltip_text(_("Nie wykryto karty NVIDIA ze sterownikiem (nvidia-smi)."))
        g3.attach(cuda, 0, 0, 2, 1)
        c3.pack_start(g3, False, False, 0)
        inst = Gtk.Button(label=_("Zainstaluj / zaktualizuj komponenty"))
        inst.get_style_context().add_class("suggested-action")
        inst.set_halign(Gtk.Align.START)

        def do_install(*_a):
            db.set("cuda", cuda.get_active())
            app.open_setup()
        inst.connect("clicked", do_install)
        c3.pack_start(inst, False, False, 0)
        b.pack_start(c3, False, False, 0)

        # Sprzęt
        c4 = card(spacing=4)
        c4.pack_start(label(_("Twój komputer"), "title2"), False, False, 0)
        c4.pack_start(label(_("Procesor: {} ({} wątków)\nPamięć RAM: {} GB\nKarta graficzna: {}").format(
                                hw['cpu'] or '?', hw['cores'], hw['ram'], ', '.join(hw['gpus']) or _('nie wykryto'))
                            + (_("  (sterownik NVIDIA aktywny)") if hw["nvidia"] else "")), False, False, 0)
        probs = speech.meets_minimum(hw)
        c4.pack_start(label(_("✔ Spełnia wymagania minimalne.") if not probs else
                            _("⚠ Poniżej minimum: ") + "; ".join(probs) + _(". Wybierz model „Szybki”."),
                            "ok-text" if not probs else "warn-text"), False, False, 0)
        c4.pack_start(label(_("Minimum: Ubuntu 24.04+ (64-bit), procesor 4-rdzeniowy, 8 GB RAM, ok. 1 GB miejsca, "
                            "dowolna karta graficzna (zintegrowana wystarczy), mikrofon.\n"
                            "Zalecane: procesor 6–8 rdzeni, 16 GB RAM, słuchawki z mikrofonem; "
                            "karta NVIDIA opcjonalnie przyspiesza rozpoznawanie mowy."), "dim"), False, False, 0)
        b.pack_start(c4, False, False, 0)

        # Reset
        c5 = card()
        c5.pack_start(label(_("Postęp"), "title2"), False, False, 0)
        rb = Gtk.Button(label=_("Wyzeruj cały postęp…"))
        rb.get_style_context().add_class("destructive-action")
        rb.set_halign(Gtk.Align.START)
        rb.connect("clicked", self._reset)
        c5.pack_start(rb, False, False, 0)
        b.pack_start(c5, False, False, 0)
        b.show_all()

    def _reset(self, *_a):
        dlg = Gtk.MessageDialog(transient_for=self.get_toplevel(), modal=True,
                                message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK_CANCEL,
                                text=_("Wyzerować cały postęp?"))
        dlg.format_secondary_text(_("Usunięte zostaną ukończone lekcje, słówka w powtórkach, wyniki testów i statystyki. "
                                  "Tej operacji nie można cofnąć."))
        if dlg.run() == Gtk.ResponseType.OK:
            self.app.db.reset()
            self.app.refresh_all()
        dlg.destroy()


# ====================================================================== KREATOR INSTALACJI
class SetupDialog(Gtk.Dialog):
    def __init__(self, app, parent):
        super().__init__(title=_("Instalacja silnika mowy"), transient_for=parent, modal=True)
        self.app = app
        self.set_default_size(640, 480)
        db = app.db
        hw = speech.hardware()
        size = db.get("whisper") or speech.recommend(hw)
        db.set("whisper", size)
        box = self.get_content_area()
        box.set_spacing(10)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(16)
        box.pack_start(label(_("Pobierzemy jednorazowo (wszystko zostaje na Twoim komputerze i działa offline):"), "title2"),
                       False, False, 0)
        box.pack_start(label(_('• silnik mowy Piper + faster-whisper (pakiety Python, ok. 200 MB)\n• dwa głosy hiszpańskie z Hiszpanii (ok. 130 MB)\n• model rozpoznawania mowy „{}” ({})').format(size, speech.WHISPER_SIZES[size][1])
                             + ("\n• biblioteki CUDA dla karty NVIDIA (ok. 1 GB)" if db.get("cuda") else "")),
                     False, False, 0)
        self.bar = Gtk.ProgressBar()
        box.pack_start(self.bar, False, False, 0)
        self.status = label("", markup=True)
        box.pack_start(self.status, False, False, 0)
        self.buf = Gtk.TextBuffer()
        tv = Gtk.TextView(buffer=self.buf)
        tv.set_editable(False)
        tv.set_monospace(True)
        tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        self.tv = tv
        box.pack_start(scrolled(tv), True, True, 0)
        self.start_btn = self.add_button(_("Rozpocznij"), Gtk.ResponseType.OK)
        self.start_btn.get_style_context().add_class("suggested-action")
        self.close_btn = self.add_button(_("Zamknij"), Gtk.ResponseType.CLOSE)
        self.connect("response", self._resp)
        self.show_all()

    def _resp(self, _d, rid):
        if rid == Gtk.ResponseType.OK:
            self.start_btn.set_sensitive(False)
            self.close_btn.set_sensitive(False)
            st = speech.Setup(self.app.db.get("whisper"), self.app.db.get("cuda", False),
                              lambda t: GLib.idle_add(self._log, t),
                              lambda f: GLib.idle_add(self.bar.set_fraction, f),
                              lambda ok, m: GLib.idle_add(self._done, ok, m))
            st.start()
        else:
            self.destroy()

    def _log(self, t):
        self.buf.insert(self.buf.get_end_iter(), t + "\n")
        self.tv.scroll_to_iter(self.buf.get_end_iter(), 0, False, 0, 0)

    def _done(self, ok, msg):
        self.close_btn.set_sensitive(True)
        if ok:
            self.start_btn.set_label(_("Gotowe ✔"))
            self.status.set_markup(_('<span foreground="#2e9e44" size="large"><b>✔ Instalacja zakończona '
                                   'pomyślnie.</b></span> Możesz zamknąć to okno — wymowa i ocena wymowy już działają.'))
            self.app.speech.shutdown()
            self.app.speech = speech.Speech(self.app.db)
            self.app.speech.preload_stt()
            self.app.refresh_all()
            self.app.say("¡Hola! Ya puedes aprender español conmigo.")
        else:
            self.status.set_markup(_('<span foreground="#d0353f" size="large"><b>✘ Instalacja nie powiodła się.</b>'
                                   '</span> Szczegóły w dzienniku poniżej.'))
            self.start_btn.set_label(_("Spróbuj ponownie"))
            self.start_btn.set_sensitive(True)
            self._log(_("\nNie udało się. Sprawdź połączenie z internetem i spróbuj ponownie."))
