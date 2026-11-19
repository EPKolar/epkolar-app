# Kameras Phase 2 – Sicherheitsnachweis (19.11.2026)

Stand: Zweig `feature/kameras-phase2`. Zeilenangaben für `verify.mjs`, `token.mjs`, `logic.ts`, `index.ts`, `vektoren.json`
und `sql/KAMERAS_v1_ENTWURF.sql` beziehen sich auf **110678f** (in diesem Commit unverändert); Zeilen der Vorlagen
und Tests auf den Commit, der diese Datei einführt. Nichts ist deployt, keine Datenbank berührt, Schalter in Produktion AUS.

Kurzfassung: **eine** Quelle für Pfad und Methode (vom Proxy gesetzt), **kein** Rückfall, die Kamera steckt
**signiert** im Token und wird gegen genau den Pfad geprüft, den der Proxy anschließend bedient. Ein Monteur endet
in der Edge Function **vor** jeder Kamera- oder Backend-Abfrage.

---

## a) Genau EIN vertrauenswürdiger Kopf, gesetzt vom Proxy

| Stelle | Inhalt |
|---|---|
| `tools/kamera-proxy-auth/verify.mjs:40` | `KOPF_PAARE` – nur zwei zulässige Paare: `x-forwarded-uri`+`x-forwarded-method` (Caddy) oder `x-original-uri`+`x-original-method` (nginx) |
| `verify.mjs:43-50` | `ladeKopfConfig(env)` liest `KAMERA_AUTH_URI_HEADER` / `KAMERA_AUTH_METHOD_HEADER`; ungültig oder nicht passendes Paar → `null`; alle Köpfe des **anderen** Paares landen in `fremd` |
| `verify.mjs:171-176` | ohne gültige Kopf-Konfiguration bricht der Dienst den Start ab (Exitcode 1) |
| `verify.mjs:96` | `entscheide()` ohne Konfiguration → 403 |
| `verify.mjs:98` | `for (const k of cfg.fremd) if (h[k] !== undefined) return nein(403);` – jeder Kopf des nicht konfigurierten Paares (auch leer) = eingeschleust → 403 |
| `verify.mjs:99` | `const uri = kopf(h, cfg.uriHeader);` – **einzige** Stelle, an der der Originalpfad gelesen wird |
| `verify.mjs:108` | `const methodeRoh = kopf(h, cfg.methodHeader);` – **einzige** Stelle für die Methode |
| `verify.mjs:105` | Kamera/Art ausschließlich aus diesem Pfad: `const ziel = pfadArt(pfad);` |

Was der Client sonst noch liefern darf, ist **nur das Token** (`verify.mjs:115-131`: Query `token`, `X-Kamera-Token`,
`Authorization: Bearer`, Cookie `kam_t`). Daraus wird **kein** Ziel abgeleitet – das Token wird nur gegen das aus dem
Proxy-Kopf gelesene Ziel geprüft (`verify.mjs:136`).
`req.url` wird nur an einer Stelle benutzt: `verify.mjs:181` für den Gesundheitsabruf `/gesund`, und zwar nur, wenn
**kein** Proxy-Kopf dabei ist; dieser Zweig ruft `entscheide()` nie auf und gibt nur `ok` zurück.

Die Proxys setzen den vertrauenswürdigen Kopf selbst und räumen Client-Kopien weg:

| Vorlage | Zeile | Inhalt |
|---|---|---|
| `tools/kamera-proxy-auth/vorlagen/nginx.conf` | 27 | `underscores_in_headers off;` (kein `X_Original_URI`-Schmuggel) |
| `vorlagen/nginx.conf` | 36-47 | `location = /_kamera_pruefen { internal; … }` |
| `vorlagen/nginx.conf` | 42-43 | `proxy_set_header X-Original-URI $request_uri;` / `X-Original-Method $request_method;` – **überschreibt** Client-Kopien |
| `vorlagen/nginx.conf` | 45-46 | `proxy_set_header X-Forwarded-Uri "";` / `X-Forwarded-Method "";` – Client-Kopien des anderen Paares entfernt |
| `vorlagen/Caddyfile` | 81-88, 102-109, 121-128 | jedes `forward_auth`: `header_up -X-Original-URI`, `header_up -X-Original-Method`, `header_up X-Forwarded-Uri {http.request.orig_uri}`, `header_up X-Forwarded-Method {http.request.orig_method}` (Caddy setzt X-Forwarded-* ohnehin selbst; hier zusätzlich ausdrücklich) |

