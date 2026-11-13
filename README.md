# KI-Testlabor für ein Bürgerportal

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
