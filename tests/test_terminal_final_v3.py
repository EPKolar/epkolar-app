"""v3.9.703 — sql/TERMINAL_FINAL_v3.sql: der Selbst-Nachweis, dauerhaft abgesichert.

Der guard_urlaub_edit-Replace in diesem Run-Paket wurde auf dem ECHTEN Live-Body aufgebaut
(docs/wip/trigger_bodies_LIVE_2026-07-14.csv, kalibriert gegen die DB) plus einem minimal-
invasiven stempel_terminal-Zweig. Die Garantie: v3-Body MINUS Zweig == exakter Live-Body.

Dieser Test rechnet genau das nach — mit der Postgres-äquivalenten Normalisierung (ASCII-\\s,
btrim). Bricht er, hat jemand die Datei so geändert, dass sie nicht mehr NUR den Terminal-Zweig
hinzufügt — also womöglich Live-Logik gelöscht. Genau der Fehler, den das ganze Verfahren
verhindern soll.
"""
import re
import hashlib

CTRL_MD5 = "284dc6f19d45f4a8804ddb69e74e8ef6"
CTRL_LEN = 1746


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _pg_norm(s):
    return re.sub(r"[ \t\n\r\f\v]+", " ", s).strip(" ")


def _prosrc(create_stmt):
    m = re.search(r"AS (\$[A-Za-z_]*\$)(.*)\1", create_stmt, re.S)
    assert m, "prosrc-Delimiter nicht gefunden"
    return m.group(2)


def test_selbstnachweis_v3_minus_zweig_ist_der_livebody():
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    # Abschnitt A: die guard_urlaub_edit-Funktion (bis zum ersten $function$ ... $function$)
    m = re.search(r"CREATE OR REPLACE FUNCTION public\.guard_urlaub_edit\(\).*?\$function\$.*?\$function\$", doc, re.S)
    assert m, "guard_urlaub_edit-Definition in TERMINAL_FINAL_v3 nicht gefunden"
    v3_create = m.group(0)

    # Den stempel_terminal-Zweig herausschneiden (inkl. seiner Kommentarzeilen).
    branch = re.search(
        r"  -- v3\.9\.703: Stempel-Terminal.*?  IF c_role = 'stempel_terminal' THEN\n"
        r"    IF TG_OP = 'INSERT' AND COALESCE\(NEW\.status,'beantragt'\) = 'beantragt' THEN RETURN NEW; END IF;\n"
        r"    RAISE EXCEPTION 'stempel_terminal darf nur INSERT mit status=beantragt';\n"
        r"  END IF;\n",
        v3_create, re.S)
    assert branch, "stempel_terminal-Zweig nicht im erwarteten Format gefunden"

    v3_minus = v3_create.replace(branch.group(0), "", 1)
    norm = _pg_norm(_prosrc(v3_minus))
    assert len(norm) == CTRL_LEN, f"v3 minus Zweig hat {len(norm)} Zeichen, erwartet {CTRL_LEN} — Live-Logik verändert?"
    assert hashlib.md5(norm.encode()).hexdigest() == CTRL_MD5, \
        "v3 minus Zweig != Live-Body (284dc6f1...). Der Replace fügt nicht mehr NUR den Terminal-Zweig hinzu."


def test_zweig_steht_vor_dem_vollzugriff_check():
    """Der Terminal-Zweig braucht c_role (nach users-Lookup) und muss vor dem admin/PL/buero-Check
    stehen — sonst greift er nie oder umgeht Live-Logik."""
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    i_lookup = doc.find("FROM public.users u WHERE u.auth_user_id::text = c_sub;")
    i_branch = doc.find("IF c_role = 'stempel_terminal' THEN")
    i_full = doc.find("IF c_role IN ('admin','projektleiter','buero')")
    assert 0 < i_lookup < i_branch < i_full, "Zweig-Platzierung falsch (muss nach users-Lookup, vor Voll-Zugriff)"


