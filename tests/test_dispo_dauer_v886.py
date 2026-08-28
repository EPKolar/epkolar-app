# -*- coding: utf-8 -*-
"""v3.9.886 - Derselbe Schein hatte zwei verschiedene Dauern, je nachdem WIE er
auf den Tag kam - und die falsche ging bis nach OFFA.

BEFUND: `_dispoDauer(schein, regeln, gelernt, typMedian)` hat eine Quellenkette:
gesetzte `dauer` > gelernter Klassen-Median (ab n>=8) > Typ-Median > Text-Stichwort
> 90 min. Die beiden mittleren Stufen brauchen die uebergebenen Maps.

    Plan            _dispoDauer(s, null, _gelernt, _typMed).min   <- vierarmig
    Warteliste-Zug  _dispoDauer(s).min                            <- EINARMIG

Nicht aus Nachlaessigkeit: `_dispoBuildInput` gab `_gelernt`/`_typMed` gar nicht
heraus, die Wartelisten-Stelle konnte sie also nicht benutzen.

WARUM DAS MEHR IST ALS EIN ANZEIGEFEHLER: der Drop schreibt die Dauer via
`updAs({dauer:...})`, und `dauer` steht in `JUPROWA_PUSH_FIELDS`. Ein
Reparatur-Schein ohne eigenes Dauerfeld war im Plan z.B. 120 min, aus der
Warteliste gezogen 90 - und der falsche Wert landete in der Datenbank UND im
Fremdsystem. Die Kapazitaetspruefung des Drops rechnete ebenfalls mit ihm.

FIX: `_dispoBuildInput` gibt die beiden Maps heraus, der Wartelisten-Zug benutzt
dieselbe Kette wie der Plan. Kein zweiter Rechenweg - dieselbe Funktion, dieselben
Argumente.
"""
import re


def _wl_aufruf(index_html):
    """Der _dispoDauer-Aufruf im Wartelisten-Zug (_chipDrag)."""
    i = index_html.find("onPointerDown:_wlDrag?_chipDrag(")
    assert i != -1, "Der Wartelisten-Zug ist nicht mehr auffindbar."
    return index_html[i:i + 500]


def test_die_mediane_werden_herausgegeben(index_html):
    assert "gelernt:_gelernt, typMed:_typMed};" in index_html, (
        "_dispoBuildInput gibt die gelernten Dauer-Mediane nicht heraus - dann "
        "kann die Wartelisten-Stelle sie gar nicht benutzen und rechnet wieder "
        "einarmig."
    )


def test_warteliste_nutzt_dieselbe_quellenkette(index_html):
    block = _wl_aufruf(index_html)
    assert "_dispoDauer(s,null,(_built&&_built.gelernt)||null,(_built&&_built.typMed)||null)" in block, (
        "Der Wartelisten-Zug ruft _dispoDauer nicht mehr mit den gelernten "
        "Medianen - dann schreibt er wieder eine andere Dauer als der Plan, und "
        "die geht via dauer/JUPROWA_PUSH_FIELDS bis nach OFFA:\n" + block[:300]
    )


def test_der_aufruf_ist_gegen_fehlendes_built_abgesichert(index_html):
    """_built ist ein useMemo mit try/catch, das im Fehlerfall null liefert.
    Ohne Absicherung wuerfe die Geste beim Anfassen des Chips."""
    block = _wl_aufruf(index_html)
    assert "(_built&&_built.gelernt)" in block and "(_built&&_built.typMed)" in block, (
        "Der Zugriff auf _built ist nicht abgesichert - _built kann null sein "
        "(try/catch im useMemo), dann wirft die Zieh-Geste."
    )


def test_der_plan_rechnet_unveraendert(index_html):
    """Gegenprobe: der Plan-Pfad darf sich NICHT geaendert haben - sonst haette
    ich die Dauern auf beiden Seiten verschoben statt sie anzugleichen."""
    assert "var d=_dispoDauer(s,null,_gelernt,_typMed).min;" in index_html, (
        "Der Plan-Aufruf hat sich veraendert. Ziel war, die Warteliste an den "
        "Plan anzugleichen - nicht beide zu verschieben."
    )
    assert "dauerMin:_dispoDauer(s,null,_gelernt,_typMed).min," in index_html, (
        "Der zweite Plan-Aufruf (dauerMin je Schein) hat sich veraendert."
    )


def test_dauer_ist_und_bleibt_ein_push_feld(index_html):
    """Der Grund, warum dieser Fehler mehr als kosmetisch war. Faellt dauer aus
    der Push-Liste, ist der Befund kleiner - dann gehoert dieser Test angepasst,
    nicht stillschweigend ignoriert."""
    i = index_html.find("JUPROWA_PUSH_FIELDS")
    assert i != -1, "JUPROWA_PUSH_FIELDS nicht gefunden"
    block = index_html[i:i + 2000]
    assert "dauer" in block, (
        "dauer steht nicht mehr in JUPROWA_PUSH_FIELDS. Falls das Absicht ist: "
        "die Begruendung dieses Fixes (falscher Wert geht bis nach OFFA) gilt "
        "dann nur noch fuer die eigene Datenbank."
    )


def test_kein_einarmiger_aufruf_mehr(index_html):
    """Kein zweiter Rechenweg: es darf keinen Aufruf mehr geben, der die
    gelernten Mediane weglaesst.

    Erster Entwurf dieses Riegels ZAEHLTE die Vorkommen von '_dispoDauer(' und
    verlangte 4 - er zaehlte dabei die beiden Nennungen in meinen eigenen
    ERKLAERENDEN KOMMENTAREN mit und war prompt rot. Genau die Falle, die in
    diesem Repo heute schon dreimal zugeschnappt ist. Jetzt wird die FORM des
    Aufrufs geprueft, nicht seine Haeufigkeit - und Kommentare werden vorher
    entfernt.
    """
    ohne_komm = re.sub(r"/\*.*?\*/", "", index_html, flags=re.S)
    ohne_komm = "\n".join(l for l in ohne_komm.splitlines()
                          if not l.startswith("const APP_VERSION="))
    einarmig = re.findall(r"_dispoDauer\(\s*\w+\s*\)", ohne_komm)
    assert not einarmig, (
        "Es gibt wieder einen einarmigen _dispoDauer-Aufruf (%s). Der ueberspringt "
        "Klassen- und Typ-Median und erzeugt damit eine andere Dauer als der Plan - "
        "die via dauer/JUPROWA_PUSH_FIELDS bis nach OFFA geht." % einarmig
    )
    vierarmig = re.findall(r"_dispoDauer\([^)]*,[^)]*,[^)]*,", ohne_komm)
    assert len(vierarmig) >= 3, (
        "Erwartet mindestens 3 vollarmige Aufrufe (2 Plan + 1 Warteliste), "
        "gefunden %d." % len(vierarmig)
    )


def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    zurueck = index_html.replace(
        "_dispoDauer(s,null,(_built&&_built.gelernt)||null,(_built&&_built.typMed)||null)",
        "_dispoDauer(s)", 1)
    assert zurueck != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert "(_built&&_built.gelernt)" not in _wl_aufruf(zurueck), (
        "Umkehrprobe: der Wartelisten-Riegel wuerde nicht anschlagen"
    )

    zurueck2 = index_html.replace("gelernt:_gelernt, typMed:_typMed};", "};", 1)
    assert zurueck2 != index_html, "Rueckbau 2 griff nicht - Anker veraltet"
    assert "gelernt:_gelernt, typMed:_typMed};" not in zurueck2, (
        "Umkehrprobe: der Herausgabe-Riegel wuerde nicht anschlagen"
    )
