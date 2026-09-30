# Berechtigungen gegen Oberfläche

**Die Frage.** Wo bietet die Oberfläche eine Handlung an, die der Zeilenschutz
der Datenbank abweist — und was sieht der Nutzer dabei?

Das Gebiet stand in `docs/befunde/BUGHUNT_2026-09-30.md` als **offen**; es ist
eines der zwei Gebiete, die in der Bughunt-Nacht nicht erreicht wurden.

**Kein Eingriff.** `index.html` wurde nicht angefasst — kein Edit, kein Write,
kein `sed -i`, kein Commit, kein Push. Angelegt hat dieser Lauf nur diese
Datei, zwei Messskripte und zwei JSON-Rohdateien.

---

## 0. Umfang, Stand und Methode — zuerst, weil jede Zahl daran hängt

**Stand.** `C:\repos\epkolar-app\index.html`, Arbeitsbaum auf
`origin/main = 44d52bf`, **`APP_VERSION="3.9.997-supabase"`**, 30 430 Zeilen.
Die Zahlen unten wurden zuerst gegen v3.9.996 erhoben und nach dem Sprung auf
v3.9.997 **erneut gefahren**; sie sind auf beiden Ständen identisch, weil alle
v3.9.997-Änderungen einzeilig sind und die Zeilennummern nicht verschieben.
Alle Zeilennummern in diesem Bericht gelten für **v3.9.997**.

**Umfang der Messung — und das ist eine Einschränkung, keine Fußnote.**

| | |
|---|---|
| gemessen | `index.html` allein, ausschließlich der **Quelltext** |
| Rollen | alle acht aus `ROLES` plus die sieben weiteren Rollen-Zeichenketten, die im Code verglichen werden (Abschnitt 2) |
| Ansichten | **keine** — es gab keinen Browserlauf. Die Messung sagt, was im Code steht, nicht was ein Monteur am Schirm sieht |
| Datenbank | **nicht** gemessen. Kein Zugang, kein Schlüssel. **Jede Aussage über RLS in diesem Bericht ist eine Aussage darüber, was der CODE über RLS behauptet** — in seinen eigenen Kommentaren |

**Werkzeuge.** Zwei neue Skripte, beide mit Selbstprobe, beide brechen mit
`return 2` ab, wenn eine Probe scheitert:

* `scripts/rechte_rollen_messen.py` — Rollen, Rollenabfragen, `canDo`,
  `hasPerm`, die `isAdmin`-Namensvielfalt.
* `scripts/rechte_schreibwege_messen.py` — Schreibwege, der Wächter
  `_RLS_SILENT_DENIAL_LABELS`, die Löschwege, die Umleitungen am Wächter
  vorbei, die Rollenabfrage in der Umgebung einer Schreibstelle.

Beide benutzen das geeichte `scripts/code_scan.py` (`ist_code`) zum Ausblenden
von Kommentaren. Das zweite Skript führt zusätzlich eine eigene Maske
`ist_kein_kommentar` — `ist_code` blendet **Zeichenketten mit aus**, und genau
darin steht der zu messende Inhalt (`method:"PUT"`, `url:"/api/…"`). Ein
Zähler auf `ist_code` allein meldet für jeden dieser Schlüssel „kommt nicht
vor". Die Selbstprobe prüft deshalb auch die Einbettung: jede Stelle, die
`ist_code` als Code führt, muss auch `ist_kein_kommentar` bestehen.

### Die Selbstproben — was sie abdecken

`rechte_rollen_messen.py`: **zehn Schreibweisen, je ein eigener Köder**
(`u.role==="x"` und `u.role==='x'`, `.rolle`, `.role` ohne Vergleich,
`hasPerm(`, `canDo(`, `ROLES[`, `ROLLE.`, `permsOverride`/`perms_override`,
`curUser.role`), dazu drei Gegenproben, die **nicht** gezählt werden dürfen:
dieselben Formen im Zeilenkommentar, im Blockkommentar und in einer
Zeichenkette. Dazu eine Gegenprobe an der Ausblendung selbst — die rohe Suche
muss **mehr** finden als die auf Code eingeschränkte, sonst blendet sie nichts
aus und die Nullen wären wertlos. Dazu ein Köder, bei dem eine `canDo`-Aktion
definiert und nie gefragt wird (das ist der Kern von Befund R4), und einer,
bei dem `adminTabs` als Name **keine** Rollenmenge ist und nicht mitgezählt
werden darf.

`rechte_schreibwege_messen.py`: **fünf SQ.push-Köder**, einer je Form —
doppelt zitierte Methode, einfach zitierte Methode, Adresse als
Vorlagenliteral (`` `/api/x/${id}` ``), ein **Regex-Literal im Rumpf**
(`/[)}]/g` — es enthält beide Klammern, die den Abgleich aus dem Tritt
brächten), und eine **`}` in einer Zeichenkette**. Dazu **vier** Gegenproben:
Zeilenkommentar, Blockkommentar, ein Backtick-Zitat im Blockkommentar und eine
Zeichenkette. Dazu eine Gegenprobe an der Näherung aus Abschnitt 10: ein zu
großer Ausschnitt **muss** eine fremde Rollenabfrage einsammeln, sonst misst
die Ebenen-Angabe nichts.

### Und die Selbstprobe selbst ist geprüft — auf WIRKUNG, nicht Anwesenheit

