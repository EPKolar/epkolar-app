"""v3.9.661 Kern-View-Bug-Hunt — Stundenbestaetigung Sonntag-Label-Fix.

DAYS wurde in v3.9.546 auf 7 (Mo-So) erweitert, die lokalen Label-Arrays
FULL_DAYS/STD_TIMES in exportWochenStz/exportTagesStz blieben aber bei 6:
- Wochen-Stz: DAYS.forEach erzeugte fuer i=6 einen Block mit leerem Wochentagsnamen.
- Tages-Stz: FULL_DAYS[6]===undefined → "undefined" in Titel/Dateiname/Toast.
"""


def test_wochen_full_days_7(index_html):
    # FULL_DAYS in exportWochenStz um Sonntag ergaenzt
    assert index_html.count(
        'const FULL_DAYS=["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"];'
    ) == 2  # exportWochenStz + exportTagesStz


def test_wochen_std_times_7(index_html):
    # STD_TIMES hat jetzt 7 Elemente (2x "" am Ende: Samstag + Sonntag)
    assert '"7.00 Uhr - 12.00 Uhr","",""];' in index_html


def test_wochen_skip_empty_sunday(index_html):
    assert "if(i>=6&&dt===0&&arr.length===0)return;" in index_html


def test_wochen_header_end_date_dynamic(index_html):
    assert "bis <b>${dayTotal(6)>0?dateFmt(6):dateFmt(5)}</b>" in index_html


def test_no_six_element_full_days_left(index_html):
    # Keine 6-elementige FULL_DAYS-Definition mehr uebrig
    assert 'const FULL_DAYS=["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"];' not in index_html
