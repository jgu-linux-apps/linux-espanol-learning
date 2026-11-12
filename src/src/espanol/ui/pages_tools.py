"""Ekrany: Alfabet i wymowa, Powtórki, Słownik, Odmiana, Laboratorium wymowy."""
import random
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import (label, rich_text, scrolled, page_box, card, SpeakButton, slow_button, clear)
from .pron import SpeakPractice
from .. import fsrs
from ..answers import strip_accents
from ..conjugate import table as conj_table
from ..content import POS_NAMES


# ====================================================================== ALFABET
class AlphabetPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        alpha = app.course.alphabet
        nb = Gtk.Notebook()
        self.pack_start(nb, True, True, 0)

        # litery
        b = page_box()
        b.pack_start(label("Alfabet hiszpański (el abecedario)", "hero"), False, False, 0)
        b.pack_start(label("Kliknij ▶ przy literze, aby usłyszeć jej nazwę, i przy przykładach, aby usłyszeć słowa. "
                           "Prawy przycisk myszy — wolniej.", "dim"), False, False, 0)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(3)
        flow.set_min_children_per_line(1)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)
        flow.set_homogeneous(True)
        for row in alpha["letters"]:
            letter, name, how, ex = (row + ["", "", "", ""])[:4]
            c = card(spacing=4)
            h = Gtk.Box(spacing=6)
            h.pack_start(label(letter, "big-es", wrap=False), False, False, 0)
            h.pack_start(label(name, "dim", wrap=False), False, False, 0)
            h.pack_end(SpeakButton(app, name), False, False, 0)
            c.pack_start(h, False, False, 0)
            c.pack_start(label(how), False, False, 0)
            for e in [x.strip() for x in ex.split(";") if x.strip()]:
                word = e.split("=")[0].strip()
                r = Gtk.Box(spacing=4)
                r.pack_start(SpeakButton(app, word), False, False, 0)
                r.pack_start(label(e, wrap=True), True, True, 0)
                c.pack_start(r, False, False, 0)
            flow.add(c)
        b.pack_start(flow, False, False, 0)
        nb.append_page(scrolled(b), Gtk.Label(label="Litery"))

        # trudne dźwięki
        b2 = page_box()
        b2.pack_start(label("Trudne dźwięki dla Polaków", "hero"), False, False, 0)
        b2.pack_start(label("Wymowa z Hiszpanii (castellano). Ćwicz każdy dźwięk: posłuchaj → powtórz → nagraj się "
                            "w Laboratorium wymowy.", "dim"), False, False, 0)
        for row in alpha["sounds"]:
            snd, desc, ex = (row + ["", "", ""])[:3]
            c = card(spacing=6)
            c.pack_start(label(snd, "title2"), False, False, 0)
            c.pack_start(label(desc), False, False, 0)
            fl = Gtk.FlowBox()
            fl.set_selection_mode(Gtk.SelectionMode.NONE)
            fl.set_max_children_per_line(8)
            for w in [x.strip() for x in ex.split(";") if x.strip()]:
                for part in [p.strip() for p in w.split("/")]:
                    bb = Gtk.Button(label="▶ " + part)
                    bb.connect("clicked", lambda _b, t=part: app.say(t))
                    fl.add(bb)
            c.pack_start(fl, False, False, 0)
            pr = Gtk.Button(label="Ćwicz w laboratorium wymowy")
            pr.set_halign(Gtk.Align.START)
            words = [p.strip() for w in ex.split(";") for p in w.split("/") if p.strip()]
            pr.connect("clicked", lambda _b, ws=words: app.open_pron_lab(" ".join(ws[:4])))
            c.pack_start(pr, False, False, 0)
            b2.pack_start(c, False, False, 0)
        nb.append_page(scrolled(b2), Gtk.Label(label="Trudne dźwięki"))

        # akcent
        b3 = page_box()
        c3 = card()
        c3.pack_start(rich_text(alpha.get("stress", "")), False, False, 0)
        b3.pack_start(c3, False, False, 0)
        pairs = Gtk.FlowBox()
        pairs.set_selection_mode(Gtk.SelectionMode.NONE)
        for w in ["hablo", "habló", "papa", "papá", "término", "termino", "terminó", "ciudad", "café",
                  "médico", "árbol", "lunes", "español", "jamón"]:
            bb = Gtk.Button(label="▶ " + w)
            bb.connect("clicked", lambda _b, t=w: app.say(t))
            pairs.add(bb)
        b3.pack_start(label("Posłuchaj różnicy:", "title2"), False, False, 0)
        b3.pack_start(pairs, False, False, 0)
        nb.append_page(scrolled(b3), Gtk.Label(label="Akcent"))

        # klawiatura
        b4 = page_box()
        c4 = card()
        c4.pack_start(rich_text(alpha.get("keyboard", "")), False, False, 0)
        b4.pack_start(c4, False, False, 0)
        nb.append_page(scrolled(b4), Gtk.Label(label="Pisanie znaków"))


