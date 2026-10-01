# -*- coding: utf-8 -*-
"""Der Hellmodus hing am Speicher — und fiel mit ihm aus.

**Sebastians Meldung, dreimal:** *„hellmodus am handy geht noch immer nicht —
der ganze Bildschirm bleibt dunkel, egal wie oft ich tippe"*.

## Nachgestellt und belegt

`scripts/hellmodus_speicher_voll.py`, gegen die **ausgelieferte** Datei,
390 px, Betriebssystem auf dunkel, drei Tipps auf den Schalter:

| Lauf | Körper nach drei Tipps | Helligkeit |
|---|---|---|
| Speicher heil | `rgb(240,242,245)` | **0.95** |
| Speicher **voll** | `rgb(15,17,23)` | **0.07** |

## Die Ursache war die Reihenfolge

    try{
      localStorage.setItem("epk_theme",mode);   // wirft
      const d=resolveTheme(mode,_systemDark());
      setIsDark(d);                             // läuft nie
      applyTheme(d);                            // läuft nie
      _themeToast(mode);
    }catch(e){console.warn('[silent-ls]',…);}

Das **Schreiben** stand vor der **Anzeige**, und beides lag im selben `try`.
Wirft `setItem`, bleibt die Oberfläche unverändert — und der `catch` schreibt
in die Konsole, die auf einem Telefon niemand sieht. Der Nutzer tippt, und
nichts passiert. Auch beim zehnten Mal nicht.

**Wann `setItem` auf einem Telefon wirft** — bekannte Fälle, keine Theorie:
iOS Safari im privaten Modus (Kontingent null), voller Speicher
(`QuotaExceededError`), oder eine Browsereinstellung, die Seitendaten sperrt.

## Die Kur hat drei Teile, und der dritte ist der wichtigste

1. **Erst anzeigen, dann speichern.** Was der Nutzer sieht, darf nicht davon
   abhängen, ob eine Festplatte mitspielt.
2. Das Speichern bekommt sein **eigenes** `try`.
3. **Und der Nutzer erfährt es.** Bisher ging die Meldung in die Konsole — auf
   einem Telefon ist das dasselbe wie gar nichts. Jetzt sagt die App, dass die
   Wahl für dieses Mal gilt und beim nächsten Start wieder weg ist. Das
   erklärt ihm, warum die App am nächsten Morgen wieder dunkel startet.

🔴 **Eine Meldung, die zu oft kommt, ist schlimmer als keine** — deshalb nur
dann, wenn das Speichern wirklich scheitert. Im Normalfall sieht niemand
etwas davon.

## 🔴 Warum vier frühere Messungen nichts gefunden haben

Gegen die ausgelieferte Datei, bei 390 px, mit dunklem Betriebssystem,
angemeldet, mit dem **Finger** getippt und zusätzlich in **WebKit** — in
allen vier Läufen wurde es nach einem Tipp hell. Jede dieser Messungen war
richtig. Sie hatten alle einen **heilen Speicher**, und genau der war die
Bedingung, unter der der Fehler nicht auftritt. Eine Messung, die den Fall
nicht enthalten kann, belegt nichts.
"""
import io
import json
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
PFAD = os.path.join(WURZEL, "index.html")
MESSUNG = os.path.join(WURZEL, "docs", "befunde",
                       "HELLMODUS_SPEICHER_VOLL.json")


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def _rumpf():
    code = _ohne_kommentare(_text())
    i = code.find("const setThemeMode=(mode)=>{")
    assert i > 0, "\U0001F534 setThemeMode ist weg."
    return code[i:i + 1400]


def test_koeder_die_kommentarbehandlung_traegt():
    mit = '/* HIER STAND localStorage.setItem("epk_theme",mode); */ x=1;'
    assert 'localStorage.setItem("epk_theme"' not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")


