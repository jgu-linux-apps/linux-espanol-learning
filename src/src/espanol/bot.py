"""Rozmowa z botem (tekstowa) — ograniczona do materiału z ukończonych lekcji.

Silniki: Ollama (lokalnie, offline) albo API Claude (chmura)."""
import json
import os
import re
import urllib.request

from .answers import strip_accents
from .conjugate import conjugate
from .paths import XDG_CONFIG, PKG
from . import i18n
from .i18n import _

CONFIG_DIR = os.path.join(XDG_CONFIG, PKG)
KEY_FILE = os.path.join(CONFIG_DIR, "claude_api_key")

CLAUDE_MODELS = {"claude-haiku-5-5": _("Claude Haiku (szybki, tani)"),
                 "claude-sonnet-5-5": _("Claude Sonnet (najlepszy)")}


def native():
    """The learner's own language (the course language) — for prompts."""
    return "English" if i18n.LANG == "en" else "Polish"

# ------------------------------------------------------------------ scenki
SCENARIOS = [
    dict(id="free", title=_("Swobodna rozmowa o Tobie"), lesson="a1-01",
         role=("Paco, a friendly, cheerful 30-year-old man from Madrid (a little robot-like in spirit, with a black beret and "
               "a moustache) you have just met at a language exchange (intercambio). Your name is Paco. "
               "You work as a graphic designer, live with your dog Toby, love cooking paella and cycling, and have a "
               "younger brother called Pablo. You are male: use masculine forms (encantado, contento)"),
         goal=_("Porozmawiaj o sobie: imię, skąd jesteś, praca, rodzina, zainteresowania — tylko tym, co już znasz.")),
    dict(id="bar", title=_("W barze — zamów i zapłać"), lesson="a1-13",
         role="a waiter (camarero) in a busy bar in Madrid",
         goal=_("Zamów coś do picia i jedzenia, zapytaj o cenę i zapłać kartą.")),
    dict(id="mercado", title=_("Na targu"), lesson="a1-14",
         role="a fruit and vegetable seller at a market in Valencia",
         goal=_("Kup owoce i warzywa (ilości w kilogramach), zapytaj, co jest dobre, powiedz, co lubisz.")),
    dict(id="calle", title=_("Pytanie o drogę"), lesson="a1-15",
         role="a local person on a street in Sevilla; the learner is a lost tourist",
         goal=_("Zapytaj, jak dojść do muzeum lub na dworzec, i upewnij się, że rozumiesz drogę.")),
    dict(id="tienda", title=_("W sklepie z ubraniami"), lesson="a1-16",
         role="a shop assistant (dependiente) in a clothes shop",
         goal=_("Znajdź kurtkę albo koszulę, zapytaj o rozmiar, kolor i cenę, przymierz i kup.")),
    dict(id="planes", title=_("Plany na weekend"), lesson="a1-19",
         role="a Spanish friend who wants to make plans for the weekend",
         goal=_("Umówcie się na weekend: co, gdzie, o której. Odmów jednej propozycji i zaproponuj inną.")),
    dict(id="vacaciones", title=_("Ostatnie wakacje"), lesson="a2-23",
         role="a Spanish colleague asking about the learner's last holidays",
         goal=_("Opowiedz o swoich ostatnich wakacjach w czasie przeszłym: gdzie byłeś, co robiłeś, jak było.")),
    dict(id="hotel", title=_("Recepcja hotelu"), lesson="a2-28",
         role="a hotel receptionist in Granada; there is a problem with the room",
         goal=_("Zamelduj się, zapytaj o śniadanie i zgłoś problem z pokojem.")),
    dict(id="medico", title=_("U lekarza"), lesson="a2-29",
         role="a doctor (médica) at a health centre in Spain",
         goal=_("Opisz objawy (co Cię boli, od kiedy) i zrozum zalecenia.")),
    dict(id="entrevista", title=_("Rozmowa o pracę"), lesson="a2-34",
         role="an interviewer from a Spanish IT company",
         goal=_("Opowiedz o swoim doświadczeniu, mocnych stronach i dlaczego chcesz tam pracować.")),
    dict(id="piso", title=_("Wynajem mieszkania"), lesson="a2-38",
         role="a landlady renting a flat in Valencia",
         goal=_("Zapytaj o mieszkanie: metraż, czynsz, opłaty, kaucję i umów się na oglądanie.")),
]

TENSES_BY_LESSON = [
    ("a1-01", "present tense (presente) of regular and common irregular verbs"),
    ("a1-11", "reflexive verbs (me levanto)"),
    ("a1-14", "gustar / encantar"),
    ("a1-19", "near future with ir a + infinitive, tener que, querer/poder + infinitive"),
    ("a1-20", "pretérito perfecto (he comido) for today / this week / experiences"),
    ("a2-22", "pretérito indefinido (ayer comí)"),
    ("a2-25", "pretérito imperfecto (cuando era niño…)"),
    ("a2-27", "comparatives and superlatives"),
    ("a2-30", "affirmative imperative (tú, vosotros)"),
    ("a2-31", "imperative usted/ustedes and negative imperative"),
    ("a2-32", "direct and indirect object pronouns (lo, la, le, se lo)"),
    ("a2-33", "futuro simple"),
    ("a2-35", "estar + gerundio"),
    ("a2-36", "condicional for polite requests and advice"),
]

FUNCTION_WORDS = set("""
a al ante bajo con contra de del desde durante en entre hacia hasta para por según sin sobre tras
el la los las lo un una unos unas y e o u ni pero sino que qué quien quién quienes cual cuál cuales cuáles
cuando cuándo donde dónde como cómo cuanto cuánto cuanta cuánta cuantos cuántos cuantas cuántas porque por qué
yo tú tu él ella usted nosotros nosotras vosotros vosotras ellos ellas ustedes me te se nos os le les mi mis tus su sus
nuestro nuestra nuestros nuestras vuestro vuestra vuestros vuestras mí ti conmigo contigo
este esta estos estas ese esa esos esas esto eso aquel aquella aquello aquí allí ahí
sí no muy más menos bien mal ya también tampoco nunca siempre hoy mañana ahora luego después antes
todo toda todos todas nada algo alguien nadie otro otra otros otras mucho mucha muchos muchas poco poca
hola gracias adiós vale bueno buena buenos buenas claro pues entonces así tan tanto
uno dos tres cuatro cinco seis siete ocho nueve diez señor señora don doña
""".split())


def _norm_word(w):
    return strip_accents(w.lower())


class Profile:
    """Co uczeń już zna — na podstawie ukończonych lekcji."""

    def __init__(self, course, done_ids):
        self.lessons = [l for l in course.lessons if l.id in done_ids] or course.lessons[:1]
        self.no_lessons = not done_ids
        self.level = "A2" if any(l.level == "A2" for l in self.lessons) else "A1"
        ids = {l.id for l in self.lessons}
        self.grammar = [t for lid, t in TENSES_BY_LESSON if lid in ids] or [TENSES_BY_LESSON[0][1]]
        self.topics = [l.title for l in self.lessons]
        self.vocab = []
        for l in self.lessons:
            for v in l.vocab:
                self.vocab.append(v["es"])
        self.known = set(FUNCTION_WORDS)
        for es in self.vocab:
            for part in re.split(r"\s*/\s*", es):
                words = re.findall(r"[\wáéíóúüñ]+", part.lower())
                self.known.update(words)
                if words and words[-1].endswith(("ar", "er", "ir", "ír", "arse", "erse", "irse")) and len(words) <= 2:
                    try:
                        c = conjugate(words[-1])
                        for k, forms in c.items():
                            if isinstance(forms, list):
                                for f in forms:
                                    if f:
                                        self.known.update(f.lower().split())
                            elif isinstance(forms, str):
                                self.known.add(forms.lower())
                    except Exception:  # noqa
                        pass
                # liczba mnoga i rodzaj
                for w in words:
                    self.known.update({w + "s", w + "es", w[:-1] + "a" if w.endswith("o") else w,
                                       w[:-1] + "as" if w.endswith("o") else w})
        # słowa z dialogów i czytanek ukończonych lekcji też są „znane”
        for l in self.lessons:
            for _w, es, _pl in l.dialog:
                self.known.update(re.findall(r"[\wáéíóúüñ]+", es.lower()))
        for v in ("ser", "estar", "tener", "ir", "hacer", "haber", "poder", "querer", "gustar", "llamarse"):
            c = conjugate(v)
            for k, forms in c.items():
                if isinstance(forms, list):
                    for f in forms:
                        if f:
                            self.known.update(f.lower().replace(" / hay", " hay").split())
        self.known_norm = {_norm_word(w) for w in self.known}

    def unknown_words(self, text):
        out = []
        for i, w in enumerate(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text)):
            if w[0].isupper() and i > 0 and w.lower() not in self.known:
                continue  # imię / nazwa własna
            if len(w) <= 2:
                continue
            if _norm_word(w) not in self.known_norm:
                out.append(w)
        return out


