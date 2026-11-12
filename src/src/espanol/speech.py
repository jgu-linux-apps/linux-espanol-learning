"""Silniki mowy: synteza (Piper) i rozpoznawanie (faster-whisper),
instalowane przy pierwszym uruchomieniu do ~/.local/share/linux-espanol-learning."""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import urllib.request

from .paths import VENV, VOICES, MODELS, TTS_CACHE, HERE

PIPER_VERSION = "1.8.0"
WHISPER_VERSION = "1.2.1"

VOICE_FILES = {
    "m": ("es_ES-davefx-medium", "es/es_ES/davefx/medium"),
    "f": ("es_ES-sharvard-medium", "es/es_ES/sharvard/medium"),
}
# dodatkowe głosy Piper (pobierane na żądanie z Ustawień): klucz -> (plik, ścieżka, opis)
EXTRA_VOICES = {
    "es_carlfm": ("es_ES-carlfm-x_low", "es/es_ES/carlfm/x_low", "Męski — Hiszpania (carlfm, lekki)"),
    "es_mls1": ("es_ES-mls_10246-low", "es/es_ES/mls_10246/low", "Hiszpania (mls_10246)"),
    "es_mls2": ("es_ES-mls_9972-low", "es/es_ES/mls_9972/low", "Hiszpania (mls_9972)"),
    "mx_ald": ("es_MX-ald-medium", "es/es_MX/ald/medium", "Męski — Meksyk (ald)"),
    "mx_claude": ("es_MX-claude-high", "es/es_MX/claude/high", "Żeński — Meksyk (claude, wysoka jakość)"),
}
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/{path}/{name}{ext}?download=true"

WHISPER_SIZES = {
    "base": ("Szybki", "ok. 150 MB"),
    "small": ("Dokładny", "ok. 470 MB"),
    "medium": ("Bardzo dokładny (zalecana karta NVIDIA)", "ok. 1,5 GB"),
}

VENV_PY = os.path.join(VENV, "bin", "python")


# ------------------------------------------------------------------ sprzęt
def hardware():
    cores = os.cpu_count() or 2
    ram = 0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    ram = int(line.split()[1]) / 1024 / 1024
    except OSError:
        pass
    gpus = []
    vendors = {"0x10de": "NVIDIA", "0x1002": "AMD", "0x8086": "Intel"}
    for p in glob.glob("/sys/class/drm/card[0-9]/device/vendor"):
        try:
            v = open(p).read().strip()
            gpus.append(vendors.get(v, v))
        except OSError:
            pass
    gpus = sorted(set(gpus))
    cpu = ""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    nvidia_driver = shutil.which("nvidia-smi") is not None
    return dict(cores=cores, ram=round(ram, 1), gpus=gpus, cpu=cpu, nvidia=("NVIDIA" in gpus and nvidia_driver))


def recommend(hw):
    if hw["cores"] >= 6 and hw["ram"] >= 12:
        return "small"
    if hw["cores"] >= 4 and hw["ram"] >= 7:
        return "small" if hw["cores"] >= 8 else "base"
    return "base"


def meets_minimum(hw):
    problems = []
    if hw["cores"] < 4:
        problems.append(f"procesor ma {hw['cores']} rdzenie (minimum 4)")
    if hw["ram"] and hw["ram"] < 7.5:
        problems.append(f"pamięć RAM: {hw['ram']} GB (minimum 8 GB)")
    return problems


# ------------------------------------------------------------------ stan
def engine_installed():
    if not os.path.exists(VENV_PY):
        return False
    return os.path.exists(os.path.join(VENV, ".ok"))


def voices_installed():
    return all(os.path.exists(os.path.join(VOICES, n + ".onnx")) for n, _ in VOICE_FILES.values())


def voice_info(key):
    """(nazwa pliku, ścieżka w repozytorium) dla dowolnego głosu."""
    if key in VOICE_FILES:
        return VOICE_FILES[key]
    e = EXTRA_VOICES.get(key)
    return (e[0], e[1]) if e else VOICE_FILES["m"]


def voice_available(key):
    return os.path.exists(os.path.join(VOICES, voice_info(key)[0] + ".onnx"))


def download_voice(key, progress, done):
    """Pobiera dodatkowy głos w tle. progress(frac), done(ok, komunikat)."""
    def work():
        try:
            name, path = voice_info(key)
            os.makedirs(VOICES, exist_ok=True)
            for i, ext in enumerate((".onnx.json", ".onnx")):
                dest = os.path.join(VOICES, name + ext)
                if os.path.exists(dest):
                    continue
                url = VOICE_URL.format(path=path, name=name, ext=ext)
                tmp = dest + ".part"
                req = urllib.request.Request(url, headers={"User-Agent": "linux-espanol-learning"})
                with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
                    total = int(r.headers.get("Content-Length") or 0)
                    got = 0
                    while True:
                        chunk = r.read(1 << 16)
                        if not chunk:
                            break
                        f.write(chunk)
                        got += len(chunk)
                        if total:
                            progress((i + got / total) / 2)
                os.replace(tmp, dest)
            done(True, "")
        except Exception as e:  # noqa
            done(False, str(e))
    threading.Thread(target=work, daemon=True).start()


