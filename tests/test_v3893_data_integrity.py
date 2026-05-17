"""v3.8.93 Sprint-8 Data-Integrity (Agent QQ): S8-1 + S8-3 + S8-7.

Drei Regression-Tests fuer data-integrity-Fixes:

* **S8-1 (Fire-Calls Kennzeichen-Fallback):** Wenn `f.kennzeichen` fehlt
  (Legacy- oder Teil-Datensaetze), muss die UI auf `f.id` fallen und sonst
  "Fzg" anzeigen. Pattern: ``f.kennzeichen||f.id||"Fzg"``.
* **S8-3 (Pickerl ISO-Date-Validation):** Pickerl-Datum muss vor dem
  `Date()`-Konstruktor mit ISO-Format-Regex
  ``/^\\d{4}-\\d{2}-\\d{2}/`` validiert werden, um
  ``Invalid Date``-Resultate zu vermeiden.
* **S8-7 (Sub-Tag Kennzeichen-Fallback):** Sub-Tag-Anzeige im
  Fahrtenbuch-Detail muss auf ``"Fzg"`` fallen wenn `f.kennzeichen`
  fehlt. Pattern: ``(f.kennzeichen||"Fzg")+" · "+fdt`` (oder
  aequivalent mit anderem Separator/aehnlicher Konkatenation).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_kennzeichen_fallback_in_fire_calls():
    """v3.8.93 S8-1: Fire-Calls muessen kennzeichen||id||"Fzg" Fallback haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: f.kennzeichen||f.id||"Fzg"  (tolerate single/double quotes + spacing)
    pattern = re.compile(
        r'f\.kennzeichen\s*\|\|\s*f\.id\s*\|\|\s*["\']Fzg["\']'
    )
    m = pattern.search(text)
    assert m, (
        'v3.8.93 S8-1: Fire-Calls Kennzeichen-Fallback fehlt. '
        'Erwartet Pattern `f.kennzeichen||f.id||"Fzg"` damit Legacy- oder '
        'unvollstaendige Fzg-Datensaetze nicht als "undefined" angezeigt werden.'
    )


def test_iso_date_validation_pickerl():
    """v3.8.93 S8-3: Pickerl-Datum muss ISO-Regex-Validierung haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: /^\d{4}-\d{2}-\d{2}/.test(f.pickerl
    # Tolerate optional whitespace, accept .test() or .exec() chain start.
    pattern = re.compile(
        r'/\^\\d\{4\}-\\d\{2\}-\\d\{2\}/\s*\.\s*test\s*\(\s*f\.pickerl'
    )
    m = pattern.search(text)
    assert m, (
        'v3.8.93 S8-3: Pickerl-ISO-Date-Validation fehlt. '
        'Erwartet Pattern `/^\\d{4}-\\d{2}-\\d{2}/.test(f.pickerl...)` '
        'vor jeder `new Date(f.pickerl)`-Verwendung, '
        'um Invalid-Date-Ergebnisse bei korruptem/leerem Pickerl-Feld '
        'zu vermeiden.'
    )


def test_sub_tag_kennzeichen_fallback():
    """v3.8.93 S8-7: Sub-Tag im Fahrtenbuch muss kennzeichen||"Fzg" Fallback haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: (f.kennzeichen||"Fzg")+" · "+fdt -- toleriere verschiedene
    # Separator-Encodings (UTF-8 ·, ASCII -, Bullet •) und beliebige
    # Quoting-Varianten/Whitespace.
    pattern = re.compile(
        r'\(\s*f\.kennzeichen\s*\|\|\s*["\']Fzg["\']\s*\)\s*\+\s*["\'][^"\']{1,8}["\']\s*\+\s*fdt'
    )
    m = pattern.search(text)
    assert m, (
        'v3.8.93 S8-7: Sub-Tag Kennzeichen-Fallback fehlt. '
        'Erwartet Pattern `(f.kennzeichen||"Fzg")+" · "+fdt` (oder '
        'aehnliche Konkatenation mit beliebigem Separator) im '
        'Fahrtenbuch-Sub-Tag, damit Sub-Tag nicht "undefined · ..." '
        'anzeigt wenn kennzeichen fehlt.'
    )
