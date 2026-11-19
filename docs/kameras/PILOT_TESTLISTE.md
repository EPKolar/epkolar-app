# Kamera-Pilot – Testliste Ende-zu-Ende (19.11.2026)

Gehört zu `docs/kameras/PILOT_HEUTE.md` (Schritt e). Jeder Punkt: **Wie** testen, **erwartet** genau dieses Ergebnis.
Abweichung = Pilot nicht bestanden, Ergebnis notieren und melden. Keine Tokens/Passwörter in Dateien speichern –
nur in der Shell halten (Tokens verfallen nach höchstens 120 s, Standard 90 s).

## Vorbereitung (Shell auf einem PC im Büro-Netz)

```
F=https://<projekt>.supabase.co/functions/v1/kamera-stream   # Supabase-Projekt-URL
ANON=<anon-key>                                                # öffentlicher Schlüssel (steht auch in der App)
D=https://<name-des-video-hosts>                               # = KAMERA_BACKEND_BASE
# JWT holen (Kennwort nicht in die Verlaufsdatei: read -s)
jwt() { read -s -p "Kennwort $1: " PW; echo; curl -s "https://<projekt>.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: $ANON" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$PW\"}" \
  | sed -E 's/.*"access_token":"([^"]+)".*/\1/'; unset PW; }
ADMIN=$(jwt <admin-mail>); BUERO=$(jwt <buero-mail>); MONTEUR=$(jwt <monteur-mail>)
ruf() { curl -s -w ' HTTP %{http_code}\n' -X POST "$F" -H "apikey: $ANON" -H "Authorization: Bearer $1" \
  -H 'Content-Type: application/json' -d "$2"; }
```

