"""Wczytywanie treści kursu z prostych plików tekstowych.

Format lekcji (data/lessons/<poziom>/<nn>-<nazwa>.txt):

    # id: a1-01
    # title: ...
    # unit: 1
    # unit_title: ...
    @goals            – cele lekcji, po jednym w wierszu
    @dialog           – "Osoba: zdanie hiszpańskie | tłumaczenie polskie"
    @vocab            – "słowo | tłumaczenie | część mowy | przykład ES / przykład PL"
    @grammar          – tekst z prostym formatowaniem (## nagłówek, - punkt, || tabela)
    @exercises        – "typ: pytanie | odpowiedź(i) rozdzielone /// | opcje ;"
    @culture          – ciekawostka kulturowa
"""
import os
import re
import random
import functools

from .paths import DATA

POS_NAMES = {
    "m": "rzeczownik r. męski", "f": "rzeczownik r. żeński", "mf": "rzeczownik r. męski i żeński",
    "mpl": "rzeczownik l. mn. (męski)", "fpl": "rzeczownik l. mn. (żeński)",
    "v": "czasownik", "vr": "czasownik zwrotny", "adj": "przymiotnik", "adv": "przysłówek",
    "prep": "przyimek", "conj": "spójnik", "pron": "zaimek", "interj": "wykrzyknik",
    "num": "liczebnik", "phr": "zwrot", "art": "rodzajnik", "det": "określnik",
}


