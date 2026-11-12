"""Build the demo video from real pages: the live dashboard and the GitHub repo.

    pip install -r demo/requirements-demo.txt
    python -m playwright install chromium
    python demo/make_demo.py            # full build
    python demo/make_demo.py --audio-only   # redo music, mix and mux, keep the rendered picture

Outputs (in demo/):
    price-is-not-revenue-demo-A.mp4        music version A
    price-is-not-revenue-demo-B.mp4        music version B
    price-is-not-revenue-demo-nomusic.mp4  voice only
    demo_report.txt                        measured durations, loudness and checks
Intermediate files go to demo/build/ (git-ignored).

What is real: every page is loaded live with Playwright (Chromium) and captured frame by frame while
the script scrolls it. The terminal scene shows the actual output of `python verify_data.py` and
`python pull_bigquery.py` (dry run only; this script never passes --run), captured by running them
when the video is built; the output is shown in a terminal-style window with typing sped up.
The end card is a plain title card. No numbers are typed into this script: every number on screen
comes from the live pages or from the commands' own output, and the spoken numbers are in
demo/narration.txt, checked against the results files.
"""
import argparse
import asyncio
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

DEMO = Path(__file__).resolve().parent
REPO = DEMO.parent
BUILD = DEMO / "build"
sys.path.insert(0, str(DEMO))
import music  # noqa: E402

OUTPUTS = {
    "A": DEMO / "price-is-not-revenue-demo-A.mp4",
    "B": DEMO / "price-is-not-revenue-demo-B.mp4",
    "nomusic": DEMO / "price-is-not-revenue-demo-nomusic.mp4",
}

W, H, FPS = 1920, 1080, 60
VW, VH = 1152, 648          # CSS viewport; 1152 x 5/3 = 1920
DSF = 5 / 3
HI_DSF = 2.5                # for the two slow push-in scenes
SR = 48000

VOICE = "en-US-AvaMultilingualNeural"
RATE = "-5%"
LEAD = 0.25                 # voice starts this long after its scene starts
PAD = 0.5                   # scene = line audio + PAD
XF = 0.4                    # crossfade between scenes
END_HOLD = 1.5              # extra hold on the end card (after the last line's scene time)
FADE_IN, FADE_OUT = 0.35, 0.6
VOICE_LUFS = -16.0
MUSIC_BELOW = 18.0          # music (before ducking) this many LU below the voice; the brief asks for at least 16

DASH = "https://bennytimz.github.io/price-is-not-revenue/dashboard.html"
GH = "https://github.com/bennytimz/price-is-not-revenue"
BLOB = GH + "/blob/main/"

# How the voice should say a word (captions keep the written form)
TTS_SUBS = {"NEAR's": "Near's", "NEAR": "Near", "DefiLlama": "DeFi Llama", "BigQuery": "Big Query"}
# Spoken form -> written form in captions. Each written number is the one in the results files.
CAPTION_SUBS = [
    ("nine-point-four-x", "9.4x"),
    ("twenty million dollars", "$20 million"),
    ("fifteen percent", "15%"),
    ("nine point four times", "9.4 times"),
    ("March thirty-first, twenty twenty-seven", "March 31, 2027"),
]
FUNC_WORDS = {"the", "a", "an", "of", "to", "and", "on", "in", "that", "from", "with", "is", "for", "as"}


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg  # pip install imageio-ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FF = ffmpeg_exe()


def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(map(str, cmd))}\n{p.stderr[-3000:]}")
    return p


# ----------------------------------------------------------------------------------------------- voice
def core(tok):
    m = re.match(r"^(\W*)(.*?)([^\w']*)$", tok)
    return m.group(1), m.group(2), m.group(3)


def tts_text(tokens):
    spans, parts, pos = [], [], 0
    for t in tokens:
        lead, c, trail = core(t)
        s = lead + TTS_SUBS.get(c, c) + trail
        spans.append((pos, pos + len(s)))
        parts.append(s)
        pos += len(s) + 1
    return " ".join(parts), spans