# ====================================================================== POWTÓRKI
class ReviewPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.queue = []
        self.done_count = 0

    def refresh(self):
        self.queue = self.app.db.due_cards(new_limit=self.app.db.get("new_per_day", 20))
        random.shuffle(self.queue)
        self.queue.sort(key=lambda c: c["state"] == 0)  # najpierw zaległe, potem nowe
        self.done_count = 0
        self._show()

    def _show(self):
        clear(self.inner)
        b = self.inner
        b.pack_start(label("Powtórki słówek", "hero"), False, False, 0)
        if not self.queue:
            due, new = self.app.db.count_due()
            c = card()
            if self.app.db.card_stats()["total"] == 0:
                c.pack_start(label("Nie masz jeszcze słówek do powtórek. Ukończ pierwszą lekcję albo dodaj słowa "
                                   "ze Słownika.", "title2"), False, False, 0)
            else:
                c.pack_start(label("¡Todo listo! Na dziś wszystko powtórzone. 🎉", "title2"), False, False, 0)
                c.pack_start(label(f"Powtórzone w tej sesji: {self.done_count}. Wróć jutro — algorytm FSRS "
                                   "pokaże słowa dokładnie wtedy, gdy zaczniesz je zapominać.", "dim"), False, False, 0)
            b.pack_start(c, False, False, 0)
            self.show_all()
            return
        card_ = self.queue[0]
        mode = self.app.db.get("review_dir", "mix")
        es_first = mode == "es" or (mode == "mix" and hash((card_["es"], card_["reps"])) % 2 == 0)
        b.pack_start(label(f"Zostało: {len(self.queue)}  ·  powtórzone: {self.done_count}"
                           + ("  ·  NOWE SŁOWO" if card_["state"] == 0 else ""), "dim"), False, False, 0)
        c = card(spacing=12)
        c.set_size_request(-1, 220)
        prompt = card_["es"] if es_first else card_["pl"]
        c.pack_start(label("Co to znaczy?" if es_first else "Jak to powiedzieć po hiszpańsku?", "dim", xalign=0.5),
                     False, False, 0)
        c.pack_start(label(prompt, "big-es", xalign=0.5), False, False, 0)
        if es_first:
            sb = SpeakButton(self.app, card_["es"])
            sb.set_halign(Gtk.Align.CENTER)
            c.pack_start(sb, False, False, 0)
            if self.app.db.get("autoplay", True):
                GLib.timeout_add(150, lambda: (self.app.say(card_["es"]), False)[1])
        self.answer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c.pack_start(self.answer_box, False, False, 0)
        b.pack_start(c, False, False, 0)
        self.btn_row = Gtk.Box(spacing=8, homogeneous=True)
        show = Gtk.Button(label="Pokaż odpowiedź  (Spacja)")
        show.get_style_context().add_class("suggested-action")
        show.connect("clicked", lambda *_: self._reveal(card_, es_first))
        self.btn_row.pack_start(show, True, True, 0)
        b.pack_start(self.btn_row, False, False, 0)
        b.pack_start(label("Skróty: Spacja — pokaż, 1–4 — ocena.", "dim"), False, False, 0)
        self.revealed = False
        self.current = (card_, es_first)
        self.show_all()
        show.grab_focus()

    def _reveal(self, card_, es_first):
        if self.revealed:
            return
        self.revealed = True
        ab = self.answer_box
        ab.pack_start(Gtk.Separator(), False, False, 0)
        ab.pack_start(label(card_["pl"] if es_first else card_["es"], "title2", xalign=0.5), False, False, 0)
        if not es_first:
            sb = SpeakButton(self.app, card_["es"])
            sb.set_halign(Gtk.Align.CENTER)
            ab.pack_start(sb, False, False, 0)
            self.app.say(card_["es"])
        entry = next((w for w in self.app.course.dictionary if w["es"] == card_["es"]), None)
        if entry and entry.get("ex_es"):
            r = Gtk.Box(spacing=4)
            r.set_halign(Gtk.Align.CENTER)
            r.pack_start(label(f"{entry['ex_es']} — {entry['ex_pl']}", "dim"), False, False, 0)
            r.pack_start(SpeakButton(self.app, entry["ex_es"]), False, False, 0)
            ab.pack_start(r, False, False, 0)
        clear(self.btn_row)
        iv = fsrs.preview_intervals(card_)
        for g, (txt, cls) in enumerate([("Nie pamiętam", "destructive-action"), ("Trudne", None),
                                        ("Dobrze", "suggested-action"), ("Łatwe", None)], start=1):
            bt = Gtk.Button(label=f"{g}. {txt}\n{iv[g - 1]}")
            bt.get_child().set_justify(Gtk.Justification.CENTER)
            if cls:
                bt.get_style_context().add_class(cls)
            bt.connect("clicked", lambda _b, gg=g: self._grade(gg))
            self.btn_row.pack_start(bt, True, True, 0)
        self.show_all()

    def _grade(self, g):
        card_, _ = self.current
        n = self.app.db.grade(card_, g)
        self.queue.pop(0)
        self.done_count += 1
        if n["due"] - time.time() < 20 * 60:  # wróci jeszcze w tej sesji
            n.update(es=card_["es"], pl=card_["pl"], pos=card_["pos"])
            self.queue.insert(min(len(self.queue), 4), n)
        self._show()
        self.app.refresh_today()

    def on_key(self, keyval):
        from gi.repository import Gdk
        if not self.queue:
            return False
        if keyval in (Gdk.KEY_space, Gdk.KEY_Return) and not self.revealed:
            self._reveal(*self.current)
            return True
        if self.revealed and Gdk.KEY_1 <= keyval <= Gdk.KEY_4:
            self._grade(keyval - Gdk.KEY_0)
            return True
        return False


