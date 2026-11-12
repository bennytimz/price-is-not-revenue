# Demo video

A 1920x1080, 60 fps walkthrough of the live dashboard and this repository, about 71 seconds long. It is built entirely by `make_demo.py`.

```
pip install -r demo/requirements-demo.txt
python -m playwright install chromium
python demo/make_demo.py               # full build (needs internet: live pages and the edge-tts voice)
python demo/make_demo.py --audio-only  # redo music, mix and mux; keep the rendered picture
```

ffmpeg must be on PATH, or install it with `pip install imageio-ffmpeg`. The terminal scene runs `python verify_data.py` and `python pull_bigquery.py`; the second one is a BigQuery dry run (it needs Google Cloud credentials, processes nothing and bills nothing; the script never passes `--run`).

| File | What it is |
|---|---|
| `narration.txt` | The seven narration lines, one per scene. Every number was checked against `confirmatory_results.txt`, `scenarios_results.txt` and `extension_results.txt`. |
| `make_demo.py` | Voice (edge-tts, `en-US-AvaMultilingualNeural`, rate -5%, one file per line), timeline, Playwright capture, captions, mixing, checks |
| `music.py` | Two original lo-fi instrumentals at 90 BPM (kick, hi-hat, pad, bass), synthesised with numpy; no samples |
| `demo_report.txt` | Measured scene durations, loudness (ffmpeg ebur128), file sizes and frame checks from the committed build (2026-11-12); a rebuild overwrites it |
| `price-is-not-revenue-demo-A.mp4`, `-B.mp4`, `-nomusic.mp4` | The outputs (music version A, music version B, voice only): produced locally by the build, not committed (git-ignored) |

**What is real.** Every page is loaded live in Chromium (Playwright) and screenshotted frame by frame while the script scrolls it: the dashboard at https://bennytimz.github.io/price-is-not-revenue/dashboard.html and the files on GitHub. The highlighted lines in `scenarios_results.txt` use GitHub's own line-link highlighting (`#L33-L45`). The terminal window shows the real output of the two commands, captured when the video is built and replayed with sped-up typing. The end card is a plain title card. No number on screen is typed into the script.

**Timing.** Each line's audio is measured first; each scene lasts that long plus 0.5 s, and the end card holds 1.5 s longer. Scenes crossfade over 0.4 s. Captions (54 px, at most 10 words) follow the voice's word timings, and spoken numbers are shown in written form (for example "nine-point-four-x" as "9.4x").

**Sound.** The voice is normalised to -16 LUFS. The music is set 18 LU below the voice before ducking, then side-chain compressed by the voice. All levels are measured with ffmpeg's `ebur128` filter and written to `demo_report.txt`.
