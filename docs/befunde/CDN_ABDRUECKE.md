# Fremde Dateien und ihre Abdrücke — gemessen am 29.09.2026

Die App lädt acht Dateien von `cdnjs.cloudflare.com` (`index.html:42–50`) und
eine neunte zur Laufzeit (`index.html:4304`). Bis v3.9.985 trug **keine** davon
ein `integrity`-Attribut. `crossorigin` stand an jeder — das ist die Hälfte des
Schutzes und allein wirkungslos: es *erlaubt* dem Browser die Prüfung, es
*führt sie nicht durch*.

Die CSP erlaubt cdnjs ausdrücklich (`script-src … https://cdnjs.cloudflare.com`).
Sie schützt also gegen eine *andere Herkunft*, nicht gegen eine *veränderte
Datei von derselben Herkunft*. Darunter ist `bcrypt.min.js` — die Bibliothek,
die Kennwörter verhasht.

## Wie die Abdrücke geprüft wurden

🔴 **Die Abdrücke stammen zuerst von einem fremden Server und wurden deshalb
nicht geglaubt, sondern nachgerechnet.** Die cdnjs-API ist selbst cdnjs; sie
als Quelle für die Prüfsumme von cdnjs-Dateien zu nehmen wäre ein Zirkel.

1. Abdruck von `api.cdnjs.com/libraries/<lib>/<ver>?fields=sri` geholt.
2. Dieselbe Datei von `cdnjs.cloudflare.com` abgerufen und ihr sha512 selbst
   gebildet.
3. Verglichen. **Acht von acht stimmten überein.**

Wer einen Abdruck ändert oder ergänzt, macht dasselbe:

```
curl -s <adresse> | python -c "import sys,hashlib,base64;print('sha512-'+base64.b64encode(hashlib.sha512(sys.stdin.buffer.read()).digest()).decode())"
```

## Warum ein falscher Abdruck schlimmer ist als keiner

Stimmt der Abdruck nicht, **weigert sich der Browser, die Datei auszuführen**.
Bei `react.production.min.js` heißt das: die App bleibt weiß, ohne Meldung auf
dem Schirm. Die Form, in der das passiert, ist nicht Böswilligkeit, sondern
Routine — jemand hebt Leaflet von 1.9.4 auf 1.9.5 und lässt den Abdruck stehen.

Deshalb misst `tests/test_cdn_integrity_v986.py` nicht die *Anwesenheit* des
Attributs, sondern das **Paar aus Adresse und Abdruck** gegen eine
festgeschriebene Tafel. Wer die Version hebt, wird rot und muss den Abdruck
mitheben.

## Die acht abgesicherten Dateien

| Datei | Abdruck (sha512, gekürzt) |
|---|---|
| `react/18.2.0/umd/react.production.min.js` | `8Q6Y9XnTbOE+…lrfqrQ==` |
| `react-dom/18.2.0/umd/react-dom.production.min.js` | `MOCpqoRoisC…C1OHWQ==` |
| `bcryptjs/2.4.3/bcrypt.min.js` | `DNI/FJdkfye…xUTU/w==` |
| `pdf.js/3.11.174/pdf.min.js` | `q+4liFwdPC/…Mn+oCQ==` |
| `qrcode-generator/1.4.4/qrcode.min.js` | `ZDSPMa/JM1D…y6P6Sw==` |
| `jspdf/2.5.1/jspdf.umd.min.js` | `qZvrmS2ekKP…HgtNA==` |
| `leaflet/1.9.4/leaflet.min.js` | `puJW3E/qXDq…Ib6p4g==` |
| `leaflet/1.9.4/leaflet.min.css` | `h9FcoyWjHcO…6D3BOw==` |

Die vollständigen Werte stehen in der Tafel des Riegels — dort, wo sie
gemessen werden, nicht in einer zweiten Abschrift, die auseinanderlaufen kann.

## 🔴 Die eine Stelle, die ein Abdruck nicht erreicht

```
index.html:4304
window.pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
```

Das ist kein Tag, sondern eine Adresse, die zur Laufzeit zugewiesen wird. SRI
kennt die Norm **nur für Tags** — hier gibt es kein `integrity`, an das man
etwas schreiben könnte. Das ist keine Nachlässigkeit, sondern eine Grenze des
Mittels, und sie steht hier, statt ausgelassen zu werden.

**Was trotzdem gemessen wird** (`test_der_arbeiter_hat_die_gleiche_fassung…`,
`test_es_gibt_genau_EINE_solche_ausnahme`):

* Der Arbeiter trägt dieselbe pdf.js-Fassung wie das Skript im Kopf. Laufen
  die auseinander, bleibt das PDF beim Nutzer leer — und erst dort.
* Es bleibt bei **genau einer** solchen Ausnahme. Eine zweite macht den Riegel
  rot, statt sich still dazuzulegen.

**Was zu tun wäre, wenn auch das geschlossen werden soll:** die Datei holen,
selbst hashen, und als Blob-Adresse weitergeben. Die CSP erlaubt das bereits
(`worker-src 'self' blob:`). Es ist eine Verhaltensänderung am PDF-Laden und
braucht eine eigene Messung — heute gibt es kein Tor, das PDF-Anzeige
durchspielt. **Der sauberere Weg ist ohnehin, die Dateien ins Repo zu legen**,
wie es mit der Schrift Archivo in v3.9.933 schon gemacht wurde; das löst
zusätzlich Offline-Betrieb und fremde Verfügbarkeit. Das ist eine
Entscheidung, keine Messung — sie steht in `docs/ENTSCHEIDUNGEN-OFFEN.md`.

## Was dieser Befund **nicht** belegt

Ob der Browser die Prüfung wirklich durchführt. Das hängt am
`Access-Control-Allow-Origin` von cdnjs und ist im Quelltext nicht sichtbar.
Sichtbar wird es beim Laden der Seite: schlägt ein Abdruck fehl, schreibt die
Konsole es hin, und die App bleibt weiß. Der Einbau wurde deshalb am
Pruefstand geladen und gegengesehen — siehe den Stufen-Commit zu v3.9.986.