# ====================================================================== SŁOWNIK
class DictionaryPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.app = app
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_margin_start(12)
        left.set_margin_top(12)
        left.set_margin_bottom(12)
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Szukaj po hiszpańsku lub po polsku…")
        self.search.connect("search-changed", lambda *_: self._fill())
        left.pack_start(self.search, False, False, 0)
        self.count = label("", "dim", wrap=False)
        left.pack_start(self.count, False, False, 0)
        self.list = Gtk.ListBox()
        self.list.connect("row-selected", self._selected)
        sw = scrolled(self.list)
        sw.set_size_request(320, -1)
        left.pack_start(sw, True, True, 0)
        self.pack_start(left, False, False, 0)
        self.detail = page_box()
        self.pack_start(scrolled(self.detail), True, True, 0)
        self._fill()

    def _fill(self):
        q = strip_accents(self.search.get_text().strip().lower())
        clear(self.list)
        n = 0
        for w in self.app.course.dictionary:
            if q and q not in strip_accents(w["es"].lower()) and q not in strip_accents(w["pl"].lower()):
                continue
            n += 1
            if n > 400:
                continue
            row = Gtk.ListBoxRow()
            hb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            hb.set_margin_top(4)
            hb.set_margin_bottom(4)
            hb.set_margin_start(6)
            hb.pack_start(label(w["es"], wrap=False), False, False, 0)
            sub = label(w["pl"], "dim", wrap=False)
            sub.set_ellipsize(3)
            hb.pack_start(sub, False, False, 0)
            row.add(hb)
            row.word = w
            self.list.add(row)
        self.count.set_text(f"{n} haseł" + (" (pokazano 400)" if n > 400 else ""))
        self.list.show_all()

    def _selected(self, _lb, row):
        if row is None:
            return
        w = row.word
        d = self.detail
        clear(d)
        h = Gtk.Box(spacing=8)
        h.pack_start(label(w["es"], "hero"), False, False, 0)
        h.pack_start(SpeakButton(self.app, w["es"]), False, False, 0)
        h.pack_start(slow_button(self.app, w["es"]), False, False, 0)
        d.pack_start(h, False, False, 0)
        meta = POS_NAMES.get(w.get("pos", ""), w.get("pos", ""))
        src = w.get("lesson")
        meta += f"  ·  {w.get('level', '')}" + (f"  ·  lekcja {src}" if src else
                                                (f"  ·  {w.get('topic')}" if w.get("topic") else ""))
        d.pack_start(label(meta, "dim"), False, False, 0)
        d.pack_start(label(w["pl"], "title2"), False, False, 0)
        if w.get("ex_es"):
            r = Gtk.Box(spacing=6)
            r.pack_start(label(f"{w['ex_es']}\n{w['ex_pl']}"), False, False, 0)
            r.pack_start(SpeakButton(self.app, w["ex_es"]), False, False, 0)
            d.pack_start(card(r), False, False, 0)
        add = Gtk.Button(label="✔ W powtórkach" if self.app.db.has_card(w["es"]) else "+ Dodaj do powtórek")
        add.set_sensitive(not self.app.db.has_card(w["es"]))
        add.set_halign(Gtk.Align.START)

        def _add(btn):
            self.app.db.add_card(w)
            btn.set_label("✔ W powtórkach")
            btn.set_sensitive(False)
            self.app.refresh_today()
        add.connect("clicked", _add)
        d.pack_start(add, False, False, 0)
        if w.get("pos") in ("v", "vr"):
            verb = w["es"].split("/")[0].split()[0].strip()
            cb = Gtk.Button(label=f"Pokaż odmianę: {verb}")
            cb.set_halign(Gtk.Align.START)
            cb.connect("clicked", lambda *_: self.app.open_conjugation(verb))
            d.pack_start(cb, False, False, 0)
        d.show_all()


