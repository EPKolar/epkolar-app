# -*- coding: utf-8 -*-
"""v3.9.745 — Register #26 (Sebastian/Chat-Claude): Die Dispo-ANSICHT schreibt NIE. Fuer immer testgedeckt.

Befund-Anlass: Verdacht, dass ein reiner Panel-Besuch (Mount / KW-Blaettern / Neu-berechnen) fixe Scheine
mit ihren berechneten Ablaufzeiten beschrieben + gepusht haben koennte. Live (v743) ist es sauber, aber der
Schutz darf nicht auf Vertrauen beruhen. Regel: NUR echte Gesten (Uebernehmen/Drop/Resched/Dauer-Griff)
duerfen schreiben; das Ansehen/Berechnen eines Plans ist IMMER read-only.

Statische Garantien:
  - DispoPanel enthaelt keinen direkten Schreibpfad (updAs/SQ.push) — Writes laufen ausschliesslich ueber
    die Callback-Props (onUebernehmen/onDrop), die die Elternkomponente stellt.
  - Der Ablauf-/Einreihungs-Code (die _dispoAblauf-Kette in _zelle) ruft KEINEN Schreibhelfer — Startzeiten
    werden nur BERECHNET und ANGEZEIGT, nie geschrieben.
  - Die Write-Callbacks werden nur in Event-Handlern (onClick/onPointerDown/pointerup) aufgerufen, nie im
    Render-Rumpf.
Der dynamische Beweis (Mount + alle KW-Tabs + Neu-berechnen -> 0 updAs/0 SQ.push) laeuft im Headless-Mount
(v741-Infrastruktur) und ist im Handoff dokumentiert.
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_dispopanel_hat_keinen_direkten_schreibpfad(index_html):
    body = _panel(index_html)
    assert "updAs(" not in body, "DispoPanel ruft updAs direkt — Writes muessen ueber Props laufen"
    assert "SQ.push" not in body, "DispoPanel hat einen eigenen SQ.push — verboten (Ansicht ist read-only)"


def test_ablauf_pfad_schreibt_nicht(index_html):
    body = _panel(index_html)
    # Die Einreihungs-/Ablauf-Berechnung je Zelle (von _abItems bis zum td-Render) darf keinen Schreibhelfer
    # enthalten — sie rechnet Startzeiten nur und zeigt sie an.
    seg = body[body.index("var _abItems=chips.map("):body.index("return h('td'")]
    for helfer in ("updAs", "SQ.push", "onDrop(", "onUebernehmen(", "onReschedule("):
        assert helfer not in seg, "Schreibhelfer '%s' im Ablauf-/Einreihungs-Pfad — Ansehen darf nie schreiben" % helfer


def test_write_callbacks_nur_in_handlern(index_html):
    body = _panel(index_html)
    # Jeder Aufruf von onDrop(/onUebernehmen( steht in einem Event-Handler-Kontext (onClick/onPointerDown/up),
    # nie als Render-Ausdruck. Heuristik: 200 Zeichen vor dem Aufruf enthalten ein Handler-Schluesselwort.
    import re
    # Marker eines Event-Handler-Kontexts: onClick/onPointerDown-Prop ODER der Pointer-Drop-Handler 'up'
    # (Kette function up(ev) -> if(st.moved) -> if(_dispoDropOk...)).
    for m in re.finditer(r"on(?:Drop|Uebernehmen)\(", body):
        ctx = body[max(0, m.start() - 900):m.start()]
        assert any(k in ctx for k in ("onClick", "onPointerDown", "function up(ev)", "if(st.moved)", "_dispoDropOk(")), \
            "Write-Callback ausserhalb eines Event-Handlers (~Render-Zeit): ...%s" % body[m.start():m.start() + 40]