Geprüft durch `tests/test_kameras_phase2_v1056.py`: `test_pruefer_liest_kopfnamen_nie_fest` (Z. 342, statisch:
kein fest verdrahteter Kopfname, kein `req.url`-Rückfall), `test_kopf_konfiguration_ist_pflicht_und_paarweise`,
`test_dienst_startet_nicht_ohne_kopfkonfiguration` (Z. 450), `test_vorlagen_raeumen_client_koepfe_ab` (Z. 480),
`test_snippets_raeumen_client_koepfe_ab` (README).

## b) Kein Rückfall, fehlende Quelle = 403

Die alte Zeile `const uri = fwd || orig || String(req.url || "");` existiert nicht mehr. Heute (`verify.mjs:99-101`):

```
  const uri = kopf(h, cfg.uriHeader);
  if (uri === null || uri === "") return nein(403);
  if (uri.length > MAX_URI || uri.charAt(0) !== "/") return nein(403);
```

Methode (`verify.mjs:108-110`):

```
  const methodeRoh = kopf(h, cfg.methodHeader);
  if (methodeRoh === null || methodeRoh === "") return nein(403, { art: ziel.art, s: ziel.s });
  const methode = methodeRoh.toUpperCase();
```

`kopf()` (`verify.mjs:71-75`) liefert `null` bei doppeltem Kopf → ebenfalls 403. Kein Weg führt ohne
konfigurierten Kopf zu 204. Test: `test_angriff_eingeschleuster_kopf_und_kein_rueckfall` (Z. 325, `R["direkt"] == 403`).

## c) Kamera im signierten Token = geprüfte Kamera = bediente Kamera

Kette eines einzigen Wertes `s` (Streamname):

| # | Station | Stelle | Form von `s` |
|---|---|---|---|
| 1 | DB: `kamera_backend.stream_name` | `sql/KAMERAS_v1_ENTWURF.sql:85` | CHECK `^[A-Za-z0-9_-]{1,64}$` |
| 2 | Edge Function liest ihn (service_role) | `index.ts:50-51`, `logic.ts:341-342` | – |
| 3 | nochmals geprüft | `logic.ts:343` `if (!ziel \|\| !ID_RE.test(ziel)) return … 503` mit `ID_RE` aus `logic.ts:35` | gleiche Zeichenklasse |
| 4 | signiert ins Token | `logic.ts:353` `s: ziel,` → HMAC-SHA256 über das Payload (`logic.ts:360`, Prüfung `logic.ts:188`) | unveränderbar ohne Secret |
| 5 | in die Adresse | `logic.ts:130-136` `basis + "/live/" + ziel + "/" + <art> + "?token=" + token` | **roh** (Zeichenklasse braucht keine Kodierung) |
| 6 | Proxy reicht den Originalpfad weiter | nginx `$request_uri` (`vorlagen/nginx.conf:42`), Caddy `{http.request.orig_uri}` (`vorlagen/Caddyfile:85`) | roh, unverändert |
| 7 | Prüfer zerlegt den Pfad | `verify.mjs:52-55` (`STREAM = [A-Za-z0-9_-]{1,64}`), `verify.mjs:58-69` `pfadArt` | gleiche Zeichenklasse, Anker `^…$` |
| 8 | Prüfer bindet | `verify.mjs:136` `pruefeToken(secret, token, nowMs, { s: ziel.s, sc: ziel.sc })` → `token.mjs` bzw. `logic.ts:203` `if (… p.s !== erwartet.s) return null;` (exakter String-Vergleich), Art `logic.ts:204` | – |
| 9 | Proxy bedient | Caddy: Fang-Gruppe aus `path_regexp` (`vorlagen/Caddyfile:78/99/118`) → `rewrite * /api/…?src={re.<name>.1}` (`:93/110/129`); nginx: `rewrite ^/live/([A-Za-z0-9_-]{1,64})/… /api/…?src=$1` (`vorlagen/nginx.conf:63/71/78`) | gleiche Zeichenklasse |
| 10 | go2rtc löst `src` → Kameraquelle | nur `go2rtc.yaml` auf dem Host (Admin-Konfiguration, nicht vom Client steuerbar) | – |

