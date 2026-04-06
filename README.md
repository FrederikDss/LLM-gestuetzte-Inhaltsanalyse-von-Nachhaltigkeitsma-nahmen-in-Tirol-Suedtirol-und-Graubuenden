# LLM-gestuetzte-Inhaltsanalyse-von-Nachhaltigkeitsmassnahmen-in-Tirol-Suedtirol-und-Graubuenden
Dokumentation der LLM-gestützten Inhaltsanalyse von Nachhaltigkeitsmaßnahmen in Tirol, Südtirol und Graubünden.

Dieses Repository enthält die methodischen Grundlagen zur Masterarbeit:

**[Titel Arbeit]**  
Frederik Düss, Leopold-Franzens-Universität Innsbruck, Institut für Geographie, 2026
## Inhalt

| Datei | Beschreibung |
|---|---|
| `prompt.txt` | Extraktionsprompt zur Extraktion der Maßnahmen mit einem beliebigen LLM |
| `skript.py` | Python-Skript für die LLM-gestützte Klassifikation der extrahierten Maßnahmen |
| `kategoriensystem.xlsx` | Vollständiges Kategoriensystem mit allen Variablen und Ausprägungen zur Klassifikation der Maßnahmen|

## Methodik

Die Analyse wird in drei Schritten durchgeführt:
1. Extraktion von Maßnahmen aus Planungsdokumenten mittels | `prompt.txt` |
2. Klassifikation der extrahierten Maßnahmen anhand des Kategoriensystems
3. Manuelle Bereinigung und Qualitätsprüfung des Datensatzes

Eine vollständige Beschreibung der Methodik sowie der Bereinigungsschritte 
findet sich in Kapitel 4 der Arbeit.

## Planungsdokumente & Hinweis

Die Methodik ist auf deutschsprachige Planungsdokumente der öffentlichen Verwaltung anwendbar, insbesondere auf Maßnahmenprogramme & Strategiedokumente die operative Maßnahmen enthalten.

Die analysierten Planungsdokumente sind öffentlich zugänglich und werden hier nicht reproduziert.



## Kontakt

frederik.duess@uibk.ac.at
