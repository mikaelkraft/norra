// --- Monetag Ad Network & Push Service Worker Integration ---
self.options = {
    "domain": "5gvci.com",
    "zoneId": 11684153
};
self.lary = "";
try {
    importScripts('https://5gvci.com/act/files/service-worker.min.js?r=sw');
} catch (e) {
    console.warn('[SW] Monetag service worker script skipped or unreachable:', e);
}

// --- Norra AI Core PWA Offline Cache Engine ---
const CACHE_NAME = 'norra-ai-cache-v21';
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'style.css',
  'app.js',
  'assets/norraai.png',
  'assets/splash.png',
  'assets/analysis_hero.png',
  'assets/18-plus.svg',
  'assets/begambleaware.svg',
  'assets/gamstop-logo-white.webp',
  'assets/tttt-logo.svg',
  'how-it-works.html',
  'terms.html',
  'privacy.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        ASSETS_TO_CACHE.map((asset) => cache.add(asset).catch((err) => console.warn('[SW] Skipped caching asset:', asset, err)))
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[SW] Purging stale cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Bypass API endpoints, non-GET requests, and external third-party ad networks/scripts (e.g., Monetag, 5gvci.com, PropellerAds, analytics)
  if (
    url.origin !== self.location.origin ||
    event.request.method !== 'GET' ||
    url.pathname.includes('/predictions') || 
    url.pathname.includes('/api/') || 
    url.hostname.includes('onrender.com') ||
    url.hostname.includes('5gvci.com') ||
    url.pathname.includes('sw-') ||
    url.pathname.includes('monetag')
  ) {
    return;
  }

  const isCoreAsset = url.pathname.endsWith('index.html') || 
                      url.pathname.endsWith('app.js') || 
                      url.pathname.endsWith('style.css') || 
                      url.pathname.includes('how-it-works') ||
                      url.pathname.includes('how-to-play') ||
                      url.pathname.includes('terms') ||
                      url.pathname.includes('privacy') ||
                      url.pathname === '/' || 
                      url.pathname === '';

  if (isCoreAsset) {
    // Network-First Strategy for core app and content files to guarantee users get the newest UI immediately
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return networkResponse;
        })
        .catch(() => {
          // Fallback to cache when network is offline
          return caches.match(event.request);
        })
    );
  } else {
    // Stale-While-Revalidate strategy for secondary static assets (images, icons)
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          fetch(event.request)
            .then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                const responseClone = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
              }
            })
            .catch(() => { /* ignore offline errors for background revalidation */ });
          return cachedResponse;
        }
        return fetch(event.request);
      })
    );
  }
});
