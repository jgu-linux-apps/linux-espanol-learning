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


# ====================================================================== nowy wygląd (1.13)
# Style nowych elementów idą osobnym dostawcą NAD motywem (motyw czyści tła zwykłych kontenerów: box, label).
CSS2 = b"""
.nav-head { background: none; border: none; box-shadow: none; padding: 10px 10px 3px 14px; min-height: 0; }
.nav-head label { font-size: 11px; font-weight: bold; letter-spacing: 1px; opacity: 0.55; }
.nav-head:hover label { opacity: 0.85; }
.nav-count { font-size: 11px; font-weight: bold; padding: 0 7px; border-radius: 99px;
  background-color: @theme_selected_bg_color; color: @theme_selected_fg_color; }
.kicker { font-size: 12px; font-weight: bold; letter-spacing: 1px; opacity: 0.65; }
.hero-title { font-size: 26px; font-weight: bold; }
.hello { font-size: 25px; font-weight: bold; }
.stat-big { font-size: 26px; font-weight: 800; }
.dot { min-width: 24px; min-height: 24px; border-radius: 99px; font-size: 12px; font-weight: bold; }
.dot-done { background-color: #16A34A; color: #FFFFFF; }
.dot-cur { background-color: @theme_selected_bg_color; color: @theme_selected_fg_color; }
.dot-todo { border: 2px solid alpha(currentColor, 0.18); opacity: 0.75; }
.week { min-width: 30px; min-height: 30px; border-radius: 99px; font-size: 13px; }
.week-on { background-color: #F43F5E; color: #FFFFFF; }
.week-today { border: 2px dashed #F43F5E; color: #F43F5E; }
.week-off { border: 2px solid alpha(currentColor, 0.15); }
.week-day { font-size: 11px; opacity: 0.6; }
.plan-row { padding: 9px 0; border-top: 1px solid alpha(currentColor, 0.10); }
.part { font-size: 12px; font-weight: bold; padding: 3px 10px; border-radius: 99px; border: 1px solid alpha(currentColor, 0.15); }
.part-done { background-color: #16A34A; color: #FFFFFF; border-color: #16A34A; }
.part-cur { background-color: @theme_selected_bg_color; color: @theme_selected_fg_color; border-color: @theme_selected_bg_color; }
.cur-lesson { background-color: alpha(@theme_selected_bg_color, 0.10); border: 2px solid alpha(@theme_selected_bg_color, 0.45);
  border-radius: 14px; padding: 12px 14px; }
.stars { color: #F59E0B; letter-spacing: 1px; }
.stars-off { opacity: 0.25; letter-spacing: 1px; }
.score { color: #16A34A; font-weight: bold; }
.lvl-switch { background-color: alpha(@theme_selected_bg_color, 0.10); border-radius: 12px; padding: 4px; }
.notice { padding: 10px 16px; }
.seg { min-height: 10px; border-radius: 5px; background-color: alpha(currentColor, 0.12); }
.seg-done { background-color: @theme_selected_bg_color; }
.seg-cur { background-color: alpha(@theme_selected_bg_color, 0.45); }
.ex-prompt { font-size: 28px; font-weight: bold; }
.ex-kind { font-size: 12px; font-weight: bold; letter-spacing: 1px; opacity: 0.65; }
.choice-card { padding: 14px 16px; border-radius: 14px; font-size: 16px; }
.choice-key { min-width: 26px; min-height: 26px; border-radius: 8px; border: 2px solid alpha(currentColor, 0.2);
  font-size: 13px; font-weight: bold; }
.choice-card.ok { border: 2px solid #16A34A; background-color: alpha(#16A34A, 0.12); }
.choice-card.bad { border: 2px solid #DC2626; background-color: alpha(#DC2626, 0.10); }
.fb-bar { padding: 14px 18px; border-radius: 14px; }
.fb-ok { background-color: alpha(#16A34A, 0.12); border: 2px solid #16A34A; }
.fb-warn { background-color: alpha(#D97706, 0.12); border: 2px solid #D97706; }
.fb-bad { background-color: alpha(#DC2626, 0.10); border: 2px solid #DC2626; }
.fb-icon { min-width: 40px; min-height: 40px; border-radius: 99px; font-size: 20px; font-weight: bold; color: #FFFFFF; }
.fb-ok .fb-icon { background-color: #16A34A; } .fb-warn .fb-icon { background-color: #D97706; }
.fb-bad .fb-icon { background-color: #DC2626; }
.ex-help { font-size: 12px; opacity: 0.6; }
"""


