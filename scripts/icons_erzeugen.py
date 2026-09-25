# -*- coding: utf-8 -*-
"""Erzeugt die PWA-Icons als ECHTE Dateien im Repo-Root.

WARUM ES DAS GIBT (v3.9.931)
────────────────────────────
Die Icons wurden bisher zur LAUFZEIT in index.html per Canvas gezeichnet
(`_epIcon(sz)` -> `canvas.toDataURL("image/png")`) und als data:-URL in ein
Manifest geschrieben, das ebenfalls erst zur Laufzeit als Blob-URL entstand.
Das hat drei Folgen, die alle erst beim Installieren sichtbar werden:

  * Ein Blob-Manifest hat KEINEN eigenen Ursprung - `start_url`/`scope` sind
    damit nicht verifizierbar, und mancher Browser lehnt die Installation ab.
  * Der Service Worker kann nichts vorhalten, was es als Datei nicht gibt.
  * `purpose:"maskable"` war auf DIESELBE Bilddatei gesetzt wie `purpose:"any"`.
    Das ist eine falsche Zusage: Android beschneidet maskable-Icons auf einen
    Kreis von ca. 80 % Kantenlaenge - das randlose Motiv verliert dabei die
    Ecken des gruenen Schildes und schneidet in die Buchstaben.

Dieses Skript erzeugt die vier Dateien reproduzierbar aus EINER Geometrie.
Motiv und Farben sind aus dem Canvas-Zeichner in index.html uebernommen und
NICHT neu erfunden: gruenes Schild mit abgerundeten Ecken (Radius 15,6 % der
Kantenlaenge, #009640) und weisses, fettes "EP" darauf.

Der Unterschied zum Canvas-Original: die Buchstaben werden hier GEOMETRISCH
gesetzt (Balken und Bogen), nicht ueber eine Systemschrift. Eine Systemschrift
waere geraeteabhaengig - "system-ui" ist auf Windows Segoe UI, auf Android
Roboto, auf macOS SF Pro. Dieselbe Datei zweimal erzeugt saehe dann anders aus,
und genau das soll ein reproduzierbares Skript nicht.

ERZEUGTE DATEIEN
────────────────
  icon-192.png            192x192  randlos  purpose "any"
  icon-512.png            512x512  randlos  purpose "any"
  icon-192-maskable.png   192x192  Motiv auf 78 %  purpose "maskable"
  icon-512-maskable.png   512x512  Motiv auf 78 %  purpose "maskable"

Die maskable-Fassungen sind EIGENE Dateien. "any" und "maskable" duerfen nicht
auf dieselbe Bilddatei zeigen, weil sie sich widersprechende Zusagen machen:
"any" verspricht randlose Ausnutzung, "maskable" verspricht >=10 % Sicherheits-
rand. Um die Flaeche ausserhalb des Motivs zu fuellen, wird dort die
Hintergrundfarbe des Manifests (#0f1117) deckend gelegt - maskable-Icons
duerfen nicht durchsichtig sein, sonst setzt die Startleiste Schwarz darunter.

AUFRUF
──────
    python scripts/icons_erzeugen.py            # schreibt ins Repo-Root
    python scripts/icons_erzeugen.py --pruefen  # schreibt nichts, meldet nur,
                                                # ob die Dateien aktuell sind

ABHAENGIGKEIT
─────────────
Pillow (PIL). Am 25.09.2026 im Arbeitsbaum als 12.1.1 vorgefunden; es wird
NICHTS nachinstalliert. Fehlt Pillow, bricht das Skript mit einer Meldung ab,
die das sagt - es erzeugt keine halbfertigen Dateien.
"""
import io
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - haengt an der Umgebung, nicht am Code
    sys.stderr.write(
        "Pillow (PIL) fehlt. Dieses Skript installiert NICHTS nach.\n"
        "Entweder Pillow bereitstellen oder die Icons unveraendert lassen.\n"
    )
    raise SystemExit(2)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ── Farben, woertlich aus index.html ──────────────────────────────────────
GRUEN = (0, 150, 64, 255)        # #009640  - theme_color und Schildfarbe
WEISS = (255, 255, 255, 255)     # Schrift
HINTERGRUND = (15, 17, 23, 255)  # #0f1117  - background_color des Manifests

# ── Geometrie, relativ zur Kantenlaenge des SCHILDES (nicht des Bildes) ──
# Der Eckradius ist woertlich aus dem Canvas-Zeichner: `var r=sz*0.156`.
ECKRADIUS = 0.156

# Das Canvas-Original setzt "EP" mit `font = bold 0.44*sz px` auf der Grundlinie
# `textBaseline:"middle"` bei y = 0.52*sz. Eine fette Groteske hat bei 0.44 em
# rund 0.32 em Versalhoehe - das ist der Wert, der hier nachgebaut wird.
VERSALHOEHE = 0.32
MITTE_Y = 0.52
BUCHSTABENBREITE = 0.215
BUCHSTABENLUECKE = 0.030

# Senkrechte und waagrechte Striche sind NICHT gleich stark. Werden sie gleich
# gesetzt, faellt der Innenraum des P in sich zusammen: bei Schale 0.58 und
# Strich 0.085 blieben rechnerisch 0.0156 Kantenlaengen Innenraum uebrig - auf
# dem 192er Icon drei Bildpunkte, die wie ein Kratzer aussehen, nicht wie ein
# Buchstabe. Eine fette Groteske fuehrt die Waagrechten rund 14 % duenner.
STAMMBREITE = 0.072     # Senkrechte ("bold": rund 22 % der Versalhoehe)
BALKENSTAERKE = 0.062   # Waagrechte
BOGENHOEHE = 0.62       # Anteil der Versalhoehe, den die Schale des P einnimmt
MITTELBALKEN = 0.86     # der Mittelbalken des E ist kuerzer als der obere

