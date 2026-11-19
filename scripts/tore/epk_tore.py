"""EPKolar Release-Tore (Sebastian 16.11.2026: "hooks und tore, dauerregeln").

Aufruf:  python C:/Users/technik/.claude/hooks/epk_tore.py C:/repos/<baum> [--ohne-suite]
Prueft im Baum alle Tore. NUR wenn ALLE gruen sind, schreibt es <git-dir>/epk-tore-ok = HEAD-SHA.
Der Hook bau-sperre.js laesst den Push auf main nur fuer genau diesen HEAD durch.
--ohne-suite prueft alles ausser der vollen Suite und schreibt KEINE Marke (Vorpruefung).

Tore:
 1 Arbeitsbaum sauber (bis auf docs/befunde/AUSLIEFERUNG.json)
 2 node scripts/node_check.py exit 0
 3 Klammer-Baseline () -1 {} 0 [] 0
 4 7 md5-geschuetzte Funktionen unveraendert
 5 node sql/_check_version.js -> "versions synced"
 6 Fast-Forward: origin/main ist Vorfahr von HEAD (nach git fetch)
 7 kein Test mit offa/juprowa/feed im Namen gegenueber origin/main geaendert
 8 volle Suite in zwei Haelften (speicherschonend), 0 failed/error, und
   passed+skipped+xfailed+xpassed beider Haelften == Gesamtzahl von --collect-only
"""
import os, re, subprocess, sys

def lauf(args, cwd, timeout=900):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def suite_teil(dateien, repo):
    """Laeuft pytest direkt (subprocess, keine Pipe). Rueckgabe (exit_code, gruen_gezaehlt, rot_gezaehlt).
    Der Exit-Code kommt von pytest selbst, nicht von tail/tee."""
    rc, out = lauf([sys.executable, "-m", "pytest", *dateien, "-q", "-p", "no:cacheprovider"], repo, timeout=1500)
    bilanz = [z for z in out.splitlines() if re.search(r"\d+ (passed|failed|errors?)", z)]
    b = bilanz[-1] if bilanz else out.strip()[-200:]
    print("   Haelfte:", b, "| pytest-Exit", rc, flush=True)
    summe, fehler = 0, 0
    for zahl, art in re.findall(r"(\d+) (passed|skipped|xfailed|xpassed|failed|errors?)", b):
        if art in ("failed", "error", "errors"): fehler += int(zahl)
        else: summe += int(zahl)
    return rc, summe, fehler

def selbsttest():
    """Umkehrprobe fuers Tor: ein bewusst roter Test MUSS Tor 8 rot machen (Exit-Code UND Bilanz)."""
    import tempfile
    d = tempfile.mkdtemp(prefix="epk_tor_selbsttest_")
    os.makedirs(os.path.join(d, "tests"))
    open(os.path.join(d, "tests", "test_rot.py"), "w").write("def test_rot():\n    assert False\n\ndef test_gruen():\n    assert True\n")
    rc, s, f = suite_teil(["tests/test_rot.py"], d)
    rot_erkannt = rc != 0 and f == 1 and s == 1
    open(os.path.join(d, "tests", "test_rot.py"), "w").write("def test_gruen():\n    assert True\n")
    rc2, s2, f2 = suite_teil(["tests/test_rot.py"], d)
    gruen_erkannt = rc2 == 0 and f2 == 0 and s2 == 1
    print("SELBSTTEST:", "OK" if rot_erkannt and gruen_erkannt else "LECK",
          f"(rot: exit={rc} gruen={s} rot={f}; gruen: exit={rc2} gruen={s2} rot={f2})")
    return 0 if rot_erkannt and gruen_erkannt else 1

