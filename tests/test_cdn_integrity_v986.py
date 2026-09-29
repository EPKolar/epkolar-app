# -*- coding: utf-8 -*-
"""Jede Datei von einem fremden Server wird gegen einen Abdruck geprueft.

WAS OHNE DAS PASSIERT. Die App laedt acht Dateien von `cdnjs.cloudflare.com`,
darunter `bcrypt.min.js` - die Bibliothek, die Kennwoerter verhasht. Wer
diese Auslieferung veraendert, bekommt jedes Kennwort im Klartext, und zwar
ohne einen einzigen Commit in diesem Repo. `crossorigin` stand schon an jedem
Tag; das ist die HAELFTE des Schutzes und ohne `integrity` wirkungslos - es
erlaubt die Pruefung, es fuehrt sie nicht durch.

🔴 UND WARUM DIESER RIEGEL SCHAERFER IST ALS "TRAEGT EIN INTEGRITY".
Ein FALSCHER Abdruck ist schlimmer als gar keiner: der Browser verweigert das
Skript, und die App ist vollstaendig tot - weiss, ohne Meldung. Die Form, in
der das passiert, ist nicht Boshaftigkeit, sondern Routine: jemand hebt
Leaflet von 1.9.4 auf 1.9.5 und laesst den Abdruck stehen.

Deshalb prueft dieser Riegel nicht die ANWESENHEIT des Attributs, sondern das
PAAR aus Adresse und Abdruck gegen eine hier festgeschriebene Tafel. Wer die
Version hebt, wird rot und muss den Abdruck mitheben. Genau das ist die
Wirkung, die der Riegel messen soll.

WOHER DIE ABDRUECKE STAMMEN UND WIE SIE GEPRUEFT WURDEN (29.09.):
zuerst von der cdnjs-API (`api.cdnjs.com/libraries/<lib>/<ver>?fields=sri`),
dann JEDER EINZELNE gegengerechnet, indem die Datei abgerufen und ihr
sha512 selbst gebildet wurde. Acht von acht stimmten ueberein. Die API ist
damit nicht geglaubt, sondern geprueft - sie ist selbst ein fremder Server.

WAS DIESER RIEGEL NICHT MISST: ob der Browser die Pruefung wirklich
durchfuehrt. Das haengt am Server (`Access-Control-Allow-Origin`) und wird
beim Laden der Seite im Pruefstand sichtbar, nicht im Quelltext.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

# Adresse -> Abdruck. Die Adresse ist der Teil hinter `/ajax/libs/`.
TAFEL = {
    "react/18.2.0/umd/react.production.min.js":
        "sha512-8Q6Y9XnTbOE+JNvjBQwJ2H8S+UV4uA6hiRykhdtIyDYZ2TprdNmWOUaKdGzOhy"
        "r4dCyk287OejbPvwl7lrfqrQ==",
    "react-dom/18.2.0/umd/react-dom.production.min.js":
        "sha512-MOCpqoRoisCTwJ8vQQiciZv0qcpROCidek3GTFS6KTk2+y7munJIlKCVkFCYY+p"
        "3ErYFXCjmFjnfTTRSC1OHWQ==",
    "bcryptjs/2.4.3/bcrypt.min.js":
        "sha512-DNI/FJdkfyeuPUal7lDkRVg0mFY2n4IZJJYqPbQWLL0COxLi6G6nmf5gr1vW1Bd"
        "4wYC09hOvZVsSclfXxUTU/w==",
    "pdf.js/3.11.174/pdf.min.js":
        "sha512-q+4liFwdPC/bNdhUpZx6aXDx/h77yEQtn4I1slHydcbZK34nLaR3cAeYSJshoxI"
        "Oq3mjEf7xJE8YWIUHMn+oCQ==",
    "qrcode-generator/1.4.4/qrcode.min.js":
        "sha512-ZDSPMa/JM1D+7kdg2x3BsruQ6T/JpJo3jWDWkCZsP+5yVyp1KfESqLI+7RqB5k2"
        "4F7p2cV7i2YHh/890y6P6Sw==",
    "jspdf/2.5.1/jspdf.umd.min.js":
        "sha512-qZvrmS2ekKPF2mSznTQsxqPgnpkI4DNTlrdUmTzrDgektczlKNRRhy5X5AAOnx5"
        "S09ydFYWWNSfcEqDTTHgtNA==",
    "leaflet/1.9.4/leaflet.min.js":
        "sha512-puJW3E/qXDqYp9IfhAI54BJEaWIfloJ7JWs7OeD5i6ruC9JZL1gERT1wjtwXFlh"
        "7CjE7ZJ+/vcRZRkIYIb6p4g==",
    "leaflet/1.9.4/leaflet.min.css":
        "sha512-h9FcoyWjHcOcmEVkxOfTLnmZFWIH0iZhZT1H2TbOq55xssQGEJHEaIm+PgoUaZb"
        "RvQTNTluNOEfb1ZRy6D3BOw==",
}

# Ein Tag mit `src=` oder `href=` auf einen fremden Server. Die Reihenfolge
# der Attribute ist NICHT festgelegt, deshalb wird der ganze Tag genommen und
# darin gesucht - ein Muster, das `integrity` unmittelbar hinter der Adresse
# erwartet, wuerde bei der ersten Umsortierung gruen bleiben und nichts mehr
# messen.
TAG = re.compile(r"<(script|link)\b[^>]*\bhttps://[^>]*>", re.I)
ADRESSE = re.compile(r"https://cdnjs\.cloudflare\.com/ajax/libs/([^\"'\s>]+)")
INTEGRITY = re.compile(r"""\bintegrity\s*=\s*["']([^"']+)["']""", re.I)
CROSSORIGIN = re.compile(r"\bcrossorigin\b", re.I)


def _kopf():
    """Nur der Dokumentkopf. Weiter unten steht JavaScript, das Adressen als
    Zeichenketten enthaelt - das sind keine geladenen Unterressourcen."""
    t = io.open(PFAD, encoding="utf-8", newline="").read()
    e = t.lower().find("</head>")
    assert e > 0, "Kein </head> gefunden - die Datei sieht nicht aus wie HTML."
    return t[:e]


def _tags(text):
    return [m.group(0) for m in TAG.finditer(text)]


def test_koeder_der_sucher_sieht_einen_tag_ohne_abdruck():
    """🔴 Ohne Selbstprobe waere jede Null hier wertlos.

    Drei Koeder, weil es drei verschiedene Arten gibt, durchzurutschen:
    gar kein `integrity`, ein `integrity` an anderer Stelle im Tag, und ein
    `link`, der kein `script` ist.
    """
    ohne = '<script crossorigin src="https://cdnjs.cloudflare.com/ajax/libs/x/1/x.js"></script>'
    hinten = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/x/1/x.js" '
              'crossorigin integrity="sha512-AAA=="></script>')
    stil = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/'
            'libs/y/1/y.css">')
    assert len(_tags(ohne + hinten + stil)) == 3, (
        "Der Sucher findet nicht alle drei Formen - dann sagt seine Null "
        "nichts.")
    assert not INTEGRITY.search(ohne), "Der Melder sieht einen Abdruck, der nicht da ist."
    assert INTEGRITY.search(hinten), (
        "Der Melder findet `integrity` nicht, wenn es HINTER `crossorigin` "
        "steht.\n  Dann wuerde eine blosse Umsortierung der Attribute den "
        "Riegel rot machen -\n  und eine andere Umsortierung ihn blind.")
    assert ADRESSE.search(stil), "Der Adressleser sieht ein <link> nicht an."


def test_die_grundgesamtheit_ist_nicht_leer():
    """🔴 Gegenprobe zur Null: gibt es die Tags ueberhaupt noch?"""
    tags = _tags(_kopf())
    assert len(tags) >= len(TAFEL), (
        "Nur %d fremde Unterressourcen im Kopf gefunden, die Tafel kennt %d.\n"
        "  Entweder wurden welche entfernt - dann gehoert die Tafel "
        "gekuerzt -,\n  oder der Sucher greift daneben und die andere "
        "Pruefung misst nichts."
        % (len(tags), len(TAFEL)))


def test_jede_fremde_datei_traegt_einen_abdruck():
    fehlt = []
    for tag in _tags(_kopf()):
        a = ADRESSE.search(tag)
        if not a:
            continue
        if not INTEGRITY.search(tag):
            fehlt.append(a.group(1))
    assert not fehlt, (
        "%d Dateien von cdnjs werden ohne Abdruck geladen:\n%s\n"
        "  Wer die Auslieferung dieser Dateien veraendert, laeuft im "
        "Browser jedes\n  Nutzers - `bcrypt.min.js` verhasht die Kennwoerter. "
        "`crossorigin` allein\n  erlaubt die Pruefung nur, es fuehrt sie "
        "nicht durch."
        % (len(fehlt), "\n".join("   " + f for f in fehlt)))


def test_jeder_abdruck_gehoert_zu_SEINER_adresse():
    """🔴 Der eigentliche Riegel. Ein Abdruck, der nicht zur Datei passt,
    macht die App VOLLSTAENDIG tot - der Browser verweigert das Skript."""
    schief, unbekannt = [], []
    for tag in _tags(_kopf()):
        a = ADRESSE.search(tag)
        if not a:
            continue
        pfad = a.group(1)
        i = INTEGRITY.search(tag)
        if not i:
            continue                     # die andere Pruefung meldet das
        if pfad not in TAFEL:
            unbekannt.append((pfad, i.group(1)))
        elif i.group(1).strip() != TAFEL[pfad]:
            schief.append((pfad, i.group(1), TAFEL[pfad]))
    assert not schief, (
        "%d Abdruecke passen nicht zu ihrer Adresse:\n%s\n"
        "  Ein falscher Abdruck ist schlimmer als keiner: der Browser laedt "
        "das Skript\n  dann gar nicht, und die App bleibt weiss - ohne "
        "Meldung."
        % (len(schief),
           "\n".join("   %s\n     steht : %s\n     erwartet: %s" % s
                     for s in schief)))
    assert not unbekannt, (
        "%d Adressen stehen nicht in der Tafel dieses Riegels:\n%s\n"
        "  Wer eine Bibliothek hebt oder aufnimmt, muss den Abdruck "
        "MITHEBEN. Hol ihn\n  dir nicht aus dem Kopf, sondern rechne ihn "
        "nach:\n"
        "    curl -s <adresse> | python -c \"import sys,hashlib,base64;"
        "print('sha512-'+base64.b64encode(hashlib.sha512("
        "sys.stdin.buffer.read()).digest()).decode())\""
        % (len(unbekannt), "\n".join("   %s" % u[0] for u in unbekannt)))


def test_jede_fremde_datei_traegt_auch_crossorigin():
    """Ohne `crossorigin` kann der Browser den Abdruck gar nicht pruefen -
    dann ist das Attribut Zierde."""
    fehlt = []
    for tag in _tags(_kopf()):
        a = ADRESSE.search(tag)
        if a and not CROSSORIGIN.search(tag):
            fehlt.append(a.group(1))
    assert not fehlt, (
        "%d Tags haben `integrity`, aber kein `crossorigin`:\n%s\n"
        "  Der Browser darf die Antwort dann nicht lesen und prueft den "
        "Abdruck nicht."
        % (len(fehlt), "\n".join("   " + f for f in fehlt)))


# ── Die EINE Stelle, die kein Abdruck erreichen kann ──────────────────────
# `pdf.worker.min.js` wird nicht von einem Tag geladen, sondern zur Laufzeit
# als Adresse zugewiesen (index.html:4304):
#
#     window.pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs..."
#
# Dort gibt es kein `integrity`-Attribut - die Norm kennt SRI nur fuer Tags.
# Absicherbar waere das nur, indem die Datei geholt, selbst gehasht und als
# Blob-Adresse weitergegeben wird; das ist eine Verhaltensaenderung am
# PDF-Laden und braucht eine eigene Messung. Die CSP erlaubt `worker-src
# 'self' blob:`, der Weg ist also offen - aber nicht gemessen.
#
# 🔴 Das steht hier, statt ausgelassen zu werden. Eine Ausnahme, die man
#    nicht benennt, ist eine Luecke. Zwei Dinge werden trotzdem gemessen.
ARBEITER = re.compile(
    r"""workerSrc\s*=\s*["']https://cdnjs\.cloudflare\.com/ajax/libs/"""
    r"""([^"']+)["']""")