async def _tts(text, mp3):
    import edge_tts
    com = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    events = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                events.append({"text": ch["text"], "start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7})
    return events


def make_voice_lines(lines):
    BUILD.mkdir(exist_ok=True)
    out = []
    for i, line in enumerate(lines):
        tokens = line.split()
        text, spans = tts_text(tokens)
        key = hashlib.sha256(f"{VOICE}|{RATE}|{text}".encode()).hexdigest()[:16]
        mp3, wav, js = BUILD / f"line{i + 1}.mp3", BUILD / f"line{i + 1}.wav", BUILD / f"line{i + 1}.json"
        cached = js.exists() and json.loads(js.read_text()).get("key") == key and wav.exists()
        if not cached:
            events = asyncio.run(_tts(text, mp3))
            run([FF, "-y", "-v", "error", "-i", str(mp3), "-af", "highpass=f=70", "-ar", str(SR), "-ac", "1",
                 "-c:a", "pcm_s16le", str(wav)])
            js.write_text(json.dumps({"key": key, "tts_text": text, "events": events}, indent=1))
        meta = json.loads(js.read_text())
        sr, data = wavfile.read(wav)
        assert sr == SR
        dur = len(data) / SR
        # map word events back to the written tokens
        words = [{"w": t, "start": None, "end": None} for t in tokens]
        cur = 0
        for ev in meta["events"]:
            p = text.find(ev["text"], cur)
            if p < 0:
                p = text.lower().find(ev["text"].lower(), cur)
            if p < 0:
                continue
            a, b = p, p + len(ev["text"])
            cur = b
            for k, (s0, s1) in enumerate(spans):
                if s0 < b and a < s1:
                    w = words[k]
                    w["start"] = ev["start"] if w["start"] is None else min(w["start"], ev["start"])
                    w["end"] = ev["end"] if w["end"] is None else max(w["end"], ev["end"])
        missing = [k for k, w in enumerate(words) if w["start"] is None]
        for k in missing:  # interpolate between neighbours (reported)
            prev = next((words[j]["end"] for j in range(k - 1, -1, -1) if words[j]["end"] is not None), 0.0)
            nxt = next((words[j]["start"] for j in range(k + 1, len(words)) if words[j]["start"] is not None), dur)
            words[k]["start"], words[k]["end"] = prev, nxt
        out.append({"text": line, "tts_text": text, "wav": wav, "dur": dur, "words": words, "interpolated": missing})
    return out


# ----------------------------------------------------------------------------------------------- captions
def protect_flags(line, tokens):
    """Tokens inside a CAPTION_SUBS phrase must not end a caption (except the phrase's last token)."""
    flags = [False] * len(tokens)
    starts, pos = [], 0
    for t in tokens:
        p = line.index(t, pos)
        starts.append((p, p + len(t)))
        pos = p + len(t)
    for spoken, _ in CAPTION_SUBS:
        for m in re.finditer(re.escape(spoken), line):
            inside = [k for k, (a, b) in enumerate(starts) if a >= m.start() and b <= m.end() + 1]
            for k in inside[:-1]:
                flags[k] = True
    return flags


def display(tokens):
    s = " ".join(tokens)
    for spoken, written in CAPTION_SUBS:
        s = s.replace(spoken, written)
    return s.rstrip(",")


def split_chunk(tokens, idxs, nobreak):
    def dcount(ix):
        return len(display([tokens[j] for j in ix]).split())
    if dcount(idxs) <= 9:
        return [idxs]
    best = None
    for k in range(2, len(idxs) - 3):
        j = idxs[k]
        if nobreak[j]:
            continue
        left, right = idxs[:k + 1], idxs[k + 1:]
        w = tokens[j]
        cost = abs(dcount(left) - dcount(right))
        if w[-1] in ",:;":
            cost -= 8
        if core(w)[1].lower() in FUNC_WORDS:
            cost += 3
        if dcount(left) < dcount(right):
            cost += 0.5
        if best is None or cost < best[0]:
            best = (cost, left, right)
    if best is None:
        return [idxs]
    return split_chunk(tokens, best[1], nobreak) + split_chunk(tokens, best[2], nobreak)


def build_captions(voice, scenes_t):
    caps = []
    for i, v in enumerate(voice):
        tokens = [w["w"] for w in v["words"]]
        nob = protect_flags(v["text"], tokens)
        sents, cur = [], []
        for k, t in enumerate(tokens):
            cur.append(k)
            if re.search(r"[.!?]$", t) and not nob[k]:
                sents.append(cur)
                cur = []
        if cur:
            sents.append(cur)
        chunks = [c for s in sents for c in split_chunk(tokens, s, nob)]
        S, D = scenes_t[i]
        at = S + LEAD
        line_caps = []
        for c in chunks:
            line_caps.append({
                "scene": i, "text": display([tokens[k] for k in c]),
                "w_start": at + v["words"][c[0]]["start"], "w_end": at + v["words"][c[-1]]["end"],
                "words": [(tokens[k], at + v["words"][k]["start"], at + v["words"][k]["end"]) for k in c],
            })
        for k, c in enumerate(line_caps):
            c["start"] = c["w_start"] - 0.15
            c["end"] = c["w_end"] + 0.35
        for a, b in zip(line_caps, line_caps[1:]):
            if a["end"] > b["start"]:
                m = (a["w_end"] + b["w_start"]) / 2
                a["end"], b["start"] = m, m
        lo = S + XF / 2 + 0.02
        hi = (S + D - XF / 2 - 0.02) if i < len(voice) - 1 else (S + D - FADE_OUT - 0.05)
        line_caps[0]["start"] = max(line_caps[0]["start"], lo)
        line_caps[-1]["end"] = min(line_caps[-1]["end"], hi)
        caps += line_caps
    return caps


def load_font(size):
    for f in ["C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeuib.ttf", "/System/Library/Fonts/SFNS.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


CAP_FONT_PX = 54
CAP_MAX_W = 1640


def render_caption(text):
    """Return (rgb float array, alpha float array, x, y, n_lines, text_w) for a caption box."""
    font = load_font(CAP_FONT_PX)
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= CAP_MAX_W or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) == 2:  # balance two lines
        best = None
        for k in range(1, len(words)):
            a, b = " ".join(words[:k]), " ".join(words[k:])
            wmax = max(d.textlength(a, font=font), d.textlength(b, font=font))
            if wmax <= CAP_MAX_W and (best is None or wmax < best[0]):
                best = (wmax, [a, b])
        if best:
            lines = best[1]
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * 1.12)
    tw = max(d.textlength(l, font=font) for l in lines)
    padx, pady = 40, 22
    bw, bh = int(tw + 2 * padx), int(lh * len(lines) + 2 * pady - (lh - asc - desc))
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=20, fill=(16, 19, 24, 214))
    for k, l in enumerate(lines):
        lw = dr.textlength(l, font=font)
        dr.text(((bw - lw) / 2, pady + k * lh), l, font=font, fill=(255, 255, 255, 255))
    arr = np.asarray(img).astype(np.float32) / 255.0
    x = (W - bw) // 2
    y = H - 60 - bh
    return arr[..., :3] * 255.0, arr[..., 3], x, y, len(lines), tw


# ----------------------------------------------------------------------------------------------- picture helpers
def smoother(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


class Track:
    """Piecewise eased path through (time, value) keys; equal consecutive values are holds."""

    def __init__(self, keys):
        self.keys = sorted(keys)

    def __call__(self, t):
        k = self.keys
        if t <= k[0][0]:
            return k[0][1]
        for (ta, ya), (tb, yb) in zip(k, k[1:]):
            if ta <= t <= tb:
                return ya if tb == ta else ya + (yb - ya) * smoother((t - ta) / (tb - ta))
        return k[-1][1]


def rgb(png):
    import io
    return Image.open(io.BytesIO(png)).convert("RGB")


class Shot:
    """Scroll a live page and screenshot it; caches the last frame when the position is unchanged."""

    def __init__(self, page, name):
        self.page, self.name = page, name
        self.key, self.img = None, None
        self.max_y = page.evaluate("document.documentElement.scrollHeight - innerHeight")
        self.scroll_errors = []
        self.shots = 0

    def at(self, y_css):
        y_css = max(0.0, min(self.max_y, y_css))
        ydev = int(round(y_css * DSF))
        if ydev != self.key:
            # GitHub sets scroll-behavior: smooth, so force an instant jump and wait for two painted frames
            got = self.page.evaluate(f"""new Promise(r => {{ window.scrollTo({{top: {ydev / DSF}, left: 0, behavior: 'instant'}});
                requestAnimationFrame(() => requestAnimationFrame(() => r(window.scrollY))); }})""")
            if abs(got - ydev / DSF) > 1.0:
                self.scroll_errors.append((ydev / DSF, got))
                raise RuntimeError(f"{self.name}: asked to scroll to {ydev / DSF:.1f}, page is at {got}")
            self.img = rgb(self.page.screenshot(type="png", animations="disabled", caret="hide"))
            self.key = ydev
            self.shots += 1
        return self.img


def top_of(page, js_expr):
    return page.evaluate(f"(() => {{ const e = {js_expr}; if (!e) return null; return e.getBoundingClientRect().top + window.scrollY; }})()")


class ZoomScene:
    """A single high-resolution capture with a slow push-in (crop and downscale, no upscaling)."""

    def __init__(self, img_hi, dur, z_end=1.04, focus_y=0.4):
        self.img, self.dur, self.z_end, self.focus_y = img_hi, dur, z_end, focus_y
        self.moving = True

    def frame(self, t):
        u = min(1.0, max(0.0, t / self.dur))
        z = 1 + (self.z_end - 1) * (0.5 - 0.5 * math.cos(math.pi * u))
        iw, ih = self.img.size
        cw, ch = iw / z, ih / z
        x0 = (iw - cw) / 2
        y0 = min(max(ih * self.focus_y - ch * self.focus_y, 0), ih - ch)
        return self.img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))

    def state(self, t):
        return ("zoom", round(t, 3))