BEGINNER_NOTE = ("- The learner is an ABSOLUTE BEGINNER who has finished few lessons, so the vocabulary list below is short. "
                 "You may also use very common A1 words (yo, tú, casa, familia, trabajo, comer, perro, gato, "
                 "ciudad, música, bien, mucho, también…), but keep every sentence very short and simple.")

LEVELS = {
    "easy": (_("Wolno i prosto"), _("Bardzo krótkie, najprostsze zdania, bez nowych słów.")),
    "normal": (_("Normalnie"), _("Krótkie tury, najwyżej jedno nowe słowo.")),
    "hard": (_("Wyzwanie"), _("Dłuższe wypowiedzi, do dwóch nowych słów, mniej podpowiedzi.")),
}
LEVEL_RULES = {
    "easy": ("- NO new words at all: use only the known vocabulary and the simplest present-tense sentences.\n"
             "- Very short turns: ONE or TWO sentences, max ~7 words each. Always end with a very simple question."),
    "normal": ("- At most ONE new word per turn, and only if really needed — then add its {native} meaning in brackets "
               "right after it.\n- Very short turns: 1–3 sentences, max ~12 words each. Always end with a simple "
               "question or prompt so the learner can answer."),
    "hard": ("- At most TWO new words per turn, each followed by its {native} meaning in brackets.\n"
             "- Natural, slightly longer turns: 2–4 sentences, max ~15 words each. Use the whole known grammar "
             "freely, ask open questions that need a full sentence to answer, and be less helpful with hints."),
}

FACT_LABELS = {"age": "age", "pets": "pets", "study": "studies", "memories": "things you remember about the learner",
               "last_talk": "what you talked about last time","name": "name", "city": "town/city", "country": "country", "job": "job or school",
               "family": "family", "hobbies": "interests", "notes": "other",
               "lives_in": "lives in", "from": "is from", "nationality": "nationality", "likes": "likes"}


FACT_LABELS_PL = {"age": _("wiek"), "pets": _("zwierzęta"), "study": _("nauka"), "memories": _("bot pamięta"),
                  "last_talk": _("poprzednio rozmawialiście o"), "name": _("imię"), "city": _("miejscowość"),
                  "country": _("kraj"), "job": _("praca / szkoła"), "family": _("rodzina"),
                  "hobbies": _("zainteresowania"), "notes": _("inne"), "lives_in": _("mieszka w"),
                  "from": _("pochodzi z"), "nationality": _("narodowość"), "likes": _("lubi")}


FIX_EXAMPLE = {"Polish": "Mówimy „me llamo”, nie „me llamo es”.",
               "English": "We say “me llamo”, not “me llamo es”."}


def system_prompt(profile, scenario, level="normal"):
    vocab = ", ".join(profile.vocab[-300:])
    beginner = len(profile.lessons) < 6
    nat = native()
    rules = LEVEL_RULES.get(level, LEVEL_RULES["normal"]).format(native=nat)
    home = ("they live in Poland unless they say otherwise (Poland is a country in Europe; a Polish town is not "
            "\"near Poland\", it is IN Poland)" if nat == "Polish" else
            "do not guess their country; use only what they tell you")
    return f"""You are a conversation partner for a {nat}-speaking learner of Spanish (level {profile.level}).
Speak the Spanish of Spain (castellano): use "vosotros", Spain vocabulary (coche, ordenador, móvil, zumo, vale) and tú with the learner unless your role is formal.

YOUR ROLE: {scenario['role']}.
LEARNER'S TASK (for your information): {scenario['goal']}

STRICT LIMITS — the learner only knows the material below:
- Grammar the learner knows: {"; ".join(profile.grammar)}. Do NOT use other tenses or moods (no subjunctive).
- Topics already studied: {"; ".join(profile.topics[-12:])}.
- Vocabulary the learner knows (prefer these words, plus very basic function words): {vocab}
{rules}
{BEGINNER_NOTE if beginner else ""}

CONVERSATION FLOW (VERY IMPORTANT — you are a real, curious person, not a parrot):
- NEVER repeat or paraphrase what the learner just said ("Vives en Rumia." is forbidden). React with 1–3 words at most (¡Qué bien!, Vale, ¡Genial!, Entiendo, ¡Qué interesante!), then move on.
- Every turn: (1) a tiny reaction, (2) sometimes ONE short sentence about yourself (your role's life: pets, work, hobbies) so the talk feels two-sided, (3) ONE new simple question.
- Never ask a question that was already asked or already answered. Remember everything said earlier in this conversation and refer back to it when natural ("Antes dijiste que tienes un perro…").
- If the learner answers with just one or two words, ask a natural follow-up on the same topic, or smoothly change the topic.
- Example. Learner: "Vivo en Rumia." Good reply: "¡Qué bien! Yo vivo en Madrid con mi perro Toby. ¿Tienes mascotas?"  Bad reply: "Vives en Rumia. ¿Dónde vives?"

WHO IS WHO (never mix this up!):
- YOU are the partner described in YOUR ROLE. Facts about YOU (name, city, job, pets, family) come only from YOUR ROLE.
- The LEARNER is a different person. Facts the learner told you are about THEM. NEVER say them as if they were about you
  ("Vivo en Rumia", "Soy ingeniero" are forbidden unless YOUR ROLE says so).
- When the learner asks you something ("¿Y tú?", "¿Y tú, dónde vives?"), answer about YOURSELF from YOUR ROLE in one short sentence, then ask something new.
- Write correct, simple Spanish. Double-check spelling; do not invent words.

EXAMPLES OF GOOD TURNS (style only, do not copy):
Learner: "Me llamo Jarek y vivo en Rumia."  -> <es>¡Encantado, Jarek! Yo soy Paco y vivo en Madrid. ¿Trabajas o estudias?</es>
Learner: "Trabajo con ordenadores. ¿Y tú?" -> <es>¡Qué interesante! Yo soy diseñador gráfico. ¿Qué te gusta hacer en tu tiempo libre?</es>
Learner: "Me gusta el fútbol."             -> <es>¡Genial! A mí me gusta montar en bici. ¿Tienes hermanos?</es>

WHAT THE LEARNER TELLS YOU:
- Treat everything the learner says about themselves as TRUE. Towns and places they mention are real; {home}.
- Never ask again about something the learner has already told you. React to it and ask a NEW follow-up question instead.

CORRECTIONS (about the LEARNER's last message only — never about your own sentences):
- If the learner's last message has a real mistake, put the corrected learner sentence in Spanish in <ok> and a short explanation WRITTEN IN {nat.upper()} (never in Spanish!) in <fix>. Also use the correct form naturally in your reply.
- If it is correct, leave both <ok></ok> and <fix></fix> empty. Ignore missing accents, capital letters and punctuation.
- If the learner writes in {nat} or asks for help, help briefly in <fix> (in {nat}), leave <ok> empty, and continue in simple Spanish.
- <fix> must always be {nat}. Example: <ok>Me llamo Jarek.</ok><fix>{FIX_EXAMPLE[nat]}</fix>
- Do not repeat or rephrase your previous turn: move the conversation forward with a NEW short question each time.

Stay in your role and on the topic of learning Spanish. Never write anything outside the tags.
OUTPUT FORMAT (exactly):
<es>your reply in Spanish</es>
<pl>{nat} translation of your reply</pl>
<ok>corrected learner sentence in Spanish, or empty</ok>
<fix>short explanation in {nat.upper()}, or empty</fix>"""


