# Kicktipp-Betbot

Automatisches Tipp-System für kicktipp.de via GitHub Actions.
Der Bot gibt Tipps auf Basis von KI-Recherche (aktuelle Form, Verletzungen, Head-to-Head).

## Projektstruktur

```
kicktippbb.py          – Haupt-CLI (Login, Parsing, Deadline-Fenster, Tippen)
betbot_report.py       – Rendert predictions.json zu einem Markdown-Bericht
predictors/
  fixedpredictor.py   – Liest predictions.json (Haupt-Predictor für Actions)
  calculationpredictor.py – Fallback auf Basis von Quoten
predictions.json       – Tipps (Laufzeit-Artefakt, nicht eingecheckt)
.github/workflows/
  betbot-auto.yml      – Auto-Tipps ~2h vor Anstoß (Heartbeat)
  betbot-fallback.yml  – Fallback ~30 Min vor Anstoß (Heartbeat)
  betbot-interactive.yml – @claude-Kommentare im Issue
```

## Architektur der geplanten Läufe (wichtig)

Auto- und Fallback-Workflow folgen demselben **Heartbeat-Muster**. Ein günstiger
Cron-Tick prüft per **reinem Python**, ob ein Spiel ins Zeitfenster rutscht – und
startet Claude **nur dann**. Claude macht **ausschließlich die Recherche**; alles
Deterministische ist gescriptet:

1. **Gate** (Bash/Python, kein Claude): `kicktippbb.py --dry-run --deadline <X>` →
   sucht `- betting`-Zeilen = tippbare, noch ungetippte Spiele im Fenster.
   Kein Treffer → Lauf endet, **null Abo-Verbrauch**.
2. **Recherche** (Claude/Abo, nur bei Treffer): schreibt **nur** `predictions.json`
   (kein Tippen, kein Posten). Auftrag kommt aus dem Workflow-`prompt`.
3. **Tippen** (reines Python): `kicktippbb.py --predictor FixedPredictor --deadline <X>`.
4. **Report** (Bash/`gh`): `betbot_report.py` → Kommentar im `betbot-report`-Issue.

Deshalb ist Claude in den geplanten Läufen **kein** Orchestrator mehr – nur ein
Recherche-Dienst. Diese CLAUDE.md steuert primär die **interaktiven** `@claude`-Läufe.

## Wichtige Befehle

```bash
# Alle Spiele + Communities anzeigen (nichts tippen)
python kicktippbb.py --dry-run --use-login-token "$KICKTIPP_TOKEN"

# Spiele für bestimmte Communities anzeigen
python kicktippbb.py --dry-run --use-login-token "$KICKTIPP_TOKEN" acmilfhunters172 svawm

# Tipps abgeben mit FixedPredictor
python kicktippbb.py --use-login-token "$KICKTIPP_TOKEN" --predictor FixedPredictor [community ...]

# Fallback: nur Spiele die in 1h beginnen (kein Override – nur wo noch kein Tipp)
python kicktippbb.py --use-login-token "$KICKTIPP_TOKEN" --predictor FixedPredictor --deadline 1h [community ...]

# Verfügbare Predictors
python kicktippbb.py --list-predictors
```

## Communities

- **Fallback** (Jannik tippt selbst, Bot nur als Backup falls vergessen):
  `acmilfhunters172`, `svawm`
- **Auto** (Bot tippt vollständig, Jannik tippt hier nicht):
  Alle anderen Gruppen im Account – dynamisch per Dry-Run ermitteln

## predictions.json Format

Zwei Wertformate pro Spiel sind erlaubt (beide werden vom FixedPredictor gelesen):

```json
{
  "Deutschland - Frankreich": [2, 1],
  "Katar - Schweiz": {"tip": [0, 2], "reason": "Schweiz klar überlegen"}
}
```

Das `reason`-Feld ist optional und wird nur vom Report genutzt. In den geplanten
Läufen schreibt Claude bevorzugt das `{"tip": ..., "reason": ...}`-Format, damit der
Bericht eine Begründung zeigen kann.

**Wichtig**: Teamnamen exakt so verwenden wie sie im Dry-Run-Output erscheinen.

## Tipp-Formate

Es gibt zwei Community-Typen, die der Bot automatisch erkennt:

**Ergebnis-Tipp** (Standard): Zwei Felder (`heimTipp` + `gastTipp`), z. B. `2:1`.
`predictions.json`-Eintrag: `"Deutschland - Frankreich": [2, 1]`

**Tendenz-Tipp (1X2)**: Nur ein Feld (`heimTipp`), erlaubte Werte: `1` (Heimsieg), `X` (Unentschieden), `2` (Auswärtssieg).
Beispiel: `oddset-wm-tipp`. Das Skript leitet die Tendenz automatisch aus dem vorhergesagten Ergebnis ab:
- `[2, 1]` → `1`, `[1, 1]` → `X`, `[0, 2]` → `2`
`predictions.json`-Eintrag bleibt identisch: `"USA - Paraguay": [2, 0]` (→ wird zu `1` umgerechnet).

---

## GitHub Actions: Auto-Tipps (`betbot-auto.yml`)

Heartbeat alle 30 Min. Tippt jedes Auto-Community-Spiel **~2h vor Anstoß** mit
frischer Recherche (Aufstellungen/News sind dann aktueller als morgens).

- **Gate** (Python): `kicktippbb.py --dry-run --deadline 2h` über alle Communities;
  per `awk` werden die Fallback-Gruppen (`acmilfhunters172`, `svawm`) ausgeschlossen
  und die betroffenen Auto-Communities gesammelt. Kein Treffer → Ende.
- **Recherche** (Claude/Abo, nur bei Treffer): laut Workflow-`prompt` nur
  `predictions.json` schreiben – kein Tippen, kein Posten.
- **Tippen** (Python): `kicktippbb.py --predictor FixedPredictor --deadline 2h <auto-communities>`.
- **Report** (`betbot_report.py` + `gh`): Kommentar im `betbot-report`-Issue.

## GitHub Actions: Fallback (`betbot-fallback.yml`)

Heartbeat alle 15 Min, nur `acmilfhunters172` und `svawm`. Springt **~30 Min vor
Anstoß** ein (Fenster 40m als Jitter-Puffer) und tippt **nur**, wo Jannik noch
keinen Tipp gesetzt hat (**kein** `--override-bets`).

Gleicher 4-Schritt-Ablauf wie oben, aber Deadline `40m` und feste Community-Liste.

---

## Interaktive Anpassungen (@claude Kommentare)

Wenn jemand `@claude` in einem Issue kommentiert:

- **Tipp ändern**: predictions.json anpassen und Bot neu ausführen
  - Beispiel: `@claude ändere Deutschland - Frankreich auf 3:1`
  - Beispiel: `@claude tippe acmilfhunters172 komplett neu`
- **Info**: Fragen beantworten
  - Beispiel: `@claude welche Spiele tippt der Bot heute?`
- Nach jeder Aktion: kurze Bestätigung als Kommentar posten.

### Bei Tipp-Änderung
1. Gewünschte Änderung in predictions.json übernehmen
2. Bot ausführen (mit `--override-bets` falls nötig):
   ```bash
   python kicktippbb.py --use-login-token "$KICKTIPP_TOKEN" --predictor FixedPredictor --override-bets [community]
   ```
3. Ergebnis bestätigen.
