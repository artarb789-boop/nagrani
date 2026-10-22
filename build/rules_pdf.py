# -*- coding: utf-8 -*-
"""Правила пробника в PDF для объекта Custom_PDF в TTS (листается стрелками)."""
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).parent.parent
md = (ROOT / "Правила_пробника.md").read_text(encoding="utf-8")
import re
md = re.sub(r"(?m)^(?![-*] |\d+\. |\s|$)(.+)\n(?=([-*] |\d+\. ))", r"\1\n\n", md)
body = markdown.markdown(md, extensions=["tables"])
css = """
@page{size:A5 landscape;margin:12mm 14mm}
body{font-family:'Inter','DejaVu Sans',sans-serif;font-size:11.5pt;line-height:1.4;color:#1d1b17}
h1{font-size:20pt;margin:0 0 6pt}
h2{font-size:15pt;margin:14pt 0 4pt;break-after:avoid;border-bottom:1px solid #ccc;padding-bottom:2pt}
h3{font-size:12.5pt;margin:10pt 0 3pt;break-after:avoid}
table{border-collapse:collapse;width:100%;margin:6pt 0;font-size:10.5pt}
tr{break-inside:avoid}
td,th{border:1px solid #bbb;padding:3pt 5pt;vertical-align:top;text-align:left}
th{background:#eee}
ul,ol{margin:3pt 0 3pt 16pt;padding:0}
li{margin:1.5pt 0}
p{margin:4pt 0}
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(); p.set_content(html)
    p.pdf(path=str(ROOT / "images" / "rules.pdf"), format="A5", landscape=True, print_background=True)
    b.close()
print("rules.pdf")