class ScrollScene:
    def __init__(self, shot, keys):
        self.shot, self.track = shot, Track(keys)

    def frame(self, t):
        return self.shot.at(self.track(t))

    def state(self, t):
        return ("scroll", self.shot.name, int(round(max(0, min(self.shot.max_y, self.track(t))) * DSF)))


class TerminalScene:
    def __init__(self, page, script):
        self.page, self.script = page, script  # script: list of (time, items)
        self.key, self.img = None, None
        self.shots = 0

    def items_at(self, t):
        items = self.script[0][1]
        for ts, it in self.script:
            if t >= ts:
                items = it
        return items

    def frame(self, t):
        items = self.items_at(t)
        k = json.dumps(items)
        if k != self.key:
            self.page.evaluate("items => render(items)", items)
            self.img = rgb(self.page.screenshot(type="png", animations="disabled"))
            self.key = k
            self.shots += 1
        return self.img

    def state(self, t):
        return ("term", json.dumps(self.items_at(t)))


class SplitScene:
    """Scene A, then a crossfade to scene B at time ts (both are part of one narration line)."""

    def __init__(self, a, b, ts):
        self.a, self.b, self.ts = a, b, ts

    def frame(self, t):
        if t < self.ts - XF / 2:
            return self.a.frame(t)
        if t > self.ts + XF / 2:
            return self.b.frame(t - self.ts)
        al = smoother((t - (self.ts - XF / 2)) / XF)
        return Image.blend(self.a.frame(t), self.b.frame(t - self.ts), al)

    def state(self, t):
        if t < self.ts - XF / 2:
            return self.a.state(t)
        if t > self.ts + XF / 2:
            return self.b.state(t - self.ts)
        return ("blend", round(t, 3))


