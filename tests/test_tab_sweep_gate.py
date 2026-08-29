# -*- coding: utf-8 -*-
"""Das Gate, das beim ersten Lauf an sich selbst starb (29.08.2026).

Ohne Versionsnummer im Namen, weil dieser Riegel ein SKRIPT sichert und keine
App-Version - index.html ist dafuer unveraendert geblieben.

`scripts/tab_sweep.py` ist das EINZIGE Gate, das eine bestimmte Fehlerklasse
ueberhaupt sehen kann: eine Ansicht, die erst beim Anklicken abstuerzt. Am
25.08.2026 stand der Tab "Monatsabrechnung" monatelang kaputt live, weil eine
Callsite eine nicht existierende Bindung durchreichte - und wegen des
&&-Kurzschlusses wird der Ausdruck NUR ausgewertet, wenn genau dieser Tab aktiv
ist. Kein statisches Gate kann das sehen: node_check parst nur, der
Klammer-Riegel zaehlt, pytest prueft Text, und der Browser-Check laedt allein
die Startseite.

Das Skript stand seit dem 28.08. im Repo und war dreimal im Handoff als "nie
ausgefuehrt" vermerkt. Beim ERSTEN echten Lauf am 29.08. ist es an der ERSTEN
Ansicht gestorben - und zwar nicht an der App:

    Version: 3.9.896-supabase
    UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f3e0'

Die Tab-Namen der App tragen Emoji ("Home" heisst dort mit Haus-Zeichen davor),
und Windows-stdout ist cp1252. Der Absturz sass also nicht im MESSEN, sondern im
BERICHTEN: das Gate hat Ansicht 1 korrekt geprueft und ist dann beim Ausgeben
des Ergebnisses umgefallen. Es haette nie einen Befund melden koennen.

Das ist dieselbe Krankheit wie die geloeschte index.html, nur andersherum: dort
meldete ein Gate GRUEN, wo alles weg war; hier konnte ein Gate ueberhaupt nichts
melden. Beide Male war das Messgeraet das Problem, nicht das Gemessene.

Nach der Reparatur (stdout/stderr auf UTF-8) lief der Durchlauf gegen die
Live-App vollstaendig durch: alle 18 Ansichten sauber, Version 3.9.896.

WAS DIESER RIEGEL PRUEFT: nicht die Schreibweise der Reparatur, sondern ihre
Wirkung - dass das Modul auch dann einen Emoji-Namen ausgeben kann, wenn die
Umgebung cp1252 vorgibt. Genau der Fall, der live eingetreten ist.
"""
import os
import subprocess
import sys

import pytest

from conftest import EPK_TEST_TIMEOUT

SKRIPT = os.path.join("scripts", "tab_sweep.py")

# Das Haus-Zeichen aus dem ersten Tab-Namen - der Character, an dem es starb.
EMOJI = "\U0001f3e0"


def _lauf(repo_root, code, encoding):
    """Fuehrt `code` in einer Umgebung aus, die stdout auf `encoding` festnagelt."""
    umgebung = dict(os.environ)
    umgebung["PYTHONIOENCODING"] = encoding
    umgebung["PYTHONPATH"] = os.path.join(repo_root, "scripts")
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root, env=umgebung, capture_output=True,
        encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT,
    )


def test_das_skript_existiert(repo_root):
    assert os.path.isfile(os.path.join(repo_root, SKRIPT)), (
        "scripts/tab_sweep.py fehlt - dann gibt es kein Gate mehr, das eine erst "
        "beim Anklicken abstuerzende Ansicht sehen kann."
    )


def test_es_kann_einen_emoji_tabnamen_ausgeben(repo_root):
    """DER KERN. Die Tab-Namen der App tragen Emoji. Kann das Skript sie nicht
    ausgeben, stirbt es beim ersten Treffer - egal wie gut es misst."""
    code = ("import tab_sweep" + chr(10) +
            "print('  %-20s ok' % '" + EMOJI + " Home')")
    r = _lauf(repo_root, code, "cp1252")
    assert r.returncode == 0, (
        "tab_sweep kann einen Emoji-Tabnamen nicht ausgeben, wenn stdout cp1252 "
        "ist - genau der Absturz vom 29.08., der das Gate an Ansicht 1 beendet "
        "hat:" + chr(10) + r.stderr[-600:]
    )
    assert "ok" in r.stdout


def test_umkehrprobe_ohne_die_reparatur_stirbt_es(repo_root):
    """Die Gegenprobe MUSS zeigen, dass der Riegel etwas misst: ohne das Modul
    (also ohne dessen Umstellung von stdout) faellt derselbe print um.

    Waere das hier gruen, pruefte der Test oben nur, dass Python laeuft."""
    code = "print('  %-20s ok' % '" + EMOJI + " Home')"
    r = _lauf(repo_root, code, "cp1252")
    assert r.returncode != 0 and "UnicodeEncodeError" in r.stderr, (
        "Umkehrprobe: ohne tab_sweep laeuft der Emoji-print hier durch. Dann "
        "misst der Riegel darueber nichts - vermutlich ignoriert diese "
        "Python-Fassung PYTHONIOENCODING, und der Test braucht einen anderen "
        "Aufbau." + chr(10) + "stdout=" + repr(r.stdout[:200]) +
        chr(10) + "stderr=" + repr(r.stderr[-300:])
    )


def test_das_importieren_hat_keine_nebenwirkung(repo_root):
    """Gegenprobe: der Riegel oben importiert das Modul. Wuerde dabei der
    Browser-Durchlauf starten, waere jeder Testlauf zwei Minuten laenger und
    haette eine Netzabhaengigkeit."""
    code = ("import tab_sweep" + chr(10) +
            "print('IMPORT-OK', hasattr(tab_sweep,'main'))")
    r = _lauf(repo_root, code, "utf-8")
    assert r.returncode == 0, r.stderr[-400:]
    assert "IMPORT-OK True" in r.stdout, (
        "Das Modul laesst sich nicht folgenlos importieren oder hat keine "
        "main()-Funktion mehr:" + chr(10) + r.stdout[:300]
    )


@pytest.mark.parametrize("begriff", ["401", "403", "supabase"])
def test_der_testzugang_wird_als_rauschen_erkannt(repo_root, begriff):
    """Der Durchlauf meldet sich mit einem gebauten Token an; die Datenabrufe
    laufen darum in 401/403. Stuende das nicht auf der Ignorierliste, meldete
    das Gate bei JEDEM Lauf Fehler - und ein Gate, das immer rot ist, wird
    genauso ignoriert wie eines, das immer gruen ist."""
    quelle = open(os.path.join(repo_root, SKRIPT), encoding="utf-8").read()
    i = quelle.find("IGNORIEREN")
    assert i != -1, "Die Ignorierliste fehlt"
    liste = quelle[i:quelle.find(")", i)]
    assert begriff in liste, (
        "'%s' steht nicht auf der Ignorierliste - dann meldet der Durchlauf das "
        "Rauschen des Testzugangs als Befund." % begriff
    )
