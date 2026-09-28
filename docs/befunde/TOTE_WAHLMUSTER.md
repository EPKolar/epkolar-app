# Vierundzwanzig CSS-Regeln, die nie greifen — die Schreibweise passt nicht

**Gemessen am 28.09.2026** am laufenden Baum, Ansicht `as_liste` bei 1440 px,
mit der echten Saat.

## Der Befund in einer Zeile

Mehrere CSS-Regeln zielen auf den **Inhalt des `style`-Attributs** und suchen
darin die **JavaScript**-Schreibweise. React schreibt dort aber **CSS**:

| gesucht | gefunden | dieselbe Regel in CSS-Schreibweise |
|---|---|---|
| `[style*="fontSize:24"]` | **0** | `[style*="font-size: 24px"]` → **11** |
| `[style*="display:flex"]` | **0** | `[style*="display: flex"]` → **206** |
| `[style*="position:fixed"]` | 0 | `[style*="position: fixed"]` → 0 *(in dieser Ansicht gibt es keine)* |
| `[style*="inset:0"]` | 0 | `[style*="inset: 0px"]` → 0 *(dito)* |
| `[style*="zIndex:1001"]` | 0 | — |

React setzt `style={{fontSize:24}}` als `style="font-size: 24px"` — mit
Bindestrich, mit Leerzeichen, mit Einheit. Ein Wahlmuster, das `fontSize:24`
sucht, findet das nie.

## Die Zahlen

**34 Vorkommen** von `[style*="…"]`, **25 verschiedene** Muster. Davon
**24 Vorkommen in JavaScript-Schreibweise** — also tot.

```
position:fixed      6 ×      fontSize:24         4 ×
display:flex        2 ×      zIndex:1000…2000    5 ×
fontSize:10/11/12   3 ×      inset:0             1 ×
cursor:pointer      1 ×      touch-action:none   1 ×
width:220px         1 ×
```

🔴 **Es ist schon halb aufgefallen.** Bei `width`, `cursor` und `touchAction`
steht **beides** da — einmal in JS-, einmal in CSS-Schreibweise:

```css
[style*='width:220px'], [style*='width: 220px']
[style*='cursor:pointer'], [style*='cursor: pointer']
[style*='touch-action:none'], [style*='touchAction: none']
```

Jemand hat das Problem an drei Stellen bemerkt und die zweite Schreibweise
nachgetragen — aber nicht gesucht, wo es sonst noch vorkommt. Genau die
Fehlerform, die dieser Bestand seit Wochen jagt: *eine Regel zu kennen
verhindert den Fehler nicht, solange sie nicht an EINER Stelle mit Eichung
liegt.*

## Warum das nicht nur Kosmetik ist

Ein Teil dieser toten Regeln soll die **44-px-Tippziele** erzwingen:

```css
[style*="display:flex"] > button,
[style*="display:flex"] > [role="button"] { min-height: 44px !important; }

button[title][style*="fontSize:10"],
button[title][style*="fontSize:11"],
button[title][style*="fontSize:12"] { padding: 10px !important; }
```

Die erste Regel würde **206 Behälter** treffen, wenn sie die richtige
Schreibweise benutzte. Sie greift heute an **keinem einzigen**. Der Bestand
zählt **1952 Tippziele unter 44 px** — es ist plausibel, dass ein erheblicher
Teil davon genau hier hängt. *Plausibel, nicht gemessen:* dafür müsste man die
Regeln aktivieren und neu messen, und das ist ein eigener Schritt.

## Was gemessen ist und was nicht

**Gemessen:** die Trefferzahlen oben, in `as_liste` bei 1440 px. Das Verfahren
war `document.querySelectorAll('[style*="…"]').length` für beide
Schreibweisen, direkt nebeneinander — also mit Gegenprobe.

**Nicht gemessen:**

* ob die `position:fixed`- und `zIndex`-Regeln in **anderen** Ansichten
  Treffer hätten. In `as_liste` gibt es keine Überlagerung; diese Regeln
  betreffen Dialoge und Schubladen, und die waren bei der Messung zu.