# ----------------------------------------------------------------------------------------------- terminal
TERMINAL_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;background:#e9e6dd}
.win{position:absolute;left:48px;right:48px;top:26px;height:474px;background:#0f1419;border-radius:10px;
 box-shadow:0 12px 40px rgba(0,0,0,.28);overflow:hidden;border:1px solid #2b3036}
.bar{height:34px;background:#1b2128;display:flex;align-items:center;padding:0 14px;gap:8px;color:#9aa4ae;
 font:13px "Segoe UI",system-ui,sans-serif}
.dot{width:11px;height:11px;border-radius:50%;background:#3a4149}.title{margin-left:10px}
#t{position:absolute;left:0;right:0;bottom:0;top:34px;margin:0;padding:12px 20px;color:#e6edf3;
 font:16px/1.42 "Cascadia Mono",Consolas,"DejaVu Sans Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere;
 overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end}
.p{color:#7ee787}.c{display:inline-block;width:.6em;height:1.1em;background:#e6edf3;vertical-align:text-bottom}
</style></head><body><div class="win"><div class="bar"><span class="dot"></span><span class="dot"></span>
<span class="dot"></span><span class="title">Terminal: price-is-not-revenue (real output, captured when this video was built)</span></div>
<div id="t"></div></div><script>
function render(items){const t=document.getElementById('t');t.innerHTML='';
 for(const it of items){const d=document.createElement('div');
  if(it.cmd!==undefined){const p=document.createElement('span');p.className='p';p.textContent='price-is-not-revenue> ';
   d.appendChild(p);d.appendChild(document.createTextNode(it.cmd));
   if(it.cursor){const c=document.createElement('span');c.className='c';d.appendChild(c)}}
  else{d.textContent=it.out||' '}
  t.appendChild(d)}}
render([]);</script></body></html>"""


def capture_commands(recapture=False):
    """Run the two commands for real and keep their output (dry run only: never --run).
    The capture is reused on later runs (so finished clips stay valid) unless recapture is set."""
    cache = BUILD / "terminal_capture.json"
    if cache.exists() and not recapture:
        return json.loads(cache.read_text())
    cmds = [["python", "verify_data.py"], ["python", "pull_bigquery.py"]]
    res = []
    for c in cmds:
        assert "--run" not in c
        p = subprocess.run([sys.executable] + c[1:], cwd=REPO, capture_output=True, text=True, timeout=300)
        txt = (p.stdout + p.stderr).replace("\r\n", "\n").rstrip("\n")
        if p.returncode != 0:
            raise RuntimeError(f"{' '.join(c)} failed (exit {p.returncode}):\n{txt}")
        res.append({"cmd": " ".join(c), "output": txt.split("\n"), "exit": p.returncode})
    (BUILD / "terminal_capture.json").write_text(json.dumps(res, indent=1))
    return res


def terminal_script(caps, dur):
    """Timeline of terminal states: type each command, then print its real output line by line."""
    cps = 32.0
    steps, t, done = [], 0.15, []
    steps.append((0.0, [{"cmd": "", "cursor": True}]))
    for k, c in enumerate(caps):
        for n in range(1, len(c["cmd"]) + 1):
            steps.append((t, done + [{"cmd": c["cmd"][:n], "cursor": True}]))
            t += 1 / cps
        done = done + [{"cmd": c["cmd"]}]
        t += 0.12
        out = c["output"]
        per = min(0.035, 0.9 / max(1, len(out)))
        for n in range(1, len(out) + 1):
            steps.append((t, done + [{"out": l} for l in out[:n]]))
            t += per
        done = done + [{"out": l} for l in out]
        t += 0.3
    steps.append((t, done + [{"cmd": "", "cursor": True}]))
    return steps, t


# ----------------------------------------------------------------------------------------------- end card
def end_card_html():
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;height:100%;background:#f3f1ea;color:#1d1f1c;font-family:Georgia,"Times New Roman",serif}}
.wrap{{position:absolute;left:0;right:0;top:0;height:500px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}}
h1{{font-size:42px;margin:0 0 26px;font-weight:700}}
.row{{font-size:22px;margin:7px 0}}.lab{{color:#666a63;margin-right:10px}}
.url{{font-family:"Cascadia Mono",Consolas,monospace;font-size:20px;color:#0b6b4f}}
.src{{margin-top:28px;font-size:19px;color:#1d1f1c}}.note{{margin-top:8px;font-size:15px;color:#666a63}}
.rule{{width:120px;height:2px;background:#d6d3c8;margin:0 0 24px}}
</style></head><body><div class="wrap">
<h1>Price Is Not Revenue: the 9.4x Question</h1><div class="rule"></div>
<div class="row"><span class="lab">Code and data</span><span class="url">{html.escape(GH.replace('https://', ''))}</span></div>
<div class="row"><span class="lab">Live dashboard</span><span class="url">{html.escape(DASH.replace('https://', ''))}</span></div>
<div class="src">Source: Blockworks, DefiLlama, NEAR BigQuery.</div>
<div class="note">Research, not investment advice.</div>
</div></body></html>"""


# ----------------------------------------------------------------------------------------------- render
def wt(voice, i, word, nth=0):
    """Local scene time at which word `word` (nth occurrence) of line i starts."""
    hits = [w for w in voice[i]["words"] if core(w["w"])[1].lower() == word.lower()]
    return LEAD + hits[nth]["start"]


def prepare_github(page, url):
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2500)
    page.evaluate("document.fonts.ready.then(() => true)")
    left_js = """(() => { const e = document.querySelector('article.markdown-body') || document.querySelector('#LC1');
        return e ? e.getBoundingClientRect().left : 0; })()"""
    if page.evaluate(left_js) > 150:  # file tree is open: collapse it with GitHub's own button
        page.locator('[data-testid="collapse-file-tree-button"]').first.click()
        page.wait_for_timeout(800)
    if page.evaluate(left_js) > 150:
        raise RuntimeError(f"could not collapse GitHub's file tree on {url}")
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.mouse.move(2, VH - 2)
    page.wait_for_timeout(300)


def new_contexts(br):
    opts = dict(viewport={"width": VW, "height": VH}, color_scheme="light", locale="en-US", reduced_motion="no-preference")
    return br.new_context(device_scale_factor=DSF, **opts), br.new_context(device_scale_factor=HI_DSF, **opts)


def make_scene(k, ctx, ctx_hi, voice, scenes_t, cmd_caps):
    """Build scene k (0-based) on its own pages. Returns (scene, objects that took screenshots)."""
    D = [d for _, d in scenes_t]
    sticky = 100
    if k == 0:  # title and headline tiles (high-res capture, slow push-in)
        p = ctx_hi.new_page()
        p.goto(DASH, wait_until="networkidle", timeout=60000)
        p.wait_for_timeout(2500)
        img = rgb(p.screenshot(type="png", animations="disabled"))
        p.close()
        return ZoomScene(img, D[0], z_end=1.045, focus_y=0.25), []
    if k == 1:  # scorecard: eased scroll with pauses, ending on E3 when the voice reaches it
        p = ctx.new_page()
        p.goto(DASH, wait_until="networkidle", timeout=60000)
        p.wait_for_timeout(2500)
        head = top_of(p, "[...document.querySelectorAll('h2')].find(h => h.textContent.trim() === 'Verdict scorecard')")
        cards = p.evaluate("""[...document.querySelectorAll('.card')].filter(c => /^(H|E|F)\\d:/.test((c.querySelector('h3')||{}).textContent||''))
            .map(c => [c.querySelector('h3').textContent.slice(0, 3), c.getBoundingClientRect().top + scrollY])""")
        ctop = {name[:2]: y for name, y in cards}
        stops = [head - 24, ctop["H3"] - 18, ctop["H5"] - 18, ctop["E3"] - 18]
        t0, t_arr = 1.2, wt(voice, 1, "idea") + 0.35
        seg = (t_arr - t0) / (len(stops) - 1)
        keys = [(0, stops[0]), (t0, stops[0])]
        for j in range(1, len(stops)):
            a = t0 + (j - 1) * seg
            keys += [(a + 0.62 * seg, stops[j]), (a + seg, stops[j])]
        s = Shot(p, "scorecard")
        return ScrollScene(s, keys), [s]
    if k == 2:  # sensitivity table in scenarios_results.txt (GitHub highlights lines 33-45 from the URL)
        p = ctx.new_page()
        prepare_github(p, BLOB + "scenarios_results.txt#L33-L45")
        y_a = top_of(p, "document.querySelector('#LC24')") - sticky - 6
        y_b = top_of(p, "document.querySelector('#LC33')") - sticky - 10
        tm = wt(voice, 2, "covers") - 0.2
        s = Shot(p, "scenarios_results.txt")
        return ScrollScene(s, [(0, y_a), (tm, y_a), (tm + 1.3, y_b)]), [s]
    if k == 3:  # THESIS.md: My call, then What you would have to believe
        p = ctx.new_page()
        prepare_github(p, BLOB + "THESIS.md")
        y_a = top_of(p, "document.querySelector('article.markdown-body blockquote')") - sticky - 18
        y_b = top_of(p, "[...document.querySelectorAll('article.markdown-body h2')].find(h => h.textContent.trim().startsWith('What you would have to believe'))") - sticky - 14
        tm = wt(voice, 3, "and") - 0.15
        s = Shot(p, "THESIS.md")
        return ScrollScene(s, [(0, y_a), (tm, y_a), (tm + 1.6, y_b)]), [s]
    if k == 4:  # PREDICTIONS.md, then the terminal
        p = ctx.new_page()
        prepare_github(p, BLOB + "PREDICTIONS.md")
        y_a = top_of(p, "document.querySelector('article.markdown-body h1, article.markdown-body h2')") - sticky - 12
        y_b = top_of(p, "[...document.querySelectorAll('article.markdown-body p')].find(e => e.textContent.trim().startsWith('P1.'))") - sticky - 12
        tm = wt(voice, 4, "resolve") - 0.3
        s = Shot(p, "PREDICTIONS.md")
        pred = ScrollScene(s, [(0, y_a), (tm, y_a), (tm + 1.2, y_b)])
        tp = ctx.new_page()
        tp.set_content(TERMINAL_HTML)
        tp.wait_for_timeout(300)
        script, t_end = terminal_script(cmd_caps, None)
        ts = wt(voice, 4, "everything") - 0.3
        if t_end > D[4] - ts:
            print(f"note: terminal animation ({t_end:.2f}s) is longer than its slot ({D[4] - ts:.2f}s); it is cut at the scene end")
        term = TerminalScene(tp, script)
        term.name = "terminal"
        return SplitScene(pred, term, ts), [s, term]
    if k == 5:  # DATA_PROVENANCE.md
        p = ctx.new_page()
        prepare_github(p, BLOB + "DATA_PROVENANCE.md")
        y_a = top_of(p, "document.querySelector('article.markdown-body h1, article.markdown-body h2')") - sticky - 12
        y_b = top_of(p, "document.querySelector('article.markdown-body table')") - sticky - 14
        tm = wt(voice, 5, "cross-checked") - 0.2
        s = Shot(p, "DATA_PROVENANCE.md")
        return ScrollScene(s, [(0, y_a), (tm, y_a), (tm + 2.4, y_b)]), [s]
    if k == 6:  # end card
        p = ctx_hi.new_page()
        p.set_content(end_card_html())
        p.wait_for_timeout(300)
        img = rgb(p.screenshot(type="png"))
        p.close()
        return ZoomScene(img, D[6], z_end=1.03, focus_y=0.38), []
    raise ValueError(k)


RENDER_VERSION = "3"  # bump to force re-rendering every clip


def scene_frame_ranges(scenes_t, n_frames):
    S = [s for s, _ in scenes_t]
    idx = [max(k for k in range(len(S)) if S[k] <= n / FPS + 1e-9) for n in range(n_frames)]
    return [(idx.index(k), len(idx) - idx[::-1].index(k)) for k in range(len(S))]


def clip_key(k, voice, scenes_t, caps, cmd_caps, total):
    """Fingerprint of everything that affects a clip: timeline, words, captions, command output and the renderer code."""
    src = Path(__file__).read_text(encoding="utf-8")
    render_src = src.split("# " + "-" * 95 + " audio")[0]
    blob = json.dumps({"v": RENDER_VERSION, "k": k, "scenes": scenes_t, "total": total,
                       "words": [[(w["w"], w["start"], w["end"]) for w in v["words"]] for v in voice],
                       "caps": [(c["text"], c["start"], c["end"]) for c in caps], "cmd": cmd_caps}, sort_keys=True)
    return hashlib.sha256((blob + render_src).encode()).hexdigest()[:20]


def encoder(path):
    return subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-threads", "2", "-g", str(FPS * 2),
                             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                             "-f", "mp4", str(path)], stdin=subprocess.PIPE)


