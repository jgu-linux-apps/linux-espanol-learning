"""English version checks: python3 -m unittest discover -s tests (from src/)."""
import ast
import glob
import os
import re
import sys
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["ESPANOL_LANG"] = "pl"

from espanol import i18n  # noqa: E402
from espanol.content import Lesson  # noqa: E402
from espanol.i18n_en import EN  # noqa: E402

def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


CODE = sorted(glob.glob(os.path.join(ROOT, "src", "espanol", "*.py")) +
              glob.glob(os.path.join(ROOT, "src", "espanol", "ui", "*.py")))


def _uses_translation(tree):
    return any(isinstance(n, ast.ImportFrom) and n.module and n.module.endswith("i18n")
               and any(a.name == "_" for a in n.names) for n in ast.walk(tree))


class Translations(unittest.TestCase):
    def test_every_text_has_english(self):
        missing = []
        for f in CODE:
            for n in ast.walk(ast.parse(_read(f))):
                if isinstance(n, ast.Call) and getattr(n.func, "id", None) in ("_", "plural"):
                    args = n.args[:1] if n.func.id == "_" else n.args[1:]
                    missing += [(os.path.basename(f), a.value) for a in args
                                if isinstance(a, ast.Constant) and a.value not in EN]
        self.assertEqual(missing, [])

    def test_nothing_shadows_the_translation_function(self):
        """`_` as a variable or parameter would hide _() in files that translate (a crash in Care Check once)."""
        bad = []
        for f in CODE:
            tree = ast.parse(_read(f))
            if not _uses_translation(tree):
                continue
            for n in ast.walk(tree):
                if (isinstance(n, ast.Name) and n.id == "_" and isinstance(n.ctx, ast.Store)) or \
                        (isinstance(n, ast.arg) and n.arg == "_"):
                    bad.append((os.path.basename(f), n.lineno))
        self.assertEqual(bad, [])

    def test_placeholders_match(self):
        for pl, en in EN.items():
            self.assertEqual(pl.count("{"), en.count("{"), pl)

    def test_plural(self):
        i18n.LANG = "pl"
        self.assertEqual([i18n.plural(n, "zadanie", "zadania", "zadań") for n in (1, 2, 5, 12, 22)],
                         ["zadanie", "zadania", "zadań", "zadań", "zadania"])
        i18n.LANG = "en"
        self.assertEqual([i18n.plural(n, "zadanie", "zadania", "zadań") for n in (1, 2, 5)], ["task", "tasks", "tasks"])
        i18n.LANG = "pl"


class EnglishLessons(unittest.TestCase):
    def test_same_spanish_as_polish(self):
        for path in sorted(glob.glob(os.path.join(ROOT, "data", "en", "lessons", "*", "*.txt"))):
            rel = os.path.relpath(path, os.path.join(ROOT, "data", "en"))
            pl, en = Lesson(os.path.join(ROOT, "data", rel)), Lesson(path)
            with self.subTest(rel):
                self.assertEqual(pl.id, en.id)
                self.assertEqual([d[:2] for d in pl.dialog], [d[:2] for d in en.dialog])
                self.assertEqual([v["es"] for v in pl.vocab], [v["es"] for v in en.vocab])
                self.assertEqual([(e["type"], e["answers"], e.get("options")) for e in pl.exercises],
                                 [(e["type"], e["answers"], e.get("options")) for e in en.exercises])
                self.assertTrue(all(d[2] for d in en.dialog), "every dialogue line has a translation")
                text = _read(path).replace("Gdańsk", "")
                self.assertIsNone(re.search(r"[ąęłśźżćńĄĘŁŚŹŻĆŃ]", text), "no Polish left")


class EnglishReadingsAndVocabulary(unittest.TestCase):
    @staticmethod
    def _section(text, name):
        return text.split("@" + name + "\n", 1)[1].split("\n@", 1)[0]

    def test_readings_keep_the_spanish(self):
        for path in sorted(glob.glob(os.path.join(ROOT, "data", "en", "readings", "*.txt"))):
            en, pl = _read(path), _read(os.path.join(ROOT, "data", "readings", os.path.basename(path)))
            with self.subTest(os.path.basename(path)):
                for name in ("text", "questions"):
                    self.assertEqual(self._section(en, name), self._section(pl, name))
                self.assertIsNone(re.search(r"[ąęłśźżćńĄĘŁŚŹŻĆŃ]", en.replace("Gdańsk", "")))

    def test_extra_vocabulary_keeps_the_spanish(self):
        def words(path):
            return [line.split(" | ")[0] for line in _read(path).splitlines() if " | " in line and not line.startswith("//")]
        en = os.path.join(ROOT, "data", "en", "vocab_extra.txt")
        self.assertEqual(words(en), words(os.path.join(ROOT, "data", "vocab_extra.txt")))
        self.assertIsNone(re.search(r"[ąęłśźżćńĄĘŁŚŹŻĆŃ]", _read(en)))


