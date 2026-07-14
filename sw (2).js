const CACHE_NAME = 'norra-ai-cache-v1';
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'style.css',
  'app.js',
  'norraai.png',
  'analysis_hero.png'
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

  // Stale-While-Revalidate caching strategy for static assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch fresh asset in the background and update the cache
        fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
            }
          })
          .catch(() => { /* ignore background fetch errors when offline */ });
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});