| # | Test | Wie | Erwartet |
|---|---|---|---|
| 1 | Live-Bild Admin | App als Admin mit `?kameras_test=1` öffnen → Reiter „Kameras“ → Kachel „Elektrolager 03“ und „G3 Dome 01“ | Bewegtes Bild in ≤ 5 s, kein „Kamera nicht erreichbar“. Gegenprobe Funktion: `ruf "$ADMIN" '{"kamera_id":"kam_g3_lager03"}'` → `HTTP 200`, `"typ":"webrtc"`, `webrtcUrl` beginnt mit `$D/live/g3_lager03/whep?token=` |
| 2 | Monteur: kein Reiter | App als Monteur normal **und** mit `?kameras_test=1` öffnen | Kein Reiter „Kameras“, kein Abruf |
| 3 | Monteur: Funktion | `ruf "$MONTEUR" '{"kamera_id":"kam_g3_lager03"}' \| tee m.txt; grep -c 'live/' m.txt` | `{"error":"kein_zugriff"} HTTP 403`, `grep` zählt `0` (keine Adresse, kein Streamname) |
| 4 | Monteur: Zuordnung | `curl -s -w ' %{http_code}\n' "https://<projekt>.supabase.co/rest/v1/kamera_backend?select=*" -H "apikey: $ANON" -H "Authorization: Bearer $MONTEUR"` | Fehler `permission denied` (HTTP 401/403), nie ein Streamname. Dasselbe mit `$ADMIN`: ebenfalls verweigert |
| 5 | Ohne Token → 401 | `curl -s -o /dev/null -w '%{http_code}\n' "$D/live/g3_lager03/snapshot.jpg"` und `curl -s -o /dev/null -w '%{http_code}\n' -X POST "$D/live/g3_lager03/whep"` | `401` und `401` |
| 6 | Gefälschter Kopf → 403 | Admin-Token für `g3_01` holen: `T=$(ruf "$ADMIN" '{"kamera_id":"kam_g3_01"}' \| sed -E 's/.*token=([^"&]+).*/\1/')`, dann `curl -s -o /dev/null -w '%{http_code}\n' -H "X-Forwarded-Uri: /live/g3_01/snapshot.jpg?token=$T" -H "X-Original-URI: /live/g3_01/snapshot.jpg?token=$T" "$D/live/g3_lager03/snapshot.jpg?token=$T"` | `403` (Caddy überschreibt den Kopf, Token passt nicht zum Stream), nie ein Bild |
| 7 | Falscher Stream → 403 | `curl -s -o /dev/null -w '%{http_code}\n' "$D/live/g3_lager03/snapshot.jpg?token=$T"` (Token aus 6) | `403` |
| 8 | Token abgelaufen → 401 | Test 7 mit `.../g3_01/snapshot.jpg?token=$T` sofort (→ `200`, Bild) und nach 2 min erneut | erst `200`, nach 2 min `401` |
| 9 | Interne Oberflächen → 404 | `for p in /api/streams /api/webrtc / /api/config; do curl -s -o /dev/null -w "$p %{http_code}\n" "$D$p"; done`; `curl -s "$D/gesund"` | alle `404`; `/gesund` → `ok` |
| 10 | Zeitfenster Büro (außerhalb) | Samstag/Sonntag oder Mo–Fr vor 07:00 / ab 17:00: `ruf "$BUERO" '{"kamera_id":"kam_g3_lager03"}'`. Ist gerade Fensterzeit: SQL-Probe aus `sql/KAMERA_PILOT_HEUTE_ENTWURF.sql` (Zeitpunkte Sa 10:00, Mo 06:59, Mo 17:00) | `{"error":"kein_zugriff"} HTTP 403`, keine Adresse. SQL-Probe: `false`/`false`/`false` |
| 11 | Zeitfenster Büro (innerhalb) | Mo–Fr 07:00–16:59: derselbe Aufruf | `HTTP 200`, `"typ":"webrtc"`. (Büro hat im Testbetrieb **keinen** Reiter – nur der Admin sieht den Bereich; geprüft wird hier die Funktion) |
| 12 | Aufnahme-Bereich außerhalb Fenster | **In** der Fensterzeit als Büro einen vergangenen Bereich außerhalb anfragen, z. B. gestern 17:30–18:30: `ruf "$BUERO" '{"kamera_id":"kam_g3_lager03","scope":"aufzeichnung","geraet":"pc","von":"<gestern>T17:30:00+01:00","bis":"<gestern>T18:30:00+01:00"}'` | `{"error":"kein_zugriff"} HTTP 403`. Gegenprobe gestern 08:00–09:00 → `HTTP 200` mit `aufzeichnungUrl` (Wiedergabe am Proxy folgt erst in Phase 3 → dort `404`) |
| 13 | Aufnahme Monteur | `ruf "$MONTEUR" '{"kamera_id":"kam_g3_lager03","scope":"aufzeichnung","geraet":"pc","von":"…","bis":"…"}'` | `HTTP 403 kein_zugriff` |
| 14 | Zugriffsprotokoll | SQL-Editor: `select ts, user_id, kamera_id, scope, ergebnis, grund from public.kamera_abruf_log order by ts desc limit 30;` | Zeilen zu den Tests: Admin `erteilt`/`ok`; Monteur `abgelehnt`/`rolle` (kamera_id leer); Büro außerhalb `abgelehnt`/`regel`; Bereich `abgelehnt`/`bereich`; Büro innerhalb `erteilt`. Für 401-Fälle am Proxy gibt es keine Zeile (die stehen nur im Proxy-Protokoll) |
| 15 | Keine Tokens im Proxy-Protokoll | auf dem Host: `docker compose exec caddy sh -c 'grep -c "token=" /protokoll/zugriff.log'` | `0` |
| 16 | Prüfer-Protokoll | auf dem Host: `docker compose logs kamera-auth --tail 30` (mit `KAMERA_AUTH_LOG=1`) | je Anfrage Zeit, Status (204/401/403), Stream, Nutzer-ID – **nie** ein Token |

Ergebnis je Zeile mit Datum/Uhrzeit notieren. Nach dem Pilot: Messwerte (CPU, RAM, Netz, Speicher) laut
`C:/repos/epk-kamera-pilot/PILOT.md` Abschnitt 8.