Wo könnten Prüfer-Sicht (roher Pfad, Schritt 6–8) und bediente Sicht (Schritt 9) auseinanderlaufen, und warum nicht:

| Abweichung | Risiko | Abwehr |
|---|---|---|
| **URL-Kodierung** (`/live/g3%5f38/…`) | Proxy dekodiert zum Routen, Prüfer sähe kodiert | `verify.mjs:60` – jedes `%` im Pfad → 403 (Vektor `kodiert`, `vektoren.json:352`) |
| **`..` / Pfad-Normalisierung** (`/live/g3_37/hls/../../g3_38/…`) | nginx `$uri` und Caddy normalisieren, `$request_uri` nicht | `verify.mjs:60` – `..` → 403 (Vektor `punktpunkt`, `:346`) |
| **doppelte Schrägstriche** (`/live//g3_37/…`) | `merge_slashes` | `verify.mjs:60` – `//` → 403 (Vektor `doppelslash`, `:358`) |
| **Groß/Klein** | Proxy-Regex case-insensitive? | Prüfer exakt (`logic.ts:203`), Vorlagen case-sensitiv: nginx `~` (nicht `~*`), Caddy `path_regexp` ohne `(?i)`; Vektor `stream_gross` (`:125`) |
| **Präfix** (`g3_3` vs `g3_37`) | Teilwort-Treffer | Anker `^…$` in `verify.mjs:54-55`, exakter Vergleich; Vektor `stream_praefix_im_pfad` (`:297`) |
| **fremder Stream im Pfad** | Token für A, Pfad B | 403 (`verify.mjs:137`); Vektor `anderer_stream_im_pfad` (`:291`) |
| **Unterpfade / API** (`/live/g3_37/api/streams`) | go2rtc-API durchreichen | nur die festen Formen aus `verify.mjs:54-55`; Vektor `go2rtc_api_ueber_live` (`:340`); Proxy-Fallback 404 (`vorlagen/nginx.conf:84`, `vorlagen/Caddyfile:162`) |
| **Nicht-ASCII, `;`, Leerzeichen, `\`** | unterschiedliche Parser | Zeichenklasse lässt nur `A-Za-z0-9_-` zu → 403 |
| **Query vom Client an go2rtc** | `src` per Query überschreiben | beide Proxys ersetzen die **ganze** Adresse beim `rewrite`; die Client-Query (inkl. Token) erreicht go2rtc nicht |
| **Kopf statt Pfad** (Befund HIGH, 110678f) | Client spielt dem Prüfer Pfad A per Kopf vor | Abschnitt a) + Umkehrprobe unten |
| **go2rtc-Alias** (`mx_32: g3_37` in der yaml) | anderer Stream hinter gleichem Namen | nur Admin-Konfiguration auf dem Host, nicht Client-erreichbar; Kontrolle beim Pilot |

Unter diesen Regeln ist der rohe Pfad, den der Prüfer sieht, zeichengleich mit dem normalisierten Pfad, nach dem der
Proxy routet – alles, wo sie abweichen könnten, enthält `%`, `..`, `//` oder Zeichen außerhalb der Klasse und endet
mit 403. **Vor Ort zu bestätigen** (PILOT.md Abschnitt 9): `curl` mit `%5f`, `..`, `//` und Großschreibung gegen den
echten Proxy → jeweils 401/403/404, nie ein Bild.

## d) Monteur bekommt serverseitig keinen Stream

| Schritt | Stelle |
|---|---|
| JWT prüfen | `logic.ts:285-291` (`deps.authUser(jwt)`) |
| Nutzerzeile aktiv/nicht gesperrt | `logic.ts:293-295` |
| **harte Rollenliste** – Monteur, Helfer, Techniker, Obermonteur, Display, Terminal enden hier | `logic.ts:297-302` (`if (ERLAUBTE_ROLLEN.indexOf(rolle) < 0) … 403 kein_zugriff`) |
| erst danach: Regelabfrage DB | `logic.ts:333-334` (`deps.darfSehen`) |
| erst danach: Backend-Zuordnung (Streamname, Typ) | `logic.ts:340-344` (`deps.ladeBackend`) |
| Verdrahtung: `ladeBackend` nur über den Service-Client, nur aus `bearbeite()` | `index.ts:50-51`; einziger Einstieg `index.ts:66` → `bearbeite` |
| DB: `kamera_backend` ohne Policy, keine Rechte für anon/authenticated | `sql/KAMERAS_v1_ENTWURF.sql` (`revoke all on public.kamera_backend from authenticated;`, RLS an) |

