# kamera-proxy-auth (EPKolar Cameras Phase 2, 19.11.2026)

Tiny, dependency-free Node service (Node >= 20) that the reverse proxy asks **before every request** to
`/live/*` and `/aufzeichnung/*`. It verifies the HMAC token issued by the Edge Function `kamera-stream`
(contract: `supabase/functions/kamera-stream/README.md`). **Not deployed** — the infrastructure templates live
outside the app repo in `C:/repos/epk-kamera-pilot/`.

| File | Purpose |
|---|---|
| `verify.mjs` | HTTP service + pure decision `entscheide(req, secret, nowMs)` + path grammar `pfadArt(path)` |
| `token.mjs` | 1:1 port of `signiere` / `pruefeToken` from `logic.ts` (same rule lines, checked word for word by the tests) |
| `vektoren.json` | shared test vectors (token level + request level); the secret inside is a **test value only** |
| `vorlagen/` | reviewable proxy templates without real addresses: `nginx.conf` (auth_request, header overwrite/clear, `underscores_in_headers off`) and `Caddyfile` (forward_auth with explicit `header_up`) |

Tests: `tests/test_kameras_phase2_v1056.py` runs `logic.ts` AND `token.mjs` against the same `vektoren.json`,
signs cross-wise (tokens are byte-identical), checks every URL the Edge Function emits is accepted here, and
has reverse probes (removing the expiry or the path binding makes the vectors fail).

## Decision

| Status | When |
|---|---|
| `204` | token valid **and** path stream == `s` **and** path kind == `sc` **and** path shape + method allowed |
| `401` | no token, two `token` parameters, bad signature, tampered payload, expired (`exp <= now`), `exp - iat > 120` or `<= 0`, `iat > now + 5` (clock skew), `v != 1`, malformed |
| `403` | signature fine but wrong stream / wrong kind (`live` vs `aufzeichnung`), path not one of the allowed shapes, method not allowed, recording whose query `von`/`bis` is missing, duplicated, %-encoded or not character-identical to the `von`/`bis` signed in the token |

Allowed shapes (everything else 403; the Caddyfile already answers 404 before asking):

```
POST      /live/<s>/whep                 WebRTC offer (WHEP)          sc=live
GET|HEAD  /live/<s>/index.m3u8           HLS playlist                 sc=live
GET|HEAD  /live/<s>/hls/<file>           HLS parts (token or cookie)  sc=live
GET|HEAD  /live/<s>/mjpeg                MJPEG stream (<img>)         sc=live
GET|HEAD  /live/<s>/snapshot.jpg         single frame (<img>, 2 s)    sc=live
GET|HEAD  /aufzeichnung/<s>?von=&bis=    recording (span <= 2 h)      sc=aufzeichnung, von/bis == signed
GET|HEAD  /aufzeichnung/<s>/<file>...    recording parts              sc=aufzeichnung (von/bis if present == signed)
<s> = [A-Za-z0-9_-]{1,64}; no %, no .., no // anywhere in the path
```

Token sources, in order: query `?token=` (from the app) → header `X-Kamera-Token` → `Authorization: Bearer` →
cookie `kam_t` (only for `hls/<file>` and recording parts). On a valid query token for `index.m3u8` or a
recording the service answers with `Set-Cookie: kam_t=<token>; Path=/live/<s>/; Max-Age=<= 120; HttpOnly; Secure; SameSite=None`.

Original URI and method come ONLY from the header pair configured explicitly (required, the service refuses
to start otherwise):

| Proxy | `KAMERA_AUTH_URI_HEADER` | `KAMERA_AUTH_METHOD_HEADER` |
|---|---|---|
| Caddy `forward_auth` | `x-forwarded-uri` | `x-forwarded-method` |
| nginx `auth_request` | `x-original-uri` | `x-original-method` |

There is **no fallback** to the request URL. If a request carries any header of the OTHER pair, it is a
client-injected header → `403`. Reason: nginx passes client headers to the auth subrequest by default, so
without this a client holding a token for camera A could request camera B and send `X-Forwarded-Uri: <path of A>`
to fool the path binding. In addition the proxy snippets below overwrite/clear the client copies.
Missing or empty configured header → `403`; a duplicated header is rejected.

On 204 the response carries `X-Kamera-Stream: <s>` and `X-Kamera-User: <users.id>` for the proxy access log.

**No token logging.** The service logs nothing by default; `KAMERA_AUTH_LOG=1` writes one JSON line per request
with `t, status, art, s, u` only — never the token, query, cookie or headers. The proxy's own access log must strip
the query parameter `token` (snippets below).

## Run