def extract_facts(text):
    """Proste wyłuskanie faktów o uczniu z jego hiszpańskiej wypowiedzi → dict klucz → [wartości]."""
    W = r"([A-Za-zÁÉÍÓÚÑáéíóúñü]+(?-i:(?: (?:de |del |la |las )?[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñü]+)?))"
    out = {}

    def add(k, v):
        v = v.strip(" .,!?¡¿")
        if len(v) >= 2:
            out.setdefault(k, [])
            if v.lower() not in [x.lower() for x in out[k]]:
                out[k].append(v[:1].upper() + v[1:] if k in ("name", "lives_in", "from") else v)
    for m in re.finditer(r"\bme llamo ([A-Za-zÁÉÍÓÚÑáéíóúñü]+)", text, re.I):
        add("name", m.group(1))
    for m in re.finditer(r"\bmi nombre es ([A-Za-zÁÉÍÓÚÑáéíóúñü]+)", text, re.I):
        add("name", m.group(1))
    for m in re.finditer(r"\bvivo en " + W, text, re.I):
        add("lives_in", m.group(1))
    for m in re.finditer(r"\bsoy de " + W, text, re.I):
        add("from", m.group(1))
    if re.search(r"\bsoy (polaco|polaca)\b", text, re.I):
        add("nationality", "Polish")
    for m in re.finditer(r"\btrabajo (?:como|de|en) ([a-záéíóúñü ]{3,25})", text, re.I):
        add("job", re.split(r"[.,;!?]| y ", m.group(1))[0])
    for m in re.finditer(r"\bme gusta(?:n)? ((?:el |la |los |las )?[a-záéíóúñü]+(?: [a-záéíóúñü]+)?)", text, re.I):
        add("likes", m.group(1))
    for m in re.finditer(r"\btengo (\d+|un|una|dos|tres|cuatro) (hermanos?|hermanas?|hijos?|hijas?)",
                         text, re.I):
        add("family", f"{m.group(1)} {m.group(2)}")
    for m in re.finditer(r"\btengo (\d{1,2}) años\b", text, re.I):
        add("age", _("{} lat").format(m.group(1)))
    for m in re.finditer(r"\btengo (?:un|una) (perro|gato|pájaro|conejo|pez)\b", text, re.I):
        add("pets", m.group(1))
    for m in re.finditer(r"\b[Mm]i (hermano|hermana|mujer|esposa|marido|novio|novia|madre|padre|hijo|hija) "
                         r"(?:se llama|es) ([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", text):
        add("family", f"{m.group(1)} {m.group(2)}")
    for m in re.finditer(r"\bestudio ([a-záéíóúñ ]{3,25})", text, re.I):
        add("study", re.split(r"[.,;!?]| y ", m.group(1))[0])
    for m in re.finditer(r"\bme encanta(?:n)? ((?:el |la |los |las )?[a-záéíóúñ]+(?: [a-záéíóúñ]+)?)", text, re.I):
        add("likes", m.group(1))
    for m in re.finditer(r"\bmi ([a-záéíóúñ]+) favorit[oa] es ([a-záéíóúñ ]{2,25})", text, re.I):
        add("likes", f"{m.group(1)}: {m.group(2)}".strip())
    return out


def facts_prompt(manual, auto):
    """Tekst „co wiesz o uczniu” do prompta. manual: dict z zakładki O mnie, auto: z rozmów."""
    lines = []
    for k in ("name", "city", "country", "job", "family", "hobbies", "notes"):
        v = (manual or {}).get(k)
        if v:
            lines.append(f"- {FACT_LABELS[k]}: {v}")
    for k, vals in (auto or {}).items():
        if vals:
            lines.append(f"- {FACT_LABELS.get(k, k)}: {', '.join(vals)}")
    return "\n".join(lines)


def parse(text):
    def tag(t):
        m = re.search(rf"<{t}>(.*?)</{t}>", text, re.S)
        return m.group(1).strip() if m else ""
    es = tag("es") or re.sub(r"<[^>]+>", "", text).strip()
    return dict(es=es, pl=tag("pl"), fix=tag("fix"), ok=tag("ok"))


_PL_CHARS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
_ES_WORDS = {"el", "la", "los", "las", "es", "está", "se", "de", "que", "una", "un", "se", "usa", "verbo",
             "para", "con", "en", "por", "debe", "decir", "forma", "correcta"}


def looks_spanish(text):
    if not text or any(c in _PL_CHARS for c in text):
        return False
    words = re.findall(r"[a-záéíóúüñ]+", text.lower())
    return bool(words) and sum(w in _ES_WORDS for w in words) >= 2


def _normq(t):
    import unicodedata
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-zñ ]", "", "".join(c for c in t if unicodedata.category(c) != "Mn")).strip()


def is_repeated_question(sent, asked):
    import difflib
    if not sent.strip().endswith("?"):
        return False
    n = _normq(sent)
    return any(difflib.SequenceMatcher(None, n, _normq(a)).ratio() > 0.75 for a in asked)


def drop_repeats(es, asked, user_text="", values=()):
    """Usuwa z odpowiedzi pytania, które bot już zadał. Zwraca (tekst, czy_coś_usunięto)."""
    parts = [x for x in re.split(r"(?<=[.!?…])\s+", es.strip()) if x]
    kept, dropped = [], False
    asked = list(asked)
    for x in parts:
        if is_repeated_question(x, asked) or is_echo(x, user_text) or claims_learner_fact(x, values):
            dropped = True
            continue
        kept.append(x)
        if x.endswith("?"):
            asked.append(x)
    return " ".join(kept), dropped


FACT_TOPICS = {"age": "the learner's age", "pets": "the learner's pets", "study": "the learner's job or school",
               "name": "the learner's name", "city": "where the learner lives", "lives_in": "where the learner lives",
               "country": "which country the learner is from", "from": "where the learner is from",
               "nationality": "the learner's nationality", "job": "the learner's job or school",
               "family": "the learner's family", "hobbies": "the learner's interests", "likes": "the learner's interests"}


def known_topics(manual, auto):
    keys = [k for k, v in (manual or {}).items() if v and k in FACT_TOPICS] + \
           [k for k, v in (auto or {}).items() if v and k in FACT_TOPICS]
    seen = []
    for k in keys:
        t = FACT_TOPICS[k]
        if t not in seen:
            seen.append(t)
    return seen


TOPIC_PLAN = [
    ("family", "the learner's family (brothers, sisters, children, parents)", ("family",)),
    ("job", "the learner's job or studies", ("job", "study")),
    ("hobbies", "the learner's hobbies and free time", ("hobbies", "likes")),
    ("pets", "pets (do they have a dog or a cat?)", ("pets",)),
    ("food", "favourite food and drinks", ()),
    ("weekend", "what the learner usually does at the weekend", ()),
    ("music", "music the learner likes", ()),
    ("travel", "travel and holidays — a place the learner would like to visit", ()),
    ("routine", "a normal day of the learner (morning, work, evening)", ()),
    ("city", "the learner's town — what is nice there", ()),
]

_SECOND_PERSON = re.compile(r"^(vives|eres|tienes|trabajas|hablas|estudias|te llamas|te gusta|te gustan|llegas|"
                            r"haces|quieres)\b", re.I)


def is_echo(sent, user_text):
    """Zdanie rozmówcy, które tylko powtarza wypowiedź ucznia (np. „Vives en Rumia.”)."""
    if not user_text or sent.strip().endswith("?"):
        return False
    words = [w for w in _normq(sent).split() if len(w) >= 3]
    if len(words) < 2 or len(words) > 8:
        return False
    if _SECOND_PERSON.match(sent.strip()):
        return True
    uw = set(_normq(user_text).split())
    return sum(w in uw for w in words) / len(words) >= 0.7


_FIRST_PERSON = re.compile(r"^(yo\b|vivo\b|soy\b|trabajo\b|estudio\b|tengo\b|me llamo\b|mi\b|mis\b|"
                           r"también vivo|también soy|también trabajo)", re.I)


def claims_learner_fact(sent, values):
    """Zdanie w 1. osobie, które przypisuje botowi fakt o uczniu (np. „Vivo en Rumia.”)."""
    t = sent.strip()
    if t.endswith("?") or not _FIRST_PERSON.match(t):
        return False
    n = " " + _normq(t) + " "
    for v in values:
        v = _normq(v)
        if len(v) >= 4 and (" " + v + " ") in n:
            return True
    return False


_PL_WORDS = {"kiedy", "jak", "co", "dlaczego", "czemu", "czy", "mówi", "mowi", "się", "sie", "jest", "jaka", "jaki",
             "jakie", "różnica", "roznica", "znaczy", "wyjaśnij", "wyjasnij", "wytłumacz", "wytlumacz", "po", "polsku",
             "nie", "to", "na", "mam", "chcę", "chce", "powiedzieć", "powiedziec", "mówię", "mowie", "pomóż", "pomoz",
             "proszę", "prosze", "że", "ze", "też", "tez", "ale", "tylko", "zrozumiałem", "zrozumialem"}
_ES_HINT = {"yo", "tú", "tu", "soy", "eres", "es", "estoy", "estás", "tengo", "tienes", "vivo", "vives", "me", "mi",
            "gusta", "llamo", "hola", "gracias", "bien", "muy", "sí", "si", "y", "en", "de", "el", "la", "un", "una",
            "trabajo", "estudio", "hablo", "quiero", "tienen", "somos", "son", "también"}


def _phrase_key(t):
    return re.sub(r"[¡!¿?.,…]", "", t.lower()).strip()