Tests (Monteur):
- `tests/test_kameras_phase1_v1055.py`: `test_andere_rollen_403_ohne_adresse_und_ohne_abfrage` (Z. 312, prüft `darf == 0` und `backend == 0`),
  `test_monteur_mit_eigener_nutzerfreigabe_bleibt_draussen` (Z. 321), `test_monteur_auch_bei_aufzeichnung_und_tippfehler_in_der_konfig` (Z. 328),
  `test_monteur_und_helfer_sehen_nichts_und_rufen_nichts_ab` (Z. 822, App ruft nichts ab),
  Umkehrproben `test_umkehrprobe_ohne_rollensperre_fragt_monteur_die_db` (Z. 487), `test_umkehrprobe_ohne_rollenpruefung_wuerde_monteur_abrufen` (Z. 884).
- `tests/test_kameras_phase2_v1056.py`: `test_typ_erst_nach_voller_pruefung` (Z. 245, Monteur mit mjpeg/snapshot-Kamera: 403, kein Typ, `backend == 0`, `darf == 0`),
  `test_umkehrprobe_typ_vor_pruefung_wuerde_monteur_verraten` (Z. 549), `test_monteur_weiterhin_nichts` (Z. 640).

---

## Umkehrprobe (Pflichtnachweis)

Ziel: zeigen, dass die Angriffstests den Befund wirklich erkennen. Dafür wird **in einer Kopie** des Arbeitsbaums
(Scratch-Ordner, nicht der Zweig) `verify.mjs` auf das alte Verhalten vor 110678f zurückgesetzt – Pfad aus
`X-Forwarded-Uri` **oder** `X-Original-URI` **oder** `req.url`, Methode ebenso, kein Fremdkopf-Riegel:

```
const fwd = kopf(h, "x-forwarded-uri");
const orig = kopf(h, "x-original-uri");
if (fwd === null || orig === null) return nein(403);
const uri = fwd || orig || String(req.url || "");
…
const methodeRoh = kopf(h, "x-forwarded-method") || kopf(h, "x-original-method") || String(req.method || "GET");
```

Befehle (Skripte `probe.sh` + `revert.py` im Sitzungs-Scratch; Kopie von `tests/ tools/ sql/ scripts/
supabase/functions/kamera-stream/ docs/kameras/ index.html`):

```
python revert.py <kopie>/tools/kamera-proxy-auth/verify.mjs
cd <kopie> && python -m pytest \
  tests/test_kameras_phase2_v1056.py::test_angriff_gueltiges_a_token_mit_gefaelschtem_b_kopf \
  tests/test_kameras_phase2_v1056.py::test_angriff_eingeschleuster_kopf_und_kein_rueckfall \
  tests/test_kameras_phase2_v1056.py::test_nur_der_konfigurierte_kopf_zaehlt \
  tests/test_kameras_phase2_v1056.py::test_pruefer_liest_kopfnamen_nie_fest -q -p no:cacheprovider
# danach: verify.mjs aus dem Zweig zurueck in die Kopie (cmp == Zweig), gleicher pytest-Aufruf
```

Ergebnis (19.11.2026):

| Lauf | Ergebnis | Exitcode |
|---|---|---|
| 1) Fix zurückgenommen | **4 failed** in 0.62s | **1** (ROT) |
| 2) Fix wiederhergestellt (Kopie byte-gleich mit dem Zweig) | **4 passed** in 0.56s | **0** (GRÜN) |

Fehlermeldungen im roten Lauf:
- `test_angriff_gueltiges_a_token_mit_gefaelschtem_b_kopf`: `AssertionError: 204` – nginx-Fall: echter Pfad B in
  `X-Original-URI`, eingeschleustes `X-Forwarded-Uri` mit Pfad A, Token für A → das alte Verhalten **gab das Bild
  von B frei** (Pfadbindung umgangen).
