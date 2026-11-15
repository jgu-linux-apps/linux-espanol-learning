# -*- coding: utf-8 -*-
"""English interface texts (keys: the Polish texts in the code). Course content in English lives in data/en/."""
EN = {
    # ---- app.py: navigation, menu, profiles, about
    "Dzisiaj": "Today", "Kurs": "Course", "Powtórki": "Review", "Słownik ES–PL": "ES–EN dictionary",
    "Dyktando": "Dictation", "Scenki z Paco": "Scenes with Paco", "Rozmowa z botem": "Chat with the bot",
    "Czytanki": "Readings", "Filmy i słuchanie": "Videos and listening", "Statystyki": "Statistics",
    "Ustawienia": "Settings", "Nauka": "Learn", "Narzędzia": "Tools",
    "Kurs hiszpańskiego A1–A2 · Hiszpania": "Spanish course A1–A2 · Spain",
    "Skróty klawiszowe": "Keyboard shortcuts", "O programie": "About", "Zakończ": "Quit",
    "Profil użytkownika — osobny postęp dla każdej osoby": "Learner profile — separate progress for each person",
    "Anuluj": "Cancel", "Zmień nazwę profilu": "Rename profile",
    "Cały postęp, powtórki, historia rozmów i dane „O mnie” tego profilu zostaną trwale usunięte.":
        "All progress, reviews, chat history and the “About me” details of this profile will be deleted for good.",
    "Usuń": "Delete", "Przejdź do kolejnych ekranów menu": "Go to the next screens of the menu",
    "Ta lista skrótów": "This list of shortcuts", "Powtórki: Spacja / Enter": "Review: Space / Enter",
    "Pokaż odpowiedź": "Show the answer", "Powtórki: 1 2 3 4": "Review: 1 2 3 4",
    "Oceń fiszkę (znowu / trudne / dobrze / łatwe)": "Rate the card (again / hard / good / easy)",
    "Dyktando: F2 / F3 / F4": "Dictation: F2 / F3 / F4", "Posłuchaj / wolno / podpowiedź": "Listen / slowly / hint",
    "Dyktando: Enter": "Dictation: Enter", "Sprawdź / dalej": "Check / next",
    "Rozmowa z botem: Ctrl+M": "Chat with the bot: Ctrl+M", "Mikrofon: mów / skończ mówić": "Microphone: speak / stop speaking",
    "Scenki: Ctrl+Enter": "Scenes: Ctrl+Enter", "Następna kwestia": "Next line",
    "Prawdziwy kurs hiszpańskiego od zera (A1–A2, hiszpański z Hiszpanii)\nz lekcjami, słownikiem ES–PL, powtórkami FSRS, testami i oceną wymowy offline.\n\nCreated by: JGu\nSupported by Claude":
        "A real Spanish course from zero (A1–A2, Spanish from Spain)\nwith lessons, an ES–EN dictionary, FSRS reviews, tests and offline pronunciation scoring.\n\nCreated by: JGu\nSupported by Claude",
    "Freeware — darmowe użytkowanie.\nBez prawa do modyfikacji i rozpowszechniania zmienionych wersji.\n\nKomponenty pobierane osobno (Piper, faster-whisper, głosy, modele Whisper)\nmają własne licencje.":
        "Freeware — free to use.\nNo right to modify it or to distribute changed versions.\n\nComponents downloaded separately (Piper, faster-whisper, voices, Whisper models)\nhave their own licences.",
    "Profile na tym komputerze": "Profiles on this computer", "➕  Nowy profil…": "➕  New profile…",
    "✎  Zmień nazwę bieżącego…": "✎  Rename the current one…", "Nazwa (np. imię):": "Name (e.g. first name):",
    "Test — {}, dział {}: {}": "Test — {}, unit {}: {}",
    "Przejdź do Ustawień i kliknij „Zainstaluj / zaktualizuj komponenty”.":
        "Go to Settings and click “Install / update components”.",
    "Głosy es_ES davefx i sharvard (piper-voices)": "es_ES voices davefx and sharvard (piper-voices)",
    "FSRS — algorytm powtórek (open-spaced-repetition)": "FSRS — review scheduling algorithm (open-spaced-repetition)",
    "Usuń profil i jego postęp": "Delete the profile and its progress",
    "zostało Ci kilka minut do dzisiejszego celu ({} min). ¡Vamos!": "just a few minutes left to today's goal ({} min). ¡Vamos!",
    "Usunąć profil „{}”?": "Delete the profile “{}”?", "Egzamin próbny — poziom {}": "Mock exam — level {}",
    "Nie mogę odtworzyć: {}": "Can't play it: {}", "Masz serię {} dni — ": "You have a {}-day streak — ",

    # ---- exercise.py
    "Wybierz poprawną odpowiedź": "Choose the right answer", "Uzupełnij lukę": "Fill in the gap",
    "Przetłumacz na hiszpański": "Translate into Spanish", "Odmień czasownik": "Conjugate the verb",
    "Ułóż zdanie z rozsypanki": "Put the words in order", "Popraw zdanie z rozmowy z Paco": "Correct the sentence from your chat with Paco",
    "Wpisz poprawną odpowiedź": "Type the right answer", "Sprawdź": "Check",
    "Wpisz odpowiedź po hiszpańsku…": "Type the answer in Spanish…", "Dalej  →": "Next  →", "Nie wiem": "I don't know",
    "Klawisze 1–4 wybierają odpowiedź · Enter: dalej": "Keys 1–4 choose an answer · Enter: next",
    "Enter sprawdza odpowiedź, potem przechodzi dalej": "Enter checks the answer, then moves on",
    "Cofnij": "Back", "Posłuchaj i zapisz, co słyszysz.": "Listen and write what you hear.",
    "Odtwórz jeszcze raz": "Play again", "Podpowiedź: ": "Hint: ",
    "Dobrze, ale uważaj na akcenty": "Right, but mind the accents", "Prawie — literówka": "Almost — a typo",
    "Niestety nie": "Not quite",

    # ---- widgets.py, themes.py
    "Posłuchaj wolno": "Listen slowly", "Posłuchaj (prawy przycisk — wolniej)": "Listen (right click — slower)",
    "Coral (domyślny) — koral i słońce": "Coral (default) — coral and sunshine",
    "Pomarańcz — ciepły pomarańcz (dawny domyślny)": "Orange — warm orange (the former default)",
    "Aurora — fiolet i cyjan": "Aurora — violet and cyan", "Oliva — oliwka i terakota Andaluzji": "Oliva — olive and Andalusian terracotta",
    "España — czerwień i złoto": "España — red and gold", "Azulejo — błękit sewilskich kafli": "Azulejo — the blue of Seville tiles",

    # ---- content.py
    "rzeczownik r. męski": "masculine noun", "rzeczownik r. żeński": "feminine noun",
    "rzeczownik r. męski i żeński": "masculine and feminine noun", "rzeczownik l. mn. (męski)": "plural noun (masculine)",
    "rzeczownik l. mn. (żeński)": "plural noun (feminine)", "przysłówek": "adverb", "spójnik": "conjunction",
    "określnik": "determiner", "z rodzajnikiem lub bez": "with or without the article", "Dział {}": "Unit {}",
    "{} słowa, pierwsze zaczyna się na „{}”": "{} words, the first one starts with “{}”",
    "Posłuchaj i zapisz zdanie po hiszpańsku.": "Listen and write the sentence in Spanish.",
    "zaczyna się na „{}”, {} liter": "starts with “{}”, {} letters",
    "Przetłumacz na hiszpański: {}": "Translate into Spanish: {}", "Co znaczy „{}”?": "What does “{}” mean?",

    # ---- conjugate.py, fsrs.py
    "Presente (teraźniejszy)": "Presente (present)",
    "1 dzień": "1 day", "{} min": "{} min", "{} dni": "{} days",

    # ---- speech.py
    "Męski — Hiszpania (carlfm, lekki)": "Male — Spain (carlfm, light)", "Męski — Meksyk (ald)": "Male — Mexico (ald)",
    "Żeński — Meksyk (claude, wysoka jakość)": "Female — Mexico (claude, high quality)",
    "Dokładny": "Accurate", "Bardzo dokładny (zalecana karta NVIDIA)": "Very accurate (NVIDIA card recommended)",
    "Brak silnika mowy — dokończ instalację komponentów w Ustawieniach.":
        "No speech engine — finish installing the components in Settings.",
    "Krok 2/3: pobieranie głosów hiszpańskich (Hiszpania)…": "Step 2/3: downloading the Spanish voices (Spain)…",
    "pamięć RAM: {} GB (minimum 8 GB)": "RAM: {} GB (8 GB minimum)",
    "silnik mowy nie uruchomił się": "the speech engine did not start", "silnik mowy przerwał pracę": "the speech engine stopped",
    "polecenie zakończyło się błędem ({})": "the command failed ({})",
    "Krok 3/3: pobieranie modelu rozpoznawania mowy „{}” ({})… to może chwilę potrwać.":
        "Step 3/3: downloading the speech recognition model “{}” ({})… this may take a while.",

    # ---- backup.py
    "To nie jest plik kopii zapasowej (.zip).": "This is not a backup file (.zip).",
    "Plik nie wygląda na kopię z tej aplikacji.": "The file doesn't look like a backup from this app.",
    "Plik kopii jest zbyt duży.": "The backup file is too large.", "Kopia nie zawiera danych postępu.": "The backup has no progress data.",
    "Baza w kopii jest uszkodzona.": "The database in the backup is damaged.", "Profil": "Profile",

    # ---- ollama_local.py
    "Zalecany — bardzo dobry hiszpański (Qwen 3, 8B)": "Recommended — very good Spanish (Qwen 3, 8B)",
    "najlepiej z kartą NVIDIA 6–8 GB lub 16 GB RAM": "best with a 6–8 GB NVIDIA card or 16 GB RAM",
    "Najmądrzejszy — najlepsze rozmowy (Qwen 3, 14B)": "Smartest — the best conversations (Qwen 3, 14B)",
    "wymaga karty NVIDIA 12 GB+ lub 32 GB RAM; wolniejszy": "needs a 12 GB+ NVIDIA card or 32 GB RAM; slower",
    "Szybki — lżejszy model (Gemma 3, 4B)": "Fast — a lighter model (Gemma 3, 4B)",
    "dla słabszych komputerów; częściej się myli": "for slower computers; makes more mistakes",
    "Serwer Ollamy nie wystartował (szczegóły: ~/.local/share/linux-espanol-learning/ollama/serve.log)":
        "The Ollama server did not start (details: ~/.local/share/linux-espanol-learning/ollama/serve.log)",
    "Rozpakowuję…": "Unpacking…", "Ollama zainstalowana (bez uprawnień administratora).": "Ollama installed (without administrator rights).",
    "Ollama nie jest zainstalowana — użyj przycisku „Zainstaluj Ollamę i model”.":
        "Ollama is not installed — use the “Install Ollama and the model” button.",
    "Gotowe! Bot jest gotowy do rozmowy. ¡Vamos a hablar!": "Done! The bot is ready to talk. ¡Vamos a hablar!",
    "w archiwum nie znaleziono programu ollama": "the ollama program was not found in the archive",
    "Używam Ollamy zainstalowanej w systemie.": "Using the Ollama installed in the system.",
    "Krok 1/2: pobieram Ollamę ({}; z bibliotekami dla kart NVIDIA, ok. 1–2 GB)…":
        "Step 1/2: downloading Ollama ({}; with libraries for NVIDIA cards, about 1–2 GB)…",
    "Pobieram model {}… (to największy plik — może potrwać kilka–kilkanaście minut)":
        "Downloading the model {}… (the biggest file — it may take several minutes)",
    "nieobsługiwana architektura: {}": "unsupported architecture: {}", "BŁĄD: {}": "ERROR: {}",
}