def render_clip(k, voice, scenes_t, caps, cap_imgs, cmd_caps, total, rng, out_path):
    """Render global frames rng[0]..rng[1]-1 (scene k, including its halves of the crossfades) to out_path.
    Opens only scenes k-1, k and k+1, streams each frame to ffmpeg, and keeps only the last screenshot per page."""
    from playwright.sync_api import sync_playwright
    S = [s for s, _ in scenes_t]
    s0, d0 = scenes_t[k]
    samples = {}
    for frac in (0.08, 0.35, 0.65, 0.95):
        samples[int((s0 + frac * d0) * FPS)] = f"scene{k + 1}_{int(frac * 100):02d}"
    if k:
        samples[rng[0]] = f"xfade_{k}_{k + 1}"
    for j, c in enumerate(caps):
        if c["scene"] == k:
            samples[int(((c["start"] + c["end"]) / 2) * FPS)] = f"cap{j + 1:02d}"
    sample_dir = BUILD / "frames"
    sample_dir.mkdir(exist_ok=True)
    for f in sample_dir.glob("*.jpg"):
        if rng[0] <= int(f.name[:5]) < rng[1]:
            f.unlink()
    tmp = out_path.with_name(out_path.stem + ".part.mp4")
    enc = encoder(tmp)
    stats, prev_small, prev_state, counts = [], None, None, {}
    t_start = time.time()
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            ctx, ctx_hi = new_contexts(br)
            built, objs = {}, []
            for j in (k - 1, k, k + 1):
                if 0 <= j < len(S):
                    built[j], o = make_scene(j, ctx, ctx_hi, voice, scenes_t, cmd_caps)
                    if j == k:
                        objs = o
            for n in range(*rng):
                t = n / FPS
                i = k
                img = built[i].frame(t - S[i])
                state = [built[i].state(t - S[i])]
                trans = False
                if i + 1 < len(S) and t > S[i + 1] - XF / 2:
                    al = smoother((t - (S[i + 1] - XF / 2)) / XF)
                    img = Image.blend(img, built[i + 1].frame(t - S[i + 1]), al)
                    trans = True
                elif i > 0 and t < S[i] + XF / 2:
                    al = smoother((t - (S[i] - XF / 2)) / XF)
                    img = Image.blend(built[i - 1].frame(t - S[i - 1]), img, al)
                    trans = True
                if isinstance(built[i], SplitScene) and abs((t - S[i]) - built[i].ts) <= XF / 2:
                    trans = True
                arr = np.array(img, dtype=np.uint8)
                cap_alpha = []
                for c, (crgb, ca, x, y, _, _) in zip(caps, cap_imgs):
                    if c["start"] <= t <= c["end"]:
                        a = smoother(min(1.0, (t - c["start"]) / 0.1, (c["end"] - t) / 0.1))
                        if a > 0:
                            h_, w_ = ca.shape
                            reg = arr[y:y + h_, x:x + w_].astype(np.float32)
                            k_ = (ca * a)[..., None]
                            arr[y:y + h_, x:x + w_] = np.clip(reg * (1 - k_) + crgb * k_ + 0.5, 0, 255).astype(np.uint8)
                        cap_alpha.append((c["text"], round(a, 3)))
                g = min(1.0, t / FADE_IN, (total - t) / FADE_OUT)
                if g < 1:
                    arr = np.clip(arr.astype(np.float32) * max(0.0, smoother(g)) + 0.5, 0, 255).astype(np.uint8)
                    trans = True
                enc.stdin.write(arr.tobytes())
                small = arr[::8, ::8].mean(axis=2)
                diff = 0.0 if prev_small is None else float(np.abs(small - prev_small).mean())
                prev_small = small
                moving = state != prev_state
                prev_state = state
                stats.append({"n": n, "t": round(t, 4), "scene": k + 1, "diff": round(diff, 4), "moving": moving,
                              "trans": trans, "caps": cap_alpha})
                if n in samples:
                    Image.fromarray(arr).resize((960, 540), Image.LANCZOS).save(sample_dir / f"{n:05d}_{samples[n]}.jpg", quality=90)
            for o in objs:
                counts[getattr(o, "name", "?")] = {"screenshots": o.shots, "scroll_errors": getattr(o, "scroll_errors", [])}
        finally:
            br.close()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"encode of scene {k + 1} failed")
    tmp.replace(out_path)
    return stats, {"scene": k + 1, "frames": rng[1] - rng[0], "render_s": round(time.time() - t_start, 1), "pages": counts}