- `test_angriff_eingeschleuster_kopf_und_kein_rueckfall`: `AssertionError: ('caddy_fremd_bei_gutem_pfad', 204)` –
  eingeschleuster Fremdkopf wurde nicht abgewiesen (und der `req.url`-Rückfall lieferte 204).
- `test_nur_der_konfigurierte_kopf_zaehlt`, `test_pruefer_liest_kopfnamen_nie_fest`: rot (Angriffsfälle bzw. fest verdrahtete Kopfnamen/`req.url`).

Hinweis zur Ehrlichkeit: der Caddy-Fall „echter Pfad B in `X-Forwarded-Uri`, eingeschleustes `X-Original-URI` A“
war auch im alten Code **nicht** ausnutzbar (dort gewann `X-Forwarded-Uri`); verwundbar war der nginx-Weg.
Der Zweig blieb dabei unverändert; der zurückgesetzte Stand wurde nicht committet.

Gesamtlauf im Zweig: `python -m pytest tests/test_kameras_phase2_v1056.py -q` → 53 passed, Exitcode 0.
Die Umkehrproben `test_umkehrprobe_fremdkopf_sperre` (Z. 534) und `test_umkehrprobe_altes_verhalten_einer_von_beiden_koepfen`
(Z. 539) wiederholen diesen Nachweis bei jedem Testlauf automatisch.

## Offen / vor Ort

1. `curl`-Proben gegen den echten Proxy (Kodierung, `..`, `//`, Großschreibung, eingeschleuste Köpfe) – PILOT.md Abschnitt 9.
2. Caddy `{http.request.orig_uri}` / `{http.request.orig_method}` mit `caddy validate` und einem Mitschnitt am Prüfer bestätigen.
3. Laufende WebRTC-/MJPEG-Verbindungen überleben das Token bis zur nächsten Erneuerung der App (≤ 120 s + Sitzung) – Obergrenze am Proxy offen.

## Nachtrag `feature/kameras-app` (19.11.2026): Einrichtungsabfrage

`logic.ts` hat einen Schritt 3b: `{"pruefen":"einrichtung"}` wird erst **nach** JWT-, Aktiv- und Rollenprüfung
ausgewertet und nur für `rolle === "admin"` beantwortet (sonst 403 `kein_zugriff`). Antwort: ob das Secret gesetzt ist
und die Basisadresse des Video-Hosts (nur gültiges `https://`, ohne Zugangsdaten – `backendBasis()`), ohne Kamera,
Streamname, Token oder DB-Abfrage. Ein Monteur endet weiter an der Rollensperre (Abschnitt d). Die Zeilenangaben oben
beziehen sich weiter auf 110678f. Tests mit Umkehrproben: `tests/test_kameras_einrichtung_v1060.py`.

## e) Nachtrag `fix/kamera-aufzeichnung-fenster` (19.11.2026): Aufzeichnung nur im freigegebenen Zeitraum, `geraet` ist keine Grenze

Zwei Funde einer automatischen Sicherheitsprüfung von `logic.ts`. Zeilenangaben in diesem Abschnitt beziehen sich auf
den Commit, der ihn einführt (Zweig `fix/kamera-aufzeichnung-fenster`, Basis v3.9.1062). Nichts deployt, keine DB berührt.

### e1) `geraet` („pc“/„mobil“) ist eine Client-Angabe – KEINE Sicherheitsgrenze

`geraet` kommt aus dem Anfragekörper; jeder Client kann `"pc"` schicken. Die Prüfung `geraet !== "pc"` bleibt als
Bedienkomfort (ehrliche Handys/Tablets bleiben auf Live), ist aber nirgends mehr als Schutz beschrieben.
Die Kontrolle für Aufzeichnungen ist ausschließlich **Rolle** (`KAMERA_AUFZEICHNUNG_ROLLEN`) + **Zeitraum-Prüfung** (e2).

