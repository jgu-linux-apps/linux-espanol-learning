"""Wspólne elementy interfejsu."""
import html
import re
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango  # noqa: E402

CSS = b"""
.hero-banner { padding: 16px; border-radius: 10px; background-color: alpha(@theme_selected_bg_color, 0.14); }
.card { background-color: @theme_base_color; border: 1px solid alpha(@borders, 0.8);
        border-radius: 10px; padding: 14px; }
.hero { font-size: 22px; font-weight: bold; }
.title2 { font-size: 17px; font-weight: bold; }
.dim { opacity: 0.7; }
.big-es { font-size: 26px; font-weight: bold; }
.mid-es { font-size: 18px; }
.ok-text { color: #2e9e44; font-weight: bold; }
.bad-text { color: #d0353f; font-weight: bold; }
.warn-text { color: #c77c00; font-weight: bold; }
.word-ok { color: #2e9e44; }
.word-bad { color: #d0353f; text-decoration: underline; }
.accent-btn { min-width: 30px; padding: 2px 6px; }
.stat-num { font-size: 28px; font-weight: bold; }
.sidebar-row { padding: 8px 12px; }
.lesson-done { color: #2e9e44; }
.choice-btn { padding: 10px; }
.tile { padding: 4px 10px; }
.levelbar-mic block.filled { background-color: #2e9e44; }
.badge { background-color: alpha(@theme_selected_bg_color, 0.18); border-radius: 8px; padding: 1px 8px; }

button.mic-btn { border-radius: 999px; padding: 12px 30px; min-height: 30px; font-size: 115%; font-weight: bold;
  background-image: linear-gradient(to bottom, #35b6e8, #1a8fc7); color: white; border: none;
  box-shadow: 0 3px 8px rgba(0,0,0,0.30); }
button.mic-btn:hover { background-image: linear-gradient(to bottom, #52c6f2, #269ed8); }
button.mic-btn:active { box-shadow: 0 1px 3px rgba(0,0,0,0.35); }
button.mic-btn:disabled { background-image: none; background-color: alpha(currentColor, 0.15); color: alpha(currentColor, 0.5); box-shadow: none; }
button.mic-btn.rec { background-image: linear-gradient(to bottom, #f0605a, #d0342c); }
"""


def label(text, cls=None, wrap=True, xalign=0.0, markup=False, selectable=False):
    lb = Gtk.Label()
    if markup:
        lb.set_markup(text)
    else:
        lb.set_text(text)
    lb.set_xalign(xalign)
    if wrap:
        lb.set_line_wrap(True)
        lb.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    if selectable:
        lb.set_selectable(True)
    for c in (cls.split() if cls else []):
        lb.get_style_context().add_class(c)
    return lb


def md_inline(text):
    """**pogrubienie** i *kursywa* -> Pango."""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)
    return t


def rich_text(text, speak=None):
    """Prosty markdown: ## nagłówek, - punkt, || tabela. Zwraca Gtk.Box."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    table_rows = []

    def flush_table():
        if not table_rows:
            return
        grid = Gtk.Grid(column_spacing=18, row_spacing=4)
        grid.set_margin_start(8)
        for r, cells in enumerate(table_rows):
            for c, cell in enumerate(cells):
                lb = label(md_inline(cell), markup=True, wrap=True)
                if c == 0 and len(cells) > 1:
                    lb.get_style_context().add_class("dim")
                grid.attach(lb, c, r, 1, 1)
        box.pack_start(grid, False, False, 2)
        table_rows.clear()

    for line in text.splitlines():
        s = line.strip()
        if s.startswith("||"):
            table_rows.append([c.strip() for c in s[2:].split("|")])
            continue
        flush_table()
        if not s:
            continue
        if s.startswith("## "):
            lb = label(md_inline(s[3:]), "title2", markup=True)
            lb.set_margin_top(8)
            box.pack_start(lb, False, False, 0)
        elif s.startswith("- "):
            lb = label("•  " + md_inline(s[2:]), markup=True)
            lb.set_margin_start(10)
            box.pack_start(lb, False, False, 0)
        else:
            box.pack_start(label(md_inline(s), markup=True), False, False, 0)
    flush_table()
    return box


def scrolled(child, hpolicy=Gtk.PolicyType.NEVER):
    sw = Gtk.ScrolledWindow()
    sw.set_policy(hpolicy, Gtk.PolicyType.AUTOMATIC)
    sw.add(child)
    return sw


def page_box(margin=24, spacing=14):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
    for side in ("start", "end", "top", "bottom"):
        getattr(b, f"set_margin_{side}")(margin)
    return b


def card(child=None, spacing=8):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
    b.get_style_context().add_class("card")
    if child:
        b.pack_start(child, False, False, 0)
    return b


def run_bg(fn, done, error=None):
    """Uruchom fn() w wątku, done(wynik) / error(wyjątek) w wątku GUI."""
    def work():
        try:
            res = fn()
        except Exception as e:  # noqa
            if error:
                GLib.idle_add(error, e)
            else:
                print("Błąd:", e)
            return
        GLib.idle_add(done, res)
    threading.Thread(target=work, daemon=True).start()


class AccentBar(Gtk.Box):
    """Przyciski á é í ó ú ü ñ ¿ ¡ wstawiające znak do pola tekstowego."""
    CHARS = ["á", "é", "í", "ó", "ú", "ü", "ñ", "¿", "¡"]

    def __init__(self, entry):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.entry = entry
        for ch in self.CHARS:
            b = Gtk.Button(label=ch)
            b.set_can_focus(False)
            b.get_style_context().add_class("accent-btn")
            b.connect("clicked", self._ins, ch)
            self.pack_start(b, False, False, 0)

    def _ins(self, _b, ch):
        e = self.entry
        pos = e.get_position()
        bounds = e.get_selection_bounds()
        if bounds:
            e.delete_text(bounds[0], bounds[1])
            pos = bounds[0]
        e.insert_text(ch, pos)
        e.set_position(pos + len(ch))
        e.grab_focus_without_selecting()


class SpeakButton(Gtk.Button):
    """▶ odtwarza tekst syntezą mowy. Prawy klik / Shift — wolniej."""

    def __init__(self, app, text, slow=False, tooltip=None, icon="audio-speakers-symbolic"):
        super().__init__()
        self.app, self.text, self.slow = app, text, slow
        self.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_valign(Gtk.Align.CENTER)
        self.set_tooltip_text(tooltip or ("Posłuchaj wolno" if slow else "Posłuchaj (prawy przycisk — wolniej)"))
        self.connect("clicked", lambda *_: self.app.say(self.text, self.slow))
        self.connect("button-press-event", self._press)

    def _press(self, _w, ev):
        if ev.button == 3:
            self.app.say(self.text, True)
            return True
        return False


def slow_button(app, text):
    return SpeakButton(app, text, slow=True, icon="media-seek-backward-symbolic")


def clear(box):
    for ch in box.get_children():
        box.remove(ch)
        ch.destroy()
