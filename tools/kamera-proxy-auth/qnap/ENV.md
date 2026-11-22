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
go2rtc (eigene App, nicht hier): Zugangsdaten `MOBOTIX_USER` / `MOBOTIX_PASS` und die API-Anmeldung
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

## Variante öffentliches Zertifikat: `https://kameras.ep-kolar.at:8443` (Let's Encrypt, ohne Geräte-Installation)

Dateien: `Caddyfile.publiccert`, `acme_start.sh`, `caddy_start.sh`, eingebettet in **`qnap-gateway-publiccert-inline.compose.yml`**
(erzeugt von `qnap/inline_bauen.py`; Riegel `tests/test_kamera_publiccert.py`). Die Variante `tls internal` oben bleibt unverändert.
Zertifikat per **DNS-01 im DNS-Alias-Modus** (acme.sh, Image `neilpang/acme.sh:3.1.5`): kein eingehender Port, die QNAP
bleibt im LAN. `ep-kolar.at` bleibt bei myNET/Squarebase – **kein Nameserver-Wechsel**; myNET bekommt nur einen A-Eintrag
und **einen** CNAME, der die Prüfung an eine Zone bei deSEC delegiert (myNET hat keine API, deSEC schon: acme.sh `dns_desec`).

Zusätzliche Namen in derselben `.env` (zu den Namen oben; `KAMERA_TOKEN_SECRET`, `QNAP_LAN_IP`, `GATEWAY_PORT` bleiben):

| Name | Dienst | Bedeutung |
|---|---|---|
| `KAMERA_HOST` | caddy, acme | **Pflicht.** Name des Gateways, `kameras.ep-kolar.at`. Site-Adresse und Zertifikatsname. |
| `ALIAS_ZONE` | acme | **Pflicht.** Zone bei deSEC, in der acme.sh den TXT-Eintrag setzt (z. B. eine eigene `….dedyn.io`-Zone). |
| `ALIAS_ART` | acme | `challenge` (Standard) = acme.sh `--challenge-alias`, CNAME-Ziel **mit** Präfix `_acme-challenge.<ALIAS_ZONE>`. `domain` = `--domain-alias`, CNAME-Ziel **ohne** Präfix (dann steht in `ALIAS_ZONE` genau das CNAME-Ziel). |
| `ACME_EMAIL` | acme | **Pflicht.** Konto-Adresse bei Let's Encrypt (Firmenadresse, kein Secret). |
| `DEDYN_TOKEN` | acme | **Pflicht, Secret.** deSEC-API-Token (so heißt die Variable in acme.sh `dnsapi/dns_desec.sh`). Nur in der `.env` und nur im acme-Container; acme.sh legt eine Kopie im Volume `acme_daten` ab (privat). Nie Repo/Chat/Log. |

Volumes: `acme_daten` (acme.sh-Konto), `kamera_zertifikate` (acme schreibt `kameras.pem` = fullchain, `kameras-key.pem`,
Marke `.erneuert`; caddy liest **nur**). Der acme-Container hat **keinen Port und keinen Docker-Socket**.