Eine Selbstprobe, die immer grün meldet, ist Zierrat. `scripts/rechte_selbstprobe_mutieren.py`
macht die Messwerkzeuge absichtlich kaputt und prüft, ob die Selbstprobe das
merkt. Gefahren, Ergebnis:

| Mutation | erwartet | gemessen |
|---|---|---|
| dem Köder die einfach zitierte Schreibweise nehmen | rot | **rot** |
| die Kommentar-Ausblendung abschalten (`ist_code` → alles Code) | rot | **rot** |
| den Klammerabgleich bei der ersten `)` abbrechen | rot | **rot** |
| `ist_kein_kommentar` auf `ist_code` zurückfallen lassen | rot | **rot** |
| *Kontrolle:* Vorlagenliteral im Köder durch eine Zeichenkette ersetzen | grün | **grün** |

🔴 **Die Kontrolle zeigt zugleich die Grenze, und sie gehört hierher:** nimmt
man dem **Köder** eine Form weg, statt das Werkzeug kaputtzumachen, bleibt die
Selbstprobe grün. Sie kann nur prüfen, was im Köder steht. Gegen einen zu
dünnen Köder hilft keine Mutation, nur Nachsehen.

**Die Befehle, die jede Zahl unten erzeugen:**

```
python scripts/rechte_rollen_messen.py --json
python scripts/rechte_schreibwege_messen.py --json
python scripts/rechte_selbstprobe_mutieren.py
```

Alle drei laufen mit Rückgabewert **0**; die beiden Messskripte brechen mit
**2** ab und nennen keine Zahl, wenn eine Probe scheitert.
Rohdaten: `docs/befunde/bughunt/rechte_rollen.json`,
`docs/befunde/bughunt/rechte_schreibwege.json`.

---

## 1. Der Plausibilitätsanker — zur Hälfte gehalten, zur Hälfte widerlegt

Die Vorgabe lautete: *„es gibt 3–5 Rollen; die Rolle ‚monteur' sieht mehrere
Schreibwege, die der Zeilenschutz abweist; und ein Teil dieser Wege läuft
NICHT über den Wächter `_RLS_SILENT_DENIAL_LABELS` (der deckt seit v3.9.994 23
Tabellen ab)."*

| Behauptung | Messung |
|---|---|
| 3–5 Rollen | ❌ **widerlegt.** `ROLES` führt **8**; im Code werden **15** verschiedene Rollen-Zeichenketten verglichen, davon **7 ohne Eintrag in `ROLES`** |
| Wächter deckt 23 Tabellen | ✅ **bestätigt**, genau 23 — und sie decken 23 der 27 per `PUT`/`PATCH` beschriebenen Tabellen |
| ein Teil der Wege läuft nicht über den Wächter | ✅ **bestätigt, und schärfer als erwartet**: es sind nicht nur die 4 ungedeckten Tabellen. **21 Schreibaufrufe** laufen baulich am Wächter vorbei, und **fünf davon treffen Tabellen, die in der Tafel STEHEN** (Befund R1) |
| „monteur sieht Schreibwege, die der Zeilenschutz abweist" | ⚪ **nicht entscheidbar.** Ohne Datenbankzugang ist nicht messbar, welchen Schreibvorgang der Zeilenschutz heute abweist. Messbar ist, **wo kein Rollen-Riegel davor steht** und **was der Nutzer im Abweisungsfall sähe** — das sind die Befunde R2, R5 und R6 |

---

## 2. Rollen: acht im Katalog, fünfzehn im Code

```
python scripts/rechte_rollen_messen.py      # Abschnitt 1
```

`const ROLES` (`index.html:3696`) führt **8** Rollen:

| Rolle | Module |
|---|---:|
| `admin` | 20 |
| `buero` | 19 |
| `projektleiter` | 18 |
| `obermonteur` | 15 |
| `techniker` | 14 |
| **`monteur`** | **11** |
| `helfer` | 9 |
| `viewer` | 4 |

Die elf Module von `monteur`: `projekte`, `wochenplanung`, `mitarbeiter`,
`arbeitsscheine`, `zeiterfassung`, `urlaub`, `formulare`, `maengel`, `plaene`,
`bautagebuch`, `material`.

Daneben steht ein **eingefrorener Aufzähler** `const ROLLE=Object.freeze({…})`
(`index.html:727`) mit **7** Werten — `viewer` fehlt darin.

> 🟡 **R7a — der Aufzähler wird NIE benutzt.** `ROLLE.ADMIN` & Co. kommen im
> ganzen Dokument **0-mal** vor (Zähler `ROLLE_enum_nutzung`). Ein
> eingefrorenes Objekt, das niemand liest, ist keine Einzelquelle, sondern
> eine zweite Liste, die stillschweigend auseinanderlaufen darf — sie ist es
> bereits (`viewer`).

**Rollen-Zeichenketten, die im Code verglichen werden** — sieben davon haben
keinen Eintrag in `ROLES`:

| Zeichenkette | Vergleiche | in `ROLES`? |
|---|---:|---|
| `admin` | 78 | ja |
| `projektleiter` | 34 | ja |
| `buero` | 21 | ja |
| `monteur` | 19 | ja |
| `helfer` | 15 | ja |
| `techniker` | 13 | ja |
| `obermonteur` | 13 | ja |
| `lager_display` | 5 | **nein** |
| `anon` | 3 | **nein** |
| `lagerleitung` | 3 | **nein** |
| `stempel_terminal` | 2 | **nein** |
| `alle` | 1 | **nein** |
| `Lagerleitung` | 1 | **nein** (und grossgeschrieben) |
| `backoffice` | 1 | **nein** |

