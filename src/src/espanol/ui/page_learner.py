"""Ekran: O mnie — informacje o uczniu, z których korzysta bot."""
import json

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import label, scrolled, page_box, card, clear
from .. import bot

FIELDS = [
    ("name", "Imię", "np. Jarek"),
    ("city", "Miejscowość", "np. Rumia"),
    ("country", "Kraj", "np. Polska"),
    ("job", "Praca / szkoła", "np. informatyk, student"),
    ("family", "Rodzina", "np. żona, dwoje dzieci"),
    ("hobbies", "Zainteresowania", "np. muzyka, rower, podróże"),
]


def load_manual(db):
    d = db.get("learner", {}) or {}
    return d if d.get("use", True) is not False else {}


def load_auto(db):
    return db.get("learner_auto", {}) or {}


class LearnerPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(self.outer, True, True, 0)
        self.refresh()

    def refresh(self):
        db = self.app.db
        clear(self.outer)
        data = db.get("learner", {}) or {}
        b = page_box()
        b.pack_start(label("O mnie", "hero"), False, False, 0)
        b.pack_start(label("Tu wpisujesz to, co bot ma o Tobie wiedzieć, żeby rozmowa była naturalna i nie pytał "
                           "w kółko o to samo. Wszystko jest zapisane tylko na tym komputerze. Przy silniku Claude API "
                           "te informacje są wysyłane razem z tekstem rozmowy.", "dim"), False, False, 0)

        c = card(spacing=10)
        use = Gtk.CheckButton(label="Bot zna informacje o mnie")
        use.set_active(data.get("use", True) is not False)

        def save(*_):
            d = {k: e.get_text().strip() for k, e in self.entries.items()}
            nb = self.notes.get_buffer()
            d["notes"] = nb.get_text(nb.get_start_iter(), nb.get_end_iter(), False).strip()
            d["use"] = use.get_active()
            db.set("learner", d)
            self._preview()
        c.pack_start(use, False, False, 0)
        grid = Gtk.Grid(column_spacing=12, row_spacing=8)
        self.entries = {}
        for i, (k, name, ph) in enumerate(FIELDS):
            e = Gtk.Entry()
            e.set_text(data.get(k, ""))
            e.set_placeholder_text(ph)
            e.set_hexpand(True)
            e.connect("changed", save)
            self.entries[k] = e
            grid.attach(label(name + ":", wrap=False), 0, i, 1, 1)
            grid.attach(e, 1, i, 1, 1)
        grid.attach(label("Inne:", wrap=False), 0, len(FIELDS), 1, 1)
        self.notes = Gtk.TextView()
        self.notes.set_wrap_mode(Gtk.WrapMode.WORD)
        self.notes.set_size_request(-1, 70)
        self.notes.get_buffer().set_text(data.get("notes", ""))
        self.notes.get_buffer().connect("changed", save)
        frame = Gtk.Frame()
        frame.add(self.notes)
        grid.attach(frame, 1, len(FIELDS), 1, 1)
        use.connect("toggled", save)
        c.pack_start(grid, False, False, 0)
        c.pack_start(label("Możesz pisać po polsku — bot to zrozumie.", "dim"), False, False, 0)
        b.pack_start(c, False, False, 0)

        # fakty zebrane z rozmów
        auto = load_auto(db)
        c2 = card(spacing=6)
        c2.pack_start(label("Czego bot dowiedział się z naszych rozmów", "title2"), False, False, 0)
        if not any(auto.values()):
            c2.pack_start(label("Jeszcze nic — pojawi się tu to, co powiesz po hiszpańsku, np. „me llamo…”, "
                                "„vivo en…”, „trabajo como…”, „me gusta…”.", "dim"), False, False, 0)
        for k, vals in auto.items():
            for v in vals:
                row = Gtk.Box(spacing=8)
                row.pack_start(label(f"{bot.FACT_LABELS_PL.get(k, k)}: <b>{GLib.markup_escape_text(v)}</b>", markup=True), True, True, 0)
                rm = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
                rm.set_tooltip_text("Usuń ten fakt")
                rm.connect("clicked", lambda _b, kk=k, vv=v: self._remove(kk, vv))
                row.pack_start(rm, False, False, 0)
                c2.pack_start(row, False, False, 0)
        if any(auto.values()):
            cl = Gtk.Button(label="Wyczyść wszystko")
            cl.set_halign(Gtk.Align.START)
            cl.connect("clicked", lambda *_: (db.set("learner_auto", {}), self.refresh()))
            c2.pack_start(cl, False, False, 0)
        b.pack_start(c2, False, False, 0)

        c3 = card(spacing=6)
        c3.pack_start(label("Tak bot widzi Twoją „kartkę”", "title2"), False, False, 0)
        self.prev = label("", "dim", selectable=True)
        c3.pack_start(self.prev, False, False, 0)
        b.pack_start(c3, False, False, 0)
        self.outer.pack_start(scrolled(b), True, True, 0)
        self.outer.show_all()
        self._preview()

    def _preview(self):
        db = self.app.db
        txt = bot.facts_prompt(load_manual(db), load_auto(db))
        self.prev.set_text(txt or "(pusto — bot nie wie jeszcze nic o Tobie)")

    def _remove(self, k, v):
        db = self.app.db
        auto = load_auto(db)
        auto[k] = [x for x in auto.get(k, []) if x != v]
        if not auto[k]:
            auto.pop(k)
        db.set("learner_auto", auto)
        self.refresh()
