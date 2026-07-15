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


def test_abschnitt_B_hat_alle_sieben_kiosk_sperren():
    doc = _read("sql/TERMINAL_FINAL_v3.sql")
    for tbl in ("fz_fahrten", "fz_positions", "geo_cache", "kunden",
                "time_entries", "forms", "bautagebuch"):
        assert f"{tbl}_no_kiosk" in doc, f"Kiosk-Sperre {tbl}_no_kiosk fehlt in Abschnitt B"
    assert doc.count("AS RESTRICTIVE") == 7


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
