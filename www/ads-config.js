/* =====================================================================
 * FLOWER FEVER — AdMob + Google Play settings
 * =====================================================================
 * appId          AdMob App ID (copied into the Android manifest by the build)
 * bannerId       Banner under the board (during levels only)
 * interstitialId Full-screen ad between levels (after every 5 wins, from level 20)
 * rewardedId     "Watch an ad" rewards (diamonds, lives, lifelines, x2 coins, +5 moves)
 * testing        false = real ads. The DEBUG test APK always switches to Google
 *                test ads, so you can play it on your own phone safely.
 *
 * Real Flower Fever AdMob ids (account ca-app-pub-2452250229562082).
 * ===================================================================== */
window.FLOWER_ADS = {
  appId: 'ca-app-pub-2452250229562082~6470928510',
  bannerId: 'ca-app-pub-2452250229562082/2148540129',
  interstitialId: 'ca-app-pub-2452250229562082/7867770663',
  rewardedId: 'ca-app-pub-2452250229562082/9807538292',
  testing: false
};

/* Google Play in-app products (create these exact ids in Play Console → Monetize → In-app products) */
window.FLOWER_PRODUCTS = {
  consumable: ['starter30', 'gems10', 'gems25', 'gems60', 'gems170', 'gems400'],
  nonConsumable: ['noads100']
};
