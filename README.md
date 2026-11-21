# Linux Español Learning

**A real Spanish course from scratch for Ubuntu**: Spanish from Spain (castellano), explained in Polish or English.
Lessons, grammar, vocabulary, spaced repetition, tests and pronunciation scoring.

Version **1.20.1** · Created by: **JGu** · Supported by **Claude** · part of the *JGu Linux Apps* series

> **Language note:** the course is available **for Polish speakers** and, since 1.14, **for English
> speakers**. The course language belongs to the learner profile (☰ profile menu →
> “Name and language”), so one person can learn in Polish and another in English on the same computer.
> In English: the whole interface, the alphabet and pronunciation tips for English speakers, all 40 lessons
> (A1 and A2), the readings, the dictionary, the video list, the scenes and the bot (Paco), who corrects,
> translates and explains in English.

---

## What's inside

| Module | Contents |
|---|---|
| **A1–A2 course** | 40 lessons in 10 units (A1: 20, A2: 20). Every lesson has 5 steps: a dialogue with audio → vocabulary → grammar (explained in Polish or English) → exercises → speaking. Plus culture notes and a link to videos on the topic. |
| **Alphabet and pronunciation** | All letters with their names, a pronunciation guide for Polish or English speakers (by course language) and examples; difficult sounds (rr, j/g, c/z as "th", ll, ñ, b=v, silent h); stress rules; how to type á é í ó ú ñ ¿ ¡. |
| **Exercises** | Multiple choice, fill in the gap, translation PL→ES, verb conjugation, dictation (by ear), building a sentence from shuffled words. About 430 hand-written exercises plus ones generated from the dialogues and vocabulary. A missing accent is not a mistake (you get a reminder); a typo counts as half a point. |
| **Review** | Two tabs. **Flashcards** with the **FSRS** algorithm (as in modern Anki): words get here automatically after you finish a lesson; ES→PL/EN, PL/EN→ES or alternating; keyboard shortcuts Space and 1–4. **Mistakes — training**: exercises you got wrong (lessons, tests, readings) and sentences corrected by Paco come back tomorrow, then in 3 and in 7 days; after 3 correct answers in a row they disappear. |
| **ES–PL / ES–EN dictionary** | Its own Spanish–Polish (or Spanish–English) dictionary, about **1000 entries**: words from the lessons and topic lists, with part of speech, examples and audio. Search in both directions, also without accents. |
| **Conjugation** | Conjugation tables for any verb: presente, perfecto, indefinido, imperfecto, futuro, condicional, imperativo, *ir a*, *estar + gerundio* — with the **vosotros** form and with irregular, reflexive and stem-changing verbs. |
| **Pronunciation lab** | Listen → record yourself → word-by-word score (green/red), result in %, playback of your own recording and tips on typical mistakes of Polish (or English) speakers. |
| **Scenes with Paco** | Lesson dialogues to act out loud: Paco plays one role, you play the other; every line gets a pronunciation score and the whole scene gets a result. |
| **Dictation** | Paco reads a sentence and you type it; a colour comparison word by word (green — correct, yellow — missing accent, red — mistake), rounds of 8 sentences from finished lessons. |
| **Readings** | 10 texts (one per unit), with audio, translation, a glossary and questions. |
| **Tests and exams** | A test for every unit (15 questions) and a mock A1 / A2 exam (about 40 questions: vocabulary, grammar, translation, listening, reading + a speaking part). Pass mark 60%. Score history. |
| **Videos and listening** | Hand-picked channels with Spanish from Spain (Español con Juan, Easy Spanish, Español Automático, Spanish with Vicente, María Español, Dreaming Spanish, RTVE Play, *Aquí no hay quien viva*). They open in the browser. |
| **Today** | One big **Continue** card that takes you back to the lesson you were doing, exactly to the step where you stopped; rings for the daily goal, the streak and the level progress; a week strip; a **Plan for today** (review, lesson, exercise of the day); the hardest words and a word of the day. |
| **Chat with the bot** | Text **and voice** conversation in Spanish with a partner who only knows the material of your finished lessons (vocabulary, dialogues, grammar). 11 scenes (free talk, bar, market, directions, shop, plans, holidays, hotel, doctor, job interview, renting a flat). Corrections in the course language (Polish or English) next to your lines — every sentence goes through a separate grammar check, so typical beginner mistakes are caught reliably — translation of the replies, playback in the narrator's voice, highlighting of words beyond your lessons, automatic simplifying of replies that are too hard, and a summary (mistakes → statistics, new words → review). |
| **Statistics** | Finished lessons, mastered words, minutes of study (30-day chart), average pronunciation score, recent mistakes. |

