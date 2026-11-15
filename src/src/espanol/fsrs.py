"""Planowanie powtórek — algorytm FSRS (wersja 4.5, domyślne wagi).

Oceny: 1 = Nie pamiętam, 2 = Trudne, 3 = Dobrze, 4 = Łatwe.
"""
import math
import time
from .i18n import _  # noqa: E402

W = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474,
     0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755]
DECAY = -0.5
FACTOR = 19 / 81
DAY = 86400
RETENTION = 0.9
MAX_INTERVAL_DAYS = 365

NEW, LEARNING, REVIEW, RELEARNING = 0, 1, 2, 3


def _clamp_d(d):
    return min(10.0, max(1.0, d))


def init_difficulty(g):
    return _clamp_d(W[4] - (g - 3) * W[5])


def retrievability(elapsed_days, stability):
    if stability <= 0:
        return 0.0
    return (1 + FACTOR * elapsed_days / stability) ** DECAY


def interval_days(stability, retention=RETENTION):
    i = stability / FACTOR * (retention ** (1 / DECAY) - 1)
    return max(1, min(MAX_INTERVAL_DAYS, round(i)))


def review(card, grade, now=None):
    """card: dict(state, stability, difficulty, due, last_review, reps, lapses).
    Zwraca nowy dict."""
    now = now or time.time()
    c = dict(card)
    state = c.get("state", NEW)
    s = c.get("stability") or 0.0
    d = c.get("difficulty") or 0.0
    last = c.get("last_review") or now
    elapsed = max(0.0, (now - last) / DAY)
    c["reps"] = (c.get("reps") or 0) + 1

    if state == NEW:
        s = W[grade - 1]
        d = init_difficulty(grade)
    else:
        r = retrievability(elapsed, s)
        d_new = d - W[6] * (grade - 3)
        d = _clamp_d(W[7] * init_difficulty(4) + (1 - W[7]) * d_new)
        if grade == 1:
            c["lapses"] = (c.get("lapses") or 0) + 1
            s = W[11] * d ** (-W[12]) * ((s + 1) ** W[13] - 1) * math.exp(W[14] * (1 - r))
        else:
            hard = W[15] if grade == 2 else 1.0
            easy = W[16] if grade == 4 else 1.0
            if elapsed < 1 and state in (LEARNING, RELEARNING):
                # powtórka tego samego dnia — niewielki wzrost
                s = s * math.exp(0.3 * (grade - 3) + 0.2)
            else:
                s = s * (math.exp(W[8]) * (11 - d) * s ** (-W[9]) *
                         (math.exp(W[10] * (1 - r)) - 1) * hard * easy + 1)
    s = max(0.1, s)

    if grade == 1:
        c["state"] = RELEARNING if state in (REVIEW, RELEARNING) else LEARNING
        c["due"] = now + 10 * 60  # za 10 minut
    elif grade == 2 and state in (NEW, LEARNING, RELEARNING) and s < 1:
        c["state"] = LEARNING
        c["due"] = now + 30 * 60
    else:
        c["state"] = REVIEW
        c["due"] = now + interval_days(s) * DAY
    c["stability"] = s
    c["difficulty"] = d
    c["last_review"] = now
    return c


def preview_intervals(card, now=None):
    """Teksty typu '10 min', '3 dni' dla czterech przycisków."""
    now = now or time.time()
    out = []
    for g in (1, 2, 3, 4):
        n = review(card, g, now)
        out.append(human_delta(n["due"] - now))
    return out


def human_delta(sec):
    if sec < 3600:
        return _('{} min').format(max(1, round(sec / 60)))
    if sec < DAY:
        return f"{round(sec / 3600)} godz."
    d = round(sec / DAY)
    if d == 1:
        return _("1 dzień")
    if d < 31:
        return _('{} dni').format(d)
    m = round(d / 30)
    return f"{m} mies."
