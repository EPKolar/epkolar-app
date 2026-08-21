"""
Nachtlauf-Hunt v3.9.852 — stiller AS-Ladeausfall am Monteur-Wandpanel sichtbar.

Kiosk-Agent-Fund P2 (Diagnose-Lücke): der v3.9.827-Marker `window.__kioskAsErr`
(gesetzt in `_kioskWeekArbeitsscheine` :2017 bei RLS/401/Netz/parse) wurde NIE
gerendert → die erklärte Absicht (Ausfall per Foto vom Wandpanel diagnostizierbar)
blieb unerreicht. Der Zwilling `__kioskFzErr` zeigt es in der WochenplanTafel
(:6698). Fix: AS-Fehler-Diagnosezeile im MonteurTafel-Kopf.
"""


def test_kiosk_as_err_wird_gerendert(index_html):
    # __kioskAsErr wird jetzt im Render gelesen (nicht nur gesetzt)
    assert "window.__kioskAsErr&&window.__kioskAsErr!=='ok')?window.__kioskAsErr:null" in index_html
    assert "'⚠️ AS:Fehler('+_asErr+')'" in index_html


def test_marker_wird_weiterhin_gesetzt(index_html):
    # der Setter (Quelle) bleibt unveraendert
    assert 'window.__kioskAsErr="HTTP"+((r&&r.status)||' in index_html
    assert "window.__kioskAsErr=(_kwaJ===null)?'parse':null;" in index_html
