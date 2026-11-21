import os
import sys

svg = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">'
    b'<rect width="32" height="32" fill="red"/></svg>'
)

try:
    import cairosvg

    out = cairosvg.svg2png(bytestring=svg, output_width=32, output_height=32)
    print("cairosvg OK, png bytes:", len(out))
except Exception as exc:  # noqa: BLE001
    print("cairosvg FAILED:", type(exc).__name__, exc)

try:
    import cairocffi

    print("cairocffi file:", cairocffi.__file__)
    print("cairocffi VERSION:", cairocffi.VERSION)
except Exception as exc:  # noqa: BLE001
    print("cairocffi import failed:", exc)

import ctypes.util

print("find_library('cairo-2'):", ctypes.util.find_library("cairo-2"))
for name in ("cairo-2", "cairo", "libcairo-2"):
    try:
        ctypes.CDLL(name)
        print("CDLL ok:", name)
    except OSError as exc:
        print("CDLL failed:", name, exc)

env = os.environ.get("PATH", "")
cairo_on_path = [
    p for p in env.split(os.pathsep) if p and os.path.exists(os.path.join(p, "libcairo-2.dll"))
]
print("dirs on PATH containing libcairo-2.dll:", cairo_on_path)
print("sys.prefix:", sys.prefix)
