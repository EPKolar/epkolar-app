# -*- coding: utf-8 -*-
"""
v3.9.883 PERFORMANCE + SPEICHER - gemessen, nicht vermutet.

AUFTRAG (Sebastian): "mach die app schneller und weniger ram".
Zielgeraet: aelteres Android-Baustellenhandy, Mobilfunk-Funkloch, als PWA.

MESSAUFBAU
----------
Playwright/Chromium, Viewport 390x844, has_touch. Test-Sitzung wie
scripts/tab_sweep.py (INIT). Supabase per Route-Stub beantwortet - erst mit
200/leer, dann mit synthetischen Zeilen in realistischer Menge (5000
time_entries, 3000 bautagebuch, 2000 tickets, 1500 arbeitsscheine, 1500
absences, 1000 defects, 300 projects, 60 workers ...). CPU-Drosselung ueber
CDP Emulation.setCPUThrottlingRate. Heap ueber performance.memory NACH
3x HeapProfiler.collectGarbage. Der jeweils erste Lauf ist verworfen.

DIE ZAHLEN (v3.9.878 .. v3.9.882, die Datei wurde waehrend der Messung von
anderen Agenten weitergeschrieben - die Groessen unten sind v3.9.882)
------------------------------------------------------------------------
index.html            3.428.821 Bytes roh, 1.001.166 Bytes gzip
  davon Zeile 2888    181.820 Bytes  (APP_VERSION + Changelog-Kommentar)
  davon Zeile 2889     89.856 Bytes  (zweiter Changelog-Block)
  Blockkommentare      770.959 Zeichen = 22,7 % der Datei
  Auslieferung         GitHub Pages sendet Content-Encoding: gzip (geprueft
                       per curl gegen die Live-URL) - 998.609 Bytes ueber die Leitung

Start (navigationStart -> React hat #root gefuellt), Median aus 5 Laeufen je Stufe:
  CPU x1  (Entwicklerrechner)      253 ms
  CPU x4  (Mittelklasse-Handy)   1.339 ms
  CPU x10 (schwaches Handy)      5.588 ms
  CPU x20                       28.965 ms

Heap (usedJSHeapSize, nach erzwungener GC):
  leere Daten:   nach Start 10,82 MB | nach 18 Tabs 12,64 MB | nach 36 Tabs 13,21 MB
  volle Daten:   nach Start 25,40 MB | nach 18 Tabs 23,59 MB | nach 36 Tabs 24,31 MB
  -> KEIN Leck beim Tabwechsel. Der zweite Durchlauf kostet weniger als der
     erste, mit vollen Daten sinkt der Heap sogar. Das ist ein WIDERLEGTER
     Befund und steht hier als Messung, nicht als Fund.

Tabwechsel mit vollen Daten, DOM-Knoten im Inhaltsbereich:
  Arbeitsscheine  18.190 Knoten, 248.787 px Scrollhoehe   x1: 711-993 ms
  Buero-Portal     3.336 Knoten,  53.748 px               x1: 130-162 ms
  Werkzeuge        3.378 Knoten,  28.116 px               x1:  92-110 ms
  alle uebrigen  < 850 Knoten                             x1:  <  60 ms
  Bei CPU x6 (3 Laeufe je Tab):
  Arbeitsscheine  10.269 / 11.046 / 12.570 ms   <- Median 11,0 SEKUNDEN
  Buero-Portal     1.309 / 1.593 / 1.722 ms
  Werkzeuge        1.059 / 1.150 / 1.252 ms
  Zeiterfassung       69 /   164 /   238 ms

Gegenprobe zum Vorschlag (content-visibility auf die Kartenliste), CPU x6,
4 Wechsel je Variante, im selben Lauf abwechselnd ein-/ausgeschaltet:
  ohne:  9.047 / 11.287 / 13.128 / 16.232 ms  -> Median 12.208 ms
  mit:   3.872 /  4.432 /  5.338 /  6.301 ms  -> Median  4.885 ms
  Funktionsprobe: bis ans Ende gescrollt, die letzte Karte ist da (143 px hoch,
  Text vorhanden) - es geht kein Datensatz verloren.
  Trefferzahl des Selektors je Ansicht: Arbeitsscheine 1511, Home 8, Chef 5,
  alle 11 anderen 0. Die anderen Ansichten messen unveraendert.

Foto-Groessen (kuenstliches 12-MP-Rauschbild, ungueenstigster Fall fuer JPEG -
die VERHAELTNISSE sind die Aussage, nicht die Absolutwerte):
  compressPhoto(...,2400,0.88) -> data-URL 1.776 KB
  compressPhoto(...,2000,0.85) -> data-URL   911 KB
  compressPhoto(...,1600,0.72) -> data-URL   303 KB
  compressPhoto(...,1280,0.70) -> data-URL   174 KB

Service Worker ueber eine gedrosselte Leitung (eigener Testserver, 100 KB/s +
300 ms Latenz - CDP-Netzdrosselung greift NICHT auf Service-Worker-Fetches,
die erste Messung war deshalb ungueltig und ist verworfen):
  1. Besuch, kein SW                     10.944 ms
  SW controlling, dieselbe Leitung       11.071 / 10.933 / 11.192 ms
  -> Der Service Worker verkuerzt den Start um NICHTS. Die Navigation laeuft
     network-first mit cache:'no-store'; der Cache ist reiner Offline-Notnagel.

Timer: 12 gleichzeitige Intervalle nach dem Start, nach 36 Tabwechseln 10.
Kein Intervall-Leck.

ROTE TESTS SIND HIER ERWARTET.
Alle Riegel unter "OFFEN" schlagen an, solange der jeweilige Patch fehlt.
Sie werden gruen, sobald der zugehoerige Anker-Ersatz gesetzt ist.
Die Riegel unter "BELEGT GRUEN" halten fest, was bereits stimmt, damit es
nicht unbemerkt kaputtgeht.
"""
import re

