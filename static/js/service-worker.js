// Service Worker for Electoral Office PWA
// Version 2.2.0 - Simplified Offline-First Strategy
// المكتب الانتخابي - كتلة الصادقون

const CACHE_VERSION = 'v2.2.0';
const CACHE_NAME = `electoral-office-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline/';

// ملفات حرجة يجب تخزينها فوراً
const PRECACHE_URLS = [
    '/',
    '/dashboard/',
    '/offline/',
    '/vote/candidates/',
    '/electoral-public/',
    '/my-voters/',
    '/static/css/styles.css',
    '/static/css/pwa.css',
    '/static/css/responsive.css',
    '/static/js/main.js',
    '/static/js/pwa-install.js',
    '/static/js/localdb.js',
    '/static/js/data-sync.js',
    '/static/js/sync.js',
    '/static/manifest.json',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-128x128.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-152x152.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-384x384.png',
    '/static/icons/icon-512x512.png',
    '/static/images/sadiqoon_logo.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://code.jquery.com/jquery-3.7.0.min.js',
];

// Install Event
self.addEventListener('install', event => {
    console.log('[SW v2.2] Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching app shell');
                // تخزين بدون فشل للملفات المحلية
                const localFiles = PRECACHE_URLS.filter(url => !url.startsWith('http'));
                return cache.addAll(localFiles).catch(err => {
                    console.warn('[SW] Some files failed to cache:', err);
                });
            })
            .then(() => {
                // تخزين الملفات الخارجية بشكل منفصل
                return caches.open(CACHE_NAME).then(cache => {
                    PRECACHE_URLS
                        .filter(url => url.startsWith('http'))
                        .forEach(url => {
                            fetch(url, { mode: 'cors' })
                                .then(response => cache.put(url, response))
                                .catch(err => console.warn('[SW] Failed to cache:', url));
                        });
                });
            })
            .then(() => self.skipWaiting())
    );
});

// Activate Event
self.addEventListener('activate', event => {
    console.log('[SW v2.2] Activating...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName.startsWith('electoral-office-') && cacheName !== CACHE_NAME) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch Event - الاستراتيجية الجديدة المبسطة
self.addEventListener('fetch', event => {
    const { request } = event;

    // تجاهل الطلبات غير GET
    if (request.method !== 'GET') {
        return;
    }

    // تجاهل Chrome extensions
    if (request.url.startsWith('chrome-extension:')) {
        return;
    }

    event.respondWith(handleFetch(request));
});

async function handleFetch(request) {
    const url = new URL(request.url);

    // استراتيجية 1: Cache First للملفات الثابتة (CSS, JS, صور)
    if (isStaticAsset(url)) {
        return cacheFirst(request);
    }

    // استراتيجية 2: Stale While Revalidate للصفحات HTML
    if (request.mode === 'navigate' || request.destination === 'document') {
        return staleWhileRevalidateForPages(request);
    }

    // استراتيجية 3: Network First للباقي
    return networkFirst(request);
}

// Cache First - للملفات الثابتة
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return cached || new Response('Offline', { status: 503 });
    }
}

// Stale While Revalidate - للصفحات (الاستراتيجية الأهم!)
async function staleWhileRevalidateForPages(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    // نحاول جلب من الشبكة في الخلفية
    const fetchPromise = fetch(request).then(response => {
        // تخزين الصفحة إذا كانت ناجحة وليست redirect
        if (response.ok && !response.redirected) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => null);

    // إذا كان لدينا كاش، نرجعه فوراً (حتى لو كانت الشبكة متوفرة!)
    if (cached) {
        console.log('[SW] Serving from cache:', request.url);
        // تحديث الكاش في الخلفية
        fetchPromise;
        return cached;
    }

    // إذا لم يكن لدينا كاش، ننتظر الشبكة
    try {
        const response = await fetchPromise;
        if (response && response.ok) {
            return response;
        }

        // إذا فشلت الشبكة أو redirect، نحاول Dashboard
        const dashboardCache = await cache.match('/dashboard/');
        if (dashboardCache) {
            console.log('[SW] Serving dashboard from cache');
            return dashboardCache;
        }

        // آخر محاولة: صفحة offline
        const offlineCache = await cache.match(OFFLINE_URL);
        return offlineCache || new Response('غير متصل', { status: 503 });

    } catch (error) {
        console.log('[SW] Network failed, checking cache');

        // محاولة Dashboard من الكاش
        const dashboardCache = await cache.match('/dashboard/');
        if (dashboardCache) {
            return dashboardCache;
        }

        // صفحة offline
        const offlineCache = await cache.match(OFFLINE_URL);
        return offlineCache || new Response('غير متصل', { status: 503 });
    }
}

// Network First - للـ API والباقي
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        return cached || new Response('Offline', { status: 503 });
    }
}

// Helper Functions
function isStaticAsset(url) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.webp'];
    return staticExtensions.some(ext => url.pathname.endsWith(ext)) ||
        url.pathname.startsWith('/static/') ||
        url.pathname.startsWith('/media/');
}

// Message Handler
self.addEventListener('message', event => {
    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }

    if (event.data.action === 'clearCache') {
        event.waitUntil(
            caches.delete(CACHE_NAME)
                .then(() => console.log('[SW] Cache cleared'))
        );
    }
});

console.log('[SW v2.2] Loaded - Offline-First Strategy');
