from __future__ import annotations

import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PLUGIN_ROOT.parent.parent
SKILL_PATH = PLUGIN_ROOT / "skills" / "canvas-mds-redisenar" / "SKILL.md"
JUDGE_GUIDE_PATH = REPO_ROOT / "JUDGE_GUIDE.md"


class RedesignSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.judge_guide = JUDGE_GUIDE_PATH.read_text(encoding="utf-8")

    def test_first_hard_stop_forbids_premature_alternatives_and_files(self) -> None:
        self.assertIn("HARD STOP 1", self.skill)
        self.assertIn("no proponer alternativas", self.skill)
        self.assertIn("no crear ni modificar archivos", self.skill)

    def test_second_hard_stop_requires_an_explicit_selection(self) -> None:
        self.assertIn("HARD STOP 2", self.skill)
        self.assertIn("Mientras no exista una selección explícita", self.skill)
        self.assertIn("no generar artefactos", self.skill)

    def test_cohort_workload_must_be_calculated(self) -> None:
        self.assertIn("calcular su carga total con el tamaño de la cohorte", self.skill)
        self.assertIn("tiempo de revisión docente", self.skill)

    def test_portable_output_forbids_absolute_local_paths(self) -> None:
        self.assertIn("rutas relativas a la raíz portable declarada", self.skill)
        self.assertIn("nunca emitir rutas absolutas", self.skill)

    def test_p03_rejects_unselected_instruments_and_cartesian_traceability(self) -> None:
        self.assertIn("Seleccionar todo instrumento usado por el procedimiento", self.skill)
        self.assertIn("exactamente un objetivo y un componente", self.skill)

    def test_p03_requires_resolvable_portable_bundle(self) -> None:
        self.assertIn("cada `source_evidence.path` resuelva", self.skill)
        self.assertIn("--repository-root .", self.skill)

    def test_p03_separates_exclusive_evidence_metrics(self) -> None:
        self.assertIn("categorías excluyentes", self.skill)
        self.assertIn("total de evidencia no final", self.skill)

    def test_p032_requires_udd_source_trace_in_hard_stop(self) -> None:
        self.assertIn("registrar esta base en el inventario como `SRC-00`", self.skill)
        self.assertIn("no emitir identificadores `UDD-R*` o `UDD-H*`", self.skill)

    def test_p032_bounds_process_evidence_claims(self) -> None:
        self.assertIn("No equiparar la ausencia de hitos calificados", self.skill)
        self.assertIn("contribución de la evidencia posterior es indeterminada", self.skill)

    def test_p032_traces_questions_as_manual_decisions(self) -> None:
        self.assertIn("Asignar IDs estables `Q-01`, `Q-02` y `Q-03`", self.skill)
        self.assertIn("reflejar cada una como objeto `MD-*` pendiente", self.skill)

    def test_p033_separates_confirmation_from_resolution(self) -> None:
        self.assertIn("`status: confirmed`", self.skill)
        self.assertIn("`resolution: modified`", self.skill)

    def test_p033_structures_every_pending_decision(self) -> None:
        self.assertIn("cada `manual_decision` como objeto", self.skill)
        self.assertIn("`blocking_stage`", self.skill)

    def test_p033_requires_four_layer_handoff(self) -> None:
        self.assertIn("`GPT-5.6 comprendió y propuso`", self.skill)
        self.assertIn("`El docente decidió`", self.skill)
        self.assertIn("`El motor determinístico verificó`", self.skill)
        self.assertIn("`Sigue pendiente`", self.skill)

    def test_judge_guide_exercises_the_first_hard_stop(self) -> None:
        self.assertIn("HARD STOP 1", self.judge_guide)
        self.assertIn("must not propose alternatives", self.judge_guide)
        self.assertIn("register the packaged UDD knowledge base", self.judge_guide)
        self.assertIn("Do not equate the absence of graded process", self.judge_guide)
        self.assertIn("milestones with 0% process evidence", self.judge_guide)
        self.assertIn("Q-01", self.judge_guide)
        self.assertIn("manual_decisions", self.judge_guide)


if __name__ == "__main__":
    unittest.main()