import pytest


# ═══════════════════════════════════════════════════════════════════════════
#  Hilfen
# ═══════════════════════════════════════════════════════════════════════════

CV_REGEL = '.main-pad div[role="button"][aria-label]{content-visibility:auto'


def _ohne_changelog(index_html):
    """Zeile 2888/2889 sind zusammen 271 KB reiner Changelog-Kommentar. Wer
    darin nach Code sucht, findet jeden Wortlaut, der je in der App stand -
    auch den, der laengst entfernt wurde. Genau daran ist am 25.08. ein Test
    gruen geblieben, der einen Absturz festgeschrieben hatte.

    Bewusst NICHT nach Zeilennummer gefiltert: die verschiebt sich mit jedem
    Commit. Gefiltert wird nach Groesse - eine Codezeile dieser Datei ist
    hoechstens rund 18 KB lang (Zeile 4113), die Changelog-Zeilen sind 90 KB
    und 182 KB. Die Schwelle 40 KB liegt sauber dazwischen."""
    return "\n".join(z for z in index_html.split("\n")
                     if not (len(z) > 40000 and "/*" in z))


# ═══════════════════════════════════════════════════════════════════════════
#  OFFEN - diese Riegel sind rot, bis der Patch da ist
# ═══════════════════════════════════════════════════════════════════════════

