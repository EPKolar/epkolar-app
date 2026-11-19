# Kamera-Gateway QNAP – Umgebungsvariablen (nur NAMEN, keine Werte)

Datei `.env` neben `docker-compose.yml` **auf der QNAP**, `chmod 600`. Nie ins Repo, nie in Chat/Mail/Protokoll.

| Name | Dienst | Bedeutung |
|---|---|---|
| `KAMERA_TOKEN_SECRET` | kamera-auth | HMAC-Schlüssel. **Muss exakt dem Supabase-Secret `KAMERA_TOKEN_SECRET` der Edge Function `kamera-stream` entsprechen** (mit diesem Wert signiert sie). ≥ 32 Zeichen. Setzt Sebastian auf der QNAP; nie Repo/Chat/Log. Kontrolle nur über den sha256-Präfix (Anleitung `docs/kameras/PILOT_HEUTE.md`, Schritt a). |
| `KAMERA_TOKEN_SECRET_FILE` | kamera-auth | Alternative zu oben: Pfad einer Datei mit dem Secret (Docker-Secret). |
| `KAMERA_AUTH_URI_HEADER` | kamera-auth | Vertrauenswürdiger Kopf, fest `x-forwarded-uri` (Caddy). In `docker-compose.yml` gesetzt. |
| `KAMERA_AUTH_METHOD_HEADER` | kamera-auth | Passendes Paar, fest `x-forwarded-method`. Fehlt/passt nicht → Start abgebrochen. |
| `KAMERA_AUTH_HOST` | kamera-auth | Fest `127.0.0.1` (nur lokal, nie im LAN). |
| `KAMERA_AUTH_PORT` | kamera-auth, caddy | Port des Prüfers (Standard 9099), nur 127.0.0.1. |
| `KAMERA_AUTH_LOG` | kamera-auth | `1` = knappes Protokoll (Zeit, Status, Art, Stream, users.id) – nie Tokens. |
| `QNAP_LAN_IP` | caddy | LAN-Adresse der QNAP; Site-Adresse und IP-Zertifikat (`tls internal`). Steht nur in der `.env` auf der QNAP. |
| `KAMERA_GATEWAY_PORT` | caddy | HTTPS-Port des Gateways (Standard 443; ist 443 durch QTS belegt, z. B. 8443). |

Supabase (setzt ein Mensch im Dashboard, nicht hier): `KAMERA_GATEWAY_BASE` = `https://<QNAP-LAN-IP>` bzw.
`https://<QNAP-LAN-IP>:<KAMERA_GATEWAY_PORT>` (Variante mit DNS: `https://kameras.ep-kolar.at`), `KAMERA_TOKEN_SECRET`.

Im LAN erreichbar: `KAMERA_GATEWAY_PORT` (Caddy) und **8555 TCP+UDP** (go2rtc WebRTC-Medien, direkt, nicht über Caddy).
Nicht erreichbar: 1984 (go2rtc-API, nur 127.0.0.1) und `KAMERA_AUTH_PORT`.
Stammzertifikat für die Geräte (Variante `tls internal`): Volume `caddy_daten`, Datei `/data/caddy/pki/authorities/local/root.crt`.
