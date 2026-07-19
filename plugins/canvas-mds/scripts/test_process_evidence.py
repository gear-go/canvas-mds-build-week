from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
PROFILE_PATH = PLUGIN_ROOT / "assets" / "profiles" / "entornos-digitales-2026.json"
REPO_ROOT = PLUGIN_ROOT.parent.parent
ALIGNMENT_PATH = PLUGIN_ROOT / "assets" / "judge-case" / "reference" / "planning-alignment.json"
sys.path.insert(0, str(SCRIPT_DIR))

from process_evidence import (  # noqa: E402
    process_metrics,
    render_before_after,
    validate_artifact_bundle,
    validate_assignment_alignment,
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
        self.assertEqual(metrics["process_checkpoint_weight_percent"], 55)
        self.assertEqual(metrics["individual_verification_weight_percent"], 5)
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
        self.assertIn(
            "| Process checkpoints (excluding individual verification) | 0% | 55.0% |",
            report,
        )
        self.assertIn("| Individual verification | 5% | 5.0% |", report)
        self.assertIn("| Total non-final evidence | 5% | 60.0% |", report)
        self.assertIn("GPT-5.6 proposed the diagnosis", report)

    def test_assignment_alignment_uses_selected_chain(self) -> None:
        alignment = json.loads(ALIGNMENT_PATH.read_text(encoding="utf-8"))
        assignment = {
            "key": "aligned-assignment",
            "objective_ids": ["OBJ-01"],
            "indicator_ids": ["IND-01"],
            "evidence_ids": ["EV-01"],
            "instrument_id": "INS-01",
            "procedure_moment_id": "MOM-01",
        }
        validate_assignment_alignment([assignment], alignment)

    def test_assignment_alignment_rejects_unselected_instrument(self) -> None:
        alignment = json.loads(ALIGNMENT_PATH.read_text(encoding="utf-8"))
        assignment = {
            "key": "misaligned-assignment",
            "objective_ids": ["OBJ-01"],
            "indicator_ids": ["IND-01"],
            "evidence_ids": ["EV-01"],
            "instrument_id": "INS-03",
            "procedure_moment_id": "MOM-01",
        }
        with self.assertRaisesRegex(ValueError, "instrumento seleccionado"):
            validate_assignment_alignment([assignment], alignment)

    def test_portable_sources_resolve_from_declared_root(self) -> None:
        metrics = validate_process_blueprint(
            self.blueprint, repository_root=REPO_ROOT
        )
        self.assertEqual(metrics["process_weight_percent"], 60)

    def test_artifact_bundle_rejects_profile_outside_declared_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            outside_profile = Path(outside_dir) / "course-profile.json"
            outside_profile.write_text(
                json.dumps(self.blueprint, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "fuera de la raíz portable"):
                validate_artifact_bundle(outside_profile, Path(root_dir))


if __name__ == "__main__":
    unittest.main()