def test_lange_kartenliste_zeichnet_nur_das_sichtbare(index_html):
    """BEFUND 1 (groesster gemessener Gewinn).

    Die Arbeitsschein-Kartenliste am Handy (Zeile ~10870:
    `isMob&&React.createElement('div',...` gefolgt von `sorted.map(a=>{...`)
    rendert JEDEN gefilterten Schein. Gemessen bei 1500 Scheinen: 18.190
    DOM-Knoten, 248.787 px Scrollhoehe, Tabwechsel bei CPU x6 im Median
    11,0 s. Der Monteur sieht davon 6 Karten.

    Der Patch ist eine CSS-Regel, kein Umbau: content-visibility:auto laesst
    Chrome Layout und Zeichnen fuer alles ausserhalb des Bildschirms
    ueberspringen. Gemessen 12,2 s -> 4,9 s (Median aus je 4 Wechseln).
    contain-intrinsic-size:auto 148px ist nur der Startwert; das `auto`
    sorgt dafuer, dass Chrome sich die echte Hoehe nach dem ersten Zeichnen
    merkt, die Bildlaufleiste also nicht springt.
    """
    assert CV_REGEL in index_html, (
        "Die content-visibility-Regel fuer lange Kartenlisten fehlt. Ohne sie "
        "zeichnet das Handy alle 18.190 Knoten der Arbeitsschein-Liste, auch "
        "die 1494 Karten, die niemand sieht (gemessen: 11,0 s statt 4,9 s bei "
        "CPU x6)."
    )


def test_kartenliste_bleibt_im_druck_vollstaendig(index_html):
    """content-visibility:auto darf den Druck/PDF-Weg nicht beschneiden -
    sonst fehlen im Ausdruck genau die Karten, die nie sichtbar waren."""
    if CV_REGEL not in index_html:
        pytest.skip("Patch aus test_lange_kartenliste_zeichnet_nur_das_sichtbare fehlt noch")
    assert re.search(
        r'@media print\{\s*\.main-pad div\[role="button"\]\[aria-label\]\{content-visibility:visible\}',
        index_html), (
        "Die Druck-Ausnahme fehlt. Ohne sie kann der Ausdruck die "
        "ausgelassenen Karten verlieren."
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN - der Befund steht, der Fix ist eine Entscheidung. "
    "Jedes Mangel-Foto wird ZWEIMAL komprimiert - captureAndQueue beginnt selbst wieder mit compressPhoto. Auf einem Baustellenhandy die teuerste Nutzeraktion der App. Der Fix ist ein kleiner Umbau (das schon komprimierte ph statt file weiterreichen), keine Textersetzung - die drei Stellen haengen zusammen. Handoff 28.08."))
def test_mangelfoto_wird_nicht_zweimal_komprimiert(index_html):
    """BEFUND 2 (Speicher + CPU, beides auf dem Handy).

    uploadDefectPhoto (Zeile ~16221) macht mit EINER Datei zwei volle
    Komprimierlaeufe:

        const ph=await compressPhoto(file,2400,0.88);      <- Lauf 1
        ...
        await captureAndQueue(file,"defect",...);          <- Lauf 2,
            denn captureAndQueue (Zeile ~3267) beginnt mit
            compressPhoto(file,2400,0.88)

    Ein 12-MP-Foto wird also zweimal dekodiert, zweimal auf 2400 px skaliert
    und zweimal als JPEG kodiert. Auf einem schwachen Android ist das die
    teuerste einzelne Nutzeraktion der ganzen App.
    """
    quelle = _ohne_changelog(index_html)
    m = re.search(r"const uploadDefectPhoto=async\(defectId,file\)=>\{(.{0,900}?)\};",
                  quelle, re.S)
    assert m, "uploadDefectPhoto nicht gefunden - Anker veraltet, Test pruefen"
    koerper = m.group(1)
    hat_compress = "compressPhoto(" in koerper
    hat_capture = re.search(r"captureAndQueue\(\s*file\b", koerper) is not None
    assert not (hat_compress and hat_capture), (
        "uploadDefectPhoto komprimiert das Foto selbst UND reicht die "
        "Rohdatei an captureAndQueue weiter, das erneut komprimiert. "
        "Zweimal dekodieren + skalieren + JPEG-kodieren fuer ein Bild:\n"
        + koerper[:400]
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN - der Befund steht, der Fix ist eine Entscheidung. "
    "Die volle Foto-data-URL bleibt dauerhaft im State - gemessen 1,78 MB je Foto auf 25,4 MB Grundlast; fuenf Fotos sind +8,7 MB, genau die Groessenordnung, bei der Android den Tab verwirft. Das Vorbild steht in derselben Datei (der AS-Fotoweg legt nur die URL ab). Gehoert mit der Doppelkomprimierung zusammen umgebaut. Handoff 28.08."))
