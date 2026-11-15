from ..i18n import _  # noqa: E402
"""Motywy kolorystyczne aplikacji — każdy w wersji jasnej i ciemnej."""

THEMES = {
    # klucz „system” = motyw domyślny (dawniej pomarańcz/cyjan; od 1.13 Coral — ten sam odcień w jasnym i ciemnym)
    "system": (
        _("Coral (domyślny) — koral i słońce"),
        dict(bg="#FFF7F5", fg="#2A1B19", header="#FFECE8", header_fg="#3A2420", sidebar="#FFEDE9",
             card="#FFFFFF", border="#F7D6CF", accent="#E8505B", accent_fg="#FFFFFF", button="#FFFFFF",
             hover="#FFE0D9", sel="#E8505B", sel_fg="#FFFFFF", entry="#FFFFFF", extra="coral_light",
             accent2="#F59E0B", ring2="#F43F5E", ring3="#0EA5E9"),
        dict(bg="#1A1416", fg="#F5E6E8", header="#151012", header_fg="#F5E6E8", sidebar="#1A1416",
             card="#241B1E", border="#3C2C31", accent="#FB7185", accent_fg="#2A0A10", button="#2A2024",
             hover="#3A2830", sel="#FB7185", sel_fg="#2A0A10", entry="#201719", extra="coral_dark",
             accent2="#FBBF24", ring2="#F43F5E", ring3="#A78BFA"),
    ),
    "pomarancz": (
        _("Pomarańcz — ciepły pomarańcz (dawny domyślny)"),
        dict(bg="#FFF8F3", fg="#1F2937", header="#FFEFE4", header_fg="#3B2A20", sidebar="#FFEEE3",
             card="#FFFFFF", border="#F6DCCB", accent="#F97316", accent_fg="#FFFFFF", button="#FFFFFF",
             hover="#FFE3D0", sel="#F97316", sel_fg="#FFFFFF", entry="#FFFFFF", extra="soft",
             accent2="#F59E0B", ring2="#F43F5E", ring3="#0EA5E9"),
        dict(bg="#1A1410", fg="#F3E8DF", header="#15100C", header_fg="#F3E8DF", sidebar="#1A1410",
             card="#251C16", border="#3D2E24", accent="#FB923C", accent_fg="#2A1405", button="#2B211A",
             hover="#3A2C22", sel="#FB923C", sel_fg="#2A1405", entry="#201812", extra="soft_dark",
             accent2="#FBBF24", ring2="#FB7185", ring3="#38BDF8"),
    ),
    "mar": (
        "Mediterráneo — morski turkus",
        dict(bg="#F2FAF9", fg="#12302D", header="#E3F4F2", header_fg="#12302D", sidebar="#E3F4F2",
             card="#FFFFFF", border="#C7E6E2", accent="#0D9488", accent_fg="#FFFFFF", button="#FFFFFF",
             hover="#D2EEEA", sel="#0D9488", sel_fg="#FFFFFF", entry="#FFFFFF", extra="mar_light",
             accent2="#0EA5E9", ring2="#F43F5E", ring3="#6366F1"),
        dict(bg="#0B1A1D", fg="#E2F2F0", header="#0A1517", header_fg="#E2F2F0", sidebar="#0B1A1D",
             card="#10252A", border="#1E3B40", accent="#2DD4BF", accent_fg="#06201E", button="#142C30",
             hover="#16363B", sel="#2DD4BF", sel_fg="#06201E", entry="#0D2124", extra="mar_dark",
             accent2="#38BDF8", ring2="#FB7185", ring3="#A78BFA"),
    ),
    "classic": ("Systemowy — jasny/ciemny jak Ubuntu", None, None),
    # Aurora: wspólny motyw całej serii (jasny = pastelowe szkło, ciemny = zorza na granacie)
    "aurora": (
        _("Aurora — fiolet i cyjan"),
        dict(bg="#F4F1FF", fg="#1F1A3A", header="#FBFAFF", header_fg="#1F1A3A", sidebar="#EEEAFF",
             card="#FFFFFF", border="#E2DCFA", accent="#7C5CFF", accent_fg="#FFFFFF", button="#FFFFFF",
             hover="#ECE7FF", sel="#7C5CFF", sel_fg="#FFFFFF", entry="#FFFFFF", extra="aurora_light"),
        dict(bg="#0C0E1A", fg="#ECEBFF", header="#10132A", header_fg="#ECEBFF", sidebar="#0E1122",
             card="#14172A", border="#252A45", accent="#8B5CF6", accent_fg="#FFFFFF", button="#181C33",
             hover="#1E2340", sel="#3A2A6E", sel_fg="#FFFFFF", entry="#11142A", extra="aurora_dark"),
    ),
    "espana": (
        _("España — czerwień i złoto"),
        dict(bg="#FFF8EC", fg="#2B1D14", header="#AA151B", header_fg="#FFFFFF", sidebar="#F7E9CC",
             card="#FFFFFF", border="#E8D3A8", accent="#C8102E", accent_fg="#FFFFFF", button="#FBEFD6",
             hover="#F5E2BC", sel="#F1BF00", sel_fg="#2B1D14", entry="#FFFFFF"),
        dict(bg="#1E1513", fg="#F3E6D3", header="#6E0E14", header_fg="#FFF2D6", sidebar="#2A1C18",
             card="#2E211D", border="#4A3128", accent="#E0A800", accent_fg="#1E1513", button="#3A2A24",
             hover="#4A3630", sel="#AA151B", sel_fg="#FFF2D6", entry="#261B18"),
    ),
    "azulejo": (
        _("Azulejo — błękit sewilskich kafli"),
        dict(bg="#F4F8FC", fg="#12263F", header="#1F4E8C", header_fg="#FFFFFF", sidebar="#E3ECF7",
             card="#FFFFFF", border="#C9D8EC", accent="#1F5FAF", accent_fg="#FFFFFF", button="#E9F0F9",
             hover="#DAE6F4", sel="#1F5FAF", sel_fg="#FFFFFF", entry="#FFFFFF"),
        dict(bg="#0F1724", fg="#DCE6F4", header="#13294A", header_fg="#E6EEF9", sidebar="#152238",
             card="#1A2A42", border="#2A3F60", accent="#5B9BE6", accent_fg="#0F1724", button="#22344F",
             hover="#2C4263", sel="#2F64A8", sel_fg="#FFFFFF", entry="#132033"),
    ),
    "oliva": (
        _("Oliva — oliwka i terakota Andaluzji"),
        dict(bg="#F5F3EA", fg="#2C2A1E", header="#5B6B2E", header_fg="#FFFFFF", sidebar="#E8E6D2",
             card="#FFFFFF", border="#D6D2B5", accent="#C0603A", accent_fg="#FFFFFF", button="#ECE9D8",
             hover="#E0DCC4", sel="#5B6B2E", sel_fg="#FFFFFF", entry="#FFFFFF"),
        dict(bg="#1A1B14", fg="#E8E6D5", header="#3A4520", header_fg="#F0EEDC", sidebar="#23251B",
             card="#2A2C20", border="#44472F", accent="#D9824F", accent_fg="#1A1B14", button="#34372A",
             hover="#414533", sel="#5B6B2E", sel_fg="#F0EEDC", entry="#202218"),
    ),
}

