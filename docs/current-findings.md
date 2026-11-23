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

### Diagnose und strengere Formatprüfung umgesetzt

Die lokale Ablaufprüfung findet für beide Fragen die richtige Ortsquelle und
`documents` als einziges erkanntes Thema. Bei einer Modellantwort mit diesem
Thema wird der freigegebene Quellentext ausgegeben. Jede andere Themenentscheidung
führt an der Schutzprüfung zur Enthaltung. Im archivierten ungeschützten
Lindenfeld-Lauf steht tatsächlich der ganze Antwortsatz im Themenfeld; dies ist
ein belegter Formatverstoß in diesem separaten Lauf, kein Nachweis des genauen
Werts im geschützten Lauf.

Die Adapter für NVIDIA und Ollama akzeptieren jetzt ausschließlich die zwei
Textfelder `topic` und `draft` sowie einen vorhandenen Quellenschlüssel oder
`unknown` als Thema. Zusätzliche Felder und freie Sätze als Thema werden als
Formatfehler abgewiesen. Es erfolgt keine automatische Umdeutung der Antwort.

Routing bedeutet hier die Zuordnung einer Frage zu einer Themenkategorie.
Das Audit-Log und neue Evaluationsberichte speichern dafür feste Ursachencodes:
`model_contract_rejected`, `topic_not_in_context`, `topic_mismatch` oder
`approved_source`. Frage, Antwortentwurf und beliebige Modellstrings werden
nicht protokolliert. Die Schutzregeln bleiben bestehen.

18 lokale Tests bestehen, einschließlich beider Fälle mit kontrollierten
Modellantworten und der Adapterprüfung; die deterministische Auswertung bleibt
bei 50/50 geschützten Fällen. Ein erneuter externer Modelllauf wurde nicht
vorgenommen. Die zwei historischen Modellfehler bleiben bis zu einer erneuten
kontrollierten Messung offen. Bei einer Wiederholung enthält jeder Fall nun
`routing_diagnostic` zur Eingrenzung der Fehlerstelle.

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