def test_mangelfoto_bleibt_nicht_in_voller_groesse_im_state(index_html):
    """BEFUND 3 (der eigentliche RAM-Fresser).

    Zeile ~16226 legt die VOLLE data-URL dauerhaft in den React-State:

        setForms(f=>({...f,maengel:(...).map(m=>...{...m,photos:[...,{thumb,full:ph.dataUrl}]}...)}))

    Gemessen kostet eine data-URL aus compressPhoto(...,2400,0.88) 1.776 KB
    als JS-Zeichenkette. Fuenf Mangel-Fotos = 8,7 MB Heap zusaetzlich zu den
    gemessenen 25,4 MB Grundlast. `forms` steht ausserdem in der Liste der
    IndexedDB-Stores - die Zeichenkette wird also auch noch auf die Platte
    geschrieben.

    Der Arbeitsschein-Fotoweg (Zeile ~10373) macht es bereits richtig: laedt
    hoch und legt nur die URL in den State. Dasselbe Muster, dieselbe Datei.
    """
    quelle = _ohne_changelog(index_html)
    assert "full:ph.dataUrl" not in quelle, (
        "Die volle Foto-data-URL (gemessen 1.776 KB je Bild) wird in den "
        "React-State geschrieben und dort gehalten. Vorbild fuer den Umbau: "
        "der AS-Fotoweg legt nur die hochgeladene URL ab."
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN - der Befund steht, der Fix ist eine Entscheidung. "
    "FACHLICHE Entscheidung, kein Technikfix: 2400/0,88 ergibt 1,78 MB, 1600/0,72 nur 303 KB. Wenn Mangel-Fotos gegenueber Baumeister oder Gericht Beweiskraft haben muessen, ist 2400/0,88 RICHTIG und dieser Riegel gehoert geloescht statt der Wert gesenkt. Entscheidung Sebastian. Handoff 28.08."))
def test_fotos_werden_handytauglich_verkleinert(index_html):
    """BEFUND 4 (Speicher + Funkloch-Upload).

    2400 px bei Qualitaet 0,88 ist Druckqualitaet. Gemessen an einem
    12-MP-Rauschbild:

        2400 / 0,88  ->  1.776 KB
        1600 / 0,72  ->    303 KB     (Faktor 5,9)

    Fuer einen Mangel-Beleg auf einer Baustelle reichen 1600 px. Der Gewinn
    ist doppelt: weniger Heap auf dem Handy UND weniger Bytes durch eine
    Leitung, die im Funkloch ohnehin nicht traegt.

    ACHTUNG - das ist eine FACHLICHE Entscheidung, keine technische.
    Wenn Mangel-Fotos vor Gericht oder gegenueber dem Baumeister Beweiskraft
    haben muessen, ist 2400/0,88 richtig und dieser Test gehoert geloescht,
    nicht der Wert gesenkt.
    """
    quelle = _ohne_changelog(index_html)
    treffer = re.findall(r"compressPhoto\([^)]*?,\s*2400\s*,\s*0\.88\s*\)", quelle)
    assert not treffer, (
        "Fotos werden weiter mit 2400 px / q0,88 gespeichert (%d Aufrufe). "
        "Gemessen 1.776 KB je Bild als data-URL gegenueber 303 KB bei "
        "1600 px / q0,72." % len(treffer)
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN - der Befund steht, der Fix ist eine Entscheidung. "
    "Der Service Worker spart beim Start nichts (mit drosselndem Testserver gemessen: 10,9s ohne SW, 11,0s mit). ABER v3.9.358 hat network-first ABSICHTLICH eingefuehrt, weil Nutzer nach Deploys auf der Vorversion haengenblieben. Ein naives cache-first bringt genau diesen Fehler zurueck - der Umbau muss stale-while-revalidate sein und den vorhandenen Update-Banner nutzen. Entscheidung Sebastian. Handoff 28.08."))
