"""Runs in GitHub Actions right after `npx cap add android`.
Makes the Android project game-ready: portrait, fullscreen, AdMob app id, app icons, notification icon, version number.
"""
import os, re, pathlib
from PIL import Image, ImageDraw

APP_ID = "com.alxmobileapps.flowerfever"
A = pathlib.Path("android/app/src/main")
RES = A / "res"

def edit(path, fn):
    p = pathlib.Path(path); s = p.read_text(); n = fn(s)
    if n == s: print("WARNING: no change in", path)
    p.write_text(n)

# 1) Portrait only + AdMob app id (read from www/ads-config.js)
ads_cfg = pathlib.Path("www/ads-config.js").read_text()
m = re.search(r"appId:\s*'([^']+)'", ads_cfg)
ADMOB_APP_ID = m.group(1) if m else "ca-app-pub-3940256099942544~3347511713"

def manifest(s):
    if "screenOrientation" not in s:
        s = s.replace('android:name=".MainActivity"',
                      'android:name=".MainActivity"\n            android:screenOrientation="portrait"', 1)
    if "gms.ads.APPLICATION_ID" not in s:
        s = re.sub(r"(<application\b[^>]*>)", lambda m: m.group(1) +
                   '\n        <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="'
                   + ADMOB_APP_ID + '"/>', s, count=1)
    for perm in ("android.permission.POST_NOTIFICATIONS", "com.android.vending.BILLING"):
        if perm not in s:
            s = s.replace("</manifest>", f'    <uses-permission android:name="{perm}"/>\n</manifest>', 1)
    return s
edit(A / "AndroidManifest.xml", manifest)
print("AdMob app id:", ADMOB_APP_ID)

# 2) Fullscreen theme (no status bar), draw under the camera cutout
def styles(s):
    extra = ('<item name="android:windowFullscreen">true</item>\n'
             '        <item name="android:windowLayoutInDisplayCutoutMode" tools:targetApi="p">shortEdges</item>\n        ')
    s = re.sub(r'(<style name="AppTheme.NoActionBar"[^>]*>\s*)', lambda m: m.group(1) + extra, s)
    s = re.sub(r'(<style name="AppTheme.NoActionBarLaunch"[^>]*>\s*)', lambda m: m.group(1) + extra, s)
    if 'xmlns:tools' not in s:
        s = s.replace('<resources>', '<resources xmlns:tools="http://schemas.android.com/tools">', 1)
    return s
edit(RES / "values/styles.xml", styles)

# 3) Immersive mode (hide the navigation bar too); the game keeps running audio only while visible
java = A / "java" / pathlib.Path(*APP_ID.split(".")) / "MainActivity.java"
java.write_text(f"""package {APP_ID};

import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {{
    @Override
    public void onResume() {{ super.onResume(); hideBars(); }}

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {{
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideBars();
    }}

    private void hideBars() {{
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        WindowInsetsControllerCompat c = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        c.hide(WindowInsetsCompat.Type.systemBars());
        c.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
    }}
}}
""")

# 4) Google Play requires targeting API level 36
vg = pathlib.Path("android/variables.gradle")
edit(vg, lambda t: re.sub(r"(targetSdkVersion\s*=\s*)\d+", r"\g<1>36", re.sub(r"(compileSdkVersion\s*=\s*)\d+", r"\g<1>36", t)))
edit(vg, lambda t: re.sub(r"(minSdkVersion\s*=\s*)\d+", r"\g<1>24", t))
gp = pathlib.Path("android/gradle.properties")
gp.write_text(gp.read_text().rstrip("\n") + "\nandroid.suppressUnsupportedCompileSdk=36\n")

# 5) Version from the GitHub run number
vc = os.environ.get("VERSION_CODE", "1")
edit("android/app/build.gradle", lambda s: re.sub(r'versionName "[^"]*"', f'versionName "1.0.{vc}"',
                                                  re.sub(r"versionCode \d+", f"versionCode {vc}", s)))

# 6) App icons from resources/app-icon.png (square artwork, 1024x1024)
art = Image.open("resources/app-icon.png").convert("RGBA")
BG = (0, 52, 46, 255)   # dark green behind the artwork on adaptive icons (matches the icon's edges)
dens = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
for d, m in dens.items():
    folder = RES / f"mipmap-{d}"; folder.mkdir(parents=True, exist_ok=True)
    a, l = int(108 * m), int(48 * m)
    fg = Image.new("RGBA", (a, a), (0, 0, 0, 0))
    inner = art.resize((int(a * 76 / 108),) * 2, Image.LANCZOS)
    off = (a - inner.width) // 2; fg.alpha_composite(inner, (off, off))
    fg.save(folder / "ic_launcher_foreground.png")
    Image.new("RGBA", (a, a), BG).save(folder / "ic_launcher_background.png")
    full = art.resize((l, l), Image.LANCZOS)
    full.convert("RGB").save(folder / "ic_launcher.png")
    mask = Image.new("L", (l * 4, l * 4), 0); ImageDraw.Draw(mask).ellipse((0, 0, l * 4 - 1, l * 4 - 1), fill=255)
    rnd = full.copy(); rnd.putalpha(mask.resize((l, l), Image.LANCZOS)); rnd.save(folder / "ic_launcher_round.png")
    # notification icon: white flower silhouette on transparent (Android tints it)
    dfold = RES / f"drawable-{d}"; dfold.mkdir(parents=True, exist_ok=True)
    n = int(24 * m); s4 = n * 4
    ic = Image.new("L", (s4, s4), 0); dr = ImageDraw.Draw(ic); c = s4 / 2; r = s4 * .2
    import math
    for k in range(5):
        ang = k * 2 * math.pi / 5 - math.pi / 2; x, y = c + math.cos(ang) * r, c + math.sin(ang) * r
        dr.ellipse((x - r * .95, y - r * .95, x + r * .95, y + r * .95), fill=255)
    dr.ellipse((c - r * .55, c - r * .55, c + r * .55, c + r * .55), fill=0)
    out = Image.new("RGBA", (n, n), (255, 255, 255, 0)); out.putalpha(ic.resize((n, n), Image.LANCZOS))
    out.save(dfold / "ic_stat_flower.png")

any_dpi = RES / "mipmap-anydpi-v26"; any_dpi.mkdir(parents=True, exist_ok=True)
xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
       '    <background android:drawable="@mipmap/ic_launcher_background"/>\n'
       '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
       '</adaptive-icon>\n')
for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
    (any_dpi / name).write_text(xml)
for p in RES.glob("drawable*/ic_launcher_foreground.xml"):
    p.unlink()

# splash: the app's cream background instead of the Capacitor logo
for p in RES.glob("drawable*/splash.png"):
    w, h = Image.open(p).size
    sp = Image.new("RGB", (w, h), (253, 248, 241))
    lg = art.resize((min(w, h) // 3,) * 2, Image.LANCZOS)
    sp.paste(lg, ((w - lg.width) // 2, (h - lg.height) // 2), lg)
    sp.save(p)

os.makedirs("dist", exist_ok=True)
art.resize((512, 512), Image.LANCZOS).save("dist/playstore-icon-512.png")
print("Android project patched: portrait, fullscreen, AdMob, icons, version", vc)
