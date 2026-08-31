# Offene Entscheidungen — acht Fragen an Sebastian

**Stand: 31.08.2026, v3.9.924.** Diese Seite fasst zusammen, was seit dem 28.08. als
`xfail(strict)` im Testlauf steht. Jede dieser Marken ist **kein Fehler im Code**,
sondern eine Frage, die niemand außer dir beantworten kann.

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