def test_die_anzeige_kommt_vor_dem_speichern():
    """🔴 Die eine Aussage, auf die alles ankommt."""
    r = _rumpf()
    i_anzeige = r.find("applyTheme(d)")
    i_speicher = r.find('localStorage.setItem("epk_theme"')
    assert i_anzeige > 0, "\U0001F534 applyTheme wird nicht mehr gerufen."
    assert i_speicher > 0, "\U0001F534 Die Wahl wird nicht mehr gespeichert."
    assert i_anzeige < i_speicher, (
        "\U0001F534 Das SPEICHERN steht wieder vor der ANZEIGE. Wirft "
        "localStorage.setItem -\n  voller Speicher, privates Fenster, "
        "gesperrte Seitendaten -, laeuft applyTheme\n  nie, und der Nutzer "
        "tippt ins Leere. Genau das hat Sebastian dreimal\n  gemeldet.")


def test_jedes_stueck_hat_sein_eigenes_try():
    """🔴 Ein gemeinsames `try` macht die Anzeige vom Speichern abhängig —
    auch wenn die Reihenfolge stimmt, risse ein Fehler im Speichern den
    Rest mit, sobald jemand wieder etwas dahinter schreibt."""
    r = _rumpf()
    assert r.count("try{") >= 2, (
        "\U0001F534 Anzeige und Speichern liegen wieder in EINEM try "
        "(%d gefunden, erwartet\n  mindestens 2)." % r.count("try{"))


def test_der_nutzer_erfaehrt_es_wenn_die_wahl_nicht_bleibt():
    """🔴 Eine Meldung in der Konsole ist auf einem Telefon dasselbe wie
    keine Meldung."""
    r = _rumpf()
    assert "_gemerkt" in r, (
        "\U0001F534 Es wird nicht mehr unterschieden, ob das Speichern "
        "geklappt hat.")
    assert "__toast" in r, (
        "\U0001F534 Scheitert das Speichern, erfaehrt der Nutzer nichts mehr. "
        "Dann startet die\n  App am naechsten Morgen wieder dunkel, und "
        "niemand weiss warum.")
    assert "laesst sich auf diesem Geraet nicht merken" in _text(), (
        "\U0001F534 Der erklaerende Text fehlt. 'Fehler' allein hilft "
        "niemandem, der vor der\n  Wand steht.")


def test_im_normalfall_kommt_keine_warnung():
    """🔴 Gegenprobe zur Kur: sie darf nicht bei jedem Umschalten melden.

    Was zu oft kommt, wird weggeklickt — danach ist auch der echte Fall
    unsichtbar. Die Warnung hängt deshalb am `else` des geglückten
    Speicherns, nicht am Umschalten.
    """
    r = _rumpf()
    assert "if(_gemerkt){_themeToast(mode);}" in r, (
        "\U0001F534 Die uebliche Rueckmeldung haengt nicht mehr am "
        "GEGLUECKTEN Speichern.")
    assert "else if(window.__toast)" in r, (
        "\U0001F534 Die Warnung haengt nicht mehr am else - dann koennte sie "
        "auch im Normalfall\n  feuern.")


def test_die_schirmmessung_belegt_die_kur():
    """🔴 Gemessen, nicht behauptet.

    Ein Quelltextriegel kann hier nur die Reihenfolge sehen. Ob der
    Bildschirm wirklich hell wird, wenn der Speicher streikt, sagt nur ein
    Lauf im Browser.
    """
    d = json.loads(io.open(MESSUNG, encoding="utf-8", newline="").read())
    heil = (d.get("heil") or {}).get("helligkeit")
    voll = (d.get("voll") or {}).get("helligkeit")
    assert heil is not None and voll is not None, (
        "\U0001F534 Die Schirmmessung ist unvollstaendig.\n"
        "  Lauf: python scripts/hellmodus_speicher_voll.py --lokal")
    assert heil > 0.5, (
        "\U0001F534 GEGENPROBE GESCHEITERT: schon mit heilem Speicher wird "
        "es nicht hell\n  (%.2f). Dann misst der Lauf nicht, was er "
        "behauptet - der Schalter wurde\n  nicht getroffen." % heil)
    assert voll > 0.5, (
        "\U0001F534 Mit blockiertem Speicher bleibt der Bildschirm dunkel "
        "(%.2f).\n  Die Anzeige haengt wieder am Schreiben - das ist "
        "Sebastians Fehler, zurueck.\n"
        "  Lauf: python scripts/hellmodus_speicher_voll.py --lokal" % voll)
