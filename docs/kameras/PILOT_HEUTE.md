# Kamera-Pilot heute – Reihenfolge (19.11.2026)

Ziel: 2 Kameras (G3 Dome `g3_01` und `g3_lager03`) **nur intern** im Büro-Netz in der App sehen.
Mobotix, externer Zugang (WireGuard) und Aufzeichnungs-Wiedergabe sind **nicht** Teil des Pilots.
Vorlagen für den Video-Host: Ordner `C:/repos/epk-kamera-pilot/pilot-heute/` (außerhalb des Repos, dort stehen
die Kamera-Adressen). In diesem Repo stehen **keine** Adressen und **keine** Geheimnisse.
Stand: Datenmodell eingespielt (Tabellen leer), Edge Function `kamera-stream` deployt (Version 1, `verify_jwt`),
sie antwortet ohne Secrets absichtlich `503 nicht_konfiguriert`.

## a) Secret `KAMERA_TOKEN_SECRET` setzen
1. Supabase-Dashboard → Projekt → Edge Functions → Secrets → `KAMERA_TOKEN_SECRET` anlegen.
2. Wert: die Zeile `KAMERA_TOKEN_SECRET=` aus `C:/repos/epk-kamera-pilot/.env` auf diesem PC (nicht neu erzeugen –
   derselbe Wert muss in die `.env` des Video-Hosts). Kontrolle ohne Anzeige des Werts (PowerShell):
   `$v=(Select-String -Path C:\repos\epk-kamera-pilot\.env -Pattern '^KAMERA_TOKEN_SECRET=').Line.Substring(20); ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($v))) -replace '-','').Substring(0,8).ToLower()`
   → erwartet `5c83ca0b`.
3. Nie per Mail/Chat, nie ins Repo. Wechsel des Werts = alle ausgegebenen Tokens sofort ungültig.

## b) Video-Host hochfahren
1. VM auf dem Supermicro-Server (Debian 12 / Ubuntu 24.04), feste freie LAN-Adresse, NTP an
   (`timedatectl status` → synchronisiert; der Prüfer erlaubt nur 5 s Uhrversatz).
2. Docker Engine + Compose-Plugin (offizielles Docker-Repository).
3. Ordner `pilot-heute` nach `/opt/epk-kamera` kopieren (enthält den aktuellen Token-Prüfer `kamera-proxy-auth/`;
   **nicht** die ältere Kopie eine Ebene höher verwenden). `.env.beispiel` → `.env`, ausfüllen, `chmod 600 .env`.
   In der `.env` dieses PCs heißen die Kamera-Zugangsdaten noch `G3_USER`/`G3_PASS` → auf dem Host `KAM_USER`/`KAM_PW`.
4. TLS-Zertifikat nach `zertifikate/kamera.crt` + `kamera.key` (Weg siehe `Caddyfile`); interner DNS-Name
   (= `KAMERA_DOMAIN`) zeigt auf die VM (Host-Override auf der Firewall, Rebind-Schutz beachten).
5. Prüfen: `docker compose config >/dev/null && echo compose-ok` und
   `docker compose run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile`
6. Start: `docker compose up -d`, dann `docker compose ps` und `curl -s https://<name>/gesund` → `ok`.
7. Supabase-Secret `KAMERA_BACKEND_BASE` = `https://<name>` (ohne Pfad, ohne Schrägstrich am Ende).

## c) Kamera-Zugang (Wert nur in der `.env` des Hosts)
- **Weg A (heute):** direkt von der G3, RTSP-Pfad `/s0` (1080p) – am Gerät geprüft. `KAM_USER`/`KAM_PW` eintragen.
  Probe auf dem Host: `ffprobe -v error -rtsp_transport tcp -show_streams "rtsp://$KAM_USER:$KAM_PW@<kamera>:554/s0"`.
- **Weg B (Alternative):** Kamera in UniFi Protect adoptiert → dort RTSP einschalten, Token als `PROTECT_TOKEN_01/02`
  in die `.env`, in `go2rtc.yaml` die B-Zeile statt der A-Zeile aktivieren. Streamname bleibt gleich.
- Der Pilot holt nur das **Video** (kein Ton).

## d) Pilot-Kameras anmelden
1. `sql/KAMERA_PILOT_HEUTE_ENTWURF.sql` im SQL-Editor: zuerst den Probe-Block (BEGIN … ROLLBACK), dann einspielen.
   Ergebnis: 2 Kameras, 2 Stream-Zuordnungen, Regeln „Admin immer“ und „Büro Mo–Fr 07:00–17:00“.
2. Namen, Standorte und Regeln lassen sich danach in der App ändern (Kameras → Verwaltung). Die **Stream-Zuordnung**
   (`kamera_backend`) kann die App absichtlich nicht schreiben – nur dieses SQL.
3. Sichtbar wird der Bereich in der App nur im Testbetrieb: Admin, `system_config.kameras_testumgebung = true`
   (Eintrag fehlt heute – eigene Entscheidung des Inhabers) und App mit `?kameras_test=1`. Produktionsschalter bleibt AUS.
4. Rücknahme: `sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql` (oder Kameras in der App auf inaktiv).

## e) Ende-zu-Ende prüfen
`docs/kameras/PILOT_TESTLISTE.md` vollständig durchgehen und jedes Ergebnis eintragen. Erst wenn alle Punkte das
erwartete Ergebnis zeigen, gilt der Pilot als bestanden.