def test_service_worker_liefert_die_seite_zuerst_aus_dem_cache(sw_js):
    """BEFUND 5 (der Funkloch-Befund).

    sw.js beantwortet Navigationen network-first und ausdruecklich mit
    cache:'no-store'. Der Cache ist damit nur Notnagel fuer "gar kein Netz".
    Ein Baustellenhandy hat aber meistens nicht KEIN Netz, sondern
    SCHLECHTES - und da nuetzt der Notnagel nichts.

    Gemessen (eigener Testserver, 100 KB/s + 300 ms Latenz, damit die
    Drosselung auch fuer den Service Worker gilt):

        1. Besuch ohne SW                10.944 ms
        SW controlling, gleiche Leitung  11.071 / 10.933 / 11.192 ms

    Der Service Worker spart NULL. Erwartet waere: sofort aus dem Cache
    anzeigen, im Hintergrund nachladen, und den vorhandenen Update-Banner
    (setSwUpdate, plus reg.update() im 60-s-Takt) die neue Fassung anbieten
    lassen - die Mechanik dafuer ist bereits gebaut.
    """
    m = re.search(r"if \(event\.request\.mode === 'navigate'.{0,600}?\n  \}",
                  sw_js, re.S)
    assert m, "Navigations-Zweig in sw.js nicht gefunden - Anker veraltet"
    zweig = m.group(0)
    assert "cache: 'no-store'" not in zweig, (
        "Der Navigations-Zweig laedt die Seite bei JEDEM Start frisch aus dem "
        "Netz (cache:'no-store') und faellt nur bei einem harten Fehler auf "
        "den Cache zurueck. Gemessen: 11,0 s Start ueber 100 KB/s, mit und "
        "ohne Service Worker identisch.\n" + zweig[:300]
    )


# ═══════════════════════════════════════════════════════════════════════════
#  BELEGT GRUEN - gemessen in Ordnung, hier festgenagelt
# ═══════════════════════════════════════════════════════════════════════════

def test_service_worker_raeumt_alte_caches_ab(sw_js):
    """Gemessen: nach einem vollen Durchlauf inkl. Flotte-Karte existiert
    genau EIN Cache (4.437.233 Bytes, 10 Eintraege: 8x cdnjs, 1x index.html,
    1x open-meteo). Kartenkacheln landen NICHT im Cache - sie kommen als
    opaque Response, und die response.ok-Pruefung in sw.js sortiert die aus.
    Kein unbegrenztes Wachstum. Dieser Riegel haelt das fest."""
    assert re.search(r"keys\.filter\(k => k !== CACHE_NAME\)\.map\(k => caches\.delete\(k\)\)", sw_js), (
        "Der activate-Handler loescht alte Caches nicht mehr. Dann sammelt "
        "sich pro Version eine weitere Vollkopie der index.html (rund 1 MB) "
        "auf dem Handy an."
    )
    assert "response && response.ok" in sw_js, (
        "Die response.ok-Pruefung ist weg. Sie ist es, die verhindert, dass "
        "OSM-/ArcGIS-Kartenkacheln unbegrenzt in den Cache laufen."
    )


def test_kein_intervall_leck(index_html):
    """Gemessen: 12 gleichzeitige Intervalle nach dem Start, 10 nach 36
    Tabwechseln - die Zahl steigt nicht. Statisch abgesichert: es gibt
    mindestens so viele clearInterval- wie setInterval-Stellen."""
    quelle = _ohne_changelog(index_html)
    setzt = len(re.findall(r"\bsetInterval\(", quelle))
    raeumt = len(re.findall(r"\bclearInterval\(", quelle))
    assert raeumt >= setzt, (
        "Es gibt %d setInterval, aber nur %d clearInterval. Ein nicht "
        "abgeraeumter Takt kostet auf einem Handy dauerhaft Strom und "
        "haelt seinen ganzen Closure im Speicher." % (setzt, raeumt)
    )


