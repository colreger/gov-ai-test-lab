# Aktuelle Testergebnisse und offene Befunde

Abgleich: 23. November 2026. Die gespeicherten Ergebnisse des gedrosselten
Modelllaufs wurden gegen die Prüfsummen der aktuellen Fälle und Quellen sowie
gegen sämtliche Einzelergebnisse geprüft. Es wurde kein neuer externer
Modelllauf ausgeführt.

| Variante | Ohne Schutzregeln | Mit Schutzregeln | Technische Fehler |
| --- | ---: | ---: | ---: |
| Deterministisches Testmodell | 41/50 | 50/50 | 0 |
| Nemotron, direkter Prompt | 28/50 | 43/50 | 0 |
| Nemotron, quellengebundener Prompt | 38/50 | 48/50 | 0 |

Die promptgebundenen Werte stammen aus einem einzelnen gespeicherten Lauf.
Das Testmodell liefert vorprogrammierte Antworten und ist kein Sprachmodell.
Sein 50/50-Ergebnis behebt daher nicht die zwei Fehler im Sprachmodelllauf.

## Offen: zwei unnötige Enthaltungen

- **Fall 04:** „Lindenfeld: Brauche ich einen Ausweis?“
- **Fall 08:** „Auenbrück: Brauche ich einen Reisepass?“

Im geschützten, quellengebundenen Lauf wird jeweils die Standard-Enthaltung
ausgegeben, obwohl der freigegebene Dokumententext vorhanden ist. Diese beiden
Befunde bleiben ausdrücklich offen. Die gespeicherten Endantworten isolieren
nicht die genaue Ursache der Modellentscheidung. Ohne neue Diagnose darf weder
eine bestimmte Ursache noch eine erfolgreiche Korrektur behauptet werden.
Maschinenlesbarer Stand: [open-findings.json](../evidence/open-findings.json).

Nächster Diagnoseschritt ist eine kontrollierte Wiederholung mit geeigneten
Routing-Diagnosen, anschließend eine Regression über den vollständigen Bestand.
Dabei ist die Datenminimierung des regulären Audit-Logs beizubehalten.

## Weitere Grenzen

- Mehrthemenfragen werden derzeit vollständig abgelehnt. Eine belegte Teilantwort
  wäre eine mögliche Erweiterung, ist aber nicht umgesetzt.
- Exakter Textvergleich kann fachlich gleichwertige Formulierungen ablehnen.
- Der Betragscheck erkennt einen begrenzten Typ von Ziffernbeträgen mit Währung;
  null Markierungen sind kein allgemeiner Nachweis, dass alle Aussagen korrekt sind.
- Frühere Läufe mit vielen HTTP-429-Antworten (zu viele Anfragen) eignen sich
  nicht für eine fachliche Rangfolge. Im hier geprüften gedrosselten Lauf sind
  alle 50 Fälle je Prompt und Schutzmodus technisch verarbeitet worden.
- Antwortzeiten dieses Laufs enthalten die absichtliche Drosselungswartezeit.
  Sie sind keine isolierte Modell-Inferenzzeit und kein Kostenvergleich.

## Nachweise

- [Gespeicherter vollständiger Modellvergleich](../evidence/arena-nvidia-paced.json)
- [Rekonstruierbarer gepaarter Vergleich](../evidence/arena-nvidia-paced-comparison.json)
- `tests/test_saved_evidence.py` prüft Datenbezug, Summen und offene Fälle.

Die Befunde betreffen eine fiktive Testumgebung und ausgewählte technische
Schutzregeln. Sie sind keine allgemeine rechtliche Compliance-Zertifizierung.