def _grad(a1, a2, dark):
    """Wspólne akcenty palet z gradientem (Coral, Pomarańcz ciemny, Mediterráneo): ten sam odcień w jasnym i ciemnym."""
    return MODERN + f"""
.navigation-sidebar row:selected {{ background-image: linear-gradient(to right, {a1}, {a2});
    box-shadow: 0 4px 12px alpha({a1}, {0.30 if dark else 0.35}); }}
.navigation-sidebar row:selected label {{ font-weight: bold; }}
.hero-banner {{ background-image: linear-gradient(to right, {a1}, {a2}); box-shadow: 0 6px 18px alpha({a1}, 0.30); }}
.hero-banner label {{ color: #FFFFFF; }}
button.suggested-action {{ background-image: linear-gradient(to right, {a1}, {a2}); border-color: {a1};
    box-shadow: 0 4px 12px alpha({a1}, 0.30); }}
progressbar progress {{ background-image: linear-gradient(to right, {a1}, {a2}); }}
.card {{ box-shadow: 0 2px 10px alpha({a1}, {0.10 if dark else 0.07}); }}
"""


MODES = {"auto": _("Automatycznie (jak system)"), "light": _("Zawsze jasny"), "dark": _("Zawsze ciemny")}


MODERN = """
.card { border-radius: 18px; padding: 18px; }
button { border-radius: 12px; padding: 7px 14px; }
.accent-btn { padding: 2px 6px; border-radius: 9px; }
entry, spinbutton { border-radius: 12px; min-height: 36px; }
combobox button { border-radius: 12px; }
.badge { border-radius: 10px; padding: 2px 10px; }
.navigation-sidebar row { border-radius: 14px; margin: 3px 10px; }
.sidebar-row { padding: 9px 10px; }
button.suggested-action label { background-color: transparent; }
.navigation-sidebar row:selected label, .navigation-sidebar row:selected image { background-color: transparent; }
.hero-banner { border-radius: 22px; padding: 24px; }
stackswitcher button { border-radius: 0; }
stackswitcher button:first-child { border-radius: 12px 0 0 12px; }
stackswitcher button:last-child { border-radius: 0 12px 12px 0; }
progressbar trough, progressbar progress { border-radius: 6px; min-height: 8px; }
"""
EXTRA = {
    "coral_light": _grad("#E8505B", "#F59E0B", False),
    "coral_dark": _grad("#FB7185", "#FBBF24", True),
    "soft_dark": _grad("#F97316", "#F59E0B", True),
    "mar_light": _grad("#0D9488", "#0EA5E9", False),
    "mar_dark": _grad("#2DD4BF", "#38BDF8", True),
    "soft": MODERN + """
.navigation-sidebar row:selected { background-image: linear-gradient(to right, #F97316, #FB923C);
    box-shadow: 0 4px 12px alpha(#F97316, 0.35); }
.navigation-sidebar row:selected label { font-weight: bold; }
.hero-banner { background-image: linear-gradient(to right, #F97316, #F59E0B);
    box-shadow: 0 6px 18px alpha(#F97316, 0.30); }
.hero-banner label { color: #FFFFFF; }
button.suggested-action { background-image: linear-gradient(to right, #F97316, #FB923C); border-color: #F97316; }
.card { box-shadow: 0 2px 10px alpha(#F97316, 0.07); }
""",
    "aurora_light": MODERN + """
window.background { background-image: linear-gradient(135deg, #F6F2FF 0%, #EEF8FF 55%, #FFF4F8 100%); }
headerbar, .titlebar { box-shadow: inset 0 -1px alpha(#7C5CFF, 0.12); }
.navigation-sidebar row:selected { background-image: linear-gradient(to right, #7C5CFF, #22B8E6);
    box-shadow: 0 6px 18px alpha(#7C5CFF, 0.30); }
.navigation-sidebar row:selected label { font-weight: bold; }
.navigation-sidebar row:hover:not(:selected) { background-color: #FFFFFF;
    box-shadow: 0 0 0 1px alpha(#7C5CFF, 0.55), 0 4px 14px alpha(#7C5CFF, 0.22); }
.hero-banner { background-image: linear-gradient(135deg, #7C5CFF, #22B8E6); box-shadow: 0 6px 18px alpha(#7C5CFF, 0.30); }
.hero-banner label { color: #FFFFFF; }
.hero-banner .badge { background-color: alpha(#FFFFFF, 0.22); color: #FFFFFF; }
button.suggested-action { background-image: linear-gradient(to right, #7C5CFF, #22B8E6); border-color: #7C5CFF;
    box-shadow: 0 4px 14px alpha(#7C5CFF, 0.35); }
.card { box-shadow: 0 2px 10px alpha(#7C5CFF, 0.08); }
.card:hover { border-color: alpha(#7C5CFF, 0.55); box-shadow: 0 3px 14px alpha(#7C5CFF, 0.20); }
progressbar progress { background-image: linear-gradient(to right, #7C5CFF, #22B8E6); }
switch:checked { border-color: #7C5CFF; }
""",
    "aurora_dark": MODERN + """
window.background { background-image: radial-gradient(ellipse at 12% 0%, alpha(#22D3EE, 0.20), transparent 55%),
    radial-gradient(ellipse at 100% 100%, alpha(#A855F7, 0.24), transparent 55%); }
headerbar, .titlebar { box-shadow: inset 0 -1px alpha(#FFFFFF, 0.07); }
.navigation-sidebar row:selected { background-image: linear-gradient(to right, alpha(#A855F7, 0.60), alpha(#22D3EE, 0.48));
    box-shadow: 0 6px 18px alpha(#A855F7, 0.30); }
.navigation-sidebar row:hover:not(:selected) { background-color: alpha(#FFFFFF, 0.05);
    box-shadow: 0 0 0 1px alpha(#22D3EE, 0.55), 0 0 18px alpha(#22D3EE, 0.28); }
.hero-banner { background-image: linear-gradient(135deg, alpha(#A855F7, 0.55), alpha(#22D3EE, 0.40));
    border: 1px solid alpha(#22D3EE, 0.35); }
.hero-banner label { color: #FFFFFF; }
.hero-banner .badge { background-color: alpha(#22D3EE, 0.15); color: #A5F3FC; border: 1px solid alpha(#22D3EE, 0.5); }
button.suggested-action { background-image: linear-gradient(to right, #A855F7, #22D3EE); border-color: #A855F7;
    box-shadow: 0 0 16px alpha(#A855F7, 0.45); }
.card:hover { border-color: alpha(#22D3EE, 0.55); box-shadow: 0 0 16px alpha(#22D3EE, 0.20); }
progressbar progress { background-image: linear-gradient(to right, #A855F7, #22D3EE); box-shadow: 0 0 8px alpha(#22D3EE, 0.5); }
switch:checked { border-color: #8B5CF6; }
""",
    "glass": MODERN + """
.navigation-sidebar row:selected { background-image: linear-gradient(to right, alpha(#22D3EE, 0.30), alpha(#22D3EE, 0.08));
    border: 1px solid alpha(#22D3EE, 0.55); box-shadow: 0 0 16px alpha(#22D3EE, 0.30), inset 3px 0 0 #22D3EE; }
.navigation-sidebar row:selected label, .navigation-sidebar row:selected image { color: #A5F3FC; }
.hero-banner { background-image: none; background-color: #141C2E; border: 1px solid #26334D; }
.hero-banner .badge { background-color: alpha(#22D3EE, 0.15); color: #67E8F9; border: 1px solid alpha(#22D3EE, 0.5); }
button.suggested-action { box-shadow: 0 0 14px alpha(#22D3EE, 0.25); }
.title2 { color: #F1F5F9; }
""",
}