# ====================================================================== ODMIANA
class ConjugationPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        top = Gtk.Box(spacing=8)
        for side in ("start", "end", "top"):
            getattr(top, f"set_margin_{side}")(16)
        top.pack_start(label("Odmiana czasowników", "hero", wrap=False), False, False, 0)
        self.entry = Gtk.SearchEntry()
        self.entry.set_placeholder_text("np. hablar, tener, levantarse")
        self.entry.connect("activate", lambda *_: self.show_verb(self.entry.get_text()))
        top.pack_end(self.entry, False, False, 0)
        verbs = sorted({w["es"].split("/")[0].split()[0] for w in app.course.dictionary
                        if w.get("pos") in ("v", "vr") and w["es"].split()[0].endswith(("r", "rse", "ír"))})
        combo = Gtk.ComboBoxText()
        combo.append_text("— czasowniki z kursu —")
        for v in verbs:
            combo.append_text(v)
        combo.set_active(0)
        combo.connect("changed", lambda c: c.get_active() > 0 and self.show_verb(c.get_active_text()))
        top.pack_end(combo, False, False, 0)
        self.pack_start(top, False, False, 0)
        self.body = page_box()
        self.pack_start(scrolled(self.body), True, True, 0)
        self.show_verb("hablar")

    def show_verb(self, verb):
        verb = verb.strip().lower()
        if not verb.endswith(("ar", "er", "ir", "ír", "arse", "erse", "irse", "írse")):
            return
        clear(self.body)
        self.entry.set_text(verb)
        tables, part, ger = conj_table(verb)
        w = next((x for x in self.app.course.dictionary if x["es"].split("/")[0].split()[0] == verb), None)
        h = Gtk.Box(spacing=8)
        h.pack_start(label(verb, "hero", wrap=False), False, False, 0)
        h.pack_start(SpeakButton(self.app, verb), False, False, 0)
        if w:
            h.pack_start(label("— " + w["pl"], "title2"), False, False, 0)
        self.body.pack_start(h, False, False, 0)
        self.body.pack_start(label(f"Imiesłów (participio): {part}    ·    Gerundio: {ger}", "dim"), False, False, 0)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(3)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)
        flow.set_homogeneous(True)
        for name, rows in tables:
            c = card(spacing=4)
            c.pack_start(label(name, "title2"), False, False, 0)
            g = Gtk.Grid(column_spacing=12, row_spacing=3)
            for i, (person, form) in enumerate(rows):
                g.attach(label(person, "dim", wrap=False), 0, i, 1, 1)
                g.attach(label(form, wrap=False, selectable=True), 1, i, 1, 1)
                sb = SpeakButton(self.app, form.replace(" / hay", ""))
                g.attach(sb, 2, i, 1, 1)
            c.pack_start(g, False, False, 0)
            flow.add(c)
        self.body.pack_start(flow, False, False, 0)
        self.body.pack_start(label("Formy generowane automatycznie według reguł i listy czasowników nieregularnych "
                                   "(odmiana z Hiszpanii, z vosotros). Imperativo pokazuje formy twierdzące.", "dim"),
                             False, False, 0)
        self.body.show_all()