```
KAMERA_TOKEN_SECRET=<same value as the Edge Function secret, >= 32 chars> \
KAMERA_AUTH_URI_HEADER=x-forwarded-uri KAMERA_AUTH_METHOD_HEADER=x-forwarded-method \
KAMERA_AUTH_HOST=0.0.0.0 KAMERA_AUTH_PORT=9099 node verify.mjs
```

- `KAMERA_TOKEN_SECRET_FILE=/run/secrets/kamera_token_secret` instead of the variable (Docker secret).
- Missing or short secret, or missing/mismatched `KAMERA_AUTH_URI_HEADER` / `KAMERA_AUTH_METHOD_HEADER` → exit
  code 1, the proxy then fails closed (forward_auth gets no 2xx).
- `GET /gesund` (without forwarded headers) → `200 ok` for health checks.
- Bind it only inside the Docker network / localhost. It trusts `X-Forwarded-Uri`, so it must never be reachable
  by clients directly.

## Caddy (forward_auth)

Order matters: `forward_auth` must run **before** any `rewrite`, otherwise the verifier sees the rewritten
go2rtc path. Use `route` blocks. Full file: `C:/repos/epk-kamera-pilot/Caddyfile`.
Verifier env for Caddy: `KAMERA_AUTH_URI_HEADER=x-forwarded-uri`, `KAMERA_AUTH_METHOD_HEADER=x-forwarded-method`.
Caddy's `forward_auth` **overwrites** `X-Forwarded-Uri` / `X-Forwarded-Method` with the real values, so a client
copy never arrives. Client-supplied `X-Original-*` headers are stripped with `header_up` (if one slipped through,
the verifier answers 403 anyway).

```
route /live/* {
	forward_auth kamera-auth:9099 {
		uri /pruefen
		header_up -X-Original-URI
		header_up -X-Original-Method
		copy_headers X-Kamera-User X-Kamera-Stream
	}
	# whep -> go2rtc /api/webrtc?src=<s>, mjpeg -> /api/stream.mjpeg?src=<s>, snapshot.jpg -> /api/frame.jpeg?src=<s>
	...
	reverse_proxy go2rtc:1984
}

log {
	format filter {
		wrap json
		fields {
			request>uri query {
				delete token
			}
		}
	}
}
```

Caddy's `forward_auth` does not pass the verifier's `Set-Cookie` to the client on success. HLS via Caddy is
therefore **not part of the pilot** (all G3 run as `webrtc`; Safari also uses WebRTC). See open questions.

## nginx (auth_request)

Verifier env for nginx: `KAMERA_AUTH_URI_HEADER=x-original-uri`, `KAMERA_AUTH_METHOD_HEADER=x-original-method`.
nginx passes client headers to the subrequest, so the snippet sets the trusted pair from nginx variables and
**clears** the client copies of the other pair (an empty value makes nginx drop the header).

```
location = /_kamera_pruefen {
    internal;
    proxy_pass              http://kamera-auth:9099/pruefen;
    proxy_pass_request_body off;
    proxy_set_header        Content-Length "";
    proxy_set_header        X-Original-URI     $request_uri;
    proxy_set_header        X-Original-Method  $request_method;
    proxy_set_header        X-Forwarded-Uri    "";
    proxy_set_header        X-Forwarded-Method "";
}

location ~ ^/live/([A-Za-z0-9_-]{1,64})/(whep|index\.m3u8|mjpeg|snapshot\.jpg|hls/[A-Za-z0-9._-]+)$ {
    auth_request     /_kamera_pruefen;
    proxy_set_header X-Original-URI "";      # never forward client copies upstream either
    proxy_set_header X-Original-Method "";
    proxy_set_header X-Forwarded-Uri "";
    proxy_set_header X-Forwarded-Method "";
    auth_request_set $kam_cookie $upstream_http_set_cookie;
    add_header       Set-Cookie $kam_cookie;
    add_header       Cache-Control no-store always;
    # rewrite to go2rtc as in the Caddyfile, then:
    proxy_pass       http://go2rtc:1984;
}

location / { return 404; }

# access log WITHOUT the query string (no tokens in logs)
log_format kamera '$remote_addr [$time_local] "$request_method $uri" $status $body_bytes_sent';
access_log /var/log/nginx/kamera.log kamera;
```

`auth_request` maps 401/403 from the verifier to the client and treats any other non-2xx as 500 (fail closed).

## Changing the contract

Change `logic.ts` and `token.mjs` together, regenerate `vektoren.json` (signed with `logic.ts`), run
`python -m pytest tests/test_kameras_phase2_v1056.py`.
