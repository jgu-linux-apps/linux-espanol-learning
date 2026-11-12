"""Paco — animowany robocik-rozmówca (rysowany w Cairo, bez zewnętrznych plików).
Stany: idle, listening, thinking, speaking; reakcje: happy, worried."""
import array
import math
import random
import time
import wave

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

try:
    gi.require_foreign("cairo")
except Exception:  # noqa
    pass

TAU = math.tau


def _lerp(a, b, k):
    return a + (b - a) * k


def load_envelope(path, step=0.05):
    """Obwiednia głośności WAV (wartości 0..1 co `step` s) do poruszania ustami."""
    try:
        with wave.open(path, "rb") as w:
            ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            raw = w.readframes(n)
        if width != 2:
            return []
        a = array.array("h")
        a.frombytes(raw)
        if ch > 1:
            a = a[::ch]
        size = max(1, int(rate * step))
        env = []
        for i in range(0, len(a), size):
            chunk = a[i:i + size]
            if chunk:
                env.append(math.sqrt(sum(x * x for x in chunk) / len(chunk)))
        if not env:
            return []
        top = sorted(env)[int(len(env) * 0.9)] or max(env) or 1
        return [min(1.0, e / top) for e in env]
    except Exception:  # noqa
        return []


class Paco(Gtk.DrawingArea):
    DRAW = True

    def __init__(self, size=110):
        super().__init__()
        self.set_size_request(size, int(size * 1.18))
        self.state = "idle"
        self.react_kind = None
        self.react_until = 0.0
        self.level = 0.0            # poziom mikrofonu 0..1
        self.env, self.env_t0, self.env_step = [], 0.0, 0.05
        # bieżące (wygładzone) parametry
        self.p = dict(tilt=0.0, mouth=0.0, smile=0.0, pdx=0.0, pdy=0.0, brow_l=0.0, brow_r=0.0,
                      happy=0.0, wave=0.0, dots=0.0)
        self.blink = 0.0
        self.next_blink = time.monotonic() + 2.5
        self.t0 = time.monotonic()
        self.tick_id = GLib.timeout_add(40, self._tick)
        if self.DRAW:
            self.connect("draw", lambda w, cr: (self.paint(cr, w.get_allocated_width(), w.get_allocated_height()), False)[1])
        self.connect("destroy", lambda *_: self.tick_id and GLib.source_remove(self.tick_id))

    # ------------------------------------------------------------ sterowanie
    def set_state(self, st):
        self.state = st

    def set_level(self, v):
        self.level = v

    def talk(self, wav_path):
        self.env = load_envelope(wav_path, self.env_step)
        self.env_t0 = time.monotonic()

    def react(self, kind, seconds=2.2):
        self.react_kind = kind
        self.react_until = time.monotonic() + seconds

    # ------------------------------------------------------------ animacja
    def _targets(self, now):
        st = self.state
        react = self.react_kind if now < self.react_until else None
        t = dict(tilt=0.0, mouth=0.0, smile=0.0, pdx=0.0, pdy=0.0, brow_l=0.0, brow_r=0.0,
                 happy=0.0, wave=0.0, dots=0.0)
        if st == "listening":
            t.update(tilt=-9.0, pdx=0.5, pdy=-0.4, brow_l=-4.0, brow_r=0.0, wave=0.25 + 0.75 * self.level)
        elif st == "thinking":
            t.update(pdx=0.8, pdy=-0.9, brow_l=2.0, brow_r=-3.0, dots=1.0, tilt=3.0)
        elif st == "speaking":
            i = int((now - self.env_t0) / self.env_step)
            m = self.env[i] if 0 <= i < len(self.env) else 0.0
            t.update(mouth=m, smile=0.15)
        if react == "happy":
            t.update(happy=1.0, smile=1.0, mouth=max(t["mouth"], 0.35), dots=0.0, wave=0.0, tilt=0.0)
        elif react == "worried":
            t.update(brow_l=-3.0, brow_r=-3.0, smile=-0.6, pdy=0.3, tilt=-4.0)
        return t

    def _tick(self):
        if not self.get_mapped():
            return True
        now = time.monotonic()
        tgt = self._targets(now)
        fast = {"mouth": 0.6}
        for k, v in tgt.items():
            self.p[k] = _lerp(self.p[k], v, fast.get(k, 0.18))
        if now >= self.next_blink and self.blink == 0.0:
            self.blink = 0.001
        if self.blink > 0:
            self.blink += 0.28
            if self.blink >= 2.0:
                self.blink = 0.0
                self.next_blink = now + random.uniform(2.0, 5.0)
        self.queue_draw()
        return True

    # ------------------------------------------------------------ rysowanie
    @staticmethod
    def _rrect(cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -TAU / 4, 0)
        cr.arc(x + w - r, y + h - r, r, 0, TAU / 4)
        cr.arc(x + r, y + h - r, r, TAU / 4, TAU / 2)
        cr.arc(x + r, y + r, r, TAU / 2, 3 * TAU / 4)
        cr.close_path()

    @staticmethod
    def _col(cr, hexcol, a=1.0):
        h = hexcol.lstrip("#")
        cr.set_source_rgba(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

    def _fill_stroke(self, cr, fill, stroke=None, lw=2.0):
        self._col(cr, fill)
        if stroke:
            cr.fill_preserve()
            self._col(cr, stroke)
            cr.set_line_width(lw)
            cr.stroke()
        else:
            cr.fill()

    def paint(self, cr, W, H):
        p = self.p
        now = time.monotonic()
        s = min(W / 175.0, H / 190.0)
        cr.save()
        cr.translate((W - 175 * s) / 2, (H - 190 * s) / 2 + 3 * s)
        cr.scale(s, s)
        bob = math.sin((now - self.t0) * 1.6) * (1.2 if self.state == "idle" else 0.6)
        cr.translate(15, 22 + bob)          # układ głowy: 130 × 150

        # korpus (szalik)
        self._rrect(cr, 30, 118, 70, 26, 8)
        self._fill_stroke(cr, "#C8102E")
        cr.rectangle(30, 127, 70, 7)
        self._fill_stroke(cr, "#F1BF00")

        # fale dźwięku (słucha)
        if p["wave"] > 0.05:
            self._col(cr, "#C8102E", min(1.0, p["wave"]))
            cr.set_line_width(2.5)
            cr.set_line_cap(1)
            for k, r in enumerate((10, 18)):
                cr.arc(126, 66, r, -0.9, 0.9)
                cr.stroke()

        # głowa z przechyłem
        cr.save()
        cr.translate(65, 80)
        cr.rotate(math.radians(p["tilt"]))
        cr.translate(-65, -80)

        # antena
        self._col(cr, "#8a6a3b")
        cr.set_line_width(2)
        cr.move_to(65, 18); cr.line_to(65, 6); cr.stroke()
        cr.arc(65, 5, 5, 0, TAU)
        self._fill_stroke(cr, "#F1BF00", "#8a6a3b", 1)
        # głowa
        self._rrect(cr, 10, 26, 110, 90, 26)
        self._fill_stroke(cr, "#EBD9B8", "#8a6a3b", 2)
        # beret
        cr.save(); cr.translate(65, 26); cr.scale(52, 13); cr.arc(0, 0, 1, 0, TAU); cr.restore()
        self._fill_stroke(cr, "#2b2b2b")
        cr.arc(65, 13, 4, 0, TAU)
        self._fill_stroke(cr, "#2b2b2b")
        # nity po bokach
        for x in (6, 124):
            cr.arc(x, 72, 6, 0, TAU)
            self._fill_stroke(cr, "#C9A96B", "#8a6a3b", 1.5)

        # oczy
        bl = 0.0
        if self.blink > 0:
            bl = 1 - abs(self.blink - 1.0)      # 0→1→0
        if p["happy"] > 0.5:
            self._col(cr, "#2b2b2b")
            cr.set_line_width(4)
            cr.set_line_cap(1)
            for cx in (42, 88):
                cr.arc(cx, 68, 12, math.radians(200), math.radians(340))
                cr.stroke()
            self._col(cr, "#E8836F", 0.6)
            for cx in (26, 104):
                cr.arc(cx, 82, 7, 0, TAU); cr.fill()
        else:
            for cx in (42, 88):
                cr.save()
                cr.translate(cx, 62)
                cr.scale(1, max(0.08, 1 - bl))
                cr.arc(0, 0, 14, 0, TAU)
                self._fill_stroke(cr, "#FFFFFF", "#8a6a3b", 1.5)
                cr.restore()
                if bl < 0.7:
                    cr.save()
                    cr.translate(cx + p["pdx"] * 5, 62 + p["pdy"] * 5)
                    cr.scale(1, max(0.1, 1 - bl))
                    cr.arc(0, 0, 6, 0, TAU)
                    self._fill_stroke(cr, "#2b2b2b")
                    cr.restore()
        # brwi
        self._col(cr, "#2b2b2b")
        cr.set_line_width(3)
        cr.set_line_cap(1)
        by = -6 if p["happy"] > 0.5 else 0
        cr.move_to(28, 46 + by + p["brow_l"] * 0.5); cr.curve_to(34, 40 + by + p["brow_l"], 50, 40 + by + p["brow_l"], 56, 46 + by)
        cr.stroke()
        cr.move_to(74, 46 + by); cr.curve_to(80, 40 + by + p["brow_r"], 96, 40 + by + p["brow_r"], 102, 46 + by + p["brow_r"] * 0.5)
        cr.stroke()
        # wąs
        cr.move_to(40, 88)
        cr.curve_to(52, 80, 60, 82, 65, 87)
        cr.curve_to(70, 82, 78, 80, 90, 88)
        cr.curve_to(78, 94, 70, 93, 65, 91)
        cr.curve_to(60, 93, 52, 94, 40, 88)
        self._fill_stroke(cr, "#2b2b2b")
        # usta
        m, sm = p["mouth"], p["smile"]
        if m > 0.08 or sm > 0.7:
            ry = 2 + 7 * max(m, 0.45 if sm > 0.7 else 0)
            cr.save(); cr.translate(65, 100 + ry * 0.4); cr.scale(10 + 3 * m, ry); cr.arc(0, 0, 1, 0, TAU); cr.restore()
            self._fill_stroke(cr, "#7a2a2a", "#2b2b2b", 1.5)
        else:
            self._col(cr, "#2b2b2b")
            cr.set_line_width(3)
            cr.set_line_cap(1)
            cr.move_to(55, 102)
            cr.curve_to(60, 102 + 6 * sm, 70, 102 + 6 * sm, 75, 102)
            cr.stroke()
        cr.restore()   # koniec przechyłu

        # myśli
        if p["dots"] > 0.05:
            ph = int((now - self.t0) * 2.5) % 4
            for i, (x, y, r) in enumerate(((132, 22, 3), (141, 14, 4), (152, 3, 5))):
                if i < ph:
                    cr.arc(x, y, r, 0, TAU)
                    self._col(cr, "#8a6a3b", p["dots"])
                    cr.fill()
        cr.restore()
