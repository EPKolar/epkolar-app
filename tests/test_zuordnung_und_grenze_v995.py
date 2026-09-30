# -*- coding: utf-8 -*-
"""Zwei Kuren: wem eine Krankmeldung gehoert, und wann eine Liste endet.

## B1 — Krankmeldungen wurden ueber den NAMEN zugeordnet

`absence_files` traegt `worker_id` **und** `worker_name`; beim Hochladen
werden beide geschrieben. Beim Anzeigen wurde nur der Name benutzt:

* die Zuordnung legte jede Zeile unter ihrem **gespeicherten** Namen ab und
  schleppte die Kennung ungenutzt mit,
* die zweite Liste filterte mit einem **ODER** - eine Zeile galt auch dann
  als zugehoerig, wenn ihre Kennung **widersprach**.

**Drei Folgen, aufsteigend nach Wahrscheinlichkeit:**

1. **Eine Namensaenderung liess die Atteste verschwinden.** Der Name wird
   beim Hochladen festgeschrieben. Heiratet jemand oder wird ein Tippfehler
   im Stammsatz berichtigt, passte der alte Name nicht mehr - die Unterlagen
   waren in der Datenbank noch da und in der Uebersicht weg. **Das trifft
   jeden.**
2. Zwei Mitarbeiter gleichen Namens teilten sich einen Topf.
3. Eine Zeile ohne Namen fiel still heraus.

Es geht um **Gesundheitsdaten**: unter dem falschen Namen heisst, der
Falsche sieht sie; gar nicht heisst, sie fehlen, wenn sie gebraucht werden.

**Die Kur:** die Kennung hat Vorrang. Die Zuordnung laeuft ueber
`worker_id` auf den **aktuellen** Namen; der gespeicherte Name ist nur noch
der Rueckfall fuer Altzeilen ohne Kennung.

🔴 **WAS DIESE KUR NICHT HEILT, und das steht hier statt verschwiegen zu
werden:** der Abwesenheits-Speicher selbst ist namensbasiert. Die Schluessel
lauten `NAME_DATUM`, und der Primaerschluessel der Tabelle `absences` ist
laut dem Kommentar bei v3.9.623 ebenfalls `NAME_DATE`. Das ist eine
Schema-Entscheidung und gehoert auf die Entscheidungsliste, nicht in eine
Quelltext-Kur.

## B2 — jede Leseabfrage hoerte bei 5000 Zeilen auf, und niemand merkte es

`_sbGet`/`_sbGetOrder` haengen `limit=5000` an; **36 von 113** Leseaufrufen
haben keinen eigenen Filter. Was darueber liegt, kam nicht an - und die
Antwort sah aus wie eine vollstaendige. **Kein einziger Aufrufer** verglich
die Zeilenzahl mit der Grenze; der einzige `length>5000`-Treffer im ganzen
Dokument ist eine Textlaengenpruefung fuer eine Mangelbeschreibung.

Ueberschlag zu `time_entries`, ausdruecklich Rechnung und nicht Messung:
15 Leute x 1 Eintrag je Arbeitstag x 250 Tage ≈ 3750 Zeilen im Jahr. Die
5000 sind nach gut einem Jahr erreicht, und weil `date.desc` sortiert,
fallen die **aeltesten** heraus - genau die, die man fuer eine Nachrechnung
braucht.

**Die Kur:** liefert eine Abfrage genau so viele Zeilen wie ihre Grenze, ist
sie vermutlich gekappt - dann sagt die App es.

🔴 **Sie kann sich irren**, und das steht in der Meldung: eine Tabelle mit
zufaellig genau 5000 Zeilen wird gemeldet, obwohl nichts fehlt.
„Vermutlich" ist keine Hoeflichkeit, sondern die Wahrheit ueber diese
Messung. Genauer waere `Prefer: count=exact` mit `Content-Range` - im Haus
zweimal in Gebrauch -, das kostet aber je Abfrage eine Zaehlung am Server.

🔴 **Zwei Leser bleiben bewusst ohne Melder:** `_sbAuthLogin` und der
Anmeldeweg bei Zeile 784 holen keine Liste und haben keine Grenze. Der
Anker wurde deshalb je Funktion aus der Datei **geschnitten** - die Zeile
`return r.json();` kommt fuenfmal vor, und die Zeile davor ist an allen
Stellen wortgleich.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

# Drei Leser mit Grenze melden, zwei Anmeldewege nicht.
ERWARTET_MELDER = 3
ERWARTET_OHNE = 2


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    """🔴 Die Kur-Kommentare zitieren die alte Form und die Zahl 5000. Wer
    den rohen Text durchsucht, misst seine eigene Begruendung mit."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_die_kommentarbehandlung_traegt():
    mit = "/* HIER STAND r.worker_name===workerName */ x=1;"
    assert "worker_name===workerName" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")