EN.update({
    # ---- leftovers: app, speech, backup, ollama
    "Ta kopia pochodzi z innej aplikacji.": "This backup comes from another app.",
    "Uruchamiam serwer Ollamy…": "Starting the Ollama server…",
    "Hiszpania (mls_10246)": "Spain (mls_10246)", "Hiszpania (mls_9972)": "Spain (mls_9972)", "Szybki": "Fast",
    "Wszystko gotowe. ¡Vamos!": "All set. ¡Vamos!",
    "Krok 1/3: przygotowanie silnika mowy (Piper + Whisper)…": "Step 1/3: preparing the speech engine (Piper + Whisper)…",
    "Pobieranie bibliotek CUDA dla karty NVIDIA (ok. 1 GB)…": "Downloading the CUDA libraries for the NVIDIA card (about 1 GB)…",
    "Alfabet i wymowa": "Alphabet and pronunciation", "Odmiana": "Conjugation", "Laboratorium wymowy": "Pronunciation lab",
    "O mnie (dla bota)": "About me (for the bot)", "Testy i egzaminy": "Tests and exams", "Ćwicz": "Practise", "Ty": "You",
    "Nowy profil": "New profile", "Wykorzystane projekty": "Projects used", "Brak": "None",
    "Piper TTS — synteza mowy (OHF-Voice, GPL-3.0, pobierany osobno)": "Piper TTS — speech synthesis (OHF-Voice, GPL-3.0, downloaded separately)",
    "faster-whisper / OpenAI Whisper — rozpoznawanie mowy": "faster-whisper / OpenAI Whisper — speech recognition",

    # ---- pages_course.py
    "pn": "Mon", "wt": "Tue", "śr": "Wed", "cz": "Thu", "pt": "Fri", "so": "Sat", "nd": "Sun",
    "poniedziałek": "Monday", "wtorek": "Tuesday", "środa": "Wednesday", "czwartek": "Thursday", "piątek": "Friday",
    "sobota": "Saturday", "niedziela": "Sunday",
    "stycznia": "January", "lutego": "February", "marca": "March", "kwietnia": "April", "maja": "May", "czerwca": "June",
    "lipca": "July", "sierpnia": "August", "września": "September", "października": "October", "listopada": "November",
    "grudnia": "December",
    "Dialog": "Dialogue", "Słówka": "Words", "Gramatyka": "Grammar", "Ćwiczenia": "Exercises", "Mówienie": "Speaking",
    "1. Dialog": "1. Dialogue", "2. Słownictwo": "2. Vocabulary", "3. Gramatyka": "3. Grammar", "4. Ćwiczenia": "4. Exercises",
    "5. Mówienie": "5. Speaking",
    "mówienie · ok. 6 min": "speaking · about 6 min", "wymowa · ok. 5 min": "pronunciation · about 5 min",
    "słuchanie i pisanie · ok. 5 min": "listening and writing · about 5 min", "czytanie · ok. 6 min": "reading · about 6 min",
    "Poziom początkujący — przetrwanie w codziennych sytuacjach": "Beginner level — getting by in everyday situations",
    "Poziom podstawowy — przeszłość, przyszłość, opowiadanie, opinie": "Elementary level — past, future, telling stories, opinions",
    "Postęp kursu": "Course progress", "Dział": "Unit", "Postęp": "Progress", "Śr. wynik lekcji": "Avg. lesson score",
    "Test działu": "Unit test", "słówek dziś": "words today", "Powtórz": "Review", "Wróć do kursu": "Back to the course",
    "Szukaj filmów do tego tematu na YouTube": "Find videos on this topic on YouTube",
    "Wskazówka: tabele odmiany dowolnego czasownika znajdziesz w zakładce „Odmiana”.":
        "Tip: conjugation tables for any verb are in the “Conjugation” tab.",
    "¡Fantástico! Świetna robota.": "¡Fantástico! Great work.", "Cel dzienny": "Daily goal", "PLAN NA DZIŚ": "PLAN FOR TODAY",
    "Powtórka słówek": "Word review", "Kurs ukończony": "Course completed", "Lekcja {}: {}": "Lesson {}: {}",
    "POWTÓRKI": "REVIEW", "SŁOWO DNIA": "WORD OF THE DAY", "Otwórz lekcję": "Open the lesson",
    "W tej lekcji nauczysz się:": "In this lesson you will learn to:", "▶  Odtwórz cały dialog": "▶  Play the whole dialogue",
    "Pokaż tłumaczenie": "Show the translation", "▶  Odtwórz wszystkie": "▶  Play all",
    "Po ukończeniu lekcji wszystkie słowa trafią automatycznie do powtórek.": "When you finish the lesson, all the words go to your reviews.",
    "Do ćwiczeń  →": "To the exercises  →", "¡Muy bien! Lekcja zaliczona.": "¡Muy bien! Lesson passed.",
    "Lekcja zapisana — warto ją powtórzyć, żeby utrwalić materiał.": "Lesson saved — it's worth repeating it to make it stick.",
    "Powtórz ćwiczenia": "Repeat the exercises", "Ćwicz mówienie  →": "Practise speaking  →",
    "Posłuchaj zdania, nagraj się i porównaj. Najlepiej w słuchawkach z mikrofonem, w cichym miejscu.":
        "Listen to the sentence, record yourself and compare. Best with a headset, somewhere quiet.",
    "←  Poprzednie": "←  Previous", "Następne  →": "Next  →", "Ćwicz mówienie jeszcze raz": "Practise speaking again",
    "Zakończ  ✔": "Finish  ✔", "Cały kurs: {}/{} lekcji": "Whole course: {}/{} lessons", "<b>Poziom {}</b>": "<b>Level {}</b>",
    "Słówka opanowane: {} z {} w słowniku": "Words mastered: {} of {} in the dictionary",
    "Znasz już trochę hiszpańskiego? Zrób krótki test poziomujący, a podpowiem, od której lekcji zacząć.":
        "Know some Spanish already? Take a short placement test and I'll suggest which lesson to start with.",
    "Zrób test": "Take the test",
    "🎙️ Nagrania i ocena wymowy potrzebują jednorazowo silnika mowy (ok. 0,3–0,7 GB). Potem wszystko działa offline.":
        "🎙️ Recording and pronunciation scoring need a one-time speech engine (about 0.3–0.7 GB). After that everything works offline.",
    "CAŁY KURS UKOŃCZONY": "WHOLE COURSE COMPLETED",
    "Powtarzaj słówka, rób egzaminy próbne i czytaj czytanki.": "Review words, take mock exams and read the readings.",
    "dni": "days", "wszystko powtórzone": "all reviewed", "{} · ok. 10 min": "{} · about 10 min", "Ciekawostka": "Did you know?",
    "Do poprawy:": "To correct:", "✔ Lekcja ukończona — ¡enhorabuena!": "✔ Lesson completed — ¡enhorabuena!",
    "Mówienie zakończone": "Speaking done",
    "Lekcja zostanie zaliczona po zrobieniu ćwiczeń (krok 4) — wtedy słówka trafią do powtórek.":
        "The lesson counts as passed after the exercises (step 4) — then its words go to your reviews.",
    "Przejdź do ćwiczeń  →": "Go to the exercises  →", "Zdanie {} z {}": "Sentence {} of {}",
    "▶  Kontynuuj lekcję": "▶  Continue the lesson", "▶  Zacznij lekcję": "▶  Start the lesson",
    "Szybka powtórka · 5 min": "Quick review · 5 min", "Poziom {}": "Level {}", "{} z {} · ok. 20 min": "{} of {} · about 20 min",
    "Start": "Start", "Lekcja ukończona dziś ({})": "Lesson completed today ({})", "następna: {}": "next: {}",
    "Egzamin próbny {}": "Mock exam {}",
    "{} · {} · Hiszpania (castellano). Lekcje możesz robić w dowolnej kolejności, ale najlepiej po kolei.":
        "{} · {} · Spain (castellano). You can take the lessons in any order, but in order works best.",
    "Pokaż lekcje": "Show the lessons", "Zwiń": "Collapse", "{} · Dział {} · Lekcja {}": "{} · Unit {} · Lesson {}",
    "Nowe słowa ({})": "New words ({})", "Ćwiczenia ({})": "Exercises ({})", "Wynik: {} / {}  ({}%)": "Score: {} / {}  ({}%)",
    "{} słów dodano do powtórek.": "{} words added to your reviews.", "NASTĘPNA LEKCJA": "NEXT LESSON",
    "{} z {} części": "{} of {} parts", "/ {} min": "/ {} min", "Rekord: {} dni": "Best: {} days",
    "{} słówek · ok. {} min": "{} words · about {} min", "Błędy ({})": "Mistakes ({})", "Dział {}: {}": "Unit {}: {}",
    "średnio {}%": "average {}%", "test działu {}%": "unit test {}%", "następna lekcja": "next lesson",
    "▶  Kontynuuj": "▶  Continue", "▶  Zacznij": "▶  Start",
    "Wynik ćwiczeń: {}%. Słówka z tej lekcji są już w powtórkach.": "Exercise score: {}%. The words from this lesson are in your reviews now.",
    " · {} · DZIAŁ {}": " · {} · UNIT {}", "Następna lekcja: {}. {}  →": "Next lesson: {}. {}  →",
    "Scenka z Paco": "Scene with Paco", "Czytanka": "Reading", "Lekcje": "Lessons", "Seria 🔥": "Streak 🔥",
    "egzamin: —": "exam: —", "Zaczynam od zera": "I'm starting from zero", "Zainstaluj": "Install", "KONTYNUUJ": "CONTINUE",
    "Najtrudniejsze: <b>": "Hardest: <b>",

    # ---- placement.py
    "Zaczynamy": "Let's start", "Wynik testu": "Test result",
    "Znasz materiał całego kursu A1–A2 — możesz iść prosto do egzaminów próbnych i rozmów z Paco.":
        "You know the whole A1–A2 course — you can go straight to the mock exams and chats with Paco.",
    "Egzamin próbny A2": "Mock exam A2",
    "Wcześniejsze lekcje możesz oznaczyć jako znane — wtedy kurs poprowadzi Cię od polecanej lekcji (nic się nie usuwa, wyniki tych lekcji oznaczone będą jako 100%).":
        "You can mark the earlier lessons as known — the course then leads you from the suggested lesson (nothing is deleted; those lessons are marked 100%).",
    "Oznacz wcześniejsze jako znane i zacznij": "Mark the earlier ones as known and start", "Tylko otwórz lekcję": "Just open the lesson",
    "{} krótkich pytań o rosnącej trudności (słownictwo i gramatyka). Na tej podstawie podpowiem, od której lekcji najlepiej zacząć. Nie zgaduj na siłę — „Nie wiem” to dobra odpowiedź.":
        "{} short questions of growing difficulty (vocabulary and grammar). From them I'll suggest the best lesson to start with. Don't force a guess — “I don't know” is a good answer.",
    "Pytanie {} z {}": "Question {} of {}", "Poprawnie: {} z {}": "Correct: {} of {}",
    "Polecam zacząć od: {} · Lekcja {}: {}": "I suggest starting with: {} · Lesson {}: {}",

    # ---- pron.py
    "<span alpha=\"70%\">Analizuję wymowę…</span>": "<span alpha=\"70%\">Analysing your pronunciation…</span>",
    "Odsłuchaj siebie": "Play yourself back",
    "<span alpha=\"70%\">Ocena wymowy wymaga modelu rozpoznawania mowy — zainstaluj go w <b>Ustawieniach</b>.</span>":
        "<span alpha=\"70%\">Pronunciation scoring needs the speech recognition model — install it in <b>Settings</b>.</span>",
    "■  Zakończ nagrywanie": "■  Stop recording", "🎤  Nagraj się": "🎤  Record yourself",
    "<span alpha=\"70%\">Słyszę Cię… skończę sam po chwili ciszy.</span>": "<span alpha=\"70%\">I can hear you… I'll stop by myself after a moment of silence.</span>",
    "<span foreground=\"#d0353f\">Nie udało się nagrać dźwięku. Sprawdź mikrofon w ustawieniach systemu.</span>":
        "<span foreground=\"#d0353f\">Could not record any sound. Check the microphone in the system settings.</span>",
    "(nic nie rozpoznano)": "(nothing recognised)",
    "<span foreground=\"#d0353f\">Błąd rozpoznawania mowy: {}</span>": "<span foreground=\"#d0353f\">Speech recognition error: {}</span>",
    "Nieźle — spróbuj jeszcze raz.": "Not bad — try once more.", "Spróbuj jeszcze raz, wolniej.": "Try again, more slowly.",
    "<span size=\"large\">{}</span>\n<b>{}%</b> — {}\n<span alpha=\"70%\">Usłyszałem: „{}”</span>":
        "<span size=\"large\">{}</span>\n<b>{}%</b> — {}\n<span alpha=\"70%\">I heard: “{}”</span>",
    "<span alpha=\"70%\">Mów teraz… Nagranie zakończy się samo po {:g} s ciszy (albo kliknij ponownie).</span>":
        "<span alpha=\"70%\">Speak now… Recording stops by itself after {:g} s of silence (or click again).</span>",
    "<span alpha=\"70%\">Nic nie usłyszałem — kliknij „Nagraj się”, gdy będziesz gotowy.</span>":
        "<span alpha=\"70%\">I didn't hear anything — click “Record yourself” when you're ready.</span>",

    # ---- page_learner.py
    "Imię": "First name", "Miejscowość": "Town", "Praca / szkoła": "Work / school", "Kraj": "Country", "Rodzina": "Family",
    "Zainteresowania": "Interests", "np. Jarek": "e.g. Alex", "np. Rumia": "e.g. Leeds", "np. Polska": "e.g. England",
    "np. informatyk, student": "e.g. engineer, student", "np. żona, dwoje dzieci": "e.g. wife, two children",
    "np. muzyka, rower, podróże": "e.g. music, cycling, travel", "O mnie": "About me",
    "Tu wpisujesz to, co bot ma o Tobie wiedzieć, żeby rozmowa była naturalna i nie pytał w kółko o to samo. Wszystko jest zapisane tylko na tym komputerze. Przy silniku Claude API te informacje są wysyłane razem z tekstem rozmowy.":
        "Here you write what the bot should know about you, so the chat feels natural and it doesn't keep asking the same things. Everything stays on this computer. With the Claude API engine this information is sent together with the chat text.",
    "Inne:": "Other:", "Możesz pisać po polsku — bot to zrozumie.": "You can write in English — the bot will understand.",
    "Czego bot dowiedział się z naszych rozmów": "What the bot learned from our chats", "Tak bot widzi Twoją „kartkę”": "How the bot sees your “card”",
    "(pusto — bot nie wie jeszcze nic o Tobie)": "(empty — the bot doesn't know anything about you yet)",
    "Jeszcze nic — pojawi się tu to, co powiesz po hiszpańsku, np. „me llamo…”, „vivo en…”, „trabajo como…”, „me gusta…”.":
        "Nothing yet — what you say in Spanish will show up here, e.g. “me llamo…”, “vivo en…”, “trabajo como…”, “me gusta…”.",
    "Usuń ten fakt": "Delete this fact", "Wyczyść wszystko": "Clear everything", "Bot zna informacje o mnie": "The bot knows about me",

    # ---- page_dictation.py
    "Wpisz to, co słyszysz…": "Type what you hear…", "▶  Zacznij rundę": "▶  Start a round", "▶  Posłuchaj": "▶  Listen",
    "🐢  Wolno": "🐢  Slowly", "💡  Podpowiedź": "💡  Hint", "Dalej": "Next", "Zakończ rundę": "End the round",
    "Koniec rundy": "End of the round", "▶  Kolejna runda": "▶  Another round", "Wróć": "Back",
    "Do dyktanda potrzebny jest głos — zainstaluj silnik mowy na ekranie „Dzisiaj”.": "Dictation needs a voice — install the speech engine on the “Today” screen.",
    "Wynik: {}%": "Score: {}%", "Nieźle — ćwicz dalej.": "Not bad — keep practising.",
    "Posłuchaj jeszcze raz wolniej i spróbuj ponownie.": "Listen again more slowly and try again.", "Do powtórki:": "To review:",
    "Paco czyta zdanie po hiszpańsku, a Ty je wpisujesz. Dostaniesz kolorowe porównanie słowo po słowie: zielone — dobrze, żółte — brak akcentu, czerwone — błąd. Jedna runda to {} zdań z ukończonych lekcji.":
        "Paco reads a sentence in Spanish and you type it. You get a word-by-word colour comparison: green — right, yellow — missing accent, red — mistake. One round is {} sentences from finished lessons.",
    "  (jeszcze nic nie ukończono — użyję zdań z pierwszych lekcji)": "  (nothing finished yet — I'll use sentences from the first lessons)",
    "Dyktando · zdanie {} z {}": "Dictation · sentence {} of {}", "{} słów: ": "{} words: ", "Dostępnych zdań: {}": "Sentences available: {}",
    "✔ Idealnie!": "✔ Perfect!", "Doskonale!": "Excellent!", "Bardzo dobrze.": "Very good.", "Poprawnie:": "Correct:",
    "Dobrze.": "Good.", "Poprawnie: <b>": "Correct: <b>",
})

