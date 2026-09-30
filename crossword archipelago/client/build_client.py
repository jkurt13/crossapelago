"""Rebuild ../index.html from index.template.html + demo.json.

Run from anywhere:  python client/build_client.py
"""
from pathlib import Path

here = Path(__file__).resolve().parent
template = (here / "index.template.html").read_text(encoding="utf-8")
demo = (here / "demo.json").read_text(encoding="utf-8").strip()
(here.parent / "index.html").write_text(template.replace("__DEMO__", demo), encoding="utf-8")
print("Wrote", here.parent / "index.html")