def render_video(voice, scenes_t, caps, cmd_caps, total):
    """Render each scene to demo/build/clips/sceneN.mp4, skipping clips that are up to date, then concatenate."""
    clips = BUILD / "clips"
    clips.mkdir(exist_ok=True)
    n_frames = int(round(total * FPS))
    ranges = scene_frame_ranges(scenes_t, n_frames)
    cap_imgs = [render_caption(c["text"]) for c in caps]
    for c, (_, _, x, y, nl, tw) in zip(caps, cap_imgs):
        c["box"] = [int(x), int(y), int(nl), round(float(tw))]
    infos = []
    for k, rng in enumerate(ranges):
        key = clip_key(k, voice, scenes_t, caps, cmd_caps, total)
        clip, meta = clips / f"scene{k + 1}.mp4", clips / f"scene{k + 1}.json"
        stats_f = clips / f"scene{k + 1}_stats.json"
        if clip.exists() and stats_f.exists() and meta.exists() and json.loads(meta.read_text()).get("key") == key:
            print(f"  scene {k + 1}: up to date, skipped", flush=True)
            infos.append(json.loads(meta.read_text())["info"])
            continue
        print(f"  scene {k + 1}: rendering frames {rng[0]}-{rng[1] - 1}", flush=True)
        stats, info = render_clip(k, voice, scenes_t, caps, cap_imgs, cmd_caps, total, rng, clip)
        stats_f.write_text(json.dumps(stats))
        meta.write_text(json.dumps({"key": key, "info": info}))
        infos.append(info)
        print(f"  scene {k + 1}: done in {info['render_s']} s", flush=True)
    lst = clips / "concat.txt"
    lst.write_text("".join(f"file 'scene{k + 1}.mp4'\n" for k in range(len(ranges))))
    run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart",
         str(BUILD / "video.mp4")])
    stats = []
    for k in range(len(ranges)):
        stats += json.loads((clips / f"scene{k + 1}_stats.json").read_text())
    (BUILD / "frame_stats.json").write_text(json.dumps(stats))
    return {"frames": n_frames, "clips": infos}


