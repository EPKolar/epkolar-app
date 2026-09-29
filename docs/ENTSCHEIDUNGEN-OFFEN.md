# Offene Entscheidungen — dreißig Fragen, davon SIEBEN erledigt

> **Stand 29.09.2026, v3.9.986.** Seit dem 28.09. hat sich dreierlei geändert,
> und zwar durch Messen, nicht durch Nachdenken:
>
> * **Frage 17 (Prüfsummen) ist erledigt** — acht cdnjs-Tags tragen einen
>   geprüften Abdruck, und die Wirkung ist am Schirm belegt, samt Köderlauf
>   mit verdorbenem Abdruck. Daraus ist die **neue Frage 30** entstanden: die
>   Dateien ganz ins Repo holen? Das löst drei Dinge, die ein Abdruck nicht
>   löst.
> * **Frage 28 ist fast beantwortet.** Die 1954 Tippziele stammten aus einer
>   Liste, die nach *Höhe* sortiert und auf zwölf geschnitten war — für die
>   *Breite* war sie blind. Neu gemessen, ungekappt, 22 Ansichten: auf dem
>   Handy sind **2099 von 2100** Zielen auf 44×44, der eine Rest ist der
>   Leaflet-Urheberhinweis. Offen bleibt nur noch der Touch-Laptop.
> * Die Zählung im Titel oben war seit dem 28.09. **falsch** (sie sagte
>   siebenundzwanzig, es waren schon neunundzwanzig). Das ist behoben.
> * **Frage 27 (Wandtafel zeigt Ausgetretene) ist in v3.9.988 gebaut** — auf
>   deinen Zuruf, samt Messung am Schirm vor und nach der Kur.

**Stand: 27.09.2026, v3.9.961.** Die Fragen 1–13 stammen vom 01.09.2026 (v3.9.928) und sind unverändert; **14 und 15** sind am 26.09. dazugekommen, **16 und 17** am 27.09. — alle vier stehen als Nachtrag am Ende.

**Stand der Fragen 1–13: 01.09.2026, v3.9.928.** Diese Seite sammelt alles, was ich gemessen, aber
nicht entschieden habe. Die Fragen 1–8 stehen seit dem 28.08. als `xfail(strict)` im
Testlauf; 9–13 sind in der Woche danach dazugekommen. Jede davon ist **kein Fehler im
Code**, sondern eine Frage, die niemand außer dir beantworten kann.

Die drei schärfsten, falls du nur drei beantworten willst: **Nummer 3** (Beweiskraft der
Mangel-Fotos — Faktor 6 im Speicher), **Nummer 11** (was passiert, wenn ein Beleg die
Cloud nicht erreicht — heute geht er verloren) und **Nummer 13** (müssen Dokumente auf
der Baustelle nur sichtbar oder auch zu öffnen sein).

> **Warum sie als Tests dastehen und nicht als Notiz:** `strict=True` heißt, sie
> werden **rot**, sobald jemand sie unbemerkt behebt. Sie sind der einzige Ort, an
> dem eine offene Frage im Testlauf sichtbar bleibt. **Bitte nicht wegräumen** —
> beantworten, dann verschwinden sie von selbst.

Jede Frage hat dieselbe Form: was heute passiert, was es kostet, und welche
Antworten möglich sind. Wo ich eine Empfehlung habe, steht sie dabei; wo nicht,
sage ich das.

---

## Die drei Foto-Fragen (gehören zusammen)

Sie betreffen dasselbe: was passiert, wenn ein Monteur auf der Baustelle einen
Mangel fotografiert. Das ist die **teuerste Nutzeraktion der App** auf einem
Handy.

### 1. Jedes Mangel-Foto wird zweimal komprimiert

**Heute:** `captureAndQueue` beginnt selbst wieder mit `compressPhoto` — das Foto
läuft zweimal durch dieselbe Rechnung. Auf einem Baustellenhandy dauert das
spürbar und kostet Akku.

**Kosten des Fixes:** kein Textersatz, sondern ein kleiner Umbau — das bereits
komprimierte Bild statt der Originaldatei weiterreichen. Drei Stellen hängen
zusammen.

**Meine Empfehlung: machen.** Hier gibt es keine fachliche Frage, nur Arbeit. Ich
habe es nicht allein gemacht, weil es mit Frage 2 zusammen umgebaut gehört.

### 2. Das volle Foto bleibt dauerhaft im Arbeitsspeicher

**Heute:** die vollständige Bilddaten-Adresse bleibt im Zustand liegen. Gemessen:
**1,78 MB je Foto** auf 25,4 MB Grundlast. Fünf Fotos sind **+8,7 MB** — genau die
Größenordnung, bei der Android den Browser-Tab verwirft. Der Monteur verliert
dann, was er noch nicht gesendet hat.

**Das Vorbild steht in derselben Datei:** der Arbeitsschein-Fotoweg legt nur die
Adresse ab, nicht das Bild.

**Meine Empfehlung: machen, zusammen mit Frage 1.**

### 3. 🔴 Wie scharf müssen Mangel-Fotos sein? — Das ist die eigentliche Frage

**Heute:** 2400 Pixel Kantenlänge bei Qualität 0,88 → **1,78 MB** je Foto.
Alternative 1600 / 0,72 → **303 KB**. Das ist Faktor 6.

**Und deshalb kann ich das nicht entscheiden:**

> Wenn ein Mangel-Foto gegenüber einem Baumeister oder vor Gericht **Beweiskraft**
> haben muss, ist **2400 / 0,88 richtig** — und dann gehört der Riegel gelöscht,
> nicht der Wert gesenkt.

