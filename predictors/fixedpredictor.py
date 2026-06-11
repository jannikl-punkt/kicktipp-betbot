import json
import os
from helper.match import Match
from .base import PredictorBase
from .calculationpredictor import CalculationPredictor


class FixedPredictor(PredictorBase):
    """Reads predictions from predictions.json, falls back to CalculationPredictor."""

    PREDICTIONS_FILE = "predictions.json"

    def __init__(self):
        self._predictions = {}
        self._fallback = CalculationPredictor()
        if os.path.exists(self.PREDICTIONS_FILE):
            with open(self.PREDICTIONS_FILE, encoding="utf-8") as f:
                self._predictions = json.load(f)

    def predict(self, match: Match):
        key = f"{match.hometeam} - {match.roadteam}"
        if key in self._predictions:
            goals = self._predictions[key]
            return (int(goals[0]), int(goals[1]))
        print(f"  [FixedPredictor] '{key}' nicht in predictions.json, nutze CalculationPredictor")
        return self._fallback.predict(match)
