"""Rozmowa z botem (tekstowa) — ograniczona do materiału z ukończonych lekcji.

Silniki: Ollama (lokalnie, offline) albo API Claude (chmura)."""
import json
import os
import re
import urllib.request

from .answers import strip_accents
from .conjugate import conjugate
from .paths import XDG_CONFIG, PKG

CONFIG_DIR = os.path.join(XDG_CONFIG, PKG)
KEY_FILE = os.path.join(CONFIG_DIR, "claude_api_key")

CLAUDE_MODELS = {"claude-haiku-5-5": "Claude Haiku (szybki, tani)", "claude-sonnet-5-5": "Claude Sonnet (najlepszy)"}

# ------------------------------------------------------------------ scenki
SCENARIOS = [
    dict(id="free", title="Swobodna rozmowa o Tobie", lesson="a1-01",
         role=("Paco, a friendly, cheerful 30-year-old man from Madrid (a little robot-like in spirit, with a black beret and "
               "a moustache) you have just met at a language exchange (intercambio). Your name is Paco. "
               "You work as a graphic designer, live with your dog Toby, love cooking paella and cycling, and have a "
               "younger brother called Pablo. You are male: use masculine forms (encantado, contento)"),
         goal="Porozmawiaj o sobie: imię, skąd jesteś, praca, rodzina, zainteresowania — tylko tym, co już znasz."),
    dict(id="bar", title="W barze — zamów i zapłać", lesson="a1-13",
         role="a waiter (camarero) in a busy bar in Madrid",
         goal="Zamów coś do picia i jedzenia, zapytaj o cenę i zapłać kartą."),
    dict(id="mercado", title="Na targu", lesson="a1-14",
         role="a fruit and vegetable seller at a market in Valencia",
         goal="Kup owoce i warzywa (ilości w kilogramach), zapytaj, co jest dobre, powiedz, co lubisz."),
    dict(id="calle", title="Pytanie o drogę", lesson="a1-15",
         role="a local person on a street in Sevilla; the learner is a lost tourist",
         goal="Zapytaj, jak dojść do muzeum lub na dworzec, i upewnij się, że rozumiesz drogę."),
    dict(id="tienda", title="W sklepie z ubraniami", lesson="a1-16",
         role="a shop assistant (dependiente) in a clothes shop",
         goal="Znajdź kurtkę albo koszulę, zapytaj o rozmiar, kolor i cenę, przymierz i kup."),
    dict(id="planes", title="Plany na weekend", lesson="a1-19",
         role="a Spanish friend who wants to make plans for the weekend",
         goal="Umówcie się na weekend: co, gdzie, o której. Odmów jednej propozycji i zaproponuj inną."),
    dict(id="vacaciones", title="Ostatnie wakacje", lesson="a2-23",
         role="a Spanish colleague asking about the learner's last holidays",
         goal="Opowiedz o swoich ostatnich wakacjach w czasie przeszłym: gdzie byłeś, co robiłeś, jak było."),
    dict(id="hotel", title="Recepcja hotelu", lesson="a2-28",
         role="a hotel receptionist in Granada; there is a problem with the room",
         goal="Zamelduj się, zapytaj o śniadanie i zgłoś problem z pokojem."),
    dict(id="medico", title="U lekarza", lesson="a2-29",
         role="a doctor (médica) at a health centre in Spain",
         goal="Opisz objawy (co Cię boli, od kiedy) i zrozum zalecenia."),
    dict(id="entrevista", title="Rozmowa o pracę", lesson="a2-34",
         role="an interviewer from a Spanish IT company",
         goal="Opowiedz o swoim doświadczeniu, mocnych stronach i dlaczego chcesz tam pracować."),
    dict(id="piso", title="Wynajem mieszkania", lesson="a2-38",
         role="a landlady renting a flat in Valencia",
         goal="Zapytaj o mieszkanie: metraż, czynsz, opłaty, kaucję i umów się na oglądanie."),
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
    "easy": ("Wolno i prosto", "Bardzo krótkie, najprostsze zdania, bez nowych słów."),
    "normal": ("Normalnie", "Krótkie tury, najwyżej jedno nowe słowo."),
    "hard": ("Wyzwanie", "Dłuższe wypowiedzi, do dwóch nowych słów, mniej podpowiedzi."),
}
LEVEL_RULES = {
    "easy": ("- NO new words at all: use only the known vocabulary and the simplest present-tense sentences.\n"
             "- Very short turns: ONE or TWO sentences, max ~7 words each. Always end with a very simple question."),
    "normal": ("- At most ONE new word per turn, and only if really needed — then add its Polish meaning in brackets "
               "right after it.\n- Very short turns: 1–3 sentences, max ~12 words each. Always end with a simple "
               "question or prompt so the learner can answer."),
    "hard": ("- At most TWO new words per turn, each followed by its Polish meaning in brackets.\n"
             "- Natural, slightly longer turns: 2–4 sentences, max ~15 words each. Use the whole known grammar "
             "freely, ask open questions that need a full sentence to answer, and be less helpful with hints."),
}