# Gotowe, sprawdzone tłumaczenia najczęstszych krótkich zwrotów bota
PHRASEBOOK = {_phrase_key(k): v for k, v in {
    "¡Hola!": "Cześć!", "¡Hola! ¿Qué tal?": "Cześć! Co słychać?", "¿Qué tal?": "Co słychać?",
    "¡Buenos días!": "Dzień dobry!", "¡Buenas tardes!": "Dzień dobry!", "¡Buenas noches!": "Dobry wieczór!",
    "¿Cómo estás?": "Jak się masz?", "¿Cómo te llamas?": "Jak masz na imię?", "¿De dónde eres?": "Skąd jesteś?",
    "¿Dónde vives?": "Gdzie mieszkasz?", "¿Y tú?": "A ty?", "¡Qué bien!": "Super!", "¡Genial!": "Świetnie!",
    "¡Perfecto!": "Doskonale!", "¡Muy bien!": "Bardzo dobrze!", "¡Qué interesante!": "Ciekawe!",
    "Vale.": "Okej.", "Entiendo.": "Rozumiem.", "¡Encantado!": "Miło mi!", "¡Claro!": "Jasne!",
    "¡Qué guay!": "Ale super!", "¡Qué pena!": "Szkoda!", "¡Hasta luego!": "Na razie!", "¡Adiós!": "Do widzenia!",
    "Gracias.": "Dziękuję.", "¡Muchas gracias!": "Bardzo dziękuję!", "¿Tienes hermanos?": "Masz rodzeństwo?",
    "¿Tienes mascotas?": "Masz zwierzęta?", "¿A qué te dedicas?": "Czym się zajmujesz?",
    "¿Trabajas o estudias?": "Pracujesz czy studiujesz?", "¿Qué te gusta hacer?": "Co lubisz robić?",
    "¿Qué haces en tu tiempo libre?": "Co robisz w wolnym czasie?", "Yo también.": "Ja też.",
    "A mí también.": "Ja też.", "A mí no.": "Ja nie.", "¿Cuántos años tienes?": "Ile masz lat?",
}.items()}

PHRASEBOOK_EN = {_phrase_key(k): v for k, v in {
    "¡Hola!": "Hi!", "¡Hola! ¿Qué tal?": "Hi! How's it going?", "¿Qué tal?": "How's it going?",
    "¡Buenos días!": "Good morning!", "¡Buenas tardes!": "Good afternoon!", "¡Buenas noches!": "Good evening!",
    "¿Cómo estás?": "How are you?", "¿Cómo te llamas?": "What's your name?", "¿De dónde eres?": "Where are you from?",
    "¿Dónde vives?": "Where do you live?", "¿Y tú?": "And you?", "¡Qué bien!": "Great!", "¡Genial!": "Brilliant!",
    "¡Perfecto!": "Perfect!", "¡Muy bien!": "Very good!", "¡Qué interesante!": "How interesting!",
    "Vale.": "OK.", "Entiendo.": "I see.", "¡Encantado!": "Nice to meet you!", "¡Claro!": "Of course!",
    "¡Qué guay!": "How cool!", "¡Qué pena!": "What a shame!", "¡Hasta luego!": "See you!", "¡Adiós!": "Goodbye!",
    "Gracias.": "Thank you.", "¡Muchas gracias!": "Thank you very much!", "¿Tienes hermanos?": "Do you have brothers or sisters?",
    "¿Tienes mascotas?": "Do you have any pets?", "¿A qué te dedicas?": "What do you do?",
    "¿Trabajas o estudias?": "Do you work or study?", "¿Qué te gusta hacer?": "What do you like doing?",
    "¿Qué haces en tu tiempo libre?": "What do you do in your free time?", "Yo también.": "Me too.",
    "A mí también.": "Me too.", "A mí no.": "Not me.", "¿Cuántos años tienes?": "How old are you?",
}.items()}


def phrasebook():
    return PHRASEBOOK_EN if i18n.LANG == "en" else PHRASEBOOK


_EN_WORDS = {"how", "do", "does", "did", "say", "what", "what's", "whats", "why", "when", "which", "mean", "means",
             "the", "is", "are", "can", "could", "explain", "english", "help", "please", "difference", "between",
             "should", "use", "word", "this", "that", "i", "i'm", "im", "don't", "dont", "understand", "you",
             "of", "for", "with", "and", "but", "only", "too", "want", "would", "like", "spanish", "to"}


_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]+")


def is_native(text):
    """The learner writes/speaks in their own language (asking for help), not in Spanish."""
    if i18n.LANG == "en":
        t = (text or "").lower()
        words = re.findall(r"[a-záéíóúüñ']+", t)
        en = sum(w in _EN_WORDS for w in words)
        es = sum(w in _ES_HINT for w in words if w not in _EN_WORDS)
        return en >= 2 and en > es
    return is_polish(text)


def is_polish(text):
    """Uczeń pisze/mówi po polsku (pytanie o pomoc), a nie po hiszpańsku."""
    t = (text or "").lower()
    if not t.strip():
        return False
    words = re.findall(r"[a-ząćęłńóśźżáéíóúüñ]+", t)
    if not words:
        return False
    pl = sum(w in _PL_WORDS for w in words) + (2 if any(c in _PL_CHARS for c in t) else 0)
    es = sum(w in _ES_HINT for w in words)
    return pl >= 1 and pl > es


GRAMMAR_REF = """Quick reference (use it, it is correct):
ser: yo soy, tú eres, él/ella es, nosotros somos, vosotros sois, ellos son
estar: estoy, estás, está, estamos, estáis, están
tener: tengo, tienes, tiene, tenemos, tenéis, tienen
ir: voy, vas, va, vamos, vais, van
hablar: hablo, hablas, habla, hablamos, habláis, hablan
comer: como, comes, come, comemos, coméis, comen; vivir: vivo, vives, vive, vivimos, vivís, viven
"""
SER_ESTAR = {"Polish": "ser = tożsamość, zawód, narodowość, cechy stałe, skąd jesteś; "
                       "estar = położenie, stan, samopoczucie, miejsce",
             "English": "ser = identity, job, nationality, permanent traits, where you are from; "
                        "estar = location, state, how you feel, place"}


EXPLAIN_EN = ("You are a friendly teacher of Spanish (castellano, Spain) for an English speaker at level A1. "
              "The learner asks a question in English. Answer in clear, natural English: briefly (max. 6 lines). "
              "If the learner asks \"how do I say…\", the FIRST line is the ready Spanish sentence they want to say "
              "(in their person, natural, castellano), followed by the English translation; then 1–2 sentences of "
              "explanation (the verbs and forms used) and maybe 1–2 similar examples in the format: Spanish sentence "
              "— English translation. Silently fix the learner's typos. For questions about a rule: the rule first, "
              "then 2–3 simple examples. If the learner used a wrong form, point out the right one. "
              "No markdown or asterisks. Do not invent words.\n"
              "Example answer to \"how do I say: I have a dog\":\n"
              "Tengo un perro. — I have a dog.\n"
              "The verb tener (to have) in the first person singular is \"tengo\".\n"
              "Likewise: Tengo una hermana. — I have a sister.\n")

