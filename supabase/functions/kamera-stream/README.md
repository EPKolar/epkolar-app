# kamera-stream (EPKolar Kameras Phase 1, 19.11.2026)

Edge Function: issues **short-lived, signed stream URLs** for one camera to one authorized user.
It is the security core of the camera feature — hiding the menu in the client is NOT protection
(lesson fz_finanzen). **NOT deployed.** No SQL in this folder; the data model is `sql/KAMERAS_v1_ENTWURF.sql`.

Files: `index.ts` (Deno wiring, supabase-js), `logic.ts` (pure decision + token logic, no imports,
tested in Node by `tests/test_kameras_phase1_v1055.py`).

## Deploy (later, only after the SQL gate and the infrastructure exist)

```
# from the deploy folder (C:\temp\epkfn, never from a network drive)
supabase functions deploy kamera-stream --project-ref jiggujpruejkaomgxarp
supabase secrets set --project-ref jiggujpruejkaomgxarp KAMERA_TOKEN_SECRET=<random, >= 32 chars> KAMERA_BACKEND_BASE=https://<proxy host>
```

- `verify_jwt = true` (default) — the gateway rejects calls without a JWT; the function additionally calls
  `auth.getUser(jwt)` and checks the `users` row itself.
- Both files (`index.ts`, `logic.ts`) must be deployed together (MCP `deploy_edge_function`: pass both).
- Built-in secrets used: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (auto-injected).
- Own secrets:

| Secret | Required | Meaning |
|---|---|---|
| `KAMERA_TOKEN_SECRET` | yes | HMAC key shared ONLY with the reverse proxy. >= 32 chars, random (`openssl rand -base64 48`). Never in the repo, never in the client. |
| `KAMERA_BACKEND_BASE` | yes | Public base URL of the reverse proxy, must be `https://`, no trailing slash needed. |
| `KAMERA_TOKEN_TTL` | no | Token lifetime in seconds, clamped to 30..120, default 90. |
| `KAMERA_AUFZEICHNUNG_ROLLEN` | no | Comma list of roles allowed to request recordings, default `admin,projektleiter,buero`. Always intersected with the four camera roles — a typo can never unlock a Monteur. |

Missing/invalid secret or base -> `503 {error:"nicht_konfiguriert"}` (only after the caller passed the role gate).

## Request

`POST /functions/v1/kamera-stream` with `Authorization: Bearer <user JWT>`, `apikey`, JSON body
(max 2 KB):

```
{ "kamera_id": "<kameras.id>", "scope": "live" | "aufzeichnung", "geraet": "pc" | "mobil" }
```

`scope` defaults to `live`, `geraet` defaults to `mobil`.

## Decision order (all server-side)

1. JWT valid (`auth.getUser`) — else `401 nicht_angemeldet`
2. `users` row by `auth_user_id`: active and not locked — else `403 kein_zugriff`
3. `users.role` in **admin, projektleiter, buero, lagerleitung** — else `403 kein_zugriff`
   (Monteur, Helfer, Techniker, Obermonteur, lager_display, stempel_terminal: always here; nothing else is queried)
4. secrets present — else `503 nicht_konfiguriert`
5. body valid — else `400 ungueltig`
6. `scope=aufzeichnung`: `geraet` must be `pc` AND role in `KAMERA_AUFZEICHNUNG_ROLLEN` — else `403 kein_zugriff`.
   The server cannot really know the device; `geraet` is a client claim. Recordings are therefore gated by
   the role list as well — the `pc` check only keeps honest phones on live.
7. `rpc kamera_darf_sehen(p_kamera)` called **with the caller's JWT** (so `auth.uid()` is the caller) and
   **without** a timestamp (DB uses `now()`, evaluated in Europe/Vienna) — else `403 kein_zugriff`
8. `kamera_backend` row (service role) with a valid stream / recording name — else `503 nicht_konfiguriert`
9. sign token, return URLs, write `kamera_abruf_log` (best effort)

Error bodies are exactly `{error:<code>}`; they never contain a URL, a stream name, a user or a reason.
All responses carry `Cache-Control: no-store`. CORS: only `https://epkolar.github.io`; any other `Origin`
gets `403 {error:"origin"}` without `Access-Control-Allow-Origin`.

## Response (200)

Phase 2: the live answer depends on `kamera_backend.stream_typ` (`webrtc` | `llhls` | `mjpeg` | `snapshot`,
default `webrtc`). The type is read only in step 8, i.e. after the full authorization; an unknown type gives
`503 nicht_konfiguriert`. Every kind uses the same token. Mobotix (HTTP/MJPEG only) maps to `mjpeg` or `snapshot`;
the mapping stream name -> camera address lives only in the go2rtc config on the video host.