FACT_LABELS = {"age": "age", "pets": "pets", "study": "studies", "memories": "things you remember about the learner",
               "last_talk": "what you talked about last time","name": "name", "city": "town/city", "country": "country", "job": "job or school",
               "family": "family", "hobbies": "interests", "notes": "other",
               "lives_in": "lives in", "from": "is from", "nationality": "nationality", "likes": "likes"}


FACT_LABELS_PL = {"age": "wiek", "pets": "zwierzęta", "study": "nauka", "memories": "bot pamięta",
                  "last_talk": "poprzednio rozmawialiście o","name": "imię", "city": "miejscowość", "country": "kraj", "job": "praca / szkoła",
                  "family": "rodzina", "hobbies": "zainteresowania", "notes": "inne", "lives_in": "mieszka w",
                  "from": "pochodzi z", "nationality": "narodowość", "likes": "lubi"}


def system_prompt(profile, scenario, level="normal"):
    vocab = ", ".join(profile.vocab[-300:])
    beginner = len(profile.lessons) < 6
    return f"""You are a conversation partner for a Polish learner of Spanish (level {profile.level}).
Speak the Spanish of Spain (castellano): use "vosotros", Spain vocabulary (coche, ordenador, móvil, zumo, vale) and tú with the learner unless your role is formal.

YOUR ROLE: {scenario['role']}.
LEARNER'S TASK (for your information): {scenario['goal']}

STRICT LIMITS — the learner only knows the material below:
- Grammar the learner knows: {"; ".join(profile.grammar)}. Do NOT use other tenses or moods (no subjunctive).
- Topics already studied: {"; ".join(profile.topics[-12:])}.
- Vocabulary the learner knows (prefer these words, plus very basic function words): {vocab}
{LEVEL_RULES.get(level, LEVEL_RULES["normal"])}
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
- Treat everything the learner says about themselves as TRUE. Towns and places they mention are real; they live in Poland unless they say otherwise (Poland is a country in Europe; a Polish town is not "near Poland", it is IN Poland).
- Never ask again about something the learner has already told you. React to it and ask a NEW follow-up question instead.

CORRECTIONS (about the LEARNER's last message only — never about your own sentences):
- If the learner's last message has a real mistake, put the corrected learner sentence in Spanish in <ok> and a short explanation WRITTEN IN POLISH (never in Spanish!) in <fix>. Also use the correct form naturally in your reply.
- If it is correct, leave both <ok></ok> and <fix></fix> empty. Ignore missing accents, capital letters and punctuation.
- If the learner writes in Polish or asks for help, help briefly in <fix> (in Polish), leave <ok> empty, and continue in simple Spanish.
- <fix> must always be Polish. Example: <ok>Me llamo Jarek.</ok><fix>Mówimy „me llamo”, nie „me llamo es”.</fix>
- Do not repeat or rephrase your previous turn: move the conversation forward with a NEW short question each time.

Stay in your role and on the topic of learning Spanish. Never write anything outside the tags.
OUTPUT FORMAT (exactly):
<es>your reply in Spanish</es>
<pl>Polish translation of your reply</pl>
<ok>corrected learner sentence in Spanish, or empty</ok>
<fix>short explanation in POLISH, or empty</fix>"""


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
        add("age", m.group(1) + " lat")
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


