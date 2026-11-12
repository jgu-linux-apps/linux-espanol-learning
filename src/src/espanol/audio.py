"""Odtwarzanie i nagrywanie dźwięku przez GStreamer."""
import os
import time

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # noqa: E402

Gst.init(None)


class Player:
    def __init__(self):
        self.pb = Gst.ElementFactory.make("playbin", "player")
        bus = self.pb.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_msg)
        self.on_done = None

    def play(self, path, on_done=None):
        self.pb.set_state(Gst.State.NULL)
        self.on_done = on_done
        self.pb.set_property("uri", Gst.filename_to_uri(path))
        self.pb.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pb.set_state(Gst.State.NULL)

    def _on_msg(self, bus, msg):
        if msg.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
            self.pb.set_state(Gst.State.NULL)
            cb, self.on_done = self.on_done, None
            if cb:
                cb()


class Vad:
    """Prosty detektor mowy po poziomie dźwięku (dB RMS co ~50 ms).
    Zdarzenia: "start" (zaczęto mówić), "end" (cisza po mowie), "timeout" (nikt nie mówi), "max"."""

    def __init__(self, end_silence=3.0, wait=25.0, max_len=60.0, min_speech=0.35):
        self.end_silence, self.wait, self.max_len, self.min_speech = end_silence, wait, max_len, min_speech
        self.noise = []
        self.thr = -45.0
        self.speaking = False
        self.loud = 0
        self.speech_t = 0.0       # łączny czas mowy
        self.last_loud_t = 0.0
        self.done = False

    def feed(self, db, t):
        """db — poziom, t — sekundy od startu nagrywania. Zwraca nazwę zdarzenia lub None."""
        if self.done:
            return None
        if t < 0.4:  # kalibracja szumu tła
            self.noise.append(db)
            if self.noise:
                srt = sorted(self.noise)
                self.thr = max(-45.0, min(-25.0, srt[len(srt) // 2] + 11))
            return None
        if t > self.max_len:
            self.done = True
            return "max"
        if db > self.thr:
            self.loud += 1
            self.last_loud_t = t
            if not self.speaking and self.loud >= 3:
                self.speaking = True
                return "start"
            if self.speaking:
                self.speech_t += 0.05
        else:
            self.loud = 0
            if self.speaking and t - self.last_loud_t >= self.end_silence:
                self.done = True
                return "end" if self.speech_t >= self.min_speech else "timeout"
        if not self.speaking and t > self.wait:
            self.done = True
            return "timeout"
        return None


class Recorder:
    """Nagrywa mono 16 kHz WAV. on_level(0..1) — poziom mikrofonu.
    Z vad=Vad(...) i on_event(nazwa) wykrywa początek i koniec wypowiedzi."""

    def __init__(self):
        self.pipe = None
        self.path = None
        self.on_level = None
        self._stop_cb = None
        self.started = 0
        self.vad = None
        self.on_event = None

    @staticmethod
    def available():
        return Gst.ElementFactory.find("autoaudiosrc") is not None and Gst.ElementFactory.find("wavenc") is not None

    def start(self, path, on_level=None, vad=None, on_event=None):
        self.path = path
        self.on_level = on_level
        self.vad, self.on_event = vad, on_event
        if os.path.exists(path):
            os.remove(path)
        desc = ("autoaudiosrc ! audioconvert ! audioresample ! "
                "audio/x-raw,format=S16LE,rate=16000,channels=1 ! level name=lvl interval=50000000 ! "
                f"wavenc ! filesink location=\"{path}\"")
        self.pipe = Gst.parse_launch(desc)
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_msg)
        self.pipe.set_state(Gst.State.PLAYING)
        self.started = time.time()

    def stop(self, cb):
        """Kończy nagranie; cb(path) po zapisaniu pliku."""
        if not self.pipe:
            cb(None)
            return
        self._stop_cb = cb
        self.pipe.send_event(Gst.Event.new_eos())
        GLib.timeout_add(1500, self._force_stop)

    def _force_stop(self):
        if self.pipe:
            self._finish()
        return False

    def _finish(self):
        pipe, self.pipe = self.pipe, None
        if pipe:
            pipe.set_state(Gst.State.NULL)
        cb, self._stop_cb = self._stop_cb, None
        if cb:
            cb(self.path if os.path.exists(self.path) and os.path.getsize(self.path) > 2000 else None)

    def _on_msg(self, bus, msg):
        if msg.type == Gst.MessageType.ELEMENT and msg.get_structure().get_name() == "level":
            st = msg.get_structure()
            try:
                rms = st.get_value("rms")
                db = max(rms) if rms else -60
                lvl = min(1.0, max(0.0, (db + 50) / 50))
                if self.on_level:
                    self.on_level(lvl)
                if self.vad and self.on_event:
                    ev = self.vad.feed(db, time.time() - self.started)
                    if ev:
                        self.on_event(ev)
            except Exception:  # noqa
                pass
        elif msg.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
            if msg.type == Gst.MessageType.ERROR:
                err, _ = msg.parse_error()
                print("Błąd nagrywania:", err)
            self._finish()
