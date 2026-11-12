"""Ćwiczenie wymowy: posłuchaj → nagraj się → ocena słowo po słowie."""
import os
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .. import answers
from ..paths import REC_DIR
from .widgets import label, SpeakButton, slow_button, run_bg


class SpeakPractice(Gtk.Box):
    def __init__(self, app, target, translation="", on_scored=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.app, self.target = app, target
        self.on_scored = on_scored
        self.recording = False
        self.last_rec = None

        row = Gtk.Box(spacing=8)
        row.pack_start(label(target, "big-es"), True, True, 0)
        row.pack_start(SpeakButton(app, target), False, False, 0)
        row.pack_start(slow_button(app, target), False, False, 0)
        self.pack_start(row, False, False, 0)
        if translation:
            self.pack_start(label(translation, "dim"), False, False, 0)

        ctl = Gtk.Box(spacing=8)
        self.rec_btn = Gtk.Button()
        self._set_rec_label()
        self.rec_btn.get_style_context().add_class("suggested-action")
        self.rec_btn.connect("clicked", self._toggle)
        ctl.pack_start(self.rec_btn, False, False, 0)
        self.play_btn = Gtk.Button(label="Odsłuchaj siebie")
        self.play_btn.set_sensitive(False)
        self.play_btn.connect("clicked", lambda *_: self.last_rec and self.app.player.play(self.last_rec))
        ctl.pack_start(self.play_btn, False, False, 0)
        self.level = Gtk.LevelBar()
        self.level.set_min_value(0)
        self.level.set_max_value(1)
        self.level.set_size_request(120, 8)
        self.level.set_valign(Gtk.Align.CENTER)
        ctl.pack_start(self.level, False, False, 0)
        self.spinner = Gtk.Spinner()
        ctl.pack_start(self.spinner, False, False, 0)
        self.pack_start(ctl, False, False, 0)

        self.result = label("", markup=True)
        self.pack_start(self.result, False, False, 0)
        self.tips = label("", "dim")
        self.pack_start(self.tips, False, False, 0)

        if not app.speech.stt_available():
            self.rec_btn.set_sensitive(False)
            self.result.set_markup('<span alpha="70%">Ocena wymowy wymaga modelu rozpoznawania mowy — '
                                   'zainstaluj go w <b>Ustawieniach</b>.</span>')

    def _set_rec_label(self):
        self.rec_btn.set_label("■  Zakończ nagrywanie" if self.recording else "🎤  Nagraj się")

    def _toggle(self, *_):
        if not self.recording:
            self.recording = True
            self._set_rec_label()
            path = os.path.join(REC_DIR, f"rec-{int(time.time() * 1000)}.wav")
            self.result.set_markup('<span alpha="70%">Mów teraz… (kliknij ponownie, aby zakończyć)</span>')
            self.tips.set_text("")
            self.app.player.stop()
            self.app.recorder.start(path, on_level=self.level.set_value)
            # automatyczne zakończenie po 15 s
            self._auto = GLib.timeout_add_seconds(15, self._auto_stop)
        else:
            self._stop()

    def _auto_stop(self):
        if self.recording:
            self._stop()
        return False

    def _stop(self):
        self.recording = False
        self._set_rec_label()
        self.rec_btn.set_sensitive(False)
        self.level.set_value(0)
        self.app.recorder.stop(self._recorded)

    def _recorded(self, path):
        if not path:
            self.rec_btn.set_sensitive(True)
            self.result.set_markup('<span foreground="#d0353f">Nie udało się nagrać dźwięku. '
                                   'Sprawdź mikrofon w ustawieniach systemu.</span>')
            return
        self.last_rec = path
        self.play_btn.set_sensitive(True)
        self.spinner.start()
        self.result.set_markup('<span alpha="70%">Analizuję wymowę…</span>')
        run_bg(lambda: self.app.speech.transcribe(path), self._scored, self._error)

    def _error(self, e):
        self.spinner.stop()
        self.rec_btn.set_sensitive(True)
        self.result.set_markup(f'<span foreground="#d0353f">Błąd rozpoznawania mowy: '
                               f'{GLib.markup_escape_text(str(e))}</span>')

    def _scored(self, r):
        self.spinner.stop()
        self.rec_btn.set_sensitive(True)
        heard = r.get("text", "")
        words, score = answers.word_diff(self.target, heard)
        parts = []
        for w, ok in words:
            color = "#2e9e44" if ok else "#d0353f"
            u = "" if ok else ' underline="single"'
            parts.append(f'<span foreground="{color}"{u}><b>{GLib.markup_escape_text(w)}</b></span>')
        verdict = ("¡Excelente!" if score >= 90 else "¡Muy bien!" if score >= 75
                   else "Nieźle — spróbuj jeszcze raz." if score >= 50 else "Spróbuj jeszcze raz, wolniej.")
        heard_esc = GLib.markup_escape_text(heard or "(nic nie rozpoznano)")
        self.result.set_markup(f'<span size="large">{" ".join(parts)}</span>\n'
                               f'<b>{score}%</b> — {verdict}\n'
                               f'<span alpha="70%">Usłyszałem: „{heard_esc}”</span>')
        bad = [w for w, ok in words if not ok]
        tips = answers.tips_for(bad)
        self.tips.set_text("\n".join("💡 " + t for t in tips))
        try:
            self.app.db.save_pron(self.target, heard, score)
            self.app.db.log_activity(items=1)
        except Exception:  # noqa
            pass
        if self.on_scored:
            self.on_scored(score)
