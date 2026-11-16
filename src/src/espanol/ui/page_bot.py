"""Ekran: Rozmowa z botem (wersja tekstowa)."""
import os
import queue
import threading
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango  # noqa: E402

from .widgets import label, scrolled, page_box, card, clear, AccentBar, SpeakButton, slow_button, run_bg
from .. import bot, drill
from ..audio import Recorder, Vad
from ..paths import REC_DIR
from .page_learner import load_manual, load_auto
from .paco import Paco
from ..i18n import _

# frazy, które Whisper „wymyśla” z ciszy
_JUNK = ("amara.org", "subtítulos", "subtitulos", "gracias por ver", "suscríbete", "suscribete")


class BotPage(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.conv = None
        self.state = "idle"        # idle / listening / thinking / speaking
        self._listen_id = 0
        self._turn_id = 0
        self._playing = False
        self._play_q = []
        self._cur_cb = None
        self._misses = 0
        self._vad = None
        self.outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(self.outer, True, True, 0)
        self.show_start()

    # ------------------------------------------------------------ ekran startowy
    def show_start(self):
        app = self.app
        clear(self.outer)
        b = page_box()
        top = Gtk.Box(spacing=14)
        self.paco_start = Paco(110)
        top.pack_start(self.paco_start, False, False, 0)
        tcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        tcol.set_valign(Gtk.Align.CENTER)
        tcol.pack_start(label(_("Rozmowa z Paco"), "hero"), False, False, 0)
        tcol.pack_start(label(_("Paco to Twój rozmówca. Mówisz lub piszesz po hiszpańsku, a on używa tylko słówek "
                                "i gramatyki z lekcji, które już ukończyłeś. Błędy poprawia łagodnie, a na końcu "
                                "dostajesz podsumowanie."), "dim"), False, False, 0)
        top.pack_start(tcol, True, True, 0)
        b.pack_start(top, False, False, 0)
        backend = bot.make_backend(app.db)
        kind = app.db.get("bot_backend", "ollama")
        info = card(spacing=4)
        if kind == "claude":
            ok = bool(bot.load_api_key())
            info.pack_start(label(_("Silnik: Claude API — {}").format(bot.CLAUDE_MODELS.get(backend.model, backend.model)),
                                  "title2"), False, False, 0)
            info.pack_start(label(_("Tekst rozmowy jest wysyłany do API Anthropic (nagrania głosu nie). "
                                    "Wymaga internetu i klucza API; płatne za użycie."), "dim"), False, False, 0)
        else:
            ok = bool(backend.model)
            info.pack_start(label(_("Silnik: Ollama (lokalnie, offline) — model: {}").format(backend.model or _("nie wybrano")),
                                  "title2"), False, False, 0)
            info.pack_start(label(_("Wszystko zostaje na Twoim komputerze. Wymaga zainstalowanej Ollamy "
                                    "i pobranego modelu."), "dim"), False, False, 0)
        if not ok:
            info.pack_start(label(_("⚠ Bot nie jest jeszcze przygotowany."), "warn-text"), False, False, 0)
            ib = Gtk.Button(label=_("⬇  Zainstaluj bota offline (Ollama + model) — jednym kliknięciem"))
            ib.get_style_context().add_class("suggested-action")
            ib.set_halign(Gtk.Align.START)
            ib.connect("clicked", lambda *_a: OllamaSetupDialog(app, app.win))
            info.pack_start(ib, False, False, 0)
        sb = Gtk.Button(label=_("Ustawienia bota"))
        sb.set_halign(Gtk.Align.START)
        sb.connect("clicked", lambda *_a: app.show_page("settings"))
        info.pack_start(sb, False, False, 0)
        b.pack_start(info, False, False, 0)

        done = set(app.db.done_lessons())
        if not done:
            b.pack_start(card(label(_("Nie masz jeszcze ukończonych lekcji — bot będzie używał tylko materiału z lekcji 1. "
                                      "Najlepiej najpierw zrób kilka lekcji."), "warn-text")), False, False, 0)
        lv = Gtk.Box(spacing=10)
        lv.pack_start(label(_("Poziom rozmówcy:"), wrap=False), False, False, 0)
        self.level_combo = Gtk.ComboBoxText()
        for k, (name, _d) in bot.LEVELS.items():
            self.level_combo.append(k, f"{name} — {_d}")
        self.level_combo.set_active_id(app.db.get("bot_level", "normal"))
        self.level_combo.connect("changed", lambda w: app.db.set("bot_level", w.get_active_id()))
        lv.pack_start(self.level_combo, False, False, 0)
        hist = Gtk.Button(label=_("📜 Historia rozmów"))
        hist.connect("clicked", lambda *_a: self.show_history())
        lv.pack_end(hist, False, False, 0)
        me = Gtk.Button(label=_("🙂 O mnie (dane dla bota)"))
        me.connect("clicked", lambda *_a: app.show_page("learner"))
        lv.pack_end(me, False, False, 0)
        b.pack_start(lv, False, False, 0)
        b.pack_start(label(_("Wybierz scenkę"), "title2"), False, False, 0)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(3)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)
        flow.set_homogeneous(True)
        for sc in bot.SCENARIOS:
            les = app.course.by_id.get(sc["lesson"])
            unlocked = sc["lesson"] in done or sc["id"] == "free"
            c = card(spacing=6)
            c.pack_start(label(sc["title"], "title2"), False, False, 0)
            c.pack_start(label(sc["goal"], "dim"), False, False, 0)
            if not unlocked and les:
                c.pack_start(label(_("Zalecane po lekcji {} {}: {}").format(les.level, les.number, les.title), "warn-text"),
                             False, False, 0)
            bt = Gtk.Button(label=_("Rozpocznij") if unlocked else _("Rozpocznij mimo to"))
            if unlocked:
                bt.get_style_context().add_class("suggested-action")
            bt.set_sensitive(ok)
            bt.set_halign(Gtk.Align.START)
            bt.connect("clicked", lambda _b, s=sc: self.start(s))
            c.pack_end(bt, False, False, 0)
            flow.add(c)
        b.pack_start(flow, False, False, 0)
        self.outer.pack_start(scrolled(b), True, True, 0)
        self.outer.show_all()

    # ------------------------------------------------------------ rozmowa
    def start(self, scenario):
        app = self.app
        profile = bot.Profile(app.course, set(app.db.done_lessons()))
        self.conv = bot.Conversation(bot.make_backend(app.db), profile, scenario,
                                     level=app.db.get("bot_level", "normal"),
                                     manual=load_manual(app.db), auto=load_auto(app.db))
        self.conv.helper = bot.translator(app.db)
        self.conv.defer_translation = True     # Paco's reply shows at once; the translation follows
        clear(self.outer)
        head = Gtk.Box(spacing=10)
        for side in ("start", "end", "top"):
            getattr(head, f"set_margin_{side}")(16)
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        back.connect("clicked", lambda *_a: (self._cancel_all(), self.show_start()))
        head.pack_start(back, False, False, 0)
        back.set_valign(Gtk.Align.CENTER)
        self.paco = Paco(84)
        self.paco.set_valign(Gtk.Align.CENTER)
        head.pack_start(self.paco, False, False, 0)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.set_valign(Gtk.Align.CENTER)
        col.pack_start(label(scenario["title"], "hero"), False, False, 0)
        col.pack_start(label(_("Twoje zadanie: ") + scenario["goal"], "dim"), False, False, 0)
        head.pack_start(col, True, True, 0)
        end = Gtk.Button(label=_("Zakończ i podsumuj"))
        end.set_valign(Gtk.Align.CENTER)
        end.connect("clicked", lambda *_a: self.finish())
        head.pack_end(end, False, False, 0)
        self.outer.pack_start(head, False, False, 0)

        self.chat = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("start", "end", "top", "bottom"):
            getattr(self.chat, f"set_margin_{side}")(16)
        self.chat_sw = scrolled(self.chat)
        self.outer.pack_start(self.chat_sw, True, True, 0)

        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for side in ("start", "end", "bottom"):
            getattr(bottom, f"set_margin_{side}")(16)
        row = Gtk.Box(spacing=8)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(_("Napisz po hiszpańsku… (możesz też zapytać po polsku o pomoc)"))
        self.entry.connect("activate", lambda *_a: self.send())
        row.pack_start(self.entry, True, True, 0)
        self.send_btn = Gtk.Button(label=_("Wyślij"))
        self.send_btn.get_style_context().add_class("suggested-action")
        self.send_btn.connect("clicked", lambda *_a: self.send())
        row.pack_start(self.send_btn, False, False, 0)
        bottom.pack_start(row, False, False, 0)
        bottom.pack_start(self._voice_bar(), False, False, 0)
        tools = Gtk.Box(spacing=12)
        tools.pack_start(AccentBar(self.entry), False, False, 0)
        self.show_pl = Gtk.CheckButton(label=_("Pokazuj tłumaczenie"))
        self.show_pl.set_active(self.app.db.get("bot_show_pl", True))
        self.show_pl.connect("toggled", self._toggle_pl)
        tools.pack_end(self.show_pl, False, False, 0)
        self.spinner = Gtk.Spinner()
        tools.pack_end(self.spinner, False, False, 0)
        bottom.pack_start(tools, False, False, 0)
        self.outer.pack_start(bottom, False, False, 0)
        self.pl_labels = []
        self.outer.show_all()
        self._misses = 0
        self._set_state("idle")
        if self._speak_on():
            self._bot_turn(self.conv.start_stream)
        else:
            self._busy(True)
            run_bg(self.conv.start, self._bot_said, self._error)

    def _busy(self, on):
        self.send_btn.set_sensitive(not on)
        self.entry.set_sensitive(not on)
        if on:
            self.spinner.start()
        else:
            self.spinner.stop()
            self.entry.grab_focus()

    # ------------------------------------------------------------ pasek głosowy
    def _voice_bar(self):
        app = self.app
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        row = Gtk.Box(spacing=10)
        self.mic_btn = Gtk.Button(label=_("🎤  Mów"))
        self.mic_btn.get_style_context().add_class("mic-btn")
        self.mic_btn.connect("clicked", lambda *_a: self._mic_clicked())
        row.pack_start(self.mic_btn, False, False, 0)
        self.level = Gtk.LevelBar()
        self.level.set_min_value(0)
        self.level.set_max_value(1)
        self.level.set_size_request(140, 8)
        self.level.set_valign(Gtk.Align.CENTER)
        row.pack_start(self.level, False, False, 0)
        self.cancel_btn = Gtk.Button(label=_("✖ Anuluj"))
        self.cancel_btn.set_no_show_all(True)
        self.cancel_btn.connect("clicked", lambda *_a: (self._cancel_listen(), self._set_state("idle")))
        row.pack_start(self.cancel_btn, False, False, 0)
        self.vstatus = label("", "dim", wrap=False)
        row.pack_start(self.vstatus, True, True, 0)
        box.pack_start(row, False, False, 0)
        opts = Gtk.Box(spacing=16)
        self.voice_chk = Gtk.CheckButton(label=_("Rozmówca mówi na głos"))
        self.voice_chk.set_active(bool(app.db.get("bot_voice", True)) and app.speech.tts_available())
        self.voice_chk.set_sensitive(app.speech.tts_available())
        self.voice_chk.connect("toggled", lambda w: app.db.set("bot_voice", w.get_active()))
        opts.pack_start(self.voice_chk, False, False, 0)
        self.hands_chk = Gtk.CheckButton(label=_("Bez rąk: po odpowiedzi sam zacznę słuchać"))
        self.hands_chk.set_active(bool(app.db.get("bot_handsfree", False)))
        self.hands_chk.connect("toggled", self._hands_toggled)
        opts.pack_start(self.hands_chk, False, False, 0)
        from .. import speech as _sp
        inst = [(k, v[0]) for k, v in _sp.WHISPER_SIZES.items() if _sp.engine_installed() and _sp.whisper_ready(k)]
        if len(inst) >= 2:
            opts.pack_end(self._whisper_combo(inst), False, False, 0)
            opts.pack_end(label(_("Rozpoznawanie mowy:"), "dim", wrap=False), False, False, 0)
        box.pack_start(opts, False, False, 0)
        self.mic_ok = app.speech.stt_available() and Recorder.available()
        if not self.mic_ok:
            self.mic_btn.set_sensitive(False)
            self.hands_chk.set_sensitive(False)
            self.vstatus.set_text(_("Rozmowa głosowa wymaga modelu rozpoznawania mowy i mikrofonu (Ustawienia)."))
        else:
            box.pack_start(label(_("Wskazówka: najlepiej w słuchawkach — wtedy mikrofon nie łapie głosu rozmówcy."),
                                 "dim"), False, False, 0)
        return box

    def _whisper_combo(self, inst):
        cb = Gtk.ComboBoxText()
        for k, name in inst:
            cb.append(k, name)
        cb.set_active_id(self.app.db.get("whisper", "small"))
        cb.connect("changed", lambda w: self.app.db.set("whisper", w.get_active_id()))
        return cb

    def _hands_toggled(self, w):
        self.app.db.set("bot_handsfree", w.get_active())
        if w.get_active() and self.state == "idle" and self.conv:
            self._listen()

    def _speak_on(self):
        return hasattr(self, "voice_chk") and self.voice_chk.get_active() and self.app.speech.tts_available()

    def _set_state(self, st, note=""):
        self.state = st
        if getattr(self, "paco", None):
            self.paco.set_state(st)
        texts = {"idle": _("🎤  Mów"), "listening": _("✔  Skończyłem mówić"),
                 "thinking": _("🎤  Mów"), "speaking": _("🎤  Przerwij i mów")}
        self.mic_btn.set_label(texts[st])
        (self.mic_btn.get_style_context().add_class if st == "listening"
         else self.mic_btn.get_style_context().remove_class)("rec")
        self.cancel_btn.set_visible(st == "listening")
        status = {"idle": "", "listening": _("Słucham… masz czas — kliknij „Skończyłem”, gdy skończysz"),
                  "thinking": _("Rozmówca myśli…"), "speaking": _("Rozmówca mówi…")}[st]
        self.vstatus.set_text(note or status)
        self.mic_btn.set_sensitive(self.mic_ok and st != "thinking")
        if st == "thinking":
            self.spinner.start()
            self.send_btn.set_sensitive(False)
            self.entry.set_sensitive(False)
        else:
            self.spinner.stop()
            self.send_btn.set_sensitive(True)
            self.entry.set_sensitive(True)
            if st == "idle":
                self.level.set_value(0)

    # ------------------------------------------------------------ nasłuchiwanie
    def _mic_clicked(self):
        if self.state == "listening":
            if self._vad and self._vad.speaking:
                self._vad_event("end", self._listen_id)   # ręczne zakończenie → wyślij
            else:
                self._cancel_listen()
                self._set_state("idle")
        elif self.state == "speaking":
            self._interrupt_speech()
            self._listen()
        elif self.state == "idle":
            self._listen()

    def _listen(self):
        if not self.conv or not self.mic_ok:
            return
        self.app.stop_audio()
        self._listen_id += 1
        lid = self._listen_id
        self._set_state("listening")
        path = os.path.join(REC_DIR, f"bot-{int(time.time() * 1000)}.wav")
        vad = self._vad = Vad(end_silence=float(self.app.db.get("bot_silence", 3.0)))
        self.app.recorder.start(path, on_level=lambda v: (self.level.set_value(v), self.paco.set_level(v)), vad=vad,
                                on_event=lambda ev: self._vad_event(ev, lid))

    def _cancel_listen(self):
        self._listen_id += 1
        self.app.recorder.stop(lambda _p: None)
        self.level.set_value(0)

    def _vad_event(self, ev, lid):
        if lid != self._listen_id or self.state != "listening":
            return
        if ev == "start":
            self.vstatus.set_text(_("Słyszę Cię… (po dłuższej ciszy sam skończę — albo kliknij „Skończyłem”)"))
        elif ev in ("end", "max"):
            self._listen_id += 1
            self.level.set_value(0)
            self.app.recorder.stop(self._recorded)
            self._set_state("thinking", _("Rozpoznaję mowę…"))
        elif ev == "timeout":
            self._cancel_listen()
            self._set_state("idle", _("Nie słyszę, żebyś mówił — kliknij 🎤, gdy będziesz gotowy."))
            self.hands_chk.set_active(False)

    def _recorded(self, path):
        if not path:
            self._set_state("idle", _("Nie udało się nagrać dźwięku — sprawdź mikrofon w ustawieniach systemu."))
            return
        last = next((t["es"] for t in reversed(self.conv.turns) if t["who"] == "bot"), "") if self.conv else ""
        prompt = ("Conversación en español de España con un estudiante principiante. " + last)[:400]
        run_bg(lambda: self.app.speech.transcribe(path, prompt), self._heard, self._voice_error)

    def _voice_error(self, e):
        self._set_state("idle", _("Błąd rozpoznawania mowy: {}").format(e))

    def _heard(self, r):
        if not self.conv:
            return
        text = (r.get("text") or "").strip()
        low = text.lower()
        if len(text.strip(" .,!?¡¿…")) < 2 or any(j in low for j in _JUNK):
            self._misses += 1
            self._set_state("idle", _("Nie zrozumiałem — spróbuj jeszcze raz."))
            if self.hands_chk.get_active() and self._misses < 3:
                GLib.timeout_add(500, lambda: (self.state == "idle" and self._listen(), False)[1])
            return
        self._misses = 0
        self._submit(text)

    # ------------------------------------------------------------ tura bota (strumieniowo)
    def _submit(self, text):
        self._bubble("me", text)
        if self._speak_on():
            self._bot_turn(lambda cb: self.conv.send_stream(text, cb))
        else:
            self._busy(True)

            self.conv.on_help = None

            def done(r):
                if r.get("help"):
                    self._help_note(r["help"])
                if r.get("fix"):
                    self._fix_note(r["fix"], r.get("ok", ""))
                self._bot_said(r)
                self._persist_facts()
                self.paco.react("worried" if r.get("fix") else "happy")
                self._set_state("idle")
                if self.hands_chk.get_active():
                    GLib.timeout_add(300, lambda: (self.state == "idle" and self._listen(), False)[1])
            self._set_state("thinking")
            run_bg(lambda: self.conv.send(text), done, self._error)

    def _bot_turn(self, fn):
        self._set_state("thinking")
        self.app.stop_audio()
        self._turn_id += 1
        tid = self._turn_id
        self._play_q, self._playing = [], False
        self._live = None
        self._live_text = ""
        self._reply_done = False
        self._tts_done = False
        self._help_shown = False
        self.conv.on_help = lambda h: GLib.idle_add(self._help_note, h)
        q = queue.Queue()
        speech = self.app.speech

        def tts_loop():
            while True:
                sent = q.get()
                if sent is None or tid != self._turn_id:
                    break
                try:
                    path = speech.synth(sent)
                except Exception as e:  # noqa
                    GLib.idle_add(self.app.toast, _("Nie mogę odtworzyć: {}").format(e))
                    continue
                GLib.idle_add(self._enqueue, path, tid)
            GLib.idle_add(self._tts_finished, tid)
        threading.Thread(target=tts_loop, daemon=True).start()

        def on_sentence(sent):
            GLib.idle_add(self._live_add, sent, tid)
            q.put(sent)

        def work():
            try:
                return fn(on_sentence)
            finally:
                q.put(None)
        run_bg(work, lambda r: self._turn_done(r, tid), lambda e: self._turn_error(e, tid))

    def _live_add(self, sent, tid):
        if tid != self._turn_id or not self.conv:
            return
        self._live_text = (self._live_text + " " + sent).strip()
        if self._live is None:
            self._live = self._bubble("bot", self._live_text)
        else:
            self._live._es_label.set_text(self._live_text)
            GLib.timeout_add(80, self._scroll_end)

    def _turn_done(self, r, tid):
        if tid != self._turn_id or not self.conv:
            return
        if self._live is not None:
            self._live.destroy()
        if r.get("help") and not self._help_shown:
            self._help_note(r["help"])
        if r.get("fix"):
            self._fix_note(r["fix"], r.get("ok", ""))
        if r.get("es"):
            bub = self._bubble("bot", r["es"], r.get("pl", ""), r.get("unknown", []), pending=r.get("pl_pending"))
            if r.get("pl_pending"):
                self._translate_later(bub)
        self._persist_facts()
        self.paco.react("worried" if r.get("fix") else "happy")
        self._reply_done = True
        self._maybe_finish(tid)

    def _turn_error(self, e, tid):
        if tid != self._turn_id:
            return
        self._reply_done = True
        self._error(e)
        self._set_state("idle")

    def _tts_finished(self, tid):
        if tid != self._turn_id:
            return
        self._tts_done = True
        self._maybe_finish(tid)

    def _enqueue(self, path, tid):
        if tid != self._turn_id:
            return
        self._play_q.append(path)
        # ktoś inny (np. przycisk 🔊) mógł przejąć odtwarzacz
        if self._playing and self.app.player.on_done is not self._cur_cb:
            self._playing = False
        if not self._playing:
            self._play_next(tid)

    def _play_next(self, tid):
        if tid != self._turn_id or not self._play_q:
            return
        path = self._play_q.pop(0)
        self._playing = True
        if self.state != "listening":
            self._set_state("speaking")
        self._cur_cb = lambda: self._play_done(tid)
        self.paco.talk(path)
        self.app.player.play(path, on_done=self._cur_cb)

    def _play_done(self, tid):
        if tid != self._turn_id:
            return
        self._playing = False
        if self._play_q:
            GLib.timeout_add(120, lambda: (self._play_next(tid), False)[1])
        else:
            self._maybe_finish(tid)

    def _maybe_finish(self, tid):
        if tid != self._turn_id or self._playing or self._play_q:
            return
        if not (self._reply_done and self._tts_done):
            return
        if self.state in ("thinking", "speaking"):
            self._set_state("idle")
        if self.conv and self.hands_chk.get_active() and self.mic_ok:
            GLib.timeout_add(350, lambda: (self.state == "idle" and self.conv and self._listen(), False)[1])

    def _interrupt_speech(self):
        self._turn_id += 1       # unieważnia kolejkę i wątek TTS
        self._play_q, self._playing = [], False
        self.app.stop_audio()
        self._set_state("idle")

    def _cancel_all(self):
        self._turn_id += 1
        self._play_q, self._playing = [], False
        if self.state == "listening":
            self._cancel_listen()
        self.app.stop_audio()
        if hasattr(self, "mic_btn"):
            try:
                self._set_state("idle")
            except Exception:  # noqa
                pass

    def _toggle_pl(self, w):
        self.app.db.set("bot_show_pl", w.get_active())
        for lb in self.pl_labels:
            lb.set_visible(w.get_active())

    def _translate_later(self, bubble):
        """Translation of the last bot turn in the background; fills the line under the bubble."""
        conv = self.conv
        turn = next((t for t in reversed(conv.turns) if t["who"] == "bot"), None) if conv else None
        lb = getattr(bubble, "_pl_label", None)
        if turn is None or lb is None:
            return

        def done(tr):
            try:
                if tr:
                    lb.get_style_context().remove_class("pending")
                    lb.set_text(tr)
                else:
                    lb.set_text(_("(brak tłumaczenia)"))
            except Exception:  # noqa  — the chat screen may be gone already
                pass
        run_bg(lambda: conv.translate_turn(turn), done, lambda e: done(""))

    def _bubble(self, who, es, pl="", unknown=(), pending=False):
        c = card(spacing=4)
        c.set_halign(Gtk.Align.START if who == "bot" else Gtk.Align.END)
        c.set_size_request(320, -1)
        top = Gtk.Box(spacing=6)
        top.pack_start(label(_("🤖 Rozmówca") if who == "bot" else _("🙂 Ty"), "dim", wrap=False), False, False, 0)
        if who == "bot":
            top.pack_end(slow_button(self.app, es), False, False, 0)
            top.pack_end(SpeakButton(self.app, es), False, False, 0)
        c.pack_start(top, False, False, 0)
        txt = GLib.markup_escape_text(es)
        for w in sorted(set(unknown), key=len, reverse=True):
            txt = txt.replace(w, f'<u>{GLib.markup_escape_text(w)}</u>')
        lb = label(txt, "mid-es", markup=True, selectable=True)
        lb.set_max_width_chars(60)
        c._es_label = lb
        c.pack_start(lb, False, False, 0)
        if pl or pending:
            p = label(pl or _("tłumaczę…"), "dim")
            if pending:
                p.get_style_context().add_class("pending")
            p.set_max_width_chars(60)
            p.set_no_show_all(True)
            p.set_visible(self.show_pl.get_active())
            self.pl_labels.append(p)
            c._pl_label = p
            c.pack_start(p, False, False, 0)
        if unknown:
            c.pack_start(label(_("Podkreślone — słowa spoza Twoich lekcji: ") + ", ".join(sorted(set(unknown))), "dim"),
                         False, False, 0)
        self.chat.pack_start(c, False, False, 0)
        c.show_all()
        if pl or pending:
            self.pl_labels[-1].set_visible(self.show_pl.get_active())
        GLib.timeout_add(80, self._scroll_end)
        return c

    def _scroll_end(self):
        adj = self.chat_sw.get_vadjustment() if self.conv else None
        if adj:
            adj.set_value(adj.get_upper())
        return False

    def _bot_said(self, r):
        self._busy(False)
        if not r.get("es"):
            return
        bub = self._bubble("bot", r["es"], r.get("pl", ""), r.get("unknown", []), pending=r.get("pl_pending"))
        if r.get("pl_pending"):
            self._translate_later(bub)
        if self.app.db.get("autoplay", True):
            self.app.say(r["es"])

    def _help_note(self, text):
        c = card(spacing=4)
        c.set_halign(Gtk.Align.START)
        c.pack_start(label(_("💡 Wyjaśnienie Paco"), "warn-text", wrap=False), False, False, 0)
        lb = label(text)
        lb.set_max_width_chars(70)
        lb.set_selectable(True)
        c.pack_start(lb, False, False, 0)
        c.pack_start(label(_("🎤 Teraz spróbuj powiedzieć to sam — Paco czeka na Ciebie."), "dim"), False, False, 0)
        self.chat.pack_start(c, False, False, 0)
        c.show_all()
        GLib.timeout_add(80, self._scroll_end)
        self._help_shown = True

    def _fix_note(self, text, ok=""):
        c = card(spacing=2)
        c.set_halign(Gtk.Align.END)
        c.pack_start(label(_("✎ Poprawka"), "warn-text", wrap=False), False, False, 0)
        if ok:
            c.pack_start(label(_("Poprawnie: ") + ok, "mid-es"), False, False, 0)
        lb = label(text)
        lb.set_max_width_chars(60)
        c.pack_start(lb, False, False, 0)
        self.chat.pack_start(c, False, False, 0)
        c.show_all()

    def send(self):
        text = self.entry.get_text().strip()
        if not text or not self.conv:
            return
        self.entry.set_text("")
        if self.state == "listening":
            self._cancel_listen()
        elif self.state == "speaking":
            self._interrupt_speech()
        self._submit(text)

    def _error(self, e):
        if self.state == "thinking":
            self._set_state("idle")
        self._busy(False)
        c = card(label(_("Błąd silnika bota: {}").format(e), "bad-text"))
        self.chat.pack_start(c, False, False, 0)
        c.show_all()
        if self.conv and self.conv.messages and self.conv.messages[-1]["role"] == "user":
            self.conv.messages.pop()  # pozwól wysłać ponownie

    # ------------------------------------------------------------ podsumowanie
    def _persist_facts(self):
        if self.conv:
            self.app.db.set("learner_auto", self.conv.auto)

    def finish(self):
        if not self.conv:
            return
        self._cancel_all()
        s = self.conv.summary()
        db = self.app.db
        self._persist_facts()
        for orig, ok, fix in s["fixes"]:
            db.save_mistake("bot", orig, "", (ok + " — " if ok else "") + fix)
            item = drill.from_bot_fix(orig, ok, fix)
            if item:
                db.drill_add(item)
        score, verdict = bot.rate(s)
        s["score"], s["verdict"] = score, verdict
        if s["messages"]:
            db.save_test("bot", self.conv.scenario["id"], s["messages"] - len(s["fixes"]), max(1, s["messages"]),
                         {"words": s["words"]})
            cid = db.save_conversation(self.conv.scenario["id"], self.conv.scenario["title"], self.conv.level,
                                       score, self.conv.turns, s)
        else:
            cid = None
        conv, self.conv = self.conv, None
        self._remember_async(conv)
        self.app.refresh_all()
        if cid:
            self.show_saved(cid, from_history=False)
        else:
            self.show_start()

    def _remember_async(self, conv):
        """W tle: bot zapisuje sobie, co zapamiętać o uczniu (pamięć między rozmowami)."""
        db = self.app.db

        def merge(mem):
            if not mem:
                return
            auto = db.get("learner_auto", {}) or {}
            old = auto.get("memories", [])
            seen = {x.lower() for x in old}
            for m in mem.get("memories", []):
                if m.lower() not in seen:
                    old.append(m)
                    seen.add(m.lower())
            if old:
                auto["memories"] = old[-12:]
            if mem.get("last_talk"):
                auto["last_talk"] = mem["last_talk"]
            db.set("learner_auto", auto)
        run_bg(conv.make_memory, merge, lambda e: print("pamięć bota:", e))

    # ------------------------------------------------------------ zapisana rozmowa / podsumowanie
    def show_saved(self, cid, from_history=True):
        db = self.app.db
        d = db.get_conversation(cid)
        if not d:
            self.show_history()
            return
        s = d["summary"]
        clear(self.outer)
        b = page_box()
        head = Gtk.Box(spacing=10)
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        back.connect("clicked", lambda *_a: self.show_history() if from_history else self.show_start())
        head.pack_start(back, False, False, 0)
        head.pack_start(label(_("Podsumowanie rozmowy") if not from_history else _("Zapisana rozmowa"), "hero"),
                        True, True, 0)
        b.pack_start(head, False, False, 0)
        c = card(spacing=4)
        lvl = bot.LEVELS.get(d["level"], ("", ""))[0]
        c.pack_start(label(d["title"], "title2"), False, False, 0)
        c.pack_start(label(time.strftime("%d.%m.%Y %H:%M", time.localtime(d["ts"])) + (_("  ·  poziom: {}").format(lvl) if lvl else ""),
                           "dim"), False, False, 0)
        score = d["score"] or 0
        c.pack_start(label(_("Ocena rozmowy: {}/100 — {}").format(score, s.get('verdict', '')),
                           "ok-text" if score >= 70 else "warn-text"), False, False, 0)
        bar = Gtk.ProgressBar()
        bar.set_fraction(score / 100)
        c.pack_start(bar, False, False, 0)
        c.pack_start(label(_("Twoje wypowiedzi: {}  ·  słowa: {} (różnych: {})  ·  poprawki: {}").format(
            s['messages'], s['words'], s['unique'], len(s['fixes']))), False, False, 0)
        if s["messages"]:
            pct = round(100 * (s["messages"] - len(s["fixes"])) / s["messages"])
            c.pack_start(label(_("Wypowiedzi bez błędów: {}%  ·  średnio {} słowa na wypowiedź").format(
                pct, f"{s['words'] / s['messages']:.1f}"), "dim"), False, False, 0)
        b.pack_start(c, False, False, 0)

        if s["fixes"]:
            c2 = card(spacing=6)
            c2.pack_start(label(_("Do poprawy"), "title2"), False, False, 0)
            esc = GLib.markup_escape_text
            for orig, ok, fix in s["fixes"]:
                txt = (_("Ty: ") + f'<span foreground="#d0353f">{esc(orig)}</span>\n'
                       + (_("Poprawnie: ") + f'<b><span foreground="#2e9e44">{esc(ok)}</span></b>\n' if ok else "")
                       + f"{esc(fix)}")
                row = Gtk.Box(spacing=8)
                row.pack_start(label(txt, markup=True), True, True, 0)
                if ok:
                    row.pack_start(SpeakButton(self.app, ok), False, False, 0)
                    row.pack_start(slow_button(self.app, ok), False, False, 0)
                c2.pack_start(row, False, False, 0)
            cards = [(ok, fix) for _o, ok, fix in s["fixes"] if ok]
            if cards:
                todo = [(ok, fix) for ok, fix in cards if not db.has_card(ok)]
                ex = Gtk.Button(label=_("➕ Dodaj poprawione zdania do powtórek ({})").format(len(todo)) if todo
                                else _("✔ Poprawione zdania są już w powtórkach"))
                ex.set_sensitive(bool(todo))
                ex.set_halign(Gtk.Align.START)

                def _export(btn, items=todo):
                    for ok, fix in items:
                        db.add_card(dict(es=ok, pl=fix, pos="zdanie", lesson="rozmowa"))
                    btn.set_label(_("✔ Dodano {} do powtórek").format(len(items)))
                    btn.set_sensitive(False)
                    self.app.refresh_all()
                ex.connect("clicked", _export)
                c2.pack_start(ex, False, False, 0)
            b.pack_start(c2, False, False, 0)

        new_words = [w for w in self.app.course.dictionary
                     if w["es"].split("/")[0].strip().split()[-1].lower() in s.get("bot_unknown", [])]
        if new_words:
            c3 = card(spacing=6)
            c3.pack_start(label(_("Nowe słowa z rozmowy (są w słowniku)"), "title2"), False, False, 0)
            for w in new_words[:15]:
                row = Gtk.Box(spacing=8)
                row.pack_start(label(f"{w['es']} — {w['pl']}"), True, True, 0)
                add = Gtk.Button(label=_("✔ W powtórkach") if db.has_card(w["es"]) else _("+ Do powtórek"))
                add.set_sensitive(not db.has_card(w["es"]))

                def _add(btn, dd=w):
                    db.add_card(dd)
                    btn.set_label(_("✔ W powtórkach"))
                    btn.set_sensitive(False)
                add.connect("clicked", _add)
                row.pack_start(add, False, False, 0)
                c3.pack_start(row, False, False, 0)
            b.pack_start(c3, False, False, 0)

        c4 = card(spacing=6)
        c4.pack_start(label(_("Zapis rozmowy"), "title2"), False, False, 0)
        for t in d["turns"]:
            mine = t["who"] == "me"
            row = Gtk.Box(spacing=8)
            who = label(_("🙂 Ty") if mine else "🤖", "dim", wrap=False)
            who.set_size_request(60, -1)
            row.pack_start(who, False, False, 0)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            col.pack_start(label(t["es"], "mid-es", selectable=True), False, False, 0)
            if t.get("pl") and not mine:
                col.pack_start(label(t["pl"], "dim"), False, False, 0)
            if mine and t.get("fix"):
                col.pack_start(label("✎ " + (t.get("ok") + " — " if t.get("ok") else "") + t["fix"], "warn-text"),
                               False, False, 0)
            row.pack_start(col, True, True, 0)
            if not mine:
                row.pack_start(SpeakButton(self.app, t["es"]), False, False, 0)
                row.pack_start(slow_button(self.app, t["es"]), False, False, 0)
            c4.pack_start(row, False, False, 0)
        b.pack_start(c4, False, False, 0)

        act = Gtk.Box(spacing=8)
        if from_history:
            dl = Gtk.Button(label=_("Usuń z historii"))
            dl.connect("clicked", lambda *_a: (db.delete_conversation(cid), self.show_history()))
            act.pack_start(dl, False, False, 0)
        again = Gtk.Button(label=_("Nowa rozmowa"))
        again.get_style_context().add_class("suggested-action")
        again.connect("clicked", lambda *_a: self.show_start())
        act.pack_end(again, False, False, 0)
        b.pack_start(act, False, False, 0)
        self.outer.pack_start(scrolled(b), True, True, 0)
        self.outer.show_all()

    def show_history(self):
        db = self.app.db
        self._cancel_all()
        self.conv = None
        clear(self.outer)
        b = page_box()
        head = Gtk.Box(spacing=10)
        back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        back.connect("clicked", lambda *_a: self.show_start())
        head.pack_start(back, False, False, 0)
        head.pack_start(label(_("Historia rozmów"), "hero"), True, True, 0)
        b.pack_start(head, False, False, 0)
        rows = db.list_conversations()
        if not rows:
            b.pack_start(card(label(_("Jeszcze nie masz zapisanych rozmów. Po kliknięciu „Zakończ i podsumuj” "
                                      "rozmowa trafia tutaj."), "dim")), False, False, 0)
        else:
            scores = [r["score"] or 0 for r in rows][:10][::-1]
            if len(scores) >= 2:
                trend = scores[-1] - scores[0]
                b.pack_start(label(_("Ostatnie {} rozmów — średnia ocena {}/100").format(len(scores), round(sum(scores) / len(scores)))
                                   + (_(", zmiana {} pkt względem pierwszej z nich").format(f"{trend:+d}") if trend else ""),
                                   "dim"),
                             False, False, 0)
        for r in rows:
            c = card(spacing=4)
            row = Gtk.Box(spacing=10)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            col.pack_start(label(r["title"], "title2"), False, False, 0)
            col.pack_start(label(time.strftime("%d.%m.%Y %H:%M", time.localtime(r["ts"]))
                                 + _("  ·  poziom: {}").format(bot.LEVELS.get(r['level'], ('?',))[0]), "dim"), False, False, 0)
            row.pack_start(col, True, True, 0)
            sc = r["score"] or 0
            row.pack_start(label(f"{sc}/100", "ok-text" if sc >= 70 else "warn-text", wrap=False), False, False, 0)
            op = Gtk.Button(label=_("Otwórz"))
            op.connect("clicked", lambda _b, cid=r["id"]: self.show_saved(cid, True))
            row.pack_start(op, False, False, 0)
            c.pack_start(row, False, False, 0)
            b.pack_start(c, False, False, 0)
        self.outer.pack_start(scrolled(b), True, True, 0)
        self.outer.show_all()


