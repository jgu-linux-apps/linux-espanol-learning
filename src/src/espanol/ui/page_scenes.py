"""Scenki z Paco: dialog z lekcji — Paco mówi swoje kwestie, Ty swoje (z oceną wymowy)."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import label, scrolled, page_box, card, clear, SpeakButton, slow_button
from .pron import SpeakPractice
from ..i18n import _


def scene_list(course, done_ids):
    """Lekcje z dialogiem dwóch osób; ukończone najpierw."""
    out = []
    for l in course.lessons:
        who = []
        for w, es, _pl in l.dialog:
            if es and w not in who:
                who.append(w)
        if len(l.dialog) >= 4 and len(who) >= 2:
            out.append((l, who))
    out.sort(key=lambda x: (x[0].id not in done_ids, x[0].level, x[0].number))
    return out


class ScenesPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.scene = None
        self.show_start()

    def refresh(self):
        pass

    # ----------------------------------------------------------- wybór scenki
    def show_start(self):
        self.app.stop_audio() if hasattr(self.app, "stop_audio") else None
        clear(self.inner)
        b = self.inner
        b.pack_start(label(_("Scenki z Paco"), "hero"), False, False, 0)
        c = card(spacing=8)
        c.pack_start(label(_("Odegraj dialog z lekcji: Paco mówi swoje kwestie na głos, a Ty mówisz swoje do "
                             "mikrofonu. Każda Twoja kwestia dostaje ocenę wymowy słowo po słowie, na końcu "
                             "dostajesz wynik całej scenki."), None), False, False, 0)
        if not self.app.speech.stt_available():
            c.pack_start(label(_("Ocena wymowy wymaga modelu rozpoznawania mowy — zainstaluj go na ekranie „Dzisiaj”."),
                               "warn-text"), False, False, 0)
        b.pack_start(c, False, False, 0)
        done = set(self.app.db.done_lessons())
        scenes = scene_list(self.app.course, done)
        if not scenes:
            b.pack_start(label(_("Brak dialogów do odegrania.")), False, False, 0)
        for les, who in scenes:
            r = card(spacing=4)
            row = Gtk.Box(spacing=10)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            col.pack_start(label(_("{} · Lekcja {}: {}").format(les.level, les.number, les.title) +
                                 ("  ✔" if les.id in done else ""), "title2"), False, False, 0)
            col.pack_start(label(_("Role: {}  ·  {} kwestii").format(_(" i ").join(who[:2]), len(les.dialog)), "dim"), False, False, 0)
            row.pack_start(col, True, True, 0)
            for who_me in who[:2]:
                bt = Gtk.Button(label=_("Gram: {}").format(who_me))
                bt.connect("clicked", lambda _b, l=les, w=who_me: self.start_scene(l, w))
                row.pack_start(bt, False, False, 0)
            r.pack_start(row, False, False, 0)
            b.pack_start(r, False, False, 0)
        self.show_all()

    # ----------------------------------------------------------- scenka
    def start_scene(self, lesson, me):
        self.lesson, self.me = lesson, me
        self.lines = [(w, es, pl) for w, es, pl in lesson.dialog if es]
        self.i, self.scores, self.history = 0, [], []
        self.render()

    def render(self):
        clear(self.inner)
        b = self.inner
        b.pack_start(label(f"{self.lesson.level} · {self.lesson.title}", "hero"), False, False, 0)
        partner = next((w for w, _e, _p in self.lines if w != self.me), "")
        b.pack_start(label(_("Grasz: {}  ·  Paco gra: {}  ·  kwestia {} z {}").format(
            self.me, partner, min(self.i + 1, len(self.lines)), len(self.lines)),
                           "dim"), False, False, 0)
        # dotychczasowy przebieg
        if self.history:
            hc = card(spacing=4)
            for who, es, pl, sc in self.history:
                mine = who == self.me
                row = Gtk.Box(spacing=8)
                tag = f"{who}: " + es + (f"   — {sc}%" if sc is not None else "")
                lb = label(tag, "mid-es")
                lb.set_halign(Gtk.Align.END if mine else Gtk.Align.START)
                row.pack_start(lb, True, True, 0)
                hc.pack_start(row, False, False, 0)
            b.pack_start(hc, False, False, 0)
        if self.i >= len(self.lines):
            self.show_end(b)
            self.show_all()
            return
        who, es, pl = self.lines[self.i]
        cur = card(spacing=8)
        if who == self.me:
            cur.pack_start(label(_("Twoja kolej — powiedz:"), "dim"), False, False, 0)
            sp = SpeakPractice(self.app, es, pl, on_scored=self.on_scored)
            cur.pack_start(sp, False, False, 0)
            row = Gtk.Box(spacing=8)
            nxt = Gtk.Button(label=_("Dalej ▶"))
            nxt.get_style_context().add_class("suggested-action")
            nxt.connect("clicked", lambda *_a: self.advance(self._last))
            skip = Gtk.Button(label=_("Pomiń"))
            skip.connect("clicked", lambda *_a: self.advance(None))
            row.pack_start(nxt, False, False, 0)
            row.pack_start(skip, False, False, 0)
            cur.pack_start(row, False, False, 0)
            self._last = None
            self.next_btn = nxt
            nxt.set_sensitive(not self.app.speech.stt_available())
        else:
            cur.pack_start(label(_("{} mówi:").format(who), "dim"), False, False, 0)
            r = Gtk.Box(spacing=8)
            r.pack_start(label(es, "big-es"), True, True, 0)
            r.pack_start(SpeakButton(self.app, es), False, False, 0)
            r.pack_start(slow_button(self.app, es), False, False, 0)
            cur.pack_start(r, False, False, 0)
            cur.pack_start(label(pl, "dim"), False, False, 0)
            nxt = Gtk.Button(label=_("Dalej ▶"))
            nxt.get_style_context().add_class("suggested-action")
            nxt.set_halign(Gtk.Align.START)
            nxt.connect("clicked", lambda *_a: self.advance(None))
            cur.pack_start(nxt, False, False, 0)
            GLib.timeout_add(300, lambda i=self.i: (self.app.say(es) if i == self.i else None, False)[1])
        b.pack_start(cur, False, False, 0)
        self.show_all()
        GLib.timeout_add(100, self._scroll_end)

    def _scroll_end(self):
        sw = self.get_children()[0]
        adj = sw.get_vadjustment()
        adj.set_value(adj.get_upper())
        return False

    def on_scored(self, score):
        self._last = score
        if getattr(self, "next_btn", None):
            self.next_btn.set_sensitive(True)

    def advance(self, score):
        who, es, pl = self.lines[self.i]
        if who == self.me and score is not None:
            self.scores.append(score)
        self.history.append((who, es, pl, score if who == self.me else None))
        self.i += 1
        self.render()

    def show_end(self, b):
        c = card(spacing=8)
        c.pack_start(label(_("Koniec scenki!"), "title2"), False, False, 0)
        if self.scores:
            avg = round(sum(self.scores) / len(self.scores))
            c.pack_start(label(f"{avg}%", "stat-num", wrap=False), False, False, 0)
            verdict = (_("¡Excelente! Brzmisz bardzo naturalnie.") if avg >= 90 else
                       _("¡Muy bien! Jeszcze trochę wprawy.") if avg >= 75 else
                       _("Nieźle — powtórz scenkę i mów wolniej.") if avg >= 50 else
                       _("Posłuchaj Paco jeszcze raz i spróbuj ponownie."))
            c.pack_start(label(verdict, "dim"), False, False, 0)
            weak = [(es, sc) for w, es, pl, sc in self.history if sc is not None and sc < 75]
            if weak:
                c.pack_start(label(_("Do poćwiczenia:"), "title2", wrap=False), False, False, 0)
                for es, sc in weak:
                    c.pack_start(label(f"{es} — {sc}%", "mid-es"), False, False, 0)
        else:
            c.pack_start(label(_("Nie oceniono żadnej kwestii — spróbuj nagrać swoje kwestie."), "dim"),
                         False, False, 0)
        row = Gtk.Box(spacing=8)
        again = Gtk.Button(label=_("↻  Jeszcze raz"))
        again.get_style_context().add_class("suggested-action")
        again.connect("clicked", lambda *_a: self.start_scene(self.lesson, self.me))
        other = Gtk.Button(label=_("Zamień role"))
        other_me = next((w for w, _e, _p in self.lines if w != self.me), self.me)
        other.connect("clicked", lambda *_a: self.start_scene(self.lesson, other_me))
        back = Gtk.Button(label=_("Wróć do listy"))
        back.connect("clicked", lambda *_a: self.show_start())
        for x in (again, other, back):
            row.pack_start(x, False, False, 0)
        c.pack_start(row, False, False, 0)
        b.pack_start(c, False, False, 0)