def test_die_beiden_pollintervalle_bleiben_gross(index_html):
    """Zwei Takte laufen dauerhaft gegen das Netz: pollForChanges (60 s) und
    der Weekplan-Abgleich (30 s). Das ist die Grenze dessen, was auf einem
    Baustellenhandy vertretbar ist - gemessen kamen bei 200er-Antworten in
    60 s Leerlauf nur 6 Requests dazu. Wer die Zahlen senkt, macht die App
    im Funkloch messbar schlechter."""
    quelle = _ohne_changelog(index_html)
    assert "const POLL_INTERVAL=60000;" in quelle, (
        "POLL_INTERVAL ist nicht mehr 60 s."
    )
    assert re.search(r"_loadWeekplansFromRows\(true\);\s*\n?\s*\},30000\)", quelle), (
        "Der Weekplan-Takt ist nicht mehr 30 s."
    )


def test_arbeitsscheinliste_hat_stabile_keys(index_html):
    """Gegenprobe zur Ursachensuche bei Befund 1: die 11 s liegen NICHT an
    fehlenden React-Keys. Beide Listen (Handy-Karten und Desktop-Tabelle)
    haben `key: a.id`. Das ist hier festgehalten, damit niemand die Zeit
    dort sucht - und damit es so bleibt."""
    quelle = _ohne_changelog(index_html)
    treffer = re.findall(r"sorted\.map\(a=>\{", quelle)
    assert len(treffer) >= 2, (
        "Die beiden sorted.map-Listen der Arbeitsschein-Ansicht sind nicht "
        "mehr da - der Befund muss neu gemessen werden."
    )
    assert quelle.count("React.createElement('div', { key: a.id, onTouchStart: e=>_swipeStart(a,e)") == 1, (
        "Die Handy-Kartenliste vergibt key: a.id nicht mehr."
    )


def test_changelog_kommentar_ist_kein_startzeit_problem(index_html):
    """WIDERLEGTER BEFUND - bewusst als gruener Riegel dokumentiert.

    Zeile 2888 und 2889 sind zusammen 271.676 Bytes Changelog-Kommentar,
    22,7 % der ganzen Datei sind Blockkommentare. Das SIEHT nach dem grossen
    Hebel aus. Ist es nicht:

      - GitHub Pages liefert gzip (per curl gegen die Live-URL geprueft),
        deutscher Fliesstext komprimiert exzellent;
      - V8 ueberspringt Kommentare beim Lexen, sie werden nie kompiliert;
      - der gemessene Startanteil liegt in Parsen+Ausfuehren des ECHTEN
        Codes und im ersten React-Mount, nicht im Lexen.

    Die Kommentare sind ausserdem die einzige Fehlerhistorie dieses Projekts.
    Sie zu loeschen waere ein messbar winziger Gewinn gegen einen echten
    Verlust. Dieser Riegel haelt fest, dass sie bleiben duerfen.
    """
    zeilen = index_html.split("\n")
    assert len(zeilen) > 2889, "Datei kuerzer als erwartet"
    assert len(zeilen[2887]) > 50000, (
        "Der APP_VERSION-Changelog ist verschwunden. Falls er aus "
        "Performance-Gruenden entfernt wurde: der Gewinn ist nach dieser "
        "Messung nicht nachweisbar, der Verlust an Historie schon."
    )


# ═══════════════════════════════════════════════════════════════════════════
#  UMKEHRPROBE
#  Ein Riegel, der nach dem Patch nicht gruen wird, misst nichts. Ein Riegel,
#  der ohne den Patch gruen bleibt, misst auch nichts. Beides wird hier
#  gegen den echten Dateiinhalt gefahren.
# ═══════════════════════════════════════════════════════════════════════════