# ====================================================================== KREATOR: OLLAMA + MODEL
class OllamaSetupDialog(Gtk.Dialog):
    def __init__(self, app, parent):
        from .. import ollama_local as ol
        from .. import speech
        super().__init__(title=_("Bot offline — instalacja Ollamy i modelu"), transient_for=parent, modal=True)
        self.app, self.ol = app, ol
        self.set_default_size(680, 560)
        box = self.get_content_area()
        box.set_spacing(10)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(16)
        hw = speech.hardware()
        self.use_system = ol.system_ollama()
        box.pack_start(label(_("Jednym kliknięciem zainstaluję wszystko, czego potrzebuje bot — działa potem "
                               "całkowicie offline, za darmo, bez hasła administratora."), "title2"), False, False, 0)
        if self.use_system:
            what = _("• Wykryto Ollamę w systemie — użyję jej, pobiorę tylko model.")
        elif ol.installed():
            what = _("• Prywatna Ollama jest już zainstalowana — pobiorę tylko model.")
        else:
            what = _("• Ollama (silnik modeli językowych) — do Twojego katalogu domowego, ok. 1–2 GB\n"
                     "  (zawiera biblioteki dla kart NVIDIA; uruchamia się sama tylko na czas rozmowy)")
        box.pack_start(label(what + _("\n• wybrany model językowy (poniżej)")), False, False, 0)
        gpu = ", ".join(hw["gpus"]) or _("brak")
        box.pack_start(label(_("Twój komputer: {} GB RAM · karta: {}").format(hw['ram'], gpu)
                             + (_(" (sterownik NVIDIA aktywny — będzie szybko)") if hw["nvidia"] else ""), "dim"),
                       False, False, 0)
        rec = ol.recommended_model(hw)
        group = None
        self.radios = {}
        for name, desc, size, note in ol.MODELS:
            rb = Gtk.RadioButton.new_with_label_from_widget(group, f"{desc} — {size}"
                                                            + (_("   ← zalecany dla Ciebie") if name == rec else ""))
            group = group or rb
            rb.set_active(name == rec)
            box.pack_start(rb, False, False, 0)
            nl = label(f"      {name}: {note}", "dim")
            box.pack_start(nl, False, False, 0)
            self.radios[name] = rb
        self.bar = Gtk.ProgressBar()
        box.pack_start(self.bar, False, False, 0)
        self.status = label("", markup=True)
        box.pack_start(self.status, False, False, 0)
        self.buf = Gtk.TextBuffer()
        self.tv = Gtk.TextView(buffer=self.buf)
        self.tv.set_editable(False)
        self.tv.set_monospace(True)
        self.tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        box.pack_start(scrolled(self.tv), True, True, 0)
        self.start_btn = self.add_button(_("Zainstaluj"), Gtk.ResponseType.OK)
        self.start_btn.get_style_context().add_class("suggested-action")
        self.close_btn = self.add_button(_("Zamknij"), Gtk.ResponseType.CLOSE)
        self.connect("response", self._resp)
        self.show_all()

    def _resp(self, _d, rid):
        if rid != Gtk.ResponseType.OK:
            self.destroy()
            return
        model = next(n for n, rb in self.radios.items() if rb.get_active())
        self.model = model
        for rb in self.radios.values():
            rb.set_sensitive(False)
        self.start_btn.set_sensitive(False)
        self.close_btn.set_sensitive(False)
        self.status.set_markup(_("<b>Instaluję…</b> Możesz zostawić to okno otwarte — to potrwa kilka minut."))
        self.ol.Installer(model, self.use_system,
                          lambda t: GLib.idle_add(self._log, t),
                          lambda f: GLib.idle_add(self.bar.set_fraction, min(1.0, f)),
                          lambda ok, m: GLib.idle_add(self._done, ok, m)).start()

    def _log(self, t):
        self.buf.insert(self.buf.get_end_iter(), t + "\n")
        self.tv.scroll_to_iter(self.buf.get_end_iter(), 0, False, 0, 0)

    def _done(self, ok, info):
        db = self.app.db
        self.close_btn.set_sensitive(True)
        if ok:
            db.set("bot_backend", "ollama")
            db.set("ollama_model", self.model)
            db.set("ollama_url", info)
            db.set("ollama_managed", not self.use_system)
            self.start_btn.set_label(_("Gotowe ✔"))
            self.status.set_markup('<span foreground="#2e9e44" size="large"><b>' + _("✔ Bot jest gotowy!")
                                   + '</b></span> ' + _("Zamknij to okno i wybierz scenkę w „Rozmowa z botem”."))
            self.app.pages["settings"].refresh()
            if not self.app.pages["bot"].conv:
                self.app.pages["bot"].show_start()
        else:
            self.start_btn.set_label(_("Spróbuj ponownie"))
            self.start_btn.set_sensitive(True)
            for rb in self.radios.values():
                rb.set_sensitive(True)
            self.status.set_markup('<span foreground="#d0353f" size="large"><b>' + _("✘ Nie udało się.")
                                   + '</b></span> ' + _("Sprawdź internet i miejsce na dysku, potem spróbuj ponownie."))
