# Flower Fever 🌸

Flower match-3 puzzles (1,000 levels) plus a garden to grow: plant 54 kinds of flowers, earn flower coins,
buy houses and garden visitors. Portrait Android game built from a web page with Capacitor.

## How the Android app is built

Everything runs on GitHub; nothing needs to be installed on a computer.

1. The game is `www/index.html` (one file). `www/native.js` connects it to Android: AdMob ads,
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

## Player ID and friends' gardens

`scripts/patch-social.py` (runs at build time) adds:

- a **Player ID** (`FF-XXXXXX`) and a nickname for every player (Profile and Home → Friends),
- **Friends**: type a friend's ID to look at their garden; visited gardens stay in the list,
- **Water gift**: water a friend's garden once a day; you get 💧+1 and +1 Garden XP (up to 5 a day), they get 💧+1 next time they play (up to 10 a day),
- **Coin gift**: send 100 of your own flower coins to a friend, once per friend a day (+2 Garden XP for you); a player receives up to 300 coins a day, extra gifts arrive the next day,
- **Share** buttons for a level win and for your garden (picture with your Player ID and the Google Play link).

It needs Firebase (`google-services.json`). In the Firebase console:

1. **Authentication → Sign-in method → Anonymous → Enable** (players who never sign in with Google still get a Player ID).
2. **Firestore → Rules**: paste the contents of `firestore.rules` and **Publish**. Without the new rules, profiles, water gifts and coin gifts are refused.

Public profiles hold only the nickname, flower picture, level, stars and garden layout (no email or real name).

## Signed release for Google Play

Repository secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `KEYSTORE_BASE64` | the upload keystore (`.jks`), base64-encoded |
| `KEYSTORE_PASSWORD` | keystore password |
| `KEY_ALIAS` | `flowerfever` |
| `KEY_PASSWORD` | same as the keystore password |

App ID: `com.alxmobileapps.flowerfever`