# ====================================================================== LABORATORIUM WYMOWY
class PronLabPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        b = page_box()
        b.pack_start(label("Laboratorium wymowy", "hero"), False, False, 0)
        b.pack_start(label("Wybierz źródło zdań albo wpisz własne. Aplikacja porównuje to, co powiedziałeś, z wzorem — "
                           "słowo po słowie — i podpowiada, nad czym pracować.", "dim"), False, False, 0)
        row = Gtk.Box(spacing=8)
        self.src = Gtk.ComboBoxText()
        self.src.append("done", "Zdania z ukończonych lekcji")
        self.src.append("all", "Zdania z całego kursu")
        self.src.append("words", "Słowa ze słownika")
        self.src.append("hard", "Trudne dźwięki (rr, j, z, ll, ñ)")
        self.src.set_active_id("done")
        row.pack_start(self.src, False, False, 0)
        nxt = Gtk.Button(label="Losuj  ⟳")
        nxt.get_style_context().add_class("suggested-action")
        nxt.connect("clicked", lambda *_: self.random_item())
        row.pack_start(nxt, False, False, 0)
        self.own = Gtk.Entry()
        self.own.set_placeholder_text("…albo wpisz własne zdanie po hiszpańsku i naciśnij Enter")
        self.own.connect("activate", lambda e: e.get_text().strip() and self.set_target(e.get_text().strip(), ""))
        row.pack_start(self.own, True, True, 0)
        b.pack_start(row, False, False, 0)
        self.holder = card()
        b.pack_start(self.holder, False, False, 0)
        self.stats = label("", "dim")
        b.pack_start(self.stats, False, False, 0)
        self.pack_start(scrolled(b), True, True, 0)
        self.random_item()

    HARD = ["perro", "carro", "rojo", "tierra", "jamón", "ajo", "mujer", "gente", "zapato", "cerveza",
            "gracias", "diez", "llave", "calle", "niño", "España", "mañana", "guitarra", "queso",
            "El perro de Roberto corre rápido.", "Me gusta el jamón de Jabugo.", "Cinco cervezas, por favor.",
            "Mañana voy a la montaña con mi niña.", "La lluvia en Sevilla es una maravilla."]

    def random_item(self):
        s = self.src.get_active_id()
        c = self.app.course
        done = set(self.app.db.done_lessons())
        pool = []
        if s in ("done", "all"):
            for l in c.lessons:
                if s == "all" or l.id in done:
                    pool += [(es, pl) for _, es, pl in l.dialog if 2 <= len(es.split()) <= 14]
            if not pool:
                pool = [(es, pl) for _, es, pl in c.lessons[0].dialog]
        elif s == "words":
            pool = [(w["es"].split("/")[0].strip(), w["pl"]) for w in c.dictionary]
        else:
            pool = [(w, "") for w in self.HARD]
        es, pl = random.choice(pool)
        self.set_target(es, pl)

    def set_target(self, es, pl):
        clear(self.holder)
        self.holder.pack_start(SpeakPractice(self.app, es, pl, on_scored=lambda s: self._stats()), False, False, 0)
        self.holder.show_all()
        self._stats()

    def _stats(self):
        n, avg, recent = self.app.db.pron_stats()
        if n:
            self.stats.set_text(f"Twoje próby: {n} · średnio {round(avg)}% · ostatnie 30: {round(recent)}%")
