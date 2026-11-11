# Flower Fever 🌸

Flower match-3 puzzles (1,000 levels) plus a garden to grow: plant **138 flower variants**\n(72 ground, 18 water, 24 hanging and 24 flowering trees), earn flower coins, buy\nhouses and garden visitors. Portrait Android game built from a web page with Capacitor.

## How the Android app is built

Everything runs on GitHub; nothing needs to be installed on a computer.

1. The base match-3 game is `www/index.html`. In the Android workflow, `scripts/apply-garden-v2.py`\n   injects `scripts/garden-v2-inline.js` and `scripts/garden-v2-styles.css` after the existing\n   gameplay-effects patches, preserving the original match-3 engine and earlier garden saves.\n   `www/native.js` connects it to Android: AdMob ads,
   Google Play Billing, notifications, the back button and (optionally) Firebase Analytics.
2. On every push to `main`, the **Build Android app** workflow (Actions tab) wraps the game with Capacitor,
   runs `scripts/android-setup.py` (portrait, fullscreen, AdMob app id, icons from `resources/app-icon.png`,
   version number) and builds the app.
3. **Actions → latest run → Artifacts → `flower-fever-android`**:
   - `flower-fever-debug-TEST-ADS.apk`: install on a phone for testing (always shows Google test ads)
   - `playstore-icon-512.png`: the Play Console icon
   - `flower-fever-release.aab`: for Google Play (only when the signing secrets are set).
     The signed AAB is also saved on the `play-upload` branch.

## Ads (AdMob)

Real ids are in **`www/ads-config.js`**. Banner under the board during levels, an interstitial after every
5 wins from level 20, and rewarded ads. Nothing forced is shown to "No ads" buyers.

## In-app products (Play Console → Monetize → In-app products)

| Product id | Type | Gives | Price |
|---|---|---|---|
| `starter30` | Consumable | 30 diamonds + 3 free lifelines (once) | $0.99 |
| `gems10` | Consumable | 10 diamonds | $0.99 |
| `gems25` | Consumable | 25 diamonds | $1.99 |
| `gems60` | Consumable | 60 diamonds | $3.99 |
| `noads100` | Non-consumable | No forced ads + 100 diamonds | $5.99 |
| `gems170` | Consumable | 170 diamonds | $9.99 |
| `gems400` | Consumable | 400 diamonds | $19.99 |

## Firebase (optional)

Put `google-services.json` (Android app `com.alxmobileapps.flowerfever`) in the repo root and push.
The build then adds Firebase Analytics automatically.

## Signed release for Google Play

Repository secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `KEYSTORE_BASE64` | the upload keystore (`.jks`), base64-encoded |
| `KEYSTORE_PASSWORD` | keystore password |
| `KEY_ALIAS` | `flowerfever` |
| `KEY_PASSWORD` | same as the keystore password |

App ID: `com.alxmobileapps.flowerfever`

## Garden V2 (in PR until merged)

- **83 planting positions:** eight beds × nine ground flowers, three ponds × two aquatic flowers, one flowering arch × two hanging flowers, three tree spaces.
- **New garden economy:** 100 flower coins and 5 water for new gardens; cheapest seeds start at 25 flower coins. Existing player balances are preserved.
- Houses and purchased visitors continue to use the original sprites and benefits; old plots are migrated once into `farm.gardenV2` while preserving the legacy save fields.
- Flower sprites and the new backdrop are embedded within `scripts/garden-v2-inline.js` so the game works offline without additional external asset requests.
- Pull-request builds are test-only. The signed AAB is written to `play-upload` only for pushes to `main`. No Play Console release is created by merging alone.