def test_terminal_zweig_ist_nur_insert_beantragt():
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    assert "IF TG_OP = 'INSERT' AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;" in doc
    # kein UPDATE/DELETE-Recht für die Terminal-Rolle im Zweig:
    m = re.search(r"IF c_role = 'stempel_terminal' THEN(.*?)END IF;", doc, re.S)
    assert m and "UPDATE" not in m.group(1) and "DELETE" not in m.group(1)


# ---------------------------------------------------------------------------
# DIE ZWEITE RECHNUNG IST WEG (v3.9.922)
#
# Hier standen ZWEI Pruefungen derselben sieben Sperren untereinander:
#   1. je Tabelle `f"{tbl}_no_kiosk" in doc`
#   2. `doc.count("AS RESTRICTIVE") == 7`
#
# Nachgemessen, und die namentliche war die SCHLECHTERE von beiden: `in doc`
# trifft auch die Zeile `DROP POLICY IF EXISTS x_no_kiosk ON ...`, die direkt
# ueber jedem CREATE steht. Eine Sperre, die nur noch gedroppt und nicht mehr
# angelegt wird, waere durchgerutscht - genau das, was das Paket verhindern
# soll. Die Festzahl 7 hat das aufgefangen, aber blind: sie sagt nicht, WELCHE
# fehlt, und beim TAUSCH (eine Sperre umbenannt oder auf eine andere Tabelle
# gelegt) bleibt sie gruen.
#
# Deshalb jetzt EINE Rechnung: die MENGE der aktiven RESTRICTIVE-Policies wird
# gegen die sieben erwarteten Tripel (Policy-Name, Tabelle, Bedingung)
# verglichen. Das deckt alle Richtungen ab - fehlende Sperre, ueberzaehlige,
# vertauschte, und die mit richtigem Namen aber falscher Bedingung - und die
# Festzahl entfaellt ERSATZLOS, weil `==` auf Mengen die Vollzaehligkeit schon
# enthaelt.
#
# `-- `-Zeilen werden vorher entfernt: die Datei enthaelt einen komplett
# auskommentierten ROLLBACK-Block (Abschnitt A). Gemessen v3.9.922: dort steht
# heute keine Policy (0 CREATE POLICY in kommentierten Zeilen), aber ein Riegel,
# der auskommentierten Text mitzaehlt, ist genau der Fehler aus tests/_hilfen.py.
# ---------------------------------------------------------------------------
_KIOSK_TABELLEN = ("fz_fahrten", "fz_positions", "geo_cache", "kunden",
                   "time_entries", "forms", "bautagebuch")


# Mitgeprueft wird die BEDINGUNG: eine Policy, die `x_no_kiosk` heisst, aber
# auf etwas anderes gatet als die Kiosk-Rolle, waere ein Loch mit richtigem
# Namen. Das hat bisher NICHTS geprueft - `is_kiosk_role` kam in tests/ 0x vor.
_BEDINGUNG = "NOT public.is_kiosk_role()"


def _aktive_restriktive_policies(doc):
    """(Policy-Name, Tabelle, Bedingung) je AS-RESTRICTIVE-Policy.
    Auskommentierte Zeilen zaehlen NICHT mit."""
    aktiv = "\n".join(z for z in doc.splitlines() if not z.lstrip().startswith("--"))
    roh = re.findall(r"CREATE POLICY\s+(\S+)\s+ON\s+(\S+)\s+AS RESTRICTIVE"
                     r"\s+FOR ALL USING\s*\((.*?)\)\s*;", aktiv, re.S)
    return {(name, tab, " ".join(bed.split())) for name, tab, bed in roh}


def _erwartete_policies():
    return {("%s_no_kiosk" % t, "public.%s" % t, _BEDINGUNG)
            for t in _KIOSK_TABELLEN}


def test_abschnitt_B_hat_genau_die_sieben_kiosk_sperren():
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    assert _aktive_restriktive_policies(doc) == _erwartete_policies()


