# kamera-auth - Token-Pruefer fuer Caddy forward_auth (EP Kolar Kamera-Gateway auf der QNAP, 20.11.2026)
# Build-Kontext = tools/kamera-proxy-auth (siehe docker-compose.yml: context "..", dockerfile "qnap/Dockerfile").
# Kopiert NUR die beiden Pruefer-Dateien (unveraendert aus dem Repo) + package.json. Keine Abhaengigkeiten
# (verify.mjs/token.mjs nutzen nur node:http, node:fs, node:url und Web Crypto) -> kein npm install.
# Node-LTS fest gepinnt; vor Ort ggf. auf den aktuellen 22er-Patch heben (QNAP ARM: Multi-Arch-Image).
FROM node:22.11.0-alpine3.20

WORKDIR /app
COPY --chown=root:root qnap/package.json ./package.json
COPY --chown=root:root token.mjs ./token.mjs
COPY --chown=root:root verify.mjs ./verify.mjs
RUN chmod 0444 /app/package.json /app/token.mjs /app/verify.mjs

# nie als root laufen (Benutzer "node" aus dem offiziellen Image, uid 1000); Dateisystem in compose read_only
USER node
ENV NODE_ENV=production
EXPOSE 9099
CMD ["node", "/app/verify.mjs"]