EN.update({
    # ---- pages_more.py: readings, videos, tests, stats, settings
    "Zapisz kopię zapasową": "Save a backup", "Zapisz": "Save", "Wczytaj kopię zapasową": "Load a backup", "Wczytaj": "Load",
    "Kopia wczytana": "Backup loaded", "Męski — Hiszpania (davefx)": "Male — Spain (davefx)", "Żeński — Hiszpania (sharvard)": "Female — Spain (sharvard)",
    "Ollama — lokalnie, offline (darmowe)": "Ollama — local, offline (free)",
    "Claude API — chmura (najlepsza jakość, płatne)": "Claude API — cloud (best quality, paid)",
    "Bot offline: Ollama + model instalują się do Twojego katalogu domowego, bez sudo. Na karcie NVIDIA odpowiedzi przychodzą w 1–3 s, na samym procesorze wolniej.":
        "Offline bot: Ollama and the model install into your home folder, no sudo. With an NVIDIA card replies take 1–3 s, on the processor alone longer.",
    "Klucz jest zapisany tylko na tym komputerze (w systemowym schowku haseł — GNOME Keyring; bez niego w pliku z prawami 600). Do API wysyłany jest tylko tekst rozmowy. Klucz utworzysz na console.anthropic.com.":
        "The key is stored only on this computer (in the system keyring — GNOME Keyring; without it in a file with 600 permissions). Only the chat text is sent to the API. You can create a key at console.anthropic.com.",
    "Na zmianę (ES→PL i PL→ES)": "Alternating (ES→EN and EN→ES)", "Hiszpański → polski": "Spanish → English", "Polski → hiszpański": "English → Spanish",
    "Usunięte zostaną ukończone lekcje, słówka w powtórkach, wyniki testów i statystyki. Tej operacji nie można cofnąć.":
        "Finished lessons, review words, test results and statistics will be deleted. This cannot be undone.",
    "Rozpocznij": "Start", "Zamknij": "Close",
    "Krótkie teksty do każdego działu kursu — z nagraniem, tłumaczeniem, słowniczkiem i pytaniami sprawdzającymi zrozumienie.":
        "Short texts for every unit of the course — with audio, a translation, a glossary and comprehension questions.",
    "▶  Przeczytaj na głos": "▶  Read aloud", "Sprawdź, czy zrozumiałeś": "Check that you understood",
    "Sprawdzone kanały i źródła z hiszpańskim. Linki otwierają się w przeglądarce — aplikacja niczego nie pobiera. Najwięcej daje codzienne słuchanie materiałów, które rozumiesz w ok. 70–90%.":
        "Trusted channels and sources in Spanish. Links open in the browser — the app downloads nothing. Daily listening to things you understand 70–90% of helps the most.",
    "Otwórz": "Open",
    "Wskazówka: w każdej lekcji (zakładka „Dialog”) jest też link do wyszukiwania filmów na temat tej lekcji.":
        "Tip: every lesson (the “Dialogue” tab) also has a link to search for videos on its topic.",
    "Bez podpowiedzi i bez cofania. Powodzenia — ¡suerte!": "No hints and no going back. Good luck — ¡suerte!",
    "Część ustna — mówienie": "Oral part — speaking", "Przeczytaj na głos 3 zdania. Liczy się zrozumiałość wymowy.": "Read 3 sentences aloud. What counts is clear pronunciation.",
    "Pomiń część ustną": "Skip the oral part", "Wróć do testów": "Back to the tests",
    "Test działu: 15 pytań z 4 lekcji. Egzamin próbny: ok. 40 pytań — słownictwo, gramatyka, tłumaczenie, słuchanie, czytanie i część ustna. Próg zaliczenia: 60%.":
        "Unit test: 15 questions from 4 lessons. Mock exam: about 40 questions — vocabulary, grammar, translation, listening, reading and an oral part. Pass mark: 60%.",
    "Test poziomujący": "Placement test",
    "Znasz już trochę hiszpańskiego? Krótki test (ok. 20 pytań) podpowie, od której lekcji zacząć.":
        "Know some Spanish already? A short test (about 20 questions) suggests which lesson to start with.",
    "Zrób test poziomujący": "Take the placement test", "Egzamin": "Exam",
    "Słowa w powtórkach": "Words in review", "Słowa opanowane": "Words mastered", "Minuty nauki (30 dni)": "Study minutes (30 days)",
    "Próby wymowy": "Pronunciation attempts", "Śr. wymowa (ost. 30)": "Avg. pronunciation (last 30)",
    "Aktywność — ostatnie 30 dni (minuty)": "Activity — last 30 days (minutes)",
    "Wymowa — średni wynik dnia (ostatnie 30 dni)": "Pronunciation — daily average (last 30 days)",
    "Nowe: {}  ·  W nauce: {}  ·  Powtarzane: {}  ·  Opanowane (odstęp ≥ 21 dni): {}":
        "New: {}  ·  Learning: {}  ·  Reviewing: {}  ·  Mastered (interval ≥ 21 days): {}",
    "Głos i odtwarzanie": "Voice and playback", "Pobieram głos… (kilkadziesiąt MB)": "Downloading the voice… (a few dozen MB)",
    "Głos lektora:": "Narrator voice:", "▶ Posłuchaj": "▶ Listen", "Normalne tempo": "Normal speed", "Trochę wolniej": "A bit slower",
    "Wolno": "Slow", "Tempo mowy:": "Speech speed:", "Czytaj automatycznie odpowiedzi i fiszki:": "Read answers and flashcards aloud automatically:",
    "Wygląd": "Appearance", "Motyw kolorystyczny:": "Colour theme:", "Jasny / ciemny:": "Light / dark:",
    "Każdy motyw ma wersję jasną i ciemną. „Automatycznie” przełącza się razem z systemem.":
        "Every theme has a light and a dark version. “Automatic” switches together with the system.",
    "Silnik:": "Engine:", "Zmień model / zainstaluj ponownie": "Change the model / reinstall",
    "⬇  Zainstaluj Ollamę i model (automatycznie)": "⬇  Install Ollama and the model (automatically)", "nazwa modelu": "model name",
    "klucz API sk-ant-… (tylko do tłumaczeń; rozmowa zostaje lokalna)": "API key sk-ant-… (for translations only; the chat stays local)",
    "Nagrywanie głosu — cisza kończąca wypowiedź:": "Voice recording — silence that ends what you say:",
    "s  (rozmowa z botem i ćwiczenie wymowy; dłużej = więcej czasu na myślenie, zawsze możesz też kliknąć)":
        "s  (bot chat and pronunciation practice; longer = more time to think, you can always click as well)",
    "Cel dzienny i przypomnienia": "Daily goal and reminders", "Cel nauki:": "Study goal:",
    "Przypomnij, jeśli cel niezaliczony:": "Remind me if the goal isn't met:", "Godzina przypomnienia:": "Reminder time:",
    "Przypomnienie to zwykłe powiadomienie systemowe — pojawia się, gdy aplikacja jest uruchomiona.":
        "The reminder is an ordinary system notification — it shows up while the app is running.",
    "Kopia zapasowa postępu": "Progress backup",
    "Zapisz cały postęp bieżącego profilu (lekcje, powtórki, wyniki, rozmowy, „O mnie”) do jednego pliku .zip — np. żeby przenieść naukę na inny komputer. Import zawsze tworzy nowy profil i niczego nie nadpisuje.":
        "Save all progress of the current profile (lessons, reviews, scores, chats, “About me”) to one .zip file — e.g. to move your learning to another computer. Importing always creates a new profile and overwrites nothing.",
    "💾  Zapisz kopię…": "💾  Save a backup…", "📂  Wczytaj kopię…": "📂  Load a backup…", "Nowych słów dziennie:": "New words per day:",
    "Kierunek fiszek:": "Flashcard direction:", "Silnik mowy (offline)": "Speech engine (offline)", "Model rozpoznawania mowy:": "Speech recognition model:",
    "Używaj karty NVIDIA (CUDA) — pobiera dodatkowo ok. 1 GB bibliotek": "Use the NVIDIA card (CUDA) — downloads about 1 GB of extra libraries",
    "Nie wykryto karty NVIDIA ze sterownikiem (nvidia-smi).": "No NVIDIA card with a driver was found (nvidia-smi).",
    "Zainstaluj / zaktualizuj komponenty": "Install / update components", "Twój komputer": "Your computer",
    "Minimum: Ubuntu 24.04+ (64-bit), procesor 4-rdzeniowy, 8 GB RAM, ok. 1 GB miejsca, dowolna karta graficzna (zintegrowana wystarczy), mikrofon.\nZalecane: procesor 6–8 rdzeni, 16 GB RAM, słuchawki z mikrofonem; karta NVIDIA opcjonalnie przyspiesza rozpoznawanie mowy.":
        "Minimum: Ubuntu 24.04+ (64-bit), a 4-core processor, 8 GB RAM, about 1 GB of space, any graphics (integrated is enough), a microphone.\nRecommended: a 6–8 core processor, 16 GB RAM, a headset; an NVIDIA card optionally speeds up speech recognition.",
    "Wyzeruj cały postęp…": "Reset all progress…", "Wyzerować cały postęp?": "Reset all progress?",
    "Instalacja silnika mowy": "Installing the speech engine",
    "Pobierzemy jednorazowo (wszystko zostaje na Twoim komputerze i działa offline):": "One-time download (everything stays on your computer and works offline):",
    "Gotowe ✔": "Done ✔",
    "<span foreground=\"#2e9e44\" size=\"large\"><b>✔ Instalacja zakończona pomyślnie.</b></span> Możesz zamknąć to okno — wymowa i ocena wymowy już działają.":
        "<span foreground=\"#2e9e44\" size=\"large\"><b>✔ Installation finished.</b></span> You can close this window — speech and pronunciation scoring work now.",
    "<span foreground=\"#d0353f\" size=\"large\"><b>✘ Instalacja nie powiodła się.</b></span> Szczegóły w dzienniku poniżej.":
        "<span foreground=\"#d0353f\" size=\"large\"><b>✘ The installation failed.</b></span> Details in the log below.",
    "Spróbuj ponownie": "Try again", "\nNie udało się. Sprawdź połączenie z internetem i spróbuj ponownie.": "\nIt failed. Check your internet connection and try again.",
    "Czytaj": "Read", "Słowniczek": "Glossary", "Przetłumacz na hiszpański:": "Translate into Spanish:", "Błędy:": "Mistakes:",
    "Historia": "History", "Ostatnie błędy — warto do nich wrócić": "Recent mistakes — worth going back to", "Kopia zapisana": "Backup saved",
    "Nie udało się wczytać kopii": "Could not load the backup",
    "Utworzono nowy profil „{} (import)”. Przełączam na niego.": "Created a new profile “{} (import)”. Switching to it.",
    "prywatna Ollama aplikacji (uruchamia się sama)": "the app's private Ollama (starts by itself)",
    "Zaawansowane (własny serwer Ollama)": "Advanced (your own Ollama server)", "Adres Ollama:": "Ollama address:", "Odśwież listę": "Refresh the list",
    "Model:": "Model:",
    "Polskie tłumaczenia i wyjaśnienia przez Claude API (znacznie lepsza polszczyzna)": "English translations and explanations through the Claude API (better quality)",
    "Wysyłane są tylko pojedyncze zdania bota do przetłumaczenia i Twoje pytania po polsku. Bez klucza lub bez zaznaczenia wszystko robi lokalny model.":
        "Only single bot sentences to translate and your questions in English are sent. Without a key, or unticked, the local model does everything.",
    "Klucz API:": "API key:", "✔ Spełnia wymagania minimalne.": "✔ Meets the minimum requirements.",
    "✔ Zaliczone — próg to 60%. ": "✔ Passed — the pass mark is 60%. ", "✘ Jeszcze nie — próg to 60%. ": "✘ Not yet — the pass mark is 60%. ",
    "Świetnie!": "Great!", "maks. {} min": "max. {} min",
    "Brak prób. Poćwicz w Laboratorium wymowy lub w Scenkach z Paco — wykres pojawi się po pierwszych ocenach.":
        "No attempts yet. Practise in the Pronunciation lab or in Scenes with Paco — the chart appears after the first scores.",
    "Najtrudniejsze zdania (do poćwiczenia)": "Hardest sentences (to practise)", "Otwórz trening": "Open the training",
    "Nie udało się zapisać kopii": "Could not save the backup", "  ⬇ pobierze się": "  ⬇ will be downloaded", "Głos pobrany ✔": "Voice downloaded ✔",
    "Bot offline nie jest jeszcze zainstalowany.": "The offline bot is not installed yet.", "{} minut dziennie": "{} minutes a day",
    "Synteza mowy (Piper, głosy z Hiszpanii): {}": "Speech synthesis (Piper, voices from Spain): {}", "✔ zainstalowana": "✔ installed",
    "✘ brak": "✘ missing", "Rozpoznawanie mowy (Whisper, model „{}”): {}": "Speech recognition (Whisper, model “{}”): {}",
    "✔ zainstalowane": "✔ installed", "  (sterownik NVIDIA aktywny)": "  (NVIDIA driver active)", ". Wybierz model „Szybki”.": ". Choose the “Fast” model.",
    "{} · Dział {}": "{} · Unit {}", "Wynik: {}/{}": "Score: {}/{}", "Część ustna: {}%": "Oral part: {}%",
    "Powtórz lekcje, w których były błędy.": "Go over the lessons where you made mistakes.", "Dobrze, utrwal słabsze miejsca.": "Good, now firm up the weaker spots.",
    "Nie udało się pobrać głosu: ": "Could not download the voice: ", "Modele na serwerze: {}": "Models on the server: {}", "brak": "none",
    "Procesor: {} ({} wątków)\nPamięć RAM: {} GB\nKarta graficzna: {}": "Processor: {} ({} threads)\nRAM: {} GB\nGraphics: {}",
    "nie wykryto": "not found", "⚠ Poniżej minimum: ": "⚠ Below the minimum: ",
    "• silnik mowy Piper + faster-whisper (pakiety Python, ok. 200 MB)\n• dwa głosy hiszpańskie z Hiszpanii (ok. 130 MB)\n• model rozpoznawania mowy „{}” ({})":
        "• the Piper + faster-whisper speech engine (Python packages, about 200 MB)\n• two Spanish voices from Spain (about 130 MB)\n• the speech recognition model “{}” ({})",
    "W treningu błędów: {} (do powtórki teraz: {})": "In mistake training: {} (due now: {})",
    "✔ Gotowe — model: {}  ·  {}": "✔ Done — model: {}  ·  {}", "Serwer nie odpowiada": "The server doesn't respond",
    " — prywatna Ollama uruchomi się sama przy rozmowie.": " — the private Ollama starts by itself when you chat.",
    "← zalecany": "← recommended", "• biblioteki CUDA dla karty NVIDIA (ok. 1 GB)": "• CUDA libraries for the NVIDIA card (about 1 GB)",
    "— najlepszy:": "— best:", "(Twoja odp.:": "(your answer:",

    # ---- pages_tools.py: alphabet, review, dictionary, conjugation, pronunciation lab
    "dziś": "today", "za {} dni": "in {} days", "Szukaj po hiszpańsku lub po polsku…": "Search in Spanish or English…",
    "np. hablar, tener, levantarse": "e.g. hablar, tener, levantarse", "— czasowniki z kursu —": "— verbs from the course —",
    "Zdania z ukończonych lekcji": "Sentences from finished lessons", "Zdania z całego kursu": "Sentences from the whole course",
    "Słowa ze słownika": "Words from the dictionary", "Trudne dźwięki (rr, j, z, ll, ñ)": "Hard sounds (rr, j, z, ll, ñ)",
    "…albo wpisz własne zdanie po hiszpańsku i naciśnij Enter": "…or type your own sentence in Spanish and press Enter",
    "Alfabet hiszpański (el abecedario)": "The Spanish alphabet (el abecedario)",
    "Kliknij ▶ przy literze, aby usłyszeć jej nazwę, i przy przykładach, aby usłyszeć słowa. Prawy przycisk myszy — wolniej.":
        "Click ▶ next to a letter to hear its name, and next to the examples to hear the words. Right mouse button — slower.",
    "Trudne dźwięki dla Polaków": "Hard sounds for English speakers",
    "Wymowa z Hiszpanii (castellano). Ćwicz każdy dźwięk: posłuchaj → powtórz → nagraj się w Laboratorium wymowy.":
        "Pronunciation from Spain (castellano). Practise each sound: listen → repeat → record yourself in the Pronunciation lab.",
    "Posłuchaj różnicy:": "Hear the difference:", "Fiszki": "Flashcards", "Fiszki (": "Flashcards (", "Błędy (trening)": "Mistakes (training)",
    "Błędy — trening": "Mistakes — training", "Powtórki słówek": "Word review", "Pokaż odpowiedź  (Spacja)": "Show the answer  (Space)",
    "Skróty: Spacja — pokaż, 1–4 — ocena.": "Shortcuts: Space — show, 1–4 — rate.", "Trening błędów": "Mistake training",
    "Tu wracają ćwiczenia, w których się pomyliłeś — w lekcjach, testach i czytankach — oraz zdania, które poprawił Paco. Zadanie wraca jutro, potem za 3 i za 7 dni; po 3 dobrych odpowiedziach z rzędu znika. Literówki i brak akcentu się nie liczą.":
        "Exercises you got wrong come back here — from lessons, tests and readings — plus sentences Paco corrected. A task comes back tomorrow, then in 3 and in 7 days; after 3 right answers in a row it disappears. Typos and missing accents don't count.",
    "Usuń z treningu": "Remove from training", "Trening błędów — koniec rundy": "Mistake training — end of the round", "Wróć do listy": "Back to the list",
    "✔ W powtórkach": "✔ In review", "Odmiana czasowników": "Verb conjugation",
    "Formy generowane automatycznie według reguł i listy czasowników nieregularnych (odmiana z Hiszpanii, z vosotros). Imperativo pokazuje formy twierdzące.":
        "Forms are generated from the rules and a list of irregular verbs (as in Spain, with vosotros). Imperativo shows the affirmative forms.",
    "Wybierz źródło zdań albo wpisz własne. Aplikacja porównuje to, co powiedziałeś, z wzorem — słowo po słowie — i podpowiada, nad czym pracować.":
        "Choose where the sentences come from, or type your own. The app compares what you said with the model — word by word — and tells you what to work on.",
    "Losuj  ⟳": "Shuffle  ⟳", "Litery": "Letters", "Ćwicz w laboratorium wymowy": "Practise in the pronunciation lab", "Trudne dźwięki": "Hard sounds",
    "Akcent": "Stress", "Pisanie znaków": "Typing the characters", "Co to znaczy?": "What does it mean?",
    "Jak to powiedzieć po hiszpańsku?": "How do you say it in Spanish?", "Nie pamiętam": "Forgot", "Trudne": "Hard", "Dobrze": "Good", "Łatwe": "Easy",
    "Znowu": "Again", "Nie masz błędów do treningu. 🎉": "No mistakes to train. 🎉",
    "Gdy pomylisz się w ćwiczeniu albo Paco poprawi Twoje zdanie, zadanie trafi tutaj.": "When you get an exercise wrong or Paco corrects your sentence, the task lands here.",
    "+ Dodaj do powtórek": "+ Add to review", "Błędy — trening ({})": "Mistakes — training ({})",
    "Nie masz jeszcze słówek do powtórek. Ukończ pierwszą lekcję albo dodaj słowa ze Słownika.": "No words to review yet. Finish the first lesson or add words from the Dictionary.",
    "¡Todo listo! Na dziś wszystko powtórzone. 🎉": "¡Todo listo! Everything reviewed for today. 🎉", "  ·  NOWE SŁOWO": "  ·  NEW WORD",
    "Na dziś wszystkie błędy powtórzone. ✔": "All mistakes reviewed for today. ✔", "▶  Zacznij trening": "▶  Start training",
    "Wszystkie zapamiętane błędy ({})": "All saved mistakes ({})", "Wynik: {} / {}": "Score: {} / {}",
    "opanowane i usunięte z treningu: {}": "mastered and removed from training: {}", "dobrze — wrócą za kilka dni: {}": "right — back in a few days: {}",
    "do poprawy — wrócą jutro: {}": "to fix — back tomorrow: {}", "{} haseł": "{} entries",
    "Imiesłów (participio): {}    ·    Gerundio: {}": "Participle (participio): {}    ·    Gerundio: {}",
    "Twoje próby: {} · średnio {}% · ostatnie 30: {}%": "Your attempts: {} · average {}% · last 30: {}%",
    "Zostało: {}  ·  powtórzone: {}": "Left: {}  ·  reviewed: {}", "zadanie": "task", "zadania": "tasks", "zadań": "tasks",
    "Opanowane błędy (usunięte z treningu): {}": "Mastered mistakes (removed from training): {}",
    "{}  ·  wraca {}  ·  seria {}/{}  ·  pomyłek: {}": "{}  ·  back {}  ·  streak {}/{}  ·  mistakes: {}",
    "Kolejna runda ({})": "Another round ({})", "Pokaż odmianę: {}": "Show the conjugation: {}",
    "Powtórzone w tej sesji: {}. Wróć jutro — algorytm FSRS pokaże słowa dokładnie wtedy, gdy zaczniesz je zapominać.":
        "Reviewed this session: {}. Come back tomorrow — FSRS shows the words just when you start forgetting them.",
    "W treningu: {}. Następne wrócą {}.": "In training: {}. The next ones come back {}.", "Do powtórki teraz: {}": "Due now: {}",
    "Runda: {} {}  ·  w treningu łącznie: {}": "Round: {} {}  ·  in training in total: {}", "·  lekcja": "·  lesson",
})

