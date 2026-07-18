from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
PROFILE_PATH = PLUGIN_ROOT / "assets" / "profiles" / "entornos-digitales-2026.json"
sys.path.insert(0, str(SCRIPT_DIR))

from process_evidence import (  # noqa: E402
    process_metrics,
    render_before_after,
    validate_process_blueprint,
)


class ProcessEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.blueprint = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_reference_profile_passes_process_validation(self) -> None:
        metrics = validate_process_blueprint(self.blueprint)
        self.assertEqual(metrics["product_weight_percent"], 40)
        self.assertEqual(metrics["process_weight_percent"], 60)

    def test_metrics_capture_individual_feedback_and_ai_evidence(self) -> None:
        metrics = process_metrics(self.blueprint)
        self.assertEqual(metrics["individual_evidence_weight_percent"], 5)
        self.assertTrue(metrics["has_individual_evidence"])
        self.assertTrue(metrics["has_feedback_iteration"])
        self.assertTrue(metrics["has_ai_use_disclosure"])

    def test_rejects_unknown_learning_outcome(self) -> None:
        invalid = copy.deepcopy(self.blueprint)
        invalid["assignments"][0]["ra"].append("RA-UNKNOWN")
        with self.assertRaisesRegex(ValueError, "resultados de aprendizaje desconocidos"):
            validate_process_blueprint(invalid)

    def test_rejects_missing_self_or_peer_assessment(self) -> None:
        invalid = copy.deepcopy(self.blueprint)
        for assignment in invalid["assignments"]:
            assignment["process_dimensions"] = [
                item
                for item in assignment["process_dimensions"]
                if item not in {"self_assessment", "peer_assessment"}
            ]
        with self.assertRaisesRegex(ValueError, "autoevaluación o coevaluación"):
            validate_process_blueprint(invalid)

    def test_rejects_low_cognitive_demand_quiz(self) -> None:
        invalid = copy.deepcopy(self.blueprint)
        quiz = next(item for item in invalid["assignments"] if "quiz_settings" in item)
        for question in quiz["quiz_settings"]["questions"]:
            question["type"] = "multiple_choice"
        with self.assertRaisesRegex(ValueError, "demanda cognitiva baja"):
            validate_process_blueprint(invalid)

    def test_rejects_feedback_without_named_actor(self) -> None:
        invalid = copy.deepcopy(self.blueprint)
        target = next(
            item
            for item in invalid["assignments"]
            if item["feedback_loop"]["receives_feedback"]
        )
        target["feedback_loop"].pop("actor")
        with self.assertRaisesRegex(ValueError, "actor del feedback"):
            validate_process_blueprint(invalid)

    def test_rejects_unknown_udd_knowledge_reference(self) -> None:
        invalid = copy.deepcopy(self.blueprint)
        invalid["assignments"][0]["knowledge_base_refs"] = ["UDD-R99"]
        with self.assertRaisesRegex(ValueError, "referencias desconocidas"):
            validate_process_blueprint(invalid)

    def test_before_after_report_exposes_the_paradigm_shift(self) -> None:
        report = render_before_after(self.blueprint)
        self.assertIn("| Final product | 95% | 40.0% |", report)
        self.assertIn("| Process evidence | 0% | 60.0% |", report)
        self.assertIn("GPT-5.6 proposed the diagnosis", report)


if __name__ == "__main__":
    unittest.main()
