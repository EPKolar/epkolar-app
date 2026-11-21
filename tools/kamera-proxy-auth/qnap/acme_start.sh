#!/bin/sh
# EP Kolar Kamera-Gateway - Start des acme-Containers (acme.sh, Let's Encrypt per DNS-01 im DNS-ALIAS-MODUS ueber deSEC).
# Eingebettet in qnap-gateway-publiccert-inline.compose.yml (Blob ACME_START_B64, Riegel tests/test_kamera_publiccert.py).
#
# Ablauf: Konto registrieren (idempotent) -> ausstellen (Rueckgabe 2 = noch gueltig, kein Fehler) -> --install-cert in das
# gemeinsame Volume /certs -> taeglich "acme.sh --cron" (erneuert faellige Zertifikate und kopiert sie erneut).
# --reloadcmd schreibt NUR die Pruefsumme des Zertifikats nach /certs/.erneuert; caddy_start.sh im caddy-Container sieht die
# geaenderte Marke und startet Caddy neu. Kein Docker-Socket, kein Zugriff auf andere Container.
#
# Alias-Modus (acme.sh-Wiki "DNS alias mode"):
#   ALIAS_ART=challenge (Standard): CNAME _acme-challenge.<KAMERA_HOST> -> _acme-challenge.<ALIAS_ZONE>   (--challenge-alias)
#   ALIAS_ART=domain:               CNAME _acme-challenge.<KAMERA_HOST> -> <ALIAS_ZONE> (ohne Praefix)    (--domain-alias)
# dns_desec liest DEDYN_TOKEN aus der Umgebung (acme.sh speichert es danach in /acme.sh - Volume acme_daten, privat).
set -eu

: "${KAMERA_HOST:?KAMERA_HOST fehlt}"
: "${ALIAS_ZONE:?ALIAS_ZONE fehlt}"
: "${ACME_EMAIL:?ACME_EMAIL fehlt}"
: "${DEDYN_TOKEN:?DEDYN_TOKEN fehlt}"

case "${ALIAS_ART:-challenge}" in
  challenge) ALIAS_OPT="--challenge-alias" ;;
  domain) ALIAS_OPT="--domain-alias" ;;
  *) echo "ALIAS_ART muss challenge oder domain sein" >&2; exit 64 ;;
esac

acme.sh --set-default-ca --server letsencrypt
acme.sh --register-account --server letsencrypt -m "$ACME_EMAIL" || true

rc=0
acme.sh --issue --server letsencrypt --dns dns_desec -d "$KAMERA_HOST" "$ALIAS_OPT" "$ALIAS_ZONE" --keylength ec-256 || rc=$?
if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
  echo "Ausstellen fehlgeschlagen (Rueckgabe $rc) - CNAME/Token/ALIAS_ZONE pruefen, Neuversuch in 1 h" >&2
  sleep 3600
  exit "$rc"
fi

acme.sh --install-cert -d "$KAMERA_HOST" --ecc \
  --fullchain-file /certs/kameras.pem \
  --key-file /certs/kameras-key.pem \
  --reloadcmd "sha256sum /certs/kameras.pem > /certs/.erneuert.neu && mv /certs/.erneuert.neu /certs/.erneuert"

while :; do
  sleep 86400
  acme.sh --cron || echo "acme.sh --cron fehlgeschlagen - naechster Versuch in 24 h" >&2
done