_TR_RULES = {
    "English": ("You translate the lines of a Spanish conversation partner into natural, correct English for a learner.\n"
                "RULES:\n"
                "- Translate EVERY line COMPLETELY: keep every piece of information (who, what, where, when, numbers).\n"
                "  Never shorten a sentence to \"Me too\" / \"Me neither\" when it says more.\n"
                "- Keep the numbering: one translated line for each numbered line, nothing else.\n"
                "- Translate the meaning naturally, the way a native speaker says it; no comments, quotes or emoji.\n"
                "- \"usted\" (su, le, tome, siga) is a polite YOU: \"Su mesa\" = \"Your table\", never his/her.\n"
                "Examples:\n"
                "1. Yo también juego al tenis. → 1. I play tennis too.\n"
                "2. Yo tampoco como carne. → 2. I don't eat meat either.\n"
                "3. A mí también me gusta leer. → 3. I like reading too.\n"
                "4. A mí también. → 4. Me too.\n"
                "5. ¡Encantada, Ana! → 5. Nice to meet you, Ana!\n"
                "6. ¿Vienes mucho a este parque? → 6. Do you come to this park often?\n"
                "7. ¿Quedamos el viernes? → 7. Shall we meet on Friday?\n"
                "8. Son dos euros con veinte. → 8. That's two euros twenty.\n"
                "9. Su mesa está lista, señor. → 9. Your table is ready, sir.\n"
                "10. Tome esta pastilla por la noche. → 10. Take this pill at night.\n"
                "11. El invierno pasado fui a Polonia. → 11. Last winter I went to Poland.\n"
                "12. ¿Te gusta el café o más bien el té? → 12. Do you prefer coffee or tea?"),
    "Polish": ("Tłumaczysz kwestie hiszpańskiego rozmówcy na naturalną, POPRAWNĄ GRAMATYCZNIE polszczyznę dla ucznia.\n"
               "ZASADY:\n"
               "- Tłumacz KAŻDĄ linijkę W CAŁOŚCI: zachowaj każdą informację (kto, co, gdzie, kiedy, liczby).\n"
               "  Nigdy nie skracaj zdania do „Ja też” / „Ja też nie”, gdy mówi więcej.\n"
               "- Zachowaj numerację: jedna przetłumaczona linijka na każdą numerowaną linijkę, nic więcej.\n"
               "- Tłumacz sens, tak jak mówi Polak w swobodnej rozmowie; poprawne przypadki i odmiana; "
               "bez komentarzy, cudzysłowów i emoji.\n"
               "- „tú” = „ty”. „usted” (su, le, tome, siga) to forma grzecznościowa: Pan/Pani, „proszę…”.\n"
               "- Nigdy kalek: „czy cię podoba”, „czy byś”, „co słuchasz” (poprawnie: podoba ci się, czego słuchasz).\n"
               "Przykłady:\n"
               "1. Yo también juego al tenis. → 1. Ja też gram w tenisa.\n"
               "2. Yo tampoco como carne. → 2. Ja też nie jem mięsa.\n"
               "3. A mí también me gusta leer. → 3. Ja też lubię czytać.\n"
               "4. A mí también. → 4. Ja też.\n"
               "5. ¡Encantada, Ana! → 5. Miło mi, Ano!\n"
               "6. ¿Te gusta tu barrio? → 6. Podoba ci się twoja dzielnica?\n"
               "7. ¿Vienes mucho a este parque? → 7. Często przychodzisz do tego parku?\n"
               "8. ¿Quedamos el viernes? → 8. Umówimy się na piątek?\n"
               "9. Son dos euros con veinte. → 9. Razem dwa euro dwadzieścia.\n"
               "10. Su mesa está lista, señor. → 10. Pana stolik jest gotowy.\n"
               "11. Tome esta pastilla por la noche. → 11. Proszę brać tę tabletkę wieczorem.\n"
               "12. El invierno pasado fui a Polonia. → 12. Zeszłej zimy pojechałem do Polski.\n"
               "13. ¿Qué libros lees? → 13. Jakie książki czytasz?\n"
               "14. Mi madre es profesora. → 14. Moja mama jest nauczycielką.\n"
               "15. ¿Cómo es tu casa? → 15. Jaki jest twój dom?\n"
               "16. ¿Te gusta el café o más bien el té? → 16. Wolisz kawę czy herbatę?"),
}
TRANSLATE_PROMPT = _TR_RULES
PROOF_PL = ("Jesteś korektorem polszczyzny. Popraw w każdej numerowanej linijce błędy odmiany (przypadki, rodzaj, "
            "końcówki), kalki i nienaturalne sformułowania. Mówi mężczyzna (Paco). Nie zmieniaj sensu, nie usuwaj "
            "informacji, zachowaj numerację. Wypisz tylko poprawione linijki.")


_ES_LIGHT = {"a", "mí", "mi", "me", "te", "se", "nos", "os", "le", "les", "el", "la", "los", "las", "lo", "un", "una",
             "unos", "unas", "y", "de", "del", "al", "que"}


def _too_short(es, tr):
    """A translation that lost content ("Yo también tomo café." → "Me too."): much fewer words than the
    Spanish sentence, counting only Spanish words that carry meaning (not articles, "a mí", "me"…)."""
    n_es = len([w for w in re.findall(r"\w+", es.lower()) if w not in _ES_LIGHT])
    return n_es >= 3 and len(re.findall(r"\w+", tr or "")) < 0.6 * n_es


def _too_long(es, tr):
    """A "translation" that adds content the Spanish sentence does not have (the model answered instead)."""
    n_es = len(re.findall(r"\w+", es))
    return len(re.findall(r"\w+", tr or "")) > 1.6 * n_es + 3


CHECK_PROMPT = """You check ONE sentence written by a beginner learner of Spanish (castellano, Spain), level A1–A2.
Find REAL mistakes only: wrong verb form or person (yo tiene → yo tengo), ser/estar, gender or number agreement
(la coche, los casa), wrong preposition or article, gustar used wrongly (yo gusto → me gusta), a wrong word.
IGNORE: missing accents, ¿ ¡, capital letters, punctuation, and any style or word choice that is correct.
Short, simple sentences are fine. Never change the meaning, numbers, names or facts — fix only the mistake.
If the sentence is correct, answer exactly: OK
If it has a mistake, answer exactly:
<ok>the whole corrected sentence</ok><fix>one short explanation in {nat}</fix>

Examples:
Tengo dos hermanas. -> OK
Me llamo Jarek y vivo en Rumia. -> OK
soy informatico -> OK
Me gusta cocinar. -> OK
Estoy cansado hoy. -> OK
Yo tiene dos hermanos. -> <ok>Yo tengo dos hermanos.</ok><fix>{ex1}</fix>
Yo es informático. -> <ok>Yo soy informático.</ok><fix>{ex2}</fix>
Soy en Madrid. -> <ok>Estoy en Madrid.</ok><fix>{ex3}</fix>
Yo gusto el café. -> <ok>Me gusta el café.</ok><fix>{ex4}</fix>"""

CHECK_EXAMPLES = {
    "Polish": ("Z „yo” używamy formy „tengo” (ja mam), nie „tiene”.",
               "Z „yo” czasownik ser ma formę „soy”, nie „es”.",
               "Miejsce, w którym ktoś jest, wyrażamy czasownikiem estar: „estoy”.",
               "„Lubię” to „me gusta” — rzecz, którą lubisz, jest podmiotem."),
    "English": ("With “yo” the form is “tengo” (I have), not “tiene”.",
                "With “yo” the verb ser is “soy”, not “es”.",
                "Where someone is takes estar: “estoy”.",
                "“I like” is “me gusta” — the thing you like is the subject."),
}


_PRONOUNS = {"yo", "tu", "el", "ella", "usted", "nosotros", "nosotras", "vosotros", "vosotras", "ellos",
             "ellas", "ustedes"}


def check_sentence(backend, text):
    """Separate grammar check of the learner's sentence → (ok, fix); ("", "") when it is correct.
    None when the check could not run (the reply's own <ok>/<fix> is used then)."""
    from .answers import norm
    nat = native()
    ex = CHECK_EXAMPLES[nat]
    system = CHECK_PROMPT.format(nat=nat, ex1=ex[0], ex2=ex[1], ex3=ex[2], ex4=ex[3])
    try:
        try:
            raw = backend.chat(system, [{"role": "user", "content": text}], temperature=0)
        except TypeError:
            raw = backend.chat(system, [{"role": "user", "content": text}])
    except Exception:  # noqa
        return None
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    m_ok, m_fix = re.search(r"<ok>(.*?)</ok>", raw, re.S), re.search(r"<fix>(.*?)</fix>", raw, re.S)
    if not m_ok:
        return ("", "") if raw.upper().startswith("OK") else None
    ok, fix = m_ok.group(1).strip(), (m_fix.group(1).strip() if m_fix else "")
    import difflib
    def bare(x):                              # without accents, punctuation and subject pronouns
        return [w for w in norm(x, False).split() if w not in _PRONOUNS]
    if not ok or bare(ok) == bare(text):
        return "", ""                         # only accents / punctuation / "yo" differ
    if difflib.SequenceMatcher(None, norm(ok, False), norm(text, False)).ratio() < 0.6:
        return "", ""                         # a rewrite, not a correction — do not trust it
    return ok, fix


def _same(a, b):
    import difflib
    n = lambda x: re.sub(r"[^a-záéíóúüñ ]", "", x.lower()).strip()
    return bool(a and b) and difflib.SequenceMatcher(None, n(a), n(b)).ratio() > 0.8


class SentenceStream:
    """Wyciąga z napływającego tekstu zdania z tagu <es>…</es>, gdy tylko są kompletne."""
    END = re.compile(r"(?<=[.!?…])\s+")

    def __init__(self):
        self.raw = ""
        self.sent = 0       # ile znaków części <es> już oddano
        self.closed = False

    def _es(self):
        t = re.sub(r"<think>.*?</think>", "", self.raw, flags=re.S)
        if "<think>" in t:
            return "", False
        m = re.search(r"<es>", t)
        if m:
            body = t[m.end():]
            e = body.find("</es>")
            return (body[:e], True) if e >= 0 else (body, False)
        if t.strip() and not t.lstrip().startswith("<") and len(t) > 12:
            return t, False   # model pominął tagi
        return "", False

    def feed(self, chunk):
        self.raw += chunk
        body, closed = self._es()
        pend = body[self.sent:]
        out = []
        while True:
            m = self.END.search(pend)
            if not m:
                break
            piece = pend[:m.start()].strip()
            self.sent += m.end()
            pend = pend[m.end():]
            if piece:
                out.append(piece)
        if closed and not self.closed:
            self.closed = True
            rest = pend.strip()
            self.sent = len(body)
            if rest:
                out.append(rest)
        return out

    def finish(self):
        body, _closed = self._es()
        rest = body[self.sent:].strip()
        self.sent = len(body)
        return [rest] if rest else []


# ------------------------------------------------------------------ silniki
_SECRET_ATTRS = {"app": "linux-espanol-learning", "what": "claude-api-key"}