| Stelle | Inhalt |
|---|---|
| `supabase/functions/kamera-stream/logic.ts:14-28` | Kopf: Schritt 6 = Rolle; `geraet` ausdrücklich „KEINE Sicherheitsgrenze“; Schritt 7b = echte Kontrolle |
| `logic.ts:417-418` | `const geraet = …` mit Kommentar „Client-Behauptung, KEINE Sicherheitsgrenze“ |
| `logic.ts:426` | Schritt 6: „Rolle … = Kontrolle; geraet=pc = nur Bedienung (fälschbar)“ |
| `supabase/functions/kamera-stream/README.md` (Abschnitt Request + Schritt 6) | „**`geraet` is NOT a security control.**“ |
| `docs/kameras/PHASE1_2026-11-19.md` (Prüfreihenfolge 6/7b, Testplan 10/10b) | gleiche Klarstellung, Fall 10b = Zeitraum-Angriff |
| `index.html:31191` | `var geraet=…` mit Kommentar „nur Bedienkomfort (Client-Angabe, fälschbar) – KEINE Sicherheitsgrenze“ |

UI-Texte geprüft: „Am Handy und Tablet nur Live-Bild. Aufzeichnungen und Verwaltung am PC.“ beschreibt nur die
Bedienung, behauptet keinen Schutz – unverändert. `KAMERA_REC_ROLLEN` war schon als „nur für die Anzeige“ markiert.

### e2) Aufzeichnung: Freigabe galt für „jetzt“, die Adresse aber für jeden Zeitraum (HIGH, Betriebsvereinbarung)

**Vorher:** `darfSehen(jwt, kamera)` wertete die Regel zu `now()` aus; die Aufzeichnungsadresse nahm danach beliebige
`von`/`bis` aus der Query an (nur Form, Spanne ≤ 6 h). Eine Regel Mo–Fr erlaubte damit am Montag die Aufnahmen vom
Samstag. **Nachher**, Ende zu Ende:

| # | Station | Stelle |
|---|---|---|
| 1 | App schickt den Zeitraum (ISO, UTC, höchstens 1 h, nie über jetzt hinaus) | `index.html:30737` `_kamBereichIso`, `:30648` Body mit `von`/`bis`, `:30899` Aufruf; Zukunft → Hinweis ohne Abruf |
| 2 | Edge Function prüft die Form → sonst 400 | `logic.ts:95-113` (`isoSekunden`, `aufzeichnungsBereich`): ISO mit Zone, ganze Sekunden, `von < bis`, Spanne ≤ 2 h (`:48`), `bis ≤ jetzt`, `von ≥ jetzt − 30 Tage` (`:49`, harte Obergrenze = CHECK-Maximum von `aufbewahrung_tage`); Aufruf `logic.ts:422` |
| 3 | Rolle (Kontrolle), `geraet` (Komfort) | `logic.ts:426-430` |
| 4 | Regel jetzt (unverändert, für Live und Aufzeichnung) | `logic.ts:432-437` |
| 5 | **Zeitraum-Prüfung in der DB mit dem JWT des Aufrufers** → sonst 403 (`grund: "bereich"` im Protokoll) | `logic.ts:439-447`; Verdrahtung `index.ts:54-58` → `rpc("kamera_darf_sehen_bereich", { p_kamera, p_von, p_bis })` über `aufruferClient(jwt)` |
| 6 | SQL-Funktion | `sql/KAMERAS_v1_ENTWURF.sql:231-259`: SECURITY DEFINER, `set search_path = public, pg_temp`, `v_auth := auth.uid()` (kein Nutzer-Parameter), `p_von < p_bis`, `p_bis ≤ now()`, Spanne ≤ 2 h (`:241`), Kamera aktiv + `p_von ≥ now() − aufbewahrung_tage` (`:244-247`), `kamera_pruefen` an `p_von` und an **jeder vollen Minute** in `(p_von, p_bis)` (`:248-257`) |
| 7 | Rechte | `:264-265` – `revoke all … from public, anon; grant execute … to authenticated;`; Rücknahme `sql/KAMERAS_v1_RUECKNAHME.sql:29` (vor `kamera_pruefen`) |
| 8 | Voraussetzung der Exaktheit | `sql/KAMERAS_v1_ENTWURF.sql:113` `kamera_zugriff_minuten_chk` – Regelgrenzen nur auf ganzen Minuten |
| 9 | Zeitraum signiert ins Token und in die Adresse | `logic.ts:470-473` (`payload.von/bis`), `logic.ts:480` `…?token=T&von=V&bis=B`; App hängt nichts mehr an (`index.html:30904`) |
| 10 | Token-Regel (beide Umsetzungen wortgleich) | `logic.ts:246-247` = `tools/kamera-proxy-auth/token.mjs:70-71`: `sc=aufzeichnung` verlangt ganzzahlige `von < bis`, `sc=live` darf keine tragen |
| 11 | **Proxy-Prüfer bindet die Query an das Token** → sonst 403 | `tools/kamera-proxy-auth/verify.mjs:155-169`: je genau ein `von`/`bis`, dekodiert **und** roh (kein `%`-kodierter Doppelgänger, `rohParameter` `:89-96`), nur Ziffern, **zeichengleich** mit dem signierten Wert; Spanne ≤ 2 h (`:39`) |
| 12 | Proxy baut den Abruf nur aus dem signierten Bereich | `verify.mjs:172-176` gibt `X-Kamera-Von`/`X-Kamera-Bis` zurück; Vorlage `vorlagen/Caddyfile` (Phase 3, auskommentiert): `copy_headers` + `rewrite …/start/{http.request.header.X-Kamera-Von}/end/{…Bis}/…` statt `{query.*}` |
| 13 | Live unverändert | Live-Token ohne `von`/`bis`, Live fragt keinen Bereich ab (`test_live_bleibt_bei_jetzt`) |

