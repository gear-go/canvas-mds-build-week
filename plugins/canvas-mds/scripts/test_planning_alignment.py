from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from planning_alignment import validate_planning_alignment
from process_evidence import validate_redesign_artifact


def fixture() -> dict:
    indicator_ids = [f"IND-0{i}" for i in range(1, 5)]
    indicators = [
        {
            "id": iid,
            "statement": f"Fundamenta el criterio observable {iid}.",
            "type": "process" if index < 3 else "result",
            "observable": True,
            "attendance_or_participation_only": False,
            "quality_condition": "Usa evidencia verificable.",
            "objective_ids": ["OBJ-01"],
            "evidence_ids": ["EV-01"],
        }
        for index, iid in enumerate(indicator_ids)
    ]
    return {
        "schema_version": "0.1.0",
        "alignment_id": "ALIGN-01",
        "alignment_status": "confirmed",
        "scope": "workshop",
        "need": "Tomar decisiones verificables ante patrones de asistencia.",
        "audience": "Equipos escolares",
        "duration": {"value": 3, "unit": "hours"},
        "objectives": [
            {
                "id": "OBJ-01",
                "statement": "Fundamentar decisiones mediante analisis verificado.",
                "observable_action": "Fundamentar",
                "content_or_performance": "decisiones de escalamiento",
                "condition": "mediante datos sanitizados y analisis verificado",
                "status": "faculty_confirmed",
                "activity_free": True,
                "source_evidence_ids": ["SRC-01"],
                "faculty_decision_ids": ["FD-01"],
            }
        ],
        "indicators": indicators,
        "evidence": [
            {
                "id": "EV-01",
                "description": "Decision fundamentada y verificada.",
                "scope": "team",
                "indicator_ids": indicator_ids,
            }
        ],
        "instruments": [
            {
                "id": "INS-01",
                "type": "analytic_rubric",
                "role": "primary",
                "selected": True,
                "rationale": "Valora criterios diferenciados.",
                "advantages": "Feedback preciso.",
                "limitations": "Mayor carga.",
                "indicator_ids": indicator_ids,
                "evidence_ids": ["EV-01"],
                "review_workload": {
                    "items_to_review": 10,
                    "minutes_per_item": 5,
                    "estimated_total_minutes": 50,
                    "reviewer": "facilitator",
                },
            },
            {
                "id": "INS-02",
                "type": "checklist",
                "role": "considered",
                "selected": False,
                "rationale": "Verifica presencia.",
                "advantages": "Rapida.",
                "limitations": "Poca profundidad.",
            },
            {
                "id": "INS-03",
                "type": "holistic_rubric",
                "role": "considered",
                "selected": False,
                "rationale": "Valoracion global.",
                "advantages": "Eficiente.",
                "limitations": "Feedback menos preciso.",
            },
        ],
        "evaluation_procedure": {
            "moments": [
                {
                    "id": "MOM-01",
                    "stage": "final",
                    "actor": "facilitator",
                    "action": "Valora la decision fundamentada.",
                    "evidence_ids": ["EV-01"],
                    "instrument_ids": ["INS-01"],
                    "feedback": "Indica una fortaleza y una mejora.",
                    "feedback_use": "Revisar el plan de escalamiento.",
                }
            ]
        },
        "alignment_matrix": [
            {
                "objective_component": component,
                "objective_ids": ["OBJ-01"],
                "indicator_ids": indicator_ids,
                "evidence_ids": ["EV-01"],
                "instrument_ids": ["INS-01"],
                "procedure_moment_ids": ["MOM-01"],
            }
            for component in ("action", "content_or_performance", "condition")
        ],
        "unresolved_decisions": [],
    }


class PlanningAlignmentTests(unittest.TestCase):
    def validate(self, value: dict) -> dict:
        return validate_planning_alignment(
            value,
            source_ids={"SRC-01"},
            accepted_decision_ids={"FD-01"},
        )

    def test_valid_alignment(self) -> None:
        metrics = self.validate(fixture())
        self.assertEqual(metrics["indicator_count"], 4)
        self.assertEqual(metrics["estimated_review_minutes"], 50)

    def test_reference_alignment_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "assets" / "judge-case" / "reference" / "planning-alignment.json"
        alignment = json.loads(path.read_text(encoding="utf-8"))
        metrics = validate_planning_alignment(alignment)
        self.assertEqual(metrics["indicator_count"], 5)
        self.assertEqual(metrics["estimated_review_minutes"], 180)

    def test_rejects_ambiguous_objective_action(self) -> None:
        value = fixture()
        value["objectives"][0]["observable_action"] = "Comprender"
        with self.assertRaisesRegex(ValueError, "no observable"):
            self.validate(value)

    def test_rejects_activity_as_objective(self) -> None:
        value = fixture()
        value["objectives"][0]["activity_free"] = False
        with self.assertRaisesRegex(ValueError, "actividad"):
            self.validate(value)

    def test_rejects_too_few_indicators(self) -> None:
        value = fixture()
        value["indicators"] = value["indicators"][:3]
        with self.assertRaisesRegex(ValueError, "cuatro y seis"):
            self.validate(value)

    def test_rejects_non_bidirectional_evidence(self) -> None:
        value = fixture()
        value["evidence"][0]["indicator_ids"].remove("IND-04")
        with self.assertRaisesRegex(ValueError, "bidireccional"):
            self.validate(value)

    def test_rejects_unreal_workload(self) -> None:
        value = fixture()
        value["instruments"][0]["review_workload"]["estimated_total_minutes"] = 10
        with self.assertRaisesRegex(ValueError, "carga"):
            self.validate(value)

    def test_rejects_feedback_without_use(self) -> None:
        value = fixture()
        value["evaluation_procedure"]["moments"][0]["feedback_use"] = ""
        with self.assertRaisesRegex(ValueError, "feedback"):
            self.validate(value)

    def test_redesign_03_requires_alignment(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "assets" / "judge-case" / "reference" / "pedagogical-redesign.json"
        artifact = json.loads(path.read_text(encoding="utf-8"))
        artifact["schema_version"] = "0.3.0"
        with self.assertRaisesRegex(ValueError, "requiere planning_alignment"):
            validate_redesign_artifact(copy.deepcopy(artifact))


if __name__ == "__main__":
    unittest.main()
