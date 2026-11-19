# Kamera-Pilot – Reihenfolge am QNAP-Gateway (20.11.2026)

Ziel: die 4 UniFi G3 (`cam37`, `cam38`, `cam39`, `hochregal01`) **nur live** und **nur intern** in der App sehen.
Kamera-Server = **QNAP EP-KOLAR-QNAP**: go2rtc läuft dort in Container Station (Host-Netz, Port 1984), Quelle RTSP `/s0`.
Der Browser holt WebRTC (WHEP) bzw. Einzelbild über den Prüf-Proxy (Caddy + kamera-auth) auf der QNAP – nie RTSP.
Surveillance Station und die Aufnahmen der QNAP bleiben **unberührt (TABU)**; es gibt keine Aufzeichnung in der App.
In diesem Repo stehen **keine** Adressen und **keine** Geheimnisse. Alte Vorlage (nicht starten, kein
`docker compose up`): `C:/repos/epk-kamera-pilot/pilot-heute/` – „Vorlage – der Kamera-Server ist die QNAP“.
Stand: Datenmodell eingespielt, Edge Function `kamera-stream` deployt (`verify_jwt`); ohne Secrets antwortet sie
absichtlich `503 nicht_konfiguriert` (App: „Kamera-Server noch nicht in Betrieb“).

## a) Secret `KAMERA_TOKEN_SECRET` (Mensch, Supabase-Dashboard)
1. Dashboard → Edge Functions → Secrets → `KAMERA_TOKEN_SECRET`. Wert = Zeile `KAMERA_TOKEN_SECRET=` aus
   `C:/repos/epk-kamera-pilot/.env` (nicht neu erzeugen – derselbe Wert gehört in die kamera-auth-Umgebung auf der QNAP).
   Kontrolle ohne Anzeige (PowerShell):
   `$v=(Select-String -Path C:\repos\epk-kamera-pilot\.env -Pattern '^KAMERA_TOKEN_SECRET=').Line.Substring(20); ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($v))) -replace '-','').Substring(0,8).ToLower()`
   → erwartet `5c83ca0b`.
2. Nie per Mail/Chat, nie ins Repo. Wechsel des Werts = alle ausgegebenen Tokens sofort ungültig.

## b) Zertifikat + DNS (Sebastian)
1. Interner DNS-Name des Gateways (Host-Override auf FW-KOLAR01, Rebind-Schutz beachten) zeigt auf die QNAP.
2. TLS-Zertifikat für genau diesen Namen (Firmen-Wildcard o. ä.) bereitstellen; NTP auf der QNAP an
   (der Prüfer erlaubt nur 5 s Uhrversatz).

## c) Prüf-Proxy auf der QNAP (Chat-Claude)
1. Caddy + kamera-auth vor go2rtc, Vorlage `tools/kamera-proxy-auth/vorlagen/Caddyfile` (auf der QNAP:
   `reverse_proxy` auf den lokalen go2rtc-Port 1984). Nur `/live/<stream>/whep`, `/live/<stream>/snapshot.jpg`, `/live/<stream>/mjpeg`,
   `/gesund` – alles andere 404, go2rtc-Port 1984 nie nach außen. WebRTC-Medien: Port 8555 (TCP+UDP) im LAN.
2. Abschottung: nur die QNAP darf die G3 erreichen (`KAMERAS_ABSICHERN.md` im Vorlagen-Ordner). Zugangsdaten nur als
   `KAM_USER`/`KAM_PW` in der Umgebung auf der QNAP.
3. Ergebnis an CC/Sebastian: Gateway-URL `https://<name>` und `curl -s https://<name>/gesund` → `ok`.

## d) Gateway-Adresse setzen und Kameras anmelden
1. **Mensch** im Dashboard: Secret `KAMERA_GATEWAY_BASE` = `https://<name>` (nur https, ohne Schrägstrich am Ende).
   Der alte Name `KAMERA_BACKEND_BASE` wird nur gelesen, wenn `KAMERA_GATEWAY_BASE` fehlt.
2. Sebastian im SQL-Editor: zuerst `sql/KAMERA_GATEWAY_SEED_PROBE.sql` (BEGIN … ROLLBACK; Ergebnis in der Meldung
   `PROBE_ERGEBNIS …`, jede Zeile `OK`), dann `sql/KAMERA_GATEWAY_SEED_ENTWURF.sql` (BEGIN … COMMIT).
   Ergebnis: 4 Kameras, 4 Zuordnungen in `kamera_backend` (ID = Streamname), Regeln „Admin immer“ und
   „Büro Mo–Fr 07:00–17:00“. Anzeigenamen sind vorläufig („Kamera .37 (Name folgt)“) – echte Namen in der App setzen.
3. Abgelöst: `sql/KAMERA_PILOT_HEUTE_ENTWURF.sql` / `sql/KAMERA_PILOT_HEUTE_PROBE.sql` (nie beide). War der Pilot
   eingespielt, bricht der Gateway-Seed ab → zuerst `sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql`.
4. Mobotix (`mob32`…`mob36`): zweiter Block im Seed, Standard AUS (Schalter `epk.mobotix_aktiv`). Jeder Mobotix-Stream
   kostet eine ffmpeg-Umwandlung auf der QNAP-CPU (1024x768 MJPEG → H.264): einzeln einschalten, QNAP-CPU beobachten.
5. Rücknahme: `sql/KAMERA_GATEWAY_SEED_RUECKNAHME.sql` (oder Kameras in der App auf inaktiv).

## e) Ende-zu-Ende prüfen
`docs/kameras/PILOT_TESTLISTE.md` vollständig durchgehen und jedes Ergebnis eintragen. Erst wenn alle Punkte das
erwartete Ergebnis zeigen, gilt der Pilot als bestanden. Sichtbar ist der Bereich „Kameras“ nur für den **Admin**;
der Produktionsschalter für weitere Rollen bleibt AUS, bis die Testliste bestanden ist.
