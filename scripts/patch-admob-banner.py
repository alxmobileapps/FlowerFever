"""Center the native AdMob banner container on Android."""
from pathlib import Path

path = Path("node_modules/@capacitor-community/admob/android/src/main/java/com/getcapacitor/community/admob/banner/BannerExecutor.java")
source = path.read_text()
before = "mAdViewLayoutParams.gravity = Gravity.BOTTOM;"
after = "mAdViewLayoutParams.gravity = Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL;"
if source.count(before) == 1:
    path.write_text(source.replace(before, after))
elif source.count(after) != 1:
    raise RuntimeError("AdMob banner layout changed; check the bottom-center placement.")
