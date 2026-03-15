/**
 * EP: Kolar & Sohn - Service Worker v3.1 (Supabase)
 */
const CACHE = 'epkolar-v3.1-supabase';
const APP_SHELL = ['./', './index.html'];
const SUPABASE_HOST = 'jiggujpruejkaomgxarp.supabase.co';

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.hostname === SUPABASE_HOST) return;
  if (url.hostname === 'cdnjs.cloudflare.com') {
    e.respondWith(caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(resp => {
        if (resp.ok) { const clone = resp.clone(); caches.open(CACHE).then(c => c.put(e.request, clone)); }
        return resp;
      });
    }));
    return;
  }
  e.respondWith(caches.match(e.request).then(cached => {
    if (cached) return cached;
    return fetch(e.request).then(resp => {
      if (resp.ok && resp.type === 'basic') { const clone = resp.clone(); caches.open(CACHE).then(c => c.put(e.request, clone)); }
      return resp;
    });
  }).catch(() => caches.match('./index.html')));
});

self.addEventListener('sync', e => {
  if (e.tag === 'epkolar-sync') {
    e.waitUntil(self.clients.matchAll().then(clients => { clients.forEach(client => client.postMessage({ type: 'SYNC_TRIGGER' })); }));
  }
});

self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
    self.clients.matchAll().then(clients => { clients.forEach(client => client.postMessage({ type: 'SW_UPDATED' })); });
  }
});