def test_b1_die_kennung_hat_vorrang_statt_eines_oder():
    code = _ohne_kommentare(_text())
    assert ("(workerId&&r.worker_id===workerId)||"
            "(workerName&&r.worker_name===workerName)") not in code, (
        "Das alte ODER ist zurueck. Damit gilt eine Zeile auch dann als "
        "zugehoerig, wenn\n  ihre KENNUNG widerspricht - bei zwei "
        "Mitarbeitern gleichen Namens sieht jeder\n  die Krankmeldungen des "
        "anderen.")
    assert "r&&r.worker_id?String(r.worker_id)===String(workerId)" in code, (
        "Der Vorrang der Kennung fehlt. Eine Zeile MIT Kennung muss ueber "
        "die Kennung\n  passen; nur eine Altzeile ohne Kennung darf auf den "
        "Namen zurueckfallen.")


def test_b1_die_zuordnung_laeuft_ueber_die_kennung():
    code = _ohne_kommentare(_text())
    assert 'var wn=(r&&r.worker_name)||"";if(!wn)return;' not in code, (
        "Die Zuordnung legt wieder ausschliesslich nach dem GESPEICHERTEN "
        "Namen ab.\n  Dann verschwinden die Atteste bei jeder "
        "Namensaenderung aus der Uebersicht -\n  sie sind in der Datenbank "
        "noch da und nicht mehr zu sehen.")
    assert "_b1m" in code and "String(x.id)===String(r.worker_id)" in code, (
        "Die Aufloesung der Kennung auf den AKTUELLEN Namen fehlt.")


def test_b2_die_drei_leser_mit_grenze_melden_eine_kappung():
    code = _ohne_kommentare(_text())
    n = code.count("_sbGrenzeMelden(")
    assert n == ERWARTET_MELDER + 1, (
        "%d Vorkommen von `_sbGrenzeMelden(`, erwartet sind %d "
        "(%d Aufrufe + die Definition).\n  Weniger heisst: ein Leser meldet "
        "nicht mehr, und seine Liste endet wieder\n  stillschweigend an der "
        "Grenze. Mehr heisst: ein Leser ist dazugekommen - dann\n  gehoert "
        "diese Zahl angesehen, nicht weggezaehlt."
        % (n, ERWARTET_MELDER + 1, ERWARTET_MELDER))


def test_b2_die_anmeldewege_bleiben_ohne_melder():
    """🔴 Gegenprobe: der Melder darf sich NICHT ueberall hinsetzen.

    `_sbAuthLogin` und der Anmeldeweg holen keine Liste und haben keine
    Grenze. Ein Melder dort wuerde bei jeder Anmeldung etwas ueber gekappte
    Listen behaupten.
    """
    code = _ohne_kommentare(_text())
    n = code.count("  return r.json();")
    assert n == ERWARTET_OHNE, (
        "%d Rueckgaben ohne Melder, erwartet sind %d (die beiden "
        "Anmeldewege).\n  Weicht die Zahl ab, ist ein Leser dazugekommen "
        "oder weggefallen." % (n, ERWARTET_OHNE))


def test_b2_der_melder_nennt_seine_unsicherheit():
    """Eine Meldung, die mehr behauptet als sie weiss, ist schlimmer als
    keine."""
    t = _text()
    i = t.find("function _sbGrenzeMelden(")
    assert i > 0, "Der Melder ist weg."
    rumpf = t[i:i + 1400]
    assert "vermutlich" in rumpf.lower(), (
        "Die Meldung sagt nicht, dass sie sich irren kann. Eine Tabelle mit "
        "zufaellig\n  genau 5000 Zeilen wird gemeldet, obwohl nichts fehlt - "
        "das gehoert in den Text.")
    assert "__toast" in rumpf, (
        "Der Melder sagt dem NUTZER nichts - dann ist die Kappung weiterhin "
        "still.")
