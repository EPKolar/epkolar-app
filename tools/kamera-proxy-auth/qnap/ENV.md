# Kamera-Gateway QNAP – Umgebungsvariablen (nur NAMEN, keine Werte)

Datei `.env` neben `docker-compose.yml` **auf der QNAP**, `chmod 600`. Nie ins Repo, nie in Chat/Mail/Protokoll.
Die echte LAN-Adresse der QNAP steht NUR dort (`QNAP_LAN_IP=…`), nie in diesem Repo.

| Name | Dienst | Bedeutung |
|---|---|---|
| `KAMERA_TOKEN_SECRET` | kamera-auth | **Pflicht.** HMAC-Schlüssel, **exakt gleich dem Supabase-Secret `KAMERA_TOKEN_SECRET`** der Edge Function `kamera-stream` (damit signiert sie). ≥ 32 Zeichen. Setzt ein Mensch (Sebastian) auf der QNAP; nie Repo/Chat/Log. Kontrolle nur über den sha256-Präfix (`docs/kameras/PILOT_HEUTE.md`, Schritt a). |
| `KAMERA_TOKEN_SECRET_FILE` | kamera-auth | Alternative zu oben: Pfad einer Datei mit dem Secret (Docker-Secret). |
| `KAMERA_AUTH_URI_HEADER` | kamera-auth | Fest `x-forwarded-uri` (Caddy `forward_auth`). In `docker-compose.yml` gesetzt. |
| `KAMERA_AUTH_METHOD_HEADER` | kamera-auth | Fest `x-forwarded-method` (Paar zu oben). Fehlt/passt nicht → Start abgebrochen. |
| `KAMERA_AUTH_HOST` | kamera-auth | `0.0.0.0` im compose-Netz (nicht veroeffentlicht – nur Caddy erreicht ihn als `kamera-auth`). |
| `KAMERA_AUTH_PORT` | kamera-auth | Fest `9099` (Caddyfile `forward_auth kamera-auth:9099`). |
| `KAMERA_AUTH_LOG` | kamera-auth | `1` = knappes Protokoll (Zeit, Status, Art, Stream, users.id) – nie Tokens. |
| `QNAP_LAN_IP` | caddy | LAN-Adresse der QNAP: Site-Adresse + IP-Zertifikat (`tls internal`), Veröffentlichung `<QNAP_LAN_IP>:<GATEWAY_PORT>` und Ziel `<QNAP_LAN_IP>:1984` (go2rtc). |
| `GO2RTC_BASIC` | caddy | **Pflicht.** base64 von `<GO2RTC_USER>:<GO2RTC_PASS>` – erzeugen mit dem Einzeiler unten (nichts wird angezeigt). Caddy setzt damit bei JEDEM Weiterleiten an go2rtc `Authorization: Basic …` (ueberschreibt den Kopf des Clients). Gleiches Paar wie in der go2rtc-kam.env. |
| `GATEWAY_PORT` | caddy | Port des Gateways, **Standard `8443`** (die QNAP-Weboberfläche belegt 443 selbst). Gilt für Site-Adresse und Veröffentlichung (innen = außen). Nur wenn 443 auf der QNAP frei ist: `443`. |

Supabase (setzt ein Mensch im Dashboard, nicht hier): `KAMERA_GATEWAY_BASE` = `https://<QNAP-LAN-IP>:8443`
(bzw. `https://<QNAP-LAN-IP>` wenn `GATEWAY_PORT=443`; Variante mit DNS: `https://kameras.ep-kolar.at`) und `KAMERA_TOKEN_SECRET`.
Image-freie Variante für Container Station: `qnap-gateway-inline.compose.yml` (erzeugt von `qnap/inline_bauen.py`, gleiche `.env`).
go2rtc (eigene App, nicht hier): Zugangsdaten `KAM_USER` / `KAM_PASS`, `MOBOTIX_USER` / `MOBOTIX_PASS` und die API-Anmeldung
`GO2RTC_USER` / `GO2RTC_PASS` in deren eigener env-Datei (`kam.env`) auf der QNAP; Liste: `docs/kameras/MOBOTIX.md`.
Reihenfolge: zuerst Caddy mit `GO2RTC_BASIC` neu starten (go2rtc ohne Anmeldung ignoriert den Kopf), dann go2rtc mit
Anmeldung. Die Firewall-Sperre fuer `:1984` bleibt trotzdem Pflicht (zweite Schicht; go2rtc laesst Anfragen von localhost
OHNE Anmeldung durch).

`GO2RTC_BASIC` erzeugen, ohne den Wert anzuzeigen (auf der QNAP, im Ordner der Gateway-`.env`; liest das Paar aus der
go2rtc-`kam.env`, haengt eine Zeile an; vorher eine alte `GO2RTC_BASIC`-Zeile entfernen):
```
( set -a; . /share/Container/go2rtc/kam.env; printf 'GO2RTC_BASIC=%s\n' "$(printf %s "$GO2RTC_USER:$GO2RTC_PASS" | base64 | tr -d '\n')" ) >> .env && chmod 600 .env && grep -c '^GO2RTC_BASIC=' .env
```
Erwartete Ausgabe: `1` (Anzahl der Zeilen, nie der Wert).

Im LAN erreichbar: `<QNAP-LAN-IP>:<GATEWAY_PORT>` (Caddy, Standard 8443) und **`<QNAP-LAN-IP>:8555` TCP+UDP** (go2rtc WebRTC-Medien, direkt, nicht
über Caddy). Nicht erreichbar sein darf `:1984` (go2rtc-API, per QNAP-Firewall nur für die QNAP selbst).
Stammzertifikat (Variante `tls internal`): Volume `caddy_daten`, `/data/caddy/pki/authorities/local/root.crt` – **nur auf
Firmengeräten** (Tablet, Büro-PCs) installieren, **nie auf privaten Handys** (eine Firmen-CA könnte dort jede Seite signieren).