class PacoInEnglish(unittest.TestCase):
    class _Profile:
        level, grammar, topics, vocab, lessons = "A1", ["present"], ["greetings"], ["hola"], [1]

    def tearDown(self):
        i18n.LANG = "pl"

    def test_prompt_follows_the_course_language(self):
        from espanol import bot
        for lang, native, other in (("pl", "Polish", "English"), ("en", "English", "Polish")):
            i18n.LANG = lang
            p = bot.system_prompt(self._Profile, bot.SCENARIOS[1], "hard")
            with self.subTest(lang):
                self.assertIn(f"{native}-speaking learner", p)
                self.assertIn(f"<pl>{native} translation", p)
                self.assertIn(f"its {native} meaning", p)
                self.assertNotIn(other, p)
                self.assertNotIn("{native}", p)
        self.assertNotIn("Poland", p)

    def test_help_questions_in_english(self):
        from espanol import bot
        i18n.LANG = "en"
        self.assertTrue(bot.is_native("How do I say I have a dog?"))
        self.assertTrue(bot.is_native("what is the difference between ser and estar"))
        self.assertFalse(bot.is_native("Me llamo Jarek y tengo un perro."))
        self.assertFalse(bot.is_native("Sí, me gusta la música."))

    def test_phrasebook_in_english(self):
        from espanol import bot
        i18n.LANG = "en"
        self.assertEqual(bot.phrasebook().get(bot._phrase_key("¿Tienes mascotas?")), "Do you have any pets?")
        self.assertEqual(set(bot.PHRASEBOOK_EN), set(bot.PHRASEBOOK))


class GrammarCheck(unittest.TestCase):
    """The separate check of the learner's sentence (fake model, no Ollama needed)."""
    class _Fake:
        def __init__(self, answer):
            self.answer, self.system = answer, ""

        def chat(self, system, messages, temperature=None):
            self.system = system
            return self.answer

    def tearDown(self):
        i18n.LANG = "pl"

    def check(self, text, answer):
        from espanol import bot
        return bot.check_sentence(self._Fake(answer), text)

    def test_mistake_is_reported(self):
        self.assertEqual(self.check("Yo tiene dos hermanos.", "<ok>Yo tengo dos hermanos.</ok><fix>tengo</fix>"),
                         ("Yo tengo dos hermanos.", "tengo"))

    def test_correct_sentence(self):
        self.assertEqual(self.check("Tengo dos hermanas.", "OK"), ("", ""))

    def test_accents_and_pronouns_are_not_mistakes(self):
        self.assertEqual(self.check("Soy informatico.", "<ok>Yo soy informático.</ok><fix>x</fix>"), ("", ""))

    def test_a_rewrite_is_not_trusted(self):
        self.assertEqual(self.check("Me gusta el cine.", "<ok>Los domingos voy al teatro con mi madre.</ok><fix>x</fix>"),
                         ("", ""))

    def test_explanation_language_follows_the_course(self):
        from espanol import bot
        for lang, word in (("pl", "Polish"), ("en", "English")):
            i18n.LANG = lang
            fake = self._Fake("OK")
            bot.check_sentence(fake, "Hola.")
            self.assertIn(f"explanation in {word}", fake.system)

    def test_failure_falls_back(self):
        from espanol import bot

        class Broken:
            def chat(self, *a, **k):
                raise RuntimeError("offline")
        self.assertIsNone(bot.check_sentence(Broken(), "Hola."))


class ReplyTranslation(unittest.TestCase):
    """Translation of Paco's replies: every sentence, nothing shortened (fake model, no Ollama needed)."""
    class _Model:
        def __init__(self, answers):
            self.answers, self.calls = list(answers), []

        def chat(self, system, messages, temperature=None):
            self.calls.append(messages[0]["content"])
            return self.answers.pop(0) if self.answers else ""

    def tearDown(self):
        i18n.LANG = "pl"

    def conv(self, answers):
        from espanol import bot
        c = bot.Conversation.__new__(bot.Conversation)
        c.backend, c.helper = self._Model(answers), None
        return c

    def test_shortened_sentence_is_translated_again(self):
        i18n.LANG = "en"
        c = self.conv(["1. Me too.\n2. Do you come to the bar sometimes?", "1. I drink coffee too."])
        self.assertEqual(c.translate_pl("¡Genial! Yo también tomo café. ¿Vienes a veces al bar?"),
                         "Brilliant! I drink coffee too. Do you come to the bar sometimes?")
        self.assertEqual(c.backend.calls[1], "1. Yo también tomo café.")

    def test_echoed_spanish_is_cut_off(self):
        i18n.LANG = "en"
        c = self.conv(["1. Vale, entiendo. → 1. OK, I see.\n2. ¿Tienes un perro? → 2. Do you have a dog?"])
        self.assertEqual(c.translate_pl("Vale, entiendo. ¿Tienes un perro?"), "OK, I see. Do you have a dog?")

    def test_phrasebook_lines_are_not_sent(self):
        i18n.LANG = "en"
        c = self.conv(["1. What do you do at the weekend?"])
        self.assertEqual(c.translate_pl("¡Hola! ¿Qué haces el fin de semana?"), "Hi! What do you do at the weekend?")
        self.assertEqual(c.backend.calls, ["1. ¿Qué haces el fin de semana?"])

    def test_no_translation_rather_than_a_wrong_one(self):
        i18n.LANG = "en"
        c = self.conv(["1. Me too.", "1. Me too."])
        self.assertEqual(c.translate_pl("Yo también tengo dos gatos negros."), "")

    def test_polish_gets_a_proofreading_pass(self):
        i18n.LANG = "pl"
        c = self.conv(["1. Mój brat jest informatykem.", "1. Mój brat jest informatykiem."])
        self.assertEqual(c.translate_pl("Mi hermano es informático."), "Mój brat jest informatykiem.")