def ring_colors(widget, app=None):
    """Kolory kółek postępu z palety motywu (dla motywu systemowego: kolor zaznaczenia GTK)."""
    p = getattr(app, "palette", None) or {}
    ctx = widget.get_style_context()
    ok, acc = ctx.lookup_color("theme_selected_bg_color")
    fg = ctx.get_color(Gtk.StateFlags.NORMAL)
    a = p.get("accent")
    return {"accent": a or (acc.to_string() if ok else "#3584e4"), "ring2": p.get("ring2", "#F43F5E"),
            "ring3": p.get("ring3") or p.get("accent2") or "#0EA5E9", "fg": fg}


class Ring(Gtk.DrawingArea):
    """Kółko postępu: łuk od góry zgodnie z ruchem wskazówek, w środku liczba i podpis."""

    def __init__(self, app, frac, big, small="", color="accent", size=84, width=8):
        super().__init__()
        self.app, self.frac, self.big, self.small = app, max(0.0, min(1.0, frac)), str(big), small
        self.color, self.size, self.width = color, size, width
        self.set_size_request(size, size)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.connect("draw", self._draw)

    def _draw(self, w, cr):
        import math
        gi.require_version("PangoCairo", "1.0")
        from gi.repository import Gdk, PangoCairo
        c = ring_colors(w, self.app)
        s, lw = self.size, self.width
        cx = cy = s / 2
        r = s / 2 - lw / 2 - 1
        fg = c["fg"]
        cr.set_line_width(lw)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.12)
        cr.arc(cx, cy, r, 0, 2 * math.pi)
        cr.stroke()
        if self.frac > 0:
            col = Gdk.RGBA()
            col.parse(c.get(self.color, self.color))
            cr.set_source_rgba(col.red, col.green, col.blue, 1)
            cr.set_line_cap(1)  # ROUND
            cr.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * self.frac)
            cr.stroke()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 1)
        lay = PangoCairo.create_layout(cr)
        lay.set_font_description(w.get_style_context().get_font(Gtk.StateFlags.NORMAL))  # czcionka motywu
        big = max(11, int(s * 0.24))
        small = max(8, int(s * 0.13))
        txt = f"<b><span size='{big * 1024}'>{html.escape(self.big)}</span></b>"
        if self.small:
            txt += f"\n<span size='{small * 1024}' alpha='65%'>{html.escape(self.small)}</span>"
        lay.set_markup(txt, -1)
        lay.set_alignment(Pango.Alignment.CENTER)
        tw, th = lay.get_pixel_size()
        cr.move_to(cx - tw / 2, cy - th / 2)
        PangoCairo.show_layout(cr, lay)
        return False


def dot(text, state):
    """Kółko stanu lekcji/punktu planu: done (✓), cur, todo."""
    lb = Gtk.Label(label="✓" if state == "done" else text)
    lb.get_style_context().add_class("dot")
    lb.get_style_context().add_class("dot-" + state)
    lb.set_valign(Gtk.Align.CENTER)
    return lb


def stars_for(score):
    """Gwiazdki za wynik lekcji: ≥90% ★★★, ≥75% ★★, inaczej ★."""
    return 3 if score >= 90 else 2 if score >= 75 else 1
