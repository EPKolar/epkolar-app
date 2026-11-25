"""v3.9.1121 - Uebrige echte Namen im Code durch Platzhalter/Rollen ersetzt.

Suchliste: Nach- und Vornamen aus den Startlisten MONT/INIT_USERS des Stands
05cfb99 (3.9.1119) - sie werden zur Laufzeit aus git gelesen, damit dieser
Test selbst keine Namen traegt.

Geprueft wird nur Code (Kommentare ausgeblendet). Erlaubt bleiben nur die
funktionalen Stellen (siehe ERLAUBT):
  - Vergleiche des angemeldeten Benutzernamens mit festen Benutzernamen
    (user.username==="..." / curUser.username==="...") - Rechtesteuerung
  - SACHBEARBEITER-Auswahlliste (Werte stehen so in Arbeitsscheinen)
  - _fixAdminName (Anzeigename-Korrektur fuer das Admin-Konto)
Umkehrprobe: dieselbe Pruefung gegen 05cfb99 MUSS Funde liefern.
"""
import io
import os
import re
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIS = "05cfb99"

ERLAUBT = [  # erlaubte Bereiche im (kommentarfreien) Code - Treffer muessen GANZ darin liegen
    re.compile(r'\.username==="[a-z]+"'),
    re.compile(r"const SACHBEARBEITER=\[[^\]]*\]"),
    re.compile(r"const _fixAdminName=\(u\)=>\{.*?return u;\};"),
]


def _jetzt():
    return io.open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()


def _basis():
    try:
        out = subprocess.run(["git", "-C", ROOT, "show", BASIS + ":index.html"],
                             capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Basis %s nicht im Repo lesbar" % BASIS)
    return out.stdout.decode("utf-8")


def _namen():
    b = _basis()
    a = b.index("const MONT=[")
    blk = b[a:b.index("];", a)]
    paare = re.findall(r'n:"([^"]+)",vorname:"([^"]+)"', blk)
    assert len(paare) == 8, "Suchliste nicht ermittelbar"
    nach = sorted({p[0] for p in paare})
    vor = sorted({p[1] for p in paare})
    # Umschrift ue/u fuer Umlaute mitsuchen
    extra = set()
    for n in nach:
        if "ü" in n:
            extra.add(n.replace("ü", "ue"))
    return nach + sorted(extra), vor


def _maske(src):
    """Kommentare durch Leerzeichen ersetzen (Zeilen bleiben), Zeichenketten beachten."""
    out = []
    i, n, st = 0, len(src), None
    while i < n:
        c = src[i]
        if st is None:
            if src.startswith("/*", i):
                j = src.find("*/", i + 2)
                j = n if j < 0 else j + 2
                out.append(re.sub(r"[^\r\n]", " ", src[i:j]))
                i = j
                continue
            if src.startswith("//", i) and (i == 0 or src[i - 1] not in ":\"'\\"):
                j = src.find("\n", i)
                j = n if j < 0 else j
                out.append(" " * (j - i))
                i = j
                continue
            if c in "\"'`":
                st = c
            out.append(c)
            i += 1
        else:
            if c == "\\":
                out.append(src[i:i + 2])
                i += 2
                continue
            if c == st or (c == "\n" and st != "`"):
                st = None
            out.append(c)
            i += 1
    return "".join(out)


def funde(src):
    nach, vor = _namen()
    pat = re.compile(r"(?i:" + "|".join(map(re.escape, nach)) + r")|\b(?:" + "|".join(map(re.escape, vor)) + r")\b")
    code = _maske(src)
    frei = [(m.start(), m.end()) for e in ERLAUBT for m in e.finditer(code)]
    out = []
    for m in pat.finditer(code):
        if any(a <= m.start() and m.end() <= b for a, b in frei):
            continue
        out.append(code.count("\n", 0, m.start()) + 1)
    return sorted(set(out))


def test_keine_echten_namen_im_code():
    f = funde(_jetzt())
    assert not f, "Echte Namen im Code (Zeilen): %r" % f


def test_umkehrprobe_basis_hat_namen_im_code():
    f = funde(_basis())
    # Basis: MONT, INIT_USERS, DEMO_FZ, Bescheinigung, Ansprechpartner, Hinweistext, Suchbeispiel, Bezeichner
    assert len(f) >= 6, f


def test_erlaubte_stellen_sind_wirklich_nur_vergleiche():
    """Die Ausnahmen duerfen keine neuen Namen verstecken: Benutzernamen-Vergleiche sind
    reine Kleinbuchstaben-Logins, und es gibt genau eine SACHBEARBEITER-Liste."""
    code = _maske(_jetzt())
    assert code.count("const SACHBEARBEITER=[") == 1
    assert code.count("const _fixAdminName=(u)=>") == 1


def test_rollen_statt_personen():
    s = _jetzt()
    assert 'const kontaktPerson=pvAnsprechpartner==="lager"?"Lagerleitung":monteurName;' in s
    assert '<span class="n">(6) Name und Vorname</span><span class="v">&nbsp;</span>' in s
    assert "Musterprojekt 1" in s and "portalCode" not in s[s.index("const INIT_PROJECTS=["):s.index("];", s.index("const INIT_PROJECTS=["))]
