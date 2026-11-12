#!/usr/bin/env python3
"""Inject the new Flower Fever garden into the existing match-3 game.

Run after the existing graphics/effects patches and before Capacitor sync.
Keeps the puzzle, native integrations, 20 original houses and animal art intact.
"""
from pathlib import Path

game = Path("www/index.html")
js = Path("scripts/garden-v2-inline.js").read_text(encoding="utf-8")
css = Path("scripts/garden-v2-styles.css").read_text(encoding="utf-8")

# Keep the painted soil visible and start progression at the foreground beds.
js = js.replace("return view+plantLayers(slots);", "return plantLayers(slots);")
js = js.replace("unlocked:{'bed-1':true}", "unlocked:{'bed-7':true}")
js = js.replace("g.unlocked['bed-'+(bi+1)]=true;", "g.unlocked[G2_GROUND_ORDER[bi].id]=true;")
js = js.replace("const key=G2_AREAS[bi].slots[j];", "const key=G2_GROUND_ORDER[bi].slots[j];")
anchor = "const G2_PLANT_BY_ID ="
progression = """const G2_GROUND_ORDER = [7,8,5,6,3,4,1,2].map(n=>G2_AREAS.find(a=>a.id==='bed-'+n));
G2_GROUND_ORDER.forEach((area,i)=>{
 area.name='Flower Bed '+(i+1);
 area.level=[1,2,4,6,8,10,13,16][i];
 area.price=[0,150,300,550,850,1300,2050,3100][i];
});
"""
if "const G2_GROUND_ORDER =" not in js:
    js = js.replace(anchor, progression + anchor, 1)


import re
empty_background = Path("scripts/garden-empty-background.txt").read_text().strip()
js = re.sub(r'const G2_BACKGROUND = "[^"]+";', lambda _: 'const G2_BACKGROUND = "data:image/webp;base64,' + empty_background + '";', js, count=1)
js = js.replace('<div class="g2legend"><span>🌿 8 beds</span><span>💧 3 ponds</span><span>🌸 138 breeds</span><span>🌳 3 trees</span></div>', '')
js = js.replace("root.querySelector('.g2legend').title=readyCount+' flowers ready to harvest';", "")

# Fit each sprite inside its actual painted soil cell.
geometry = """
G2_SLOTS.filter(s=>s.kind==='ground').forEach(s=>{
 const bed=Number(s.area.split('-')[1]), row=Number(s.id.match(/_R(\\d)/)[1])-1;
 const band=Math.floor((bed-1)/2);
 s.y=[[402,432,462],[540,583,625],[721,773,825],[949,1009,1069]][band][row];
 s.h=[25,34,42,48][band];
 s.x+=s.w*.1;s.w*=.8;s.anchor=[s.x+s.w/2,s.y+s.h];
});
"""
if "const G2_GROUND_ORDER =" in js:
    js = js.replace("const G2_GROUND_ORDER =", geometry + "const G2_GROUND_ORDER =", 1)
else:
    js = js.replace("const G2_PLANT_BY_ID =", geometry + "const G2_PLANT_BY_ID =", 1)
old_image = '<img class="g2flower ${state===\'ready\'?\'\':\'g2sprout\'}" alt="" loading="lazy" src="${src}" style="left:${slot.x/1024*100}%;top:${slot.y/1536*100}%;width:${slot.w/1024*100}%;height:${slot.h/1536*100}%;z-index:${Math.floor(slot.anchor[1])}">'
new_image = '<svg class="g2flower" viewBox="${state===\'sprout\'?\'0 0 98 70\':state===\'bud\'?\'0 0 122 110\':\'0 0 100 100\'}" style="left:${slot.x/1024*100}%;top:${slot.y/1536*100}%;width:${slot.w/1024*100}%;height:${slot.h/1536*100}%;z-index:${Math.floor(slot.anchor[1])}" aria-hidden="true"><image href="${src}" width="${state===\'ready\'?100:300}" height="${state===\'ready\'?100:state===\'sprout\'?242:255}" preserveAspectRatio="xMidYMid meet"/></svg>'
js = js.replace(old_image, new_image)
js = js.replace('<i class="g2thirdpond" aria-hidden="true"></i>', '<svg class="g2thirdpond" viewBox="0 1200 310 215" aria-hidden="true"><image href="${G2_BACKGROUND}" width="1024" height="1536"/></svg>')
css += "\n.garden2 .g2flower{overflow:hidden}.garden2 .g2thirdpond{left:70%;top:15%;width:22%;height:10%;border:0;background:none;box-shadow:none;transform:none;border-radius:0}\n"

src = game.read_text(encoding="utf-8")
marker = "/* ============ Home screen ============ */"
old_start = "f.coins = 150; f.water = 3;"
old_welcome = "Here are ${FC_SVG}<b>150</b> to start!"

# The garden never requests a banner, including any of its open panels.
banner_conditions = (
    "adsAllowed() && (!!gardenOpen || (!homeOpen && !mapOpen && booted && levelIdx >= 20))",
    "adsAllowed() && !homeOpen && !mapOpen && (booted || !!gardenOpen)",
    "adsAllowed() && !homeOpen && !mapOpen && !gardenOpen && booted",
)
new_banner = "adsAllowed() && !homeOpen && !mapOpen && !gardenOpen && booted && levelIdx >= 20"
if new_banner not in src:
    matches = [condition for condition in banner_conditions if condition in src]
    if len(matches) != 1 or src.count(matches[0]) != 1:
        raise SystemExit("Garden V2 patch aborted: missing or ambiguous banner visibility condition")
    src = src.replace(matches[0], new_banner, 1)

if 'const G2_BACKGROUND' in src:
    # Refresh installed previews as well as fresh builds from the base game.
    import re
    start = src.index("/* Flower Fever Garden 2 —")
    end = src.index(marker, start)
    src = src[:start] + js + "\n" + src[end:]
    src, count = re.subn(r'<style id="garden-v2-styles">.*?</style>',
                         lambda _: '<style id="garden-v2-styles">' + css + '</style>',
                         src, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Garden V2 patch aborted: missing installed styles")
    game.write_text(src, encoding="utf-8")
    print("Garden V2 artwork and banner policy refreshed.")
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