Sind die Fotos dagegen nur zur Verständigung im Büro („schau dir das an"), spart
1600 / 0,72 auf jedem Handy Speicher, Zeit und Datenvolumen.

**Antwortmöglichkeiten:** `Beweiskraft` (Wert bleibt, Riegel wird gelöscht) ·
`Verständigung` (Wert wird gesenkt) · `beides` (volle Auflösung nur bei Mängeln
mit Abnahmebezug — teurer, weil es eine Fallunterscheidung braucht).

---

## Die zwei Lohnzettel-Fragen

### 4. Die Pausenspalte im Wochenblatt

**Heute:** das Wochenblatt hat **eine** Pausenspalte für die ganze Woche. Das ist
strukturell falsch — der naheliegende Fix würde nur den Montag lesen und die
anderen vier Tage stillschweigend unterschlagen.

**Was es braucht:** eine Pausenspalte **je Tag**. Das ändert das Layout des
Blattes, das unterschrieben wird.

**Frage an dich:** Soll das Wochenblatt fünf Pausenspalten bekommen — oder ist die
Pause auf dem Wochenblatt bewusst eine Wochensumme?

### 5. Ein- und Austritt mitten im Monat

**Heute:** das Monats-Blatt rechnet die Sollstunden für den **ganzen** Monat, auch
wenn jemand am 15. eingetreten ist. Ergebnis: rund **60 Stunden Minus-Saldo, den
es nicht gibt**. Ein Austrittsdatum kennt der Code überhaupt nicht.

**Frage an dich:** Wie sollen Teilmonate gerechnet werden — Sollstunden ab
Eintritt taggenau, oder pauschal anteilig? Und gibt es Austritte, die das Blatt
abbilden muss?

---

## Die zwei Fragen zur Stundenkorrektur (gehören zusammen)

### 6. Korrigierte Stunden widersprechen den Zeiten daneben

**Heute:** die Schnellkorrektur schreibt nur die Stundenzahl und lässt von/bis
stehen. Auf dem **unterschriebenen** Blatt steht dann *6 Stunden* neben
*07:00 – 16:00*.

**Frage an dich:** Sollen von/bis mitgezogen werden — oder soll die Abweichung
ausdrücklich aufs Blatt gedruckt werden („korrigiert von 9,0 auf 6,0")? Das
zweite ist ehrlicher, das erste ruhiger.

### 7. Stundenbestätigung und Zulagen-PDF laufen auseinander

**Heute:** dieselbe Stelle aktualisiert die Tagesansicht, aber nicht die
Datengrundlage des PDFs. Bis zum nächsten Neuladen zeigen die beiden
unterschiedliche Zahlen.

**Gehört mit Frage 6 zusammen entschieden** — es ist dieselbe Codestelle.

---

## Die Frage zum Startverhalten

### 8. Der Service Worker spart beim Start nichts

**Heute gemessen** (mit drosselndem Testserver): **10,9 s ohne** Service Worker,
**11,0 s mit**. Er bringt beim Start also nichts.

**Aber — und das ist der Grund, warum ich nichts angefasst habe:** v3.9.358 hat
das absichtlich so gebaut. Vorher blieben Nutzer nach einer Auslieferung auf der
alten Fassung hängen. **Ein naives „erst aus dem Zwischenspeicher" bringt genau
diesen Fehler zurück.**

**Was es bräuchte:** „erst aus dem Zwischenspeicher, dann im Hintergrund
erneuern", zusammen mit dem Hinweisband, das es schon gibt.

**Frage an dich:** Ist der Start heute langsam genug, dass sich dieser Umbau
lohnt? Wenn die App auf euren Geräten schnell genug startet, ist die richtige
Antwort **nichts tun** — und dann gehört diese Marke gelöscht.

---

## Und zwei Fragen, die aus dieser Woche dazugekommen sind

### 9. Welche Kennzahl-Kacheln brauchst du täglich? (Punkt 28)

v3.9.924 hat die Auswahl auf **eine Zeile** gelegt:

```js
const AS_KPI_KACHELN = Object.keys(AS_STATUS);   // heute alle acht
```

Kürzen kostet diese Zeile und einen Erwartungswert im Riegel. **Ersparnis
gemessen: ~65 px je Reihe am Telefon, ~77 px am Rechner.** Keine Kachel ist
Funktionsverlust — jeder Status bleibt über das Auswahlfeld erreichbar.

### 10. 🔴 Kundenname: voller Name oder mehr Scheine? (Punkt 31)

**Live gemessen, 1440×900, 15 Scheine:**

| Kundenname | Zeilenhöhe | sichtbare Scheine |
|---|---|---|
| „Huber GmbH" | 43 px | **5** |
| „Wohnbau Genossenschaft Krems Süd" | **85 px** | **3** |

Der Platz, den v3.9.924 oben gewonnen hat, geht unten wieder verloren. **Der
Mittelweg ist gemessen wertlos:** höchstens zwei Zeilen ergeben 65 px und
weiterhin nur 3 sichtbare Scheine.

**Warum ich es nicht entschieden habe:** genau dieses Abschneiden wurde in
v3.9.919 beim Monteursfeld als **Fehler** benannt. „Wohnbau Genossenschaft Krems
Süd" und „… Nord" wären in der Liste nicht mehr zu unterscheiden. Wie oft das bei
euren echten Kunden vorkommt, ist ohne Kundendaten nicht messbar.

**Antwortmöglichkeiten:** `voller Name` (bleibt wie heute) · `eine Zeile` (5 statt
3 Scheine, voller Name beim Zeigen).

---

### 11. 🔴 Was soll passieren, wenn ein Beleg die Cloud nicht erreicht? (Punkt 34)

**Heute:** bei Serviceheft, Tank-/KM-Log, KM-Korrektur und Werkzeug-Serviceheft fällt bei
einem Rechtefehler die Schreibung aus, **die Route meldet trotzdem Erfolg, und die
Warteschlange löscht den Eintrag.** Der Beleg ist weg.

**Warum ich das nicht allein entschieden habe:** ein neuer Fehler an dieser Stelle müsste
das Muster `5xx|408|429|offline` treffen, damit die Warteschlange den Eintrag behält 
— dann bleibt er bei dauerhaft dichtem RLS aber **für immer** darin stehen und wird bei
jedem Start erneut versucht. Die Alternative ist ein eigener Zustand „nicht zustellbar“,
den jemand ansehen muss.

**Antwortmöglichkeiten:** `im Versuch behalten` (nichts geht verloren, kann sich stauen) ·
`eigener Zustand` (braucht eine Ansicht dafür) · `so lassen` (der seltene Fall kostet
einen Beleg).

### 12. Sollen die Chef-Kacheln bei einem Rechtefehler Punkte zeigen? (Punkt 35)

**Heute:** rund 60 Stellen zeigen bei einem Rechtefehler eine **0**, die wie eine Tatsache
aussieht — Chef-/Admin-Kacheln, Projekt-Abzeichen, gesperrte Mitarbeiter erscheinen
verfügbar, die Attest-Spalte meldet „fehlt“ für alle. **Geschrieben wird dabei nichts.**

Nach der Linie aus v3.9.912/913 sind das keine Belege, deshalb sind sie unangetastet
geblieben. Der Umbau wäre jeweils eine Zeile (`_rlsLeer` lesen, drei Punkte statt Null).

**Frage an dich:** Ist eine 0, die in Wahrheit „nicht lesbar“ heißt, auf deinen
Chef-Kacheln ein Problem? Wenn ja, ist es ein Nachmittag Arbeit.

### 13. Dokumente offline ÖFFNEN, nicht nur sehen (Punkt 36)

**Seit v3.9.928** sind Projektdokumente, Ordner, Fotos und das Bautagebuch offline
**sichtbar** — vorher waren sie es nie, seit es diese Reiter gibt. Aber die Datei selbst
liegt nicht im Gerät: ein Klick springt **stumm** zurück, nicht einmal ein Hinweis.

**Frage an dich:** Reicht es, auf der Baustelle zu **sehen**, welche Dokumente es gibt —
oder müssen die Pläne und Datenblätter dort auch zu **öffnen** sein? Das zweite ist
Etappe 2 nach dem Muster der Pläne (ausdrücklich „mitnehmen“, mit Deckel), und es
hängt an derselben Frage wie Punkt 19: **wie groß sind eure Dokumente wirklich?**

## Und zwei, die nicht mir gehören — sondern der Datenbank

Beide gemessen, beide **nicht angefasst**: Schreibzugriffe auf die
Produktions-Datenbank passieren nur auf deine ausdrückliche Anweisung.

* 🔴 **`plans_anon_select` ist offen** — anonyme Besucher lesen **alle** Pläne,
  gefiltert wird erst im Browser. Beim Namen genannt in
  `sql/RLS_anon_scope_v3.9.155.sql:29`. Die Folge-Migration
  `migrate_anon_portal_lockdown_v3103.sql` ist **nicht appliziert**.
* **Der Checklisten-Block im Kundenportal ist tot** — `portal_fetch` liefert keine
  `checklists`, eine anon-Regel dafür gibt es nicht. Entweder Regel nachziehen
  oder den Block entfernen.

---

# Nachtrag 26.09.2026, v3.9.956 — zwei neue Fragen aus dem UI-Umbau

Der Kopf dieser Seite sagt „dreizehn Fragen" und ist damit überholt. Die beiden
hier sind **nicht** als `xfail` im Testlauf hinterlegt, sondern als Riegel, die
**rot werden, wenn jemand sie unbemerkt entscheidet** — das ist bei diesen
beiden die passendere Form, weil eine falsche Antwort schlimmer ist als keine.

### 14. 🔴 Vier Ansichten haben keine Überschrift — wie sollen sie heißen?

**Gemessen** am Schluss-Grundstand v3.9.954: von 22 Ansichten liefern **fünf**
keine einzige `h1`/`h2`/`h3`. Für eine Vorlesehilfe ist das eine Seite ohne
Gliederung — sie kann nicht sagen, wo man ist.

Eine davon ist behoben (Bauprovisorien, die Überschrift war fertig und stand
nur in einem `div`). Bei den vier anderen habe ich **absichtlich nichts
gebaut**, weil es keinen geeigneten Text gibt:

| Ansicht | Was oben steht | Warum das kein Titel ist |
|---|---|---|
| **Wochenplanung** | ◀ · `KW 39 / 2026` · ▶ · `23.09. – 28.09.` | Ein **Zeitraum** zwischen zwei Pfeilknöpfen. Er wechselt beim Blättern |
| **Zeiterfassung** | formgleich, derselbe Wochenschalter | dasselbe |
| **Flotte / Fuhrpark-GPS** | nichts mit Titelgewicht | Das „📖 Fahrtenbuch" gehört zu `FahrtenbuchView`, und die rendert laut eigenem Kommentar **als Overlay innerhalb** von FlotteView — ein Fenstertitel |
| **Startseite** | „Guten Abend, Sebastian ☀️" | Text ist da, aber es ist eine **Begrüßung**. Als Überschrift gehoben würde eine Vorlesehilfe den **Leser** ansagen, nicht die Seite |

**Warum ich nicht selbst einen erfunden habe:** eine erfundene Überschrift
sieht richtig aus und behauptet etwas, das niemand entschieden hat. Ein Titel
aus dem Bauteilnamen („FlotteView" → „Flotte"), aus dem Reiter oder frei
formuliert ist genau das. Und sie stünde dann als `h2` an der obersten Stelle
der Seite — die auffälligste Stelle, die es gibt.

**Frage an dich:** vier Wörter, eines je Ansicht. Mein Vorschlag wäre je der
Reitertext, aber das ist eine Vermutung und keine Messung — deshalb steht er
hier nicht als Empfehlung.

**Was daran hängt:** `tests/test_d9_seitenueberschriften_v956.py` macht jede
neue `h1`/`h2`/`h3` in diesen vier Ansichten **rot**, auch wenn es nach einer
Verbesserung aussieht. Wer eine setzt, nennt dort den Text und woher er kommt.
Das ist kein Verbot von Überschriften, sondern ein Verbot von Überschriften
**ohne Herkunft**.

### ~~15. Das Klammertor beurteilt 28 % von `index.html`~~ — **erledigt am 29.09.2026**

> **Das war keine Entscheidung.** Die Frage lautete „soll der Streicher neu
> gebaut werden, das Ergebnis ist eine neue Grundlinie, die erst geprüft
> werden muss". Genau das ist jetzt passiert — und die neue Grundlinie
> brauchte keine Prüfung durch dich, sie ist **null**.
>
> `scripts/klammerbilanz.py` benutzt `code_scan.ist_code`, denselben
> zustandsbasierten Abtaster, der schon fünf andere Riegel trägt und eine
> Eichprobe bestehen muss:
>
> | | altes Tor | neues Tor |
> |---|---:|---:|
> | beurteilter Anteil | 27,9 % | **54,9 %** |
> | Bilanz `()` | −1 | **0** |
> | Bilanz `[]` / `{}` | 0 / 0 | 0 / 0 |
> | nennt die Stelle | nein | **ja, mit Zeile** |
>
> **Die alte Grundlinie war ein Artefakt** — und das ist nachgerechnet, nicht
> vermutet. Der Kopftext des alten Tors behauptete seit dem 18.05.2026 das
> Gegenteil („*confirmed it is NOT a stripper artifact … a real, stable
> code-level imbalance*"). Gegengerechnet: die Klammern, die **nur** das alte
> Tor zählt, sind netto 0; die, die **nur** das neue zählt, sind netto **+1**.
> Das `−1` ist also das Spiegelbild eines `+1` in der eigenen blinden Zone
> des alten Streichers. Die falsche Notiz steht jetzt richtiggestellt in
> `scripts/_bracket_check.py`.
>
> 🔴 **Das Argument ist nicht die schönere Zahl.** Ein Tor auszutauschen,
> weil die neue Zahl gefälliger aussieht, ist dieselbe Bewegung wie eine
> Prüfung anzupassen, damit sie grün wird. Das Argument ist, dass das neue
> Tor einen Fehler findet, den das alte nicht findet — belegt an `index.html`
> selbst: eine einzelne unpaarige `(` in echten Code bei Zeile 11380 gesetzt,
> **altes Tor grün, neues Tor rot mit Zeilenangabe**
> (`scripts/klammertor_vergleich.py`; arbeitet auf einer Kopie und vergleicht
> den Abdruck des Originals davor und danach).
>
> **Das alte Tor bleibt in der Kette**, mit unveränderter Grundlinie. Es
> kommt eines **dazu**, es wird keines ersetzt — `test_klammertor_blindheit_v956`
> misst den alten Streicher weiter und hält seine Blindheit fest.
>
> **Die praktische Regel unten gilt trotzdem weiter:** kein Backtick in einen
> Kommentar von `index.html`, solange das alte Tor so gebaut ist. Es ist
> immer noch in der Kette, und es wird immer noch rot davon.

Der ursprüngliche Befund, unverändert:

#### 15. 🔴 Das Klammertor beurteilt 28 % von `index.html` — soll es repariert werden?

**Gefunden durch einen eigenen Fehler.** Ich habe in einen Blockkommentar ein
Paar Backticks geschrieben — `` `ueberschriften: []` ``, die übliche
Zitierweise dieser Datei. Danach meldete `scripts/_bracket_check.py` `() -4`
statt der Grundlinie `() -1`, und der Riegel daneben wurde rot. **Am Quelltext
war nichts falsch.**

Der Streicher in `_bracket_check.py` setzt das Template-Literal-Muster
(`` `…` ``) **vor** das Kommentarmuster. Mein Backtick wurde deshalb als
**Ende** eines viel früher geöffneten Template-Literals gelesen: ein einzelner
Treffer lief über **375.741 Zeichen echten Code** und nahm dessen Klammern mit
aus der Bilanz.

**Beim Nachmessen kam das Größere heraus.** Am heilen Stand:

```
Datei        3.663.123 Zeichen
gestrichen   2.640.833  = 72,1 %
beurteilt    1.022.290  = 27,9 %
```

Davon gehen **1.466.372 Zeichen (40,0 % der Datei)** auf 22 Treffer, die mit
einem Backtick beginnen und länger als 20.000 Zeichen sind. Bei den meisten
folgt dem Backtick **deutsche Kommentar-Prosa**:

```
"` wird BENUTZT, nicht nachgebaut; die Funktion bleibt bytegleich. */..."
"` war immer truthy -> ALLE FS-Chips hatten blauen Rand */,cursor:..."
```

Das sind keine Template-Literale. Diese Datei zitiert in Kommentaren mit
Backticks, und **jeder einzelne verschiebt die Paarung**. Die Grundlinie
`() -1` ist damit die Restsumme dessen, was übrig bleibt — **keine Aussage über
die Klammern des Codes**. In den blinden Bereichen liegen
Klammer-Ungleichgewichte im Umfang von 52.

**Das Tor ist nicht geändert, und das ist Absicht.** Ein besserer Streicher
ergibt eine andere Grundlinie, und ob eine neue Zahl ein echter Fund oder ein
Artefakt ist, kann ich nicht allein entscheiden. Ein Tor anzupassen, weil man
es besser zu wissen glaubt, ist dieselbe Bewegung wie es grün zu machen.

**Frage an dich:** soll der Streicher zustandsbasiert neu gebaut werden — so
wie `scripts/code_scan.py`, das eine Eichprobe bestehen muss und die Auskunft
verweigert, wenn es sie nicht besteht? Das wäre ein halber Tag, und das
Ergebnis ist eine **neue Grundlinie**, die erst einmal geprüft werden muss.

**Was in der Zwischenzeit schützt:**
`tests/test_klammertor_blindheit_v956.py` nagelt die Blindheit fest, damit sie
nicht weiter wächst — gestrichener Anteil höchstens 73 %, kein
**Backtick**-Treffer über 250.000 Zeichen (der längste echte ist 196.656, ein
HTML-Bericht als Template-Literal). Ausdrücklich nicht der längste Treffer
überhaupt: das ist der Changelog-Kommentar hinter `APP_VERSION` mit 256.069
Zeichen, und der wächst mit jeder Version.

**Und die praktische Regel für jeden, der hier schreibt:** in `index.html`
gehört **kein Backtick in einen Kommentar**, solange das Tor so gebaut ist.

### 16. 🔴 Elf übersprungene Prüfungen verweisen auf einen Nachfolger, der nur die *Datei* prüft

**Gemessen am 27.09.2026.** Die Stempeluhr hat mit v3.9.769 ihre Logik
umgezogen: Richtung, Doppel-Scan und Übernacht lagen vorher in der App und
liegen jetzt im Datenbank-RPC `stempel_terminal_stempel`.

Die alten Prüfungen sind dabei nicht gelöscht, sondern **übersprungen** worden —
elf Fälle in drei Dateien, jeder mit einer sauberen Begründung, die sogar den
Nachfolger nennt:

> „Richtung/Doppel-Scan/Übernacht leben jetzt im RPC
> (`sql/STEMPEL_TERMINAL_RPC_v3.sql`, gepinnt in
> `test_stempel_terminal_rpc_v769`). Dieser Pin testet toten Code."

**Das ist bis hierher richtig — und eine Stufe kleiner, als es klingt.**
`test_stempel_terminal_rpc_v769` prüft: die App ruft den RPC (13 Fälle am
`StempelTafel`-Rumpf), und die **Datei im Repo** trägt ihre Härte-Auflagen
(`SECURITY DEFINER`, `SET search_path = public`, `REVOKE ALL … FROM PUBLIC`).

Was **niemand** prüft: den Rumpf, der in der Datenbank tatsächlich **läuft**.

**Warum das in diesem Projekt kein Kleingedrucktes ist:** es ist schon
vorgekommen, dass im Repo eine Fassung steht, die nicht läuft. Eine über die
Management-API gefahrene Migration erscheint außerdem nicht im
Migrationsregister. Die Logik ist also von einem Ort, an dem sie gepinnt war
(die App), an einen Ort gewandert, an dem sie **nicht** gepinnt ist — und die
elf Skips lesen sich, als sei sie weiter abgedeckt.

**Warum ich es nicht selbst gemessen habe:** im Repo gibt es kein lesendes
Werkzeug für Funktionsrümpfe (das einzige DB-Werkzeug ist ein *schreibender*
Migrationsläufer), und der ausgelieferte Anon-Schlüssel kommt an `pg_proc`
nicht heran. Eine Zahl hätte ich hier nur erfinden können.

**Frage an dich:** einmal die laufende Fassung gegenlesen. Rein lesend, in
deiner angemeldeten Sitzung im Supabase-SQL-Editor:

```sql
select p.proname,
       p.prosecdef                              as security_definer,
       p.proconfig                              as gesetzte_einstellungen,
       pg_get_functiondef(p.oid)                as rumpf
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname = 'stempel_terminal_stempel';
```

Drei Dinge daran sind die Antwort: `security_definer` muss `true` sein,
`gesetzte_einstellungen` muss `search_path=public` enthalten, und der `rumpf`
muss mit `sql/STEMPEL_TERMINAL_RPC_v3.sql` übereinstimmen. Weicht er ab, sind
die elf Skips ohne Deckung.

**Und wenn du es beantwortet hast:** dann lohnt ein Prüfer, der das regelmäßig
gegenmisst. Er braucht aber eine Sitzung mit Leserecht auf `pg_proc` — mit dem
Anon-Schlüssel geht es nicht, und ein Prüfer, der aus Mangel an Rechten nichts
findet, meldet grün.

### ~~17. Sieben Skripte kommen von einer fremden CDN — ohne Prüfsumme~~ — **erledigt in v3.9.986 (29.09.2026)**

> **Das war keine Entscheidung, sondern ein Mangel** — deshalb ist es gebaut
> und nicht gefragt worden. Alle acht Tags (sieben Skripte **und** das
> Leaflet-Stilblatt) tragen jetzt `integrity` neben dem `crossorigin`, das
> schon da war.
>
> Die Abdrücke stammen von `api.cdnjs.com` — und weil das **selbst cdnjs**
> ist, wäre das ein Zirkel gewesen: jede der acht Dateien wurde zusätzlich
> abgerufen und ihr sha512 selbst gebildet. Acht von acht stimmten überein.
> `scripts/cdn_abdruecke_setzen.py --nachrechnen` wiederholt genau das vor
> jedem Schreiben und schreibt **nichts**, wenn einer abweicht.
>
> **Am Schirm belegt, nicht nur im Quelltext**
> (`scripts/cdn_abdruecke_wirkung.py`): echter Lauf 8/8 HTTP 200, keine
> Konsolenmeldung, React hängt im Baum. Köderlauf mit einem absichtlich
> verdorbenen Abdruck: *„Failed to find a valid digest"*, React `undefined`,
> `#root` leer — **weiße Seite**. Ohne diesen Köderlauf wäre die grüne
> Meldung wertlos gewesen.
>
> **Eine Stelle bleibt und wird benannt:** `index.html:4304` weist
> `workerSrc` zur **Laufzeit** eine Adresse zu. Die Norm kennt SRI nur für
> Tags — dort gibt es kein Attribut, an das man etwas schreiben könnte.
> Gemessen wird trotzdem, dass der Arbeiter dieselbe pdf.js-Fassung trägt wie
> das Skript im Kopf und dass es bei **genau einer** solchen Ausnahme bleibt.
>
> **Was offen bleibt, ist die größere Frage dahinter:** sollen die Dateien
> ganz ins Repo, wie es mit der Schrift Archivo in v3.9.933 gemacht wurde?
> Das löst zusätzlich Offline-Betrieb, fremde Verfügbarkeit **und** den
> Arbeiter oben. Das ist eine Entscheidung — siehe unten, Frage 30.
>
> Riegel: `tests/test_cdn_integrity_v986.py` (8 Fälle, drei Köder).
> Messung: `docs/befunde/CDN_ABDRUECKE.md`.

Der ursprüngliche Befund, unverändert:

**Gemessen am 27.09.2026.** Der Kopf von `index.html` lädt sieben Bibliotheken
von `cdnjs.cloudflare.com`. **Keine einzige** trägt ein `integrity`-Attribut:

| | |
|---|---|
| `react` 18.2.0 · `react-dom` 18.2.0 | die ganze Oberfläche |
| **`bcryptjs` 2.4.3** | **hasht die Passwörter** |
| `pdf.js` 3.11.174 | Planansicht |
| `qrcode-generator` 1.4.4 | Bauprovisorien-Aufkleber |
| `jspdf` 2.5.1 | PDF-Erzeugung |
| `leaflet` 1.9.4 | Flottenkarte |

**Was das bedeutet.** Ohne `integrity` prüft der Browser nicht, *was* er
ausführt — nur *von wo*. Liefert cdnjs eines dieser Dateien verändert aus (weil
die CDN kompromittiert ist, ein Konto übernommen oder ein Zwischenspeicher
vergiftet), führt jeder Browser den fremden Code mit allen Rechten der App aus.
Bei `bcryptjs` heißt das: die Passwörter laufen durch fremden Code.

Die CSP erlaubt `cdnjs` ausdrücklich (`script-src 'self' cdnjs`) — sie schützt
also gegen *andere* Herkünfte, nicht gegen eine veränderte Datei von cdnjs.

**Warum ich es nicht gebaut habe.** Ein `integrity`-Attribut mit einer falschen
Prüfsumme lädt die Datei **nicht** — die App wäre weiß. Sieben Hashes müssen
alle stimmen, und ich müsste sie aus dem Netz holen. Das ist kein Aufräumen,
das ist eine Änderung, die die App beim ersten Fehler unbenutzbar macht. Sowas
entscheidest du.

**Wenn du willst, ist es ein überschaubarer Schritt** — und zwar einer mit einer
klaren Gegenmessung:

1. Für jede der sieben Dateien den Hash holen. cdnjs liefert ihn selbst mit,
   pro Version, in seiner API:
   `https://api.cdnjs.com/libraries/react?fields=sri` (und so für jede).
2. Ins Skript-Tag: `integrity="sha384-…" crossorigin="anonymous"`. Das
   `crossorigin` ist nicht optional — ohne es kann der Browser die Prüfung
   nicht durchführen.
3. **Gegenmessung, und die ist der eigentliche Punkt:** die App einmal laden und
   in der Konsole nachsehen, dass *keine* der sieben Dateien blockiert wurde.
   Ein Tippfehler in einem Hash sieht genauso aus wie ein Angriff — die Datei
   lädt nicht. Ein Riegel danach ist leicht: „jedes absolute `<script src>` im
   Kopf trägt `integrity` und `crossorigin`", mit einem Köder je Form.

**Die dritte Möglichkeit, und vielleicht die bessere:** die sieben Dateien ins
Repo legen, so wie es mit Archivo schon gemacht wurde (v3.9.933, aus demselben
Grund — eine Schrift von Google scheiterte still an der CSP). Dann hängt die App
an keiner fremden Verfügbarkeit, funktioniert offline vollständig, und die Frage
nach der Prüfsumme erledigt sich. Kosten: rund 1,5 MB im Repo und ein
Aktualisierungsschritt bei jedem Versionswechsel.

**Nicht gemessen:** ob cdnjs für alle sieben Versionen einen SRI-Hash anbietet
(ich war nicht im Netz), und wie groß die sieben Dateien zusammen wirklich sind.
Die 1,5 MB sind geschätzt und als Schätzung gekennzeichnet.

---

# Nachtrag 27.09.2026, v3.9.967 — vier neue Fragen aus den fuenf Lesbarkeits-Punkten

Alle vier sind **gemessen** und alle vier sind **aufgeschoben**, nicht vergessen: jede
verlangt einen eigenen Schritt mit eigener Messung, und drei davon haben einen
Preis, der erst gemessen werden muss.

### 18. Soll die App-Hülle auf 12 px gehoben werden? (27.09.2026)

**Was gemessen ist:** nach dem Heben von Fahrzeugen, Arbeitsscheinen und
Planung bleiben bei 390 px **zwei** und bei 1440 px **sieben** Stellen unter
12 px — und **alle** sitzen in der Hülle, nicht im Inhalt einer Ansicht:

* `header`: die Firmenzeile („Der Haustechnikprofi · Visionen – Konzepte – …"),
  die Server-Anzeige, `⌘K`, `Administrator · KW 39`, der Abmelde-Knopf
* `div.bottom-nav`: die Beschriftungen unter den Symbolen
* das Sync-Banner (`🔄 Jetzt sync`, `18 ausstehend`)

**Warum es nicht einfach mitgemacht wurde:** die Hülle trägt **jede** der 22
Ansichten. Ein Griff dort verändert 22 Messwerte gleichzeitig, und dann lässt
sich nicht mehr sagen, welche Zahl von wo kommt. Bei den CSS-Regeln wurde die
Fußnavigation schon von 9 auf 12 px gehoben (v3.9.966) — was jetzt noch
übrigbleibt, sind **Inline**-Werte, die die mobile CSS-Stufe vorher verdeckt
hat und die bei 1440 px sichtbar werden.

**Die Frage:** eigener Schritt mit eigener Messung über alle 22 Ansichten —
oder bleibt die Hülle bewusst kompakt, weil sie dauerhaft sichtbar ist und
Platz kostet? Die Kopfleiste hat am 26.09. schon einmal einen Zwilling
gehabt; sie ist die empfindlichste Stelle der App.

**Nicht gemessen:** ob die Kopfleiste bei 12 px in zwei Zeilen umbricht. Genau
das war der Grund für die v3.8.81-Zweizeiligkeit.

---

### 19. Soll `svg text` in den Diagrammen auf 12 px? (27.09.2026)

Es ist die **einzige** CSS-Regel, die noch eine Schrift unter 12 px erzwingt —
10 px, für die Achsenbeschriftungen der Diagramme. Sie steht absichtlich, und
der Riegel `test_css_boden_12px_v966` hält sie **namentlich** fest: verschiebt
sich die Ausnahme oder wächst die Liste, schlägt er an.

**Warum sie steht:** Achsenbeschriftungen stehen dicht nebeneinander. 10 → 12 px
kann sie zum Überlappen bringen, und ein überlappender Text ist schlechter
lesbar als ein kleiner.

**Was zu messen wäre:** die Diagramme bei 390 und 1440 px, mit der echten Saat
(185 Arbeitsscheine liefern deutlich mehr Datenpunkte als drei), und zwar auf
**Überlappung** — nicht auf Schriftgröße. Dafür gibt es noch keinen Melder.

---

### 20. Sollen die 124 anklickbaren Nicht-Knöpfe Tastaturzugang bekommen? (27.09.2026)

**Gemessen:** 237 Elemente mit `onClick`, die keine `button` sind. 58 haben
`role` und `tabIndex` schon — das Muster ist im Haus etabliert. Nativ
erreichbare (`a`, `input`, `select`, `textarea`) und `img`/`canvas` abgezogen
bleiben 154, davon **29 reine Weiterleitungssperren**
(`onClick: e=>e.stopPropagation()`, kein Bedienelement) →
**124 echte Bedienelemente ohne Tastaturzugang**: 81 `div`, 16 `span`, 15 `th`,
7 `td`, 5 `tr`. Dicht: `ArbeitsscheinView` (29), `WeekPlan` (19), `VPlan` (11).

**Warum nicht im Rundumschlag:** die 15 `th` sind Sortierköpfe — dort gehört
ein echter Knopf hinein, nicht ein `role` auf die Zelle. Die `div`, die eine
ganze Karte oder Zeile anklickbar machen, enthalten selbst Knöpfe, und ein
Knopf in einem Knopf ist ungültiges ARIA; dort ist `tabIndex` + Tastenbehandler
ohne `role` die richtige Form (so gebaut in `ProjList`, v3.9.964). Das sind
**drei verschiedene Kuren** für eine Zahl.

**Die Klinke steht bei 124** und darf fallen, nie steigen.

---

### 21. Soll die Tageszelle der Wochenplanung mehr als drei Monteure zeigen? (27.09.2026)

`maIds.slice(0,3)` — die Tageszelle zeigt drei Namen und dann `+N`. Bei neun
aktiven Monteuren steht dort `+6`, und wer den Tag planen will, muss die Zelle
öffnen.

**Warum nicht einfach gehoben:** neun Namen in einer Zelle verdreifachen deren
Höhe, und die Wochenplanung hat sechs Tagesspalten. Seit v3.9.967 umbrechen die
Namen außerdem (statt auf sechs Zeichen gekürzt zu werden), also wächst jede
Zeile ohnehin schon.

**Nicht gemessen — und mit diesem Aufbau NICHT messbar:** wie hoch eine Zeile
mit echten Namen wirklich wird. Der Wochenplan liegt nicht im Offline-Speicher
(21 Speicher, keiner davon), `rows` kommt aus `_wpGet(kw)||W0`, und `W0` führt
die Kürzel `w1…w5` mit zwei Zeichen. Die echte Saat erreicht diese Ansicht
nicht, und der Server-Weg ist in diesem Lauf TABU.

**Die Vorfrage ist deshalb wichtiger:** soll der Wochenplan in den
Offline-Speicher aufgenommen werden? Ohne das bleibt die Wochenplanung bei
jeder Messung „nicht aussagekräftig" gestempelt — zu Recht.

---

# Nachtrag 28.09.2026 — vier Fragen aus der Gegenprüfung

Drei Messagenten haben die Arbeit vom 27.09. nachgeprüft. Diese vier Fragen
sind dabei entstanden; alle vier sind **gemessen** und keine ist ein
Aufräumwunsch.

### 22. 🔴 Bei ≤ 340 px sollen die Kopfzeilen-Knöpfe ihren Text verlieren — sie tun es nicht

Im Stilblock steht für sehr schmale Telefone (iPhone SE 1. Generation):

```css
.header-row .mob-stack button {
  font-size: 0 !important;   /* Text weg, Icon (Emoji) bleibt */
}
.header-row .mob-stack button::first-letter,
.header-row .mob-stack button { font-size: 16px !important; }
```

**Gleiche Spezifität, drei Zeilen später — die Null verliert.** Die Absicht
wirkt nicht und hat vermutlich nie gewirkt: bei 340 px steht der volle Text mit
16 px im Knopf, und das ist einer der Gründe, warum die Kopfzeile dort eng ist.

**Die Frage:** soll die ursprüngliche Absicht hergestellt werden (Text weg,
Symbol bleibt) — oder war sie von Anfang an falsch und die Null gehört
gelöscht? Beides ist vertretbar; ein Knopf ohne Text braucht dann aber ein
`aria-label`, sonst ist er für eine Vorlesehilfe stumm.

**Nachgemessen am 29.09.2026** (`python scripts/kopfzeile_340_messen.py 340`),
in **allen** Ansichten mit einer `.header-row`, nicht nur in der ersten:

| Ansicht | Knöpfe | zusammen | Überlauf |
|---|---:|---:|---:|
| werkzeuge | 4 | 416 px | **+0** |
| mitarbeiter | 3 | 352 px | +0 |
| zeit | 3 | 221 px | +0 |
| plaene | 2 | 226 px | +0 |
| as_liste | 1 | 104 px | +0 |

Die Zeile ist 324 px breit, die Knöpfe zusammen bis zu 416 — und trotzdem
**kein Querlauf**: sie brechen um. **Die tote Regel kostet Höhe, nicht
Richtigkeit.** Das ist der Grund, warum sie jahrelang niemandem aufgefallen
ist. Jeder Knopf misst 104 × 44 px und trägt 16 px Schrift; die Null ist am
Schirm bestätigt wirkungslos.

**Was die Entscheidung kostet, in Zahlen:** in `werkzeuge` bräuchten vier
Knöpfe statt 416 px nur noch rund 160 px und passten in *eine* Zeile — die
Kopfzeile wäre eine Zeile flacher. Dem stehen vier Knöpfe gegenüber, die dann
nur noch `+`, `🏷️`, `📊` und `🖨️` heißen. Ein Symbol bleibt jedem,
**ein `aria-label` hat keiner**. Wer die Absicht herstellt, muss die Namen
vorher vergeben — sonst heißt der Knopf für eine Vorlesehilfe „Drucker".

Der Riegel `tests/test_kopfzeile_340_v990.py` hält **nicht** fest, dass die
Regel tot ist — das würde bei der Kur rot. Er hält fest, was in beiden Fällen
gelten muss: bei 340 px läuft nichts quer aus dem Bild, und jeder
Kopfzeilen-Knopf behält ohne Text noch ein Zeichen oder einen Namen.

Bis zur Antwort ist die Null als **neutralisiert** im Riegel geführt: fällt die
16-px-Zeile weg, wird sie scharf und der Riegel geht rot.

---

### 23. 🔴 Das Ringdiagramm verliert Einträge — und das ist kein Schriftproblem

`SvgPie` zeichnet die Legendenzeile *i* bei `y = i*18+16` in eine `viewBox` von
nur 150 Höhe. **Ab der neunten Zeile liegt sie außerhalb und wird nie
gezeichnet.**

Gemessen: **`absTyp` verliert 7 von 15 Einträgen, `asArt` 1 von 9.**

Das ist fehlende Information, nicht kleine Information. Keine Schriftgröße
behebt es. Drei Wege: die `viewBox` mitwachsen lassen · die Legende neben statt
unter den Ring setzen · ab der neunten Zeile zusammenfassen („+7 weitere").

**Die Frage an dich:** welcher — und ist es dringend? Es betrifft die
Abwesenheitsarten, also eine Auswertung, die du vermutlich regelmäßig ansiehst.

---

### 24. Drei CSS-Regeln pflegen Bauteile, die es nicht gibt

`.ber-table`, `.badge` und das Sync-Banner-Muster treffen im Hauptdokument
**nichts**. Ich habe sie am 27.09. von 11 px auf 12 px gehoben — richtig
gedacht, wirkungslos.

* `.ber-table` kommt als Klasse in der ganzen Datei nicht vor.
* `.badge` nur in Druck- und Export-HTML, das eigene Stilblöcke mitbringt.
* Das Sync-Banner sucht `[style*="Änderungen warten"]` im *style-Attribut*,
  der Text steht aber im *Textinhalt*; und kein Knopf trägt ein `title` mit
  „Jetzt sync".

**Die Frage:** löschen oder reparieren? Löschen ist ehrlicher — eine Regel für
ein Bauteil, das es nicht gibt, täuscht den nächsten Leser. Reparieren wäre
richtig, wenn die Bauteile eigentlich gemeint sind und nur anders heißen.

**Nicht gemessen:** ob `.ber-table` früher existiert hat und umbenannt wurde.
Dafür müsste man die Historie durchgehen.

---

### 25. 🔴 MEMORY.md hat mehrere Schreiber und keine Sperre

Das ist keine Frage zur App, aber sie gehört hierher, weil sie die Grundlage
aller anderen betrifft: **die Lektionen, aus denen die Riegel entstehen.**

Gemessen (`docs/befunde/MEMORY_RISIKO.md`):

* `MEMORY.md` wird **ganz gelesen und ganz zurückgeschrieben**, ohne zu prüfen,
  ob sich die Datei seit dem Lesen geändert hat. Die Lücke zwischen Lesen und
  Schreiben ist **Minuten bis Stunden**, nicht Millisekunden.
* Der Speicherordner ist **nicht versioniert**. Es gibt keine Sicherungskopien.
* **Achtzehn** verschiedene Sitzungen haben hineingeschrieben; **zwei liefen
  heute gleichzeitig**.
* Über die Strecke, für die eine Historie existiert (18.–27.09.), ist **kein
  Verlust nachweisbar**. Davor gibt es keine Historie — und *das ist selbst der
  Befund*.
* **Ein harter Fund:** `mlg_regel_agenten_bei_freier_last.md` — deine
  Dauervorgabe, Agenten zu benutzen, wenn die Last es erlaubt — wird vom Index
  in **keiner** Schreibweise genannt. Ob nie eingetragen oder herausgefallen:
  nicht feststellbar. Die Wirkung ist dieselbe.

**Empfehlung:** zuerst `git init` im Speicherordner, mit einem Commit nach
jeder Verdichtung — alles, was sich oben überhaupt belegen ließ, ließ sich nur
belegen, weil zufällig eine Versionshistorie an anderer Stelle mitläuft. Danach
„nur anhängen, getrennt verdichten". Eine Sperrdatei löst das Problem **nicht**:
eine Sperre nur während des Schreibens verhindert keinen der konstruierten
Verluste, und eine über das ganze Lese-Schreib-Fenster sperrt die zweite
Sitzung stundenlang aus.

**Deine Entscheidung.** Das ist Datenrichtigkeit, kein Aufräumen.

---

### 26. Trägt `finkzeit.worker_id` künftig worker- oder users-IDs? (28.09.2026)

**Gemessen:** die Tabelle `finkzeit` ist **leer — 0 Zeilen**. Der Eintrag
`finkzeit.worker_id` im Lösch-Trigger `trg_workers_block_delete` ist damit
heute **wirkungslos**. Kein Fehler, nur folgenlos.

**Warum es trotzdem hier steht:** sobald FinkZeit-Daten hereinkommen, entscheidet
diese Spalte mit, ob ein Mitarbeiter gelöscht werden darf. Trägt sie
**u-IDs** statt **w-IDs**, prüft der Trigger gegen die falsche Menge — er
findet keine Referenz, lässt das Löschen durch, und die FinkZeit-Zeilen zeigen
danach ins Leere. Das ist genau die Form, die man erst merkt, wenn jemand
gelöscht ist.

Der Verdacht aus der Analyse lautet: **u-IDs**.

**Nicht gemessen** — und mit leerer Tabelle auch nicht messbar: welche Form die
Spalte tatsächlich bekommt. Das entscheidet die FinkZeit-Anbindung, nicht diese
App.

**Die Frage:** wenn die Anbindung kommt, vorher festlegen — und dann entweder
den Trigger-Eintrag anpassen oder die Spalte auf w-IDs festlegen. Eine leere
Tabelle ist der billigste Zeitpunkt dafür.

---

### ~~27. Die Kiosk-Wochenplantafel hat denselben Austrittsfehler~~ — **erledigt in v3.9.988 (29.09.2026)**

> **Auf deinen Zuruf gebaut.** `maName` in `WochenplanTafel` bekommt jetzt den
> ISO-Tag der Spalte und fragt `_wpMaSichtbarAmTag` — dieselbe Form wie in
> `WeekPlan` an seinen vier Stellen, **kein** eigener Vergleich auf
> `.austritt`. `_maIstEhemalig` wurde nur gerufen, nicht angefasst.
>
> **Am Schirm gemessen** (`scripts/tafel_austritt_wirkung.py`), mit drei
> erfundenen Leuten:
>
> | | vorher | nachher |
> |---|---|---|
> | aktiv, kein Austritt | steht da | steht da |
> | Austritt in 400 Tagen | steht da | steht da |
> | **Austritt vorige Woche** | **steht da** | **weg** |
>
> Die ersten beiden Zeilen sind die Selbstprobe — ohne sie wäre „der
> Ausgetretene ist weg" von „es wurde gar nichts gezeichnet" nicht zu
> unterscheiden.
>
> Der Riegel `tests/test_tafel_austritt_v988.py` misst die **Klasse**, nicht
> diese eine Stelle: jede Stelle, die aus einer Monteur-Kennung den *Namen*
> holt, muss im selben Block (per Klammerabgleich, nicht per Ausschnitt) die
> Prüfung stellen. Heute vier Auflösungen, drei davon Namensstellen; die
> vierte holt nur die Rolle für den Farbbalken und ist als Ausnahme
> **gebucht und mitgezählt**. Mutationsprobe an der echten Datei bestanden.

Der ursprüngliche Befund, unverändert:

Der Auftrag zu v3.9.970 hat die Kiosk-Tafel **zweimal ausdrücklich ausgenommen**
(„falls sie denselben Fehler hat: NUR melden"). Hier ist die Messung.

**`WochenplanTafel` (Zeile 7242–7350) prüft den Austritt an keiner Stelle.**
Gezählt im Bauteil: `austritt` **0 mal**, `_maIstEhemalig` **0 mal**,
`_wpMaSichtbarAmTag` **0 mal**. Die Auflösung läuft über

```js
const maName=id=>{const m=monteure.find(x=>x.id===id);return m?(m.n||''):'';};
```

— genau die Form, die in `WeekPlan` an vier Stellen behoben wurde. Ein
ausgetretener Mitarbeiter steht auf der Tafel also weiter in allen sechs
Tagesspalten.

**Der Fix wäre eine Zeile.** Alles Nötige ist dort bereits vorhanden:

* `dayDates` — ein Array von Datumswerten je Spalte (Zeile 7265)
* `_ymd` — dieselbe ISO-Formatierung, die `WeekPlan` über `dk` benutzt
* die Zellenschleife ist `DAYS.map((dn,i)=>…)`, **`i` ist im Scope**
* `_wpMaSichtbarAmTag` ist auf Modulebene und `window`-exportiert, also von
  dort aus erreichbar

Es genügte, `maName` um den Tag zu erweitern und über den Helfer zu filtern —
dieselbe Kur wie in den vier Fundstellen, nur an einer statt vier Stellen.

**Warum es trotzdem nicht gemacht ist:** die Kiosk-Tafeln stehen auf der
Tabu-Liste dieses Laufs, und der Auftrag hat sie namentlich ausgenommen. Eine
Tafel hängt an der Wand und wird von mehreren Leuten gleichzeitig gelesen; wenn
dort plötzlich Namen verschwinden, ist das eine andere Art von Änderung als im
Einzelarbeitsplatz.

**Die Frage:** soll die Tafel dieselbe Regel bekommen? Ein Satz genügt.

**Nicht gemessen:** ob `StempelTafel` und `MonteurTafel` denselben Fehler
haben. Sie führen keine Wochenplanung, aber sie lösen ebenfalls Namen auf.

---

# Nachtrag 28.09.2026, spät — vier Fragen haben sich durch Messen erledigt

Sebastians Vorgabe war „forcieren und machen". Vier der offenen Fragen sind
damit **nicht beantwortet, sondern gebaut** — und zwar so, dass die Antwort
gemessen ist statt behauptet. Sie bleiben hier stehen, durchgestrichen, mit
dem Ergebnis: eine entfernte Frage ist nicht nachprüfbar.

## ~~18. App-Hülle auf 12 px~~ — **erledigt in v3.9.972**

Die Hülle war Teil der 513 gehobenen Stellen. Die Sorge im Text („bricht die
Kopfleiste bei 12 px in zwei Zeilen um?") ist gemessen: **kein `roll` ist
gestiegen, kein `verl`** — in keiner der 44 Aufnahmen.

## ~~19. `svg text` in den Diagrammen~~ — **erledigt in v3.9.971, anders als gedacht**

Die Frage lautete „auf 12 heben oder so lassen". Die Antwort war eine dritte:
**entfernen**. Die Regel stand innerhalb von `@media (max-width: 600px)`, galt
nur am Telefon, und dort wo es weh tat (8 px am Schreibtisch) gar nicht — vor
allem aber *nahm sie zurück*: die x-Achse von `SvgBar` steht im Quelltext auf
12 und wurde auf 10 gedrückt, die Ringsumme von 15 auf 10.

`auswertungen`: **264 → 0** bei 390 px, **338 → 0** bei 1440 px.

## ~~23. Das Ringdiagramm verliert Einträge~~ — **erledigt in v3.9.971**

`SvgPie` zeichnete Legendenzeile *i* bei `y=i*18+16` in eine `viewBox` der Höhe
150 — sichtbar waren acht Zeilen. `absTyp` verlor 7 von 15, `asArt` 1 von 9.
Die Höhe wächst jetzt mit der Legende, die Breite ist mitgewachsen (bei 12 px
braucht `Pflegefreistellung (3)` 126 von 114 verfügbaren Pixeln, und der äußere
`svg` hat `overflow:hidden`).

## ~~24. Drei CSS-Regeln pflegen Bauteile, die es nicht gibt~~ — **bleibt offen**

`.ber-table`, `.badge` und das Sync-Banner-Muster treffen weiterhin nichts. Sie
sind **harmlos geworden** (alle drei stehen auf 12 px), aber sie stehen noch da
und täuschen den nächsten Leser. Löschen ist eine Aufräumfrage, keine
Messfrage — **die bleibt bei dir**.

---

## Was in der Schriftfrage NICHT erledigt ist

* **`tipp44` = 1952 Tippziele unter 44 px.** Unverändert, und nie Gegenstand
  gewesen. Das ist jetzt die größte offene Zahl des Bestands.
* **Die Tab-Reihenfolge der Arbeitsscheinliste**: 1894 Stopps bei 1440 px.
  Siehe Frage 20.
* **Die `pt`-Größen im Druck- und Export-HTML** (9pt, 8pt in den erzeugten
  Tabellen). Sie betreffen Papier, nicht den Schirm, und sind von dieser
  Messreihe nie erfasst worden. Ob 8pt auf Papier zu klein ist, ist eine
  eigene Frage — und eine, die man nicht am Bildschirm beantwortet.

---

### 20b. 🔴 Präzisierung: die 67 offenen Bedienelemente sind **zwei** Fragen, nicht eine

Frage 20 sagte: „drei verschiedene Kuren für eine Zahl". Nach dem Bau der
Sortierköpfe und der Projektliste ist die Zahl auf **67** gesunken, und beim
Durchsehen zeigt sich: der größere Teil ist gar keine Attributfrage.

**Verteilung:** 67 Stellen in **27 Bauteilen**, davon 22 mit ein bis drei
Stellen. Konzentriert sind nur `WeekPlan` (12), `ArbeitsscheinView` (7) und
`AbsView` (6).

#### Klasse A — einfache Flächen, eindeutig (rund 40 Stellen)

Eine Karte, eine Zeile, ein Eintrag, der etwas öffnet. Behandlung ist
entschieden und in `ProjList` (v3.9.964) und den Sortierköpfen (v3.9.969)
vorgeführt: `tabIndex`, Enter und Leertaste, `role="button"` **nur wenn das
Element nicht selbst einen Knopf enthält**.

Beispiel: die Fahrzeugkarte (`setSel(f.id)`) — 21 Instanzen, ein Stopp je
Karte. Die Ansicht hat heute 51 Tab-Stopps; 21 mehr sind unauffällig.

#### Klasse B — **Raster**, und das ist eine Navigationsfrage (rund 27 Stellen)

`WeekPlan` und die Arbeitsscheinliste sind **Gitter**. Dort führt „ein
Tab-Stopp je Zelle" in die Irre:

* Die Zellen-Auswahl der Wochenplanung (`setCellPick`) steht in **5 Zeilen ×
  6 Tagen = 30 Zellen**, dazu die Bemerkungsspalte. Die Ansicht hat heute **54**
  Tab-Stopps — mit einem Stopp je Zelle würden es rund **130**.
* Die Arbeitsscheinliste hat bei 1440 px **1894** Stopps bei 185 Zeilen. Drei
  anklickbare Zellen je Zeile wären **555** weitere.

Für Gitter ist der übliche Weg ein **einziger** Tab-Stopp auf das Gitter und
danach **Pfeiltasten** zwischen den Zellen. Das ist kein Attribut mehr, das ist
ein Stück Tastaturführung mit eigenem Zustand — und eine eigene Messung.

**Die Frage an dich:** sollen die beiden Gitter Pfeiltasten-Navigation
bekommen? Das ist der einzige Weg, der sie mit der Tastatur wirklich bedienbar
macht, ohne die Reihenfolge unbrauchbar zu machen.

Bis dahin bleibt Klasse B **unverändert**, und das ist Absicht: *lieber ein
fehlender Zugang als ein Phantom in der Tab-Reihenfolge* — dein Satz aus dem
ursprünglichen Auftrag.

#### Was dabei noch aufgefallen ist

Eine der 67 ist gar kein Bedienelement: ein `div` von **56 150 Zeichen** in
`WeekPlan`, dessen `onClick` nur die Zellenauswahl aufhebt, wenn man daneben
klickt. Das ist eine Fläche, kein Knopf — sie hat nur deshalb nicht in der
Klasse „keine Bedienelemente" gelandet, weil ihr Behandler mehr tut als
`stopPropagation`. Ein `role="button"` auf 56 kB Fläche wäre genau das Phantom.

---

### 28. Tippziele zwischen 24 und 44 px — am 29.09. nachgemessen, es bleibt **eine** Frage: gibt es Touch-Geräte in Schreibtischbreite?

**Der Stand nach v3.9.976/977.** Unter **24 px** liegt im Ruhezustand noch
genau ein Element, und das gehört uns nicht (der Urheberhinweis der
Kartenbibliothek Leaflet, 51.4×14, Lizenzbedingung). Das war vorher **50** in
sechs Gruppen. Auch in den geöffneten Bereichen — den vier Überlagerungen der
Hülle und den 20 Inline-Bereichen der Fahrzeugansicht — ist nichts mehr
darunter.

**Nachgemessen am 29.09.2026 mit einem Werkzeug, das nicht kappt.** Die Zahl
1954 stammte aus einer Liste, die nach **Höhe** sortiert und auf zwölf
geschnitten war — für die **Breite** war sie blind: ein hohes, schmales Ziel
fiel systematisch heraus. `scripts/tippziel_histogramm.py` zählt stattdessen
über die ganze Menge, Höhe und Breite getrennt, mit drei Ködern (20×200,
200×20, 200×200), von denen jeder genau einen Zähler auslösen darf.

22 Ansichten, beide Breiten, **ungekappt**:

| | Ziele | <24 nur hoch | <24 nur **breit** | <44 nur hoch | <44 nur **breit** | <44 beides |
|---|---:|---:|---:|---:|---:|---:|
| **1440 px** (Maus) | 2506 | 1 | **0** | 390 | **335** | 1233 |
| **390 px** (Finger) | 2100 | 1 | **0** | 1 | **0** | 0 |

Die Zahlen sind **Vorkommen**, nicht verschiedene Stellen: Kopf- und
Fußleiste zählen in jeder Ansicht mit.

**Zwei Dinge sind damit belegt, die vorher nur behauptet waren.**

1. *„Bei 390 px sind es null"* stimmt fast: es ist **eins**, und zwar
   dasselbe eine wie unter 24 px — der Urheberhinweis von Leaflet
   (`51.4×14`), kein Bedienelement, sondern eine Lizenzbedingung. Die
   Grobzeiger-Regel bei `index.html:514` hebt also **2099 von 2100** Zielen
   auf 44×44, und sie setzt `min-height` **und** `min-width`. Das ist ihre
   gemessene Wirkung, nicht mehr ihre Anwesenheit im Quelltext.
2. **335 Ziele sind hoch genug und zu schmal.** Diese Gruppe hat das alte
   Werkzeug nie gezeigt. Sie ändert nichts an der Antwort unten — aber sie
   hätte jede Kur unterlaufen, die nur `min-height` hebt. Wer die 44 px je
   ans breite Fenster holt, muss beide Maße heben; die Hausregel tut das
   bereits richtig.

Berichte: `docs/befunde/TIPPZIEL_HISTOGRAMM_1440.md` und `_390.md`.

**Warum das keine Messung mehr entscheidet.** 44 px ist die Marke für einen
**Finger**. 24 px ist die Marke, die unabhängig vom Zeigegerät gilt. Am
Schreibtisch mit einer Maus ist die Lücke dazwischen kein Fehler, sondern eine
Wahl: mehr Zeilen auf den Schirm gegen größere Ziele.

**Die Frage an dich:** Wird der Baumanagement-Schreibtisch je mit einem
**Touchscreen** bedient — Laptop mit Touch, Surface, ein Monitor in der
Werkstatt? Dann greift dort dieselbe Begründung wie am Telefon, und die 44 px
gehören auch ans breite Fenster.

* **Nein, nur Maus und Tastatur** → nichts zu tun. Die Zahl wandert aus den
  offenen Punkten in den Grundstand, mit dieser Begründung.
* **Ja, es gibt Touch-Geräte in Schreibtischbreite** → dann ist die
  Grobzeiger-Regel heute *unvollständig*: sie hängt an `pointer: coarse`
  **oder** `max-width: 768px`. Ein Touch-Laptop bei 1440 px meldet
  `pointer: fine` (Maus vorhanden) und fällt durch beide Bedingungen. Der
  saubere Weg wäre `any-pointer: coarse` statt `pointer: coarse` — eine
  einzeilige Änderung mit großer Wirkung, die vorher gemessen gehört.

Messungen dazu: `docs/befunde/UNTER24.md`, `docs/befunde/DIALOGE.md`,
`docs/befunde/INLINE_BEREICHE.json`.

---

### 29. Die Dauer eines Dispo-Blocks lässt sich nur mit der Maus ändern

**Gefunden am 28.09.2026** beim ersten Öffnen der Dispo-Ansicht durch eine
Messung (`scripts/inline_bereiche_messen.py`).

Ein Zeitblock in der Dispo hat unten eine Griffzone von 10 px Höhe. Ziehen
ändert die Dauer in 15-Minuten-Schritten. Das hängt an `onPointerDown` und hat
**keinen Tastenweg** — mit der Tastatur allein ist die Dauer nicht änderbar.

v3.9.975 hatte dem Griff versehentlich `role="button"`, `tabIndex` und einen
Tastenbehandler gegeben, dessen Rumpf nichts tut. Das ist in v3.9.978 wieder
entfernt: **lieber ein fehlender Zugang als ein Phantom in der
Tab-Reihenfolge** — dein Satz aus dem ursprünglichen Auftrag.

Die Lücke ist damit ehrlich, aber sie ist noch da.

**Die Frage an dich:** soll die Dauer per Tastatur änderbar werden? Der übliche
Weg wäre: der Block bekommt einen Tab-Stopp, und dort ändern **Pfeil hoch/
runter** die Dauer um je 15 Minuten, mit einer Ansage („90 Minuten"). Das ist
dieselbe Bauart wie die Pfeiltasten-Navigation, die Frage 20b für die beiden
Gitter offen hält — es wäre sinnvoll, beides zusammen zu entscheiden.

Solange das nicht entschieden ist, bleibt der Griff wie er ist: 242.6×10 px,
Maus und Finger, keine Tastatur, und **keine Attrappe, die etwas anderes
behauptet**.

---

# Nachtrag 29.09.2026, v3.9.986 — eine neue Frage aus einer erledigten

### 30. Sollen die neun fremden Dateien ganz ins Repo?

**Der Anlass.** Frage 17 (Prüfsummen) ist in v3.9.986 erledigt: acht Tags
tragen jetzt einen geprüften Abdruck. Beim Bauen ist aber sichtbar geworden,
dass das die *kleinere* Hälfte des Themas war.

**Was der Abdruck löst:** eine veränderte Datei von cdnjs wird nicht mehr
ausgeführt. **Was er nicht löst**, drei Dinge:

1. **`pdf.worker.min.js` bleibt ungeschützt.** Es wird zur Laufzeit als
   Adresse zugewiesen (`index.html:4304`), und die Norm kennt `integrity`
   nur für Tags. Ein Abdruck kann dort nicht stehen.
2. **Ohne Netz zu cdnjs startet die App nicht.** Kein React, keine
   Oberfläche. Auf einer Baustelle ohne Empfang ist das nicht theoretisch.
3. **Ist cdnjs weg, ist die App weg.** Der Abdruck macht die Lage dann sogar
   strenger: eine *ersetzte* Datei wird verweigert statt ausgeführt — richtig
   für die Sicherheit, aber die App bleibt trotzdem weiß.

**Der Weg ist im Haus schon gegangen worden:** die Schrift Archivo liegt seit
v3.9.933 im Repo statt bei Google. Dasselbe mit den neun Dateien löst alle
drei Punkte auf einmal.

* **Aufwand:** die Dateien holen und ablegen (rund 3,5 MB zusammen, das
  meiste `pdf.min.js` und sein Arbeiter), die neun Adressen umstellen, die
  CSP um die cdnjs-Einträge erleichtern. Ein Riegel, der prüft, dass keine
  cdnjs-Adresse mehr im Quelltext steht, ist dann einfacher als der heutige.
* **Preis:** das Repo wächst; ein Versionswechsel wird ein Commit statt einer
  Zeile. Bei sieben Bibliotheken, die seit Monaten stillstehen, ist das
  wenig.
* **Meine Empfehlung:** ja. Der einzige Grund dagegen wäre, dass jemand die
  Bibliotheken häufig hebt — das ist hier nicht der Fall.

Das ist eine Entscheidung und kein Mangel, deshalb steht sie hier und ist
nicht einfach gebaut worden. Messung dazu: `docs/befunde/CDN_ABDRUECKE.md`.
