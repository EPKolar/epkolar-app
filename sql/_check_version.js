#!/usr/bin/env node
// Verify APP_VERSION (index.html), CACHE_NAME (sw.js) and Header-Comment
// (sw.js line 1) are in sync. Exit 1 on mismatch.
//
// Usage: node sql/_check_version.js

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const idx = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const sw  = fs.readFileSync(path.join(root, 'sw.js'),      'utf8');

const mAppVersion = idx.match(/const\s+APP_VERSION\s*=\s*["']([\d.]+)-supabase["']/);
const mHeader     = sw.match(/^\/\/\s*EP Kolar Service Worker\s+v([\d.]+)/m);
const mCacheName  = sw.match(/const\s+CACHE_NAME\s*=\s*["']epkolar-v([\d.]+)["']/);

const app    = mAppVersion ? mAppVersion[1] : null;
const header = mHeader     ? mHeader[1]     : null;
const cache  = mCacheName  ? mCacheName[1]  : null;

console.log(`index.html APP_VERSION : ${app    ?? 'MISSING'}`);
console.log(`sw.js header comment   : ${header ?? 'MISSING'}`);
console.log(`sw.js CACHE_NAME       : ${cache  ?? 'MISSING'}`);

if (!app || !header || !cache) {
  console.error('✗ at least one version marker missing');
  process.exit(1);
}

if (app === header && header === cache) {
  console.log(`✓ versions synced: ${app}`);
  process.exit(0);
}

console.error('✗ version mismatch detected');
process.exit(1);
