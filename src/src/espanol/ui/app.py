"""Główne okno aplikacji."""
import os
import time
import random
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib  # noqa: E402

from .. import i18n  # noqa: E402
i18n.init()          # course language of the active profile — before the pages, which translate at import time

from .. import VERSION
from ..paths import APP_ID, APP_NAME, DATA
from ..db import DB
from ..content import Course
from ..speech import Speech, engine_installed, voices_installed
from ..audio import Player, Recorder
from .widgets import CSS, CSS2, run_bg, label
from . import themes
from .pages_course import TodayPage, CoursePage, LessonView
from .pages_tools import AlphabetPage, ReviewPage, DictionaryPage, ConjugationPage, PronLabPage
from .page_bot import BotPage
from .page_learner import LearnerPage
from .page_dictation import DictationPage
from .page_scenes import ScenesPage
from .pages_more import (ReadingsPage, VideosPage, TestsPage, StatsPage, SettingsPage, SetupDialog,
                         TestView, build_unit_test, build_exam)
from ..i18n import _  # noqa: E402

ICON = "linux-espanol-learning"

PAGES = [
    ("today", _("Dzisiaj"), "go-home-symbolic"),
    ("course", _("Kurs"), "accessories-dictionary-symbolic"),
    ("alphabet", _("Alfabet i wymowa"), "format-text-bold-symbolic"),
    ("review", _("Powtórki"), "view-refresh-symbolic"),
    ("dictionary", _("Słownik ES–PL"), "edit-find-symbolic"),
    ("conj", _("Odmiana"), "view-list-symbolic"),
    ("pron", _("Laboratorium wymowy"), "audio-input-microphone-symbolic"),
    ("dictation", _("Dyktando"), "document-edit-symbolic"),
    ("scenes", _("Scenki z Paco"), "face-smile-symbolic"),
    ("bot", _("Rozmowa z botem"), "user-available-symbolic"),
    ("learner", _("O mnie (dla bota)"), "avatar-default-symbolic"),
    ("readings", _("Czytanki"), "x-office-document-symbolic"),
    ("videos", _("Filmy i słuchanie"), "video-x-generic-symbolic"),
    ("tests", _("Testy i egzaminy"), "emblem-ok-symbolic"),
    ("stats", _("Statystyki"), "x-office-spreadsheet-symbolic"),
    ("settings", _("Ustawienia"), "emblem-system-symbolic"),
]

