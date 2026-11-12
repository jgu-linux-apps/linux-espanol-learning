"""Worker syntezy mowy (Piper). Uruchamiany w środowisku silnika (venv).
Protokół: JSON w jednej linii na stdin -> JSON w jednej linii na stdout."""
import json
import os
import sys
import wave


def main():
    voices_dir = sys.argv[1]
    from piper import PiperVoice, SynthesisConfig
    cache = {}

    def voice(name):
        if name not in cache:
            path = os.path.join(voices_dir, name + ".onnx")
            cache[name] = PiperVoice.load(path)
        return cache[name]

    print(json.dumps({"ready": True}), flush=True)
    for line in sys.stdin:
        try:
            req = json.loads(line)
            v = voice(req["voice"])
            spk = req.get("speaker")
            cfg = SynthesisConfig(speaker_id=spk, length_scale=float(req.get("length_scale", 1.0)),
                                  noise_scale=0.5, noise_w_scale=0.6)
            tmp = req["out"] + ".part"
            with wave.open(tmp, "wb") as wf:
                v.synthesize_wav(req["text"], wf, syn_config=cfg)
            os.replace(tmp, req["out"])
            print(json.dumps({"ok": True, "path": req["out"]}), flush=True)
        except Exception as e:  # noqa
            print(json.dumps({"ok": False, "error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
