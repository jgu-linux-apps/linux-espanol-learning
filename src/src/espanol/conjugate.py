"""Odmiana czasowników hiszpańskich (hiszpański z Hiszpanii — z formą vosotros).

Obsługuje czasowniki regularne, zmiany tematu (e>ie, o>ue, e>i, u>ue),
zmiany pisowni (-car/-gar/-zar, -ger/-gir, -cer/-cir -> zc) oraz listę
najważniejszych czasowników nieregularnych.
"""

PERSONS = ["yo", "tú", "él/ella/usted", "nosotros/as", "vosotros/as", "ellos/ellas/ustedes"]

TENSES = [
    ("presente", "Presente (teraźniejszy)"),
    ("perfecto", "Pretérito perfecto (he hablado)"),
    ("indefinido", "Pretérito indefinido (hablé)"),
    ("imperfecto", "Pretérito imperfecto (hablaba)"),
    ("futuro", "Futuro simple (hablaré)"),
    ("condicional", "Condicional (hablaría)"),
    ("imperativo", "Imperativo afirmativo (¡habla!)"),
    ("ir_a", "Ir a + bezokolicznik (voy a hablar)"),
    ("estar_gerundio", "Estar + gerundio (estoy hablando)"),
]

HABER = ["he", "has", "ha", "hemos", "habéis", "han"]
ESTAR = ["estoy", "estás", "está", "estamos", "estáis", "están"]
IR = ["voy", "vas", "va", "vamos", "vais", "van"]