def _keyring():
    """Zwraca (Secret, schema) gdy dostępny systemowy schowek (libsecret), inaczej None."""
    try:
        import gi
        gi.require_version("Secret", "1")
        from gi.repository import Secret
        schema = Secret.Schema.new("pl.jgu.LinuxEspanolLearning", Secret.SchemaFlags.NONE,
                                   {"app": Secret.SchemaAttributeType.STRING,
                                    "what": Secret.SchemaAttributeType.STRING})
        return Secret, schema
    except Exception:  # noqa
        return None


def _file_key():
    try:
        return open(KEY_FILE).read().strip()
    except OSError:
        return ""


def load_api_key():
    """Klucz API: najpierw systemowy schowek (GNOME Keyring); stary plik jest do niego migrowany."""
    kr = _keyring()
    if kr:
        Secret, schema = kr
        try:
            v = Secret.password_lookup_sync(schema, _SECRET_ATTRS, None)
        except Exception:  # noqa
            v = None
        if v:
            return v.strip()
        old = _file_key()
        if old:
            try:
                if Secret.password_store_sync(schema, _SECRET_ATTRS, Secret.COLLECTION_DEFAULT,
                                              "Linux Español Learning — klucz Claude API", old, None):
                    os.remove(KEY_FILE)
            except Exception:  # noqa
                pass
            return old
        return ""
    return _file_key()


def save_api_key(key):
    key = key.strip()
    kr = _keyring()
    if kr:
        Secret, schema = kr
        try:
            if key:
                ok = Secret.password_store_sync(schema, _SECRET_ATTRS, Secret.COLLECTION_DEFAULT,
                                                "Linux Español Learning — klucz Claude API", key, None)
            else:
                Secret.password_clear_sync(schema, _SECRET_ATTRS, None)
                ok = True
            if ok:
                try:
                    os.remove(KEY_FILE)
                except OSError:
                    pass
                return
        except Exception:  # noqa
            pass
    os.makedirs(CONFIG_DIR, exist_ok=True)         # awaryjnie: plik z prawami 600
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key)


def _post(url, body, headers, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")[:300]
        raise RuntimeError(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(_("brak połączenia ({})").format(e.reason))


# num_ctx: domyślne 2048 tokenów ucinało początek instrukcji (lista słówek) — model „głupiał”
OLLAMA_OPTIONS = {"temperature": 0.75, "top_p": 0.9, "repeat_penalty": 1.15, "num_ctx": 8192}


class OllamaBackend:
    name = _("Ollama (lokalnie)")

    def __init__(self, url, model, managed=False):
        self.url = url.rstrip("/")
        self.model = model
        self.managed = managed

    def chat(self, system, messages, temperature=None):
        if not self.model:
            raise RuntimeError(_("Nie wybrano modelu Ollama w Ustawieniach."))
        if self.managed:
            from .ollama_local import Manager
            self.url = Manager.ensure_running()
        opts = dict(OLLAMA_OPTIONS, **({"temperature": temperature, "repeat_penalty": 1.0}
                                       if temperature is not None else {}))
        body = {"model": self.model, "stream": False, "think": False, "options": opts,
                "messages": [{"role": "system", "content": system}] + messages}
        r = _post(self.url + "/api/chat", body, {"Content-Type": "application/json"}, timeout=300)
        return re.sub(r"<think>.*?</think>", "", r.get("message", {}).get("content", ""), flags=re.S)

    def chat_stream(self, system, messages):
        """Generator kawałków tekstu."""
        if not self.model:
            raise RuntimeError(_("Nie wybrano modelu Ollama w Ustawieniach."))
        if self.managed:
            from .ollama_local import Manager
            self.url = Manager.ensure_running()
        body = {"model": self.model, "stream": True, "think": False, "options": OLLAMA_OPTIONS,
                "messages": [{"role": "system", "content": system}] + messages}
        req = urllib.request.Request(self.url + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                for line in r:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line.decode())
                    piece = d.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if d.get("done"):
                        break
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='ignore')[:300]}")
        except urllib.error.URLError as e:
            raise RuntimeError(_("brak połączenia ({})").format(e.reason))

    @staticmethod
    def list_models(url):
        with urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=5) as r:
            data = json.loads(r.read().decode())
        return [m["name"] for m in data.get("models", [])]


class ClaudeBackend:
    name = _("Claude API (chmura)")

    def __init__(self, key, model):
        self.key, self.model = key, model

    def chat(self, system, messages, temperature=None):
        if not self.key:
            raise RuntimeError(_("Brak klucza API Claude — wpisz go w Ustawieniach."))
        body = {"model": self.model, "max_tokens": 600, "system": system, "messages": messages}
        if temperature is not None:
            body["temperature"] = temperature
        r = _post("https://api.anthropic.com/v1/messages", body,
                  {"Content-Type": "application/json", "x-api-key": self.key,
                   "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")


def _claude_stream(self, system, messages):
    if not self.key:
        raise RuntimeError(_("Brak klucza API Claude — wpisz go w Ustawieniach."))
    body = {"model": self.model, "max_tokens": 400, "system": system, "messages": messages, "stream": True}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-api-key": self.key,
                                          "anthropic-version": "2023-06-01"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            for line in r:
                line = line.decode().strip()
                if not line.startswith("data:"):
                    continue
                try:
                    d = json.loads(line[5:].strip())
                except ValueError:
                    continue
                if d.get("type") == "content_block_delta" and d.get("delta", {}).get("type") == "text_delta":
                    yield d["delta"].get("text", "")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='ignore')[:300]}")
    except urllib.error.URLError as e:
        raise RuntimeError(_("brak połączenia ({})").format(e.reason))


ClaudeBackend.chat_stream = _claude_stream


BIELIK = "SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M"


def translator(db):
    """Separate model for translations and explanations (the chat itself stays on the main engine):
    Claude API when chosen and a key is set; in the Polish course Bielik (a Polish offline model) when chosen."""
    if db.get("bot_backend", "ollama") != "ollama":
        return None
    if db.get("pl_claude", False) and load_api_key():
        return ClaudeBackend(load_api_key(), "claude-sonnet-5-5")
    if db.get("pl_bielik", False) and i18n.LANG == "pl":
        return OllamaBackend(db.get("ollama_url", "http://localhost:11434"), BIELIK,
                             managed=bool(db.get("ollama_managed", False)))
    return None


def make_backend(db):
    kind = db.get("bot_backend", "ollama")
    if kind == "claude":
        return ClaudeBackend(load_api_key(), db.get("claude_model", "claude-haiku-5-5"))
    return OllamaBackend(db.get("ollama_url", "http://localhost:11434"), db.get("ollama_model", ""),
                         managed=bool(db.get("ollama_managed", False)))


def rate(summary):
    """Ocena rozmowy 0–100 i opis słowny."""
    n = summary["messages"]
    if not n:
        return 0, _("Brak wypowiedzi")
    ok = (n - len(summary["fixes"])) / n
    avg = summary["words"] / n
    score = round(60 * ok + 25 * min(1.0, avg / 8) + 15 * min(1.0, summary["unique"] / 20) * 1.0)
    label = (_("Świetnie!") if score >= 85 else _("Bardzo dobrze") if score >= 70 else _("Dobrze — tak trzymaj")
             if score >= 50 else _("Ćwicz dalej — każda rozmowa pomaga"))
    return score, label