class DeferredTranslation(unittest.TestCase):
    def test_reply_first_translation_later(self):
        from espanol import bot
        i18n.LANG = "en"
        try:
            c = bot.Conversation.__new__(bot.Conversation)
            c.backend, c.helper, c.banned, c.defer_translation = ReplyTranslation._Model(["1. Do you have a dog?"]), None, set(), True
            r = c._finalize(dict(es="¿Tienes un perro?", pl="", fix="", ok="", unknown=[]))
            self.assertEqual((r["pl"], r.get("pl_pending")), ("", True))
            self.assertEqual(c.backend.calls, [])                 # nothing translated yet
            turn = dict(r, who="bot")
            self.assertEqual(c.translate_turn(turn), "Do you have a dog?")
            self.assertEqual(turn["pl"], "Do you have a dog?")
            self.assertNotIn("pl_pending", turn)
        finally:
            i18n.LANG = "pl"


class TranslatorChoice(unittest.TestCase):
    class _DB(dict):
        def get(self, k, d=None):
            return super().get(k, d)

    def tearDown(self):
        i18n.LANG = "pl"

    def test_bielik_only_for_the_polish_course(self):
        from espanol import bot
        db = self._DB(bot_backend="ollama", pl_bielik=True, ollama_url="http://127.0.0.1:11435")
        i18n.LANG = "pl"
        self.assertEqual(bot.translator(db).model, bot.BIELIK)
        i18n.LANG = "en"
        self.assertIsNone(bot.translator(db))

    def test_off_by_default_and_not_with_claude_chat(self):
        from espanol import bot
        i18n.LANG = "pl"
        self.assertIsNone(bot.translator(self._DB(bot_backend="ollama")))
        self.assertIsNone(bot.translator(self._DB(bot_backend="claude", pl_bielik=True)))

    def test_made_up_content_is_rejected(self):
        from espanol import bot
        self.assertTrue(bot._too_long("¿Y qué haces los fines de semana?",
                                      "A ja w weekendy lubię spędzać czas z rodziną i przyjaciółmi, chodzić na "
                                      "spacery i odpoczywać."))
        self.assertFalse(bot._too_long("¿Quiere probársela?", "Czy chciałby Pan ją przymierzyć?"))

    def test_mistake_check_stays_on_the_chat_model(self):
        from espanol import bot
        c = bot.Conversation.__new__(bot.Conversation)
        c.backend = bot.OllamaBackend("x", "qwen3:8b")
        c.helper = bot.OllamaBackend("x", bot.BIELIK)
        seen = []
        orig = bot.check_sentence
        bot.check_sentence = lambda be, text: seen.append(be.model) or ("", "")
        try:
            th, _box = c._check_async("Hola.")
            th.join(5)
        finally:
            bot.check_sentence = orig
        self.assertEqual(seen, ["qwen3:8b"])


class ProfileNames(unittest.TestCase):
    def test_default_name_follows_the_profile_language(self):
        from espanol.profiles import display_name
        self.assertEqual(display_name({"name": "Główny", "lang": "en"}), "Main")
        self.assertEqual(display_name({"name": "Main", "lang": "pl"}), "Główny")
        self.assertEqual(display_name({"name": "Ola", "lang": "en"}), "Ola")


class DownloadSizes(unittest.TestCase):
    def test_sizes_in_english(self):
        """Sizes are translated at import time, so this runs in a fresh process with the English course."""
        import subprocess
        code = ("import sys; sys.path.insert(0, 'src'); from espanol import i18n; i18n.init(); "
                "from espanol import speech, ollama_local; "
                "from espanol.ui import bot_settings as b; "
                "print('|'.join([v[1] for v in speech.WHISPER_SIZES.values()] + [m[2] for m in ollama_local.MODELS]"
                " + list(b.SIZES.values())))")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                             env=dict(os.environ, ESPANOL_LANG="en")).stdout.strip()
        self.assertTrue(out, "no output")
        self.assertNotIn("ok.", out)
        self.assertIsNone(re.search(r"\d,\d", out), out)
        self.assertIn("about 150 MB", out)


class SpeechParts(unittest.TestCase):
    def test_slash_is_not_read(self):
        from espanol.speech import speech_parts
        self.assertEqual(speech_parts("el tío / la tía"), ["el tío", "la tía"])
        self.assertEqual(speech_parts("nosotros/as"), ["nosotros", "nosotras"])
        self.assertEqual(speech_parts("1/2 kilo"), ["1/2 kilo"])


if __name__ == "__main__":
    unittest.main()
