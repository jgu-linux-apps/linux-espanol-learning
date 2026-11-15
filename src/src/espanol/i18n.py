"""Course language: Polish (texts in the code and data/) or English (EN table below, data/en/).

The language belongs to the learner's profile (profiles.json, "lang"); a profile without it follows the
system language. ESPANOL_LANG=pl|en forces one (tests, screenshots). init() runs before the UI modules
are imported, because some of them translate texts at import time; switching to a profile with another
language restarts the app."""
import os

LANGS = {"pl": "Polski", "en": "English"}
LANG = "pl"


def system_lang():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var, "")
        if v:
            return "pl" if v.startswith("pl") else "en"
    return "en"


def profile_lang(profile):
    lang = (profile or {}).get("lang")
    return lang if lang in LANGS else system_lang()


def init(lang=None):
    """Sets LANG: ESPANOL_LANG, then the given language, then the active profile's language."""
    global LANG
    forced = os.environ.get("ESPANOL_LANG")
    if forced in LANGS:
        LANG = forced
    elif lang in LANGS:
        LANG = lang
    else:
        try:
            from . import profiles
            LANG = profile_lang(profiles.active())
        except Exception:  # noqa
            LANG = system_lang()
    return LANG


def _(s):
    if LANG == "en":
        from .i18n_en import EN
        return EN.get(s, s)
    return s


def plural(n, one, few, many):
    """Polish number forms (1 zadanie, 2 zadania, 5 zadań); in English only one / many.
    The three forms are Polish source texts, translated through _()."""
    if LANG != "pl":
        return _(one) if n == 1 else _(many)
    if n == 1:
        return one
    return few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many


def data_path(*parts):
    """A data file in the course language: data/en/... when it exists, otherwise the Polish data/..."""
    from .paths import DATA
    if LANG != "pl":
        p = os.path.join(DATA, LANG, *parts)
        if os.path.exists(p):
            return p
    return os.path.join(DATA, *parts)
