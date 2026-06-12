# Kicktipp-Betbot

Automatisches Tipp-System für kicktipp.de via GitHub Actions.
Der Bot gibt Tipps auf Basis von KI-Recherche (aktuelle Form, Verletzungen, Head-to-Head).

## Projektstruktur

```
kicktippbb.py          – Haupt-CLI
predictors/
  fixedpredictor.py   – Liest predictions.json (Haupt-Predictor für Actions)
  calculationpredictor.py – Fallback auf Basis von Quoten
predictions.json       – Tipps: {"Heimteam - Gastteam": [heim_tore, gast_tore]}
```

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

```json
{
  "Deutschland - Frankreich": [2, 1],
  "Bayern München - Borussia Dortmund": [3, 1],
  "Brasilien - Argentinien": [1, 2]
}
```

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

## GitHub Actions: Tägliche Auto-Tipps

Läuft täglich um 08:00 CEST. Tippt alle Auto-Communities vollständig.

### Ablauf

1. **Dry-Run aller Communities** (keine Community-Angabe = alle):
   ```bash
   python kicktippbb.py --dry-run --use-login-token "$KICKTIPP_TOKEN"
   ```

2. **Fallback-Communities herausfiltern**: `acmilfhunters172`, `svawm` aus der Liste entfernen.
   Falls keine Auto-Communities übrig bleiben: direkt zu Schritt 6 (nur Bericht).

3. **Pro anstehendem Spiel** (nur Spiele von heute und morgen):
   - Kurze Web-Recherche: aktuelle Form beider Teams, Verletzungen, Head-to-Head
   - Kontext: WM 2026, Gruppenphase oder K.o.-Runde beachten

4. **predictions.json schreiben** mit den recherchierten Tipps.
   Begründung pro Spiel notieren (für Bericht).

5. **Tipps abgeben**:
   ```bash
   python kicktippbb.py --use-login-token "$KICKTIPP_TOKEN" --predictor FixedPredictor <auto-communities...>
   ```

6. **Tagesbericht** als Kommentar im GitHub Issue mit Label `betbot-report` posten.
   Falls kein solches Issue existiert: neues Issue erstellen mit Titel
   "🤖 Betbot Tagesberichte" und Label `betbot-report`.
   ```bash
   gh issue list --label betbot-report --json number --jq '.[0].number'
   gh issue create --title "🤖 Betbot Tagesberichte" --label betbot-report --body "Tägliche Tipp-Berichte des Betbots."
   gh issue comment <nummer> --body "<bericht>"
   ```

### Bericht-Format

```markdown
## 🏆 Betbot Tagesbericht – TT.MM.YYYY

### Getippte Spiele (Auto-Communities)
| Spiel | Tipp | Kurzbegründung |
|-------|------|----------------|
| Deutschland vs Frankreich | 2:1 | DE starke Heimform; FR ohne Mbappé |

### Communities
Auto: [liste oder "keine – noch nicht konfiguriert"]

### Hinweise
[Fehler, fehlende Quoten, etc. – sonst weglassen]
```

---

## GitHub Actions: Stündlicher Fallback

Läuft stündlich für `acmilfhunters172` und `svawm`.
Tippt **nur** Spiele die innerhalb der nächsten Stunde beginnen **und** noch keinen Tipp haben.

### Ablauf

1. **Dry-Run mit Deadline-Check**:
   ```bash
   python kicktippbb.py --dry-run --use-login-token "$KICKTIPP_TOKEN" --deadline 1h acmilfhunters172 svawm
   ```
   Falls der Output "no bets possible" oder "not betting yet" für alle Spiele zeigt: fertig, keine Aktion.

2. **Pro Spiel in den nächsten 60 Minuten**: schnelle Web-Recherche (Form, Aufstellung).

3. **predictions.json schreiben**.

4. **Tipps abgeben**:
   ```bash
   python kicktippbb.py --use-login-token "$KICKTIPP_TOKEN" --predictor FixedPredictor --deadline 1h acmilfhunters172 svawm
   ```
   (Kein `--override-bets` – bereits gesetzte Tipps von Jannik bleiben erhalten!)

5. Falls Tipps gesetzt wurden: kurzen Kommentar im betbot-report Issue posten.

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