# Pełne formy nieregularne (nadpisują wynik reguł)
IRREGULAR = {
    "ser": {
        "presente": ["soy", "eres", "es", "somos", "sois", "son"],
        "indefinido": ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"],
        "imperfecto": ["era", "eras", "era", "éramos", "erais", "eran"],
        "imperativo": [None, "sé", "sea", "seamos", "sed", "sean"],
        "gerundio": "siendo",
    },
    "estar": {
        "presente": ESTAR,
        "indefinido": ["estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron"],
        "imperativo": [None, "está", "esté", "estemos", "estad", "estén"],
    },
    "ir": {
        "presente": IR,
        "indefinido": ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"],
        "imperfecto": ["iba", "ibas", "iba", "íbamos", "ibais", "iban"],
        "imperativo": [None, "ve", "vaya", "vamos", "id", "vayan"],
        "gerundio": "yendo",
    },
    "haber": {
        "presente": ["he", "has", "ha / hay", "hemos", "habéis", "han"],
        "indefinido": ["hube", "hubiste", "hubo", "hubimos", "hubisteis", "hubieron"],
    },
    "tener": {
        "presente": ["tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"],
        "indefinido": ["tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron"],
        "imperativo": [None, "ten", "tenga", "tengamos", "tened", "tengan"],
    },
    "hacer": {
        "presente": ["hago", "haces", "hace", "hacemos", "hacéis", "hacen"],
        "indefinido": ["hice", "hiciste", "hizo", "hicimos", "hicisteis", "hicieron"],
        "imperativo": [None, "haz", "haga", "hagamos", "haced", "hagan"],
    },
    "poder": {
        "presente": ["puedo", "puedes", "puede", "podemos", "podéis", "pueden"],
        "indefinido": ["pude", "pudiste", "pudo", "pudimos", "pudisteis", "pudieron"],
        "gerundio": "pudiendo",
    },
    "querer": {
        "presente": ["quiero", "quieres", "quiere", "queremos", "queréis", "quieren"],
        "indefinido": ["quise", "quisiste", "quiso", "quisimos", "quisisteis", "quisieron"],
    },
    "decir": {
        "presente": ["digo", "dices", "dice", "decimos", "decís", "dicen"],
        "indefinido": ["dije", "dijiste", "dijo", "dijimos", "dijisteis", "dijeron"],
        "imperativo": [None, "di", "diga", "digamos", "decid", "digan"],
        "gerundio": "diciendo",
    },
    "venir": {
        "presente": ["vengo", "vienes", "viene", "venimos", "venís", "vienen"],
        "indefinido": ["vine", "viniste", "vino", "vinimos", "vinisteis", "vinieron"],
        "imperativo": [None, "ven", "venga", "vengamos", "venid", "vengan"],
        "gerundio": "viniendo",
    },
    "poner": {
        "presente": ["pongo", "pones", "pone", "ponemos", "ponéis", "ponen"],
        "indefinido": ["puse", "pusiste", "puso", "pusimos", "pusisteis", "pusieron"],
        "imperativo": [None, "pon", "ponga", "pongamos", "poned", "pongan"],
    },
    "salir": {
        "presente": ["salgo", "sales", "sale", "salimos", "salís", "salen"],
        "imperativo": [None, "sal", "salga", "salgamos", "salid", "salgan"],
    },
    "saber": {
        "presente": ["sé", "sabes", "sabe", "sabemos", "sabéis", "saben"],
        "indefinido": ["supe", "supiste", "supo", "supimos", "supisteis", "supieron"],
    },
    "dar": {
        "presente": ["doy", "das", "da", "damos", "dais", "dan"],
        "indefinido": ["di", "diste", "dio", "dimos", "disteis", "dieron"],
    },
    "ver": {
        "presente": ["veo", "ves", "ve", "vemos", "veis", "ven"],
        "indefinido": ["vi", "viste", "vio", "vimos", "visteis", "vieron"],
        "imperfecto": ["veía", "veías", "veía", "veíamos", "veíais", "veían"],
    },
    "oír": {
        "presente": ["oigo", "oyes", "oye", "oímos", "oís", "oyen"],
        "indefinido": ["oí", "oíste", "oyó", "oímos", "oísteis", "oyeron"],
        "imperativo": [None, "oye", "oiga", "oigamos", "oíd", "oigan"],
        "gerundio": "oyendo",
    },
    "traer": {
        "presente": ["traigo", "traes", "trae", "traemos", "traéis", "traen"],
        "indefinido": ["traje", "trajiste", "trajo", "trajimos", "trajisteis", "trajeron"],
        "gerundio": "trayendo",
    },
    "caer": {
        "presente": ["caigo", "caes", "cae", "caemos", "caéis", "caen"],
        "indefinido": ["caí", "caíste", "cayó", "caímos", "caísteis", "cayeron"],
        "gerundio": "cayendo",
    },
    "conducir": {
        "presente": ["conduzco", "conduces", "conduce", "conducimos", "conducís", "conducen"],
        "indefinido": ["conduje", "condujiste", "condujo", "condujimos", "condujisteis", "condujeron"],
    },
    "traducir": {
        "presente": ["traduzco", "traduces", "traduce", "traducimos", "traducís", "traducen"],
        "indefinido": ["traduje", "tradujiste", "tradujo", "tradujimos", "tradujisteis", "tradujeron"],
    },
    "andar": {
        "indefinido": ["anduve", "anduviste", "anduvo", "anduvimos", "anduvisteis", "anduvieron"],
    },
    "leer": {
        "indefinido": ["leí", "leíste", "leyó", "leímos", "leísteis", "leyeron"],
        "gerundio": "leyendo",
    },
    "creer": {
        "indefinido": ["creí", "creíste", "creyó", "creímos", "creísteis", "creyeron"],
        "gerundio": "creyendo",
    },
    "construir": {
        "presente": ["construyo", "construyes", "construye", "construimos", "construís", "construyen"],
        "indefinido": ["construí", "construiste", "construyó", "construimos", "construisteis", "construyeron"],
        "gerundio": "construyendo",
    },
    "elegir": {
        "presente": ["elijo", "eliges", "elige", "elegimos", "elegís", "eligen"],
    },
    "seguir": {
        "presente": ["sigo", "sigues", "sigue", "seguimos", "seguís", "siguen"],
    },
    "reír": {
        "presente": ["río", "ríes", "ríe", "reímos", "reís", "ríen"],
        "indefinido": ["reí", "reíste", "rio", "reímos", "reísteis", "rieron"],
        "gerundio": "riendo",
    },
}

