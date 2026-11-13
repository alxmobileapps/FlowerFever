"""Garden: the current look, plus the 138 plants and the economy of Garden V2 (PR #1).

- Same garden picture, house, 3 beds and visitors. Two ponds and a pergola are added under the
  front bed, and the two trees beside the house can be planted with flowering trees
  (drawn in front of the house so even the biggest house never covers them).
- Plants, prices, growing times, earnings, XP and Garden Levels come from www/garden-plants.js
  (copied from PR #1). Flowers already planted keep growing and sell as before.
- Garden XP only from picking flowers (rarer = more XP), watering (+1), buying (1 XP per 100 coins)
  and new puzzle levels (+1). Bloom now stays 1 diamond per hour. New gardens start with 100 coins and 5 water.
- Garden fits one screen: the garden banner ad is removed.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path
import re

path = Path("www/index.html")
src = path.read_text()
if "GARDEN_PLANTS_PATCH" in src:
    print("garden plants patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-garden-plants: expected {count} of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

# --- data file -------------------------------------------------------------------------------
rep('<script src="board-webgl.js"></script>', '<script src="board-webgl.js"></script>\n<script src="garden-plants.js"></script>')

# --- picture size: the garden picture is taller (ponds and pergola under the front bed) ---------
rep("const OV_W = 725, OV_H = 1024,", "const OV_W = 725, OV_H = window.GARDEN_OVERVIEW ? 1249 : 1024,")
rep("stage.style.backgroundImage = `url(${FARM_IMG.overview_nh})`;", "stage.style.backgroundImage = `url(${window.GARDEN_OVERVIEW || FARM_IMG.overview_nh})`;")

# --- plants ----------------------------------------------------------------------------------
rep("const SEED_IDS = Object.keys(SEEDS);", """const SEED_IDS = Object.keys(SEEDS);
// GARDEN_PLANTS_PATCH: the 138 Garden V2 plants (ground, water, hanging, tree). The first 54 flowers still grow and sell, but are no longer sold.
const NEW_SEED_IDS = (window.GARDEN_PLANTS || []).map(p => { SEEDS[p.id] = { n: p.name, base: p.type, t: p.type, cost: p.cost, min: p.minutes, gain: p.gain, xp: p.xp, lv: p.level, r: p.rarity }; return p.id; });
const brImg = k => (window.GARDEN_ART && window.GARDEN_ART[k]) || FARM_BR[k];
const seedsFor = kind => NEW_SEED_IDS.length ? NEW_SEED_IDS.filter(k => SEEDS[k].t === kind) : (kind === "ground" ? SEED_IDS : []);""")
# pictures of the new plants
garden_start = src.index("function showMyGarden(")
garden_end = src.index("/* ============ Home screen ============ */")
body = src[garden_start:garden_end]
body = re.sub(r"FARM_BR\[([^\]]+)\]", r"brImg(\1)", body)
src = src[:garden_start] + body + src[garden_end:]
rep("st === \"bud\" ? FARM_IMG.bud : FARM_BR[p.b]; }", "st === \"bud\" ? FARM_IMG.bud : brImg(p.b); }")

# --- economy (PR #1) -------------------------------------------------------------------------
rep('{ n: "Left bed", lv: 3, coins: 300,', '{ n: "Left bed", lv: 2, coins: 150,')
rep('{ n: "Right bed", lv: 6, coins: 800,', '{ n: "Right bed", lv: 4, coins: 300,')
rep("f.coins = 150; f.water = 3;", "f.coins = 100; f.water = 5;")
rep("<p>Here are ${FC_SVG}<b>150</b> to start!</p>", "<p>Here are ${FC_SVG}<b>100</b> and 💧<b>5</b> to start!</p>")
# XP: only when a flower is picked (the plant's own XP: rarer gives more); no XP for planting or blooming
rep("const sellXP = sd => Math.ceil(sd.xp / 2);   // selling gives half of the bloom XP",
    "const sellXP = sd => sd.t ? sd.xp : ({ Common: 1, Uncommon: 2, Rare: 4, Epic: 5, Legendary: 7 }[sd.r] || 1);   // picking a flower: rarer gives more XP")
rep("function claimBlooms() {", "function claimBlooms() { return;")
rep("persist(); sheet.hidden = true; sfx(\"dirt\"); track(\"garden_plant\", { flower: k }); render(); gainXP(PLANT_XP[sd.r] || 1);",
    "persist(); sheet.hidden = true; sfx(\"dirt\"); track(\"garden_plant\", { flower: k }); render();")
rep("<b>🌱+${PLANT_XP[sd.r] || 1} · 🌸+${sd.xp} · 🪙+${sellXP(sd)}</b>", "<b>+${sellXP(sd)} when picked</b>")
rep("<ul class=\"fxplist\"><li>🌱 Plant seeds</li><li>💧 Water your plants</li><li>🌸 Let flowers bloom</li><li>🪙 Sell flowers</li><li>🛍 Buy houses, garden visitors and beds</li><li>🧩 Win new puzzle levels</li></ul>",
    "<ul class=\"fxplist\"><li>🌸 Pick flowers in bloom (rarer flowers give more)</li><li>💧 Water your plants</li><li>🛍 Buy houses, garden visitors, beds and ponds</li><li>🧩 Win new puzzle levels</li></ul>")
rep("Higher levels unlock new seeds, flower beds and grander houses.", "Higher levels unlock new plants, beds, ponds, the pergola, flowering trees and grander houses.")

# --- ponds, pergola and the two trees ----------------------------------------------------------
xareas = """
// ponds and pergola under the front bed, flowering trees beside the house (pixel boxes in the garden picture)
const XAREAS = {
  "pond-1": { n: "Left pond", kind: "water", lv: 4, coins: 350, cells: [[52, 1050, 124, 1106], [96, 1056, 168, 1112]], box: [4, 1046, 168, 1126] },
  "pond-2": { n: "Right pond", kind: "water", lv: 6, coins: 650, cells: [[541, 1050, 613, 1106], [585, 1056, 657, 1112]], box: [544, 1046, 712, 1126] },
  arch: { n: "Pergola", kind: "hanging", lv: 7, coins: 950, cells: [[230, 1010, 306, 1104], [408, 1010, 484, 1104]], box: [214, 1000, 512, 1112] },
  "tree-left": { n: "Left tree", kind: "tree", lv: 10, coins: 1400, cells: [[-4, 168, 150, 332]], box: [0, 60, 150, 336] },
  "tree-right": { n: "Right tree", kind: "tree", lv: 12, coins: 1800, cells: [[576, 168, 730, 332]], box: [576, 60, 725, 336] }
};
Object.values(XAREAS).forEach(a => { a.cells = a.cells.map(r => pct(r, OV_W, OV_H)); a.box = pct(a.box, OV_W, OV_H); });
const XAREA_ON = () => NEW_SEED_IDS.length > 0 && !!window.GARDEN_OVERVIEW;
"""
rep("const HOUSE_BOX = pct(", xareas + "const HOUSE_BOX = pct(")
rep("""    if (s.types) { s.plots.forEach((p, j) => { if (p && !p.b) p.b = s.types[j] + "0"; }); delete s.types; }   /* older saves: one fixed flower per plot */ });
  return f;""", """    if (s.types) { s.plots.forEach((p, j) => { if (p && !p.b) p.b = s.types[j] + "0"; }); delete s.types; }   /* older saves: one fixed flower per plot */ });
  f.areas = f.areas || {};
  Object.keys(XAREAS).forEach(k => { const s = f.areas[k] || (f.areas[k] = { open: 0 }); if (!s.plots) s.plots = Array(XAREAS[k].cells.length).fill(null); });
  return f;""")

# which plots the plant menus work on: a bed (view) or a pond / pergola / tree (area)
rep("let view = -1, moveFrom = null, moving = false, alive = true;",
    "let view = -1, moveFrom = null, moving = false, alive = true, area = null;\n  const holder = () => area ? f.areas[area] : f.beds[view];")
rep("const s = f.beds[view], p = s.plots[i], st = plotState(p), sd = p && SEEDS[p.b];", "const s = holder(), p = s.plots[i], st = plotState(p), sd = p && SEEDS[p.b];")
rep("const s = f.beds[view], p = s.plots[i], sd = SEEDS[p.b];", "const s = holder(), p = s.plots[i], sd = SEEDS[p.b];")
rep("const s = f.beds[view], sd = SEEDS[k];", "const s = holder(), sd = SEEDS[k];")
# moving is only between bed plots
rep("card.querySelectorAll(\"[data-x]\").forEach(b => b.onclick = () => { sheet.hidden = true; }); wire && wire(card); }",
    "card.querySelectorAll(\"[data-x]\").forEach(b => b.onclick = () => { sheet.hidden = true; }); wire && wire(card); if (area) { const m = card.querySelector(\"#sMove\"); if (m) m.hidden = true; } }")
rep("function openBed(bi) {\n    const b = BEDS[bi], s = f.beds[bi];", "function openBed(bi) {\n    area = null;\n    const b = BEDS[bi], s = f.beds[bi];")
# plant picker: only the plants for that place
rep("<div class=\"fseeds\">${SEED_IDS.map(k => {", "<div class=\"fseeds\">${seedsFor(area ? XAREAS[area].kind : \"ground\").map(k => {")
rep("const nb = BEDS.find(b => b.lv === L.lv), nn = SEED_IDS.filter(", "const nb = [...BEDS, ...(XAREA_ON() ? Object.values(XAREAS) : [])].filter(b => b.lv === L.lv), nn = (NEW_SEED_IDS.length ? NEW_SEED_IDS : SEED_IDS).filter(")
rep("${nn.length ? `<p>🌱 New seeds: <b>${nn.join(\", \")}</b></p>` : \"\"}", "${nn.length ? `<p>🌱 New plants: <b>${nn.slice(0, 6).join(\", \")}</b>${nn.length > 6 ? ` and ${nn.length - 6} more` : \"\"}</p>` : \"\"}")
rep("${nb ? `<p>🔓 You can now open the <b>${nb.n}</b>.</p>` : \"\"}", "${nb.length ? `<p>🔓 You can now open the <b>${nb.map(b => b.n).join(\"</b> and the <b>\")}</b>.</p>` : \"\"}")

# overview: draw the area plants and their tap areas
rep("""          <button class="fbedbtn" data-b="${bi}" aria-label="${b.n}" style="left:${b.box.l - 1}%;top:${b.box.t - 1}%;width:${b.box.w + 2}%;height:${b.box.h + 2}%">${f.beds[bi].open ? "" : `<span class="flock">🔒 ${b.n}<br><small>Garden Level ${b.lv} · ${FC_SVG}${b.coins}</small></span>`}</button>`).join("");""",
    """          <button class="fbedbtn" data-b="${bi}" aria-label="${b.n}" style="left:${b.box.l - 1}%;top:${b.box.t - 1}%;width:${b.box.w + 2}%;height:${b.box.h + 2}%">${f.beds[bi].open ? "" : `<span class="flock">🔒 ${b.n}<br><small>Garden Level ${b.lv} · ${FC_SVG}${b.coins}</small></span>`}</button>`).join("") + xareasHTML();""")
rep("      stage.querySelectorAll(\".fbedbtn\").forEach(b => b.onclick = () => openBed(+b.dataset.b));",
    "      stage.querySelectorAll(\".fbedbtn\").forEach(b => b.onclick = () => openBed(+b.dataset.b));\n      stage.querySelectorAll(\".fareabtn\").forEach(b => b.onclick = () => openArea(b.dataset.a));")
area_code = """
  function xareasHTML() {
    if (!XAREA_ON()) return "";
    return Object.entries(XAREAS).map(([k, a]) => { const s = f.areas[k];
      const plants = s.open ? a.cells.map((c, i) => { const p = s.plots[i], st = plotState(p); return st === "empty" ? "" :
        `<img class="fxpl ${st} k${a.kind}" alt="" src="${plotImg(p, st)}" style="left:${c.l}%;top:${c.t}%;width:${c.w}%;height:${c.h}%">`; }).join("") : "";
      const rdy = s.open ? s.plots.filter(p => plotState(p) === "ready").length : 0;
      return plants + `<button class="fareabtn k${a.kind}" data-a="${k}" aria-label="${a.n}${s.open ? "" : ", locked"}" style="left:${a.box.l}%;top:${a.box.t}%;width:${a.box.w}%;height:${a.box.h}%">${s.open ? (rdy ? `<span class="fxready">🌸</span>` : "") : `<span class="flock fxlock">🔒 Lv ${a.lv}</span>`}</button>`;
    }).join("");
  }
  function areaSig() { return XAREA_ON() ? Object.keys(XAREAS).map(k => f.areas[k].plots.map(p => plotState(p)).join()).join("|") : ""; }
  function openArea(k) {
    const a = XAREAS[k], s = f.areas[k]; if (!a) return;
    if (!s.open) {
      const L = farmLevel(f.xp), okLv = L.lv >= a.lv, okC = f.coins >= a.coins, what = a.kind === "water" ? "water flowers" : a.kind === "hanging" ? "hanging plants" : "a flowering tree";
      sheetShow(`<h3>🔒 ${a.n}</h3><p>Grow ${what} here.</p><ul class="fneed"><li class="${okLv ? "ok" : ""}">${okLv ? "✓" : "✗"} Garden Level ${a.lv} <small>(you are Level ${L.lv})</small></li><li class="${okC ? "ok" : ""}">${okC ? "✓" : "✗"} ${FC_SVG}${a.coins} <small>(you have ${f.coins})</small></li></ul>
        <div class="btns">${okLv && okC ? `<button class="btn" id="sOpen">Open for ${FC_SVG}${a.coins}</button>` : ""}<button class="btn alt" data-x>${okLv && okC ? "Not now" : "OK"}</button></div>`,
        c => { const o = c.querySelector("#sOpen"); if (o) o.onclick = () => { f.coins -= a.coins; s.open = 1; persist(); sheet.hidden = true; sfx("create"); track("garden_area_open", { area: k }); gainXP(buyXP(a.coins)); render(); }; });
      return;
    }
    if (s.plots.length === 1) { area = k; sfx("pick"); tapPlot(0, stage.querySelector(`.fareabtn[data-a="${k}"]`)); return; }
    area = k; sfx("pick");
    sheetShow(`<h3>${a.n}</h3><div class="fxslots">${s.plots.map((p, i) => { const st = plotState(p), sd = p && SEEDS[p.b];
        return `<button class="fxslot ${st}" data-i="${i}">${p ? `<img alt="" src="${plotImg(p, st)}"><b>${sd.n}</b><small>${st === "ready" ? "🌸 Ready to pick" : "⏳ " + fmtLeft(p.at + p.ms - Date.now())}</small>` : `<span class="fxplus">＋</span><b>Plant</b>`}</button>`; }).join("")}</div>
      <div class="btns"><button class="btn alt" data-x>Close</button></div>`,
      c => c.querySelectorAll(".fxslot").forEach(b => b.onclick = () => tapPlot(+b.dataset.i, b)));
  }