# ── maskable ──────────────────────────────────────────────────────────────
# Die Zusage lautet: das Motiv nimmt hoechstens 80 % der Kantenlaenge ein.
# 78 % laesst bewusst Luft, damit die weiche Kante der Verkleinerung nicht in
# den 10-%-Rand hineinlaeuft, den der Riegel misst.
MASKABLE_MOTIV = 0.78

# Vierfache Abtastung, danach herunterskaliert - das ist die Kantenglaettung.
UEBERABTASTUNG = 4

DATEIEN = [
    ("icon-192.png", 192, False),
    ("icon-512.png", 512, False),
    ("icon-192-maskable.png", 192, True),
    ("icon-512-maskable.png", 512, True),
]


def _schild(zeichner, ox, oy, s):
    """Gruenes Schild mit abgerundeten Ecken - `x.fillStyle="#009640"` im Original."""
    zeichner.rounded_rectangle(
        [ox, oy, ox + s - 1, oy + s - 1],
        radius=s * ECKRADIUS,
        fill=GRUEN,
    )


def _ep(zeichner, ox, oy, s, fuellfarbe):
    """Weisses fettes "EP", geometrisch gesetzt, zentriert auf dem Schild.

    `fuellfarbe` ist die Farbe UNTER der Schrift - sie wird gebraucht, um den
    Innenraum des P wieder auszustanzen.
    """
    t = s * STAMMBREITE
    tb = s * BALKENSTAERKE
    h = s * VERSALHOEHE
    b = s * BUCHSTABENBREITE
    luecke = s * BUCHSTABENLUECKE

    gesamt = 2 * b + luecke
    x_e = ox + (s - gesamt) / 2.0
    x_p = x_e + b + luecke
    oben = oy + s * MITTE_Y - h / 2.0
    unten = oben + h

    # ── E: Stamm + drei Balken ──
    zeichner.rectangle([x_e, oben, x_e + t, unten], fill=WEISS)
    zeichner.rectangle([x_e, oben, x_e + b, oben + tb], fill=WEISS)
    zeichner.rectangle([x_e, unten - tb, x_e + b, unten], fill=WEISS)
    mitte = (oben + unten) / 2.0
    zeichner.rectangle(
        [x_e, mitte - tb / 2.0, x_e + b * MITTELBALKEN, mitte + tb / 2.0],
        fill=WEISS,
    )

    # ── P: Stamm + Schale mit ausgestanztem Innenraum ──
    bh = h * BOGENHOEHE
    zeichner.rounded_rectangle(
        [x_p, oben, x_p + b, oben + bh],
        radius=bh / 2.0,
        fill=WEISS,
    )
    innen_h = bh - 2 * tb
    innen_b = b - t - tb
    if innen_h > 0 and innen_b > 0:
        zeichner.rounded_rectangle(
            [x_p + t, oben + tb, x_p + b - tb, oben + bh - tb],
            radius=min(innen_h, innen_b) / 2.0,
            fill=fuellfarbe,
        )
    zeichner.rectangle([x_p, oben, x_p + t, unten], fill=WEISS)


def bild(kante, maskable):
    """Liefert das fertige RGBA-Bild in der gewuenschten Kantenlaenge."""
    gross = kante * UEBERABTASTUNG
    if maskable:
        # Deckende Flaeche: maskable-Icons duerfen nicht durchsichtig sein.
        im = Image.new("RGBA", (gross, gross), HINTERGRUND)
        seite = gross * MASKABLE_MOTIV
        rand = (gross - seite) / 2.0
    else:
        # Randlos und mit durchsichtigen Ecken - wie `canvas.toDataURL` heute.
        im = Image.new("RGBA", (gross, gross), (0, 0, 0, 0))
        seite = float(gross)
        rand = 0.0

    zeichner = ImageDraw.Draw(im)
    _schild(zeichner, rand, rand, seite)
    _ep(zeichner, rand, rand, seite, GRUEN)
    # BOX, nicht LANCZOS: LANCZOS hat negative Nebenkeulen und laesst die
    # Motivfarbe ueber die Kante hinaus "klingeln" - gemessen am 25.09.2026 mit
    # 432 Bildpunkten im 10-%-Rand von icon-192-maskable.png, die NICHT exakt
    # der Hintergrundfarbe entsprachen. Ein Sicherheitsrand, der die Motivfarbe
    # traegt, ist keiner. BOX mittelt reine Flaechen und kann nicht ueber-
    # schwingen - das ist genau die Ueberabtastung, die hier gemeint ist.
    return im.resize((kante, kante), Image.BOX)


def _bytes(kante, maskable):
    puffer = io.BytesIO()
    bild(kante, maskable).save(puffer, format="PNG", optimize=True)
    return puffer.getvalue()


def main(argv):
    nur_pruefen = "--pruefen" in argv
    abweichend = []
    for name, kante, maskable in DATEIEN:
        ziel = os.path.join(REPO_ROOT, name)
        neu = _bytes(kante, maskable)
        alt = None
        if os.path.exists(ziel):
            with open(ziel, "rb") as f:
                alt = f.read()
        if alt == neu:
            print("  gleich   %-24s %5d Bytes" % (name, len(neu)))
            continue
        abweichend.append(name)
        if nur_pruefen:
            print("  ANDERS   %-24s (Datei %s)" % (name, "fehlt" if alt is None else "veraltet"))
            continue
        with open(ziel, "wb") as f:
            f.write(neu)
        print("  %-8s %-24s %5d Bytes" % ("neu" if alt is None else "ersetzt", name, len(neu)))

    if nur_pruefen and abweichend:
        sys.stderr.write("Nicht aktuell: %s\n" % ", ".join(abweichend))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