> ⚪ **R7b — `lagerleitung` wird über ein ZWEITES Feld abgefragt.** Nicht über
> `user.role`, sondern über `user.rolle` (`index.html:5194`, `13853`, `14104`,
> `15527`, `20078`, `27989`, `29696` — 22 `.rolle`-Stellen insgesamt). Das
> Benutzerobjekt, das die Anmeldung baut, hat dieses Feld **nicht**:
> `index.html:3101` setzt `{id,name,role,username,email,permissions,monteurId,permsOverride}`.
> Nachgetragen wird es an zwei späteren Stellen aus `workers.r`
> (`index.html:8408` und `9577`). **Ob es zum Zeitpunkt der Abfragen gesetzt
> ist, ist von hier aus nicht messbar** — das braucht einen Lauf im Browser.
> Steht es nicht, fällt `isLager` (`5194`) still auf `admin||projektleiter`
> zurück, und `canDo("admin_panel")` gibt für eine Lagerleitung `false`.

### Wie die Rolle abgefragt wird — zehn Schreibweisen, 580 Stellen

| Schreibweise | Stellen |
|---|---:|
| `…role==="x"` (doppelt zitiert) | 179 |
| `…role==='x'` (einfach zitiert) | 30 |
| `.rolle` (das zweite Feld) | 22 |
| `.role` gelesen ohne Vergleich | 76 |
| `hasPerm(` | 26 |
| `canDo(` | 38 |
| `ROLES[` | 9 |
| `ROLLE.` | **0** |
| `permsOverride` / `perms_override` | 40 |
| `curUser.role` | 160 |
| **Summe (mit Überschneidung)** | **580** |

---

## 3. 🔴 R1 — Der Wächter deckt die TABELLE, aber nicht den WEG

**Stellen:** `index.html:2793`, `2818`, `2833` (`fahrzeuge`), `2851`
(`werkzeuge`), `2863` (`fz_termine`).
**Gemessen mit:** `scripts/rechte_schreibwege_messen.py`, Abschnitt 4.

Der Wächter sitzt im **allgemeinen** PATCH-Zweig von `_translateAndExec`
(`index.html:3011–3013`). `_translateAndExec` beginnt bei Zeile 2686; der
allgemeine CRUD-Block beginnt erst bei Zeile **2969**. Alles davor sind
Sonderzweige, die selbst schreiben und dann `return{ok:1}` geben.

**Gemessen: 21 direkte Schreibaufrufe stehen VOR dem allgemeinen CRUD-Block.**
Sie erreichen den Wächter baulich nie. Fünf davon treffen Tabellen, die in der
Tafel **stehen**:

| Zeile | Helfer | Tabelle | in der Tafel |
|---:|---|---|---|
| 2793 | `_sbPatch` | `fahrzeuge` | **ja** |
| 2818 | `_sbPatch` | `fahrzeuge` | **ja** |
| 2833 | `_sbPatch` | `fahrzeuge` | **ja** |
| 2851 | `_sbPatch` | `werkzeuge` | **ja** |
| 2863 | `_sbPost` | `fz_termine` | **ja** |
| 2703, 2749, 2752, 2761, 2770 | `_sbUpsert`/`fetch` | `notifications` | nein |
| 2859 | `_sbPost` | `wz_service` | nein |
| 2872 | `_sbPost` | `photos` | nein |
| 2878, 2884, 2892 | `_sbUpsert`/`fetch` | `worker_projects` | nein |
| 2920 | `_sbUpsert` | `weekplans` | nein |
| 2945, 2948, 2953 | `_sbUpsert`/`fetch` | `weekplan_rows` | nein |
| 2964 | `_sbUpsert` | `urlaubskontingent` | nein |

