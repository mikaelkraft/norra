const CACHE_NAME = 'norra-ai-cache-v3';
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'style.css',
  'app.js',
  'norraai.png',
  'splash.png',
  'analysis_hero.png',
  'terms.html',
  'privacy.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
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
  // Bypass API requests and non-GET requests from service worker cache
  if (
    event.request.url.includes('/predictions') || 
    event.request.url.includes('onrender.com') || 
    event.request.method !== 'GET'
  ) {
    return event.respondWith(fetch(event.request));
  }

  const url = new URL(event.request.url);
  const isCoreAsset = url.pathname.endsWith('index.html') || 
                      url.pathname.endsWith('app.js') || 
                      url.pathname.endsWith('style.css') || 
                      url.pathname === '/' || 
                      url.pathname === '';

  if (isCoreAsset) {
    // Network-First Strategy for core app files to guarantee users get the newest UI immediately
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
              if (networkResponse.status === 200) {
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
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

