const CACHE_NAME = "design-license-pwa-v15";
const QUESTION_IMAGE_VERSION = "20260603-figfix";
const QUESTION_IMAGE_ASSETS = [
  "./assets/questions/12600-A12-001.png",
  "./assets/questions/12600-A12-004.png",
  "./assets/questions/12600-A12-005.png",
  "./assets/questions/12600-A12-006.png",
  "./assets/questions/12600-A12-008.png",
  "./assets/questions/12600-A12-011.png",
  "./assets/questions/12600-A12-012.png",
  "./assets/questions/12600-A12-013.png",
  "./assets/questions/12600-A12-014.png",
  "./assets/questions/12600-A12-015.png",
  "./assets/questions/12600-A12-017.png",
  "./assets/questions/12600-A12-018.png",
  "./assets/questions/12600-A12-019.png",
  "./assets/questions/12600-A12-020.png",
  "./assets/questions/12600-A12-022.png",
  "./assets/questions/12600-A12-030.png",
  "./assets/questions/12600-A12-031.png",
  "./assets/questions/12600-A12-032.png",
  "./assets/questions/12600-A12-033.png",
  "./assets/questions/12600-A12-043.png",
  "./assets/questions/12600-A12-044.png",
  "./assets/questions/12600-A12-045.png",
  "./assets/questions/12600-A12-048.png",
  "./assets/questions/12600-A12-051.png",
  "./assets/questions/12600-A12-052.png",
  "./assets/questions/12600-A12-053.png",
  "./assets/questions/12600-A12-054.png",
  "./assets/questions/12600-A12-055.png",
  "./assets/questions/12600-A12-056.png",
  "./assets/questions/12600-A12-057.png",
  "./assets/questions/12600-A12-058.png",
  "./assets/questions/12600-A12-059.png",
  "./assets/questions/12600-A12-060.png",
  "./assets/questions/12600-A12-061.png",
  "./assets/questions/12600-A12-062.png",
  "./assets/questions/12600-A12-063.png",
  "./assets/questions/12600-A12-064.png",
  "./assets/questions/12600-A12-065.png",
  "./assets/questions/12600-A12-067.png",
  "./assets/questions/12600-A12-068.png",
  "./assets/questions/12600-A12-069.png",
  "./assets/questions/12600-A12-070.png",
  "./assets/questions/12600-A12-079.png",
  "./assets/questions/12600-A12-095.png",
  "./assets/questions/12600-A12-305.png"
].map((path) => `${path}?v=${QUESTION_IMAGE_VERSION}`);

const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./assets/icon-192.png?v=20260604-book2",
  "./assets/icon-512.png?v=20260604-book2",
  "./assets/icon-maskable-512.png?v=20260604-book2",
  "./assets/apple-touch-icon.png?v=20260604-book2",
  "./src/styles.css?v=20260604-fade",
  "./src/app.js?v=20260604-fade",
  "./src/data/questions.json?v=20260603-focus"
].concat(QUESTION_IMAGE_ASSETS);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put("./index.html", copy));
          return response;
        })
        .catch(() => caches.match("./index.html").then((cached) => cached || caches.match("./")))
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      });
    })
  );
});