class Lesson:
    def __init__(self, path):
        self.path = path
        self.meta = {}
        self.goals = []
        self.dialog = []      # (osoba, es, pl)
        self.vocab = []       # dict(es, pl, pos, ex_es, ex_pl)
        self.grammar = ""
        self.exercises = []   # dict(type, q, answers, options, hint)
        self.culture = ""
        self._parse()

    @property
    def id(self):
        return self.meta["id"]

    @property
    def title(self):
        return self.meta.get("title", self.id)

    @property
    def level(self):
        return self.id.split("-")[0].upper()

    @property
    def unit(self):
        return int(self.meta.get("unit", 1))

    @property
    def number(self):
        return int(self.id.split("-")[1])

    def _parse(self):
        section = None
        buf = []
        with open(self.path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for raw in lines:
            line = raw.rstrip()
            if line.startswith("# ") and ":" in line and section is None:
                k, v = line[2:].split(":", 1)
                self.meta[k.strip()] = v.strip()
                continue
            if line.startswith("@"):
                self._flush(section, buf)
                section, buf = line[1:].strip(), []
                continue
            buf.append(line)
        self._flush(section, buf)

    def _flush(self, section, buf):
        if section is None:
            return
        if section in ("grammar", "culture"):
            setattr(self, section, "\n".join(buf).strip())
            return
        for line in buf:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if section == "goals":
                self.goals.append(line.lstrip("- "))
            elif section == "dialog":
                who, rest = line.split(":", 1) if ":" in line.split("|")[0] else ("", line)
                es, _, pl = rest.partition("|")
                self.dialog.append((who.strip(), es.strip(), pl.strip()))
            elif section == "vocab":
                p = [x.strip() for x in line.split("|")]
                ex_es, ex_pl = "", ""
                if len(p) > 3 and p[3]:
                    ex_es, _, ex_pl = p[3].partition(" / ")
                self.vocab.append(dict(es=p[0], pl=p[1], pos=p[2] if len(p) > 2 else "",
                                       ex_es=ex_es.strip(), ex_pl=ex_pl.strip(), lesson=None))
            elif section == "exercises":
                typ, _, rest = line.partition(":")
                p = [x.strip() for x in rest.split("|")]
                ex = dict(type=typ.strip(), q=p[0], answers=[], options=[], hint="")
                if len(p) > 1:
                    ex["answers"] = [a.strip() for a in p[1].split("///")]
                if len(p) > 2 and p[2]:
                    if ex["type"] == "choice":
                        ex["options"] = [o.strip() for o in p[2].split(";") if o.strip()]
                    else:
                        ex["hint"] = p[2]
                if len(p) > 3:
                    ex["hint"] = p[3]
                self.exercises.append(ex)

    # ---------- ćwiczenia generowane automatycznie ----------
    def all_exercises(self, rng=None):
        rng = rng or random.Random()
        out = [dict(e, source=self.id) for e in self.exercises]
        pool = [v for v in self.vocab]
        for v in pool:
            others = [o["pl"] for o in pool if o is not v]
            if len(others) >= 3:
                opts = rng.sample(others, 3) + [v["pl"]]
                rng.shuffle(opts)
                out.append(dict(type="choice", q=f"Co znaczy „{v['es']}”?", answers=[v["pl"]],
                                options=opts, hint="", source=self.id, audio=v["es"]))
            if "+" in v["es"] or "…" in v["es"]:
                continue
            out.append(dict(type="trans", q=f"Przetłumacz na hiszpański: {v['pl']}",
                            answers=_vocab_answers(v["es"]), options=[], hint=_vocab_hint(v), source=self.id))
        for who, es, pl in self.dialog:
            if pl and 2 <= len(es.split()) <= 12:
                out.append(dict(type="listen", q="Posłuchaj i zapisz zdanie po hiszpańsku.",
                                answers=[es], options=[], hint=pl, source=self.id, audio=es))
                if len(es.split()) >= 3:
                    out.append(dict(type="order", q=pl, answers=[es], options=[], hint="",
                                    source=self.id))
        return out

    def speaking_items(self):
        return [es for _, es, _ in self.dialog if es] + [v["es"] for v in self.vocab[:6]]


def _vocab_hint(v):
    """Czytelna podpowiedź: część mowy + pierwsza litera + długość."""
    first = re.split(r"\s*/\s*|\s*,\s*", v["es"])[0].strip()
    core = re.sub(r"^(el|la|los|las|un|una)\s+", "", first).lstrip("¡¿")
    parts = [POS_NAMES.get(v["pos"], "")] if POS_NAMES.get(v["pos"]) else []
    words = core.split()
    if len(words) > 1:
        parts.append(f"{len(words)} słowa, pierwsze zaczyna się na „{words[0][0]}”")
    elif core:
        n = len(core.rstrip("?!"))
        parts.append(f"zaczyna się na „{core[0]}”, {n} liter" + ("y" if n in (2, 3, 4) else ""))
    if first != core and re.match(r"^(el|la|los|las)\s", first):
        parts.append("z rodzajnikiem lub bez")
    return " · ".join(parts)


def _vocab_answers(es):
    """'el libro' -> ['el libro', 'libro']; 'hola / buenas' -> obie."""
    alts = [a.strip() for a in re.split(r"\s*/\s*|\s*,\s*", es) if a.strip()]
    out = []
    for a in alts:
        out.append(a)
        m = re.match(r"^(el|la|los|las|un|una)\s+(.+)$", a)
        if m:
            out.append(m.group(2))
    return out


class Course:
    def __init__(self):
        self.lessons = []
        for lvl in ("a1", "a2"):
            d = os.path.join(DATA, "lessons", lvl)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".txt"):
                    les = Lesson(os.path.join(d, fn))
                    for v in les.vocab:
                        v["lesson"] = les.id
                    self.lessons.append(les)
        self.by_id = {l.id: l for l in self.lessons}
        self.readings = load_readings()
        self.alphabet = load_alphabet()
        self.videos = load_videos()
        self.extra_vocab = load_extra_vocab()

    def units(self, level):
        out = {}
        for l in self.lessons:
            if l.level == level:
                out.setdefault(l.unit, []).append(l)
        return out

    def unit_title(self, level, unit):
        for l in self.lessons:
            if l.level == level and l.unit == unit:
                return l.meta.get("unit_title", f"Dział {unit}")
        return f"Dział {unit}"

    def next_lesson(self, done_ids):
        for l in self.lessons:
            if l.id not in done_ids:
                return l
        return None

    @functools.cached_property
    def dictionary(self):
        """Słownik ES-PL: wszystkie słowa z lekcji + dodatkowe listy tematyczne."""
        seen = {}
        for l in self.lessons:
            for v in l.vocab:
                key = v["es"].lower()
                if key not in seen:
                    seen[key] = dict(v, level=l.level)
        for v in self.extra_vocab:
            key = v["es"].lower()
            if key not in seen:
                seen[key] = v
        return sorted(seen.values(), key=lambda v: _sort_key(v["es"]))


