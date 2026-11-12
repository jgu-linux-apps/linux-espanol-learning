"""Własna, prywatna instalacja Ollamy (bez sudo) + pobieranie modelu.

Ollama trafia do ~/.local/share/linux-espanol-learning/ollama, modele do .../ollama-models,
a serwer startuje automatycznie razem z rozmową (port 11435) i zamyka się z aplikacją.
Jeśli w systemie działa już Ollama (localhost:11434), używamy jej."""
import json
import os
import platform
import shutil
import subprocess
import threading
import time
import urllib.request

from .paths import USER_DATA

DIR = os.path.join(USER_DATA, "ollama")
MODELS_DIR = os.path.join(USER_DATA, "ollama-models")
BIN = os.path.join(DIR, "bin", "ollama")
SYSTEM_URL = "http://127.0.0.1:11434"
MANAGED_HOST = "127.0.0.1:11435"
MANAGED_URL = "http://" + MANAGED_HOST

# Modele do wyboru w kreatorze (nazwa, opis, rozmiar pobierania)
MODELS = [
    ("qwen3:8b", "Zalecany — bardzo dobry hiszpański (Qwen 3, 8B)", "ok. 5,2 GB",
     "najlepiej z kartą NVIDIA 6–8 GB lub 16 GB RAM"),
    ("qwen3:14b", "Najmądrzejszy — najlepsze rozmowy (Qwen 3, 14B)", "ok. 9 GB",
     "wymaga karty NVIDIA 12 GB+ lub 32 GB RAM; wolniejszy"),
    ("gemma3:4b", "Szybki — lżejszy model (Gemma 3, 4B)", "ok. 3,3 GB",
     "dla słabszych komputerów; częściej się myli"),
]


def recommended_model(hw):
    if hw.get("nvidia") or hw.get("ram", 0) >= 15:
        return MODELS[0][0]
    return MODELS[1][0]


def _alive(url, timeout=2):
    try:
        with urllib.request.urlopen(url + "/api/tags", timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:  # noqa
        return None


def system_ollama():
    return _alive(SYSTEM_URL) is not None


def installed():
    return os.path.exists(BIN)


class Manager:
    """Uruchamia prywatny serwer Ollamy na żądanie."""
    _proc = None
    _lock = threading.Lock()

    @classmethod
    def ensure_running(cls, wait=30):
        if _alive(MANAGED_URL):
            return MANAGED_URL
        if not installed():
            raise RuntimeError("Ollama nie jest zainstalowana — użyj przycisku „Zainstaluj Ollamę i model”.")
        with cls._lock:
            if cls._proc is None or cls._proc.poll() is not None:
                env = dict(os.environ, OLLAMA_HOST=MANAGED_HOST, OLLAMA_MODELS=MODELS_DIR)
                os.makedirs(MODELS_DIR, exist_ok=True)
                log = open(os.path.join(DIR, "serve.log"), "ab")
                cls._proc = subprocess.Popen([BIN, "serve"], env=env, stdout=log, stderr=log,
                                             start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < wait:
            if _alive(MANAGED_URL, 1):
                return MANAGED_URL
            time.sleep(0.5)
        raise RuntimeError("Serwer Ollamy nie wystartował (szczegóły: ~/.local/share/"
                           "linux-espanol-learning/ollama/serve.log)")

    @classmethod
    def stop(cls):
        if cls._proc and cls._proc.poll() is None:
            cls._proc.terminate()
            try:
                cls._proc.wait(5)
            except Exception:  # noqa
                cls._proc.kill()
        cls._proc = None


class Installer:
    """Kroki: (1) pobranie i rozpakowanie Ollamy, (2) start serwera, (3) pobranie modelu."""

    def __init__(self, model, use_system, log, progress, done):
        self.model, self.use_system = model, use_system
        self.log, self.progress, self.done = log, progress, done

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            if self.use_system:
                url = SYSTEM_URL
                self.log("Używam Ollamy zainstalowanej w systemie.")
            else:
                if not installed():
                    self._install()
                self.log("Uruchamiam serwer Ollamy…")
                url = Manager.ensure_running()
            self.log(f"Pobieram model {self.model}… (to największy plik — może potrwać kilka–kilkanaście minut)")
            self._pull(url)
            self.progress(1.0)
            self.log("Gotowe! Bot jest gotowy do rozmowy. ¡Vamos a hablar!")
            self.done(True, url)
        except Exception as e:  # noqa
            self.log(f"BŁĄD: {e}")
            self.done(False, str(e))

    def _install(self):
        arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine())
        if not arch:
            raise RuntimeError(f"nieobsługiwana architektura: {platform.machine()}")
        os.makedirs(DIR, exist_ok=True)
        base = f"https://ollama.com/download/ollama-linux-{arch}"
        zst = shutil.which("zstd") is not None
        url, kind = (base + ".tar.zst", "zst") if zst and self._exists(base + ".tar.zst") else (base + ".tgz", "tgz")
        self.log(f"Krok 1/2: pobieram Ollamę ({url.rsplit('/', 1)[1]}; z bibliotekami dla kart NVIDIA, ok. 1–2 GB)…")
        tmp = os.path.join(DIR, "download." + kind)
        req = urllib.request.Request(url, headers={"User-Agent": "linux-espanol-learning"})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            got, last = 0, 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total:
                    self.progress(0.4 * got / total)
                if got - last > 100 << 20:
                    last = got
                    self.log(f"  {got >> 20} MB" + (f" / {total >> 20} MB" if total else ""))
        self.log("Rozpakowuję…")
        if kind == "zst":
            cmd = ["tar", "--use-compress-program=unzstd", "-xf", tmp, "-C", DIR]
        else:
            cmd = ["tar", "-xzf", tmp, "-C", DIR]
        subprocess.run(cmd, check=True)
        os.remove(tmp)
        if not installed():
            raise RuntimeError("w archiwum nie znaleziono programu ollama")
        os.chmod(BIN, 0o755)
        self.log("Ollama zainstalowana (bez uprawnień administratora).")

    @staticmethod
    def _exists(url):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "linux-espanol-learning"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status == 200
        except Exception:  # noqa
            return False

    def _pull(self, url):
        req = urllib.request.Request(url + "/api/pull", data=json.dumps({"model": self.model, "stream": True}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        seen = {}
        with urllib.request.urlopen(req, timeout=600) as r:
            for line in r:
                if not line.strip():
                    continue
                msg = json.loads(line.decode())
                if msg.get("error"):
                    raise RuntimeError(msg["error"])
                st = msg.get("status", "")
                if msg.get("total"):
                    frac = msg.get("completed", 0) / msg["total"]
                    self.progress(0.45 + 0.55 * frac)
                    dec = int(frac * 10)
                    key = st + str(msg["total"])
                    if seen.get(key) != dec:
                        seen[key] = dec
                        self.log(f"  pobieranie: {msg.get('completed', 0) >> 20} / {msg['total'] >> 20} MB "
                                 f"({int(frac * 100)}%)")
                elif seen.get(st) is None:
                    seen[st] = 1
                    self.log("  " + st)