def _fx(p):
    """Subtelne efekty dla motywów kolorystycznych: poświata akcentu, delikatne gradienty, płynne przejścia."""
    a, ha = p["accent"], p["header"]
    return f"""
button, entry, .card {{ transition: all 160ms ease-out; }}
.navigation-sidebar row {{ transition: all 160ms ease-out; border-radius: 12px; margin: 2px 8px; }}
.navigation-sidebar row:selected {{ background-image: linear-gradient(to right, alpha({a}, 0.95), alpha({a}, 0.70));
    box-shadow: 0 2px 10px alpha({a}, 0.38); }}
.navigation-sidebar row:selected label, .navigation-sidebar row:selected image {{ background-color: transparent; }}
.navigation-sidebar row:hover:not(:selected) {{ box-shadow: inset 3px 0 0 alpha({a}, 0.7); }}
.card {{ border-radius: 14px; box-shadow: 0 1px 8px alpha({a}, 0.10); }}
.card:hover {{ border-color: alpha({a}, 0.55); box-shadow: 0 3px 14px alpha({a}, 0.20); }}
.hero-banner {{ border-radius: 18px; padding: 22px;
    background-image: linear-gradient(135deg, {ha}, shade({a}, 0.85));
    box-shadow: 0 6px 20px alpha({a}, 0.30); }}
.hero-banner label {{ color: #FFFFFF; }}
.hero-banner .badge {{ background-color: alpha(#FFFFFF, 0.20); color: #FFFFFF; }}
button {{ border-radius: 10px; }}
button.suggested-action label {{ background-color: transparent; }}
button.suggested-action {{ background-image: linear-gradient(to bottom, shade({a}, 1.10), {a});
    box-shadow: 0 2px 8px alpha({a}, 0.40); }}
button.suggested-action:hover {{ box-shadow: 0 0 0 3px alpha({a}, 0.25), 0 3px 12px alpha({a}, 0.5); }}
entry:focus {{ box-shadow: 0 0 0 3px alpha({a}, 0.22), inset 0 0 0 1px {a}; }}
progressbar progress {{ background-image: linear-gradient(to right, shade({a}, 0.9), shade({a}, 1.15));
    box-shadow: 0 0 8px alpha({a}, 0.55); border-radius: 6px; }}
progressbar trough {{ border-radius: 6px; }}
switch:checked {{ box-shadow: 0 0 8px alpha({a}, 0.5); }}
notebook > header tab:checked {{ box-shadow: inset 0 -3px {a}; }}
"""