def _sort_key(es):
    s = re.sub(r"^((el|la|los|las|un|una)\s*/?\s*)+", "", es.lower())
    s = s.lstrip("¡¿")
    from .answers import strip_accents
    return strip_accents(s)


def load_readings():
    """data/readings/*.txt: # id, # level, # unit, # title; @text; @glossary; @questions (choice)."""
    out = []
    d = os.path.join(DATA, "readings")
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"):
            continue
        r = dict(meta={}, text="", translation="", glossary=[], questions=[])
        section, buf = None, []

        def flush():
            if section in ("text", "translation"):
                r[section] = "\n".join(buf).strip()
            elif section == "glossary":
                for line in buf:
                    if "|" in line:
                        a, b = line.split("|", 1)
                        r["glossary"].append((a.strip(), b.strip()))
            elif section == "questions":
                for line in buf:
                    if "|" in line:
                        p = [x.strip() for x in line.split("|")]
                        opts = [o.strip() for o in p[2].split(";")] if len(p) > 2 else []
                        r["questions"].append(dict(type="choice", q=p[0], answers=[p[1]],
                                                   options=opts, hint=""))
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            for line in f.read().splitlines():
                if line.startswith("# ") and ":" in line and section is None:
                    k, v = line[2:].split(":", 1)
                    r["meta"][k.strip()] = v.strip()
                elif line.startswith("@"):
                    flush()
                    section, buf = line[1:].strip(), []
                else:
                    buf.append(line)
            flush()
        out.append(r)
    return out


def load_alphabet():
    """data/alphabet.txt: sekcje @letters (litera | nazwa | wymowa PL | przykłady) i @sounds."""
    path = os.path.join(DATA, "alphabet.txt")
    res = {"letters": [], "sounds": [], "stress": "", "keyboard": ""}
    if not os.path.exists(path):
        return res
    section, buf = None, []

    def flush():
        if section in ("letters", "sounds"):
            for line in buf:
                if "|" in line:
                    res[section].append([x.strip() for x in line.split("|")])
        elif section in ("stress", "keyboard"):
            res[section] = "\n".join(buf).strip()
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("@"):
                flush()
                section, buf = line[1:].strip(), []
            elif not line.startswith("//"):
                buf.append(line)
        flush()
    return res


def load_videos():
    """data/videos.txt: [Poziom] potem 'tytuł | url | opis'."""
    path = os.path.join(DATA, "videos.txt")
    out = []
    if not os.path.exists(path):
        return out
    group = None
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("[") and line.endswith("]"):
                group = line[1:-1]
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) >= 2:
                out.append(dict(group=group, title=p[0], url=p[1], desc=p[2] if len(p) > 2 else ""))
    return out


def load_extra_vocab():
    """data/vocab_extra.txt: [Temat] potem 'słowo | tłumaczenie | część mowy | przykład'."""
    path = os.path.join(DATA, "vocab_extra.txt")
    out = []
    if not os.path.exists(path):
        return out
    topic = None
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("[") and line.endswith("]"):
                topic = line[1:-1]
                continue
            p = [x.strip() for x in line.split("|")]
            ex_es, ex_pl = "", ""
            if len(p) > 3 and p[3]:
                ex_es, _, ex_pl = p[3].partition(" / ")
            out.append(dict(es=p[0], pl=p[1], pos=p[2] if len(p) > 2 else "", ex_es=ex_es.strip(),
                            ex_pl=ex_pl.strip(), lesson=None, topic=topic, level="A1–A2"))
    return out
