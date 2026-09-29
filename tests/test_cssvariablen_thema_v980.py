# -*- coding: utf-8 -*-
"""Die CSS-Variablen folgen dem Thema - sie waren fest auf DUNKEL.

🔴 EINE GANZE SCHICHT, DIE DAS THEMA NICHT KANNTE.
In `:root` standen nur dunkle Werte:

    --bg:#0f1117  --sb:#161922  --cd:#1c1f2e  --bd:#2a2e3f
    --tx:#e4e4e7  --dm:#71717a  --mt:#52525b

`applyTheme` hat sie nie angefasst. Gemessen im Hellmodus - nach dem
Umschalten UND bei vorgegebener Wahl - blieb `--bg` auf #0f1117 und `--tx`
auf #e4e4e7. In BEIDEN Faellen: das war kein Umschaltfehler, sondern eine
Schicht ohne Themenbezug.

🔴 WARUM ES TROTZDEM MEIST HELL AUSSAH - und warum das die Suche verlaengert
hat. Der dynamische Stilblock `GCSS()` deklariert die wichtigen Regeln
(`body`, `select`, `option`, `input[type=date]`) mit den LIVE-Themenwerten neu
und steht spaeter im Dokument; er gewinnt. Gemessen: `select{color:#1a1d26}`
im Hellmodus, richtig, in beiden Laeufen. Uebrig blieben die Regeln, die
GCSS nicht noch einmal fuehrt:

    ::-webkit-scrollbar-thumb { background: var(--bd) }
    .login-title              { color: var(--dm) }
    input[type="date"]::-webkit-calendar-picker-indicator
                              { filter: invert(.8) }   <- FEST verdrahtet

Das Kalendersymbol war der klarste Fall: `invert(.8)` dreht ein dunkles
Symbol ins Helle - im Hellmodus stand es damit hell auf hell. Der richtige
Wert lag im Thema bereit (`calInv`) und wurde nur im dynamischen Block
benutzt.

🔴 `--ac` IST ABSICHTLICH NICHT DABEI, und diese Ausnahme steht als PRUEFUNG
hier, nicht als Satz in einem Kommentar. Es fuehrt #f97316 (orange), waehrend
das Thema EP-Gruen fuehrt. Orange ist die FOKUSFARBE (Fokusring,
Kaestchen-Akzent) und als solche themenunabhaengig gewaehlt; sie auf Gruen zu
ziehen wuerde den Fokusring gegen die vielen gruenen Flaechen der App
schlechter unterscheidbar machen. Das ist eine Gestaltungsfrage - sie gehoert
entschieden, nicht stillschweigend geaendert.

🔴 WAS DIESER RIEGEL MISST UND WAS NICHT. Er liest den QUELLTEXT. Ob die
Variablen am Schirm wirklich umspringen, misst daneben:

    python scripts/thema_cssvariablen_messen.py

Stand 29.09.2026, mit Selbstprobe auf zwei verschiedene Modi:

    --bg   hell #f0f2f5   dunkel #0f1117
    --tx   hell #1a1d26   dunkel #f0f0f2
    --calinv  hell none   dunkel invert(.8)
"""
import io
import os

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Die Variablen, die ueber hell und dunkel entscheiden.
GESETZT = ["bg", "sb", "cd", "bd", "tx", "dm", "mt"]


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def test_applytheme_setzt_die_variablen():
    t = _text()
    assert '["bg","sb","cd","bd","tx","dm","mt"].forEach(' in t, (
        "applyTheme setzt die CSS-Variablen nicht mehr aus dem Thema.\n"
        "  Dann steht `:root` wieder fest auf den dunklen Werten, und jede "
        "CSS-Regel,\n  die GCSS() nicht noch einmal fuehrt, bleibt im "
        "Hellmodus dunkel.")
    assert '_r.style.setProperty("--"+k,_t[k])' in t, (
        "Die Zuweisung an document.documentElement fehlt.")


def test_das_kalendersymbol_folgt_dem_thema():
    t = _text()
    assert "filter: var(--calinv, invert(.8));" in t, (
        "Das Kalendersymbol steht wieder fest auf `invert(.8)`.\n"
        "  Das dreht ein dunkles Symbol ins Helle - im Hellmodus steht es "
        "dann hell auf hell.")
    assert '_r.style.setProperty("--calinv",_t.calInv||"none")' in t, (
        "`--calinv` wird nicht mehr gesetzt. Der Rueckfallwert im CSS haelt "
        "dann die\n  DUNKLE Darstellung fest.")


def test_alle_sieben_variablen_stehen_in_der_liste():
    """Eine Liste, aus der jemand still eine Variable entfernt, faellt sonst
    niemandem auf - die Regel wuerde einfach wieder dunkel bleiben."""
    t = _text()
    i = t.index('["bg","sb","cd","bd","tx","dm","mt"]')
    liste = t[i:i + 40]
    for k in GESETZT:
        assert '"%s"' % k in liste, (
            "Die Variable --%s wird nicht mehr gesetzt und bleibt damit auf "
            "ihrem\n  dunklen Wert aus `:root`." % k)


def test_der_akzent_bleibt_ausdruecklich_aussen_vor():
    """🔴 Eine Ausnahme ohne Begruendung ist eine Attrappe - hier steht sie
    als Pruefung.

    `--ac` wird NICHT aus dem Thema gesetzt. Es fuehrt Orange als Fokusfarbe,
    das Thema fuehrt EP-Gruen. Wer die Variable in die Liste aufnimmt, aendert
    Fokusring und Kaestchen-Akzent in BEIDEN Themen von Orange auf Gruen -
    und macht den Fokus gegen die gruenen Flaechen der App schlechter
    sichtbar. Das darf passieren, aber nicht nebenbei.
    """
    t = _text()
    i = t.index('["bg","sb","cd","bd","tx","dm","mt"]')
    assert '"ac"' not in t[i:i + 40], (
        "`--ac` ist in die Liste gewandert. Damit wechseln Fokusring und\n"
        "  Kaestchen-Akzent von Orange auf EP-Gruen - eine Gestaltungs"
        "entscheidung,\n  die gemessen und entschieden gehoert, nicht "
        "nebenbei gemacht.")
    assert "--ac: #f97316" in t or "--ac:#f97316" in t, (
        "Der Akzent steht nicht mehr auf #f97316. Wenn das Absicht ist, "
        "gehoert die\n  Begruendung hierher - und die Fokus-Sichtbarkeit "
        "nachgemessen.")