def main():
    if "--selbsttest" in sys.argv:
        return selbsttest()
    if len(sys.argv) < 2:
        print(__doc__); return 2
    repo = sys.argv[1]
    ohne_suite = "--ohne-suite" in sys.argv
    ok = True
    def tor(name, gut, info=""):
        nonlocal ok
        ok = ok and gut
        print(("GRUEN " if gut else "ROT   ") + name + ("  | " + info if info else ""), flush=True)

    _, head = lauf(["git", "rev-parse", "HEAD"], repo); head = head.strip()
    _, gd = lauf(["git", "rev-parse", "--git-dir"], repo); gd = gd.strip()
    if not os.path.isabs(gd): gd = os.path.join(repo, gd)
    marke = os.path.join(gd, "epk-tore-ok")
    if os.path.exists(marke): os.remove(marke)

    _, st = lauf(["git", "status", "--porcelain"], repo)
    rest = [z for z in st.splitlines() if z.strip() and "AUSLIEFERUNG.json" not in z]
    tor("1 Arbeitsbaum sauber", not rest, "; ".join(rest[:5]))

    rc, out = lauf([sys.executable, "scripts/node_check.py"], repo)
    tor("2 node_check", rc == 0, out.strip().splitlines()[-1] if out.strip() else "")

    rc, out = lauf([sys.executable, "scripts/_bracket_check.py"], repo)
    zeilen = " ".join(out.split())
    tor("3 Klammer-Baseline", "() -1" in zeilen and "{} 0" in zeilen and "[] 0" in zeilen, zeilen[-40:])

    rc, out = lauf([sys.executable, "scripts/md5_geschuetzt.py"], repo)
    tor("4 md5 geschuetzt", rc == 0 and "unveraendert" in out, out.strip().splitlines()[-1] if out.strip() else "")

    rc, out = lauf(["node", "sql/_check_version.js"], repo)
    m = re.search(r"versions synced:\s*(\S+)", out)
    tor("5 Versionen synchron", rc == 0 and bool(m), m.group(1) if m else out.strip()[-120:])

    lauf(["git", "fetch", "-q", "origin"], repo)
    rc, _ = lauf(["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"], repo)
    tor("6 Fast-Forward ueber origin/main", rc == 0)

    _, diff = lauf(["git", "diff", "--name-only", "origin/main", "HEAD"], repo)
    offa = [d for d in diff.splitlines() if d.startswith("tests/") and re.search(r"offa|juprowa|feed", d, re.I)]
    tor("7 offa/juprowa/feed-Tests unberuehrt", not offa, ", ".join(offa))

    if ohne_suite:
        print("Vorpruefung ohne Suite - keine Marke geschrieben."); return 0 if ok else 1
    if not ok:
        print("Tore rot - Suite nicht gestartet, keine Marke."); return 1

    _, coll = lauf([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q", "-p", "no:cacheprovider"], repo)
    mc = re.search(r"(\d+) tests? collected", coll)
    gesamt = int(mc.group(1)) if mc else -1
    dateien = sorted(f"tests/{f}" for f in os.listdir(os.path.join(repo, "tests")) if f.startswith("test_") and f.endswith(".py"))
    haelfte = len(dateien) // 2
    summe, fehler, rcs = 0, 0, []
    for teil in (dateien[:haelfte], dateien[haelfte:]):
        rc, s, f = suite_teil(teil, repo)
        summe += s; fehler += f; rcs.append(rc)
    # Haertung 19.11.: Exit-Code von pytest zaehlt ZUSAETZLICH zur Bilanzzeile (kein Pipe-/Zeilen-Leck)
    tor("8 volle Suite", fehler == 0 and summe == gesamt and all(r == 0 for r in rcs),
        f"{summe} von {gesamt} gesammelt, {fehler} rot, pytest-Exit {rcs}")

    if ok:
        open(marke, "w").write(head + "\n")
        print(f"ALLE TORE GRUEN - Marke fuer {head[:7]} geschrieben. Push frei.")
        return 0
    print("TORE ROT - keine Marke, Push bleibt gesperrt.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
