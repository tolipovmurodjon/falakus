"""Copy the data the static site needs into web/, as real files (no symlinks), so any static host can serve it.

    python tools/sync_web_data.py

data/cases/ -> web/cases/   (case-study JSON + images, written by the cases pipeline)
Run after the case files change and before deploying.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [(ROOT / "data" / "cases", ROOT / "web" / "cases")]

for src, dst in PAIRS:
    if dst.is_symlink():
        dst.unlink()
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    n = sum(1 for p in dst.rglob("*") if p.is_file())
    print(f"{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}: {n} files")
