# Skripte, die an ihrer eigenen Ausgabe sterben können

**Gemessen 30.09.2026, v3.9.995** — `python scripts/ausgabe_ueberlebt_messen.py`

## Der Befund

Am 30.09.2026 meldete die Torkette **zwei rote Tore**, ohne dass eine Messung
etwas gefunden hätte. Beide starben auf ihrem **Erfolgszweig**:

```
print("   \U0001F7E2 alle sechs richtig\n")
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f7e2'
```

Das Tor hatte gemessen, alles war richtig — und ist beim Hinschreiben des
grünen Punktes gestorben. Die Kette liest den Rückgabewert, sieht ihn ungleich
null und meldet ROT.

**Die gefährliche Richtung ist die andere.** Ein Skript, das auf dem
*Fehlerzweig* so stirbt, meldet den Fehler nie — und am Rückgabewert ist das
von einem Befund nicht zu unterscheiden. Bei einem Haken ist es noch schlimmer:
der hält den Lauf gar nicht an, dort sieht ein Absturz aus wie „nichts
gefunden". Genau so ist am selben Tag `hook_python_crlf.py` still ausgefallen —
gefunden hat ihn sein eigener Riegel, nicht ein Nutzer.

## Zwei Schreibweisen, und die zweite war die entscheidende

Mein erster Zähler suchte **Nicht-ASCII-Zeichen im Quelltext**. Im Quelltext
steht aber `\U0001F7E2` — acht ASCII-Zeichen; erst zur Laufzeit wird ein Symbol
daraus. Die beiden nachweislich toten Tore standen deshalb **nicht** in seiner
Liste: er meldete „14 betroffen", und die zwei, die wirklich sterben, waren
nicht dabei.

| Form | im Quelltext | Beispiel |
|---|---|---|
| `roh` | das Symbol selbst | `print("🟢 fertig")` |
| `esc` | reines ASCII | `print("\U0001F7E2 fertig")` |

## Was kuriert ist

**Alle zehn Tore der Kette.** Sieben Torskripte hatten die Vorkehrung nicht —
zwei sind gestorben, fünf waren latent und hätten es an dem Tag getan, an dem
ihre Meldung ein Symbol bekommt:

`node_check.py` · `_bracket_check.py` · `klammerbilanz.py` ·
`werkzeug_eichung.py` · `md5_geschuetzt.py` · `bestand.py` · `icons_erzeugen.py`

Dazu `hook_python_crlf.py`, der an derselben Stelle still ausfiel.

Gehalten wird das von zwei Riegeln, die **wirklich starten** statt den
Quelltext zu durchsuchen:

* `tests/test_tore_ueberleben_cp1252_v995.py` — jedes Torskript unter cp1252,
  die Tor-Liste aus `torkette.py` ausgelesen statt abgeschrieben.
* `tests/test_haken_ueberleben_cp1252_v995.py` — jeder verdrahtete Haken mit
  seinem eigenen Auslöser; eine Tafel-Sperre erzwingt einen Eintrag für jeden
  neuen Haken.

Beide haben eine Selbstprobe: stürzt ein absichtlich kaputter Köder **nicht**
ab, wirkt `PYTHONIOENCODING` in dieser Umgebung nicht und ein grüner Lauf
bedeutet nichts.

## Was NICHT kuriert ist — 43 Skripte

Sie stehen unten. Fast alle sind einmalige Erkundungen, die kein Tor fährt; sie
sterben nur, wenn jemand sie von Hand startet, und dann sofort sichtbar. Wer
eines davon zu einem Tor macht, fällt am Riegel auf.

🔴 **Sie sind nicht gefahren worden, und das ist Absicht.** Der erste Entwurf
des Messwerkzeugs hatte einen Schalter `--fahren`, der jedes gefundene Skript
startete. In dieser Liste stehen `cdn_abdruecke_setzen.py`,
`echtmengen_saat.py` und andere, die **schreiben**. Der Lauf wurde nach kurzer
Zeit abgebrochen; zwei Befund-Dateien waren neu geschrieben, beide gültig und
inhaltlich nur nachgemessen, `index.html` unberührt. Der Schalter ist entfernt.
Deshalb sagt diese Liste, wer sterben **kann**, nicht wer stirbt.

| Datei | roh | esc |
|---|---|---|
| `as_zeile_ansehen.py` | roh | — |
| `auslieferung_pruefen.py` | — | esc |
| `c_reste_messen.py` | roh | — |
| `cdn_abdruecke_setzen.py` | — | esc |
| `cdn_abdruecke_wirkung.py` | — | esc |
| `dialog_messen.py` | — | esc |
| `dialoge_erkunden.py` | — | esc |
| `echtmengen_messen.py` | roh | — |
| `echtmengen_planung_probe.py` | roh | — |
| `echtmengen_saat.py` | roh | — |
| `fahrzeug_kartenhoehe.py` | — | esc |
| `feiertag_live_probe.py` | — | esc |
| `geo_nachzieh_wirkung.py` | — | esc |
| `hausform_mindestmass.py` | roh | esc |
| `hellmodus_nach_dem_schalten.py` | — | esc |
| `hellmodus_schalter_messen.py` | — | esc |
| `inline_bereiche_auswerten.py` | — | esc |
| `inline_bereiche_messen.py` | — | esc |
| `keydown_container_audit.py` | — | esc |
| `klammer_regex_luecke.py` | — | esc |
| `klammertor_vergleich.py` | — | esc |
| `kopfzeile_340_messen.py` | — | esc |
| `landmarken_messen.py` | — | esc |
| `leerzustand_jagen.py` | — | esc |
| `rolle_ohne_namen.py` | roh | esc |
| `rollenflaeche_jagen.py` | — | esc |
| `schriftgroesse_wirkung.py` | — | esc |
| `stille_schreibfehler.py` | — | esc |
| `tabreihenfolge_messen.py` | — | esc |
| `tafel_austritt_wirkung.py` | — | esc |
| `tastatur_probe.py` | — | esc |
| `tastatur_probe_flaechen.py` | — | esc |
| `tastenkapern_messen.py` | — | esc |
| `thema_cssvariablen_messen.py` | — | esc |
| `thema_echter_tipp_messen.py` | roh | esc |
| `thema_iphone_messen.py` | — | esc |
| `thema_mehrmenue_messen.py` | — | esc |
| `thema_schalter_ring_messen.py` | — | esc |
| `tippziel_histogramm.py` | — | esc |
| `tote_regeln_messen.py` | — | esc |
| `version_stempeln.py` | — | esc |
| `vollabzug_jagen.py` | — | esc |
| `wisch_flaechen_messen.py` | roh | esc |

**Kur je Datei:** `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` vor der ersten Ausgabe.