EN.update({
    "Język kursu · Course language:": "Course language · Język kursu:",
    "Zmiana języka uruchomi aplikację ponownie.": "Changing the language restarts the app.",
    "✎  Nazwa i język bieżącego…": "✎  Name and language of the current one…",
})

EN.update({
    "{} z {} lekcji": "{} of {} lessons", "lekcja": "lesson", "lekcje": "lessons", "lekcji": "lessons",
    "Fiszki ({})": "Flashcards ({})",
    "Automatycznie (jak system)": "Automatic (like the system)", "Zawsze jasny": "Always light", "Zawsze ciemny": "Always dark",
})

EN.update({
    "czasownik": "verb", "czasownik zwrotny": "reflexive verb", "przymiotnik": "adjective", "przyimek": "preposition",
    "zaimek": "pronoun", "wykrzyknik": "interjection", "liczebnik": "number", "zwrot": "phrase", "rodzajnik": "article",
    " (pokazano 400)": " (showing 400)",
})

# ---- bot.py, page_bot.py, page_scenes.py: Paco and the scenes
EN.update({
    "Claude Haiku (szybki, tani)": "Claude Haiku (fast, cheap)", "Claude Sonnet (najlepszy)": "Claude Sonnet (the best)",
    "wiek": "age", "zwierzęta": "pets", "nauka": "studies", "bot pamięta": "the bot remembers",
    "poprzednio rozmawialiście o": "last time you talked about", "imię": "name", "miejscowość": "town",
    "kraj": "country", "praca / szkoła": "job / school", "rodzina": "family", "zainteresowania": "interests",
    "inne": "other", "mieszka w": "lives in", "pochodzi z": "is from", "narodowość": "nationality", "lubi": "likes",
    "Ollama (lokalnie)": "Ollama (local)", "Claude API (chmura)": "Claude API (cloud)",
    "Wolno i prosto": "Slow and simple", "Bardzo krótkie, najprostsze zdania, bez nowych słów.":
        "Very short, very simple sentences, no new words.",
    "Normalnie": "Normal", "Krótkie tury, najwyżej jedno nowe słowo.": "Short turns, at most one new word.",
    "Wyzwanie": "Challenge", "Dłuższe wypowiedzi, do dwóch nowych słów, mniej podpowiedzi.":
        "Longer turns, up to two new words, fewer hints.",
    "Swobodna rozmowa o Tobie": "A free chat about you",
    "Porozmawiaj o sobie: imię, skąd jesteś, praca, rodzina, zainteresowania — tylko tym, co już znasz.":
        "Talk about yourself: name, where you're from, job, family, interests — only with what you already know.",
    "W barze — zamów i zapłać": "At the bar — order and pay",
    "Zamów coś do picia i jedzenia, zapytaj o cenę i zapłać kartą.":
        "Order something to drink and eat, ask how much it is and pay by card.",
    "Na targu": "At the market",
    "Kup owoce i warzywa (ilości w kilogramach), zapytaj, co jest dobre, powiedz, co lubisz.":
        "Buy fruit and vegetables (by the kilo), ask what's good, say what you like.",
    "Pytanie o drogę": "Asking the way",
    "Zapytaj, jak dojść do muzeum lub na dworzec, i upewnij się, że rozumiesz drogę.":
        "Ask how to get to the museum or the station, and make sure you understand the way.",
    "W sklepie z ubraniami": "In a clothes shop",
    "Znajdź kurtkę albo koszulę, zapytaj o rozmiar, kolor i cenę, przymierz i kup.":
        "Find a jacket or a shirt, ask about the size, colour and price, try it on and buy it.",
    "Plany na weekend": "Weekend plans",
    "Umówcie się na weekend: co, gdzie, o której. Odmów jednej propozycji i zaproponuj inną.":
        "Make plans for the weekend: what, where, what time. Turn down one idea and suggest another.",
    "Ostatnie wakacje": "Your last holidays",
    "Opowiedz o swoich ostatnich wakacjach w czasie przeszłym: gdzie byłeś, co robiłeś, jak było.":
        "Talk about your last holidays in the past tense: where you went, what you did, what it was like.",
    "Recepcja hotelu": "Hotel reception",
    "Zamelduj się, zapytaj o śniadanie i zgłoś problem z pokojem.":
        "Check in, ask about breakfast and report a problem with the room.",
    "U lekarza": "At the doctor's",
    "Opisz objawy (co Cię boli, od kiedy) i zrozum zalecenia.":
        "Describe your symptoms (what hurts, since when) and understand the advice.",
    "Rozmowa o pracę": "A job interview",
    "Opowiedz o swoim doświadczeniu, mocnych stronach i dlaczego chcesz tam pracować.":
        "Talk about your experience, your strengths and why you want to work there.",
    "Wynajem mieszkania": "Renting a flat",
    "Zapytaj o mieszkanie: metraż, czynsz, opłaty, kaucję i umów się na oglądanie.":
        "Ask about the flat: size, rent, bills, deposit, and arrange a viewing.",
    "Brak klucza API Claude — wpisz go w Ustawieniach.": "No Claude API key — enter it in Settings.",
    "Nie wybrano modelu Ollama w Ustawieniach.": "No Ollama model chosen in Settings.",
    "brak połączenia ({})": "no connection ({})",
    "Brak wypowiedzi": "Nothing said", "Świetnie!": "Excellent!", "Bardzo dobrze": "Very good",
    "Dobrze — tak trzymaj": "Good — keep it up", "Ćwicz dalej — każda rozmowa pomaga": "Keep practising — every chat helps",
    "{} lat": "{} years old",
    # page_bot.py
    "Rozmowa z Paco": "Chat with Paco",
    "Paco to Twój rozmówca. Mówisz lub piszesz po hiszpańsku, a on używa tylko słówek i gramatyki z lekcji, które już ukończyłeś. Błędy poprawia łagodnie, a na końcu dostajesz podsumowanie.":
        "Paco is your conversation partner. You speak or write in Spanish, and he uses only the words and grammar "
        "from the lessons you have finished. He corrects mistakes gently, and at the end you get a summary.",
    "Silnik: Claude API — {}": "Engine: Claude API — {}",
    "Tekst rozmowy jest wysyłany do API Anthropic (nagrania głosu nie). Wymaga internetu i klucza API; płatne za użycie.":
        "The text of the chat is sent to the Anthropic API (voice recordings are not). Needs the internet and an API "
        "key; paid per use.",
    "Silnik: Ollama (lokalnie, offline) — model: {}": "Engine: Ollama (local, offline) — model: {}",
    "nie wybrano": "none chosen",
    "Wszystko zostaje na Twoim komputerze. Wymaga zainstalowanej Ollamy i pobranego modelu.":
        "Everything stays on your computer. Needs Ollama installed and a model downloaded.",
    "⚠ Bot nie jest jeszcze przygotowany.": "⚠ The bot isn't set up yet.",
    "⬇  Zainstaluj bota offline (Ollama + model) — jednym kliknięciem":
        "⬇  Install the offline bot (Ollama + model) — in one click",
    "Ustawienia bota": "Bot settings",
    "Nie masz jeszcze ukończonych lekcji — bot będzie używał tylko materiału z lekcji 1. Najlepiej najpierw zrób kilka lekcji.":
        "You haven't finished any lessons yet — the bot will use only the material from lesson 1. "
        "It's best to do a few lessons first.",
    "Poziom rozmówcy:": "Partner's level:", "📜 Historia rozmów": "📜 Chat history",
    "🙂 O mnie (dane dla bota)": "🙂 About me (for the bot)", "Wybierz scenkę": "Choose a situation",
    "Zalecane po lekcji {} {}: {}": "Recommended after lesson {} {}: {}",
    "Rozpocznij mimo to": "Start anyway", "Twoje zadanie: ": "Your task: ",
    "Zakończ i podsumuj": "Finish and sum up",
    "Napisz po hiszpańsku… (możesz też zapytać po polsku o pomoc)":
        "Write in Spanish… (you can also ask for help in English)",
    "Wyślij": "Send", "Pokazuj tłumaczenie": "Show the translation",
    "🎤  Mów": "🎤  Speak", "✔  Skończyłem mówić": "✔  I've finished", "🎤  Przerwij i mów": "🎤  Interrupt and speak",
    "✖ Anuluj": "✖ Cancel", "Rozmówca mówi na głos": "Partner speaks aloud",
    "Bez rąk: po odpowiedzi sam zacznę słuchać": "Hands-free: start listening again after each reply",
    "Rozpoznawanie mowy:": "Speech recognition:",
    "Rozmowa głosowa wymaga modelu rozpoznawania mowy i mikrofonu (Ustawienia).":
        "Voice chat needs a speech recognition model and a microphone (Settings).",
    "Wskazówka: najlepiej w słuchawkach — wtedy mikrofon nie łapie głosu rozmówcy.":
        "Tip: use headphones — then the microphone doesn't pick up your partner's voice.",
    "Słucham… masz czas — kliknij „Skończyłem”, gdy skończysz":
        "Listening… take your time — click “I've finished” when you're done",
    "Rozmówca myśli…": "Your partner is thinking…", "Rozmówca mówi…": "Your partner is speaking…",
    "Słyszę Cię… (po dłuższej ciszy sam skończę — albo kliknij „Skończyłem”)":
        "I can hear you… (I'll stop after a longer silence — or click “I've finished”)",
    "Rozpoznaję mowę…": "Recognising speech…",
    "Nie słyszę, żebyś mówił — kliknij 🎤, gdy będziesz gotowy.": "I can't hear you speaking — click 🎤 when you're ready.",
    "Nie udało się nagrać dźwięku — sprawdź mikrofon w ustawieniach systemu.":
        "Couldn't record any sound — check the microphone in the system settings.",
    "Błąd rozpoznawania mowy: {}": "Speech recognition error: {}",
    "Nie zrozumiałem — spróbuj jeszcze raz.": "I didn't catch that — try again.",
    "🤖 Rozmówca": "🤖 Partner", "🙂 Ty": "🙂 You",
    "Podkreślone — słowa spoza Twoich lekcji: ": "Underlined — words from outside your lessons: ",
    "💡 Wyjaśnienie Paco": "💡 Paco explains",
    "🎤 Teraz spróbuj powiedzieć to sam — Paco czeka na Ciebie.": "🎤 Now try saying it yourself — Paco is waiting for you.",
    "✎ Poprawka": "✎ Correction", "Poprawnie: ": "Correct: ", "Błąd silnika bota: {}": "Bot engine error: {}",
    "Podsumowanie rozmowy": "Chat summary", "Zapisana rozmowa": "Saved chat", "  ·  poziom: {}": "  ·  level: {}",
    "Ocena rozmowy: {}/100 — {}": "Chat score: {}/100 — {}",
    "Twoje wypowiedzi: {}  ·  słowa: {} (różnych: {})  ·  poprawki: {}":
        "Your messages: {}  ·  words: {} (different: {})  ·  corrections: {}",
    "Wypowiedzi bez błędów: {}%  ·  średnio {} słowa na wypowiedź": "Messages without mistakes: {}%  ·  {} words per message on average",
    "Do poprawy": "To correct", "Ty: ": "You: ",
    "➕ Dodaj poprawione zdania do powtórek ({})": "➕ Add the corrected sentences to reviews ({})",
    "✔ Poprawione zdania są już w powtórkach": "✔ The corrected sentences are already in reviews",
    "✔ Dodano {} do powtórek": "✔ Added {} to reviews",
    "Nowe słowa z rozmowy (są w słowniku)": "New words from the chat (they're in the dictionary)",
    "✔ W powtórkach": "✔ In reviews", "+ Do powtórek": "+ To reviews",
    "Zapis rozmowy": "Chat transcript", "Usuń z historii": "Remove from history", "Nowa rozmowa": "New chat",
    "Historia rozmów": "Chat history",
    "Jeszcze nie masz zapisanych rozmów. Po kliknięciu „Zakończ i podsumuj” rozmowa trafia tutaj.":
        "You have no saved chats yet. After you click “Finish and sum up”, the chat lands here.",
    "Ostatnie {} rozmów — średnia ocena {}/100": "Last {} chats — average score {}/100",
    ", zmiana {} pkt względem pierwszej z nich": ", a change of {} points since the first of them",
    "Bot offline — instalacja Ollamy i modelu": "Offline bot — installing Ollama and a model",
    "Jednym kliknięciem zainstaluję wszystko, czego potrzebuje bot — działa potem całkowicie offline, za darmo, bez hasła administratora.":
        "In one click I'll install everything the bot needs — it then works fully offline, for free, "
        "without an administrator password.",
    "• Wykryto Ollamę w systemie — użyję jej, pobiorę tylko model.":
        "• Ollama found on the system — I'll use it and download only the model.",
    "• Prywatna Ollama jest już zainstalowana — pobiorę tylko model.":
        "• A private Ollama is already installed — I'll download only the model.",
    "• Ollama (silnik modeli językowych) — do Twojego katalogu domowego, ok. 1–2 GB\n  (zawiera biblioteki dla kart NVIDIA; uruchamia się sama tylko na czas rozmowy)":
        "• Ollama (the language model engine) — into your home folder, about 1–2 GB\n"
        "  (includes libraries for NVIDIA cards; it starts by itself only for the time of a chat)",
    "\n• wybrany model językowy (poniżej)": "\n• the chosen language model (below)",
    "Twój komputer: {} GB RAM · karta: {}": "Your computer: {} GB RAM · graphics: {}",
    " (sterownik NVIDIA aktywny — będzie szybko)": " (NVIDIA driver active — it will be fast)",
    "   ← zalecany dla Ciebie": "   ← recommended for you",
    "<b>Instaluję…</b> Możesz zostawić to okno otwarte — to potrwa kilka minut.":
        "<b>Installing…</b> You can leave this window open — it will take a few minutes.",
    "✔ Bot jest gotowy!": "✔ The bot is ready!",
    "Zamknij to okno i wybierz scenkę w „Rozmowa z botem”.": "Close this window and choose a situation in “Chat with the bot”.",
    "✘ Nie udało się.": "✘ It didn't work.",
    "Sprawdź internet i miejsce na dysku, potem spróbuj ponownie.": "Check the internet and disk space, then try again.",
    # page_scenes.py
    "Odegraj dialog z lekcji: Paco mówi swoje kwestie na głos, a Ty mówisz swoje do mikrofonu. Każda Twoja kwestia dostaje ocenę wymowy słowo po słowie, na końcu dostajesz wynik całej scenki.":
        "Act out a dialogue from a lesson: Paco says his lines aloud and you say yours into the microphone. "
        "Each of your lines gets a word-by-word pronunciation score, and at the end you get a score for the whole scene.",
    "Ocena wymowy wymaga modelu rozpoznawania mowy — zainstaluj go na ekranie „Dzisiaj”.":
        "Pronunciation scoring needs a speech recognition model — install it on the “Today” screen.",
    "Brak dialogów do odegrania.": "No dialogues to act out.",
    "{} · Lekcja {}: {}": "{} · Lesson {}: {}", "Role: {}  ·  {} kwestii": "Roles: {}  ·  {} lines", " i ": " and ",
    "Gram: {}": "I play: {}", "Grasz: {}  ·  Paco gra: {}  ·  kwestia {} z {}": "You play: {}  ·  Paco plays: {}  ·  line {} of {}",
    "Twoja kolej — powiedz:": "Your turn — say:", "Dalej ▶": "Next ▶", "Pomiń": "Skip", "{} mówi:": "{} says:",
    "Koniec scenki!": "End of the scene!",
    "¡Excelente! Brzmisz bardzo naturalnie.": "¡Excelente! You sound very natural.",
    "¡Muy bien! Jeszcze trochę wprawy.": "¡Muy bien! Just a bit more practice.",
    "Nieźle — powtórz scenkę i mów wolniej.": "Not bad — repeat the scene and speak more slowly.",
    "Posłuchaj Paco jeszcze raz i spróbuj ponownie.": "Listen to Paco again and try once more.",
    "Do poćwiczenia:": "To practise:",
    "Nie oceniono żadnej kwestii — spróbuj nagrać swoje kwestie.": "No line was scored — try recording your lines.",
    "↻  Jeszcze raz": "↻  Once more", "Zamień role": "Swap roles", "Wróć do listy": "Back to the list",
    # pages_course.py: planned levels
    "{} · w planach": "{} · planned",
    "Poziom {} jest w planach — pojawi się w jednej z kolejnych wersji.": "Level {} is planned — it will come in a future version.",
    # pages_more.py: link to create a Claude API key
    "🔑 Utwórz klucz API (console.anthropic.com)": "🔑 Create an API key (console.anthropic.com)",
    "Otwiera w przeglądarce stronę Anthropic, na której zakładasz konto i tworzysz klucz (przycisk „Create Key”). Skopiuj go i wklej obok.":
        "Opens the Anthropic page in your browser, where you sign up and create a key (the “Create Key” button). Copy it and paste it next to this.",
})
