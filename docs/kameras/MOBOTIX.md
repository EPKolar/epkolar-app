# Mobotix am Kamera-Gateway (5 Stück) – Schritte

Stand 21.11.2026. Alle fünf Mobotix (Endungen .32–.36 im Kamera-Netz) sind von der QNAP aus erreichbar (gemessen
Chat-Claude, zeitweise wackelig). Mobotix kann **kein RTSP** → go2rtc holt das HTTP-MJPEG und reicht es **ohne
Umwandlung** durch (kein ffmpeg, die ARM-CPU der QNAP nimmt bereits auf). In der App: `stream_typ` `mjpeg`.

| Stream / Kamera-ID | Endung | Surveillance Station | Anzeigename |
|---|---|---|---|
| `hof01` | .32 | Hof | Hof |
| `hochregal03` | .33 | Hochregal03 | Hochregal 03 |
| `hochregal02` | .34 | Hochregal02 | Hochregal 02 |
| `elektrolager01` | .35 | Elektrolager01 | Elektrolager 01 |
| `elektrolager02` | .36 | Elektrolager02 | Elektrolager 02 |

**Eine Quelle:** `tools/kamera-proxy-auth/qnap/go2rtc.yaml` (Streamnamen + Quellen, nur Platzhalter) und
`sql/KAMERA_MOBOTIX_SEED_*.sql`. Riegel: `tests/test_kamera_mobotix_v1090.py`. Der alte Mobotix-Block
(`mob32`…`mob36`) in `sql/KAMERA_GATEWAY_SEED_ENTWURF.sql` ist abgelöst – Schalter bleibt `false`.

## 1. Lese-Benutzer auf jeder Mobotix (Mensch)
Ein Benutzer „nur Live-Ansicht“, **gleiches Paar auf allen fünf**. Werte nie in Repo, Chat oder App.

## 2. kam.env auf der QNAP (`/share/Container/go2rtc/kam.env`, chmod 600)
Nur Namen hier, Werte nur dort. go2rtc ersetzt `${NAME}` beim Start aus der Umgebung; fehlt ein Name, bleibt der
Platzhalter stehen und genau dieser Stream fällt aus.

| Name | Inhalt |
|---|---|
| `MOBOTIX_USER` / `MOBOTIX_PASS` | Lese-Benutzer der Mobotix (neu) |
| `GO2RTC_USER` / `GO2RTC_PASS` | Anmeldung an der go2rtc-API (neu, gilt für ALLE 9 Streams); Caddy bekommt dasselbe Paar als `GO2RTC_BASIC` (`tools/kamera-proxy-auth/qnap/ENV.md`) |
| `KAM_USER` / `KAM_PASS` | Zugang der G3 (wie bisher) |
| `QNAP_LAN_IP` | LAN-Adresse der QNAP (WebRTC-Candidate `:8555`) |
| `CAM_HOF01_IP`, `CAM_HOCHREGAL03_IP`, `CAM_HOCHREGAL02_IP`, `CAM_ELEKTROLAGER01_IP`, `CAM_ELEKTROLAGER02_IP` | Mobotix-Adressen (Endung .32/.33/.34/.35/.36) |
| `CAM_HOCHREGAL01_IP`, `CAM_VERKAUF02_IP`, `CAM_ELEKTROLAGER03_IP`, `CAM_CAM39_IP` | G3-Adressen (Endung .61/.38/.37/.39 – dieselben wie in der laufenden go2rtc.yaml) |

## 3. go2rtc.yaml ersetzen (Chat-Claude auf der QNAP)
Reihenfolge: **zuerst** Gateway-`.env` um `GO2RTC_BASIC` ergänzen (Einzeiler in `ENV.md`) und Caddy neu starten –
go2rtc ohne Anmeldung ignoriert den Kopf, es bricht also nichts. **Dann** go2rtc mit der neuen Vorlage.
Die Vorlage schaltet die Basic-Anmeldung für die ganze HTTP-API ein (`api: username/password`) und den RTSP-Server
aus (`rtsp: listen: ""`, Frigate ist abgeschaltet). WebRTC-Medien (:8555) sind davon nicht betroffen.
go2rtc lässt Anfragen von localhost **ohne** Anmeldung durch → die Firewall-Sperre für `:1984` bleibt Pflicht.