FUTURE_STEMS = {
    "tener": "tendr", "poder": "podr", "querer": "querr", "hacer": "har", "decir": "dir",
    "venir": "vendr", "poner": "pondr", "salir": "saldr", "saber": "sabr", "haber": "habr",
    "caber": "cabr", "valer": "valdr", "deshacer": "deshar", "mantener": "mantendr",
    "obtener": "obtendr", "contener": "contendr", "proponer": "propondr",
}

PARTICIPLES = {
    "hacer": "hecho", "decir": "dicho", "ver": "visto", "escribir": "escrito", "poner": "puesto",
    "volver": "vuelto", "abrir": "abierto", "morir": "muerto", "romper": "roto", "cubrir": "cubierto",
    "descubrir": "descubierto", "resolver": "resuelto", "devolver": "devuelto", "ir": "ido",
    "leer": "leído", "creer": "creído", "oír": "oído", "traer": "traído", "caer": "caído",
    "reír": "reído", "freír": "frito", "imprimir": "impreso", "deshacer": "deshecho",
    "proponer": "propuesto", "componer": "compuesto", "suponer": "supuesto",
}

# Zmiany tematu w presente (wszystkie osoby oprócz nosotros/vosotros)
STEM_CHANGE = {
    # e > ie
    "pensar": "ie", "empezar": "ie", "cerrar": "ie", "comenzar": "ie", "despertar": "ie",
    "despertarse": "ie", "entender": "ie", "perder": "ie", "preferir": "ie", "sentir": "ie",
    "sentirse": "ie", "querer": "ie", "tener": "ie", "venir": "ie", "nevar": "ie", "mentir": "ie",
    "recomendar": "ie", "calentar": "ie", "divertirse": "ie", "sentarse": "ie", "merendar": "ie",
    "encender": "ie", "defender": "ie", "convertir": "ie", "fregar": "ie", "atravesar": "ie",
    # o > ue
    "poder": "ue", "dormir": "ue", "volver": "ue", "encontrar": "ue", "contar": "ue",
    "costar": "ue", "recordar": "ue", "almorzar": "ue", "mover": "ue", "llover": "ue",
    "acostarse": "ue", "devolver": "ue", "morir": "ue", "probar": "ue", "soñar": "ue",
    "mostrar": "ue", "doler": "ue", "resolver": "ue", "encontrarse": "ue", "volar": "ue",
    "colgar": "ue", "aprobar": "ue", "sonar": "ue",
    # u > ue
    "jugar": "u_ue",
    # e > i
    "pedir": "i", "repetir": "i", "servir": "i", "vestirse": "i", "seguir": "i", "elegir": "i",
    "medir": "i", "reír": "i", "despedirse": "i", "corregir": "i", "conseguir": "i",
}

ACCENT_FREE = str.maketrans("áéíóú", "aeiou")


def _split_reflexive(inf):
    if inf.endswith("se") and len(inf) > 4 and inf[-4:-2] in ("ar", "er", "ir", "ír"):
        return inf[:-2], True
    return inf, False


REFL = ["me", "te", "se", "nos", "os", "se"]


def _apply_stem(stem, kind):
    """Zastosuj zmianę tematu na ostatniej samogłosce tematu."""
    if kind in ("ie", "i"):
        target = "e"
        repl = "ie" if kind == "ie" else "i"
    elif kind == "ue":
        target, repl = "o", "ue"
    elif kind == "u_ue":
        target, repl = "u", "ue"
    else:
        return stem
    idx = stem.rfind(target)
    if idx < 0:
        return stem
    return stem[:idx] + repl + stem[idx + 1:]


def _ending(inf):
    e = inf[-2:].translate(ACCENT_FREE)
    return e


def gerund(inf):
    base, _ = _split_reflexive(inf)
    irr = IRREGULAR.get(base, {})
    if "gerundio" in irr:
        return irr["gerundio"]
    stem, e = base[:-2], _ending(base)
    if e == "ar":
        return stem + "ando"
    # -ir ze zmianą e>i / o>u
    kind = STEM_CHANGE.get(inf) or STEM_CHANGE.get(base)
    if e == "ir" and kind in ("ie", "i"):
        stem = _apply_stem(stem, "i")
    elif e == "ir" and kind == "ue":
        idx = stem.rfind("o")
        stem = stem[:idx] + "u" + stem[idx + 1:]
    if stem and stem[-1] in "aeo":
        return stem + "yendo"
    return stem + "iendo"


