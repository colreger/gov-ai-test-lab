# KI-Testlabor für ein Bürgerportal

Der [aktuelle Abgleich von Ergebnissen und offenen Befunden](docs/current-findings.md)
trennt den erfolgreichen deterministischen Testlauf von den zwei verbleibenden
Enthaltungen im gespeicherten Sprachmodelllauf. Die veröffentlichten Berichte
verwenden dieselben Prüfsummen wie die aktuellen Testfälle und Quellen.

Automatisierte Qualitäts-, Sicherheits- und Datenschutztests für einen deutschsprachigen Assistenten zur Wohnsitzummeldung. Das Labor nutzt drei vollständig fiktive Kommunalprofile. Fragen, Gebühren, Fristen und Unterlagen dienen ausschließlich als Testdaten.

**Reproduzierbarer Befund:** Ein absichtlich fehlerhaftes Testmodell nennt bei fehlender Gebühreninformation 25 Euro. Mit der Guardrail gibt der Assistent in allen sechs betroffenen Fällen eine standardisierte Antwort ohne Gebührenbetrag aus. Alle neun Fälle mit belegter Gebühreninformation liefern weiterhin die erwartete Antwort.

## In zwei Minuten ausprobieren

Voraussetzung ist Python 3.11 oder neuer. Der Standardlauf verwendet die Python-Standardbibliothek und eine deterministische Modell-Fixture.

```bash
python3 -m govqa ask "Birkenau: Was kostet die Ummeldung?"
python3 -m govqa ask "Lindenfeld: Was kostet die Ummeldung?"
python3 -m unittest discover -v
python3 -m govqa evaluate --output results/fixture.json
```

Die CLI zeigt vor der Antwort den KI-Hinweis an. Im JSON-Bericht stehen Einzelergebnisse, Gruppenstatistik, Modellbezeichnung, Laufzeiten und Prüfsummen der Testdaten. Der Evaluator liefert Exitcode 1, wenn mindestens ein Fall mit Guardrail fehlschlägt. GitHub Actions führt Tests und Fixture-Evaluation bei Pushes und Pull Requests aus und stellt den JSON-Bericht als Workflow-Artefakt bereit.

## Wie der Assistent antwortet

1. Die Anwendung wählt anhand des Ortsnamens ein freigegebenes Kommunalprofil aus. Bei keinem oder mehreren Treffern meldet sie fehlende eindeutige Informationen.
2. Bei einer erkannten Gebührenfrage liest die Guardrail das freigegebene Gebührenfeld direkt aus. Fehlt es, gibt sie die Standardantwort aus.
3. Für andere Einzelfragen wählt das Modell eine Themen-ID. Die Anwendung prüft die ID gegen die freigegebenen Felder und einen eventuell bereits erkannten Themenhinweis. Sie rendert die freigegebene Textpassage mit Quellen-ID. Bei erkannten Mehrthemenfragen gibt sie die Standardantwort aus.
4. Das Audit-Log erfasst den Ergebnisstatus und den Guardrail-Modus. Ein Test prüft die Abwesenheit synthetischer Marker aus Anfrage und Modellentwurf.

Die Baseline gibt im Evaluator den Modellentwurf aus. Der geschützte Modus kombiniert Themenprüfung und Ausgabe freigegebener Fakten. Der Vergleich misst diese Systemänderung als Ganzes. Der separate Gebühren-Regressionstest prüft gezielt die Wirkung der Gebührenregel.

## Lokales Sprachmodell evaluieren

Wenn ein deutschsprachig geeignetes Modell bereits in Ollama installiert ist und Ollama auf `127.0.0.1:11434` läuft, ersetze `MODELLNAME` durch seinen Namen aus `ollama list`.

```bash
python3 -m govqa --model MODELLNAME ask "Lindenfeld: Welche Unterlagen brauche ich?"
python3 -m govqa --model MODELLNAME evaluate --runs 3 --output results/ollama.json
```

