"""Re-bake the 24 Sep 2026 'cloudy day' photo from raw Sentinel-2 reflectance (B04, B03, B02) with a high ceiling
(0-14000) so cloud tops and shadows keep their texture (the 'visual' product clips cloud to flat white).
Writes data/waterroad/photo_andijan_cloudy.jpg.  Usage: python tools/bake_cloud_photo.py
"""
import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import water_road as wr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
b = [73.02795, 40.68392, 73.24205, 40.84608]
it = wr.stac({"collections": ["sentinel-2-l2a"], "bbox": b, "limit": 10, "datetime": "2026-09-24T00:00:00Z/2026-09-24T23:59:59Z"})
x = max(it, key=lambda x: x["properties"]["datetime"])
u = (f"https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/{b[0]},{b[1]},{b[2]},{b[3]}.png?collection=sentinel-2-l2a&item={x['id']}"
     "&assets=B04&assets=B03&assets=B02&rescale=0,14000&nodata=0&max_size=2048")
im = Image.open(io.BytesIO(urllib.request.urlopen(u, timeout=180).read())).convert("RGB")
im.save(ROOT / "data/waterroad/photo_andijan_cloudy.jpg", quality=86, optimize=True, progressive=True)
print("ok", x["id"], im.size)
