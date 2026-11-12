"""Worker rozpoznawania mowy (faster-whisper). Uruchamiany w środowisku silnika (venv).
argv: katalog_modeli rozmiar urządzenie(cpu|cuda)"""
import json
import sys
import wave


def load_audio(path):
    """Wczytaj nagranie WAV (16 kHz, mono, 16 bit) bez PyAV.
    PyAV 15+ nie przyjmuje już argumentu metadata_errors, którego używa faster-whisper 1.2.1,
    dlatego dekodujemy sami i przekazujemy gotową tablicę numpy."""
    import numpy as np
    with wave.open(path, "rb") as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError("nieobsługiwany format WAV")
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if rate != 16000 and len(a):
        x_new = np.linspace(0, len(a) - 1, int(len(a) * 16000 / rate))
        a = np.interp(x_new, np.arange(len(a)), a).astype(np.float32)
    return a


def main():
    models_dir, size, device = sys.argv[1], sys.argv[2], sys.argv[3]
    from faster_whisper import WhisperModel
    compute = "int8" if device == "cpu" else "float16"
    try:
        model = WhisperModel(size, device=device, compute_type=compute, download_root=models_dir)
    except Exception as e:  # np. brak bibliotek CUDA -> spróbuj na procesorze
        if device != "cpu":
            print(json.dumps({"warning": f"CUDA niedostępne ({e}); używam procesora"}), flush=True)
            model = WhisperModel(size, device="cpu", compute_type="int8", download_root=models_dir)
        else:
            raise
    print(json.dumps({"ready": True}), flush=True)
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req.get("cmd") == "ping":
                print(json.dumps({"ok": True}), flush=True)
                continue
            try:
                audio = load_audio(req["path"])
            except Exception:  # noqa — inny format: niech spróbuje faster-whisper
                audio = req["path"]
            segments, info = model.transcribe(
                audio, language="es", beam_size=5, word_timestamps=True,
                vad_filter=False, condition_on_previous_text=False, temperature=0.0,
                initial_prompt=req.get("prompt") or None)
            words, text = [], []
            for seg in segments:
                text.append(seg.text)
                for w in (seg.words or []):
                    words.append({"w": w.word.strip(), "p": round(w.probability, 3)})
            print(json.dumps({"ok": True, "text": " ".join(t.strip() for t in text).strip(),
                              "words": words}), flush=True)
        except Exception as e:  # noqa
            print(json.dumps({"ok": False, "error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