def test_umkehrprobe_nur_gedroppt_wird_rot():
    """Eine Sperre, die nur noch gedroppt und nicht mehr angelegt wird, muss
    auffallen. Der alte namentliche Riegel (`"kunden_no_kiosk" in doc`) war
    hier GRUEN - die DROP-Zeile enthaelt den Namen ja weiterhin."""
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    kaputt = doc.replace("CREATE POLICY kunden_no_kiosk",
                         "-- CREATE POLICY kunden_no_kiosk", 1)
    assert "kunden_no_kiosk" in kaputt, (
        "Vorbedingung der Probe: der Name MUSS in der DROP-Zeile stehen "
        "bleiben - sonst zeigt die Probe nicht, was sie zeigen soll"
    )
    assert _aktive_restriktive_policies(kaputt) != _erwartete_policies()


def test_umkehrprobe_tausch_wird_rot():
    """DER GRUND DER UMSTELLUNG. Eine Sperre wird auf eine andere Tabelle
    gelegt: `count("AS RESTRICTIVE")` bleibt 7 (die alte Zahl WAERE gruen),
    die Menge stimmt nicht mehr."""
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    kaputt = doc.replace("CREATE POLICY geo_cache_no_kiosk ON public.geo_cache",
                         "CREATE POLICY geo_cache_no_kiosk ON public.geo_cache_alt", 1)
    assert kaputt.count("AS RESTRICTIVE") == doc.count("AS RESTRICTIVE"), \
        "Vorbedingung: die Gesamtzahl MUSS beim Tausch gleich bleiben"
    assert _aktive_restriktive_policies(kaputt) != _erwartete_policies()


def test_umkehrprobe_falsche_bedingung_wird_rot():
    """Eine Sperre mit richtigem NAMEN, aber falscher Bedingung: Gesamtzahl
    und Namensmenge bleiben unveraendert - nur die Bedingung verraet das Loch.
    Beide Vorgaenger-Riegel (Name `in doc` und `count == 7`) waeren gruen."""
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    kaputt = doc.replace(
        "CREATE POLICY forms_no_kiosk ON public.forms AS RESTRICTIVE\n"
        "  FOR ALL USING ( NOT public.is_kiosk_role() );",
        "CREATE POLICY forms_no_kiosk ON public.forms AS RESTRICTIVE\n"
        "  FOR ALL USING ( true );", 1)
    assert kaputt != doc, "Umkehrprobe hat nichts veraendert"
    assert kaputt.count("AS RESTRICTIVE") == doc.count("AS RESTRICTIVE"), \
        "Vorbedingung: die Gesamtzahl MUSS gleich bleiben"
    assert "forms_no_kiosk" in kaputt, "Vorbedingung: der Name bleibt stehen"
    assert _aktive_restriktive_policies(kaputt) != _erwartete_policies()


def test_umkehrprobe_kommentar_zaehlt_nicht_mit():
    """Eine Policy im auskommentierten ROLLBACK-Block darf NICHT als aktive
    Sperre gelten - sonst zaehlt der Riegel wieder Prosa."""
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    getarnt = (doc + "\n-- CREATE POLICY schein_no_kiosk ON public.schein AS RESTRICTIVE\n"
               "--   FOR ALL USING ( NOT public.is_kiosk_role() );\n")
    assert _aktive_restriktive_policies(getarnt) == _erwartete_policies()
    # Gegenrichtung: ohne den Kommentar-Filter WAERE sie mitgezaehlt worden.
    assert "schein_no_kiosk" in getarnt, \
        "Umkehrprobe traegt nicht - der getarnte Text ist gar nicht da"


def test_rollback_enthaelt_den_livebody():
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    assert "ROLLBACK ABSCHNITT A" in doc
    # Der Rollback-Block ist auskommentiert (jede Zeile mit -- ), enthält aber die Live-Signatur:
    assert "-- CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()" in doc


def test_fuenf_live_bodies_liegen_im_repo():
    import os
    for name in ("guard_urlaub_edit", "guard_kontingent", "guard_projects",
                 "guard_admin_only", "guard_users_privilege"):
        p = f"docs/wip/{name}_LIVE_2026-07-14.sql"
        assert os.path.exists(p), f"{p} fehlt"