🔴 **Und jetzt das Bittere: der Wächter ist genau für diesen Fall gebaut
worden.** Sein eigener Kommentar (`index.html:3006–3010`, v3.9.306 #3) sagt
wörtlich:

> *„0-rows-Safeguard für **Fahrzeug-/Tank-Saves**. RLS-Silent-Denial liefert
> HTTP 200 + leeres Array (return=representation) → Update ging NICHT in die
> DB, App hätte aber ‚erfasst' gemeldet = **stiller Tank-/km-Verlust**."*

Der Tank-/km-Weg ist `PUT /api/fahrzeuge/<id>` mit `tankLog_add` bzw.
`kmStand` (`index.html:2801–2840`). Er patcht bei `2818`/`2833` **selbst** und
endet bei `2823`/`2838` mit

```js
if(Object.keys(d).length===0)return{ok:1};
```

Bei einem reinen Tank-/km-Beleg ist `d` danach leer — der allgemeine Zweig
wird **nie** erreicht, der Wächter feuert nie, die Rückgabe von `_sbPatch`
wird gar nicht angesehen.

**Auslöser aus dem Alltag:** ein Monteur erfasst an der Tankstelle Liter und
km-Stand am Fahrzeug.
**Folge bei einer Abweisung:** `_sbPatch` liefert `[]`, niemand sieht hin,
`{ok:1}` geht zurück, `doSync` legt die Kennung in `okIds` (`index.html:9082`)
und `SQ.removeMany` löscht den Auftrag aus der Warteschlange
(`index.html:9123`). Der Monteur sieht den Erfolgs-Toast seiner eigenen
Ansicht. **Der Beleg ist weg, und niemand erfährt es.**
Genau das Szenario, gegen das der Eintrag `fahrzeuge:"Fahrzeug-Änderung"`
geschrieben wurde. **Der Eintrag ist an dieser Stelle eine Attrappe.**

Dasselbe gilt für `werkzeuge` (`2851`, Serviceheft-Eintrag über
`POST /api/werkzeuge/<id>`) und `fz_termine` (`2863`).

---

## 4. 🔴 R2 — 41 Löschwege können eine Abweisung STRUKTURELL nicht sehen

**Stellen:** `index.html:2321` (`_sbDelete`) und `2327` (`_sbDeleteWhere`).
**Gemessen mit:** `scripts/rechte_schreibwege_messen.py`, Abschnitt 3.

| Helfer | Header | sieht getroffene Zeilen |
|---|---|---|
| `_sbPatch` | `_sbWH` | **ja** |
| `_sbPost` | `_sbWH` | **ja** |
| `_sbUpsert` | `_sbWH` | **ja** |
| `_sbDelete` | `_sbH` | **NEIN** |
| `_sbDeleteWhere` | `_sbH` | **NEIN** |

`_sbWH(prefer)` (`index.html:1483`) setzt `Prefer: return=representation` —
nur damit liefert PostgREST die getroffenen Zeilen zurück. `_sbDelete` nimmt
`_sbH()` **ohne** `Prefer` und gibt bei jedem 2xx hart `return{ok:1}`.

Ein vom Zeilenschutz abgewiesener `DELETE` sieht damit **exakt** aus wie ein
erfolgreicher. Kein Array, keine Zahl, kein Unterschied.

**Gemessen: 41 `SQ.push`-Stellen mit `method:"DELETE"` auf 29 Tabellen.**
Die schwersten, nach Zahl der Schreibstellen:

| Tabelle | Löschstellen |
|---|---:|
| `time_entries` | 4 |
| `notifications` | 3 |
| `absence_files` | 3 |
| `defects` | 3 |
| `forms` | 2 |
| `tickets` | 2 |
| `absences` | 2 |
| 22 weitere Tabellen | je 1 |

🔴 **`absence_files` sind die Krankmeldungs-Atteste** (siehe B1 im
Hauptbefund) — Gesundheitsdaten. Ein Löschversuch, den der Zeilenschutz
abweist, meldet „gelöscht", und die Zeile bleibt in der Datenbank.
🔴 **`time_entries` ist lohnrelevant.** Vier Löschwege, alle blind.

Das bestätigt und **beziffert** D6 aus `datenverlust.md`, das dort ohne Zahl
steht.

**Was hier NICHT gemessen ist:** dass PostgREST auf *dieser* Instanz einen
RLS-abgewiesenen DELETE mit 204 und null gelöschten Zeilen beantwortet. Das
ist das dokumentierte Standardverhalten, aber an der Instanz ist es hier nicht
nachgefahren worden. Im Haus gibt es für so eine Prüfung einen Präzedenzfall
(der `count=exact`-Vermerk auf dem DELETE). **Dafür braucht es einen Zugang.**

---

## 5. 🔴 R3 — `isAdmin` bedeutet an 17 Stellen DREI verschiedene Rollenmengen

**Gemessen mit:** `scripts/rechte_rollen_messen.py`, Abschnitt 5.

| Name | Rollenmenge | Zeilen |
|---|---|---|
| `isAdmin` | `admin` \| `projektleiter` | 14941, 15734, 16130, 16878, 18405, 19238, 19430, 19811, 20077, 21485, 25385, 29692 — **12 Stellen** |
| `isAdmin` | `admin` \| `buero` \| `projektleiter` | 10948, 24428 |
| `isAdmin` | `admin` \| `buero` \| `projektleiter` + `hasPerm('urlaub_edit')` | 22520 |
| `isAdmin` | `admin` | 1412 |
| `isAdmin` | delegiert an `_maStaffRolle(curUser)` | 10145 |
| `isAdminPL` | `admin` \| `projektleiter` | 16203 |
| `isFullAdmin` | `admin` \| `projektleiter` | 14176 |
| `_isAdmin` | `admin` | 9973, 10038 |
| `_vcIsAdmin` | `admin` \| `projektleiter` | 16740 |
| `isVAdmin` | `admin` \| `buero` \| `projektleiter` \| `lagerleitung` | 27989 |
| `_isVAdminWz` | `buero` \| `projektleiter` \| `lagerleitung` | 29696 |
| `_isFleetAdmin` | `buero` \| `lagerleitung` | 15146 |
| `_gpAdminLike` | `admin` \| `buero` \| `projektleiter` | 20441 |

**Drei Namen tragen mehr als eine Rollenmenge** (`isAdmin`, `isVAdmin`,
`admins`). **Sieben verschiedene Rollenmengen** verstecken sich hinter Namen,
die alle „admin" enthalten.

**Warum das zur Frage dieses Berichts gehört:** die Datenbank kennt **eine**
Wahrheit je Tabelle. Wenn derselbe Bezeichner in der Fahrzeugansicht
`admin|PL` und in der Urlaubsansicht `admin|PL|büro` bedeutet, dann ist
mindestens eine der beiden Ansichten enger oder weiter als der Zeilenschutz —
und welche, sieht man an der Stelle nicht, weil der Name überall gleich
aussieht. Ein Riegel, den man beim Lesen für denselben hält, ist derselbe
nicht.

**Konkret:** `buero` sieht in den 12 `admin|projektleiter`-Ansichten die
Knöpfe **nicht**, obwohl `canDo` ihm `as_delete`, `fz_edit`, `doc_delete`,
`zeit_delete_any`, `abs_approve` und `material_edit` ausdrücklich gibt. Das
ist die harmlose Richtung (ein Knopf zu wenig). Die andere Richtung steht in
R5.

---

## 6. 🔴 R4 — Die zentrale Rechtetafel wird zu 77 % nicht gefragt

**Stelle:** `index.html:5193` (`function canDo`).
**Gemessen mit:** `scripts/rechte_rollen_messen.py`, Abschnitt 3.

| | |
|---|---:|
| Aktionen, die `canDo` kennt | **47** |
| Aktionen, die irgendwo abgefragt werden | **11** |
| **nie abgefragt** | **36** |
| `canDo(`-Aufrufstellen insgesamt | 38 |
| daneben: freie Rollenvergleiche im Code | **209** |

Die elf, die gefragt werden: `admin_panel`, `anmeldung_edit`, `as_delete`,
`doc_upload`, `fahrbewilligung_edit`, `gefahrstoff_edit`, `material_delete`,
`material_order`, `view_ek_price`, `wz_edit`, `zeit_other`.

Die 36, die nie gefragt werden, u. a.: `proj_create`, `proj_delete`,
`proj_archive`, `worker_create`, `worker_edit`, `worker_delete`,
`user_manage`, `as_create`, `fz_create`, `fz_delete`, `wz_create`,
`wz_delete`, `plan_create`, `plan_delete`, **`ticket_create`**,
`doc_delete`, `folder_delete`, `zeit_delete`, `zeit_delete_own`,
`zeit_delete_any`, `form_create`, `form_delete*`, **`mangel_create`**,
**`mangel_delete`**, `bt_create`, `bt_delete`, **`abs_approve`**,
`abs_kontingent`, `auswertungen`, `offa_export`, `material_view`,
`material_add`, `material_edit`, `supplier_manage`.

**Das ist kein Beweis, dass diese Wege ungeschützt sind** — 209 freie
Rollenvergleiche tun die Arbeit an vielen Stellen. Es ist die Aussage, dass
die Tafel, die aussieht wie die Einzelquelle, es für 36 von 47 Einträgen nicht
ist: sie ist Dokumentation, kein Riegel. Wer sie liest, um zu entscheiden, wer
was darf, liest etwas, das die Oberfläche in 36 Fällen gar nicht befragt.

Ein Eintrag sagt das sogar selbst: bei `as_create` steht *„v3.9.346:
UI-Einstiege entfernt — Permission bleibt für Backend-Konsistenz"*. Das ist
eine bewusste Entscheidung. Für die anderen 35 steht nichts dergleichen da.

---

## 7. 🟡 R5 — Ein Riegel, der nur die HALBE Menge deckt, und einer, der fehlt

**Stellen:** `index.html:17031` (`updSt`, `defects` PUT bei `17037`) und
`18539` (`updateTicket`, `tickets` PUT bei `18546`).
**Am Quelltext gelesen, Zeile für Zeile** — nicht aus der Näherung in
Abschnitt 10 übernommen.

Im selben Bauteil, wenige Zeilen daneben:

| Funktion | Zeile | Riegel |
|---|---:|---|
| `updSt` — Mangel-Status setzen | 17031 | **halb**: `if(!isAdmin && _m0 && _m0.melder==="Kunde")` → Toast + Abbruch |
| `_bulkApply` — Stapel-Änderung | 17041 | `if(!isAdmin)return;` |
| `delM` — Mangel löschen | 17042 | `if(!isAdmin)return;` |
| `reviewAccept` — Kundenmeldung annehmen | 17044 | `if(!isAdmin){…Toast „Triage ist Admin/PL-Task"…;return;}` |
| `updateTicket` — Ticket speichern | 18539 | **keiner** |
| `deleteTicket` — Ticket löschen | 18547 | `if(!isAdmin)return;` |

🔴 **`updSt` sperrt nur die vom KUNDEN gemeldeten Mängel.** Der Riegel prüft
`_m0.melder==="Kunde"`; bei jedem intern gemeldeten Mangel läuft er ins Leere,
und der Status-Wechsel steht allen Rollen offen, die die Mängelansicht
erreichen. Der Kommentar darüber (v3.9.25) nennt auch nur diesen halben
Zweck — er ist also nicht falsch, aber er ist nicht der Riegel, für den ihn
die drei Nachbarn halten könnten.

🔴 **`updateTicket` hat gar keinen.** `deleteTicket` zehn Zeilen darunter hat
einen.

`isAdmin` ist in beiden Bauteilen `admin||projektleiter` (`16878`, `18405`).
`canDo` gibt `mangel_delete` und `ticket_create` ebenfalls nur `admin|PL` —
und fragt es nie (R4). Der Status-Wechsel an einem internen Mangel und das
Speichern eines Tickets sind damit für **alle Rollen** offen, die die Ansicht
erreichen; `monteur` hat die Module `maengel` und `plaene`.

**Hier ist die Richtung des Lochs umgekehrt zu R1:** nicht „die Oberfläche
bietet an, was die Datenbank abweist", sondern „die Oberfläche bietet an, was
die eigene Rechtetafel verbietet". Ob die Datenbank es abweist, sagt der Code
selbst — im Kommentar an der `plans`-Zeile der Tafel (`index.html:2668`,
v3.9.478):

> *„defects/tickets UPDATE = authenticated → bewusst NICHT gelistet, sonst
> False-Positive bei 0-Row-Edge."*

Wenn das heute noch stimmt, geht hier **nichts verloren** — der Schreibvorgang
gelingt. Dann ist es eine Rechtefrage, keine Datenverlustfrage: ein Monteur
darf Mangel-Status und Tickets ändern, obwohl `canDo` das Admin und
Projektleitung vorbehält. Stimmt es nicht mehr, ist es der stille Verlust aus
R6(b), denn `defects` und `tickets` sind zwei der vier ungedeckten Tabellen.

**Entscheidbar ist das nur an der Datenbank.**

---

## 8. 🔴 R6 — Was der Nutzer bei einer Abweisung sieht: drei Ausgänge

Gemessen am Quelltext, Zeile für Zeile.

### (a) Er bekommt eine klare Meldung — 23 Tabellen, aber nur auf EINEM Weg

`index.html:3011–3013`: PATCH über den allgemeinen CRUD-Zweig, Tabelle in
`_RLS_SILENT_DENIAL_LABELS`, Antwort ist ein leeres Array →

> ⚠️ *„&lt;Label&gt; NICHT gespeichert — keine Schreibberechtigung. Bitte
> Büro/Admin informieren (Eingabe ging nicht in die Datenbank)."* (9 Sekunden)

**Gemessen: 23 Tafel-Einträge, 27 per `PUT`/`PATCH` beschriebene Tabellen, 23
gedeckt, 4 ungedeckt.** Jeder Tafel-Eintrag trifft mindestens eine echte
Schreibstelle — die tote Zeile `fz_schaeden` ist in v3.9.994 entfernt worden,
das ist nachgemessen (`Tafel-Einträge ohne PUT/PATCH-Schreibstelle: 0`).

### (b) Er sieht GAR NICHTS — und der Auftrag wird gelöscht

Das trifft:

* die **4 ungedeckten Tabellen** `defects`, `notifications`, `tickets`,
  `worker_projects`;
* **alle 21 Umleitungen** aus R1, auch die fünf auf Tafel-Tabellen;
* **alle 41 Löschwege** aus R2, auf allen 29 Tabellen — ausnahmslos, weil der
  Wächter eine Zeilenliste braucht und `_sbDelete` keine bekommt.

Der Ablauf ist in allen Fällen derselbe: `return{ok:1}` →
`okIds.push(item.id)` (`index.html:9082`) → `SQ.removeMany(removeIds)`
(`index.html:9123`) → der Auftrag ist aus der Warteschlange, kein
Wiederholversuch, kein Eintrag in `syncQueueFailed`. Was der Nutzer sieht, ist
der Erfolgs-Toast, den seine eigene Ansicht **vor** dem Abgleich gezeigt hat.

### (c) Er sieht eine Meldung, die er nicht lesen kann

Bei einem echten **403** (der lautere Weg — `_sbPost`/`_sbUpsert`/`_sbPatch`
werfen bei `!r.ok`, `index.html:2265`, `2270`, `2318`):

1. `_onAuthFail(403)` (`index.html:1649`) schreibt **nur in die Konsole**:
   *„[Auth] 403 Forbidden (RLS) — Session gueltig, kein Re-Login"*. Kein Toast.
   Das ist richtig so — ein „Sitzung abgelaufen" wäre falsch.
2. Der Fehler steigt auf, `doSync` behandelt 403 als **permanent**
   (`index.html:9089–9091`), zählt den Auftrag hoch und verwirft ihn nach fünf
   Versuchen (`index.html:9102–9111`).
3. Erst dann, bei `index.html:9120`, kommt die einzige sichtbare Meldung:

> ⚠ *„N Sync-Einträge nach 5 Versuchen verworfen: &lt;X&gt;, &lt;Y&gt;, &lt;Z&gt;"*

🔴 **Und `<X>` ist nicht die Handlung, sondern die Kennung.** Die Namensliste
wird gebaut aus `(item.url||"").split("/").pop()` (`index.html:9110`) — dem
**letzten** Segment der Adresse. Bei `/api/entries/1730384921_7f3a` ist das
`1730384921_7f3a`. Der Monteur liest:

> ⚠ 1 Sync-Eintrag nach 5 Versuchen verworfen: 1730384921_7f3a

Er erfährt, dass etwas verloren ging, aber nicht **was**. Für einen Eintrag
ohne Kennung (ein `POST` auf `/api/absences`) steht dort `absences` — dann
stimmt es zufällig. Die Tafel `_RLS_SILENT_DENIAL_LABELS` hält genau die
Klartext-Beschriftungen bereit, die hier fehlen; sie wird an dieser Stelle
nicht benutzt.

---

## 9. 🟡 R8 — `/api/ztest` hat keinen Eintrag in `ROUTE_MAP`

**Stelle:** `index.html:930`.

Gemessen: **188 `SQ.push`-Aufrufe** im Code, **40 `ROUTE_MAP`-Einträge**, und
genau **eine** Route ohne Eintrag: `ztest`. Sie stammt aus dem eigenen
Selbsttest (`TC-M SQ 50 parallel-push`), schreibt nichts Echtes und wird
danach wieder verworfen. **Kein Befund am Programm** — aber sie ist der
lebende Beleg für D5: eine Route ohne `ROUTE_MAP`-Eintrag läuft in
`if(!entry){console.warn("[api] Unknown route:",url);return{ok:1};}`
(`index.html:2969`) und gilt als Erfolg.

Die 188 stimmen auf den Aufruf genau mit der Zahl aus
`docs/befunde/bughunt/d2_tabellen.md` überein — dort mit einem **anderen**,
unabhängig gebauten Tokenizer erhoben. Zwei Werkzeuge, dieselbe Zahl.

---

## 10. Wie weit reicht ein Rollen-Riegel? Eine Näherung, und sie heißt so

**Gemessen mit:** `scripts/rechte_schreibwege_messen.py`, Abschnitt 5.

Zu jeder der 188 Schreibstellen wurde der **umschließende Block** rückwärts
über Code-Zeichen bestimmt (`}` hinein, `{` heraus) und darin nach einer
Rollenabfrage gesucht (`canDo(`, `hasPerm(`, ein Rollenvergleich, `.rolle`,
`ROLES[`, `permsOverride`, `isAdmin`/`_isAdmin`/`isAdminPL`/`isFullAdmin`).

| Ausschnitt | mit Rollenabfrage | ohne | Anteil ohne |
|---|---:|---:|---:|
| 1 Blockebene | 47 | **141** | 75 % |
| 2 Blockebenen | 112 | **76** | 40 % |
| 3 Blockebenen | 142 | **46** | 24 % |

🔴 **Diese Zahlen sind eine NÄHERUNG und irren in BEIDE Richtungen — ich habe
je ein Gegenbeispiel gemessen, und beide stehen hierher, weil sie sagen, wie
weit die Zahl trägt:**

* **Falsch als „mit Riegel" eingestuft:** `updSt` (Schreibstelle `17037`).
  Zwei Blockebenen zurück liegt ein `isAdmin`, das zu einer **anderen**
  Funktion gehört. Der echte Riegel an dieser Stelle deckt nur die
  Kunden-Mängel (R5).
* **Falsch als „ohne Riegel" eingestuft:** `_bulkApply` (Schreibstelle
  `17041`). Der Push steht in einem `forEach`-Rückruf; das `if(!isAdmin)return;`
  am Anfang der Funktion liegt eine Blockebene weiter draußen als der
  Ausschnitt reicht.