**Entwurfsentscheidung Zeitraum-Prüfung (exakt statt Stichprobe):** `kamera_pruefen` hängt nur von Wochentag und
Wiener Uhrzeit ab. Regelgrenzen liegen (per CHECK) auf ganzen Minuten; die Wiener Zonenversätze und
Sommerzeit-Umstellungen ebenfalls. Damit ist die Entscheidung auf jedem Stück `[volle Minute, nächste volle Minute)`
konstant, und die Prüfung an `p_von` plus jeder vollen Minute in `(p_von, p_bis)` ist **beweisbar vollständig** – auch
über Mitternacht und über die Umstellungsnacht (doppelte bzw. fehlende Stunde), wo eine Rückrechnung „Regelgrenze →
Zeitpunkt“ Fälle übersehen könnte. Kosten: höchstens 121 Aufrufe von `kamera_pruefen` je Anfrage (Spanne ≤ 2 h).
Ausführbarer Spiegel für die Tests: `entscheideBereich()` in `logic.ts:318-336`.

**Zusätzlich** muss die Regel auch **jetzt** gelten (Schritt 4): wer gerade keinen Zugriff hat, sieht auch keine
Aufnahmen (strenger als nötig, fail closed).

### Tests (Node, gegen genau diese Dateien)

`tests/test_kameras_phase1_v1055.py` (Abfragezeit Mo 23.11.2026 10:00 Wien, Regel Büro Mo–Fr 07–17, Aufbewahrung 3 Tage):
- `test_angriff_aufzeichnung_ausserhalb_des_bereichs_403` (Z. 504): **Samstag** 10–11 → 403; **teils außerhalb** Mo 06:30–07:30
  und Fr 16:30–17:01 → 403; **außerhalb der Aufbewahrung** Do 10–11 (Werktag im Fenster) → 403. Jeweils `darf == 1` (Regel gilt jetzt),
  abgewiesen erst durch die Bereichsprüfung, `backend == 0`, Protokollgrund `bereich`.
- `test_aufzeichnung_ungueltiger_bereich_400_ohne_abfrage` (Z. 523): älter als 30 Tage, Zukunft, Spanne > 2 h, `von = bis`,
  umgekehrt, fehlend, ohne Zone, Sekundenbruchteil, Zahl statt ISO → 400 ohne DB-Abfrage.
- `test_aufzeichnung_bereich_signiert_in_token_und_adresse` (Z. 488), `test_aufzeichnung_bereich_grenzfaelle_erlaubt` (Z. 515, 16:00–17:00 erlaubt,
  Admin-Regel ohne Fenster deckt Samstag), `test_geraet_ist_keine_sicherheitsgrenze_dokumentiert` (Z. 529), `test_live_bleibt_bei_jetzt` (Z. 542),
  `test_aufzeichnung_schickt_den_zeitraum_an_den_server` (Z. 986), `test_aufzeichnung_haengt_nichts_an_die_serveradresse` (Z. 1003),
  `test_sql_bereichspruefung_fuer_aufzeichnungen` (Z. 1192, statisch: DEFINER, Suchpfad, `auth.uid()`, Minutenschleife, Rechte, CHECK).
