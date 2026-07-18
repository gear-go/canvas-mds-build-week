import unittest

from canvas_mds import (
    CanvasMVPError,
    CanvasReadOnlyClient,
    build_dry_run,
    evaluate_snapshot,
    html_to_text,
)


def sample_snapshot() -> dict:
    return {
        "metadata": {"permission_issues": []},
        "course": {
            "id": 12345,
            "name": "Entornos Digitales",
            "workflow_state": "available",
            "apply_assignment_group_weights": True,
            "syllabus_body": "Diagnóstico, propuesta de valor, gobernanza ética, implementación y comunicación.",
        },
        "modules": [
            {
                "id": 1,
                "name": "Módulo 00 · Orientación",
                "published": True,
                "items": [{"title": "Reglas IAG y datos", "type": "Page", "published": True}],
            }
        ],
        "pages": [
            {
                "title": "Comience aquí",
                "front_page": True,
                "published": True,
                "body": "Propósito, ruta de navegación, apoyo y expectativas de participación.",
            }
        ],
        "assignments": [
            {
                "id": 10,
                "name": "Presentación oral bimestral",
                "published": True,
                "description": (
                    "Evalúa RA1. Nivel B IAG. Trabajo grupal con defensa individual, fuentes, "
                    "feedback, prueba de resistencia, autoridad humana y rendición de cuentas."
                ),
                "has_rubric": True,
                "due_at": "2026-08-01T23:59:00Z",
                "submission_types": ["online_upload"],
            }
        ],
        "assignment_groups": [{"name": "Presentación oral", "group_weight": 100}],
        "rubrics": [{"title": "Rúbrica", "criteria_count": 5}],
        "tabs": [],
    }


class CanvasMDSReadOnlyTests(unittest.TestCase):
    def test_html_to_text(self) -> None:
        self.assertEqual(html_to_text("<p>Hola <strong>Canvas</strong></p>"), "Hola Canvas")

    def test_audit_is_provisional_and_structured(self) -> None:
        result = evaluate_snapshot(sample_snapshot())
        self.assertIn(result["overall"], {"NO_LISTO_PROVISIONAL", "REQUIERE_REVISION_DOCENTE"})
        self.assertGreater(result["summary"]["criteria_total"], 10)
        self.assertEqual(len(result["top_priorities"]), 3)

    def test_client_rejects_non_https_and_foreign_origin(self) -> None:
        client = CanvasReadOnlyClient("https://udd.instructure.com", "not-a-real-token")
        with self.assertRaises(CanvasMVPError):
            client._absolute_url("http://udd.instructure.com/api/v1/courses")
        with self.assertRaises(CanvasMVPError):
            client._absolute_url("https://example.com/api/v1/courses")

    def test_dry_run_preserves_confirmed_policies_without_mutations(self) -> None:
        blueprint = {
            "version": "test",
            "assignment_groups": [],
            "assignments": [],
            "modules": [],
            "course_policies": [
                {
                    "key": "program_scope",
                    "label": "Programa",
                    "status": "confirmed",
                    "summary": "Aprobado.",
                }
            ],
            "manual_decisions": ["Confirmar mecanismo individual."],
        }
        plan = build_dry_run(sample_snapshot(), blueprint)
        self.assertEqual(plan["metadata"]["canvas_mutations"], 0)
        self.assertEqual(plan["course_policies"][0]["status"], "confirmed")
        self.assertEqual(plan["manual_decisions"], ["Confirmar mecanismo individual."])


if __name__ == "__main__":
    unittest.main()