def participle(inf):
    base, _ = _split_reflexive(inf)
    if base in PARTICIPLES:
        return PARTICIPLES[base]
    for k, v in PARTICIPLES.items():  # złożenia: describir -> descrito
        if base.endswith(k) and len(base) > len(k) and k in ("escribir", "poner", "hacer", "volver", "cubrir"):
            return base[: -len(k)] + v
    stem, e = base[:-2], _ending(base)
    return stem + ("ado" if e == "ar" else "ido")


def _presente(base, inf):
    stem, e = base[:-2], _ending(base)
    kind = STEM_CHANGE.get(inf) or STEM_CHANGE.get(base)
    ends = {"ar": ["o", "as", "a", "amos", "áis", "an"],
            "er": ["o", "es", "e", "emos", "éis", "en"],
            "ir": ["o", "es", "e", "imos", "ís", "en"]}[e]
    out = []
    for i, en in enumerate(ends):
        s = stem
        if kind and i not in (3, 4):
            s = _apply_stem(stem, kind)
        if i == 0:
            if base.endswith(("cer", "cir")) and not base.endswith(("hacer", "decir")) and base[-4] in "aeiou":
                s = s[:-1] + "zc"
            elif base.endswith(("ger", "gir")):
                s = s[:-1] + "j"
            elif base.endswith("guir"):
                s = s[:-1]
        out.append(s + en)
    return out


def _indefinido(base, inf):
    stem, e = base[:-2], _ending(base)
    kind = STEM_CHANGE.get(inf) or STEM_CHANGE.get(base)
    if e == "ar":
        ends = ["é", "aste", "ó", "amos", "asteis", "aron"]
    else:
        ends = ["í", "iste", "ió", "imos", "isteis", "ieron"]
    out = []
    for i, en in enumerate(ends):
        s = stem
        if i == 0 and e == "ar":
            if s.endswith("c"):
                s = s[:-1] + "qu"
            elif s.endswith("g"):
                s = s + "u"
            elif s.endswith("z"):
                s = s[:-1] + "c"
        if e == "ir" and i in (2, 5) and kind:
            if kind in ("ie", "i"):
                s = _apply_stem(stem, "i")
            elif kind == "ue":
                idx = stem.rfind("o")
                s = stem[:idx] + "u" + stem[idx + 1:]
        if e != "ar" and stem and stem[-1] in "aeo" and i in (2, 5):
            en = "yó" if i == 2 else "yeron"
        out.append(s + en)
    return out


def _imperfecto(base):
    stem, e = base[:-2], _ending(base)
    if e == "ar":
        ends = ["aba", "abas", "aba", "ábamos", "abais", "aban"]
    else:
        ends = ["ía", "ías", "ía", "íamos", "íais", "ían"]
    return [stem + en for en in ends]


def _futuro(base, cond=False):
    st = FUTURE_STEMS.get(base)
    if st is None:
        st = base.replace("í", "i")
    ends = ["ía", "ías", "ía", "íamos", "íais", "ían"] if cond else ["é", "ás", "á", "emos", "éis", "án"]
    return [st + en for en in ends]


def _imperativo(base, inf, pres):
    stem, e = base[:-2], _ending(base)
    tu = pres[2]  # tú = 3. os. presente
    vos = base[:-1] + "d"
    # usted/ustedes/nosotros z subjuntivo (uproszczone, na podstawie 1. os. presente)
    yo = pres[0]
    sub_stem = yo[:-1] if yo.endswith("o") else yo
    if e == "ar":
        if sub_stem.endswith("c"):
            sub_stem = sub_stem[:-1] + "qu"
        elif sub_stem.endswith("g"):
            sub_stem = sub_stem + "u"
        elif sub_stem.endswith("z"):
            sub_stem = sub_stem[:-1] + "c"
        s_end = ["e", "emos", "en"]
    else:
        s_end = ["a", "amos", "an"]
    nos_stem = stem
    if e == "ar" and nos_stem.endswith(("c", "g", "z")):
        nos_stem = {"c": nos_stem[:-1] + "qu", "g": nos_stem + "u", "z": nos_stem[:-1] + "c"}[nos_stem[-1]]
    if e != "ar":
        nos_stem = sub_stem
        kind = STEM_CHANGE.get(inf) or STEM_CHANGE.get(base)
        if kind == "ie":
            nos_stem = nos_stem.replace("ie", "i" if e == "ir" else "e", 1)
        elif kind == "ue":
            nos_stem = nos_stem.replace("ue", "u" if e == "ir" else "o", 1)
    return [None, tu, sub_stem + s_end[0], nos_stem + s_end[1], vos, sub_stem + s_end[2]]