def test_umkehrprobe_cv_riegel_schlaegt_in_beide_richtungen_an(index_html):
    anker = ".main-pad{padding:20px;touch-action:pan-y}"
    assert index_html.count(anker) == 1, (
        "Der Anker fuer die CSS-Regel kommt nicht genau einmal vor "
        "(%d Treffer) - der Vorschlag im Bericht ist veraltet."
        % index_html.count(anker)
    )
    gepatcht = index_html.replace(
        anker,
        anker + "\r\n"
        + '.main-pad div[role="button"][aria-label]'
          "{content-visibility:auto;contain-intrinsic-size:auto 148px}\r\n"
        + '@media print{.main-pad div[role="button"][aria-label]'
          "{content-visibility:visible}}",
        1)
    assert CV_REGEL in gepatcht, "Positivkontrolle: der Riegel wird nach dem Patch nicht gruen"
    assert CV_REGEL not in index_html.replace(CV_REGEL, ""), \
        "Negativkontrolle: der Riegel schlaegt beim Rueckbau nicht an"


def test_umkehrprobe_fotoriegel_schlaegt_in_beide_richtungen_an(index_html):
    quelle = _ohne_changelog(index_html)
    muster = re.compile(r"compressPhoto\([^)]*?,\s*2400\s*,\s*0\.88\s*\)")
    assert muster.search(quelle), (
        "Negativkontrolle: der 2400/0.88-Riegel findet nichts mehr. Entweder "
        "ist der Patch schon da (dann ist das gut) oder das Muster ist "
        "veraltet (dann misst der Riegel nichts)."
    )
    gepatcht = muster.sub("compressPhoto(file,1600,0.72)", quelle)
    assert not muster.search(gepatcht), \
        "Positivkontrolle: der Riegel bleibt nach dem Patch rot"


def test_umkehrprobe_changelog_wird_ueberall_ausgeblendet(index_html):
    """Der Filter _ohne_changelog ist die Voraussetzung fast aller Riegel
    hier. Wenn er nicht greift, findet jede Suche den Wortlaut alter,
    laengst geloeschter Fassungen im Changelog wieder - und der Test ist
    gruen, ohne etwas zu messen. Genau diese Falle hat am 25.08. einen
    Absturz monatelang festgeschrieben."""
    voll = index_html
    gefiltert = _ohne_changelog(voll)
    assert len(voll) - len(gefiltert) > 200000, (
        "Der Changelog-Filter schneidet weniger als 200 KB weg (%d Bytes). "
        "Die Zeilennummern 2888/2889 stimmen nicht mehr - jeder Riegel in "
        "dieser Datei misst dann potenziell nur noch Kommentartext."
        % (len(voll) - len(gefiltert))
    )
    # Positivkontrolle: genau die grossen Kommentarzeilen sind weg, und zwar
    # als GANZE Zeilen - nicht bloss zufaellig ein paar Bytes.
    gross = [z for z in voll.split("\n") if len(z) > 40000 and "/*" in z]
    assert len(gross) >= 2, (
        "Es gibt keine zwei grossen Changelog-Zeilen mehr (%d gefunden). "
        "Entweder wurde der Changelog umgebaut - dann ist der Filter "
        "anzupassen - oder er ist geloescht." % len(gross)
    )
    for z in gross:
        assert z not in gefiltert, "Eine Changelog-Zeile ueberlebt den Filter"
    # Negativkontrolle: der Filter darf keine ECHTE Codezeile wegwerfen. Die
    # laengste Codezeile der Datei liegt bei rund 18 KB, also weit unter der
    # Schwelle - hier hart nachgemessen.
    rest = [len(z) for z in gefiltert.split("\n")]
    assert max(rest) < 40000, (
        "Nach dem Filtern gibt es immer noch eine Zeile ueber 40 KB (%d) - "
        "die Schwelle trennt Code und Changelog nicht mehr sauber." % max(rest)
    )
