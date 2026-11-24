# KI-Testlabor: vorbereitete AWS-Demo

Stand: 24. November 2026. Lokal getestet, noch nicht in AWS bereitgestellt.

## Was du ausprobieren kannst

Die Demo stellt einen fiktiven Bürgerassistenten für **Bree, Hobbiton und
Rivendell** dar. Diese Ortsnamen stammen aus der englischen Ausgabe von
*The Lord of the Rings*. Sämtliche Verwaltungsangaben sind erfunden;
das Projekt steht in keiner Verbindung zu den Rechteinhabern.
Die Oberfläche und Fragen bleiben auf Deutsch.

Du wählst einen vorbereiteten Fall. Die Anwendung zeigt die Antwort, die
Quellenkennung und den Grund für die Freigabe oder Ablehnung. Das Testmodell
ist deterministisch: Es verwendet vorprogrammierte Regeln, kein Sprachmodell.
Es werden weder Modellschlüssel noch externe Modellanfragen benötigt.

Die historischen Quellen und Berichte bleiben unverändert. Erst beim Laden
der Demo werden Lindenfeld → Bree, Birkenau → Hobbiton und Auenbrück → Rivendell
umbenannt. Der absichtlich unbekannte Ort Neustadt wird zu Minas Tirith. Die 50 ursprünglichen Erwartungen werden ebenso umbenannt und gegen
das tatsächlich erzeugte Upload-Paket geprüft.

## Lokal ansehen

Im Repository-Verzeichnis:

```bash
python3 demo/serve.py
```

Öffne anschließend http://127.0.0.1:8082. Der lokale Vorschauprozess bildet
AWS-Anfrageereignisse nach. Er ist ein Entwicklungsserver für deinen Rechner.

## Was später zu AWS kommt

**AWS** bedeutet Amazon Web Services. **Lambda** führt hier deinen Python-Code
bei einer Anfrage aus. Ein **Handler** ist die Funktion, die die Anfrage annimmt;
sie heißt in unserem Paket `handler.lambda_handler`.

```text
Ausgewählter Testfall → Python-Handler → Schutzprüfung → Antwort + Quellenkennung
```

Das ZIP enthält nur ausdrücklich ausgewählte Dateien: Handler, drei kleine
Python-Module, zwei fiktive Datendateien und drei Oberflächendateien. Es enthält
keine Zugangsdaten, Modellgewichte oder gespeicherten Modellberichte.

Neu erzeugen:

```bash
python3 demo/build.py
```

Ergebnis: `demo/build/govqa-demo.zip`. Das Archiv ist absichtlich nicht in Git
versioniert; die Bauanleitung und Quelldateien sind versioniert.

## Erster Cloud-Schritt: privat testen

1. In **AWS Settings → View all projects → Overview → Additional Info → Region**
   die zugewiesene Region bestätigen. Die lokale Konfiguration des Profils
   `portfolio` nennt `eu-north-1`; sie wurde noch nicht in AWS bestätigt.
2. Unter **AWS Settings → Billing** Plan, Guthaben und gegebenenfalls Spend Limit
   prüfen. Ein Spend Limit ist die Ausgabengrenze des Projekts. Die lokale
   Anmeldung war bei der Vorbereitung abgelaufen, deshalb wurde der Plan nicht
   ausgelesen. Für die Vorbereitung wurden keine Ressourcen erstellt.
3. Nach erneuter Anmeldung die AWS Management Console in der bestätigten Region
   öffnen. Dort eine Lambda-Funktion mit einer unterstützten Python-3-Laufzeit
   erstellen und das ZIP hochladen. Die Ausführung benötigt nur die von AWS
   vorgesehene Berechtigung zum Schreiben technischer Logs; keine Zugriffe auf
   Datenbanken, Dateispeicher oder Sprachmodelle. Laufzeitlimit 3 Sekunden und
   Speicher 128 MB sind Startwerte für diesen kleinen Versuch.
4. Unter Runtime settings den Handler `handler.lambda_handler` eintragen.
5. Zunächst ausschließlich über die angemeldete Konsole testen. Eine öffentliche
   Funktionsadresse ist für diesen ersten Schritt nicht erforderlich.
6. Dieses Testereignis eintragen:

```json
{
  "rawPath": "/ask",
  "requestContext": {"http": {"method": "POST"}},
  "body": "{\"case_id\":\"04\"}",
  "isBase64Encoded": false
}
```

Erwartung: Statuscode 200, `mode: deterministic_fixture`, Quelle `bree`,
Thema `documents`, Status `answered`. Fall `08` liefert Quelle `rivendell`.
Ein gültiges Testereignis ist keine Zugriffskontrolle: In AWS ist zunächst nur
angemeldeter Zugriff vorgesehen.

## Danach: mit der Portfolioseite verbinden

Die Oberfläche ist vorbereitet. Vor einer öffentlichen Veröffentlichung werden
Authentifizierung, Begrenzung der Anfragen und der Projektplan geprüft. Es gibt
noch keinen öffentlichen AWS-Endpunkt und keine Verbindung zur Live-Portfolioseite.
Ein Link von der bestehenden Portfolioseite zur Demo genügt als erster Schritt;
die komplette Portfolioseite muss dafür nicht umziehen.

Nach dem ersten Cloud-Test entscheiden wir gemeinsam, ob die Testressourcen
für weitere Übungen bleiben oder gelöscht werden. Kosten entstehen abhängig von
Plan, Guthaben, Nutzung und beteiligten Diensten; das Paket ist keine Zusage eines
dauerhaft kostenlosen Betriebs.

## Tests und Grenzen

```bash
python3 -m unittest discover -s tests -v
```

19 lokale Tests bestanden, darunter ein isolierter Test des tatsächlichen ZIPs:
50 umbenannte Fälle, unerlaubte Eingaben, Methodenauswahl und Oberflächendateien.
Die Demo akzeptiert ausschließlich veröffentlichte Fallkennungen und keine
freien Nutzereingaben. Logs enthalten feste Diagnosecodes statt Frage/Entwurf.

Die zwei offenen historischen Sprachmodellfälle bleiben offen. Ein erfolgreicher
Test mit dem vorprogrammierten Modell ersetzt keinen erneuten Sprachmodelllauf.
Die Browseroberfläche wurde lokal mit einer beantwortbaren Frage geprüft.
Cloud-Erreichbarkeit ist noch nicht geprüft.

Offizielle Schnittstellen: [Lambda Python Handler](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html),
[HTTP-Anfrageformat 2.0](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html).
