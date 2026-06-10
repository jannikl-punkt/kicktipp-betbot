# Kicktipp-Betbot — Setup-Brief für Claude Code

> Diese Datei ins Repo legen (z. B. Wurzelverzeichnis) und in Claude Code als Kontext mitgeben:
> „Lies `CLAUDE_SETUP_BRIEF.md` und arbeite den Plan ab."

## Ziel

Den [kicktipp-betbot](https://github.com/schwalle/kicktipp-betbot) so aufsetzen, dass er für **mehrere Tippspiele (Communities)** Tipps abgibt — bei einem Teil **voll automatisiert**, beim anderen Teil nur als **Fallback**, falls ich vergessen habe selbst zu tippen.

## Wie das Tool funktioniert (Kurzfassung)

- Python-CLI (`kicktippbb.py`), gedacht für Cron / Scheduler.
- Nimmt einen oder mehrere **Community-Namen** als Positionsargument → pro Lauf gezielt bestimmte Runden ansteuerbar.
- **Überschreibt standardmäßig keine** schon abgegebenen Tipps (kein `--override-bets`).
- `--deadline <dauer>` → tippt nur Spiele, die innerhalb des Fensters starten (Format: `30m`, `1h`, `1d`).
- Predictor-Klassen liegen im Ordner `predictors/`; Default ist der erste alphabetisch. Auswahl per `--predictor <Name>`, Liste via `--list-predictors`.
- Login per **accountweitem Token** (ein Token deckt alle Runden ab).

## Architektur: zwei Job-Typen

Kein Code-Umbau nötig — die zwei Modi entstehen rein über Aufruf-Parameter:

**1. Voll automatisiert** (Runden, wo ich nicht selbst tippe)
- Lauf z. B. einmal beim Öffnen des Spieltags oder täglich.
- Nur die betreffenden Community-Namen, **ohne** `--deadline`.
- Setzt einfach die Tipps.

**2. Fallback** (Runden, wo ich selbst tippe)
- Lauf häufiger, mit kurzem `--deadline` (z. B. `1h`).
- Springt durch den No-Override-Default nur dort ein, wo kurz vor Schluss noch nichts gesetzt ist.
- Muss nahe an den Anstoßzeiten oft genug laufen (z. B. Wochenende stündlich).

## Offene Entscheidungen (mit Jannik klären)

| Punkt | Optionen / Notiz | Entscheidung |
|---|---|---|
| Communities + Modus | Liste aller Tipprunden, je „auto" oder „fallback" | _TODO_ |
| Hosting | GitHub Actions (keine HW) / Raspberry Pi / VPS (Hetzner) | _TODO_ |
| Predictor | Default ansehen, ggf. eigener | _TODO_ |
| Schedules | Auto: wann? · Fallback: wie oft? | _TODO_ |

## Vorgehen in Claude Code

1. Repo klonen, venv anlegen, `pip install -r requirements.txt`.
2. Vorhandene Workflow-Datei unter `.github/workflows/` prüfen — evtl. schon brauchbar.
3. Login-Token interaktiv erzeugen: `python kicktippbb.py --get-login-token` (Token sicher ablegen, NICHT committen).
4. Trockenlauf je Runde: `python kicktippbb.py --use-login-token <token> --dry-run <community>` → ansehen, was der Predictor ausspuckt.
5. Predictor festlegen (`--list-predictors`, ggf. eigene Klasse von `PredictorBase` ableiten).
6. Die zwei Jobs als GitHub Action mit zwei Cron-Schedules bauen; Token als Repo-Secret (z. B. `KICKTIPP_TOKEN`).

## Befehls-Referenz

```
python kicktippbb.py --get-login-token
python kicktippbb.py --use-login-token <token> [community ...]
  --dry-run            nur anzeigen, nichts setzen
  --override-bets      vorhandene Tipps überschreiben
  --deadline <dauer>   nur Spiele im Fenster (z. B. 30m, 1h, 1d)
  --predictor <name>   bestimmten Predictor nutzen
  --list-predictors    verfügbare Predictors anzeigen
  --matchday <1-34>    bestimmten Spieltag (nützlich bei Nachholspielen)
```

## Caveats

- **Token läuft irgendwann ab** (ist ein Login-Cookie) → muss dann neu erzeugt werden. Bei Bedarf eine Erinnerung/Healthcheck einbauen.
- **Erst `--dry-run`**, bevor irgendwas „echt" in eine Runde gesetzt wird.
- **GitHub-Actions-Cron ist nur best-effort** und kann unter Last mehrere Minuten verspätet starten. Für den Fallback deshalb das `--deadline`-Fenster nicht zu knapp wählen (eher `1h` als `10m`) und/oder häufiger laufen lassen. Wenn es minutengenau sein muss → Pi/VPS-Cron ist verlässlicher.
- Token & Secrets niemals ins Repo committen; `.gitignore` prüfen.
