# -*- coding: utf-8 -*-
"""v3.9.909 - Fuenf Zeitfenster, und eine gemeinsame Wurzel: die Zeitumstellung.

Die Klasse hat an einem Tag SECHSMAL zugeschlagen. Erst drei einzeln:

    v3.9.897  Fahrtenbuch: `from + 32*TIME_DAY` als "Monat" - Februar lud bis
              zum 4. Maerz, Kilometergeld wurde zweimal ausgewiesen. LOHN.
    v3.9.901  "Abwesend diese Woche" bei HEUTE abgeschnitten, die Nachbarzahl
              nicht - am Montag stand 0 neben 1.
    v3.9.907  "naechste Woche" auf +(14-day): Montag bis SAMSTAG, der Sonntag
              fiel heraus.

Dann ein eigener Durchgang ueber ALLE Fenster der Datei - und der hat gezeigt,
dass vier der fuenf neuen Befunde derselbe Denkfehler in vier Kleidern sind:

    EIN TAG IST NICHT 24 STUNDEN LANG.

Am letzten Sonntag im Oktober hat er 25, Ende Maerz 23. Wer mit `+TIME_DAY`
rechnet oder zwei verschieden geparste Mitternachten vergleicht, verliert oder
verdoppelt genau eine Stunde - und diese eine Stunde reicht, um einen ganzen
Tag aus einem Fenster fallen zu lassen.

────────────────────────────────────────────────────────────────────────────
Was gemessen wurde, mit Zahlen
────────────────────────────────────────────────────────────────────────────
1 URLAUB, LOHNRELEVANT - und es ist MEIN Fehler aus v3.9.897. Die
  Werktage-Zaehlung der Antragskarte lief ueber die Zeitumstellung falsch:

      19.10.-30.10.2026   Karte "9 Werktage"   gebucht 10
      20.10.-31.10.2025   Karte "9"            gebucht 10
      24.10.-26.10.2026   Karte "0"            gebucht 1

  Zwei Zahlen ueber DENSELBEN Antrag, die sich widersprechen - genau die
  Krankheit, die ich mit v897 beheben wollte. Trifft jedes Jahr.

2/3 STEMPELUHR, LOHNRELEVANT. Das Fensterende wurde als UTC-Mitternacht
  gerechnet: am 25.10.2026 endet es um 23:00 Ortszeit statt um Mitternacht.
  Ein Stoerungsdiensttechniker, der Sonntag um 23:10 ausstempelt, taucht in
  der PZE-Maske nicht auf - sein Tag steht als Kommen OHNE Gehen da.

4 BAUTAGEBUCH. Das Fenster "diese Woche" hatte gar kein Ende - ein Tippfehler
  im Datum (2027 statt 2026) hebt die Zahl DAUERHAFT an, waehrend "gesamt"
  danebensteht und nicht mitwaechst.

5 UEBERFAELLIG. "N Tage ueber Frist" zaehlte im ganzen Sommerhalbjahr einen zu
  wenig; am 30.03. stand "0 Tage ueber Frist" neben einem Posten, der in der
  Ueberfaelligenliste steht. Der Fehler hebt sich Ende Oktober von selbst auf -
  deshalb ueberlebt er jede Nachrechnung im Winter.

────────────────────────────────────────────────────────────────────────────
Warum dieser Riegel Code AUSFUEHRT
────────────────────────────────────────────────────────────────────────────
Ein Zeitfenster kann man nicht an seiner Schreibweise pruefen. `+(14-day)` sieht
genauso vernuenftig aus wie `+(15-day)`, und `+TIME_DAY` sieht sogar besser aus
als eine Kalenderrechnung. Der Riegel schneidet die Ausdruecke deshalb woertlich
aus index.html und laesst sie in Node gegen echte Stichtage laufen - Montag,
Sonntag, Monatsgrenze, Schaltjahr und beide Zeitumstellungen -, mit
`TZ=Europe/Vienna`.

Gemessen in beide Richtungen: gegen den Stand VOR den Reparaturen sind alle
fuenf ROT (mit den Zahlen oben), danach alle gruen.
"""
import os
import subprocess

from conftest import EPK_TEST_TIMEOUT

SKRIPT = os.path.join("scripts", "riegel_zeitfenster.js")


def _lauf(node_exe, repo_root, ziel):
    return subprocess.run(
        [node_exe, os.path.join(repo_root, SKRIPT), ziel],
        cwd=repo_root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT,
    )


def test_das_skript_ist_da(repo_root):
    assert os.path.isfile(os.path.join(repo_root, SKRIPT)), (
        "scripts/riegel_zeitfenster.js fehlt - dann gibt es keinen Riegel "
        "mehr, der Zeitfenster ueber die Zeitumstellung prueft."
    )


def test_alle_fenster_halten(node_exe, repo_root, index_html):
    r = _lauf(node_exe, repo_root, os.path.join(repo_root, "index.html"))
    assert r.returncode == 0, (
        "Mindestens ein Zeitfenster rechnet falsch:" + chr(10)
        + (r.stdout or "")[-1500:] + (r.stderr or "")[-400:]
    )
    assert "GRUEN" in (r.stdout or ""), (
        "Der Riegel meldet kein Ergebnis - lief er ueberhaupt?" + chr(10)
        + (r.stdout or "")[:500]
    )


def test_umkehrprobe_der_riegel_kann_rot_werden(node_exe, repo_root, index_html, tmp_path):
    """DIE GEGENPROBE. Der Fehler mit der groessten Lohnfolge wird kuenstlich
    wieder eingebaut - die Werktage-Zaehlung des Urlaubsantrags rechnet dann
    wieder mit festen Tagesabstaenden statt kalendarisch.

    Ohne diese Probe waere der Riegel oben gruen, ohne dass jemand wuesste, ob
    er ueberhaupt etwas messen KANN."""
    kaputt = index_html.replace(
        "for(var d=new Date(a);d<=b;d.setDate(d.getDate()+1))",
        "for(var d=new Date(a);d<=b;d=new Date(d.getTime()+TIME_DAY))", 1)
    assert kaputt != index_html, (
        "Der Rueckbau griff nicht - die Werktage-Schleife sieht anders aus als "
        "erwartet, und diese Probe misst dann nichts."
    )
    p = tmp_path / "kaputt.html"
    p.write_text(kaputt, encoding="utf-8")
    r = _lauf(node_exe, repo_root, str(p))
    assert r.returncode != 0, (
        "Der Riegel bleibt gruen, obwohl die Werktage-Zaehlung wieder mit "
        "festen Tagesabstaenden rechnet - er ist damit wertlos:" + chr(10)
        + (r.stdout or "")[-900:]
    )
