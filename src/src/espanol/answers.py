"""Sprawdzanie odpowiedzi: tolerancja dla wielkości liter, interpunkcji
i (z ostrzeżeniem) brakujących akcentów."""
import re
import unicodedata
import difflib

PUNCT = re.compile(r"[¿?¡!.,;:«»\"“”()\-–—…]")


def strip_accents(s):
    s = s.replace("ñ", "\0").replace("Ñ", "\1")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("\0", "ñ").replace("\1", "Ñ")


def norm(s, accents=True):
    s = s.strip().lower().replace("’", "'")
    s = PUNCT.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not accents:
        s = strip_accents(s)
    return s


OK, ACCENT, TYPO, WRONG = "ok", "accent", "typo", "wrong"


def check(given, accepted):
    """accepted: lista poprawnych odpowiedzi. Zwraca (wynik, najlepsza_odpowiedź)."""
    if isinstance(accepted, str):
        accepted = [a for a in accepted.split("|")]
    accepted = [a.strip() for a in accepted if a.strip()]
    g = norm(given)
    if not g:
        return WRONG, accepted[0] if accepted else ""
    for a in accepted:
        if norm(a) == g:
            return OK, a
    for a in accepted:
        if norm(a, False) == norm(given, False):
            return ACCENT, a
    # literówka: jedna drobna różnica w dłuższej odpowiedzi
    best, ratio = accepted[0], 0
    for a in accepted:
        r = difflib.SequenceMatcher(None, norm(a, False), norm(given, False)).ratio()
        if r > ratio:
            best, ratio = a, r
    na = norm(best, False)
    if len(na) >= 8 and _edit_distance(na, norm(given, False)) == 1:
        return TYPO, best
    return WRONG, best


def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def word_diff(target, heard):
    """Porównanie słowo po słowie (do oceny wymowy).
    Zwraca listę (słowo_docelowe, ok:bool) i wynik 0-100."""
    t_orig = target.split()
    t = [norm(w, False) for w in t_orig]
    h = [norm(w, False) for w in heard.split()]
    h = [w for w in h if w]
    sm = difflib.SequenceMatcher(None, t, h)
    ok = [False] * len(t)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                ok[k] = True
        elif tag == "replace":
            # podobne słowo (np. drobna różnica) liczymy jako poprawne
            for k, m in zip(range(i1, i2), range(j1, j2)):
                if difflib.SequenceMatcher(None, t[k], h[m]).ratio() >= 0.85:
                    ok[k] = True
    words = [(w, ok[i]) for i, w in enumerate(t_orig) if t[i]]
    if not words:
        return [], 0
    score = round(100 * sum(1 for _, o in words if o) / len(words))
    return words, score


# Typowe trudności Polaka w wymowie hiszpańskiej (hiszpański z Hiszpanii)
TIPS = [
    ("rr", "„rr” to długie, wibrujące r (kilka uderzeń języka) — dłuższe niż polskie r."),
    ("ll", "„ll” wymawiaj jak polskie „j” (w wielu regionach Hiszpanii) — nie jak „l”."),
    ("ñ", "„ñ” brzmi jak polskie „ń” w słowie „koń”, przed samogłoską: „niña” ≈ „ninia”."),
    ("j", "„j” to mocne, gardłowe „ch”, mocniejsze niż polskie."),
    ("z", "W Hiszpanii „z” (oraz „ce”, „ci”) wymawia się jak angielskie „th” w „think”."),
    ("ce", "„ce” wymawiaj jak „the” z angielskim „th” (bezdźwięcznym): cena ≈ „thena”."),
    ("ci", "„ci” wymawiaj jak „thi” (bezdźwięczne th): cine ≈ „thine”."),
    ("h", "„h” jest nieme — hola = „ola”."),
    ("v", "„v” brzmi tak samo jak „b” — nie wymawiaj go jak polskie „w”."),
    ("qu", "„qu” to po prostu „k” — „que” = „ke”, „u” jest nieme."),
    ("gue", "W „gue/gui” litera „u” jest niema: guitarra = „gitarra”."),
    ("gi", "„gi/ge” wymawiaj jak gardłowe „chi/che”: gente = „chente”."),
    ("ge", "„ge/gi” wymawiaj jak gardłowe „che/chi”: gente = „chente”."),
    ("e", "Hiszpańskie „e” jest bardziej zamknięte niż polskie — krótkie i czyste."),
    ("y", "„y” na końcu słowa to „i” (muy = „mui”), a przed samogłoską — jak „j”."),
]


# the same tips for English speakers (other traps: the English r, v, puffed p/t/k, gliding vowels)
TIPS_EN = [
    ("rr", "“rr” is a long trilled r (several taps of the tongue) — nothing like the English r."),
    ("ll", "Say “ll” like the “y” in “yes” (in most of Spain) — not like “l”."),
    ("ñ", "“ñ” sounds like the “ny” in “canyon”: “niña” ≈ “neen-ya”."),
    ("j", "“j” is a strong “h” from the back of the throat, like Scottish “loch”."),
    ("z", "In Spain “z” (and “ce”, “ci”) sounds like the “th” in “think”."),
    ("ce", "Say “ce” with the “th” of “think”: cena ≈ “thay-na”."),
    ("ci", "Say “ci” with the “th” of “think”: cine ≈ “thee-nay”."),
    ("h", "“h” is silent — hola = “ola”."),
    ("v", "“v” sounds exactly like “b” — never the English “v”."),
    ("qu", "“qu” is just “k” — “que” = “ke”, the “u” is silent."),
    ("gue", "In “gue/gui” the “u” is silent: guitarra = “gitarra”."),
    ("gi", "Say “gi/ge” with the throaty “h” of “j”: gente = “hen-te”."),
    ("ge", "Say “ge/gi” with the throaty “h” of “j”: gente = “hen-te”."),
    ("r", "A single “r” inside a word is one quick tap, like the “tt” in American “butter”."),
    ("e", "Spanish “e” is short and pure, as in “bed” — don't glide it into “ay”."),
    ("o", "Spanish “o” is short and pure, as in “not” — don't glide it into “oh-oo”."),
    ("y", "“y” at the end of a word is “ee” (muy = “mwee”), before a vowel like the “y” in “yes”."),
]


def tips_for(words):
    """Podpowiedzi dla słów wymówionych niepoprawnie."""
    out = []
    seen = set()
    for w in words:
        lw = w.lower()
        from .i18n import LANG
        for key, tip in (TIPS_EN if LANG == "en" else TIPS):
            if key in lw and key not in seen:
                if key == "e" and len(out) >= 2:
                    continue
                seen.add(key)
                out.append(f"{w}: {tip}")
                break
    return out[:4]
