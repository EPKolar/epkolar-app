"""sql/_sql_aus_datei.py ist fest an das Prod-Projekt jiggujpruejkaomgxarp gebunden (GF 24.11.2026).

Der Zugangsschluessel gilt fuer das ganze Supabase-Konto. Jede andere Projekt-ID - ueber die Konstante, eine
Umgebungsvariable oder ein Argument - muss VOR jedem Netzzugriff abbrechen. Kein Test sendet etwas: urlopen ist
ersetzt und schlaegt fehl, falls es doch aufgerufen wird.
"""
import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKRIPT = os.path.join(ROOT, "sql", "_sql_aus_datei.py")
ANDERES = "mvbngdgzeewdudjcblab"


@pytest.fixture
def mod(monkeypatch):
    spec = importlib.util.spec_from_file_location("_sql_aus_datei_t", SKRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    gesendet = []

    def kein_netz(*a, **k):
        gesendet.append(a)
        raise AssertionError("Netzzugriff trotz falschem Projekt")

    monkeypatch.setattr(m.urllib.request, "urlopen", kein_netz)
    monkeypatch.setenv("SUPABASE_ACCESS_TOKEN", "nur-ein-testwert")
    for v in ("SUPABASE_PROJECT_REF", "SUPABASE_PROJECT_ID", "PROJECT_REF"):
        monkeypatch.delenv(v, raising=False)
    m._gesendet = gesendet
    return m


def test_fest_gebunden(mod):
    assert mod.FEST == "jiggujpruejkaomgxarp" and mod.PROJEKT == mod.FEST


def test_anderes_projekt_ueber_konstante_bricht_ab(mod, monkeypatch):
    monkeypatch.setattr(mod, "PROJEKT", ANDERES)
    with pytest.raises(SystemExit) as e:
        mod.senden(b"select 1")
    assert "falsches Projekt" in str(e.value) and mod._gesendet == []


@pytest.mark.parametrize("var", ["SUPABASE_PROJECT_REF", "SUPABASE_PROJECT_ID", "PROJECT_REF"])
def test_anderes_projekt_ueber_umgebung_bricht_ab(mod, monkeypatch, var):
    monkeypatch.setenv(var, ANDERES)
    with pytest.raises(SystemExit) as e:
        mod.main(["x", "mf", "probe"])
    assert "falsches Projekt" in str(e.value) and mod._gesendet == []


@pytest.mark.parametrize("arg", [["--projekt", ANDERES], ["--projekt=" + ANDERES]])
def test_anderes_projekt_ueber_argument_bricht_ab(mod, arg):
    with pytest.raises(SystemExit) as e:
        mod.main(["x", "dispo", "einspielen", "0" * 32, "--ja"] + arg)
    assert "falsches Projekt" in str(e.value) and mod._gesendet == []


def test_richtiges_projekt_kommt_bis_zum_senden(mod, monkeypatch):
    # Positivkontrolle: mit dem richtigen Projekt wird versucht zu senden (hier abgefangen) -> die Sperre ist nicht
    # einfach "immer zu".
    monkeypatch.setenv("SUPABASE_PROJECT_REF", "jiggujpruejkaomgxarp")
    with pytest.raises(AssertionError, match="Netzzugriff"):
        mod.senden(b"select 1")
    assert len(mod._gesendet) == 1


def test_ohne_schluessel_wird_nichts_gesendet(mod, monkeypatch):
    monkeypatch.delenv("SUPABASE_ACCESS_TOKEN")
    with pytest.raises(SystemExit) as e:
        mod.senden(b"select 1")
    assert "SUPABASE_ACCESS_TOKEN fehlt" in str(e.value) and mod._gesendet == []