def css(p):
    """Arkusz CSS GTK3 dla palety p."""
    extra = p.get("extra")
    return _base(p) + _fx(p) + EXTRA.get(extra, "")


def _base(p):
    return f"""
@define-color theme_bg_color {p['bg']};
@define-color theme_fg_color {p['fg']};
@define-color theme_base_color {p['card']};
@define-color theme_text_color {p['fg']};
@define-color theme_selected_bg_color {p['accent']};
@define-color theme_selected_fg_color {p['accent_fg']};
@define-color borders {p['border']};

window, .background, dialog, messagedialog, .dialog-vbox {{ background-color: {p['bg']}; color: {p['fg']}; }}
label {{ color: inherit; }}
scrolledwindow, viewport, stack, box, grid, flowbox, flowboxchild {{ background-color: transparent; }}

headerbar, .titlebar {{ background-image: none; background-color: {p['header']}; color: {p['header_fg']};
    border-color: {p['header']}; box-shadow: none; }}
headerbar label, headerbar .title, headerbar .subtitle {{ color: {p['header_fg']}; }}
headerbar button, headerbar button image {{ color: {p['header_fg']}; }}
headerbar button {{ background-image: none; background-color: transparent; border-color: transparent; box-shadow: none; }}
headerbar button:hover {{ background-color: alpha({p['header_fg']}, 0.15); }}

list, list row {{ background-color: transparent; color: {p['fg']}; }}
scrolledwindow > viewport > list.navigation-sidebar, .navigation-sidebar {{ background-color: {p['sidebar']}; }}
list row:hover {{ background-color: {p['hover']}; }}
list row:selected, list row:selected label, list row:selected image {{ background-color: {p['sel']}; color: {p['sel_fg']}; }}

.card {{ background-color: {p['card']}; border: 1px solid {p['border']}; }}
.badge {{ background-color: alpha({p['accent']}, 0.16); color: {p['fg']}; }}
separator {{ background-color: {p['border']}; }}

button {{ background-image: none; background-color: {p['button']}; color: {p['fg']};
    border: 1px solid {p['border']}; box-shadow: none; text-shadow: none; }}
button:hover {{ background-color: {p['hover']}; }}
button:checked, button:active {{ background-color: alpha({p['accent']}, 0.22); }}
button:disabled, button:disabled label {{ color: alpha({p['fg']}, 0.45); background-color: alpha({p['button']}, 0.6); }}
button.suggested-action, button.suggested-action label {{ background-color: {p['accent']}; color: {p['accent_fg']};
    border-color: {p['accent']}; }}
button.suggested-action:hover {{ background-color: shade({p['accent']}, 1.08); }}
button.suggested-action:disabled, button.suggested-action:disabled label {{ background-color: alpha({p['accent']}, 0.45);
    color: alpha({p['accent_fg']}, 0.7); }}
button.destructive-action, button.destructive-action label {{ background-color: #C0392B; color: #FFFFFF; border-color: #C0392B; }}
button link, .link, *:link {{ color: {p['accent']}; }}
stackswitcher button:checked, stackswitcher button:checked label {{ background-color: {p['accent']}; color: {p['accent_fg']}; }}

entry, spinbutton, textview, textview text {{ background-image: none; background-color: {p['entry']}; color: {p['fg']};
    border-color: {p['border']}; }}
entry:focus {{ border-color: {p['accent']}; box-shadow: inset 0 0 0 1px {p['accent']}; }}
entry selection, textview text selection, label selection {{ background-color: {p['accent']}; color: {p['accent_fg']}; }}

combobox button, combobox button label {{ background-color: {p['button']}; color: {p['fg']}; }}
menu, .menu, popover, popover.background, .popover {{ background-color: {p['card']}; color: {p['fg']}; border-color: {p['border']}; }}
menuitem:hover, modelbutton:hover {{ background-color: {p['hover']}; }}
menuitem label, modelbutton label {{ color: {p['fg']}; }}

notebook, notebook > stack {{ background-color: {p['bg']}; }}
notebook > header {{ background-color: {p['sidebar']}; border-color: {p['border']}; }}
notebook > header tab label {{ color: alpha({p['fg']}, 0.75); }}
notebook > header tab:checked {{ box-shadow: inset 0 -3px {p['accent']}; }}
notebook > header tab:checked label {{ color: {p['fg']}; }}

progressbar trough, levelbar trough {{ background-color: alpha({p['fg']}, 0.12); border-color: transparent; }}
progressbar progress, levelbar block.filled {{ background-image: none; background-color: {p['accent']}; border-color: {p['accent']}; }}
switch {{ background-color: alpha({p['fg']}, 0.15); }}
switch:checked {{ background-color: {p['accent']}; }}
checkbutton check:checked {{ background-color: {p['accent']}; color: {p['accent_fg']}; border-color: {p['accent']}; }}
scrollbar slider {{ background-color: alpha({p['fg']}, 0.35); }}
tooltip, tooltip.background {{ background-color: {p['header']}; color: {p['header_fg']}; }}
tooltip label {{ color: {p['header_fg']}; }}
"""