Dazu: „keine Rollenabfrage im Block" heißt ohnehin **nicht** „ungeschützt" —
das Bauteil selbst kann hinter `hasPerm(curUser, n.pm)` in der
Navigationstafel liegen, und das tut es meistens.

**Die Näherung taugt deshalb NICHT als Befund, sondern nur als Suchhilfe.**
Alle Befunde R1–R6 oben sind am Quelltext einzeln nachgelesen, keiner ist aus
dieser Tabelle abgeleitet.

**Was die Zahlen als Suchhilfe sagen:** selbst mit dem großzügigsten
Ausschnitt haben **46 von 188** Schreibstellen in drei Blockebenen Umgebung
**keinen einzigen** Rollenbezug. Die stärksten Posten aus der 2-Ebenen-Messung
— als Liste, wo man nachsehen sollte, nicht als Mängelliste:

| Tabelle | Methode | Stellen ohne Rollenbezug |
|---|---|---:|
| `absences` | PUT | 5 |
| `time_entries` | PUT | 4 |
| `users` | PUT | 3 |
| `projects` | PUT | 3 |
| `defects` | PUT | 3 |
| `fahrzeuge` | PUT | 3 |
| `time_entries` | POST / DELETE | 2 / 2 |
| `material_catalogs` | PUT / POST | 2 / 2 |
| `notifications` | DELETE | 2 |
| `absence_files` | POST | 2 |

