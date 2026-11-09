/* Flower Fever — Android bridges.
 * The game calls these when they exist (in the web preview they don't, and the game uses its own stand-ins):
 *   window.FlowerFeverAds        showBanner / hideBanner / showInterstitial() / showRewarded(kind) → true when the reward is earned
 *   window.FlowerFeverStore      buy(id) → true when paid · restore() → owned ids · prices { id: "₱49.00" }
 *   window.FlowerFeverNotify     schedule([{ id, title, body, at }]) · cancel(ids)
 *   window.FlowerFeverAnalytics  logEvent(name, params)   (Firebase, only when google-services.json was added)
 */
(function () {
  const C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const P = n => (C.Plugins && C.Plugins[n]) || (C.registerPlugin && C.registerPlugin(n));
  const cfg = window.FLOWER_ADS || {};
  const log = (...a) => { try { console.log('[FF]', ...a); } catch (e) {} };

  /* ---------- Ads (AdMob) ---------- */
  const AdMob = P('AdMob');
  if (AdMob) {
    const test = !!cfg.testing;
    let ready = (async () => {
      try {
        await AdMob.initialize({ initializeForTesting: test });
        try {
          const info = await AdMob.requestConsentInfo();
          if (info && info.isConsentFormAvailable && info.status === 'REQUIRED') await AdMob.showConsentForm();
        } catch (e) { log('consent', e); }
      } catch (e) { log('admob init', e); }
    })();

    // the web page keeps a 50px strip under the board for the banner; in the app the real banner sits there
    const st = document.createElement('style');
    st.textContent = '#adBanner{background:none!important;color:transparent!important;border:0!important;box-shadow:none!important}#adBanner *{visibility:hidden!important}';
    document.head.appendChild(st);

    let bannerShown = false, bannerWanted = false;
    const banner = {
      async show() {
        bannerWanted = true; await ready; if (!bannerWanted) return;
        try {
          if (bannerShown) await AdMob.resumeBanner();
          else { await AdMob.showBanner({ adId: cfg.bannerId, adSize: 'BANNER', position: 'BOTTOM_CENTER', margin: 0, isTesting: test }); bannerShown = true; }
        } catch (e) { log('banner', e); }
      },
      async hide() { bannerWanted = false; await ready; try { if (bannerShown) await AdMob.hideBanner(); } catch (e) {} }
    };

    // full-screen ads are loaded ahead of time so they open instantly
    let interReady = false, rewardReady = false;
    const loadInter = async () => { await ready; try { await AdMob.prepareInterstitial({ adId: cfg.interstitialId, isTesting: test }); interReady = true; } catch (e) { interReady = false; setTimeout(loadInter, 60000); } };
    const loadReward = async () => { await ready; try { await AdMob.prepareRewardVideoAd({ adId: cfg.rewardedId, isTesting: test }); rewardReady = true; } catch (e) { rewardReady = false; setTimeout(loadReward, 60000); } };
    loadInter(); loadReward();

    const once = (events, ms) => new Promise(res => {
      const hs = []; let done = false;
      const fin = v => { if (done) return; done = true; hs.forEach(h => { try { h.remove(); } catch (e) {} }); res(v); };
      events.forEach(([ev, v]) => { Promise.resolve(AdMob.addListener(ev, () => fin(v))).then(h => hs.push(h)); });
      if (ms) setTimeout(() => fin('timeout'), ms);
    });

    window.FlowerFeverAds = {
      showBanner: () => banner.show(),
      hideBanner: () => banner.hide(),
      async showInterstitial() {
        if (!interReady) { loadInter(); return; }
        interReady = false;
        const closed = once([['interstitialAdDismissed', 1], ['interstitialAdFailedToShow', 0]], 120000);
        quiet(true); try { await AdMob.showInterstitial(); await closed; } catch (e) { log('inter', e); } quiet(false);
        loadInter();
      },
      async showRewarded(kind) {
        if (!rewardReady) {
          await loadReward();
          if (!rewardReady) { alertNoAd(); return false; }
        }
        rewardReady = false;
        let earned = false;
        const rew = once([['onRewardedVideoAdReward', 1]]); rew.then(v => { if (v === 1) earned = true; });
        const closed = once([['onRewardedVideoAdDismissed', 1], ['onRewardedVideoAdFailedToShow', 0]], 180000);
        quiet(true); try { const r = await AdMob.showRewardVideoAd(); if (r) earned = true; await closed; } catch (e) { log('reward', e); } quiet(false);
        loadReward();
        return earned;
      }
    };
  }
  function quiet(on) { try { const A = window.FlowerFeverAudio; if (A) on ? A.pause() : A.resume(); } catch (e) {} }
  function alertNoAd() {
    try {
      const d = document.createElement('div');
      d.textContent = 'No ad is ready right now. Please try again in a minute.';
      d.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);z-index:99;background:#5a2e44;color:#fff;padding:12px 16px;border-radius:14px;font:700 15px/1.3 Nunito,sans-serif;max-width:80%;text-align:center';
      document.body.appendChild(d); setTimeout(() => d.remove(), 3500);
    } catch (e) {}
  }

  /* ---------- Google Play Billing (cordova-plugin-purchase) ---------- */
  const prods = window.FLOWER_PRODUCTS || { consumable: [], nonConsumable: [] };
  const storeApi = { prices: {} };
  window.FlowerFeverStore = storeApi;
  document.addEventListener('deviceready', () => {
    const Cdv = window.CdvPurchase; if (!Cdv) { log('no billing plugin'); return; }
    const { store, ProductType, Platform } = Cdv;
    const waiting = {};   // product id → resolve() of a buy() the game is waiting on
    store.register([
      ...prods.consumable.map(id => ({ id, type: ProductType.CONSUMABLE, platform: Platform.GOOGLE_PLAY })),
      ...prods.nonConsumable.map(id => ({ id, type: ProductType.NON_CONSUMABLE, platform: Platform.GOOGLE_PLAY }))
    ]);
    store.when()
      .productUpdated(p => { try { const pr = p.pricing && p.pricing.price; if (pr) storeApi.prices[p.id] = pr; } catch (e) {} })
      .approved(t => t.verify())
      .verified(r => r.finish())
      .finished(t => {
        (t.products || []).forEach(p => {
          if (waiting[p.id]) { const res = waiting[p.id]; delete waiting[p.id]; markSeen(t.transactionId); res(true); }
          else if (prods.consumable.includes(p.id) && !seen(t.transactionId)) {
            // paid earlier but never delivered (app closed during the purchase): give it now
            try { if (window.FlowerFeverGrant && window.FlowerFeverGrant(p.id)) markSeen(t.transactionId); } catch (e) {}
          }
        });
      });
    store.error(e => log('billing error', e && e.message));
    store.initialize([Platform.GOOGLE_PLAY]).catch(e => log('billing init', e));

    const seen = id => { try { return (JSON.parse(localStorage.getItem('ff.tx') || '[]')).includes(id); } catch (e) { return false; } };
    const markSeen = id => { try { const a = JSON.parse(localStorage.getItem('ff.tx') || '[]'); a.push(id); localStorage.setItem('ff.tx', JSON.stringify(a.slice(-200))); } catch (e) {} };

    storeApi.buy = id => new Promise(async res => {
      const p = store.get(id, Platform.GOOGLE_PLAY), offer = p && p.getOffer();
      if (!offer) { res(false); return; }
      waiting[id] = res;
      const err = await offer.order();
      if (err) { delete waiting[id]; res(false); }   // cancelled or failed
      setTimeout(() => { if (waiting[id]) { delete waiting[id]; res(false); } }, 10 * 60 * 1000);
    });
    storeApi.restore = async () => {
      try { await store.restorePurchases(); } catch (e) {}
      return store.products.filter(p => p.owned).map(p => p.id);
    };
  }, false);

  /* ---------- Local notifications ---------- */
  const LN = P('LocalNotifications');
  if (LN) {
    let asked = false;
    window.FlowerFeverNotify = {
      async schedule(list) {
        try {
          if (!asked) { asked = true; const p = await LN.checkPermissions(); if (p.display !== 'granted') await LN.requestPermissions(); }
          await LN.cancel({ notifications: list.map(n => ({ id: n.id })) }).catch(() => {});
          await LN.schedule({ notifications: list.map(n => ({ id: n.id, title: n.title, body: n.body, schedule: { at: new Date(n.at) } })) });
        } catch (e) { log('notify', e); }
      },
      cancel(ids) { try { LN.cancel({ notifications: ids.map(id => ({ id })) }); } catch (e) {} }
    };
  }

  /* ---------- Analytics (Firebase) ---------- */
  const FA = P('FirebaseAnalytics');
  if (FA && window.FLOWER_FIREBASE) {
    window.FlowerFeverAnalytics = {
      logEvent(name, params) {
        const clean = {}; Object.entries(params || {}).forEach(([k, v]) => { if (v !== undefined && v !== null) clean[k] = typeof v === 'boolean' ? (v ? 1 : 0) : v; });
        try { FA.logEvent({ name: String(name).slice(0, 40), params: clean }); } catch (e) {}
      }
    };
  }

  /* ---------- Android back button: close the open window, or ask before leaving ---------- */
  const App = P('App');
  if (App) App.addListener('backButton', () => {
    const ov = document.getElementById('overlay');
    const sheet = document.querySelector('.fsheet:not([hidden])');
    if (sheet) { sheet.hidden = true; return; }
    const close = ov && !ov.hidden && ov.querySelector('#gBack,#llClose,#lfNo,#sDone,#back,#rOk,#pOk,#gok2');
    if (close) { close.click(); return; }
    const home = document.querySelector('.fhomeb,#bHome');
    if (document.getElementById('homeView')) { App.minimizeApp(); return; }
    if (home && home.offsetParent) { home.click(); return; }
    App.minimizeApp();
  });
})();