```
typ=webrtc:          { "typ": "webrtc", "liveUrl": "<BASE>/live/<stream>/index.m3u8?token=<T>",
                       "webrtcUrl": "<BASE>/live/<stream>/whep?token=<T>",
                       "exp": <unix s>, "ttl": <s> }
typ=llhls:           { "typ": "llhls", "liveUrl": "<BASE>/live/<stream>/index.m3u8?token=<T>", "exp", "ttl" }
typ=mjpeg:           { "typ": "mjpeg", "mjpegUrl": "<BASE>/live/<stream>/mjpeg?token=<T>", "exp", "ttl" }
typ=snapshot:        { "typ": "snapshot", "snapshotUrl": "<BASE>/live/<stream>/snapshot.jpg?token=<T>", "exp", "ttl" }
scope=aufzeichnung:  { "aufzeichnungUrl": "<BASE>/aufzeichnung/<quelle>?token=<T>", "exp": <unix s>, "ttl": <s> }
```

The client requests a fresh URL per tile and refreshes it about 20 s before `exp`.
App rendering: `webrtc`/`llhls` -> `<video>` (WHEP, else native HLS); `mjpeg` -> `<img>` on `/live/<s>/mjpeg`
(new token URL swapped in before `exp`); `snapshot` -> `<img>` reloaded every 2 s (`&_=<n>`), paused while the tab
is hidden or the tile is off screen. Image errors / WHEP 404/5xx show "Kamera nicht erreichbar".
For recordings the client appends `&von=<unix s>&bis=<unix s>`.

## TOKEN CONTRACT (the reverse proxy MUST implement exactly this)

```
T        = P "." S
P        = base64url( UTF-8 JSON payload )              (no padding)
S        = base64url( HMAC-SHA256( key = KAMERA_TOKEN_SECRET (UTF-8 bytes), message = P as ASCII bytes ) )
payload  = { "v": 1,                     // version, reject anything else
             "k": "<kameras.id>",
             "s": "<stream_name | aufzeichnung_quelle>",
             "u": "<users.id>",          // for the proxy access log
             "sc": "live" | "aufzeichnung",
             "iat": <unix s>, "exp": <unix s>,
             "n": "<uuid nonce>" }
```

In the URL the token is percent-encoded (`encodeURIComponent`); base64url has no characters that need it,
so in practice it is passed verbatim.

The proxy accepts a request only if ALL hold:

1. `T` splits into exactly two parts; `S` verifies with a **constant-time** HMAC comparison.
2. `v == 1`, `0 < exp - iat <= 120`, `exp > now`, `iat <= now + 5` (max 5 s clock skew; proxy clock via NTP).
3. Path type matches `sc`: `/live/<s>/...` needs `sc=live`, `/aufzeichnung/<s>` needs `sc=aufzeichnung`.
4. Path stream equals `s` exactly (no prefix match, no case folding).
5. Path is one of the allowed shapes: `/live/<s>/index.m3u8`, `/live/<s>/whep`, `/live/<s>/mjpeg`,
   `/live/<s>/snapshot.jpg`, `/live/<s>/hls/<file>` (HLS parts), `/aufzeichnung/<s>` — everything else
   (go2rtc `/api/*` admin, config, Frigate UI) is 404.

Reference implementation for the proxy: `tools/kamera-proxy-auth/` (`verify.mjs` for Caddy `forward_auth` /
nginx `auth_request`, `token.mjs` = 1:1 port of `pruefeToken`, shared vectors `vektoren.json`).

Session continuity (the token is only for session START):

- **WebRTC (WHEP)**: the token is checked on the WHEP `POST` offer; the established peer connection may run past `exp`.
  The proxy ends sessions after at most 30 min; the client then re-requests.
- **LL-HLS**: on a valid `index.m3u8` request the proxy sets an `HttpOnly; Secure; SameSite=None; Path=/live/<s>/`
  cookie bound to `s` and `exp` (or rewrites segment URLs with the same token). Segments without a valid
  token/cookie → 401. When `exp` passes, the client fetches a fresh token and reloads the playlist.
- **MJPEG**: token checked when the stream starts; the app swaps in a fresh token URL before `exp` (the browser
  closes the old connection). On 403 at refresh the app removes the image at once.
- **Snapshot**: every frame request is checked (same token until the app refreshes it).
- **Recordings**: token checked per request; `von/bis` must lie inside the camera's retention
  (`kameras.aufbewahrung_tage`, enforced on the storage side by deleting older footage).

Replay inside the 120 s window is accepted by design (short lifetime instead of a nonce store). If the proxy
can keep state, it may reject a second WHEP offer with the same `n`.

`logic.ts` exports `pruefeToken(secret, token, nowMs, {s, sc})` as the executable reference of these rules.

## Infrastructure NOT built here

go2rtc/Frigate on the video host, QNAP storage, the reverse proxy (TLS + token check above), WireGuard between
office and sites. The proxy is the ONLY public entry; go2rtc/Frigate ports are never exposed. Camera
credentials (RTSP user/password) live only in the go2rtc/Frigate config on the video host.
