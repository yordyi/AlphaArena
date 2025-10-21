/**
 * Alpha Arena Service Worker
 * PWA 离线支持和缓存策略
 */

const CACHE_NAME = 'alpha-arena-v1';
const urlsToCache = [
    '/',
    '/static/manifest.json'
];

// 安装 Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('🚀 Service Worker: 缓存已打开');
                return cache.addAll(urlsToCache);
            })
    );
});

// 激活 Service Worker（清理旧缓存）
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️  Service Worker: 清理旧缓存', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// 拦截网络请求
self.addEventListener('fetch', event => {
    // 跳过 WebSocket 和 API 请求
    if (event.request.url.includes('socket.io') ||
        event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // 缓存命中，返回缓存的资源
                if (response) {
                    return response;
                }

                // 缓存未命中，发起网络请求
                return fetch(event.request).then(response => {
                    // 检查是否是有效响应
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }

                    // 克隆响应（因为响应流只能使用一次）
                    const responseToCache = response.clone();

                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, responseToCache);
                        });

                    return response;
                });
            })
    );
});