PDFJS_IM_KOPF = re.compile(
    r"https://cdnjs\.cloudflare\.com/ajax/libs/pdf\.js/([0-9.]+)/pdf\.min\.js")


def _ganz():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def test_koeder_der_arbeiter_sucher_findet_die_zuweisung():
    """🔴 Selbstprobe: ohne sie waere die Null der naechsten Pruefung leer."""
    echt = ('window.pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdnjs.'
            'cloudflare.com/ajax/libs/pdf.js/9.9.9/pdf.worker.min.js";')
    m = ARBEITER.search(echt)
    assert m and m.group(1) == "pdf.js/9.9.9/pdf.worker.min.js", (
        "Der Sucher findet die Zuweisung nicht einmal in einem Text, der nur "
        "daraus besteht.")
    assert not ARBEITER.search('workerSrc="/lokal/pdf.worker.js"'), (
        "Eine OERTLICHE Adresse wird als fremde gezaehlt - dann wuerde der "
        "Riegel rot,\n  sobald jemand die Datei ins Repo holt, also genau "
        "beim RICHTIGEN Schritt.")


def test_der_arbeiter_hat_die_gleiche_fassung_wie_pdfjs_selbst():
    """Laeuft die Fassung auseinander, bricht das PDF-Lesen - und zwar erst
    beim Nutzer, nicht im Bau."""
    t = _ganz()
    kopf = PDFJS_IM_KOPF.search(t)
    arbeiter = ARBEITER.search(t)
    if not arbeiter:
        return                       # keine fremde Arbeiterdatei mehr: gut
    assert kopf, (
        "Ein fremder pdf.js-Arbeiter wird geladen, aber pdf.js selbst steht "
        "nicht mehr\n  als cdnjs-Skript im Kopf. Dann passt hier etwas nicht "
        "zusammen.")
    fassung = arbeiter.group(1).split("/")[1]
    assert fassung == kopf.group(1), (
        "pdf.js steht im Kopf als %s, der Arbeiter aber als %s.\n"
        "  Zwei Fassungen von pdf.js reden nicht miteinander - das PDF bleibt "
        "leer,\n  und zwar erst beim Nutzer." % (kopf.group(1), fassung))


def test_es_gibt_genau_EINE_solche_ausnahme():
    """🔴 Eine benannte Ausnahme darf sich nicht unbemerkt vermehren."""
    treffer = ARBEITER.findall(_ganz())
    assert len(treffer) <= 1, (
        "%d Dateien werden zur Laufzeit von cdnjs nachgeladen, nicht nur die "
        "eine\n  bekannte:\n%s\n"
        "  Fuer keine davon kann ein Abdruck greifen. Jede neue gehoert "
        "entweder ins\n  Repo oder ausdruecklich hierher."
        % (len(treffer), "\n".join("   " + x for x in treffer)))
