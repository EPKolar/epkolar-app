# Erzeugt qnap/qnap-gateway-inline.compose.yml (image-freie Variante fuer Container Station) aus den Repo-Dateien.
# Aufruf aus dem Repo-Wurzelverzeichnis:  python tools/kamera-proxy-auth/qnap/inline_bauen.py
# Eingebettet werden verify.mjs, token.mjs und qnap/Caddyfile als base64 (Inhalt mit LF-Zeilenenden = Git-Blob).
# Der Riegel tests/test_kamera_inline_compose.py prueft, dass die Blobs Zeichen fuer Zeichen zu den Dateien dekodieren.
import base64, io, os

HIER = os.path.dirname(os.path.abspath(__file__))
AUTH = os.path.dirname(HIER)
ZIEL = os.path.join(HIER, "qnap-gateway-inline.compose.yml")


def lf_text(pfad):
    return io.open(pfad, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def b64(pfad):
    return base64.b64encode(lf_text(pfad).encode("utf-8")).decode("ascii")


VORLAGE = """# EP Kolar Kamera-Gateway auf der QNAP - image-freie Variante (kein build), fuer Container Station "Anwendung erstellen".
# ERZEUGT von qnap/inline_bauen.py - nicht von Hand aendern; der Riegel tests/test_kamera_inline_compose.py prueft, dass
# die base64-Blobs Zeichen fuer Zeichen zu verify.mjs, token.mjs und qnap/Caddyfile dekodieren.
# Inhaltlich wie qnap/docker-compose.yml: kamera-auth (Pruefer, nicht veroeffentlicht) + caddy (einziger Web-Eingang).
# Die Dateien werden beim Start aus der Umgebung dekodiert (tmpfs, Dateisystem sonst read_only).
# KEINE Secrets, KEINE Adressen hier. .env auf der QNAP (chmod 600, siehe ENV.md):
#   KAMERA_TOKEN_SECRET (Pflicht, = Supabase-Secret), QNAP_LAN_IP (Pflicht), GATEWAY_PORT (Standard 8443),
#   GO2RTC_BASIC (Pflicht, base64 von <go2rtc-API-Benutzer>:<Kennwort>, Caddy meldet sich damit bei go2rtc an).
# go2rtc laeuft separat (eigene App, Host-Netz :1984). :1984 im LAN sperren; :GATEWAY_PORT + :8555 TCP/UDP offen.
# Surveillance Station / Aufnahmen: TABU.

services:
  kamera-auth:
    image: node:22.11.0-alpine3.20
    restart: unless-stopped
    user: node
    read_only: true
    tmpfs:
      - /app:uid=1000,gid=1000,mode=0700
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    expose: ["9099"]
    command: ["sh", "-c", "printf %s \\"$$KA_TOKEN_B64\\" | base64 -d > /app/token.mjs && printf %s \\"$$KA_VERIFY_B64\\" | base64 -d > /app/verify.mjs && unset KA_TOKEN_B64 KA_VERIFY_B64 && exec node /app/verify.mjs"]
    environment:
      - NODE_ENV=production
      - KAMERA_TOKEN_SECRET=${{KAMERA_TOKEN_SECRET:?KAMERA_TOKEN_SECRET fehlt (gleicher Wert wie das Supabase-Secret)}}
      - KAMERA_AUTH_HOST=0.0.0.0
      - KAMERA_AUTH_PORT=9099
      - KAMERA_AUTH_URI_HEADER=x-forwarded-uri
      - KAMERA_AUTH_METHOD_HEADER=x-forwarded-method
      - KAMERA_AUTH_LOG=${{KAMERA_AUTH_LOG:-1}}
      - KA_TOKEN_B64={token}
      - KA_VERIFY_B64={verify}

  caddy:
    image: caddy:2.8.4-alpine
    restart: unless-stopped
    depends_on: [kamera-auth]
    tmpfs:
      - /cfg:mode=0700
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: ["no-new-privileges:true"]
    ports:
      - "${{QNAP_LAN_IP:?QNAP_LAN_IP fehlt}}:${{GATEWAY_PORT:-8443}}:${{GATEWAY_PORT:-8443}}"
    command: ["sh", "-c", "printf %s \\"$$CADDYFILE_B64\\" | base64 -d > /cfg/Caddyfile && exec caddy run --config /cfg/Caddyfile --adapter caddyfile"]
    environment:
      - QNAP_LAN_IP=${{QNAP_LAN_IP:?QNAP_LAN_IP fehlt}}
      - GATEWAY_PORT=${{GATEWAY_PORT:-8443}}
      - GO2RTC_BASIC=${{GO2RTC_BASIC:?GO2RTC_BASIC fehlt (base64 von go2rtc-API-Benutzer:Kennwort)}}
      - CADDYFILE_B64={caddy}
    volumes:
      - caddy_daten:/data            # interne CA + Zertifikate (root.crt fuer die Firmengeraete liegt hier)
      - caddy_konfig:/config
      - ./protokoll:/protokoll       # Zugriffsprotokoll OHNE Tokens

volumes:
  caddy_daten: {{}}
  caddy_konfig: {{}}
"""


def bauen():
    return VORLAGE.format(
        token=b64(os.path.join(AUTH, "token.mjs")),
        verify=b64(os.path.join(AUTH, "verify.mjs")),
        caddy=b64(os.path.join(HIER, "Caddyfile")),
    )


# ── Variante oeffentliches Zertifikat (Let's Encrypt per DNS-01, acme.sh im DNS-Alias-Modus ueber deSEC) ─────────────
ZIEL_PUBLIC = os.path.join(HIER, "qnap-gateway-publiccert-inline.compose.yml")

VORLAGE_PUBLIC = """# EP Kolar Kamera-Gateway auf der QNAP - Variante OEFFENTLICHES ZERTIFIKAT (https://kameras.ep-kolar.at:8443), image-frei.
# ERZEUGT von qnap/inline_bauen.py - nicht von Hand aendern; der Riegel tests/test_kamera_publiccert.py prueft, dass die
# base64-Blobs Zeichen fuer Zeichen zu verify.mjs, token.mjs, qnap/Caddyfile.publiccert, qnap/caddy_start.sh und
# qnap/acme_start.sh dekodieren.
# Dienste: kamera-auth (Pruefer, nicht veroeffentlicht) + caddy (einziger Web-Eingang, tls aus /certs, nur lesend)
#          + acme (acme.sh: Let's Encrypt per DNS-01 im DNS-Alias-Modus ueber deSEC; KEIN Port, KEIN Docker-Socket).
# Kein eingehender Port aus dem Internet: Let's Encrypt prueft nur den TXT-Eintrag bei deSEC (CNAME von myNET dorthin).
# KEINE Secrets, KEINE Adressen hier. .env auf der QNAP (chmod 600, siehe ENV.md):
#   KAMERA_TOKEN_SECRET, QNAP_LAN_IP, KAMERA_HOST, ALIAS_ZONE, ACME_EMAIL, DEDYN_TOKEN (Pflicht), GATEWAY_PORT (8443),
#   ALIAS_ART (challenge|domain, Standard challenge).
# Erneuerung: acme.sh --reloadcmd aendert /certs/.erneuert -> caddy_start.sh beendet Caddy -> restart startet frisch.
# Container-Station-App-Name: kamera-gateway. Vorher die tls-internal-App stoppen (gleicher Port).
# go2rtc laeuft separat (eigene App, Host-Netz :1984). :1984 im LAN sperren; :GATEWAY_PORT + :8555 TCP/UDP offen.
# Surveillance Station / Aufnahmen: TABU.

services:
  kamera-auth:
    image: node:22.11.0-alpine3.20
    restart: unless-stopped
    user: node
    read_only: true
    tmpfs:
      - /app:uid=1000,gid=1000,mode=0700
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    expose: ["9099"]
    command: ["sh", "-c", "printf %s \\"$$KA_TOKEN_B64\\" | base64 -d > /app/token.mjs && printf %s \\"$$KA_VERIFY_B64\\" | base64 -d > /app/verify.mjs && unset KA_TOKEN_B64 KA_VERIFY_B64 && exec node /app/verify.mjs"]
    environment:
      - NODE_ENV=production
      - KAMERA_TOKEN_SECRET=${{KAMERA_TOKEN_SECRET:?KAMERA_TOKEN_SECRET fehlt (gleicher Wert wie das Supabase-Secret)}}
      - KAMERA_AUTH_HOST=0.0.0.0
      - KAMERA_AUTH_PORT=9099
      - KAMERA_AUTH_URI_HEADER=x-forwarded-uri
      - KAMERA_AUTH_METHOD_HEADER=x-forwarded-method
      - KAMERA_AUTH_LOG=${{KAMERA_AUTH_LOG:-1}}
      - KA_TOKEN_B64={token}
      - KA_VERIFY_B64={verify}

  acme:
    image: neilpang/acme.sh:3.1.5
    restart: unless-stopped
    tmpfs:
      - /run/epk:mode=0700
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    command: ["sh", "-c", "printf %s \\"$$ACME_START_B64\\" | base64 -d > /run/epk/start.sh && unset ACME_START_B64 && exec sh /run/epk/start.sh"]
    environment:
      - KAMERA_HOST=${{KAMERA_HOST:?KAMERA_HOST fehlt (kameras.ep-kolar.at)}}
      - ALIAS_ZONE=${{ALIAS_ZONE:?ALIAS_ZONE fehlt (Zone bei deSEC)}}
      - ALIAS_ART=${{ALIAS_ART:-challenge}}
      - ACME_EMAIL=${{ACME_EMAIL:?ACME_EMAIL fehlt (Konto-Adresse fuer Let's Encrypt)}}
      - DEDYN_TOKEN=${{DEDYN_TOKEN:?DEDYN_TOKEN fehlt (deSEC-Token, nur in der .env)}}
      - ACME_START_B64={acme}
    volumes:
      - acme_daten:/acme.sh          # acme.sh-Konto, Schluessel, gespeichertes deSEC-Token - privat
      - kamera_zertifikate:/certs    # Ausgabe: kameras.pem (fullchain) + kameras-key.pem + Marke .erneuert
    healthcheck:
      test: ["CMD", "test", "-s", "/certs/kameras.pem"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15m

  caddy:
    image: caddy:2.8.4-alpine
    restart: unless-stopped
    depends_on:
      kamera-auth:
        condition: service_started
      acme:
        condition: service_healthy
    tmpfs:
      - /cfg:mode=0700
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: ["no-new-privileges:true"]
    ports:
      - "${{QNAP_LAN_IP:?QNAP_LAN_IP fehlt}}:${{GATEWAY_PORT:-8443}}:${{GATEWAY_PORT:-8443}}"
    command: ["sh", "-c", "printf %s \\"$$CADDY_START_B64\\" | base64 -d > /cfg/start.sh && unset CADDY_START_B64 && exec sh /cfg/start.sh"]
    environment:
      - QNAP_LAN_IP=${{QNAP_LAN_IP:?QNAP_LAN_IP fehlt}}
      - KAMERA_HOST=${{KAMERA_HOST:?KAMERA_HOST fehlt (kameras.ep-kolar.at)}}
      - GATEWAY_PORT=${{GATEWAY_PORT:-8443}}
      - CADDYFILE_B64={caddy}
      - CADDY_START_B64={start}
    volumes:
      - kamera_zertifikate:/certs:ro # nur lesend: Zertifikat + Schluessel von acme
      - caddy_daten:/data
      - caddy_konfig:/config
      - ./protokoll:/protokoll       # Zugriffsprotokoll OHNE Tokens

volumes:
  acme_daten: {{}}
  kamera_zertifikate: {{}}
  caddy_daten: {{}}
  caddy_konfig: {{}}
"""


def bauen_public():
    return VORLAGE_PUBLIC.format(
        token=b64(os.path.join(AUTH, "token.mjs")),
        verify=b64(os.path.join(AUTH, "verify.mjs")),
        acme=b64(os.path.join(HIER, "acme_start.sh")),
        caddy=b64(os.path.join(HIER, "Caddyfile.publiccert")),
        start=b64(os.path.join(HIER, "caddy_start.sh")),
    )


if __name__ == "__main__":
    io.open(ZIEL, "w", encoding="utf-8", newline="\n").write(bauen())
    print(ZIEL)
    io.open(ZIEL_PUBLIC, "w", encoding="utf-8", newline="\n").write(bauen_public())
    print(ZIEL_PUBLIC)