def whisper_ready(size):
    return os.path.exists(os.path.join(MODELS, f".ok-{size}"))


# ------------------------------------------------------------------ instalacja
class Setup:
    """Instalacja komponentów w tle. log(text), progress(frac 0..1 lub None), done(ok, msg)."""

    def __init__(self, size, cuda, log, progress, done):
        self.size, self.cuda = size, cuda
        self.log, self.progress, self.done = log, progress, done
        self.cancelled = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _sh(self, args, env=None):
        self.log("$ " + " ".join(os.path.basename(a) if i == 0 else a for i, a in enumerate(args)))
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        for line in p.stdout:
            line = line.rstrip()
            if line:
                self.log("  " + line[-160:])
        if p.wait() != 0:
            raise RuntimeError(f"polecenie zakończyło się błędem ({p.returncode})")

    def _run(self):
        try:
            if not engine_installed():
                self.log("Krok 1/3: przygotowanie silnika mowy (Piper + Whisper)…")
                self.progress(0.05)
                if not os.path.exists(VENV_PY):
                    self._sh([sys.executable, "-m", "venv", VENV])
                pip = [VENV_PY, "-m", "pip", "install", "--disable-pip-version-check", "--progress-bar", "off"]
                self._sh(pip + ["--upgrade", "pip"])
                self.progress(0.15)
                self._sh(pip + [f"piper-tts=={PIPER_VERSION}", f"faster-whisper=={WHISPER_VERSION}"])
                open(os.path.join(VENV, ".ok"), "w").write("ok")
            if self.cuda and not glob.glob(os.path.join(VENV, "lib", "python*", "site-packages", "nvidia", "cudnn")):
                self.log("Pobieranie bibliotek CUDA dla karty NVIDIA (ok. 1 GB)…")
                self._sh([VENV_PY, "-m", "pip", "install", "--disable-pip-version-check", "--progress-bar", "off",
                          "nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"])
            self.progress(0.4)
            self.log("Krok 2/3: pobieranie głosów hiszpańskich (Hiszpania)…")
            os.makedirs(VOICES, exist_ok=True)
            items = list(VOICE_FILES.values())
            for i, (name, path) in enumerate(items):
                for ext in (".onnx.json", ".onnx"):
                    dest = os.path.join(VOICES, name + ext)
                    if os.path.exists(dest):
                        continue
                    url = VOICE_URL.format(path=path, name=name, ext=ext)
                    self.log(f"  {name}{ext}")
                    self._download(url, dest, 0.4 + 0.2 * i / len(items), 0.2 / len(items))
            self.progress(0.6)
            self.log(f"Krok 3/3: pobieranie modelu rozpoznawania mowy „{self.size}” "
                     f"({WHISPER_SIZES[self.size][1]})… to może chwilę potrwać.")
            os.makedirs(MODELS, exist_ok=True)
            env = engine_env(self.cuda)
            code = ("import sys; from faster_whisper.utils import download_model; "
                    f"download_model({self.size!r}, cache_dir={MODELS!r}); print('gotowe')")
            self._sh([VENV_PY, "-c", code], env=env)
            open(os.path.join(MODELS, f".ok-{self.size}"), "w").write("ok")
            self.progress(1.0)
            self.log("Wszystko gotowe. ¡Vamos!")
            self.done(True, "")
        except Exception as e:  # noqa
            self.log(f"BŁĄD: {e}")
            self.done(False, str(e))

    def _download(self, url, dest, base, span):
        tmp = dest + ".part"
        req = urllib.request.Request(url, headers={"User-Agent": "linux-espanol-learning"})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            got = 0
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total:
                    self.progress(base + span * got / total)
        os.replace(tmp, dest)


def engine_env(cuda=False):
    env = dict(os.environ)
    env["HF_HUB_DISABLE_TELEMETRY"] = "1"
    env["HF_HUB_VERBOSITY"] = "error"
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    env["HF_HOME"] = os.path.join(MODELS, "hf")
    if cuda:
        libs = glob.glob(os.path.join(VENV, "lib", "python*", "site-packages", "nvidia", "*", "lib"))
        env["LD_LIBRARY_PATH"] = ":".join(libs + [env.get("LD_LIBRARY_PATH", "")])
    return env


