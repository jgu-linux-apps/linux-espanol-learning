"""Uniwersalny „odtwarzacz” ćwiczeń — używany w lekcjach, testach i czytankach."""
import random
import re

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .. import answers
from .widgets import label, AccentBar, SpeakButton, clear, slow_button

TYPE_TITLES = {
    "choice": "Wybierz poprawną odpowiedź",
    "fill": "Uzupełnij lukę",
    "trans": "Przetłumacz na hiszpański",
    "conj": "Odmień czasownik",
    "listen": "Dyktando",
    "order": "Ułóż zdanie z rozsypanki",
    "fix": "Popraw zdanie z rozmowy z Paco",
    "text": "Wpisz poprawną odpowiedź",
}


class ExerciseRunner(Gtk.Box):
    """exercises: lista dict; on_finish(score, total, mistakes).

    drill=True — błędne odpowiedzi trafiają do treningu błędów (Powtórki → Błędy).
    on_result(ex, wynik) — wołane po każdej odpowiedzi (używa tego sam trening)."""

    def __init__(self, app, exercises, on_finish, source="", show_progress=True, allow_skip=True,
                 drill=True, on_result=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.app = app
        self.items = exercises
        self.on_finish = on_finish
        self.source = source
        self.drill = drill
        self.on_result = on_result
        self.idx = 0
        self.score = 0.0
        self.mistakes = []
        self.answered = False
        self.allow_skip = allow_skip

        top = Gtk.Box(spacing=10)
        self.counter = label("", "dim", wrap=False)
        self.bar = Gtk.ProgressBar()
        self.bar.set_valign(Gtk.Align.CENTER)
        top.pack_start(self.counter, False, False, 0)
        top.pack_start(self.bar, True, True, 0)
        if show_progress:
            self.pack_start(top, False, False, 0)

        self.area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.area.get_style_context().add_class("card")
        self.pack_start(self.area, False, False, 0)

        self.feedback = label("", wrap=True, markup=True)
        self.pack_start(self.feedback, False, False, 0)

        btns = Gtk.Box(spacing=8)
        self.skip_btn = Gtk.Button(label="Nie wiem")
        self.skip_btn.connect("clicked", lambda *_: self._check(skip=True))
        self.check_btn = Gtk.Button(label="Sprawdź")
        self.check_btn.get_style_context().add_class("suggested-action")
        self.check_btn.connect("clicked", lambda *_: self._on_main())
        btns.pack_end(self.check_btn, False, False, 0)
        if allow_skip:
            btns.pack_end(self.skip_btn, False, False, 0)
        self.pack_start(btns, False, False, 0)
        self._show()

    # ------------------------------------------------------------
    def _show(self):
        clear(self.area)
        self.feedback.set_markup("")
        self.answered = False
        self.check_btn.set_label("Sprawdź")
        self.skip_btn.set_sensitive(True)
        n = len(self.items)
        if self.idx >= n:
            self.on_finish(round(self.score), n, self.mistakes)
            return
        self.counter.set_text(f"{self.idx + 1} / {n}")
        self.bar.set_fraction(self.idx / max(1, n))
        ex = self.items[self.idx]
        t = ex["type"]
        self.area.pack_start(label(TYPE_TITLES.get(t, "Ćwiczenie"), "dim"), False, False, 0)
        self.entry = None
        self.choice = None
        if t == "choice":
            self._build_choice(ex)
        elif t == "order":
            self._build_order(ex)
        else:
            self._build_entry(ex)
        self.area.show_all()
        if self.entry:
            GLib.idle_add(self.entry.grab_focus)
        if ex.get("audio") and t == "listen":
            GLib.timeout_add(250, lambda: (self.app.say(ex["audio"]), False)[1])

    def _q_row(self, text, audio=None, cls="mid-es"):
        row = Gtk.Box(spacing=6)
        row.pack_start(label(text, cls), True, True, 0)
        if audio:
            row.pack_start(SpeakButton(self.app, audio), False, False, 0)
        self.area.pack_start(row, False, False, 0)

    def _build_choice(self, ex):
        self._q_row(ex["q"], ex.get("audio"))
        opts = list(ex["options"]) or list(ex["answers"])
        if ex.get("shuffle", True):
            random.shuffle(opts)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(2 if max(len(o) for o in opts) > 28 else 4)
        flow.set_column_spacing(8)
        flow.set_row_spacing(8)
        self.choice_buttons = []
        for o in opts:
            b = Gtk.ToggleButton(label=o)
            b.get_style_context().add_class("choice-btn")
            b.get_child().set_line_wrap(True)
            b.connect("toggled", self._on_choice, o)
            flow.add(b)
            self.choice_buttons.append(b)
        self.area.pack_start(flow, False, False, 0)

    def _on_choice(self, btn, opt):
        if self.answered:
            return
        if btn.get_active():
            self.choice = opt
            for b in self.choice_buttons:
                if b is not btn and b.get_active():
                    b.set_active(False)
            self._check()

    def _build_entry(self, ex):
        t = ex["type"]
        if t == "listen":
            row = Gtk.Box(spacing=8)
            row.pack_start(SpeakButton(self.app, ex["audio"], tooltip="Odtwórz jeszcze raz"), False, False, 0)
            row.pack_start(slow_button(self.app, ex["audio"]), False, False, 0)
            row.pack_start(label("Posłuchaj i zapisz, co słyszysz.", "dim"), False, False, 0)
            self.area.pack_start(row, False, False, 0)
        else:
            q = ex["q"]
            if t == "trans" and not q.lower().startswith("przetłumacz"):
                q = q
            self._q_row(q)
        if ex.get("hint") and t != "listen":
            self.area.pack_start(label("Podpowiedź: " + ex["hint"], "dim"), False, False, 0)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Wpisz odpowiedź po hiszpańsku…")
        if t == "fix":
            self.entry.set_text(ex["q"])   # poprawiasz własne zdanie, nie przepisujesz go od zera
        self.entry.connect("activate", lambda *_: self._on_main())
        self.area.pack_start(self.entry, False, False, 0)
        self.area.pack_start(AccentBar(self.entry), False, False, 0)

    def _build_order(self, ex):
        self._q_row(ex["q"], cls="mid-es")
        target = ex["answers"][0]
        words = re.findall(r"\S+", target)
        tiles = words[:]
        for _ in range(5):
            random.shuffle(tiles)
            if tiles != words or len(words) < 2:
                break
        self.order_picked = []
        self.order_label = label("…", "big-es")
        self.area.pack_start(self.order_label, False, False, 0)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(8)
        self.order_buttons = []
        for w in tiles:
            b = Gtk.Button(label=w)
            b.get_style_context().add_class("tile")
            b.connect("clicked", self._pick_tile, w)
            flow.add(b)
            self.order_buttons.append(b)
        self.area.pack_start(flow, False, False, 0)
        undo = Gtk.Button(label="Cofnij")
        undo.set_halign(Gtk.Align.START)
        undo.connect("clicked", self._undo_tile)
        self.area.pack_start(undo, False, False, 0)

    def _pick_tile(self, b, w):
        if self.answered:
            return
        self.order_picked.append((b, w))
        b.set_sensitive(False)
        self.order_label.set_text(" ".join(x for _, x in self.order_picked))

    def _undo_tile(self, *_):
        if self.order_picked and not self.answered:
            b, _w = self.order_picked.pop()
            b.set_sensitive(True)
            self.order_label.set_text(" ".join(x for _, x in self.order_picked) or "…")

    # ------------------------------------------------------------
    def _on_main(self):
        if self.answered:
            self.idx += 1
            self._show()
        else:
            self._check()

    def _given(self):
        ex = self.items[self.idx]
        if ex["type"] == "choice":
            return self.choice or ""
        if ex["type"] == "order":
            return " ".join(w for _, w in self.order_picked)
        return self.entry.get_text() if self.entry else ""

    def _check(self, skip=False):
        if self.answered:
            return
        ex = self.items[self.idx]
        given = "" if skip else self._given()
        if not skip and not given.strip():
            return
        res, best = answers.check(given, ex["answers"]) if not skip else (answers.WRONG, ex["answers"][0])
        self.answered = True
        self.skip_btn.set_sensitive(False)
        self.check_btn.set_label("Dalej  →")
        esc = GLib.markup_escape_text
        if res == answers.OK:
            self.score += 1
            msg = '<span foreground="#2e9e44"><b>¡Muy bien! Dobrze.</b></span>'
        elif res == answers.ACCENT:
            self.score += 1
            msg = (f'<span foreground="#c77c00"><b>Dobrze, ale uważaj na akcenty:</b></span> '
                   f'{esc(best)}')
        elif res == answers.TYPO:
            self.score += 0.5
            msg = f'<span foreground="#c77c00"><b>Prawie — literówka.</b></span> Poprawnie: <b>{esc(best)}</b>'
        else:
            msg = f'<span foreground="#d0353f"><b>Niestety nie.</b></span> Poprawnie: <b>{esc(best)}</b>'
            self.mistakes.append(dict(q=ex["q"], given=given, expected=best))
            try:
                self.app.db.save_mistake(ex.get("source", self.source), ex["q"], given, best)
                if self.drill:
                    self.app.db.drill_add(dict(ex, source=ex.get("source") or self.source))
            except Exception as e:  # noqa
                print("zapis błędu:", e)
        if ex["type"] == "listen" and ex.get("hint"):
            msg += f'\n<span alpha="70%">{esc(ex["hint"])}</span>'
        if ex.get("note"):
            msg += f'\n<span alpha="80%">{esc(ex["note"])}</span>'
        if self.on_result:
            try:
                self.on_result(ex, res)
            except Exception as e:  # noqa
                print("on_result:", e)
        self.feedback.set_markup(msg)
        if ex["type"] == "choice":
            for b in self.choice_buttons:
                if answers.norm(b.get_label()) == answers.norm(ex["answers"][0]):
                    b.get_style_context().add_class("suggested-action")
                elif b.get_active():
                    b.get_style_context().add_class("destructive-action")
        # odczytaj poprawne zdanie po hiszpańsku
        if ex["type"] in ("trans", "order", "listen", "fill", "conj", "fix") and self.app.db.get("autoplay", True):
            spoken = best
            if ex["type"] == "fill" and "___" in ex["q"]:
                spoken = re.sub(r"\(.*?\)", "", ex["q"].replace("___", best)).strip()
                if re.search(r"[ąćęłńśźż]", spoken.lower()):
                    spoken = best
            self.app.say(spoken)
        self.check_btn.grab_focus()