The interface is classic GTK 3 and follows the system light/dark theme automatically — together with the window and dock icons.

### Themes (Settings → Appearance)
| Theme | Character |
|---|---|
| **Coral (default)** | coral and sunny gold; dark — the same coral on a warm graphite background |
| **Pomarańcz** | the former default: peach and orange; dark — orange on dark brown |
| **Mediterráneo** | sea turquoise and blue; dark — turquoise on a dark sea background |
| **System** | the Ubuntu (Yaru) look, light or dark like the system |
| **Aurora** | the shared theme of the JGu Linux Apps series: light — pastel glass, violet → cyan gradient; dark — an aurora glow on deep navy |
| **España** | red and gold of the Spanish flag; dark — burgundy and gold |
| **Azulejo** | blue and white of Seville tiles; dark — night navy |
| **Oliva** | olive and terracotta of Andalusia; dark — dark olive |

Every theme has a light and a dark variant: *Automatic (like the system)*, *Always light* or *Always dark*. The change applies at once, without a restart.

## Requirements

| | Minimum | Recommended |
|---|---|---|
| System | Ubuntu 24.04+ (64-bit) | Ubuntu 26.04 / 26.10 |
| CPU | 4 cores (about the last 6 years) | 6–8 cores (e.g. Ryzen 5/7) |
| RAM | 8 GB | 16 GB |
| Disk | about 1 GB | about 1.5 GB |
| Graphics | any (integrated is enough) | NVIDIA — optionally speeds up speech recognition (CUDA) |
| Audio | speakers + any microphone | a headset with a microphone |
| Internet | only on the first start (downloading the models) | — |

The app checks the hardware itself (Settings → *Your computer*) and picks the speech recognition model:
**Fast** (`base`, about 150 MB) or **Accurate** (`small`, about 470 MB). With an NVIDIA card you can choose **Very accurate** (`medium`) and turn on CUDA.

## Installation