**Erneuerung ohne Timer:** Caddy liest Datei-Zertifikate nur beim Start; auch `caddy reload --force` erneuert den
Zertifikat-Zwischenspeicher nicht (caddyserver/caddy#6789, offen #6933). acme.sh prüft täglich (`acme.sh --cron`) und
erneuert bei Fälligkeit; danach schreibt sein `--reloadcmd` die Prüfsumme des neuen Zertifikats nach `/certs/.erneuert`.
`caddy_start.sh` sieht die geänderte Marke (Prüfung jede Minute), beendet Caddy sauber, `restart: unless-stopped` startet
den Container frisch mit dem neuen Zertifikat (~2 s Unterbrechung, etwa alle 60 Tage). `admin` bleibt aus.
**Kein wöchentlicher Cron auf der QNAP nötig.**

### Schritte für den Inhaber (einmalig, in dieser Reihenfolge)

1. **deSEC:** Konto auf desec.io anlegen → eine Zone anlegen (z. B. eigene `….dedyn.io`, das ist `ALIAS_ZONE`) →
   unter „Token" einen API-Token erzeugen (das ist `DEDYN_TOKEN`; nur in die `.env` auf der QNAP tippen).
2. **myNET (ep-kolar.at), CNAME:** `_acme-challenge.kameras.ep-kolar.at` CNAME `_acme-challenge.<ALIAS_ZONE>.`
   (bei `ALIAS_ART=domain`: CNAME direkt auf `<ALIAS_ZONE>.`). Den CNAME **dauerhaft stehen lassen** – er wird bei jeder
   Erneuerung wieder gebraucht (acme.sh-Wiki „DNS alias mode").
3. **myNET, A-Eintrag (Pflicht):** `kameras.ep-kolar.at` A `<QNAP-LAN-IP>`. Nötig für Geräte, die OPNsense umgehen
   (Android „Privates DNS", DoH im Browser) – die fragen das öffentliche DNS. Die LAN-Adresse ist von außen nicht erreichbar.
4. **OPNsense, Unbound-Host-Override (Pflicht):** Dienste → Unbound DNS → Überschreibungen: Host `kameras`, Domain
   `ep-kolar.at`, Typ A, Wert `<QNAP-LAN-IP>`. Grund: der **DNS-Rebind-Schutz** von OPNsense verwirft öffentliche Antworten mit
   privater Adresse – ohne Override bekämen normale LAN-Geräte **keine** Antwort. Der Override allein erreicht wiederum die
   Geräte mit „Privates DNS" nicht. Darum **beide** (3 und 4).
5. **QNAP:** `.env` um `KAMERA_HOST`, `ALIAS_ZONE`, `ACME_EMAIL`, `DEDYN_TOKEN` (ggf. `ALIAS_ART`) ergänzen, `chmod 600`.
   Die tls-internal-App stoppen (gleicher Port), dann `qnap-gateway-publiccert-inline.compose.yml` als App **`kamera-gateway`**
   anlegen. Der acme-Dienst stellt aus (einige Minuten; Fehlversuche wartet er 1 h ab – Ratenlimit), erst dann startet caddy
   (`depends_on … service_healthy`). Protokoll: `docker logs kamera-gateway-acme-1`.
6. **Prüfen** vom Büro-PC: `python scripts/kamera_zertifikat_pruefen.py` (Systemvertrauen, kein eigenes Stammzertifikat).
7. **Supabase:** Secret `KAMERA_GATEWAY_BASE` auf `https://kameras.ep-kolar.at:8443` umstellen (ohne Pfad). Die App-CSP
   erlaubt während des Übergangs beide Origins (Name und LAN-Adresse); der IP-Origin fällt in einer späteren Version weg.

### Abnahmekriterium (wörtlich)

> Von einem Gerät/Profil OHNE das Caddy-Stammzertifikat (z. B. das A55 oder ein frisches Chrome-Profil) liefert
> https://kameras.ep-kolar.at:8443/gesund „ok" ohne Zertifikatswarnung, Aussteller = eine öffentliche CA (Let's Encrypt),
> und der App-Abruf von epkolar.github.io = 200 ok. Erst dann „geht überall ohne Installation".

Zusätzlich am A55 **zweimal**: einmal mit **„Privates DNS"** aktiv (z. B. `dns.google` oder `1dot1dot1dot1.cloudflare-dns.com`)
und einmal in der Standardeinstellung – beide Male muss der Name aufgelöst werden und `/gesund` „ok" ohne Warnung liefern.
`scripts/kamera_zertifikat_pruefen.py` prüft Zertifikat (Systemvertrauen, Aussteller nicht „Caddy Local Authority"),
`/gesund` = „ok" mit CORS für `https://epkolar.github.io`, und meldet die DNS-Antwort des Systemresolvers und eines
öffentlichen DoH-Resolvers (erwartet: in beiden die QNAP-LAN-Adresse; der öffentliche Teil ist nur ein Bericht).