def pad_wav(path, lead=0.35, tail=0.25):
    """Dodaje ciszę na początku i końcu nagrania — karta dźwiękowa „budzi się” przez
    ułamek sekundy i bez tego ucina początek krótkich słów (np. „¡Hola!”)."""
    import wave
    try:
        with wave.open(path, "rb") as w:
            params, data = w.getparams(), w.readframes(w.getnframes())
        frame = params.sampwidth * params.nchannels
        with wave.open(path + ".pad", "wb") as w:
            w.setparams(params)
            w.writeframes(b"\0" * (int(params.framerate * lead) * frame) + data +
                          b"\0" * (int(params.framerate * tail) * frame))
        os.replace(path + ".pad", path)
    except Exception:  # noqa
        pass


# ------------------------------------------------------------------ workery
class Worker:
    def __init__(self, args, env=None):
        self.args, self.env = args, env
        self.proc = None
        self.lock = threading.Lock()
        self.warning = None

    def _ensure(self):
        if self.proc and self.proc.poll() is None:
            return
        self.proc = subprocess.Popen(self.args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, env=self.env, bufsize=1)
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("silnik mowy nie uruchomił się")
            msg = json.loads(line)
            if msg.get("warning"):
                self.warning = msg["warning"]
            if msg.get("ready"):
                break

    def request(self, obj):
        with self.lock:
            self._ensure()
            self.proc.stdin.write(json.dumps(obj) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
            if not line:
                self.proc = None
                raise RuntimeError("silnik mowy przerwał pracę")
            return json.loads(line)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()


class Speech:
    """Fasada używana przez interfejs."""

    def __init__(self, db):
        self.db = db
        self._tts = None
        self._stt = None
        self._stt_key = None

    # ---- synteza ----
    def tts_available(self):
        return (engine_installed() and voices_installed()) or shutil.which("espeak-ng") is not None

    def synth(self, text, slow=False):
        """Zwraca ścieżkę do pliku WAV (z pamięci podręcznej)."""
        voice_key = self.db.get("voice", "m")
        speed = 1.35 if slow else float(self.db.get("tts_scale", 1.0))
        h = hashlib.sha1(f"v2|{voice_key}|{speed}|{text}".encode()).hexdigest()[:20]
        out = os.path.join(TTS_CACHE, h + ".wav")
        if os.path.exists(out):
            return out
        if engine_installed() and voices_installed():
            if self._tts is None:
                self._tts = Worker([VENV_PY, os.path.join(HERE, "workers", "tts_worker.py"), VOICES],
                                   engine_env())
            if not voice_available(voice_key):
                voice_key = "m"
            name = voice_info(voice_key)[0]
            spk = None
            try:
                cfg = json.load(open(os.path.join(VOICES, name + ".onnx.json")))
                m = cfg.get("speaker_id_map") or {}
                if m:
                    spk = m.get("F" if voice_key == "f" else "M", 0)
            except Exception:  # noqa
                pass
            say = text.strip()
            if say and say[-1] not in ".!?…":
                say += "."  # pełne zdanie = stabilniejsza intonacja
            if len(say.split()) <= 2:
                speed *= 1.12  # pojedyncze słowa nieco wolniej i wyraźniej
            r = self._tts.request({"text": say, "voice": name, "speaker": spk, "length_scale": speed,
                                   "out": out})
            if not r.get("ok"):
                raise RuntimeError(r.get("error"))
            pad_wav(out)
            return out
        if shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", "-v", "es", "-s", "120" if slow else "150", "-w", out, text], check=True)
            return out
        raise RuntimeError("Brak silnika mowy — dokończ instalację komponentów w Ustawieniach.")

    # ---- rozpoznawanie ----
    def stt_available(self):
        size = self.db.get("whisper", "small")
        return engine_installed() and whisper_ready(size)

    def transcribe(self, wav, prompt=None):
        size = self.db.get("whisper", "small")
        cuda = bool(self.db.get("cuda", False))
        key = (size, cuda)
        if self._stt is None or self._stt_key != key:
            if self._stt:
                self._stt.stop()
            self._stt = Worker([VENV_PY, os.path.join(HERE, "workers", "stt_worker.py"), MODELS, size,
                                "cuda" if cuda else "cpu"], engine_env(cuda))
            self._stt_key = key
        r = self._stt.request({"path": wav, "prompt": prompt} if prompt else {"path": wav})
        if not r.get("ok"):
            raise RuntimeError(r.get("error"))
        return r

    def preload_stt(self):
        if self.stt_available():
            threading.Thread(target=lambda: self._safe(lambda: self._ping()), daemon=True).start()

    def _ping(self):
        size = self.db.get("whisper", "small")
        cuda = bool(self.db.get("cuda", False))
        if self._stt is None:
            self._stt = Worker([VENV_PY, os.path.join(HERE, "workers", "stt_worker.py"), MODELS, size,
                                "cuda" if cuda else "cpu"], engine_env(cuda))
            self._stt_key = (size, cuda)
        self._stt.request({"cmd": "ping"})

    @staticmethod
    def _safe(fn):
        try:
            fn()
        except Exception:  # noqa
            pass

    def shutdown(self):
        for w in (self._tts, self._stt):
            if w:
                w.stop()