Download the newest `linux-espanol-learning_<version>_all.deb` from the [Releases page](https://github.com/jgu-linux-apps/linux-espanol-learning/releases/latest):

```bash
sudo apt install ./linux-espanol-learning_<version>_all.deb
```

The app appears in the menu as **"Linux Español Learning"** (command: `linux-espanol-learning`).

### First start
The **"Speech engine installation"** wizard opens and downloads once (to `~/.local/share/linux-espanol-learning`):
1. the **Piper** engine (speech synthesis) and **faster-whisper** (speech recognition): Python packages in a separate environment, about 200 MB;
2. two voices from Spain: male `es_ES-davefx-medium` and female `es_ES-sharvard-medium` (about 130 MB);
3. the Whisper model chosen for your computer.

After that everything works **offline**. The wizard can be run again from Settings (e.g. to change the model).
Before the engine is installed, audio is played by `espeak-ng` as a fallback (if installed) — it sounds robotic, but works.

## Paco and user profiles (1.7)
- **Paco** — an animated little robot conversation partner in a black beret, with a moustache and a scarf in the colours of Spain. He moves his mouth in time with the narrator's voice (following the real loudness of the audio), tilts his head and shows sound waves while listening, looks up and "thinks" while waiting for a reply, blinks and sways gently. He is happy after a flawless answer and makes a concerned, gentle face after a mistake. Drawn with Cairo — no extra files.
- **User profiles** — the "👤 name" button in the window bar: several people on one computer, each with their own progress, review, conversation history, theme and "About me" data. Switching without a restart; profiles can be added, renamed and deleted. Shared by everyone: the speech engines, the models, the bot (Ollama/Claude) and the API key. Existing progress goes to the default profile, shown as "Główny" in Polish and "Main" in English (until you rename it).
- **The bot does not repeat questions** — a question that was already asked in the conversation is rejected (in voice mode it is not read out). Known facts about the learner are passed to the bot together with a list of topics it must not ask about again.
- Profile data: `~/.local/share/linux-espanol-learning/profiles/<name>/postep.db` (the main profile: `postep.db`).

## What's new in the bot conversation (1.6)
- **About me (for the bot)** — a new tab: you enter your name, town, job, family, interests. The bot treats this as true and doesn't keep asking about the same things. In addition, the app picks up facts from what you say in Spanish ("me llamo…", "vivo en…", "trabajo como…", "me gusta…"); you see them in this tab and can delete them.
- **Partner level** — *Slow and simple* (no new words, very short sentences), *Normal*, *Challenge* (longer replies, up to two new words).
- **Conversation score** 0–100 (flawless lines, length of your lines, variety of words).
- **Conversation history** — every finished conversation is saved with the full transcript, corrections and score; you can open it, replay the bot's lines and follow your progress.
- **Corrected sentences to review** — sent to the flashcards with one click.
- In voice conversation you can switch the speech recognition model (if you have several installed).
- The bot's corrections are always in the course language (Polish or English), never in Spanish; the bot does not repeat its own sentences.

## Voice conversation with the bot (since 1.4)
On the conversation screen click **🎤 Mów** (Speak) and say a sentence in Spanish. The app detects the start and end of your speech itself (after about 3 s of silence — you have time to think; change the length in *Settings → Chat with the bot*, or click **✔ Skończyłem mówić** (I've finished)). Whisper turns the speech into text, and the bot answers in the narrator's voice — **it starts speaking from the first finished sentence**, without waiting for the whole reply.
- **The partner speaks aloud** — turns reading the replies on/off.
- **Hands-free** — after a reply the app listens again by itself (a conversation without touching the mouse; it ends when you are silent for about 12 s).
- Clicking 🎤 while the bot is speaking interrupts it and gives you the floor. Typing works in parallel.
- Required: an installed speech recognition model (Settings), a microphone and ideally a headset (so the microphone doesn't pick up the partner's voice). With replies read out as they arrive, too-difficult replies are not simplified automatically — words beyond your lessons are still underlined.

## Chat with the bot — setup
In **Settings → Chat with the bot** choose the engine:
- **Ollama (local, offline, free)** — click **"Install Ollama and the model"** (in Settings or on the *Chat with the bot* screen). The app downloads Ollama to your home directory by itself (no sudo, about 1–2 GB including libraries for NVIDIA cards) and the chosen model: **Qwen 3 8B** (recommended, about 5.2 GB — best with an NVIDIA card or 16 GB RAM) or **Gemma 3 4B** (faster, about 3.3 GB). A private Ollama server starts by itself for the conversation (port 11435) and closes together with the app. If Ollama is already on the system, the app uses it and downloads only the model. Your own server can be set in the *Advanced* section.
- **Bielik for Polish translations (offline, optional)** — Settings → Chat with the bot: “Polskie tłumaczenia offline przez Bielika”. [Bielik](https://huggingface.co/speakleash) (SpeakLeash) is a Polish language model; downloaded on request with one click (about 6.7 GB) into the same private Ollama. It only translates Paco's lines and answers your questions in Polish; the chat and the mistake check stay on the main model. Much better Polish than the main model, but replies take about twice as long (on a 6 GB graphics card the two models take turns in memory). Polish course only; when the Claude option is also ticked, Claude comes first.
- **Claude API (cloud)** — paste an API key from console.anthropic.com (the “Create an API key” link next to the key field opens the right page) and choose the model (Haiku — fast and cheap, Sonnet — the best). Only the text of the conversation is sent to the API. The key is stored in the system password store (GNOME Keyring), or, without one, locally in `~/.config/linux-espanol-learning/claude_api_key` (mode 600). Using the API is paid.

## Where the data is

| What | Where |
|---|---|
| Progress (lessons, review, tests, statistics) | `~/.local/share/linux-espanol-learning/postep.db` (SQLite) |
| Speech engine and models | `~/.local/share/linux-espanol-learning/{engine,voices,whisper}` |
| Offline bot (Ollama and models) | `~/.local/share/linux-espanol-learning/{ollama,ollama-models}` |
| Audio cache, your recordings | `~/.cache/linux-espanol-learning/` |

Backing up your progress = copying the `postep.db` file (or Settings → Backup).

## Uninstalling

```bash
sudo apt remove linux-espanol-learning
rm -rf ~/.local/share/linux-espanol-learning ~/.cache/linux-espanol-learning   # optional: models and progress
```

## Building from source

The source code is in the `src/` directory of the repository (`.deb` packages are not kept in git, they are on [Releases](https://github.com/jgu-linux-apps/linux-espanol-learning/releases)).
Pushing a tag `vX.Y.Z` that matches `VERSION` in `src/src/espanol/__init__.py` starts GitHub Actions
(`.github/workflows/release.yml`), which builds the package and publishes the release. Run the commands below in `src/`:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
     gstreamer1.0-plugins-good python3-venv librsvg2-bin dpkg-dev
./bin/linux-espanol-learning      # run without installing
./build-deb.sh                    # -> dist/linux-espanol-learning_<version>_all.deb
```

### Layout
```
src/espanol/          code: content (lessons), conjugate (conjugation), fsrs (review), answers (checking),
                      speech (Piper/Whisper + installer), audio (GStreamer), db (SQLite), ui/ (GTK 3)
src/espanol/workers/  speech engine processes run in a separate Python environment
data/lessons/a1, a2/  lessons in a simple text format (easy to add more)
data/readings/        readings;  data/alphabet.txt, vocab_extra.txt, videos.txt
icons/                light and dark icon (SVG)
packaging/            .desktop file, the icon light/dark helper and its autostart entry
```

### Lesson format (for extending the course)
```
# id: a1-01
# title: ¡Hola! Powitania
# unit: 1
# unit_title: Primeros pasos
@goals          one goal per line
@dialog         Person: Spanish sentence | translation
@vocab          word | translation | part of speech | example ES / example PL
@grammar        text: ## heading, - bullet, || table | columns, **bold**
@exercises      fill|choice|trans|conj: question | answer /// another correct one | options; separated; by semicolons
@culture        culture note
```

## Honest limitations
- Pronunciation scoring works **at word level** (whether Whisper understood what you were supposed to say). It's a good test of intelligibility, but not an analysis of individual sounds like a teacher would do.
- The Piper voices are synthetic — very decent, but no substitute for recordings of native speakers. That's why the *Videos and listening* module points to real material.
- The course covers A1–A2. The subjunctive (subjuntivo) and other B1 topics are deliberately left out for now; B1 and B2 are planned (greyed out on the Course screen).
- The app is in Polish and English (see the language note at the top).

## Credits
- [Piper](https://github.com/OHF-Voice/piper1-gpl) (GPL-3.0, downloaded separately on the first start) and the voices from [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) — speech synthesis
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) / OpenAI Whisper — speech recognition
- [FSRS](https://github.com/open-spaced-repetition) — review algorithm
- The order of the material is inspired by the CEFR levels and the Instituto Cervantes curriculum (PCIC). The lesson texts, dialogues, readings and the dictionary are original.

## License
**Freeware License (No Modifications)** — the app is free to use and to share unmodified; modifying it and distributing changed versions is not permitted (see `LICENSE`).
Components downloaded separately on the first start (Piper, faster-whisper, voices, Whisper models) have their own licenses.

## Version history
- **1.20.1** — in the English version the download sizes (speech recognition models, offline bot models, Bielik) are in English too: “about 150 MB”, “5.2 GB” instead of “ok. 150 MB”, “5,2 GB”. A test checks it.
- **1.20.0** — **faster chat with Paco**: his reply appears (and is read aloud) straight away and the chat is unlocked at once; the translation is done in the background and fills the line under the bubble (“translating…”) a few seconds later. With qwen3:8b the wait until you can answer dropped from about 10 s to about 5 s per turn, with the same translation quality.
- **1.19.0** — **all bot settings in one place, as big tiles**: Settings → Chat with the bot now has four numbered steps — (1) Paco's brain: Fast (qwen3:8b), Smarter (qwen3:14b), Light (gemma3:4b) or Claude, each tile showing whether the model is downloaded and warning when it does not fit in your graphics card's memory (then it runs mostly on the processor and is several times slower); (2) translations: the same model, Bielik (Polish course) or Claude; (3) speech recognition: fast / accurate / very accurate; (4) how many seconds of silence end what you say. A model that is not downloaded is never switched on by a click — a download button appears instead. The Claude API key and the “Create an API key” link show up only when Claude is chosen; your own Ollama server is under “Advanced”. The speech-recognition choice moved here from “Speech engine”.
- **1.18.0** — **Bielik as an optional Polish translator** (offline): a Polish language model for Paco's translations and Polish explanations, downloaded on request (about 6.7 GB). In a test on 34 typical Paco replies it made about 7 mistakes against about 20 for the main model (qwen3:8b), with almost no grammar mistakes; replies take about twice as long. Translations that add content the Spanish sentence does not have are now rejected and translated again, and copied prompt notes are cut from explanations. The mistake check always stays on the main model.
- **1.17.3** — **complete translations of Paco's replies**: every sentence is translated on its own line, so nothing is shortened any more ("Yo también tomo café" was sometimes shown as just "Me too"); a sentence that comes back much shorter than the Spanish one is translated again, and the formal *usted* is translated as a polite "you" (Pan/Pani in Polish). The Polish translation gets an extra proofreading pass for case endings and calques. With the offline model the Polish translations can still contain grammar mistakes — for the best Polish, turn on translations through the Claude API in Settings.
- **1.17.2** — Settings → Chat with the bot (Claude API engine): a **“Create an API key”** link next to the key field opens the Anthropic console page where you create a key.
- **1.17.1** — the Course screen shows the next levels **B1** and **B2** as greyed-out “planned” buttons (“w planach” in Polish), so you can see where the course is heading.
- **1.17.0** — **Paco catches mistakes much more reliably** (Polish and English versions): every sentence you say is checked by a separate, short grammar check that runs at the same time as Paco's reply. In tests with the offline model (qwen3:8b) it caught 20 of 20 typical beginner mistakes (yo tiene, yo es, ser/estar, gender, gustar, past tense) with no false alarms on correct sentences, where before Paco noticed about one mistake in three. Missing accents and a left-out “yo” are not counted as mistakes; if the check fails, the correction from Paco's reply is used as before.
- **1.16.1** — in the English version the default profile is called “Main” instead of “Główny” (a renamed profile keeps its name), and the Aurora and Oliva theme names are in English.
- **1.16.0** — **English version (part 3)**: the bot (Paco) and the scenes in English. For an English-speaking learner Paco translates his replies into English, writes corrections in English, recognises questions asked in English (“how do I say…”, “what's the difference between…”) and answers them in English, and no longer assumes the learner lives in Poland; the 11 bot situations, levels, summaries, chat history, the offline bot installer and the “Scenes with Paco” screen are in English too. The Polish version works as before. Tests check the bot's prompt, help-question detection and phrasebook in both languages.
- **1.15.0** — **English version (part 2)**: the 20 A2 lessons, the 10 readings (translations and glossaries), the 284 extra dictionary words and the video list are in English too, so the whole course except the bot works in English. Grammar notes compare with English where it helps (present perfect, “used to”, “-ing”, “for/since”). Tests check that the English readings and vocabulary keep exactly the same Spanish as the Polish ones.
- **1.14.0** — **English version (part 1)**: every learner profile has its own course language, Polish or English (chosen when you create a profile and in “Name and language”; switching to a profile in another language restarts the app). In English: the whole interface, the alphabet with pronunciation tips written for English speakers, the pronunciation feedback, and all 20 A1 lessons (dialogue translations, vocabulary, grammar, exercises, culture notes). The Spanish stays the same in both versions, so progress and reviews carry over. The A2 lessons, readings, extra dictionary words and the bot follow in the next versions. Tests check that every text has an English version and that the English lessons match the Polish ones.
- **1.13.6** — the app icons in the GitHub release packages use the Ubuntu font for "¡ñ!" again (1.13.4 and 1.13.5 release packages drew it in a fallback font). No other changes.
- **1.13.5** — the voice no longer reads the slash: "el tío / la tía" is read as "el tío", a short pause, "la tía"; "él/ella" the same, and "nosotros/as" as "nosotros… nosotras". Pronunciation practice stops recording by itself after a moment of silence (the same setting as the voice conversation, 3 s by default; Settings → "Recording — silence that ends what you say"); clicking still works, and with no speech for 8 s it stops and asks you to try again.
- **1.13.4** — new icons in the series style: dark — the "¡ñ!" bubble on a deep navy tile, light — a gold bubble on a cream tile; the dock and app-menu icon switches light/dark together with the system, also while the app is closed (a small helper started at login and by the app itself).
- **1.13.0** — new look: **sidebar in foldable groups** (Learn, Practice, Tools, You; a review counter next to "Powtórki", Settings in the ☰ menu); **"Today"** with one big "Continue" card, rings for the daily goal, the streak and the level progress, a week strip, a **Plan for today** (review, lesson, exercise of the day), the hardest words and a word of the day; **"Course"** with an A1/A2 switch, a progress ring for every unit, the current lesson expanded (lesson parts and "Continue") and stars and scores on finished lessons; **focus-mode exercises** (no sidebar, a segmented progress bar, a big prompt, answer cards with keys 1–4, a coloured result bar). New default theme **Coral**, new **Mediterráneo**, the former orange one as **Pomarańcz** — each with a light and a dark variant in the same hue.
- **1.12.0** — new **Aurora** theme (Settings → Appearance), the same as in the other apps of the series: violet-cyan gradients, a glow on hover, light and dark variants switching together with the system.
- **1.11.0** — **mistake training**: Review has two tabs — *Flashcards* and *Mistakes (training)*; every exercise you get wrong (in a lesson, test or reading) and every sentence corrected by Paco comes back in full (the same type, options, audio) tomorrow, then in 3 and in 7 days, and disappears after 3 correct answers in a row; typos and missing accents don't count; existing mistakes are moved over automatically; a counter on the Today screen and in Statistics. **🐢 Slower**: slow playback is always clearly slower than the speed chosen in Settings (before, with the "Slow" speed it was barely different) and now has a button also in the scenes, in the conversation with Paco, in the readings and in the flashcards.
- **1.10.4** — license: the app is now published under the Freeware License (No Modifications), see `LICENSE` — free to use and share unmodified, modification is not permitted; no other changes in the app.
- **1.10.3** — no changes in the app: the code is in the `src/` directory of the repository, the `.deb` package is on the GitHub Releases page (built automatically for every version tag); README: installing from Releases.
- **1.10.2** — better Polish translations of Paco's lines: a glossary of ready, checked translations of the most common phrases, translating "the meaning, not word for word" with examples of difficult constructions (gustar, preferences) and a short second round of Polish proofreading.
- **1.10.1** — the Modern theme (light "Soft" and dark "Glass") got the same effects as the others: highlight and glow of the active menu item, accent on hover, smooth transitions; new project address: github.com/jgu-linux-apps; improved description of the placement test.
- **1.10.0** — the Claude API key goes to the system password store (GNOME Keyring; the old file is migrated automatically, and without a store — a file with mode 600); **placement test** (Tests and exams and a card on the "Today" screen for new learners: questions of increasing difficulty → a recommended starting lesson, optionally marking the earlier ones as known); **pronunciation in statistics** (a 30-day chart of the daily average score + the hardest sentences); **keyboard shortcuts** (F1 — list, Ctrl+1…9 — screens, Ctrl+M — bot microphone, F2/F3/F4 in Dictation, Ctrl+Enter in Scenes).
- **1.9.0** — **Scenes with Paco**: you act out a lesson dialogue (choosing your role), Paco says his lines aloud and you say yours into the microphone — every line gets a word-by-word pronunciation score, and at the end the whole scene gets a result and a list of lines to practise; **progress backup** (Settings → Backup): saving the current profile to a .zip file and loading it as a new profile (e.g. on another computer), without overwriting anything.
- **1.8.0** — study streak and daily goal (a card on the "Today" screen, goal settings 5–60 min, a system reminder at a chosen hour when the goal isn't met); a new **Dictation** screen (Paco reads a sentence from finished lessons, you type it; a colour comparison word by word, a round of 8 sentences, a list to review); lesson 7: a new section "How to choose ser/estar quickly", the most common mistakes of Polish speakers and 10 new exercises; subtle theme effects (España, Azulejo, Oliva): accent glow, soft gradients, smooth transitions, improved highlight of the active menu item.
- **1.7.6** — the question "how do I say…" in Polish: Paco gives a ready sentence in Spanish with an explanation and WAITS until you say it yourself (he doesn't carry on the conversation); the question and the explanation don't go into the history or the conversation score.
- **1.7.5** — better Polish: translations of the bot's lines are done by a separate, simple pass (low temperature, a model example), explanations are written in Polish with an example, without markdown or emoji; in Settings you can turn on the Claude API just for the Polish translations and explanations (the conversation stays local).
- **1.7.4** — "Paco's explanation": when you ask something in Polish during the conversation (e.g. "when do you say somos and when es?"), the bot answers with a separate card in Polish — the rule and examples — and then briefly returns to the conversation in Spanish (without false "corrections").
- **1.7.3** — the "Mów" (Speak) button in a modern, bigger look (rounded, with a gradient, red while recording); the partner introduces himself as Paco (matching the mascot).
- **1.7.2** — voice: in Settings a choice of extra Piper voices (Spain: carlfm, mls_10246, mls_9972; Mexico: ald, claude — downloaded on first use) and a "▶ Listen" button; if "¡Hola!" sounds wrong in one voice, choose another. Bot: clear "who is who" rules (it doesn't state the learner's facts about itself, answers about itself to "¿Y tú?"), example lines in the prompt, the topic from the first sentence, a filter for sentences that attribute the learner's facts to the bot; a new model Qwen 3 14B (for stronger computers).
- **1.7.1** — a smarter bot: Ollama gets 8192 tokens of context (the default 2048 cut off the instructions), a repetition penalty; the bot has a personality (Paco from Madrid), leads the conversation (reaction → something about itself → a new question on the next topic), doesn't repeat the learner's lines or questions; memory between conversations (facts and "what you talked about last time", visible in the "About me" tab); lighter vocabulary limits for beginners.
- **1.7.0** — Paco: an animated little robot in the conversation; user profiles on one computer; the bot doesn't repeat questions or ask again about known facts.
- **1.6.0** — the "About me (for the bot)" tab and facts from conversations, partner levels, conversation score, conversation history, exporting corrected sentences to review, choosing the speech model in the conversation, the bot "believes the learner" and doesn't ask again about what it already heard (including the content of the planned 1.4.3 and 1.5).
- **1.4.2** — bot quality: corrections always in Polish (with automatic translation when the model answers in Spanish), a "Correct" field, corrections only of your own lines, no repeated turns, the bot doesn't come back to words beyond the lessons; the summary laid out as You → Correct → explanation.
- **1.4.1** — more time to speak: 3 s of silence by default (up to 6 s), an "I've finished" button, 25 s to gather your thoughts, a context hint for speech recognition.
- **1.4.0** — voice conversation with the bot: end-of-speech detection, speech recognition, replies read out as they stream from the first sentence, hands-free mode, interrupting the bot, a silence-length setting.
- **1.3.3** — a new default look (light "Soft", dark "Glass", switching with the system theme); clear hints in the exercises (part of speech, first letter, number of letters) instead of abbreviations like "v", "phr".
- **1.3.2** — the "Speaking" step ends with a "Finish" button and a lesson summary (instead of a loop); clearer pronunciation of short words (silence before the audio, more stable synthesis).
- **1.3.1** — one-click installation of the offline bot: Ollama (no sudo) + a choice of the Qwen 3 8B / Gemma 3 4B model with a progress bar; the server starts automatically.
- **1.3.0** — Chat with the bot (text version): scenes from the lessons, limited to the material covered, corrections, a summary; the Ollama engine (local) or the Claude API.
- **1.2.0** — "Continue where you left off" and a course progress table in % on the Today screen.
- **1.1.0** — the España, Azulejo and Oliva colour themes (each light and dark) and a choice of light / dark / automatic mode.
- **1.0.2** — fixed pronunciation scoring: the error "open() got an unexpected keyword argument 'metadata_errors'" (faster-whisper incompatible with the new PyAV library); recordings are now loaded directly, without PyAV.
- **1.0.1** — fixed the error "SQLite objects created in a thread…" when playing pronunciation; the new name "Linux Español Learning"; a clear message when the speech engine installation finishes; the HF_TOKEN warning hidden; freeware license.
- **1.0.0** — first release.

Created by: JGu · Supported by Claude