- Umkehrproben bei jedem Lauf: `test_umkehrprobe_alte_logik_ohne_bereichspruefung` (Z. 624, ohne Schritt 7b → alle vier Angriffe 200),
  `test_umkehrprobe_nur_der_anfang_statt_jeder_minute` (Z. 631), `test_umkehrprobe_aufbewahrung_im_spiegel` (Z. 638),
  `test_umkehrprobe_aufzeichnung_am_handy` (Z. 616: ohne `geraet`-Abgleich bleiben die Bereichs-Angriffe 403 – `geraet` trägt keinen Schutz).

`tests/test_kameras_phase2_v1056.py` + `tools/kamera-proxy-auth/vektoren.json` (neu signiert, Testsecret):
- `test_angriff_aufzeichnung_query_bereich_ungleich_token_403` (Z. 306): `von` verschoben (z. B. auf den Samstag, `vektoren.json:410`),
  ganzes Fenster um einen Tag verschoben (`:422`), `bis` verändert, `von` doppelt, `%31…`-kodiert (`:434`), kodierter Parametername,
  führende Null, Teilstück mit falschem `von`, fehlende Zeit → 403; passender Bereich (`:343`) → 204; altes Token ohne Bereich → 401.
- `test_aufzeichnung_bereich_als_kopf_fuer_den_proxy` (Z. 317), `test_tokenvektoren_bereich` (Z. 324, beide Umsetzungen),
  `test_aufzeichnung_unveraendert_und_vom_proxy_angenommen` (Z. 240: Adresse der Edge Function wird ohne Anhängen angenommen).
- Umkehrproben: `test_umkehrprobe_ohne_bereichsbindung_im_pruefer` (Z. 331), `test_umkehrprobe_token_ohne_bereichsregel` (Z. 339).

### Umkehrprobe gegen den alten Code (Scratch-Kopie, nicht im Zweig)

Neue Angriffstests (`test_angriff_aufzeichnung_ausserhalb_des_bereichs_403` ×4, `test_aufzeichnung_bereich_signiert_in_token_und_adresse`,
`test_angriff_aufzeichnung_query_bereich_ungleich_token_403`, `test_tokenvektoren_bereich`) in einer Kopie, deren `logic.ts`,
`token.mjs`, `verify.mjs` aus `origin/main` (v3.9.1062) stammen:

| Lauf | Ergebnis | Exitcode |
|---|---|---|
| A) alter Stand (alle drei Dateien) | **7 failed** – z. B. `('rec_buero_samstag', 200, '{"aufzeichnungUrl":…')`: Samstag-Aufnahme freigegeben | **1** (ROT) |
| B) nur `verify.mjs` alt | **1 failed, 6 passed** – `('aufzeichnung_bis_manipuliert', 204)`: verschobene Query vom Prüfer angenommen | **1** (ROT) |
| C) Fix wiederhergestellt (`cmp` byte-gleich mit dem Zweig) | **7 passed** | **0** (GRÜN) |

### Offen / vor Ort

1. SQL ist Entwurf, **nicht eingespielt**. Vor dem Einspielen den Probe-Block (Bereichs-Proben, `savepoint c8`) in einer Transaktion fahren.
2. Aufzeichnungswiedergabe ist Phase 3 (Proxy-Block auskommentiert). Beim Aktivieren bestätigen, dass Caddy `copy_headers`
   Client-Kopien von `X-Kamera-Von/-Bis` verwirft und der Abruf nur aus diesen Köpfen gebaut wird; Frigate-Teilstücke
   (`/aufzeichnung/<s>/<datei>`) laufen über das Cookie-Token, dessen Bereich der Prüfer ebenfalls als Kopf zurückgibt.
3. Ein Token bleibt ≤ 120 s gültig; innerhalb dieser Zeit ist nur **genau** der signierte Zeitraum abrufbar.