Die drei `users`-PUT (`index.html:10199`, `13961`, `13981`) sind nachgesehen
und **in Ordnung**: sie tragen nach einem erfolgreichen
`rpc/admin_create_user` die `auth_user_id` nach; die RPC ist laut Kommentar
admin-gegatet, und der PUT läuft nur im `else`-Zweig ihrer Antwort. Sie stehen
hier, damit niemand zweimal nachsieht.

---

## 11. Zwei Messfehler, die dieser Lauf an sich selbst gefunden hat

Sie stehen hier, weil sie sagen, welchen Zahlen oben zu trauen ist.

**1. „Neun Module werden nie abgefragt" — falsch, und es war die zweite
Schreibweise.** Der erste Zähler suchte nur
`hasPerm(curUser,"<modul>")` mit **wörtlichem** Modulnamen. Ergebnis: 12 von
20 Modulen abgefragt, **9 angeblich nie** (`bautagebuch`, `export`,
`formulare`, `maengel`, `material`, `offa`, `plaene`, `projekte`,
`wochenplanung`). Das sah aus wie ein Befund und war ein Messfehler: es gibt
**fünf** Aufrufstellen, an denen das Modul aus einer **Variablen** kommt —
`hasPerm(curUser,t.perm)` (`9562`), `hasPerm(curUser,c.pm)` (`9642`),
`hasPerm(curUser,n.pm)` (`15954`), `hasPerm(curUser,pm)` (`8782`),
`hasPerm(curUser,a.nav)` (`15287`) — und der Modulname steht dann in den
Navigations- und Kacheltafeln (`pm:`/`perm:`/`nav:`, **25** Namen gemessen).
Nach der Korrektur: **0 Module ungegatet.** Der Zähler kennt jetzt alle drei
Schreibweisen und hat für jede einen Köder.

