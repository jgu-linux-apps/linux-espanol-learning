"""Dyktando: Paco czyta zdanie, uczeń je wpisuje; porównanie słowo po słowie."""
import difflib
import random
from xml.sax.saxutils import escape

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import label, scrolled, page_box, card, clear, AccentBar
from ..answers import norm
from ..i18n import _  # noqa: E402

ROUND = 8
GOOD, ACC, BAD = "#2E9E5B", "#D98E04", "#D64545"


def sentence_pool(course, done_ids):
    """Zdania z ukończonych lekcji (a gdy nic nie ukończono — z pierwszych trzech)."""
    lessons = [l for l in course.lessons if l.id in done_ids] or list(course.lessons[:3])
    pool, seen = [], set()
    for l in lessons:
        items = [(es, pl) for _w, es, pl in l.dialog if es] + \
                [(v["ex_es"], v["ex_pl"]) for v in l.vocab if v.get("ex_es")]
        for es, pl in items:
            n = len(es.split())
            if 2 <= n <= 12 and es not in seen:
                seen.add(es)
                pool.append((es, pl))
    return pool


def compare(target, given):
    """Zwraca (markup, wynik 0–100, [(słowo, status)]); status: ok / accent / bad / missing / extra."""
    tw = [w.strip("¿?¡!.,;:…") or w for w in target.split()]
    gw = given.split()
    tn = [norm(w) for w in tw]
    gn = [norm(w) for w in gw]
    tl = [norm(w, False) for w in tw]
    gl = [norm(w, False) for w in gw]
    sm = difflib.SequenceMatcher(None, tl, gl, autojunk=False)
    parts, pts, res = [], 0.0, []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                if tn[i1 + k] == gn[j1 + k]:
                    parts.append(f'<span foreground="{GOOD}">{escape(gw[j1 + k])}</span>')
                    pts += 1
                    res.append((tw[i1 + k], "ok"))
                else:
                    parts.append(f'<span foreground="{ACC}" underline="single">{escape(gw[j1 + k])}</span>'
                                 f' <small>({escape(tw[i1 + k])})</small>')
                    pts += 0.7
                    res.append((tw[i1 + k], "accent"))
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                t = tw[i1 + k] if i1 + k < i2 else None
                g = gw[j1 + k] if j1 + k < j2 else None
                if t and g:
                    parts.append(f'<span foreground="{BAD}"><s>{escape(g)}</s></span> '
                                 f'<span foreground="{GOOD}">{escape(t)}</span>')
                    res.append((t, "bad"))
                elif t:
                    parts.append(f'<span foreground="{BAD}">[{escape(t)}]</span>')
                    res.append((t, "missing"))
                else:
                    parts.append(f'<span foreground="{BAD}"><s>{escape(g)}</s></span>')
                    res.append((g, "extra"))
    score = round(100 * pts / max(1, len(tw)))
    return " ".join(parts), min(100, score), res


class DictationPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.inner = page_box()
        self.pack_start(scrolled(self.inner), True, True, 0)
        self.queue, self.idx, self.scores, self.misses, self.cur, self.checked = [], 0, [], [], None, False
        self.show_start()

    def refresh(self):
        pass

    # ----------------------------------------------------------- start
    def show_start(self):
        clear(self.inner)
        b = self.inner
        b.pack_start(label(_("Dyktando"), "hero"), False, False, 0)
        c = card(spacing=8)
        c.pack_start(label(_('Paco czyta zdanie po hiszpańsku, a Ty je wpisujesz. Dostaniesz kolorowe porównanie słowo po słowie: zielone — dobrze, żółte — brak akcentu, czerwone — błąd. Jedna runda to {} zdań z ukończonych lekcji.').format(ROUND), None), False, False, 0)
        pool = sentence_pool(self.app.course, set(self.app.db.done_lessons()))
        done = self.app.db.done_lessons()
        c.pack_start(label(_('Dostępnych zdań: {}').format(len(pool)) + ("" if done else _("  (jeszcze nic nie ukończono — "
                     "użyję zdań z pierwszych lekcji)")), "dim"), False, False, 0)
        if not self.app.speech.tts_available():
            c.pack_start(label(_("Do dyktanda potrzebny jest głos — zainstaluj silnik mowy na ekranie „Dzisiaj”."),
                               "warn-text"), False, False, 0)
        btn = Gtk.Button(label=_("▶  Zacznij rundę"))
        btn.get_style_context().add_class("suggested-action")
        btn.set_halign(Gtk.Align.START)
        btn.set_sensitive(len(pool) >= 2)
        btn.connect("clicked", lambda *_a: self.start_round(pool))
        c.pack_start(btn, False, False, 0)
        b.pack_start(c, False, False, 0)
        self.show_all()

    def start_round(self, pool):
        self.queue = random.sample(pool, min(ROUND, len(pool)))
        self.idx, self.scores, self.misses = 0, [], []
        self.show_item()

    # ----------------------------------------------------------- zdanie
    def show_item(self):
        clear(self.inner)
        b = self.inner
        self.checked = False
        self.cur = self.queue[self.idx]
        b.pack_start(label(_('Dyktando · zdanie {} z {}').format(self.idx + 1, len(self.queue)), "hero"), False, False, 0)
        c = card(spacing=10)
        row = Gtk.Box(spacing=8)
        for text, slow in ((_("▶  Posłuchaj"), False), (_("🐢  Wolno"), True)):
            bt = Gtk.Button(label=text)
            bt.connect("clicked", lambda _b, s=slow: self.app.say(self.cur[0], slow=s))
            row.pack_start(bt, False, False, 0)
        hint = Gtk.Button(label=_("💡  Podpowiedź"))
        hint.connect("clicked", self.on_hint)
        row.pack_start(hint, False, False, 0)
        c.pack_start(row, False, False, 0)
        self.hint_lb = label("", "dim")
        c.pack_start(self.hint_lb, False, False, 0)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(_("Wpisz to, co słyszysz…"))
        self.entry.connect("activate", lambda *_a: self.on_check() if not self.checked else self.next())
        c.pack_start(self.entry, False, False, 0)
        c.pack_start(AccentBar(self.entry), False, False, 0)
        self.btn = Gtk.Button(label=_("Sprawdź"))
        self.btn.get_style_context().add_class("suggested-action")
        self.btn.set_halign(Gtk.Align.START)
        self.btn.connect("clicked", lambda *_a: self.on_check() if not self.checked else self.next())
        c.pack_start(self.btn, False, False, 0)
        self.result = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        c.pack_start(self.result, False, False, 0)
        b.pack_start(c, False, False, 0)
        self.show_all()
        self.entry.grab_focus()
        GLib.timeout_add(250, lambda: (self.app.say(self.cur[0]), False)[1])

    def on_hint(self, *_a):
        words = self.cur[0].split()
        self.hint_lb.set_text(_('{} słów: ').format(len(words)) + " ".join(w[0] + "…" for w in words))

    def on_check(self):
        given = self.entry.get_text().strip()
        if not given:
            return
        self.checked = True
        markup, score, _res = compare(self.cur[0], given)
        self.scores.append(score)
        if score < 100:
            self.misses.append(self.cur)
        self.app.db.log_activity(items=1)
        clear(self.result)
        head = (_("✔ Idealnie!") if score == 100 else _('Wynik: {}%').format(score))
        self.result.pack_start(label(head, "title2", wrap=False), False, False, 0)
        lb = label(markup, markup=True, selectable=True)
        self.result.pack_start(lb, False, False, 0)
        if score < 100:
            self.result.pack_start(label("Poprawnie: " + self.cur[0], "mid-es", selectable=True), False, False, 0)
        self.result.pack_start(label(self.cur[1], "dim"), False, False, 0)
        self.btn.set_label(_("Dalej") if self.idx + 1 < len(self.queue) else _("Zakończ rundę"))
        self.entry.set_sensitive(False)
        self.result.show_all()

    def next(self):
        self.idx += 1
        if self.idx < len(self.queue):
            self.show_item()
        else:
            self.show_summary()

    # ----------------------------------------------------------- podsumowanie
    def show_summary(self):
        clear(self.inner)
        b = self.inner
        avg = round(sum(self.scores) / max(1, len(self.scores)))
        b.pack_start(label(_("Koniec rundy"), "hero"), False, False, 0)
        c = card(spacing=8)
        c.pack_start(label(f"{avg}%", "stat-num", wrap=False), False, False, 0)
        verdict = (_("Doskonale!") if avg >= 90 else _("Bardzo dobrze.") if avg >= 75 else
                   _("Nieźle — ćwicz dalej.") if avg >= 50 else _("Posłuchaj jeszcze raz wolniej i spróbuj ponownie."))
        c.pack_start(label(verdict, "dim"), False, False, 0)
        if self.misses:
            c.pack_start(label(_("Do powtórki:"), "title2", wrap=False), False, False, 0)
            for es, pl in self.misses:
                r = Gtk.Box(spacing=8)
                r.pack_start(label(f"{es} — {pl}", None), True, True, 0)
                sb = Gtk.Button(label="🔊")
                sb.connect("clicked", lambda _b, t=es: self.app.say(t))
                r.pack_start(sb, False, False, 0)
                c.pack_start(r, False, False, 0)
        row = Gtk.Box(spacing=8)
        again = Gtk.Button(label=_("▶  Kolejna runda"))
        again.get_style_context().add_class("suggested-action")
        again.connect("clicked", lambda *_a: self.start_round(sentence_pool(self.app.course,
                                                                           set(self.app.db.done_lessons()))))
        row.pack_start(again, False, False, 0)
        back = Gtk.Button(label=_("Wróć"))
        back.connect("clicked", lambda *_a: self.show_start())
        row.pack_start(back, False, False, 0)
        c.pack_start(row, False, False, 0)
        b.pack_start(c, False, False, 0)
        self.show_all()
