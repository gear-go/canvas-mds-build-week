import unittest

from canvas_mds_apply import question_payload, to_canvas_iso, validate_blueprint


class CanvasMDSApplyTests(unittest.TestCase):
    def test_canvas_iso_uses_course_timezone(self) -> None:
        self.assertEqual(to_canvas_iso("2026-08-20 23:59", "America/Santiago"), "2026-08-21T03:59:00Z")
        self.assertEqual(to_canvas_iso("2026-10-07 23:59", "America/Santiago"), "2026-10-08T02:59:00Z")

    def test_role_question_accepts_all_role_choices(self) -> None:
        payload = question_payload(
            {
                "name": "Q1 · Rol",
                "points": 2,
                "type": "multiple_choice",
                "prompt": "Rol",
                "options": ["A", "B"],
            },
            0,
        )
        weights = [value for key, value in payload if key.endswith("[answer_weight]")]
        self.assertEqual(weights, [100, 100])
        points = dict(payload)["question[points_possible]"]
        self.assertEqual(points, 2)

    def test_blueprint_rejects_pending_decisions(self) -> None:
        with self.assertRaises(Exception):
            validate_blueprint(
                {
                    "default_publish": False,
                    "manual_decisions": [
                        {
                            "id": "MD-01",
                            "status": "pending",
                            "decision": "Pendiente",
                            "blocking_stage": "canvas_write",
                        }
                    ],
                    "assignment_groups": [],
                    "assignments": [],
                    "modules": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