**2. „Der Wiederholungszähler wird nie gespeichert" — widerlegt.** Beim Lesen
von `doSync` sah es so aus, als werde `item._retries=retries`
(`index.html:9112`) nur auf einem Objekt gesetzt, das `SQ.getAll()` frisch aus
IndexedDB deserialisiert — dann käme kein Auftrag je auf fünf Versuche und der
Verwurfs-Toast aus R6(c) könnte nie feuern. **Nachgemessen: falsch.**
`index.html:9172` schreibt die Zähler nach der Schleife unter dem SQ-Mutex
zurück (`ODB.save("syncQueue", updated)`, v3.9.149). Die Hypothese ist tot,
der Weg ist in Ordnung, und sie steht hier, damit niemand sie noch einmal hat.

---

## 12. Was ich NICHT messen konnte — und warum

1. **Den tatsächlichen Zeilenschutz.** Es gab keinen Datenbankzugang und
   keinen Schlüssel. **Jede Aussage über RLS in diesem Bericht ist eine
   Aussage über das, was der Code in seinen Kommentaren über RLS behauptet** —
   und diese Kommentare sind teils Jahre alt (v3.9.362, v3.9.478, v3.9.820).
   Ob heute auf `defects`, `tickets`, `werkzeuge`, `fahrzeuge` oder
   `time_entries` ein Monteur schreiben darf, entscheidet allein die
   Datenbank. Die SQL-Dateien im Repo sind **kein** Ersatz: im Haus gilt die
   Regel, den Funktionsrumpf aus der DB zu ziehen und nicht aus der
   Migrationsdatei, weil im Repo Fassungen stehen, die nicht laufen.
