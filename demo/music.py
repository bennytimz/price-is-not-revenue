"""Original lo-fi background music, synthesised from scratch with numpy (no samples, no downloads).

Two versions at 90 BPM, each an 8-bar loop tiled to the requested length, with fade in and fade out:
  A: F major colour, Fmaj7 - Em7 - Dm7 - Cmaj7, warm additive pad, kick on 1 and the "and" of 3.
  B: A minor colour, Am9 - Fmaj9 - Cmaj7 - G6, softer sine pad plus a quiet plucked arpeggio,
     kick on 1, the "and" of 2 and 3, a different bass rhythm.
Both use a gentle kick, a swung hi-hat, a warm pad and a simple bass line.
"""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 90
BEAT = 60.0 / BPM
BAR = 4 * BEAT


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def lp(x, hz, order=2):
    return sosfilt(butter(order, hz, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, hz, order=2):
    return sosfilt(butter(order, hz, "high", fs=SR, output="sos"), x, axis=0)


def add(buf, start_s, sig, gain=1.0, pan=0.0):
    """Mix a mono signal into a stereo buffer, wrapping around the loop end (seamless loop)."""
    n = len(buf)
    i0 = int(round(start_s * SR)) % n
    l = gain * np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
    r = gain * np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
    idx = (i0 + np.arange(len(sig))) % n
    np.add.at(buf[:, 0], idx, sig * l)
    np.add.at(buf[:, 1], idx, sig * r)


def kick(vel):
    t = np.arange(int(0.45 * SR)) / SR
    f = 46 + (105 - 46) * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.26)
    s[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return lp(s, 3000) * vel


def hat(rng, vel, decay):
    t = np.arange(int(0.25 * SR)) / SR
    s = hp(rng.standard_normal(len(t)), 7000, 4) * np.exp(-t / decay)
    return lp(s, 12000) * vel * 0.35


def tone(freq, dur, harmonics, detune_cents=(0.0,), attack=0.5, release=0.8, lfo_hz=0.0, phase_seed=0):
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(phase_seed)
    s = np.zeros(n)
    for c in detune_cents:
        f = freq * 2 ** (c / 1200.0)
        for k, a in enumerate(harmonics, start=1):
            s += a * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 2 * np.pi))
    s /= len(detune_cents)
    env = np.ones(n)
    na = int(attack * SR)
    env[:na] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    nd = int(dur * SR)
    env[nd:] = np.exp(-(t[nd:] - dur) / (release / 4))
    if lfo_hz:
        env *= 1 - 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * lfo_hz * t))
    return s * env


def bass_note(freq, dur):
    n = int((dur + 0.12) * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.22 * np.sin(2 * np.pi * 2 * freq * t) + 0.06 * np.sin(2 * np.pi * 3 * freq * t)
    env = np.minimum(1, t / 0.012) * np.where(t < dur, np.exp(-t / (dur * 2.5)), np.exp(-dur / (dur * 2.5)) * np.exp(-(t - dur) / 0.04))
    return np.tanh(1.4 * s * env) / np.tanh(1.4)


def pluck(freq, vel):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)) * np.exp(-t / 0.22)
    s[: int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return lp(s, 2500) * vel


VERSIONS = {
    "A": dict(
        chords=[[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]],  # Fmaj7 Em7 Dm7 Cmaj7
        roots=[41, 40, 38, 36],
        pad_harm=[1.0, 0.45, 0.22, 0.12, 0.06, 0.03],
        pad_lp=1900,
        kicks=[0.0, 2.5],
        bass=[(0.0, 1.4, 0), (1.5, 0.45, 0), (2.5, 1.0, 0), (3.5, 0.45, 7)],  # (beat, length in beats, semitones above root)
        swing=0.08,
        arp=False,
        seed=11,
    ),
    "B": dict(
        chords=[[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [52, 55, 59, 60, 64], [55, 59, 62, 64, 67]],  # Am9 Fmaj9 Cmaj7 G6
        roots=[45, 41, 36, 43],
        pad_harm=[1.0, 0.25, 0.08],
        pad_lp=1500,
        kicks=[0.0, 1.5, 2.0],
        bass=[(0.0, 2.3, 0), (2.5, 0.4, 12), (3.0, 0.9, 0)],
        swing=0.11,
        arp=True,
        seed=23,
    ),
}


def make_loop(version):
    v = VERSIONS[version]
    rng = np.random.default_rng(v["seed"])
    bars = 8
    n = int(round(bars * BAR * SR))
    drums = np.zeros((n, 2))
    pad = np.zeros((n, 2))
    bass = np.zeros((n, 2))
    arp = np.zeros((n, 2))
    for b in range(bars):
        t0 = b * BAR
        ci = b % 4
        chord = v["chords"][ci]
        for j, m in enumerate(chord):
            s = tone(midi_hz(m), BAR, v["pad_harm"], detune_cents=(-6, 0, 6), attack=0.6, release=1.2,
                     lfo_hz=0.15 + 0.03 * j, phase_seed=v["seed"] * 100 + b * 10 + j)
            add(pad, t0, s, gain=0.11, pan=(-0.5 + j / max(1, len(chord) - 1)) * 0.6)
        root = v["roots"][ci]
        for beat, length, semis in v["bass"]:
            add(bass, t0 + beat * BEAT, bass_note(midi_hz(root + semis), length * BEAT), gain=0.42)
        for kb in v["kicks"]:
            add(drums, t0 + kb * BEAT, kick(0.9 if kb == 0 else 0.65), gain=0.8)
        for e in range(8):
            off = e * BEAT / 2 + (v["swing"] * BEAT if e % 2 else 0)
            vel = (0.55 if e % 2 == 0 else 0.32) * rng.uniform(0.85, 1.1)
            decay = 0.12 if (e == 7 and b % 2 == 1) else 0.032
            add(drums, t0 + off, hat(rng, vel, decay), gain=0.8, pan=0.25)
        if v["arp"]:
            seq = chord[1:] + [chord[1] + 12]
            for k in range(8):
                if k in (3, 7) and b % 2 == 0:
                    continue
                add(arp, t0 + k * BEAT / 2 + (v["swing"] * BEAT if k % 2 else 0),
                    pluck(midi_hz(seq[k % len(seq)] + 12), rng.uniform(0.7, 1.0)), gain=0.07, pan=-0.35 + 0.1 * (k % 4))
    pad = lp(pad, v["pad_lp"])
    bass = lp(bass, 500)
    mix = drums + pad + bass + arp
    mix = lp(np.tanh(mix * 1.2) / 1.2, 9500)  # gentle saturation and a soft top end
    return mix


def make_music(version, total_s, fade_in=2.0, fade_out=3.0):
    loop = make_loop(version)
    n = int(round(total_s * SR))
    reps = int(np.ceil(n / len(loop)))
    out = np.tile(loop, (reps, 1))[:n].copy()
    t = np.arange(n) / SR
    env = np.clip(t / fade_in, 0, 1) * np.clip((total_s - t) / fade_out, 0, 1)
    env = 0.5 - 0.5 * np.cos(np.pi * env)
    out *= env[:, None]
    return out / (np.max(np.abs(out)) + 1e-9) * 0.7