# menu w grupach (1.13); „Ustawienia” są w menu ☰ w nagłówku
NAV_GROUPS = [
    ("learn", _("Nauka"), ["today", "course", "review", "tests"]),
    ("practice", _("Ćwicz"), ["pron", "dictation", "scenes", "bot", "readings", "videos"]),
    ("tools", _("Narzędzia"), ["dictionary", "conj", "alphabet"]),
    ("you", _("Ty"), ["stats", "learner"]),
]


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_application_name(APP_NAME)
        GLib.set_prgname("linux-espanol-learning")
        self.win = None
        self._lang = i18n.LANG      # language this process was started in (texts are translated at import)

    # ------------------------------------------------------------ start
    def do_startup(self):
        Gtk.Application.do_startup(self)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        prov2 = Gtk.CssProvider()            # nowe elementy (1.13): nad motywem, który czyści tła kontenerów
        prov2.load_from_data(CSS2)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov2,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
        self.palette = None
        local_icons = os.path.join(DATA, "..", "icons")
        if os.path.isdir(local_icons):
            Gtk.IconTheme.get_default().append_search_path(os.path.abspath(local_icons))
        self.db = DB()
        self.course = Course()
        self._migrate_drill()
        self.speech = Speech(self.db)
        self.player = Player()
        self.recorder = Recorder()
        self._seq = []
        self._seq_token = 0
        for name, cb in (("about", self.on_about), ("shortcuts", self.show_shortcuts), ("settings", lambda *_a: self.show_page("settings")),
                         ("quit", lambda *_a: self.quit())):
            a = Gio.SimpleAction.new(name, None)
            a.connect("activate", cb)
            self.add_action(a)
        self.set_accels_for_action("app.quit", ["<Ctrl>q"])
        self._setup_theme()
        self._start_icon_helper()

    def _start_icon_helper(self):
        """Dock icon light/dark: the helper (also started at login) runs now too, so it works right after install."""
        helper = "/usr/lib/linux-espanol-learning/icon-watch.sh"
        if os.path.exists(helper):
            try:
                import subprocess
                subprocess.Popen(["sh", helper], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
            except OSError:
                pass

    def do_activate(self):
        if self.win:
            self.win.present()
            return
        self.build_window()
        if not (engine_installed() and voices_installed()) and not self.db.get("setup_offered"):
            self.db.set("setup_offered", True)
            GLib.timeout_add(600, lambda: (self.open_setup(), False)[1])
        else:
            self.speech.preload_stt()
        GLib.timeout_add_seconds(60, self._tick)

    def _tick(self):
        if self.win and self.win.is_active():
            self.db.log_activity(seconds=60)
            try:
                if "today" in self.pages and self.pages["today"].get_mapped():
                    self.pages["today"].refresh()
            except Exception:  # noqa
                pass
        self._maybe_remind()
        return True

    def _maybe_remind(self):
        """Przypomnienie o nauce (systemowe powiadomienie), jeśli cel dzienny niezaliczony."""
        db = self.db
        if not db.get("remind_on", True):
            return
        today = time.strftime("%Y-%m-%d")
        if db.get("remind_last") == today or time.localtime().tm_hour < int(db.get("remind_hour", 19)):
            return
        goal = int(db.get("daily_goal", 10))
        if db.today_seconds() >= goal * 60:
            return
        db.set("remind_last", today)
        cur, _best = db.streak()
        n = Gio.Notification.new("Linux Español Learning")
        n.set_body((_('Masz serię {} dni — ').format(cur) if cur else "") + _('zostało Ci kilka minut do dzisiejszego celu ({} min). ¡Vamos!').format(goal))
        n.set_icon(Gio.ThemedIcon.new("linux-espanol-learning"))
        try:
            self.send_notification("remind", n)
        except Exception:  # noqa
            pass

    # ------------------------------------------------------------ motyw
    def apply_theme(self):
        self._apply_theme()

    def _setup_theme(self):
        self.gsettings = None
        src = Gio.SettingsSchemaSource.get_default()
        if src and src.lookup("org.gnome.desktop.interface", True):
            self.gsettings = Gio.Settings.new("org.gnome.desktop.interface")
            self.gsettings.connect("changed", lambda *_a: self._apply_theme())
        self._apply_theme()

    def system_dark(self):
        if self.gsettings:
            keys = self.gsettings.props.settings_schema.list_keys()
            if "color-scheme" in keys and self.gsettings.get_string("color-scheme") == "prefer-dark":
                return True
            if "gtk-theme" in keys and self.gsettings.get_string("gtk-theme").lower().endswith("-dark"):
                return True
            return False
        return False

    def is_dark(self):
        mode = self.db.get("theme_mode", "auto")
        if mode == "dark":
            return True
        if mode == "light":
            return False
        return self.system_dark()

    def _apply_theme(self):
        dark = self.is_dark()
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", dark)
        screen = Gdk.Screen.get_default()
        if getattr(self, "theme_provider", None):
            Gtk.StyleContext.remove_provider_for_screen(screen, self.theme_provider)
            self.theme_provider = None
        name = self.db.get("color_theme", "system")
        entry = themes.THEMES.get(name)
        self.palette = (entry[2] if dark else entry[1]) if entry and entry[1] else None  # kolory kółek postępu
        if entry and entry[1]:
            prov = Gtk.CssProvider()
            prov.load_from_data(themes.css(entry[2] if dark else entry[1]).encode())
            # nad stylem aplikacji (CSS), żeby kolory motywu wygrywały z motywem systemu
            Gtk.StyleContext.add_provider_for_screen(screen, prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
            self.theme_provider = prov
        icon = ICON + ("-dark" if dark else "")
        Gtk.Window.set_default_icon_name(icon)
        if self.win:
            self.win.set_icon_name(icon)
            self.win.queue_draw()

    # ------------------------------------------------------------ okno
    def build_window(self):
        win = Gtk.ApplicationWindow(application=self)
        self.win = win
        win.set_title(APP_NAME)
        win.set_default_size(1180, 800)
        win.set_icon_name(ICON + ("-dark" if self.is_dark() else ""))
        self._apply_theme()
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.set_title(APP_NAME)
        hb.set_subtitle(_("Kurs hiszpańskiego A1–A2 · Hiszpania"))
        menu = Gio.Menu()
        menu.append(_("Ustawienia"), "app.settings")
        menu.append(_("Skróty klawiszowe"), "app.shortcuts")
        menu.append(_("O programie"), "app.about")
        menu.append(_("Zakończ"), "app.quit")
        mb = Gtk.MenuButton()
        mb.set_menu_model(menu)
        mb.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        hb.pack_end(mb)
        hb.pack_end(self._profile_button())
        win.set_titlebar(hb)

        paned = Gtk.Box()
        # menu w zwijanych grupach (1.13); stan zwinięcia zapamiętany w ustawieniach
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        nav.get_style_context().add_class("navigation-sidebar")
        nav.set_size_request(230, -1)
        titles = {k: (t, i) for k, t, i in PAGES}
        closed = set(self.db.get("nav_closed", []) or [])
        self.side_rows, self.side_lists, self.nav_groups = {}, [], {}
        self._nav_lock = False
        for gkey, gtitle, keys in NAV_GROUPS:
            head = Gtk.Button()
            head.get_style_context().add_class("nav-head")
            hbox = Gtk.Box(spacing=6)
            hbox.pack_start(Gtk.Label(label=gtitle.upper(), xalign=0), True, True, 0)
            arrow = Gtk.Image.new_from_icon_name("pan-down-symbolic", Gtk.IconSize.MENU)
            hbox.pack_end(arrow, False, False, 0)
            head.add(hbox)
            lb = Gtk.ListBox()
            lb.get_style_context().add_class("navigation-sidebar")
            for key in keys:
                title, icon = titles[key]
                row = Gtk.ListBoxRow()
                hb2 = Gtk.Box(spacing=10)
                hb2.get_style_context().add_class("sidebar-row")
                hb2.pack_start(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU), False, False, 0)
                hb2.pack_start(label(title, wrap=False), False, False, 0)
                if key == "review":
                    self.review_badge = Gtk.Label()
                    self.review_badge.get_style_context().add_class("nav-count")
                    self.review_badge.set_no_show_all(True)
                    hb2.pack_end(self.review_badge, False, False, 0)
                row.add(hb2)
                row.key = key
                lb.add(row)
                self.side_rows[key] = row
            lb.connect("row-selected", self._side_selected)
            rev = Gtk.Revealer()
            rev.add(lb)
            rev.set_transition_duration(150)
            rev.set_reveal_child(gkey not in closed)
            arrow.set_from_icon_name("pan-down-symbolic" if gkey not in closed else "pan-end-symbolic", Gtk.IconSize.MENU)
            head.connect("clicked", lambda _b, g=gkey: self._toggle_group(g))
            self.nav_groups[gkey] = (rev, arrow, keys)
            self.side_lists.append(lb)
            nav.pack_start(head, False, False, 0)
            nav.pack_start(rev, False, False, 0)
        self.side = nav
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(nav)
        self.side_scroll = sw
        paned.pack_start(sw, False, False, 0)
        self.side_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        paned.pack_start(self.side_sep, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(120)
        self.pages = {
            "today": TodayPage(self), "course": CoursePage(self), "alphabet": AlphabetPage(self),
            "review": ReviewPage(self), "dictionary": DictionaryPage(self), "conj": ConjugationPage(self),
            "pron": PronLabPage(self), "dictation": DictationPage(self), "scenes": ScenesPage(self), "bot": BotPage(self), "learner": LearnerPage(self), "readings": ReadingsPage(self), "videos": VideosPage(self),
            "tests": TestsPage(self), "stats": StatsPage(self), "settings": SettingsPage(self),
        }
        for k, p in self.pages.items():
            self.stack.add_named(p, k)
        paned.pack_start(self.stack, True, True, 0)
        win.add(paned)
        win.connect("key-press-event", self._on_key)
        win.connect("delete-event", self._on_close)
        win.show_all()
        self._select_side("today")
        self.update_review_badge()

    # ------------------------------------------------------------ profile użytkowników
    def _profile_button(self):
        from .. import profiles
        cur = profiles.active()
        btn = Gtk.MenuButton()
        btn.set_label("👤 " + profiles.display_name(cur))
        btn.set_tooltip_text(_("Profil użytkownika — osobny postęp dla każdej osoby"))
        pop = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(10)
        box.pack_start(label(_("Profile na tym komputerze"), "dim"), False, False, 0)
        for p in profiles.all_profiles():
            row = Gtk.Box(spacing=4)
            is_cur = p["id"] == cur["id"]
            b = Gtk.Button(label=("✔  " if is_cur else "     ") + profiles.display_name(p))
            b.set_relief(Gtk.ReliefStyle.NONE)
            b.set_halign(Gtk.Align.FILL)
            b.connect("clicked", lambda _b, pid=p["id"], po=pop: (po.popdown(), self.switch_profile(pid)))
            row.pack_start(b, True, True, 0)
            if not is_cur and p["id"] != profiles.DEFAULT_ID:
                rm = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
                rm.set_relief(Gtk.ReliefStyle.NONE)
                rm.set_tooltip_text(_("Usuń profil i jego postęp"))
                rm.connect("clicked", lambda _b, pp=p, po=pop: (po.popdown(), self.delete_profile(pp)))
                row.pack_start(rm, False, False, 0)
            box.pack_start(row, False, False, 0)
        box.pack_start(Gtk.Separator(), False, False, 4)
        new = Gtk.Button(label=_("➕  Nowy profil…"))
        new.set_relief(Gtk.ReliefStyle.NONE)
        new.connect("clicked", lambda *_a: (pop.popdown(), self.new_profile()))
        box.pack_start(new, False, False, 0)
        ren = Gtk.Button(label=_("✎  Nazwa i język bieżącego…"))
        ren.set_relief(Gtk.ReliefStyle.NONE)
        ren.connect("clicked", lambda *_a: (pop.popdown(), self.rename_profile()))
        box.pack_start(ren, False, False, 0)
        pop.add(box)
        box.show_all()
        btn.set_popover(pop)
        return btn

    def _ask_name(self, title, initial="", lang=None):
        """Name (and, with lang, the course language) of a profile; returns (name, lang) or None."""
        d = Gtk.Dialog(title=title, transient_for=self.win, modal=True)
        d.add_button(_("Anuluj"), Gtk.ResponseType.CANCEL)
        ok = d.add_button("OK", Gtk.ResponseType.OK)
        ok.get_style_context().add_class("suggested-action")
        box = d.get_content_area()
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(14)
        box.set_spacing(8)
        box.pack_start(label(_("Nazwa (np. imię):")), False, False, 0)
        e = Gtk.Entry()
        e.set_text(initial)
        e.set_activates_default(True)
        e.set_max_length(30)
        box.pack_start(e, False, False, 0)
        combo = None
        if lang is not None:
            box.pack_start(label(_("Język kursu · Course language:")), False, False, 0)
            combo = Gtk.ComboBoxText()
            for code, name in i18n.LANGS.items():
                combo.append(code, name)
            combo.set_active_id(lang)
            box.pack_start(combo, False, False, 0)
            box.pack_start(label(_("Zmiana języka uruchomi aplikację ponownie."), "dim"), False, False, 0)
        d.set_default_response(Gtk.ResponseType.OK)
        d.show_all()
        r = d.run()
        name = e.get_text().strip()
        chosen = combo.get_active_id() if combo else None
        d.destroy()
        return (name, chosen) if r == Gtk.ResponseType.OK and name else None

    def new_profile(self):
        from .. import profiles
        res = self._ask_name(_("Nowy profil"), lang=i18n.LANG)
        if res:
            pid = profiles.add(res[0], res[1])
            self.switch_profile(pid)

    def rename_profile(self):
        from .. import profiles
        cur = profiles.active()
        res = self._ask_name(_("Zmień nazwę profilu"), profiles.display_name(cur), lang=i18n.profile_lang(cur))
        if res:
            profiles.rename(cur["id"], res[0])
            profiles.set_lang(cur["id"], res[1])
            self.switch_profile(cur["id"], force=True)

    def delete_profile(self, p):
        from .. import profiles
        d = Gtk.MessageDialog(transient_for=self.win, modal=True, message_type=Gtk.MessageType.WARNING,
                              buttons=Gtk.ButtonsType.NONE,
                              text=_('Usunąć profil „{}”?').format(p['name']))
        d.format_secondary_text(_("Cały postęp, powtórki, historia rozmów i dane „O mnie” tego profilu zostaną "
                                "trwale usunięte."))
        d.add_button(_("Anuluj"), Gtk.ResponseType.CANCEL)
        d.add_button(_("Usuń"), Gtk.ResponseType.OK)
        r = d.run()
        d.destroy()
        if r == Gtk.ResponseType.OK:
            profiles.delete(p["id"])
            self.switch_profile(profiles.active_id(), force=True)

    def switch_profile(self, pid, force=False):
        """Przełącza profil bez restartu: nowa baza, nowe okno, stare zamknięte."""
        from .. import profiles
        if pid == profiles.active_id() and not force:
            return
        profiles.set_active(pid)
        if i18n.init() != self._lang:            # another course language: start again in it
            self._restart()
            return
        try:
            self.recorder.stop(lambda _p: None)
        except Exception:  # noqa
            pass
        self.stop_audio()
        self.speech.shutdown()
        old = self.win
        self.db = DB()
        self._migrate_drill()
        self.speech = Speech(self.db)
        self.build_window()          # ustawia self.win na nowe okno
        if old:
            old.destroy()
        self.win.present()
        self.speech.preload_stt()

    def _restart(self):
        try:
            self.recorder.stop(lambda _p: None)
            self.stop_audio()
            self.speech.shutdown()
        except Exception:  # noqa
            pass
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _migrate_drill(self):
        """Jednorazowo przenosi dotychczasowe błędy do treningu (Powtórki → Błędy)."""
        try:
            from .. import drill
            n = drill.migrate_mistakes(self.db, self.course)
            if n:
                print(f"trening błędów: przeniesiono {n} wcześniejszych błędów")
        except Exception as e:  # noqa
            print("migracja treningu błędów:", e)

    def open_review(self, tab="cards"):
        self.show_page("review")
        self.pages["review"].show_tab(tab)

    def _on_close(self, *_a):
        from ..ollama_local import Manager
        Manager.stop()
        self.speech.shutdown()
        self.player.stop()
        return False

    def open_placement(self):
        from .placement import PlacementDialog
        self.db.set("placement_offered", True)
        d = PlacementDialog(self)
        d.connect("destroy", lambda *_a: self.pages["today"].refresh())
        d.show()

    SHORTCUTS = [
        ("Ctrl+1 … Ctrl+9", _("Przejdź do kolejnych ekranów menu")),
        ("F1", _("Ta lista skrótów")),
        ("Ctrl+Q", _("Zakończ")),
        (_("Powtórki: Spacja / Enter"), _("Pokaż odpowiedź")),
        (_("Powtórki: 1 2 3 4"), _("Oceń fiszkę (znowu / trudne / dobrze / łatwe)")),
        (_("Dyktando: F2 / F3 / F4"), _("Posłuchaj / wolno / podpowiedź")),
        (_("Dyktando: Enter"), _("Sprawdź / dalej")),
        (_("Rozmowa z botem: Ctrl+M"), _("Mikrofon: mów / skończ mówić")),
        (_("Scenki: Ctrl+Enter"), _("Następna kwestia")),
    ]

    def show_shortcuts(self, *_a):
        d = Gtk.MessageDialog(transient_for=self.win, modal=True, message_type=Gtk.MessageType.INFO,
                              buttons=Gtk.ButtonsType.CLOSE, text=_("Skróty klawiszowe"))
        d.format_secondary_text("\n".join(f"{k}  —  {v}" for k, v in self.SHORTCUTS))
        d.run()
        d.destroy()

    def _on_key(self, _w, ev):
        ctrl = bool(ev.state & Gdk.ModifierType.CONTROL_MASK)
        page = self.stack.get_visible_child_name()
        kv = ev.keyval
        if kv == Gdk.KEY_F1:
            self.show_shortcuts()
            return True
        if ctrl and Gdk.KEY_1 <= kv <= Gdk.KEY_9:
            idx = kv - Gdk.KEY_1
            if idx < len(PAGES):
                self.show_page(PAGES[idx][0])
                return True
        if ctrl and kv in (Gdk.KEY_m, Gdk.KEY_M) and page == "bot" and self.pages["bot"].conv:
            self.pages["bot"]._mic_clicked()
            return True
        if ctrl and kv in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and page == "scenes":
            nb = getattr(self.pages["scenes"], "next_btn", None)
            if nb is not None and nb.get_sensitive():
                nb.clicked()
                return True
        if page == "dictation" and kv in (Gdk.KEY_F2, Gdk.KEY_F3, Gdk.KEY_F4):
            d = self.pages["dictation"]
            if d.cur:
                if kv == Gdk.KEY_F2:
                    self.say(d.cur[0])
                elif kv == Gdk.KEY_F3:
                    self.say(d.cur[0], slow=True)
                else:
                    d.on_hint()
                return True
        if self.stack.get_visible_child_name() == "review":
            focus = self.win.get_focus()
            if not isinstance(focus, Gtk.Entry):
                return self.pages["review"].on_key(ev.keyval)
        return False

    def _toggle_group(self, gkey):
        rev, arrow, _keys = self.nav_groups[gkey]
        show = not rev.get_reveal_child()
        rev.set_reveal_child(show)
        arrow.set_from_icon_name("pan-down-symbolic" if show else "pan-end-symbolic", Gtk.IconSize.MENU)
        closed = set(self.db.get("nav_closed", []) or [])
        (closed.discard if show else closed.add)(gkey)
        self.db.set("nav_closed", sorted(closed))

    def _select_side(self, key, notify=True):
        """Zaznacza pozycję menu (w jej grupie, inne grupy bez zaznaczenia); rozwija zwiniętą grupę."""
        row = self.side_rows.get(key)
        self._nav_lock = not notify
        try:
            for lb in self.side_lists:
                if row is None or row.get_parent() is not lb:
                    lb.unselect_all()
            if row is not None:
                for gkey, (rev, _a, keys) in self.nav_groups.items():
                    if key in keys and not rev.get_reveal_child():
                        self._toggle_group(gkey)
                row.get_parent().select_row(row)
        finally:
            self._nav_lock = False

    def update_review_badge(self):
        b = getattr(self, "review_badge", None)
        if b is None:
            return
        due, new = self.db.count_due()
        n = due + min(new, int(self.db.get("new_per_day", 20)))
        b.set_text(str(n))
        b.set_visible(n > 0)

    def _side_selected(self, lb, row):
        if row is None:
            return
        for other in self.side_lists:          # jedna zaznaczona pozycja w całym menu
            if other is not lb:
                other.unselect_all()
        if self._nav_lock:
            return
        key = row.key
        if key in ("review", "stats", "learner"):
            self.pages[key].refresh()
        if key == "bot" and not self.pages["bot"].conv:
            self.pages["bot"].show_start()
        if key == "today":
            self.pages["today"].refresh()
        self.set_focus_mode(False)
        self.stack.set_visible_child_name(key)

    def show_page(self, key):
        row = self.side_rows.get(key)
        if row and not row.is_selected():
            self._select_side(key)
        else:
            if row is None:
                self._select_side(None)
            if key in ("review", "stats", "today", "learner"):
                self.pages[key].refresh()
            self.set_focus_mode(False)
            self.stack.set_visible_child_name(key)

    def set_focus_mode(self, on):
        """Tryb skupienia (ćwiczenia w lekcji): bez menu bocznego."""
        if getattr(self, "side_scroll", None) is None:
            return
        self.side_scroll.set_visible(not on)
        self.side_sep.set_visible(not on)

    def _show_dynamic(self, widget, name, sidebar_key):
        old = self.stack.get_child_by_name(name)
        if old:
            self.stack.remove(old)
            old.destroy()
        self.stack.add_named(widget, name)
        widget.show_all()
        if hasattr(widget, "stack"):
            widget.stack.set_visible_child_name("intro")
        self._select_side(sidebar_key, notify=False)
        self.stack.set_visible_child_name(name)

    # ------------------------------------------------------------ nawigacja
    def open_lesson(self, lesson_id, tab="intro"):
        lv = LessonView(self, self.course.by_id[lesson_id])
        self._show_dynamic(lv, "lesson", "course")
        lv.stack.set_visible_child_name(tab or "intro")
        lv.track = True

    def start_unit_test(self, level, unit):
        items = build_unit_test(self.course, level, unit)
        title = _('Test — {}, dział {}: {}').format(level, unit, self.course.unit_title(level, unit))
        self._show_dynamic(TestView(self, "unit", f"{level}-{unit}", title, items), "test", "tests")

    def start_exam(self, level):
        items = build_exam(self.course, level)
        sentences = [es for l in self.course.lessons if l.level == level
                     for _u, es, _u in l.dialog if 4 <= len(es.split()) <= 10]
        speak = random.sample(sentences, min(3, len(sentences)))
        self._show_dynamic(TestView(self, "exam", level, _('Egzamin próbny — poziom {}').format(level), items, speak),
                           "test", "tests")

    def open_conjugation(self, verb):
        self.show_page("conj")
        self.pages["conj"].show_verb(verb)

    def open_pron_lab(self, text):
        self.show_page("pron")
        self.pages["pron"].set_target(text, "")

    def open_setup(self):
        SetupDialog(self, self.win)

    def refresh_today(self):
        if self.stack.get_visible_child_name() == "today":
            self.pages["today"].refresh()

    def refresh_all(self):
        self.update_review_badge()
        for k in ("today", "course", "tests", "settings"):
            try:
                self.pages[k].refresh()
            except Exception as e:  # noqa
                print("refresh", k, e)

    # ------------------------------------------------------------ audio
    def say(self, text, slow=False):
        self._seq_token += 1
        self._play_text(text, slow, self._seq_token)

    def _play_text(self, text, slow, token, then=None):
        def done(path):
            if token != self._seq_token:
                return
            self.player.play(path, on_done=then)

        def err(e):
            self.toast(_('Nie mogę odtworzyć: {}').format(e))
        run_bg(lambda: self.speech.synth(text, slow), done, err)

    def say_sequence(self, texts):
        self._seq_token += 1
        token = self._seq_token
        texts = list(texts)

        def step(i=0):
            if token != self._seq_token or i >= len(texts):
                return
            self._play_text(texts[i], False, token,
                            then=lambda: GLib.timeout_add(350, lambda: (step(i + 1), False)[1]))
        step()
        # przygotuj kolejne nagrania w tle
        run_bg(lambda: [self.speech.synth(t) for t in texts[1:]], lambda _r: None, lambda _e: None)

    def stop_audio(self):
        self._seq_token += 1
        self.player.stop()

    def toast(self, text):
        print(text, file=sys.stderr)
        if not self.win or getattr(self, "_toast_open", False):
            return
        if "silnika mowy" in text or _("Brak") in text:
            if getattr(self, "_engine_warned", False):
                return
            self._engine_warned = True
        self._toast_open = True
        dlg = Gtk.MessageDialog(transient_for=self.win, modal=True, message_type=Gtk.MessageType.INFO,
                                buttons=Gtk.ButtonsType.OK, text=text)
        if "silnika mowy" in text or _("Brak") in text:
            dlg.format_secondary_text(_("Przejdź do Ustawień i kliknij „Zainstaluj / zaktualizuj komponenty”."))
        dlg.run()
        dlg.destroy()
        self._toast_open = False

    # ------------------------------------------------------------ o programie
    def on_about(self, *_a):
        d = Gtk.AboutDialog(transient_for=self.win, modal=True)
        d.set_program_name(APP_NAME)
        d.set_version(VERSION)
        d.set_logo_icon_name(ICON + ("-dark" if self.is_dark() else ""))
        d.set_comments(_("Prawdziwy kurs hiszpańskiego od zera (A1–A2, hiszpański z Hiszpanii)\n"
                       "z lekcjami, słownikiem ES–PL, powtórkami FSRS, testami i oceną wymowy offline.\n\n"
                       "Created by: JGu\nSupported by Claude"))
        d.set_authors(["Created by: JGu", "Supported by Claude"])
        d.set_website("https://github.com/jgu-linux-apps")
        d.set_website_label("JGu Linux Apps")
        d.set_license_type(Gtk.License.CUSTOM)
        d.set_license(_("Freeware — darmowe użytkowanie.\nBez prawa do modyfikacji i rozpowszechniania zmienionych wersji.\n\n"
                      "Komponenty pobierane osobno (Piper, faster-whisper, głosy, modele Whisper)\n"
                      "mają własne licencje."))
        d.add_credit_section(_("Wykorzystane projekty"), [
            _("Piper TTS — synteza mowy (OHF-Voice, GPL-3.0, pobierany osobno)"),
            _("Głosy es_ES davefx i sharvard (piper-voices)"),
            _("faster-whisper / OpenAI Whisper — rozpoznawanie mowy"),
            _("FSRS — algorytm powtórek (open-spaced-repetition)"),
        ])
        d.run()
        d.destroy()


def main():
    app = App()
    return app.run(sys.argv)