# ------------------------------------------------------------------ rozmowa
class Conversation:
    def __init__(self, backend, profile, scenario, level="normal", manual=None, auto=None):
        self.backend, self.profile, self.scenario, self.level = backend, profile, scenario, level
        self.system = system_prompt(profile, scenario, level)
        self.manual = manual or {}
        self.auto = {k: list(v) for k, v in (auto or {}).items()}
        self.messages = []
        self.turns = []  # dict(who, es, pl, fix, ok, unknown)
        self.banned = set()   # słowa spoza lekcji, których bot już użył
        self.used_topics = []
        self.next_topic = ""
        self.helper = None    # opcjonalny silnik (Claude) tylko do polskich tłumaczeń/wyjaśnień
        self.on_help = None   # callback(tekst) wołany w wątku roboczym, gdy bot wyjaśnia coś po polsku

    def _pick_topic(self):
        """Dla swobodnej rozmowy: wybiera następny temat, którego jeszcze nie poruszono."""
        if self.scenario.get("id") != "free":
            return
        have = set(k for k, v in {**{k: v for k, v in self.manual.items() if v}, **self.auto}.items() if v)
        for key, text, fkeys in TOPIC_PLAN:
            if key in self.used_topics or (fkeys and any(f in have for f in fkeys)):
                continue
            self.used_topics.append(key)
            self.next_topic = text
            return
        self.next_topic = "anything new that fits the conversation (do not repeat earlier topics)"

    def _tutor_chat(self, system, text):
        be = self.helper or self.backend
        try:
            try:
                out = be.chat(system, [{"role": "user", "content": text}], temperature=0.2)
            except TypeError:
                out = be.chat(system, [{"role": "user", "content": text}])
        except Exception:  # noqa
            if be is self.backend:
                return ""
            try:
                out = self.backend.chat(system, [{"role": "user", "content": text}])
            except Exception:  # noqa
                return ""
        out = re.sub(r"<think>.*?</think>", "", out, flags=re.S)
        out = re.sub(r"</?[a-z]+>", "", out)
        out = re.sub(r"[*_#`]+", "", out)            # bez markdownu
        out = re.split(r"\n\s*Quick reference", out)[0]  # a model copying the grammar notes from the prompt
        return out.strip()

    def explain(self, text):
        """Odpowiedź PO POLSKU (EN: in English) na pytanie ucznia o hiszpański (osobna karta „Wyjaśnienie”)."""
        if i18n.LANG == "en":
            return self._tutor_chat(EXPLAIN_EN + GRAMMAR_REF + SER_ESTAR["English"], text)
        sysmsg = ("Jesteś życzliwym nauczycielem hiszpańskiego (castellano, Hiszpania) dla Polaka na poziomie A1. "
                  "Uczeń zadaje pytanie po polsku. Odpowiedz POPRAWNĄ, NATURALNĄ POLSZCZYZNĄ: krótko (maks. 6 linijek), "
                  "Jeśli uczeń pyta „jak powiedzieć…”, PIERWSZA linijka to gotowe zdanie po hiszpańsku, które chce powiedzieć "
                  "(w jego osobie, naturalne, castellano), a pod nim polskie tłumaczenie; potem 1–2 zdania wyjaśnienia "
                  "(użyte czasowniki i formy) i ewentualnie 1–2 podobne przykłady w formacie: hiszpańskie zdanie — "
                  "polskie tłumaczenie. Popraw literówki ucznia po cichu. Przy pytaniach o regułę: najpierw reguła, "
                  "potem 2–3 proste przykłady. Jeśli uczeń użył błędnej formy, wskaż poprawną. "
                  "Nie używaj markdownu ani gwiazdek. Nie wymyślaj słów; jeśli nie jesteś pewien polskiego słowa, "
                  "użyj prostszego.\n"
                  "Przykład odpowiedzi na pytanie „jak powiedzieć: mam psa”:\n"
                  "Tengo un perro. — Mam psa.\n"
                  "Czasownik tener (mieć) w 1. osobie liczby pojedynczej to „tengo”.\n"
                  "Podobnie: Tengo una hermana. — Mam siostrę.\n" + GRAMMAR_REF + SER_ESTAR["Polish"])
        return self._tutor_chat(sysmsg, text)

    def translate_pl(self, es):
        """Translation of Paco's reply into the course language (Polish or English), sentence by sentence:
        ready phrases from the phrasebook, the rest as a numbered list (no sentence can be dropped or merged);
        a sentence that comes back much shorter than the Spanish one is translated again on its own."""
        parts = [x for x in re.split(r"(?<=[.!?…])\s+", es.strip()) if x]
        if not parts:
            return ""
        book = phrasebook()
        out = [book.get(_phrase_key(x)) for x in parts]
        todo = [i for i, x in enumerate(out) if x is None]
        if todo:
            got = self._translate_lines([parts[i] for i in todo])
            if got is None:                       # numbering lost — one sentence per request
                got = [(self._translate_lines([parts[i]]) or [""])[0] for i in todo]
            for i, tr in zip(todo, got):
                if _too_short(parts[i], tr) or _too_long(parts[i], tr) or looks_spanish(tr) or not tr:
                    tr = (self._translate_lines([parts[i]]) or [tr])[0]
                if not tr or looks_spanish(tr) or _too_short(parts[i], tr) or _too_long(parts[i], tr):
                    return ""                     # better no translation than a wrong one
                out[i] = tr
            if native() == "Polish":
                self._proofread_pl(out, todo, parts)
        return " ".join(out).strip()

    def _proofread_pl(self, out, idx, parts):
        """Second pass for Polish: fixes inflection and calques in the model's lines (phrasebook lines stay)."""
        fixed = self._translate_lines_with(PROOF_PL, [out[i] for i in idx])
        for i, f in zip(idx, fixed or []):
            if f and not looks_spanish(f) and not _too_short(parts[i], f) and not _too_long(parts[i], f):
                out[i] = f

    def _translate_lines(self, sentences):
        """Numbered list in → the same numbered list translated. None when the numbering does not match."""
        return self._translate_lines_with(TRANSLATE_PROMPT[native()], sentences)

    def _translate_lines_with(self, system, sentences):
        text = "\n".join(f"{n}. {x}" for n, x in enumerate(sentences, 1))
        raw = self._tutor_chat(system, text)
        got = {}
        for line in raw.splitlines():
            m = re.match(r"\s*(\d+)[.)]\s*(.+)", line)
            if m:
                tr = m.group(2)
                if "→" in tr:                     # the model echoed "Spanish → n. translation"
                    tr = re.sub(r"^\s*\d+[.)]\s*", "", tr.rsplit("→", 1)[1])
                got[int(m.group(1))] = tr.strip().strip('"„”“')
        if sorted(got) != list(range(1, len(sentences) + 1)):
            if len(sentences) == 1 and raw.strip() and "\n" not in raw.strip():
                return [raw.strip().rsplit("→", 1)[-1].strip().strip('"„”“')]
            return None
        return [got[n] for n in range(1, len(sentences) + 1)]

    def _learn(self, text):
        for k, vals in extract_facts(text).items():
            cur = self.auto.setdefault(k, [])
            for v in vals:
                if v.lower() not in [x.lower() for x in cur]:
                    cur.append(v)

    def _system(self):
        facts = facts_prompt(self.manual, self.auto)
        base = self.system
        if facts:
            base += "\nKNOWN FACTS ABOUT THE LEARNER (true):\n" + facts
            topics = known_topics(self.manual, self.auto)
            if topics:
                base += ("\nYou already know: " + "; ".join(topics) + ". Do NOT ask about these again. Ask about "
                         "something NEW instead (e.g. family, job, hobbies, food, daily routine, weekend plans, "
                         "travel), and mention a known fact only to react to it.")
        if self.next_topic:
            base += ("\nTHIS TURN: after a tiny reaction (and maybe one short fact about yourself), ask ONE simple "
                     "question about: " + self.next_topic + ".")
        if not self.banned:
            return base
        return base + ("\nThe learner does NOT know these words — do not use them again: "
                              + ", ".join(sorted(self.banned)) + ".")

    def _finalize(self, r, last_user=""):
        """Porządkuje odpowiedź: poprawka po polsku, tylko o wypowiedzi ucznia, bez powtórzeń."""
        r.setdefault("ok", "")
        r["es"] = re.sub(r"\s{2,}", " ", _EMOJI.sub("", r.get("es", ""))).strip()
        if r["es"] and not r["es"].startswith("("):
            tr = self.translate_pl(r["es"])
            if tr:
                r["pl"] = tr
        if not last_user or last_user.startswith("(start)"):
            r["fix"] = r["ok"] = ""
        # „poprawka” będąca powtórzeniem zdania bota — odrzuć
        if r["fix"] and (_same(r["fix"], r["es"]) or r["fix"].strip() in r["es"]):
            r["fix"] = ""
        if r["ok"] and _same(r["ok"], r["es"]):
            r["ok"] = ""
        norm = lambda x: re.sub(r"[^a-zñ ]", "", re.sub(r"[áàä]", "a", re.sub(r"[éèë]", "e", re.sub(r"[íìï]", "i",
               re.sub(r"[óòö]", "o", re.sub(r"[úùü]", "u", x.lower())))))).split()
        if r["ok"] and last_user and norm(r["ok"]) == norm(last_user):   # to samo zdanie = brak błędu
            r["fix"] = r["ok"] = ""
        if r["fix"] and looks_spanish(r["fix"]):
            try:
                tr = self.backend.chat(f"Translate the user's text into {native()}. Output only the "
                                       f"{native()} translation.",
                                       [{"role": "user", "content": r["fix"]}]).strip()
                tr = re.sub(r"</?[a-z]+>", "", tr).strip()
                if tr and not looks_spanish(tr):
                    r["fix"] = tr
            except Exception:  # noqa
                pass
        if r["fix"] and not r["ok"] and last_user and _same(last_user, r["fix"]):
            r["fix"] = ""
        self.banned |= {w.lower() for w in r.get("unknown", [])}
        return r

    def _ask(self, extra=None):
        msgs = list(self.messages)
        if extra:
            msgs = msgs + [{"role": "user", "content": extra}] if not msgs or msgs[-1]["role"] == "assistant" \
                else msgs[:-1] + [{"role": "user", "content": msgs[-1]["content"] + "\n\n" + extra}]
        raw = self.backend.chat(self._system(), msgs)
        r = parse(raw)
        r["unknown"] = self.profile.unknown_words(r["es"])
        return r

    def _reply(self, extra=None):
        r = self._ask(extra)
        words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", r["es"])
        if len(r["unknown"]) >= 3 and len(r["unknown"]) > 0.2 * max(1, len(words)):
            hint = ("(Note for the tutor: your previous answer was too difficult. These words are probably unknown "
                    f"to the learner: {', '.join(sorted(set(r['unknown'])))}. Rewrite your answer more simply, "
                    "using only the known vocabulary and grammar. Same output format.)")
            r2 = self._ask((extra + "\n\n" if extra else "") + hint)
            if len(r2["unknown"]) <= len(r["unknown"]):
                r = r2
        _lu = next((m["content"] for m in reversed(self.messages) if m["role"] == "user"), "")
        _es, repeated = drop_repeats(r["es"], self._asked(), _lu, self._values())
        if repeated:
            r2 = self._ask((extra + "\n\n" if extra else "") +
                           "(Note for the tutor: you asked a question you already asked. Do NOT repeat any earlier "
                           "question; react to what the learner said and ask something NEW. Same output format.)")
            _es2, rep2 = drop_repeats(r2["es"], self._asked(), _lu, self._values())
            if rep2:
                r2["es"], r2["pl"] = _es2 or "¿Y tú?", ""
            r = r2
        prev = next((m["content"] for m in reversed(self.messages) if m["role"] == "assistant"), "")
        if prev and _same(prev, r["es"]):
            r2 = self._ask((extra + "\n\n" if extra else "") +
                           "(Note for the tutor: you just repeated your previous turn. Say something NEW and ask "
                           "a different simple question. Same output format.)")
            if not _same(prev, r2["es"]):
                r = r2
        return r

    def start(self):
        self._pick_topic()
        r = self._finalize(self._reply("(Start the conversation now with your first short line in your role. "
                                       "Greet the learner and ask a first simple question.)"))
        self.messages.append({"role": "user", "content": "(start)"})
        self.messages.append({"role": "assistant", "content": r["es"]})
        self.turns.append(dict(r, who="bot"))
        return r

    def _help_only(self, text):
        """Pytanie po polsku: tylko wyjaśnienie, rozmowa czeka, aż uczeń sam powie zdanie."""
        h = self.explain(text) if is_native(text) else ""
        if not h:
            return None
        if self.on_help:
            try:
                self.on_help(h)
            except Exception:  # noqa
                pass
        return dict(es="", pl="", fix="", ok="", unknown=[], help=h)

    def send(self, text):
        r = self._help_only(text)
        if r:
            return r
        self.turns.append(dict(who="me", es=text, pl="", fix="", unknown=[]))
        self._learn(text)
        self._pick_topic()
        self.messages.append({"role": "user", "content": text})
        check = self._check_async(text)
        r = self._finalize(self._apply_check(self._reply(), check), text)
        self.messages.append({"role": "assistant", "content": r["es"]})
        if r.get("fix"):
            self.turns[-1]["fix"] = r["fix"]
            self.turns[-1]["ok"] = r.get("ok", "")
        self.turns.append(dict(r, who="bot"))
        return r

    def _check_async(self, text):
        """Grammar check of the learner's sentence in a parallel thread (the reply is not slowed down)."""
        import threading
        box = {}
        checker = self.helper if isinstance(self.helper, ClaudeBackend) else self.backend
        th = threading.Thread(target=lambda: box.update(r=check_sentence(checker, text)),
                              daemon=True)
        th.start()
        return th, box

    @staticmethod
    def _apply_check(r, check):
        th, box = check
        th.join(60)
        res = box.get("r")
        if res is not None:                  # the separate check wins over the reply's own <ok>/<fix>
            r["ok"], r["fix"] = res
        return r

    def _values(self):
        """Wartości faktów o uczniu (miasto, praca, imię…) — bot nie może ich mówić o sobie."""
        out = [v for k, v in (self.manual or {}).items() if v and k != "notes" and k != "use"
               for v in re.split(r"[,;]", str(v))]
        for vals in self.auto.values():
            out += list(vals)
        return [v.strip() for v in out if v and len(v.strip()) >= 4]

    def _asked(self):
        return [x for t in self.turns if t["who"] == "bot"
                for x in re.split(r"(?<=[.!?…])\s+", t["es"]) if x.endswith("?")]

    def _stream_reply(self, on_sentence, extra=None):
        """Odpowiedź strumieniowo: on_sentence(zdanie) wołane na bieżąco (wątek roboczy).
        Bez automatycznego upraszczania — zdania są już czytane na głos."""
        msgs = list(self.messages)
        if extra:
            msgs = msgs + [{"role": "user", "content": extra}] if not msgs or msgs[-1]["role"] == "assistant" \
                else msgs[:-1] + [{"role": "user", "content": msgs[-1]["content"] + "\n\n" + extra}]
        ss = SentenceStream()
        asked, kept, state = self._asked(), [], {"dropped": False}
        vals = self._values()

        last_user = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")

        def emit(sent):
            if is_repeated_question(sent, asked) or is_echo(sent, last_user) or claims_learner_fact(sent, vals):
                state["dropped"] = True       # to pytanie już padło — nie powtarzamy
                return
            kept.append(sent)
            if sent.endswith("?"):
                asked.append(sent)
            on_sentence(sent)
        gen = self.backend.chat_stream(self._system(), msgs) if hasattr(self.backend, "chat_stream") \
            else iter([self.backend.chat(self._system(), msgs)])
        for chunk in gen:
            for sent in ss.feed(chunk):
                emit(sent)
        for sent in ss.finish():
            emit(sent)
        r = parse(re.sub(r"<think>.*?</think>", "", ss.raw, flags=re.S))
        if state["dropped"]:
            if not kept:
                kept.append("¿Y tú?")
                on_sentence("¿Y tú?")
            r["es"], r["pl"] = " ".join(kept), ""
        r["unknown"] = self.profile.unknown_words(r["es"])
        return r

    def start_stream(self, on_sentence):
        self._pick_topic()
        r = self._finalize(self._stream_reply(on_sentence, "(Start the conversation now with your first short line "
                                                           "in your role. Greet the learner and ask a first "
                                                           "simple question.)"))
        self.messages.append({"role": "user", "content": "(start)"})
        self.messages.append({"role": "assistant", "content": r["es"]})
        self.turns.append(dict(r, who="bot"))
        return r

    def send_stream(self, text, on_sentence):
        r = self._help_only(text)
        if r:
            return r
        self.turns.append(dict(who="me", es=text, pl="", fix="", unknown=[]))
        self._learn(text)
        self._pick_topic()
        self.messages.append({"role": "user", "content": text})
        check = self._check_async(text)
        r = self._finalize(self._apply_check(self._stream_reply(on_sentence), check), text)
        self.messages.append({"role": "assistant", "content": r["es"]})
        if r.get("fix"):
            self.turns[-1]["fix"] = r["fix"]
            self.turns[-1]["ok"] = r.get("ok", "")
        self.turns.append(dict(r, who="bot"))
        return r

    def make_memory(self):
        """Po rozmowie: prosi model o krótkie notatki „co zapamiętać o uczniu” (wołane w wątku roboczym)."""
        mine = [t for t in self.turns if t["who"] == "me"]
        if len(mine) < 2:
            return {}
        talk = "\n".join(("Learner: " if t["who"] == "me" else "Tutor: ") + t["es"] for t in self.turns)
        raw = self.backend.chat(
            "You write short memory notes about a language learner. Output ONLY the notes, no preface.",
            [{"role": "user", "content": talk + "\n\nWrite up to 5 short facts about the LEARNER mentioned in this "
              "conversation (one per line, in English, no numbering, only facts the learner actually said). "
              "Then one last line starting with 'TOPICS:' summarising what you talked about in at most 12 words."}])
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S)
        facts, topics = [], ""
        for line in raw.splitlines():
            line = line.strip(" -*•\t")
            if not line:
                continue
            if line.upper().startswith("TOPICS:"):
                topics = line[7:].strip()
            elif 3 < len(line) < 140 and "<" not in line:
                facts.append(line)
        out = {}
        if facts:
            out["memories"] = facts[:5]
        if topics:
            out["last_talk"] = [topics]
        return out

    def summary(self):
        mine = [t for t in self.turns if t["who"] == "me"]
        words = [w for t in mine for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", t["es"])]
        fixes = [(t["es"], t.get("ok", ""), t["fix"]) for t in mine if t.get("fix")]
        bot_unknown = sorted({w.lower() for t in self.turns if t["who"] == "bot" for w in t.get("unknown", [])})
        return dict(messages=len(mine), words=len(words), unique=len({w.lower() for w in words}),
                    fixes=fixes, bot_unknown=bot_unknown)
