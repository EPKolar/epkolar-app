"""v3.9.657 KV-V3 Fix — Zuschlag-Report aggregiert pro TAG statt pro Eintrag.

Bug (v3.9.649): KVZuschlagReport rief _kvTagZuschlag mit den Stunden JEDES Eintrags
auf; bei mehreren Eintraegen/Tag (je Projekt) wurde Ueber-/Mehrarbeit systematisch
untererfasst. Fix: erst je (Monteur, Tag) summieren, dann _kvTagZuschlag auf die
Tagessumme. Strukturelle Verifikation der Zwei-Pass-Aggregation.
"""


def test_zwei_pass_aggregation(index_html):
    # Erst je (Monteur, Tag) summieren
    assert "var byWD={};" in index_html
    assert "day.hours+=hrs;" in index_html


def test_kvtagzuschlag_auf_tagessumme(index_html):
    # _kvTagZuschlag wird auf die Tagessumme (day.hours) aufgerufen, NICHT auf Einzel-hrs
    assert "_kvTagZuschlag(day.hours,norm,hundert,kv)" in index_html


def test_kein_pro_eintrag_zuschlag_mehr(index_html):
    # der alte per-Eintrag-Aufruf _kvTagZuschlag(hrs,norm,...) darf nicht mehr existieren
    assert "_kvTagZuschlag(hrs,norm,hundert,kv)" not in index_html


def test_hundert_aus_tages_von_bis(index_html):
    # 100%-Trigger aus der zusammengefassten Tages-von/bis
    assert "_kvHundert100(dow,fei,day.von,day.bis,ueber)" in index_html


def test_ohne_uhrzeit_pro_tag(index_html):
    # ohneUhr wird pro Ue-Tag ohne Uhrzeit gezaehlt (nicht pro Eintrag)
    assert "if(ueber>0&&!day.anyVonBis&&dow!==0&&!fei)a.ohneUhr+=1;" in index_html
