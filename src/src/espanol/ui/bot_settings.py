"""Settings → Chat with the bot: everything about Paco in one card, as rows of big tiles to click.

1. Paco's brain (the chat model)   2. Translations   3. Recognising your speech   4. When you have finished speaking
The Claude API key appears only when Claude is chosen somewhere; an own Ollama server sits under "Advanced"."""
import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from .widgets import label, card, clear
from .. import bot as botmod
from .. import i18n
from .. import ollama_local as ol
from .. import speech
from ..i18n import _

FAST, SMART, LIGHT = "qwen3:8b", "qwen3:14b", "gemma3:4b"
SIZES = {FAST: "5,2 GB", SMART: "9 GB", LIGHT: "3,3 GB", botmod.BIELIK: "6,7 GB"}
NEEDS_VRAM = {FAST: 6, SMART: 12, LIGHT: 4}       # GB of graphics memory for the whole model to fit


def gpu_vram_gb():
    """Graphics card memory in GB (NVIDIA), 0 when unknown."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=3).stdout
        return round(int(out.split()[0]) / 1024)
    except Exception:  # noqa
        return 0


def tiles(options, active, on_pick):
    """A row of big toggle tiles. options: [(key, title, subtitle)]; on_pick(key) when one is clicked."""
    row = Gtk.Box(spacing=10, homogeneous=True)
    group = None
    for key, title, sub in options:
        rb = Gtk.RadioButton.new_from_widget(group)
        group = group or rb
        rb.set_mode(False)                       # a button, not a round radio dot
        rb.get_style_context().add_class("choice-tile")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        t = label(title, "tile-title")
        t.set_xalign(0)
        box.pack_start(t, False, False, 0)
        if sub:
            s = label(sub, "tile-sub")
            s.set_xalign(0)
            box.pack_start(s, False, False, 0)
        rb.add(box)
        rb.set_active(key == active)
        rb.connect("toggled", lambda w, k=key: w.get_active() and on_pick(k))
        row.pack_start(rb, True, True, 0)
    return row


def step(n, title, hint=""):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box.set_margin_top(10)
    box.pack_start(label(f"{n}. {title}", "step-title"), False, False, 0)
    if hint:
        box.pack_start(label(hint, "dim"), False, False, 0)
    return box


class BotSettings(Gtk.Box):
    """The whole bot card; rebuilds itself after every change."""

    def __init__(self, app, save_key):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app, self.db, self.save_key = app, app.db, save_key
        self.vram = gpu_vram_gb()
        self.pending = None          # model whose tile was clicked but is not downloaded yet
        self.pending_tr = False      # Bielik tile clicked but Bielik not downloaded yet
        self.status = ""
        self.build()

    # ------------------------------------------------------------ state
    def brain(self):
        if self.db.get("bot_backend", "ollama") == "claude":
            return "claude"
        return self.pending or self.db.get("ollama_model", "") or ""

    def translations(self):
        if self.db.get("pl_claude", False):
            return "claude"
        if self.db.get("pl_bielik", False) and i18n.LANG == "pl":
            return "bielik"
        return "same"

    def use_system(self):
        return not self.db.get("ollama_managed", True)

    def present(self, model):
        return ol.model_present(model, self.use_system())

    # ------------------------------------------------------------ actions
    def pick_brain(self, key):
        if key == "claude":
            self.pending = None
            self.db.set("bot_backend", "claude")
        elif self.present(key):
            self.pending = None
            self.db.set("bot_backend", "ollama")
            self.db.set("ollama_model", key)
        else:
            self.pending = key                    # show the download button; nothing changes until it is there
        GLib.idle_add(self.build)

    def pick_translations(self, key):
        self.db.set("pl_claude", key == "claude")
        self.db.set("pl_bielik", key == "bielik")
        GLib.idle_add(self.build)

    def pick_whisper(self, key):
        self.db.set("whisper", key)
        GLib.idle_add(self.build)

    def pick_silence(self, key):
        self.db.set("bot_silence", float(key))

    def download(self, model, then):
        """Downloads an Ollama model (and the private Ollama itself when needed) with a status line."""
        self.status = _("Pobieranie…")
        self.build()

        def log(t):
            self.status = t.strip()[:100]
            if self.status_lbl:
                self.status_lbl.set_text(self.status)

        def done(ok, url):
            if ok:
                if not self.use_system():
                    self.db.set("ollama_managed", True)
                    self.db.set("ollama_url", url)
                then()
                self.status = _("✔ Pobrano: {}").format(model)
            else:
                self.status = _("✘ Nie udało się pobrać — sprawdź internet i miejsce na dysku.")
            self.pending, self.pending_tr = None, False
            self.build()
        ol.Installer(model, self.use_system(), lambda t: GLib.idle_add(log, t), lambda f: None,
                     lambda ok, info: GLib.idle_add(done, ok, info)).start()

    # ------------------------------------------------------------ view
    def build(self):
        clear(self)
        db = self.db
        self.status_lbl = None
        c = card(spacing=4)
        c.pack_start(label(_("Rozmowa z botem"), "title2"), False, False, 0)
        c.pack_start(label(_("Wszystko o Paco w jednym miejscu. Kliknij kafelek, żeby wybrać."), "dim"), False, False, 0)

        # 1. brain
        vram = self.vram
        c.pack_start(step(1, _("Mózg Paco — kto prowadzi rozmowę"),
                          _("Twoja karta graficzna: {} GB pamięci.").format(vram) if vram else ""), False, False, 0)
        opts = []
        for model, title, base in ((FAST, _("🚀 Szybki"), _("Dobre rozmowy, szybkie odpowiedzi. Zalecany.")),
                                   (SMART, _("🧠 Dokładniejszy"), _("Trochę mądrzejszy, ale duży.")),
                                   (LIGHT, _("🪶 Lekki"), _("Dla słabszych komputerów, częściej się myli."))):
            sub = f"{model}\n{base}"
            if vram and NEEDS_VRAM[model] > vram:
                sub += "\n" + _("⚠ Na Twojej karcie bardzo wolny (nie mieści się w pamięci).")
            sub += "\n" + (_("✔ pobrany") if self.present(model) else _("⬇ do pobrania ({})").format(SIZES[model]))
            opts.append((model, title, sub))
        opts.append(("claude", _("☁️ Claude (chmura)"),
                     _("Najlepsze rozmowy i najszybsze odpowiedzi.\nPotrzebny klucz API, płatne za użycie.")))
        c.pack_start(tiles(opts, self.brain(), self.pick_brain), False, False, 0)
        if self.pending:
            row = Gtk.Box(spacing=10)
            row.pack_start(label(_("Model {} nie jest jeszcze pobrany.").format(self.pending), "warn-text", wrap=False),
                           False, False, 0)
            dl = Gtk.Button(label=_("⬇ Pobierz {} ({})").format(self.pending, SIZES.get(self.pending, "")))
            dl.get_style_context().add_class("suggested-action")
            model = self.pending
            dl.connect("clicked", lambda *_a: self.download(model, lambda: (db.set("bot_backend", "ollama"),
                                                                             db.set("ollama_model", model))))
            row.pack_start(dl, False, False, 0)
            c.pack_start(row, False, False, 0)
        if self.brain() == "claude":
            cm = [(k, n.split(" (")[0], n[n.find("(") + 1:-1] if "(" in n else "") for k, n in botmod.CLAUDE_MODELS.items()]
            c.pack_start(tiles(cm, db.get("claude_model", "claude-haiku-5-5"),
                               lambda k: db.set("claude_model", k)), False, False, 0)

        # 2. translations
        c.pack_start(step(2, _("Tłumaczenia odpowiedzi Paco"),
                          _("Hiszpańską odpowiedź słyszysz od razu; tłumaczenie pojawia się pod nią.")), False, False, 0)
        if self.brain() == "claude":
            c.pack_start(label(_("Przy Claude tłumaczy też Claude — nic nie trzeba wybierać."), "ok-text"), False, False, 0)
        else:
            topts = [("same", _("⚡ Ten sam model"), _("Najszybciej. Bez dodatkowych pobrań.") +
                      ("\n" + _("Polszczyzna bywa z błędami.") if i18n.LANG == "pl" else ""))]
            if i18n.LANG == "pl":
                bsub = _("Dużo lepsza polszczyzna, offline.\nOdpowiedź ok. 2× wolniej.") + "\n" + (
                    _("✔ pobrany") if self.present(botmod.BIELIK) else _("⬇ do pobrania ({})").format(SIZES[botmod.BIELIK]))
                topts.append(("bielik", _("🇵🇱 Bielik"), bsub))
            topts.append(("claude", _("☁️ Claude"), _("Najlepsza jakość.\nPotrzebny klucz API, płatne za użycie.")))
            current = "bielik" if self.pending_tr else self.translations()
            c.pack_start(tiles(topts, current, self._pick_tr_checked), False, False, 0)
            if self.pending_tr:
                row = Gtk.Box(spacing=10)
                row.pack_start(label(_("Bielik nie jest jeszcze pobrany."), "warn-text", wrap=False), False, False, 0)
                dl = Gtk.Button(label=_("⬇ Pobierz Bielika ({})").format(SIZES[botmod.BIELIK]))
                dl.get_style_context().add_class("suggested-action")
                dl.connect("clicked", lambda *_a: self.download(botmod.BIELIK, lambda: self.pick_translations("bielik")))
                row.pack_start(dl, False, False, 0)
                c.pack_start(row, False, False, 0)

        # Claude key (only when Claude is used somewhere)
        if self.brain() == "claude" or self.translations() == "claude":
            kr = Gtk.Box(spacing=10)
            kr.set_margin_top(6)
            kr.pack_start(label(_("Klucz API:"), wrap=False), False, False, 0)
            key = Gtk.Entry()
            key.set_visibility(False)
            key.set_text(botmod.load_api_key())
            key.set_placeholder_text("sk-ant-…")
            key.set_width_chars(36)
            key.connect("changed", lambda w: self.save_key(w))
            kr.pack_start(key, False, False, 0)
            link = Gtk.LinkButton.new_with_label("https://console.anthropic.com/settings/keys",
                                                 _("🔑 Utwórz klucz API (console.anthropic.com)"))
            link.set_tooltip_text(_("Otwiera w przeglądarce stronę Anthropic, na której zakładasz konto "
                                    "i tworzysz klucz (przycisk „Create Key”). Skopiuj go i wklej obok."))
            kr.pack_start(link, False, False, 0)
            c.pack_start(kr, False, False, 0)
            c.pack_start(label(_("Klucz jest zapisany tylko na tym komputerze (systemowy schowek haseł). "
                                 "Do API wysyłany jest tylko tekst rozmowy, nigdy nagrania głosu."), "dim"), False, False, 0)

        # 3. speech recognition
        c.pack_start(step(3, _("Rozpoznawanie Twojej mowy"),
                          _("Dotyczy rozmowy z botem i ćwiczeń wymowy.")), False, False, 0)
        wopts = []
        for k, sub in (("base", _("Najszybsze, mniej dokładne.")), ("small", _("Dobry kompromis. Zalecane.")),
                       ("medium", _("Najdokładniejsze, ale wolniejsze\ni zabiera pamięć karty botowi."))):
            ready = speech.engine_installed() and speech.whisper_ready(k)
            wopts.append((k, speech.WHISPER_SIZES[k][0].split(" (")[0],
                          f"{sub}\n" + (_("✔ pobrane") if ready else _("⬇ do pobrania ({})").format(speech.WHISPER_SIZES[k][1]))))
        wcur = db.get("whisper", "small")
        c.pack_start(tiles(wopts, wcur, self.pick_whisper), False, False, 0)
        if not (speech.engine_installed() and speech.whisper_ready(wcur)):
            wb = Gtk.Button(label=_("⬇ Pobierz wybrany model rozpoznawania mowy"))
            wb.get_style_context().add_class("suggested-action")
            wb.set_halign(Gtk.Align.START)
            wb.connect("clicked", lambda *_a: self.app.open_setup())
            c.pack_start(wb, False, False, 0)

        # 4. silence
        c.pack_start(step(4, _("Kiedy skończyłeś mówić"),
                          _("Po ilu sekundach ciszy Paco uzna, że skończyłeś. Zawsze możesz też kliknąć „Skończyłem”.")),
                     False, False, 0)
        sil = float(db.get("bot_silence", 3.0))
        sopts = [("2.0", _("2 s"), _("Szybko")), ("3.0", _("3 s"), _("Zalecane")),
                 ("4.0", _("4 s"), _("Spokojnie")), ("6.0", _("6 s"), _("Dużo czasu na myślenie"))]
        cur = min(sopts, key=lambda o: abs(float(o[0]) - sil))[0]
        c.pack_start(tiles(sopts, cur, self.pick_silence), False, False, 0)

        # status of a download
        if self.status:
            self.status_lbl = label(self.status, "dim")
            c.pack_start(self.status_lbl, False, False, 0)

        # advanced: own Ollama server
        exp = Gtk.Expander(label=_("Zaawansowane — własny serwer Ollama"))
        exp.set_margin_top(8)
        ga = Gtk.Grid(column_spacing=12, row_spacing=8)
        ga.set_margin_top(8)
        url = Gtk.Entry()
        url.set_text(db.get("ollama_url", "http://localhost:11434"))
        url.set_width_chars(30)

        def url_changed(w):
            db.set("ollama_url", w.get_text().strip())
            db.set("ollama_managed", False)
        url.connect("changed", url_changed)
        ga.attach(label(_("Adres Ollama:"), wrap=False), 0, 0, 1, 1)
        ga.attach(url, 1, 0, 1, 1)
        name = Gtk.Entry()
        name.set_text(db.get("ollama_model", ""))
        name.set_placeholder_text(_("nazwa modelu"))
        name.connect("changed", lambda w: db.set("ollama_model", w.get_text().strip()))
        ga.attach(label(_("Model:"), wrap=False), 0, 1, 1, 1)
        ga.attach(name, 1, 1, 1, 1)
        back = Gtk.Button(label=_("Wróć do prywatnej Ollamy aplikacji"))
        back.connect("clicked", lambda *_a: (db.set("ollama_managed", True), db.set("ollama_url", ol.MANAGED_URL),
                                              GLib.idle_add(self.build)))
        ga.attach(back, 0, 2, 2, 1)
        exp.add(ga)
        c.pack_start(exp, False, False, 0)

        self.pack_start(c, False, False, 0)
        self.show_all()
        return False

    def _pick_tr_checked(self, key):
        self.pending_tr = key == "bielik" and not self.present(botmod.BIELIK)
        if self.pending_tr:
            GLib.idle_add(self.build)                 # show the download button; nothing changes until it is there
            return
        self.pick_translations(key)
