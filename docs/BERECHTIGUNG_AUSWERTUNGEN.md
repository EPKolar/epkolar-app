# Welche Berechtigung die Auswertungen öffnet

**Stand: 26.09.2026, v3.9.954.** Alles hier ist am Quelltext **gemessen**, nicht
aus dem Gedächtnis beschrieben. Nichts daran wurde geändert — dieses Dokument
hält fest, was heute gilt, damit die Frage nicht in drei Monaten von vorn
beginnt.

---

## Die kurze Antwort

Der Reiter **Auswertungen** hängt an einer **Berechtigung**, nicht an der Rolle
allein:

```
hasPerm(curUser, "auswertungen")
```

Die Rolle liefert den **Standard**, und du kannst ihn **pro Benutzer**
übersteuern — in beide Richtungen. Zwei Dinge bleiben aber auch **mit**
Berechtigung verborgen, und die hängen ausschließlich an der Rolle. Details
unten.

---

## 1. Wer den Reiter standardmäßig sieht

Gemessen an der Rollentabelle `ROLES` — vier von acht Rollen führen
`auswertungen` in ihren Modulen:

| Rolle | Auswertungen im Standard | Module insgesamt |
|---|---|---|
| 👑 Administrator | **ja** | 20 |
| 🏗️ Projektleiter | **ja** | 18 |
| 📋 Büro | **ja** | 19 |
| ⭐ Obermonteur | **ja** | 15 |
| 🔬 Techniker | nein | 14 |
| 🔧 Monteur | nein | 11 |
| 👷 Helfer | nein | 9 |
| 👁️ Nur Lesen | nein | 4 |

---

## 2. Wo du es pro Benutzer setzt

**Admin → Benutzer → Benutzer auswählen → Modulliste.**

Neben jedem Modul steht ein Knopf. Ist eine Übersteuerung gesetzt, zeigt die
Zeile das Wort **`OVERRIDE`**.

Der Knopf ist **zweistufig**, nicht dreistufig:

* **Erster Klick** — setzt das Gegenteil des Rollen-Standards. Ein Monteur
  bekommt Auswertungen *dazu*; einem Büro-Mitarbeiter werden sie *entzogen*.
* **Zweiter Klick** — nimmt die Übersteuerung wieder heraus. Der Benutzer folgt
  wieder seiner Rolle, und `OVERRIDE` verschwindet.

Nur ein **Administrator** kann das (`if (curUser.role !== "admin") return;`).

### 🔴 Zwei Fallen, die man kennen muss

1. **Ein Rollenwechsel löscht ALLE Übersteuerungen dieses Benutzers.**
   `setRole` schreibt `permsOverride: null`. Wer also einem Monteur die
   Auswertungen einzeln freigibt und ihn später zum Techniker macht, hat die
   Freigabe damit **stillschweigend zurückgenommen** — ohne Meldung.
2. **Ein gesperrter Benutzer hat keine Berechtigung, egal welche.**
   `hasPerm` gibt für `user.locked` immer `false` zurück, noch vor der
   Rollenprüfung.

*(Nebenbei, weil es die einzige Ausnahme im ganzen Rechtesystem ist:
`gefahrstoff` ist für **jeden** Mitarbeiter offen, unabhängig von Rolle und
Übersteuerung — gesetzlicher Zugang zu Sicherheitsdatenblättern, seit v3.9.196.
Das **Bearbeiten** hängt weiter an `canDo('gefahrstoff_edit')`.)*

---

## 3. Was auch MIT Berechtigung verborgen bleibt — und warum

Zwei Inhalte im Auswertungen-Reiter hängen **nicht** an der Berechtigung,
sondern **hart an der Rolle**:

```
_canSeeVolume = ["admin", "projektleiter", "buero"].includes(curUser.role)
```

Das ist **nicht übersteuerbar.** Es gibt keinen Knopf im Admin, der das
aufhebt. Verborgen bleiben damit:

| Inhalt | Warum |
|---|---|
| Kennzahl **Auftragsvolumen** | Geschäftszahl. Monteure, Obermonteure und Feldrollen geht sie nichts an (v3.9.527) |
| Abschnitt **Auftragsvolumen nach Geschäftsjahr** (1.7.–30.6.) | dieselbe Zahl, nach Jahren |
| die zugehörigen Zeilen im **Excel-Export** | sonst wäre die Zahl über den Export doch draußen |
| **KV-Zuschlagreport** | lohnsensibel: Normal-, Mehrarbeits- und Überstunden je Monteur und Jahr |

**Der praktisch wichtigste Fall:** ein **Obermonteur** hat `auswertungen` im
Standard und sieht den Reiter — aber **weder** das Auftragsvolumen **noch** den
KV-Zuschlagreport. Das ist Absicht und keine Lücke.

---

## 4. Die aktuelle Belegung je Benutzer

🔴 **Nicht lesbar ermittelbar, und das ist belegt statt vermutet.**

Ein Leseversuch auf die Tabelle `users` gibt mit dem ausgelieferten
Anon-Schlüssel **keine Zeile** zurück — RLS lässt keine durch. Belegt mit
Köder: dieselbe Abfrage **ohne jede Einschränkung** gibt ebenfalls nichts, und
zehn weitere Tabellen melden `Content-Range: */0`. Eine erfundene Spalte gibt
sauber `42703`, der Messweg funktioniert also. Das leere Ergebnis heißt *„mein
Messweg liefert nichts"*, nicht *„keine Benutzer"* (Nachweis in
`docs/befunde/OFFA_SCHEINE.md`, Abschnitt 4).

**Wo du sie siehst:** Admin → Benutzer. Dort steht je Benutzer die Rolle, und
jede gesetzte Übersteuerung ist mit `OVERRIDE` markiert.

**Wenn du die Belegung als Liste brauchst**, ist der kürzeste Weg eine
Leseabfrage im Supabase-SQL-Editor unter deiner angemeldeten Sitzung:

```sql
select username, name, role, active, locked, "permsOverride"
from public.users
order by role, username;
```

Rein lesend. `permsOverride` ist `null`, wenn der Benutzer seiner Rolle folgt.

---

## 5. Was NICHT geprüft ist

* **Ob die echte `users`-Tabelle dieselben Spalten führt wie die eingebauten
  Beispieldaten.** `INIT_USERS` hat acht Zeilen mit
  `id, username, name, email, role, active, monteurId, lastLogin, created,
  locked, permsOverride`. Die laufende Tabelle ist nicht gemessen.
* **Ob serverseitig (RLS) dieselben Grenzen gelten wie im Frontend.** `hasPerm`
  und `_canSeeVolume` entscheiden, was die App **zeigt**. Ob ein Benutzer die
  Daten über die Schnittstelle trotzdem **lesen** könnte, ist eine andere Frage
  und hier nicht beantwortet.
* **Die Rollen `techniker`, `helfer` und `viewer` im Echtbetrieb** — ob sie
  überhaupt vergeben sind, steht nur im Admin.
