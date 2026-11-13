# Datenschutz und KI-Transparenz

Für die Fallstudie gilt ein fiktives Bürgerportal als Einsatzszenario. Das System beantwortet Informationsfragen anhand freigegebener Quellen. Die vorliegenden Dokumente, Fragen und Marker sind synthetisch.

| Bezug | Kontrolle im Labor | Nachweis und Reichweite |
| --- | --- | --- |
| DSGVO Art. 5 Abs. 1 Buchst. c und Art. 25 | Audit-Ereignisse enthalten den Ergebnisstatus und den Guardrail-Modus. | Der Markertest erfasst den Python-Audit-Logger. Infrastruktur- und Modell-Logs liegen außerhalb dieses Tests. |
| AI Act Art. 50 Abs. 1 und 5 | Die CLI macht die KI-Interaktion vor der Ausgabe sichtbar. | Ein Prozess-Test prüft Text und Reihenfolge auf der CLI. Für einen echten Einsatz sind Anbieterrolle, Erkennbarkeit beim ersten Kontakt und die tatsächliche Oberfläche zu beurteilen. |

Die Kontrollen demonstrieren ausgewählte technische Anforderungen. Die Evaluationsdatei enthält Antworten und kann im Baseline-Modus freie Modellentwürfe enthalten. Verwende den Evaluator mit dem synthetischen Datensatz und nutze für manuelle Versuche ebenfalls fiktive Eingaben.

[DSGVO auf EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj) · [Konsolidierter AI Act auf EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689)