1. Laufende `/config/go2rtc.yaml` sichern (`go2rtc.yaml.vor-mobotix`). Abschnitte `api:`/`webrtc:` vergleichen –
   weicht die laufende Datei dort ab, die laufenden Werte übernehmen.
2. Vorlage `tools/kamera-proxy-auth/qnap/go2rtc.yaml` **unverändert** als `/config/go2rtc.yaml` einsetzen,
   go2rtc-App neu starten. Keine Handarbeit an Streamnamen – Änderungen nur im Repo (Riegel).
3. Pfad: zuerst `/cgi-bin/faststream.jpg?stream=full&needlength&fps=12`. Liefert eine Kamera dort nichts (404 oder
   kein Bild), **nur in der Vorlage** für diese Kamera `/control/faststream.jpg?stream=full&needlength&fps=12` setzen.
   Anmeldung: go2rtc nimmt die Zugangsdaten aus der URL (Basic; Digest laut go2rtc-Quellcode ebenfalls) – bei 401
   trotz richtigem Paar melden, nicht auf ffmpeg ausweichen.

**Bedarfsbetrieb (gewollt):** go2rtc verbindet eine Kamera erst, wenn jemand zusieht, und trennt, wenn der letzte
geht. Bricht eine wackelige Kamera ab, verbindet go2rtc neu, solange jemand zusieht (1 s, ab Versuch 5 alle 5 s,
ab 10 alle 10 s, ab 20 jede Minute). Kein `preload`, kein ffmpeg – sonst zögen alle fünf dauernd Bilder.
Quellen: go2rtc `internal/http/README.md` („[MJPEG] stream will be proxied without modification“),
`internal/mjpeg/README.md` (`/api/stream.mjpeg`: „The source must contain the MJPEG codec“),
`internal/app/README.md` (Umgebungsvariablen), `internal/streams/producer.go` (Neuverbindung).

## 4. Prüfen auf der QNAP
```
docker run --rm --network host --env-file /share/Container/go2rtc/kam.env -v /share/Container/go2rtc:/pruef:ro \
  python:3.12-alpine python /pruef/go2rtc_streams_pruefen.py
```
Ohne Adresse nimmt das Skript `http://$QNAP_LAN_IP:1984` (LAN-Adresse – nur dort wirkt die Anmeldung; localhost
geht nur mit `--nur-streams`). Es prüft zuerst: `/api/streams` **ohne** Anmeldung und mit den wörtlichen Platzhaltern
→ 401, **mit** `GO2RTC_USER`/`GO2RTC_PASS` → 200. Zugangsdaten nur aus der Umgebung, nie ausgegeben.
(`scripts/go2rtc_streams_pruefen.py` vorher nach `/share/Container/go2rtc/` kopieren.) Das Skript öffnet je Stream
kurz einen Zuschauer (Mobotix `/api/stream.mjpeg`, G3 `/api/stream.mp4` – keine Umwandlung), liest bei offener
Verbindung `/api/streams` und wiederholt alle 3 s bis 30 s. **Exit 0** = alle 9 Streams hatten einmal einen
verbundenen Erzeuger. `FEHLT <name>` = genau diese Kamera/Variable prüfen. Ausgabe enthält nie Adressen.

Einzelbild über das Gateway (Chat-Claude, Büro-PC, mit Token aus der App – nicht im Skript, braucht ein Token):
`https://<QNAP-LAN-IP>:8443/live/hof01/snapshot.jpg?token=…` → Bild; ohne Token → 401. Kommt mit Token 401/502,
fehlt meist `GO2RTC_BASIC` bei Caddy (go2rtc lehnt ab).

## 5. Datenbank (Sebastian, SQL-Editor)
1. `sql/KAMERA_MOBOTIX_SEED_PROBE.sql` – jede Zeile `OK` (Ergebnis steht in der Fehlermeldung `PROBE_ERGEBNIS`).
2. `sql/KAMERA_MOBOTIX_SEED_ENTWURF.sql` – NACHHER `Mobotix: 5/5/10`.
3. App → Kameras: Admin sieht 9 Kacheln; die fünf Mobotix zeigen ein laufendes Bild (`/live/<s>/mjpeg`).
Zurück: `sql/KAMERA_MOBOTIX_SEED_RUECKNAHME.sql` (nur die fünf, die G3 bleiben).
