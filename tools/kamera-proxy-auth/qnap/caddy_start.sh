#!/bin/sh
# EP Kolar Kamera-Gateway - Start des caddy-Containers (Variante oeffentliches Zertifikat).
# Eingebettet in qnap-gateway-publiccert-inline.compose.yml (Blob CADDY_START_B64, Riegel tests/test_kamera_publiccert.py).
#
# Caddy liest Datei-Zertifikate (tls <cert> <key>) nur beim Start; "caddy reload --force" erneuert den Zertifikat-Zwischen-
# speicher nicht (caddyserver/caddy#6789, offen #6933). Darum: Caddy als Kindprozess starten, jede Minute die Marke
# /certs/.erneuert lesen (schreibt acme.sh per --reloadcmd NUR nach einer echten Erneuerung, Inhalt = Pruefsumme des
# Zertifikats). Inhalt geaendert -> Caddy sauber beenden, Skript endet -> "restart: unless-stopped" startet den Container
# frisch mit dem neuen Zertifikat (Unterbrechung ~2 s, etwa alle 60 Tage). admin bleibt aus, kein Docker-Socket.
set -u

printf %s "$CADDYFILE_B64" | base64 -d > /cfg/Caddyfile
unset CADDYFILE_B64

marke() { cat /certs/.erneuert 2>/dev/null || echo "-"; }

ALT="$(marke)"
caddy run --config /cfg/Caddyfile --adapter caddyfile &
PID=$!
trap 'kill -TERM "$PID" 2>/dev/null; wait "$PID"; exit 0' TERM INT

while kill -0 "$PID" 2>/dev/null; do
  sleep 60 &
  wait $!
  if [ "$(marke)" != "$ALT" ]; then
    echo "Zertifikat erneuert - Caddy startet neu"
    kill -TERM "$PID" 2>/dev/null
    wait "$PID"
    exit 0
  fi
done
wait "$PID"
exit $?
