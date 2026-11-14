"""30 s demo video from real app screenshots (docs/video/shots/s1..s7.jpg) with burned-in captions. Storyboard: docs/project/video-storyboard.md.
Every caption number is printed by the app on the same screen. Output: docs/video/falakus-30s.mp4 (1920x1080, H.264).
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "docs/video"
CAP = [
    "The Fergana valley drinks from one reservoir: Andijan.",
    "24 Sep 2026: the camera saw only cloud.\nNASA-ISRO's NISAR radar still saw the lake.",
    "Pass after pass, through cloud: 50.5 km² of open water on 14 Jul...",
    "...19.3 km² on 6 Oct. Checked against every clear photo: r = 0.83.",
    "The water becomes crops: 12.8 % of this 30 x 30 km box
lost its plant echo by late October, mostly harvest.",
    "Where the rivers end: 1,598 km² of sea in this box in 1997,\nabout 1 km² in 2026.",
    "Winter forecast: about 23 -> 29 km² by February (80 % band ±3.5 to ±6).
Falakus · open source · NISAR radar for any place on Earth.",
]
DUR, FADE = 4.6, 0.45
FONT = "C\:/Windows/Fonts/arialbd.ttf"
clips = []
for i, cap in enumerate(CAP, 1):
    t = V / f"cap{i}.txt"; t.write_text(cap, encoding="utf-8")
    out = V / f"c{i}.mp4"
    vf = (f"scale=1920:-2,pad=1920:1080:0:0:color=0xF6F3ED,"
          f"drawbox=x=0:y=842:w=1920:h=4:color=0x17515F:t=fill,"
          f"drawtext=fontfile='{FONT}':textfile='{t.as_posix().replace(':', chr(92) + ':')}':expansion=none:fontsize=44:fontcolor=0x14120D:line_spacing=2:x=(w-text_w)/2:y=842+(238-text_h)/2,"
          f"fade=t=in:st=0:d=0.3,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(DUR), "-i", str(V / f"shots/s{i}.jpg"), "-vf", vf, "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], check=True)
    clips.append(out)
inputs = sum([["-i", str(c)] for c in clips], [])
f, last, off = [], "[0:v]", DUR - FADE
for k in range(1, len(clips)):
    lab = f"[v{k}]"; f.append(f"{last}[{k}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}{lab}"); last = lab; off += DUR - FADE
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(f), "-map", last, "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(V / "falakus-30s.mp4")], check=True)
for c in clips:
    c.unlink()
print("ok", V / "falakus-30s.mp4")