2. **Was ein Monteur am Schirm sieht.** Kein Browserlauf, keine Anmeldung mit
   einer echten Rolle. Alles hier ist am ausgeschnittenen Quelltext gemessen.
   Die Aussage „Knopf ist für Rolle X sichtbar" ist daher überall als
   „im Code steht kein Riegel davor" zu lesen — was etwas anderes ist.
3. **Ob `user.rolle` zum Zeitpunkt der `lagerleitung`-Abfragen gesetzt ist**
   (R7b). Das braucht einen Lauf mit einer Lagerleitungs-Anmeldung.
4. **Ob PostgREST auf dieser Instanz einen abgewiesenen DELETE wirklich mit
   204 und null Zeilen beantwortet** (R2). Standardverhalten, hier nicht an der
   Instanz nachgefahren.
5. **Die Erreichbarkeit einer Schreibstelle für eine bestimmte Rolle.**
   Abschnitt 10 ist eine Näherung über Blockebenen, keine Analyse des
   Renderpfads. Eine echte Antwort bräuchte einen Lauf je Rolle im Browser —
   acht Rollen × die erreichbaren Ansichten.
6. **Die Kiosk-Rollen `lager_display` und `stempel_terminal`.** Ihre
   Schreibwege laufen über RPCs (`kiosk_field_workers`,
   `kiosk_week_arbeitsscheine`, `kiosk_fahrzeuge`) und über die
   Hash-Schreibwege, die für diesen Lauf tabu waren. Sie sind **gezählt**
   (5 bzw. 2 Vergleiche), aber nicht durchgemessen. Das ist das zweite noch
   offene Gebiet des Bughunts.

---

## 13. Vorschläge — ausdrücklich NICHT umgesetzt

Nichts davon wurde gebaut; `index.html` ist unberührt.

| | Vorschlag | Aufwand |
|---|---|---|
| R1 | Die fünf Umleitungen auf Tafel-Tabellen (`2793`, `2818`, `2833`, `2851`, `2863`) prüfen das Ergebnis von `_sbPatch`/`_sbPost` selbst, mit derselben Meldung wie `3012`. Besser: den Wächter in einen Helfer ziehen, den beide Wege rufen | klein, 5 Stellen |
| R2 | `_sbDelete`/`_sbDeleteWhere` auf `_sbWH()` umstellen und die zurückgemeldeten Zeilen prüfen. **Achtung:** das ändert das Antwortformat für alle 41 Aufrufer — und „0 gelöschte Zeilen" heißt auch „die Zeile gab es nicht mehr" | mittel, mit Folgen |
| R6c | Die Verwurfsmeldung soll die Beschriftung aus `_RLS_SILENT_DENIAL_LABELS` nennen statt des letzten URL-Segments | klein, 1 Stelle |
| R3 | `isAdmin` je Rollenmenge in einen benannten Helfer (`_istLeitung`, `_istBuerooder Leitung`) — ein Name, eine Menge | groß, 17 Stellen |
| R4/R5 | Entscheidung, nicht Messung: soll `canDo` die Einzelquelle sein? Dann müssen 36 Aktionen Aufrufer bekommen. Soll sie es nicht, gehört der tote Teil weg | Entscheidung |

**Keine davon ohne deine Freigabe** — R2 und R3 ändern, wer was darf.
