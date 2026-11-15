"""Test poziomujący: ok. 14 pytań o rosnącej trudności -> sugerowana lekcja startowa."""
import random

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .widgets import label, card
from ..i18n import _  # noqa: E402


def build_questions(course, rng=None):
    """Po jednym pytaniu wyboru z co drugiej lekcji (rosnąca trudność). Zwraca [(lekcja, ćwiczenie)]."""
    rng = rng or random.Random()
    out = []
    for k, les in enumerate(course.lessons):
        if k % 2:
            continue
        pool = [e for e in les.exercises if e["type"] == "choice" and len(e["options"]) >= 2 and e["answers"]]
        if pool:
            out.append((les, rng.choice(pool)))
    return out


def recommend(results):
    """results: lista (lekcja, poprawnie). Pierwsze miejsce, od którego >= 2 z 3 odpowiedzi jest błędnych."""
    for i in range(len(results)):
        win = results[i:i + 3]
        if sum(1 for _l, ok in win if not ok) >= min(2, len(win)):
            return results[i][0]
    return None   # wszystko znane


class PlacementDialog(Gtk.Dialog):
    def __init__(self, app):
        super().__init__(title=_("Test poziomujący"), transient_for=app.win, modal=True)
        self.app = app
        self.set_default_size(640, 420)
        self.questions = build_questions(app.course)
        self.i, self.results = 0, []
        self.box = self.get_content_area()
        self.box.set_spacing(10)
        for side in ("start", "end", "top", "bottom"):
            getattr(self.box, f"set_margin_{side}")(16)
        self.show_intro()

    def _clear(self):
        for ch in self.box.get_children():
            self.box.remove(ch)
            ch.destroy()

    def show_intro(self):
        self._clear()
        self.box.pack_start(label(_("Test poziomujący"), "hero"), False, False, 0)
        self.box.pack_start(label(_('{} krótkich pytań o rosnącej trudności (słownictwo i gramatyka). Na tej podstawie podpowiem, od której lekcji najlepiej zacząć. Nie zgaduj na siłę — „Nie wiem” to dobra odpowiedź.').format(len(self.questions))), False, False, 0)
        b = Gtk.Button(label=_("Zaczynamy"))
        b.get_style_context().add_class("suggested-action")
        b.set_halign(Gtk.Align.START)
        b.connect("clicked", lambda *_a: self.show_q())
        self.box.pack_start(b, False, False, 0)
        self.box.show_all()

    def show_q(self):
        self._clear()
        les, ex = self.questions[self.i]
        self.box.pack_start(label(_('Pytanie {} z {}').format(self.i + 1, len(self.questions)), "dim"), False, False, 0)
        self.box.pack_start(label(ex["q"], "title2"), False, False, 0)
        c = card(spacing=6)
        for opt in ex["options"]:
            b = Gtk.Button(label=opt)
            b.set_halign(Gtk.Align.FILL)
            b.connect("clicked", lambda _b, o=opt: self.answer(les, ex, o))
            c.pack_start(b, False, False, 0)
        idk = Gtk.Button(label=_("Nie wiem"))
        idk.connect("clicked", lambda *_a: self.answer(les, ex, None))
        c.pack_start(idk, False, False, 0)
        self.box.pack_start(c, False, False, 0)
        self.box.show_all()

    def answer(self, les, ex, opt):
        ok = opt is not None and opt.strip().lower() in [a.strip().lower() for a in ex["answers"]]
        self.results.append((les, ok))
        self.i += 1
        if self.i < len(self.questions):
            self.show_q()
        else:
            self.show_result()

    def show_result(self):
        self._clear()
        right = sum(1 for _l, ok in self.results if ok)
        start = recommend(self.results)
        self.box.pack_start(label(_("Wynik testu"), "hero"), False, False, 0)
        self.box.pack_start(label(_('Poprawnie: {} z {}').format(right, len(self.results)), "title2"), False, False, 0)
        if start is None:
            self.box.pack_start(label(_("Znasz materiał całego kursu A1–A2 — możesz iść prosto do egzaminów "
                                      "próbnych i rozmów z Paco.")), False, False, 0)
            row = Gtk.Box(spacing=8)
            b = Gtk.Button(label=_("Egzamin próbny A2"))
            b.get_style_context().add_class("suggested-action")
            b.connect("clicked", lambda *_a: (self.destroy(), self.app.start_exam("A2")))
            row.pack_start(b, False, False, 0)
        else:
            self.box.pack_start(label(_('Polecam zacząć od: {} · Lekcja {}: {}').format(start.level, start.number, start.title)),
                                False, False, 0)
            self.box.pack_start(label(_("Wcześniejsze lekcje możesz oznaczyć jako znane — wtedy kurs poprowadzi "
                                      "Cię od polecanej lekcji (nic się nie usuwa, wyniki tych lekcji "
                                      "oznaczone będą jako 100%)."), "dim"), False, False, 0)
            row = Gtk.Box(spacing=8)
            b1 = Gtk.Button(label=_("Oznacz wcześniejsze jako znane i zacznij"))
            b1.get_style_context().add_class("suggested-action")
            b1.connect("clicked", lambda *_a: self._apply(start, True))
            b2 = Gtk.Button(label=_("Tylko otwórz lekcję"))
            b2.connect("clicked", lambda *_a: self._apply(start, False))
            row.pack_start(b1, False, False, 0)
            row.pack_start(b2, False, False, 0)
        close = Gtk.Button(label=_("Zamknij"))
        close.connect("clicked", lambda *_a: self.destroy())
        row.pack_start(close, False, False, 0)
        self.box.pack_start(row, False, False, 0)
        self.box.show_all()

    def _apply(self, start, mark):
        app = self.app
        if mark:
            for les in app.course.lessons:
                if les.id == start.id:
                    break
                app.db.mark_known(les)
        self.destroy()
        app.pages["today"].refresh()
        app.open_lesson(start.id)