* was passiert, wenn man sie **aktiviert**. Vierundzwanzig schlafende Regeln
  gleichzeitig scharf zu schalten ist eine größere Wette als die
  Schriftgrößen: die Überlagerungs-Regeln steuern, was vor was liegt, und ein
  Fehler dort macht einen Dialog unbedienbar statt nur unschön.

## Vorschlag, getrennt nach Messbarkeit

**Messbar und deshalb machbar:** die Tippziel-Familie (`display:flex`,
`fontSize:10/11/12`). Wirkung direkt an `tipp44` ablesbar, in allen 22
Ansichten, vorher/nachher.

**Nicht von hier aus messbar:** die Überlagerungs-Familie (`position:fixed`,
`inset:0`, `zIndex:*`). Die Messreihe öffnet keine Dialoge. Diese Regeln
sollten **nicht blind** aktiviert werden — entweder die Messreihe wird um
geöffnete Dialoge erweitert, oder es bleibt eine Entscheidung mit Augenschein.

**In beiden Fällen gilt:** die zweite Schreibweise wird **ergänzt**, nicht
ersetzt. Ein `[style*="fontSize:24"]` schadet nicht, es trifft nur nichts —
und wer weiß, ob nicht irgendwo doch ein Element den Text so trägt.

---

## 🔴 Korrektur derselben Aufnahme, wenige Stunden später

Oben steht: *„Der Bestand zählt 1952 Tippziele unter 44 px — es ist plausibel,
dass ein erheblicher Teil davon genau hier hängt."*

**Das ist falsch, und es war in derselben Messreihe nachzulesen, die ich
zitiert habe.**

### Warum

Die toten Wahlmuster stehen alle in einem Block:

```css
@media (pointer: coarse), (max-width: 768px) { … }
```

Der gilt auf **Berührungsgeräten und schmalen Schirmen**. Und dort sind die
Tippziele längst in Ordnung — gemessen über alle 22 Ansichten:

| Breite | Tippziele unter 44 px |
|---|---|
| **390 px** | **0** in 21 von 22 Ansichten (`flotte`: 1) |
| 1440 px | **1939** |

**Alle 1939 sitzen am Schreibtisch**, wo dieser Media-Block gar nicht gilt. Die
Regeln zu reparieren kann dort nichts bewirken — und tut es auch nicht:

| | vorher | nach der Reparatur |
|---|---|---|
| `as_liste` @1440 | 733 | **733** |
| `werkzeuge` @1440 | 715 | **715** |
| beide @390 | 0 | **0** |

### Was daraus folgt

1. **Die Reparatur ist trotzdem richtig** — die Regeln sollen auf echten
   Telefonen greifen, und ein Wahlmuster, das nie trifft, ist eine Attrappe.
   Sie ist gebaut, mit ergänzter statt ersetzter Schreibweise.
2. **Sie ist auf der gemessenen Fläche wirkungslos**, und das steht hier, statt
   als Erfolg verbucht zu werden. Der Grund ist, dass die Nachbarregel
   `button, [role="button"], .clickable { min-height: 44px !important }` im
   selben Block längst greift — sie braucht kein `[style*=…]`.
3. **Die 1939 Tippziele sind ein Schreibtisch-Befund**, kein Telefon-Befund.
   Wer sie angehen will, muss außerhalb dieses Media-Blocks ansetzen. Das ist
   eine andere Frage als die, die ich hier gestellt hatte.

### Der Fehler dahinter

Ich hatte zwei Zahlen nebeneinandergelegt — „1952 Tippziele" und „206 Behälter,
die eine tote Regel treffen würde" — und daraus einen Zusammenhang geschlossen,
ohne zu prüfen, ob sie **auf derselben Fläche** gemessen sind. Sie sind es
nicht: die eine stammt von 1440 px, die andere gilt nur unter 768 px.

Dieselbe Form wie am Vortag bei den Diagramm-Achsen, wo ich 264 (bei 390 px)
und „8 und 9 px" (bei 1440 px) als eine Aussage geführt habe. Zwei Aufnahmen,
eine Behauptung — und beide Male hat erst das Nachmessen es aufgedeckt.