_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]+")


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
ser = tożsamość, zawód, narodowość, cechy stałe, skąd jesteś; estar = położenie, stan, samopoczucie, miejsce"""


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
        body, _ = self._es()
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
        raise RuntimeError(f"brak połączenia ({e.reason})")


# num_ctx: domyślne 2048 tokenów ucinało początek instrukcji (lista słówek) — model „głupiał”
OLLAMA_OPTIONS = {"temperature": 0.75, "top_p": 0.9, "repeat_penalty": 1.15, "num_ctx": 8192}


class OllamaBackend:
    name = "Ollama (lokalnie)"

    def __init__(self, url, model, managed=False):
        self.url = url.rstrip("/")
        self.model = model
        self.managed = managed

    def chat(self, system, messages, temperature=None):
        if not self.model:
            raise RuntimeError("Nie wybrano modelu Ollama w Ustawieniach.")
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
            raise RuntimeError("Nie wybrano modelu Ollama w Ustawieniach.")
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
            raise RuntimeError(f"brak połączenia ({e.reason})")

    @staticmethod
    def list_models(url):
        with urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=5) as r:
            data = json.loads(r.read().decode())
        return [m["name"] for m in data.get("models", [])]


class ClaudeBackend:
    name = "Claude API (chmura)"

    def __init__(self, key, model):
        self.key, self.model = key, model

    def chat(self, system, messages, temperature=None):
        if not self.key:
            raise RuntimeError("Brak klucza API Claude — wpisz go w Ustawieniach.")
        body = {"model": self.model, "max_tokens": 600, "system": system, "messages": messages}
        if temperature is not None:
            body["temperature"] = temperature
        r = _post("https://api.anthropic.com/v1/messages", body,
                  {"Content-Type": "application/json", "x-api-key": self.key,
                   "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")


def _claude_stream(self, system, messages):
    if not self.key:
        raise RuntimeError("Brak klucza API Claude — wpisz go w Ustawieniach.")
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
        raise RuntimeError(f"brak połączenia ({e.reason})")


ClaudeBackend.chat_stream = _claude_stream


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
        return 0, "Brak wypowiedzi"
    ok = (n - len(summary["fixes"])) / n
    avg = summary["words"] / n
    score = round(60 * ok + 25 * min(1.0, avg / 8) + 15 * min(1.0, summary["unique"] / 20) * 1.0)
    label = ("Świetnie!" if score >= 85 else "Bardzo dobrze" if score >= 70 else "Dobrze — tak trzymaj"
             if score >= 50 else "Ćwicz dalej — każda rozmowa pomaga")
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
        return out.strip()

    def explain(self, text):
        """Odpowiedź PO POLSKU na pytanie ucznia o hiszpański (osobna karta „Wyjaśnienie”)."""
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
                  "Podobnie: Tengo una hermana. — Mam siostrę.\n" + GRAMMAR_REF)
        return self._tutor_chat(sysmsg, text)

    def translate_pl(self, es):
        """Tłumaczenie zdań bota na polski: gotowe zwroty ze słowniczka + model (z przykładami trudnych
        konstrukcji) + krótka korekta polszczyzny."""
        parts = [x for x in re.split(r"(?<=[.!?…])\s+", es.strip()) if x]
        known = [PHRASEBOOK.get(_phrase_key(x)) for x in parts]
        a = 0
        while a < len(parts) and known[a] is not None:
            a += 1
        b = len(parts)
        while b > a and known[b - 1] is not None:
            b -= 1
        middle = ""
        if a < b:          # zdania spoza słowniczka (z ewentualnymi zwrotami pomiędzy) tłumaczy model
            sysmsg = ("Jesteś tłumaczem z hiszpańskiego na polski. Tłumacz SENS, nie słowo w słowo — tak, jak "
                      "powiedziałby to Polak w swobodnej rozmowie. Zachowaj formę „ty”. Wypisz tylko tłumaczenie, "
                      "bez komentarzy, cudzysłowów i emoji.\n"
                      "Trudne konstrukcje — tak tłumacz:\n"
                      "¿Te gusta el café o más bien el té? → Wolisz kawę czy herbatę?\n"
                      "¿Te gusta el fútbol? → Lubisz piłkę nożną?\n"
                      "Me encanta cocinar. → Uwielbiam gotować.\n"
                      "A mí también. → Ja też.\n"
                      "¿Qué haces en tu tiempo libre? → Co robisz w wolnym czasie?\n"
                      "¿A qué te dedicas? → Czym się zajmujesz?\n"
                      "Vale, entiendo. → Okej, rozumiem.\n"
                      "¿Vas a algún sitio en vacaciones? → Jedziesz gdzieś na wakacje?\n"
                      "Nigdy dosłownie: „czy cię podoba”, „czy ty lubisz bardziej”.")
            tr = self._tutor_chat(sysmsg, " ".join(parts[a:b]))
            if not tr or looks_spanish(tr):
                return ""
            middle = self._polish_check(tr)
        return " ".join([x for x in known[:a]] + ([middle] if middle else []) + [x for x in known[b:]]).strip()

    def _polish_check(self, pl):
        """Druga, krótka runda: popraw błędy gramatyczne i kalki w polskim zdaniu (bez zmiany sensu)."""
        sysmsg = ("Popraw błędy gramatyczne, przypadki i nienaturalne kalki w tym polskim tekście tak, by brzmiał "
                  "naturalnie w rozmowie. Nie zmieniaj sensu, nie dodawaj nic. Jeśli tekst jest poprawny, przepisz "
                  "go bez zmian. Wypisz tylko tekst.\n"
                  "Przykład: „Czy cię bardziej podoba kawa czy herbata?” → „Wolisz kawę czy herbatę?”")
        fixed = self._tutor_chat(sysmsg, pl)
        if not fixed or looks_spanish(fixed) or len(fixed) > 2 * len(pl) + 20:
            return pl
        return fixed

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
                tr = self.backend.chat("Translate the user's text into Polish. Output only the Polish translation.",
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
        h = self.explain(text) if is_polish(text) else ""
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
        r = self._finalize(self._reply(), text)
        self.messages.append({"role": "assistant", "content": r["es"]})
        if r.get("fix"):
            self.turns[-1]["fix"] = r["fix"]
            self.turns[-1]["ok"] = r.get("ok", "")
        self.turns.append(dict(r, who="bot"))
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
        r = self._finalize(self._stream_reply(on_sentence), text)
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
