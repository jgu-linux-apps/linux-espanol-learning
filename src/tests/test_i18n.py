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


class ProfileNames(unittest.TestCase):
    def test_default_name_follows_the_profile_language(self):
        from espanol.profiles import display_name
        self.assertEqual(display_name({"name": "Główny", "lang": "en"}), "Main")
        self.assertEqual(display_name({"name": "Main", "lang": "pl"}), "Główny")
        self.assertEqual(display_name({"name": "Ola", "lang": "en"}), "Ola")


class SpeechParts(unittest.TestCase):
    def test_slash_is_not_read(self):
        from espanol.speech import speech_parts
        self.assertEqual(speech_parts("el tío / la tía"), ["el tío", "la tía"])
        self.assertEqual(speech_parts("nosotros/as"), ["nosotros", "nosotras"])
        self.assertEqual(speech_parts("1/2 kilo"), ["1/2 kilo"])


if __name__ == "__main__":
    unittest.main()