def conjugate(inf):
    """Zwraca dict: czas -> lista 6 form (z zaimkiem zwrotnym dla -se)."""
    inf = inf.strip().lower()
    base, refl = _split_reflexive(inf)
    irr = IRREGULAR.get(base, {})
    res = {}
    pres = irr.get("presente") or _presente(base, inf)
    res["presente"] = pres
    res["indefinido"] = irr.get("indefinido") or _indefinido(base, inf)
    res["imperfecto"] = irr.get("imperfecto") or _imperfecto(base)
    res["futuro"] = _futuro(base)
    res["condicional"] = _futuro(base, cond=True)
    part = participle(inf)
    res["perfecto"] = [h + " " + part for h in HABER]
    res["imperativo"] = irr.get("imperativo") or _imperativo(base, inf, pres)
    ger = gerund(inf)
    res["ir_a"] = [v + " a " + inf for v in IR]
    res["estar_gerundio"] = [v + " " + ger for v in ESTAR]
    if refl:
        for t in ("presente", "indefinido", "imperfecto", "futuro", "condicional", "perfecto"):
            res[t] = [REFL[i] + " " + f for i, f in enumerate(res[t])]
        res["estar_gerundio"] = [REFL[i] + " " + f for i, f in enumerate(res["estar_gerundio"])]
        imp = res["imperativo"]
        res["imperativo"] = [None if f is None else _attach_refl(f, REFL[i], i) for i, f in enumerate(imp)]
    res["_participio"] = part
    res["_gerundio"] = ger
    return res


_STRESS = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}


def _nuclei(word):
    """Indeksy samogłosek akcentowalnych dla kolejnych sylab (z uwzględnieniem dyftongów)."""
    nuclei = []
    i = 0
    while i < len(word):
        if word[i] in "aeiouáéíóú":
            j = i
            while j + 1 < len(word) and word[j + 1] in "aeiouáéíóú":
                a, b = word[j], word[j + 1]
                if a in "aeo" and b in "aeo":
                    break  # hiat: dwie mocne samogłoski
                j += 1
            group = range(i, j + 1)
            strong = [k for k in group if word[k] in "aeo"]
            nuclei.append(strong[0] if strong else j)
            i = j + 1
        else:
            i += 1
    return nuclei


def _attach_refl(form, pron, i):
    """¡Levántate! — dołącz zaimek i dodaj akcent graficzny tam, gdzie trzeba."""
    if i == 4:  # vosotros: levantad + os -> levantaos
        if form.endswith("id"):
            return form[:-2] + "íos"  # vestíos, divertíos
        return form[:-1] + "os" if form.endswith("d") else form + "os"
    if i == 3:  # nosotros: levantemos + nos -> levantémonos
        form = form[:-1]
    if any(c in form for c in "áéíóú"):
        return form + pron
    nuc = _nuclei(form)
    if len(nuc) < 2:
        return form + pron  # ponte, vete, hazlo
    k = nuc[-2] if form[-1] in "aeiouns" else nuc[-1]
    return form[:k] + _STRESS[form[k]] + form[k + 1:] + pron


def table(inf):
    """Tabela do wyświetlenia: lista (nazwa czasu, [(osoba, forma)])."""
    c = conjugate(inf)
    out = []
    for key, label in TENSES:
        forms = c[key]
        rows = []
        for i, f in enumerate(forms):
            if f is None:
                continue
            rows.append((PERSONS[i], f))
        out.append((label, rows))
    return out, c["_participio"], c["_gerundio"]