Drei Wiederholungen sind ein Ausgangspunkt, um Schwankungen zu sehen. Die Laufzeiten enthalten auch Modellstart und lokale HTTP-Kommunikation. Der Evaluator erwartet exakte Referenztexte. Freie, fachlich gleichwertige Formulierungen der Baseline können deshalb als Abweichung erscheinen. Beurteile solche Antworten anhand der protokollierten Einzelergebnisse. Der Ollama-Adapter ist mit einem simulierten HTTP-Endpunkt getestet. Messwerte eines echten Modells entstehen erst beim lokalen Ollama-Lauf. [Ollama Generate API](https://docs.ollama.com/api/generate)

## Testnachweise

| Gruppe | Baseline | Mit Guardrail |
| --- | ---: | ---: |
| Unterlagen | 10/10 | 10/10 |
| Fristen | 10/10 | 10/10 |
| Termine | 9/9 | 9/9 |
| Belegte Gebühren | 9/9 | 9/9 |
| Fehlende Gebühren | 0/6 | 6/6 |
| Unklare und fachfremde Fragen | 3/6 | 6/6 |
| **Gesamt** | **41/50** | **50/50** |

Die Tabelle zeigt den lokalen Fixture-Lauf. Die Fallbibliothek enthält Standardfragen, einfache Sprache, Tippfehler, mehrdeutige Anfragen und direkte Manipulationsversuche. Separate Tests injizieren einen unerwünschten Modellentwurf, prüfen den KI-Hinweis und kontrollieren das Audit-Log.

- [Teststrategie und Befund](docs/teststrategie.md)
- [Datenschutz und KI-Transparenz](docs/kontrollen.md)
- [Versionierte Testfälle](data/cases.json)
- [Automatisierte QA](.github/workflows/qa.yml)

## Modelle und Schutzmodi vergleichen

```sh
python3 -m govqa evaluate --runs 3 --output results/arena-fixture.json
python3 -m govqa --model MODELL_A evaluate --compare-model MODELL_B --runs 3 --output results/arena-models.json
```

Beide Modi laufen gegen dieselben versionierten Szenarien. Der Bericht enthält
jeweils Text-, Quellen- und Themenprüfung, die genaue Übereinstimmung mit dem
freigegebenen Quellenfeld, Median und p95 der Antwortzeit sowie zusätzliche
Beträge in Gebührenantworten. Der Betragscheck erkennt Ziffernbeträge mit
Währungsangabe und vergleicht sie mit der Referenz. Er erfasst damit einen
eng begrenzten Typ unbelegter Ausgabe. Die genaue Textübereinstimmung kann
fachlich gleichwertige Paraphrasen als Abweichung zählen.

Für Ollama weist der Bericht verfügbare Eingabe- und Ausgabetoken sowie
gemeldete Modelldauer aus. Kosten in Euro benötigen zusätzlich einen
dokumentierten Tarif oder gemessenen Ressourcenverbrauch. Der mitgelieferte
Arena-Bericht stammt aus drei deterministischen Fixture-Läufen.

### NVIDIA-Promptvergleich

Mit einem bereits gesetzten `NVIDIA_API_KEY` kann das Labor die Prompts
`direct` und `grounded` für dasselbe NVIDIA-Modell vergleichen:

```sh
python3 -m govqa evaluate --nvidia-model nvidia/nemotron-3.5-lightning-30b-a3b --output results/arena-nvidia.json
```

Der Aufruf sendet die fiktiven Testfragen und die jeweiligen kommunalen
Fakten an NVIDIA. Pro Prompt wird sowohl die rohe Modellausgabe als auch
die Ausgabe mit Schutzregeln bewertet. Transport- und Formatfehler werden
pro Fall ausgewiesen und zählen nicht als bestandene Prüfungen. Tokenzahlen
stammen aus der Antwort des Anbieters. Eurobeträge für Modellkosten werden
erst mit einem belegten Tarif berechnet.

Für eine kompakte Vergleichsausgabe verwende:

```sh
python3 -m govqa.report results/arena-fixture.json
```

Bei Berichten mit Modell-Telemetrie kannst du mit `--input-eur-per-million`
und `--output-eur-per-million` dokumentierte Tarife angeben. Die Schätzung
bezieht sich auf die gemeldeten Token. Bei fehlender Telemetrie oder
fehlgeschlagenen Anfragen bleibt das Kostenfeld leer.

Der Vergleich zeigt die Bestehensquote für alle Fälle und separat für die
technisch verarbeiteten Fälle. Die zweite Quote kann bei vielen Format- oder
Transportfehlern auf einer kleinen, unterschiedlich zusammengesetzten Auswahl
beruhen. Prüfe deshalb auch `processed` und `errors_by_type`, bevor du zwei
Promptvarianten anhand ihrer fachlichen Ergebnisse vergleichst.

Der erste strukturierte Live-Lauf beseitigte die JSON-Formatfehler, enthielt
aber 84 HTTP-429-Antworten und einen Verbindungsfehler. Eine fachliche
Rangfolge der Prompts lässt sich daraus nicht ableiten. Für weitere Läufe
liegen mindestens vier Sekunden zwischen NVIDIA-Aufrufen innerhalb einer
Variante. Bei HTTP 429 berücksichtigt der Adapter einen numerischen
`Retry-After`-Wert bis 60 Sekunden und versucht den Aufruf höchstens zweimal
erneut. Die gemessene Antwortzeit enthält auch diese Wartezeit.

Mit `python3 -m govqa.report results/arena-nvidia-structured.json --paired`
siehst du zusätzlich, welche identischen Fall- und Wiederholungspaare beide
Varianten verarbeiten konnten und in welche Richtung sie sich unterscheiden.
Bei vielen technischen Ausfällen ist auch dieser Teilvergleich nur für die
gemeinsam verarbeitete Teilmenge aussagekräftig.

Der gedrosselte Live-Lauf verarbeitete alle 50 Fälle pro Prompt und Modus
ohne Transport- oder Formatfehler. Im direkten Prompt bestanden 28/50
Fälle ohne und 43/50 mit Schutzregeln. Mit Quellenbindung bestanden
38/50 beziehungsweise 48/50. Bei den zwei verbleibenden Fehlern im
geschützten, quellengebundenen Modus enthielt sich der Assistent trotz
vorhandener Unterlagen-Information. In keinem der vier Modellarme
markierte der Betragscheck eine unbelegte Gebührenausgabe. Das ist ein
einzelner Lauf auf fiktiven Referenzfällen. Die p95-Werte umfassen auch
die zugunsten des Anbieterlimits eingelegte Wartezeit.

- [Vollständiger Bericht](evidence/arena-nvidia-paced.json)
- [Kompakter gepaarter Vergleich](evidence/arena-nvidia-paced-comparison.json)

## Vorbereitete AWS-Demo

Eine lokale interaktive Demo mit Bree, Hobbiton und Rivendell sowie ein
getestetes Lambda-Upload-Paket liegen unter [demo/README.md](demo/README.md).
Sie verwendet ein vorprogrammiertes Testmodell und ist noch nicht in AWS bereitgestellt.