# ----------------------------------------------------------------------------------------------- audio
def loudness(path):
    p = subprocess.run([FF, "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = p.stderr[p.stderr.rfind("Summary:"):]
    num = r"(-?[\d.]+|-inf)"
    I = float(re.search(r"I:\s+" + num + r" LUFS", s).group(1))
    lra = float(re.search(r"LRA:\s+" + num + r" LU", s).group(1))
    tp = float(re.search(r"Peak:\s+" + num + r" dBFS", s).group(1))
    return {"I_LUFS": I, "LRA_LU": lra, "true_peak_dBTP": tp}


def write_wav(path, x):
    wavfile.write(path, SR, x.astype(np.float32))


def build_audio(voice, scenes_t, total):
    n = int(round(total * SR))
    v = np.zeros(n)
    speech = np.zeros(n, dtype=bool)
    for line, (S, _) in zip(voice, scenes_t):
        sr, d = wavfile.read(line["wav"])
        d = d.astype(np.float64) / 32768.0
        a = int(round((S + LEAD) * SR))
        v[a:a + len(d)] += d[: max(0, n - a)]
        for w in line["words"]:
            speech[int((S + LEAD + w["start"]) * SR): int((S + LEAD + w["end"]) * SR)] = True
    write_wav(BUILD / "voice_raw.wav", np.stack([v, v], 1))
    m0 = loudness(BUILD / "voice_raw.wav")
    gain = 10 ** ((VOICE_LUFS - m0["I_LUFS"]) / 20)
    v *= gain
    write_wav(BUILD / "voice.wav", np.stack([v, v], 1))
    rep = {"voice": loudness(BUILD / "voice.wav"), "voice_gain_dB": round(20 * math.log10(gain), 2)}
    if rep["voice"]["true_peak_dBTP"] > -1.0:
        run([FF, "-y", "-v", "error", "-i", str(BUILD / "voice.wav"), "-af", "alimiter=limit=0.891:level=0:attack=3:release=60",
             "-c:a", "pcm_f32le", str(BUILD / "voice_lim.wav")])
        shutil.move(BUILD / "voice_lim.wav", BUILD / "voice.wav")
        rep["voice"] = loudness(BUILD / "voice.wav")
        rep["voice_limited"] = True
    music_target = rep["voice"]["I_LUFS"] - MUSIC_BELOW
    for ver in ("A", "B"):
        mus = music.make_music(ver, total)
        write_wav(BUILD / f"music_{ver}_raw.wav", mus)
        m = loudness(BUILD / f"music_{ver}_raw.wav")
        g = 10 ** ((music_target - m["I_LUFS"]) / 20)
        mus = mus * g
        write_wav(BUILD / f"music_{ver}.wav", mus)
        r = {"music_before_ducking": loudness(BUILD / f"music_{ver}.wav")}
        run([FF, "-y", "-v", "error", "-i", str(BUILD / f"music_{ver}.wav"), "-i", str(BUILD / "voice.wav"), "-filter_complex",
             "[0:a][1:a]sidechaincompress=threshold=0.03:ratio=4:attack=25:release=450:knee=3:makeup=1[d]",
             "-map", "[d]", "-c:a", "pcm_f32le", str(BUILD / f"music_{ver}_ducked.wav")])
        r["music_after_ducking"] = loudness(BUILD / f"music_{ver}_ducked.wav")
        _, du = wavfile.read(BUILD / f"music_{ver}_ducked.wav")
        du = du[:n, 0].astype(np.float64)
        un = mus[:len(du), 0]
        sp = speech[:len(du)]
        quiet = ~sp
        rms = lambda x: math.sqrt(float(np.mean(x ** 2)) + 1e-20)
        r["duck_depth_during_words_dB"] = round(20 * math.log10(rms(du[sp]) / rms(un[sp])), 2)
        r["duck_depth_between_words_dB"] = round(20 * math.log10(rms(du[quiet]) / rms(un[quiet])), 2)
        run([FF, "-y", "-v", "error", "-i", str(BUILD / "voice.wav"), "-i", str(BUILD / f"music_{ver}_ducked.wav"),
             "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0:duration=first[m]", "-map", "[m]",
             "-c:a", "pcm_f32le", str(BUILD / f"mix_{ver}.wav")])
        r["mix"] = loudness(BUILD / f"mix_{ver}.wav")
        if r["mix"]["true_peak_dBTP"] > -1.0:
            run([FF, "-y", "-v", "error", "-i", str(BUILD / f"mix_{ver}.wav"), "-af", "alimiter=limit=0.891:level=0:attack=3:release=60",
                 "-c:a", "pcm_f32le", str(BUILD / f"mix_{ver}_lim.wav")])
            shutil.move(BUILD / f"mix_{ver}_lim.wav", BUILD / f"mix_{ver}.wav")
            r["mix"] = loudness(BUILD / f"mix_{ver}.wav")
            r["mix_limited"] = True
        r["voice_minus_music_before_ducking_LU"] = round(rep["voice"]["I_LUFS"] - r["music_before_ducking"]["I_LUFS"], 1)
        r["voice_minus_music_after_ducking_LU"] = round(rep["voice"]["I_LUFS"] - r["music_after_ducking"]["I_LUFS"], 1)
        rep[ver] = r
    return rep


def mux():
    sources = {"A": BUILD / "mix_A.wav", "B": BUILD / "mix_B.wav", "nomusic": BUILD / "voice.wav"}
    for k, out in OUTPUTS.items():
        run([FF, "-y", "-v", "error", "-i", str(BUILD / "video.mp4"), "-i", str(sources[k]), "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-movflags", "+faststart", str(out)])


# ----------------------------------------------------------------------------------------------- checks
def probe_duration(path):
    p = subprocess.run([FF, "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def decoded_frame_check(path, stats):
    """Decode the encoded file frame by frame (small greyscale, one frame in memory at a time) and look for jumps."""
    w, h = 240, 135
    proc = subprocess.Popen([FF, "-v", "error", "-threads", "2", "-i", str(path), "-vf", f"scale={w}:{h},format=gray",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    d, prev = [], None
    while True:
        buf = proc.stdout.read(w * h)
        if len(buf) < w * h:
            break
        fr = np.frombuffer(buf, np.uint8).astype(np.float32)
        if prev is not None:
            d.append(float(np.abs(fr - prev).mean()))
        prev = fr
    if proc.wait() != 0:
        raise RuntimeError(f"decoding {path} failed")
    d = np.array(d)
    n_dec = len(d) + 1
    res = {"decoded_frames": n_dec, "expected_frames": len(stats)}

    def expected(k):
        return stats[k]["moving"] or stats[k]["trans"] or stats[k]["caps"] != stats[k - 1]["caps"]

    unexplained, spikes, static = [], [], []
    for k in range(1, min(n_dec, len(stats))):
        dk = d[k - 1]
        if not expected(k):
            static.append(dk)
            if dk > 0.35:
                unexplained.append((stats[k]["t"], round(float(dk), 3)))
        lo, hi = max(0, k - 4), min(len(d), k + 3)
        neigh = float(np.median(np.r_[d[lo:k - 1], d[k:hi]])) if hi - lo > 1 else 0.0
        if dk > 2.0 and dk > 3 * neigh + 0.5:
            spikes.append((stats[k]["t"], round(float(dk), 2), round(float(neigh), 2)))
    res["max_diff_static_frames"] = round(float(max(static or [0.0])), 3)
    res["unexplained_changes"] = unexplained[:20]
    res["n_unexplained_changes"] = len(unexplained)
    res["spikes"] = spikes[:20]
    res["n_spikes"] = len(spikes)
    res["max_diff_any_frame"] = round(float(d.max()), 2)
    res["max_diff_at_s"] = round(float((int(d.argmax()) + 1) / FPS), 3)
    return res


def caption_checks(caps):
    out = {"n": len(caps), "max_words": max(len(c["text"].split()) for c in caps), "issues": []}
    worst_early, worst_late = 0.0, 0.0
    for k, c in enumerate(caps):
        nw = len(c["text"].split())
        if nw > 10:
            out["issues"].append(f"caption {k + 1} has {nw} words")
        x, y, nl, tw = c["box"]
        if x < 0 or y < 0 or nl > 2 or tw > CAP_MAX_W:
            out["issues"].append(f"caption {k + 1} does not fit: {c['box']}")
        full_from, full_to = c["start"] + 0.1, c["end"] - 0.1
        for w, s, e in c["words"]:
            worst_late = max(worst_late, full_from - s)   # word starts before caption is fully visible
            worst_early = max(worst_early, e - full_to)   # word still being spoken after caption starts fading
        if k + 1 < len(caps) and c["end"] > caps[k + 1]["start"] + 1e-6:
            out["issues"].append(f"captions {k + 1} and {k + 2} overlap in time")
    out["max_word_before_caption_fully_visible_s"] = round(worst_late, 3)
    out["max_word_after_caption_fade_starts_s"] = round(worst_early, 3)
    return out


# ----------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-only", action="store_true", help="reuse demo/build/video.mp4 and timeline; redo music, mix, mux, checks")
    ap.add_argument("--recapture", action="store_true", help="run verify_data.py and the pull_bigquery.py dry run again for the terminal scene")
    args = ap.parse_args()
    BUILD.mkdir(exist_ok=True)
    lines = [l.strip() for l in (DEMO / "narration.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 7, "narration.txt must have 7 lines, one per scene"
    print("1/6 voice (edge-tts, one file per line)")
    voice = make_voice_lines(lines)
    scenes_t, S = [], 0.0
    for k, v in enumerate(voice):
        d = v["dur"] + PAD + (END_HOLD if k == len(voice) - 1 else 0)
        scenes_t.append((S, d))
        S += d
    total = S
    caps = build_captions(voice, scenes_t)
    timeline = {"scenes": [{"scene": k + 1, "start_s": round(s, 3), "dur_s": round(d, 3), "line_audio_s": round(voice[k]["dur"], 3)}
                           for k, (s, d) in enumerate(scenes_t)], "total_s": round(total, 3),
                "captions": [{k2: c[k2] for k2 in ("scene", "text", "start", "end", "w_start", "w_end")} for c in caps],
                "interpolated_word_times": {k + 1: v["interpolated"] for k, v in enumerate(voice) if v["interpolated"]}}
    (BUILD / "timeline.json").write_text(json.dumps(timeline, indent=1))
    for c in caps:
        print(f"   [{c['start']:6.2f}-{c['end']:6.2f}] {c['text']}")
    if args.audio_only:
        stats = json.loads((BUILD / "frame_stats.json").read_text())
        vinfo = json.loads((BUILD / "video_info.json").read_text())
        caps_saved = vinfo.pop("captions")
        for c, s in zip(caps, caps_saved):
            c["box"] = s["box"]
    else:
        print("2/6 running the two commands for the terminal scene (verify_data.py, pull_bigquery.py dry run)")
        cmd_caps = capture_commands(args.recapture)
        print("3/6 capturing live pages and rendering, one clip per scene (resumable)")
        vinfo = render_video(voice, scenes_t, caps, cmd_caps, total)
        vinfo["captions"] = [{"text": c["text"], "box": c["box"]} for c in caps]
        (BUILD / "video_info.json").write_text(json.dumps(vinfo, indent=1))
        vinfo.pop("captions")
        stats = json.loads((BUILD / "frame_stats.json").read_text())
    print("4/6 music, ducking and loudness (ffmpeg ebur128)")
    arep = build_audio(voice, scenes_t, total)
    print("5/6 muxing")
    mux()
    print("6/6 checks")
    files = {}
    for k, path in OUTPUTS.items():
        files[k] = {"file": path.name, "duration_s": round(probe_duration(path), 3), "size_MB": round(path.stat().st_size / 1e6, 2),
                    "final_loudness": loudness(path), "frame_check": decoded_frame_check(path, stats)}
    report = {"built": time.strftime("%Y-%m-%d %H:%M:%S"), "voice": VOICE, "rate": RATE, "fps": FPS, "size": f"{W}x{H}",
              "timeline": timeline["scenes"], "total_s": timeline["total_s"], "video": vinfo, "audio": arep,
              "captions": caption_checks(caps), "files": files}
    (BUILD / "report.json").write_text(json.dumps(report, indent=1))
    write_text_report(report, timeline)
    print((DEMO / "demo_report.txt").read_text())


def write_text_report(r, timeline):
    L = []
    L.append(f"Demo build report ({r['built']})")
    L.append(f"Voice {r['voice']} at rate {r['rate']}; {r['size']} at {r['fps']} fps")
    L.append("")
    L.append("Scenes (scene = line audio + 0.5 s; the end card also holds 1.5 s more):")
    for s in r["timeline"]:
        L.append(f"  scene {s['scene']}: starts {s['start_s']:6.2f} s, lasts {s['dur_s']:5.2f} s (line audio {s['line_audio_s']:.2f} s)")
    L.append(f"  total {r['total_s']:.2f} s")
    L.append("")
    a = r["audio"]
    L.append("Loudness (ffmpeg ebur128, integrated LUFS / true peak dBTP):")
    L.append(f"  voice track: {a['voice']['I_LUFS']} LUFS / {a['voice']['true_peak_dBTP']} dBTP")
    for v in ("A", "B"):
        m = a[v]
        L.append(f"  music {v}: before ducking {m['music_before_ducking']['I_LUFS']} LUFS ({m['voice_minus_music_before_ducking_LU']} LU below voice); "
                 f"after ducking {m['music_after_ducking']['I_LUFS']} LUFS ({m['voice_minus_music_after_ducking_LU']} LU below voice)")
        L.append(f"           ducking: {m['duck_depth_during_words_dB']} dB while words are spoken, {m['duck_depth_between_words_dB']} dB elsewhere")
        L.append(f"  mix {v}: {m['mix']['I_LUFS']} LUFS / {m['mix']['true_peak_dBTP']} dBTP")
    L.append("")
    L.append("Files:")
    for k, f in r["files"].items():
        fc = f["frame_check"]
        L.append(f"  {f['file']}: {f['duration_s']:.2f} s, {f['size_MB']} MB, audio {f['final_loudness']['I_LUFS']} LUFS / "
                 f"{f['final_loudness']['true_peak_dBTP']} dBTP; frames {fc['decoded_frames']} (expected {fc['expected_frames']}), "
                 f"unexplained changes {fc['n_unexplained_changes']}, spikes {fc['n_spikes']}")
    c = r["captions"]
    L.append("")
    L.append(f"Captions: {c['n']}, at most {c['max_words']} words, {CAP_FONT_PX} px; issues: {c['issues'] or 'none'}")
    L.append(f"  a word starts at most {c['max_word_before_caption_fully_visible_s']} s before its caption is fully visible; "
             f"a word ends at most {c['max_word_after_caption_fade_starts_s']} s after its caption starts fading")
    for cap in timeline["captions"]:
        L.append(f"  [{cap['start']:6.2f} - {cap['end']:6.2f}] {cap['text']}")
    L.append("")
    L.append("Clips (render time, screenshots per page, scroll position errors):")
    for c in r["video"].get("clips", []):
        L.append(f"  scene {c['scene']}: {c['frames']} frames, {c['render_s']} s; {json.dumps(c['pages'])}")
    for k, f in r["files"].items():
        fc = f["frame_check"]
        L.append(f"Frame check {f['file']}: max change on static frames {fc['max_diff_static_frames']}, "
                 f"largest change {fc['max_diff_any_frame']} at {fc['max_diff_at_s']} s; unexplained {fc['unexplained_changes'][:5]}; spikes {fc['spikes'][:5]}")
    (DEMO / "demo_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