"""
rep("  function sheetShow(html, wire) {", area_code + "  function sheetShow(html, wire) {")
# the picture redraws when a pond / pergola / tree plant changes stage
rep("    if (changed && !moving) render();\n  }, 1000);", "    const sig = areaSig(); if (sig !== lastAreaSig) { lastAreaSig = sig; changed = true; }\n    if (changed && !moving) render();\n  }, 1000);\n  let lastAreaSig = areaSig();")

css = """
.farm .fxpl{position:absolute;object-fit:contain;object-position:50% 100%;pointer-events:none;z-index:2;filter:drop-shadow(0 2px 2px rgba(40,20,0,.25))}
.farm .fxpl.sprout{transform:scale(.8);transform-origin:50% 100%}
.farm .fxpl.ktree.sprout{transform:scale(.45)}.farm .fxpl.ktree.bud{transform:scale(.65)}
.farm .fxpl.ready{transform-origin:50% 100%;animation:fsway 3.2s ease-in-out infinite}
.farm .fareabtn{position:absolute;border:0;background:none;cursor:pointer;padding:0;border-radius:14px;z-index:4}
.farm .fareabtn:focus-visible{outline:3px solid #fff}
.farm .fareabtn .fxlock{font-size:11px;padding:4px 7px}.farm .fareabtn.ktree .fxlock{top:62%}
.farm .fxready{position:absolute;right:4%;top:4%;font-size:18px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))}
.farm .fxslots{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}
.farm .fxslot{border:0;border-radius:16px;background:#fff6ea;box-shadow:0 0 0 2px #f0d9b8;padding:10px 6px;display:flex;flex-direction:column;align-items:center;gap:3px;font:800 14px/1.2 var(--display);color:#5a3a20;cursor:pointer}
.farm .fxslot img{width:72px;height:72px;object-fit:contain}.farm .fxslot small{font:700 12px/1.2 var(--body);color:#8a6a50}
.farm .fxslot .fxplus{font-size:40px;line-height:72px;height:72px;color:#e8467e}
.farm .fad{display:none!important}.farm .fad ~ .fsheet{padding-bottom:12px!important}
"""
rep(".farm .fbedbtn{z-index:4}", ".farm .fbedbtn{z-index:4}" + css)

# no banner in the garden, so it fits one screen
rep("const want = adsAllowed() && (!!gardenOpen || (!homeOpen && !mapOpen && booted && levelIdx >= 20));",
    "const want = adsAllowed() && !gardenOpen && !homeOpen && !mapOpen && booted && levelIdx >= 20;")

path.write_text(src)
print("garden plants patch applied")
