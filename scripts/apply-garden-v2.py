#!/usr/bin/env python3
"""Inject the new Flower Fever garden into the existing match-3 game.

Run after the existing graphics/effects patches and before Capacitor sync.
Keeps the puzzle, native integrations, 20 original houses and animal art intact.
"""
from pathlib import Path

game = Path("www/index.html")
js = Path("scripts/garden-v2-inline.js").read_text(encoding="utf-8")
css = Path("scripts/garden-v2-styles.css").read_text(encoding="utf-8")
src = game.read_text(encoding="utf-8")
marker = "/* ============ Home screen ============ */"
old_start = "f.coins = 150; f.water = 3;"
old_welcome = "Here are ${FC_SVG}<b>150</b> to start!"

if 'const G2_BACKGROUND' in src:
    print("Garden V2 already installed; skipping.")
    raise SystemExit(0)

for token in ("</head>", marker, old_start, old_welcome):
    if token not in src:
        raise SystemExit(f"Garden V2 patch aborted: missing anchor {token!r}")

assert "const G2_BACKGROUND" in js and "function showMyGarden" in js
assert "#gardenView.garden2" in css
src = src.replace(old_start, "f.coins = 100; f.water = 5;", 1)
src = src.replace(old_welcome, "Here are ${FC_SVG}<b>100</b> and 💧<b>5</b> to start!", 1)
src = src.replace("</head>", '<style id="garden-v2-styles">' + css + "</style></head>", 1)
src = src.replace(marker, js + "\n" + marker, 1)
game.write_text(src, encoding="utf-8")
print(f"Garden V2 installed: {len(src):,} characters (138 breeds, 83 plots).")
