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
        self.assertIn("mientras no exista una selección explícita", self.skill)
        self.assertIn("no generar artefactos", self.skill)

    def test_cohort_workload_must_be_calculated(self) -> None:
        self.assertIn("calcular su carga total con el tamaño de la cohorte", self.skill)
        self.assertIn("tiempo de revisión docente", self.skill)

    def test_portable_output_forbids_absolute_local_paths(self) -> None:
        self.assertIn("rutas relativas al repositorio", self.skill)
        self.assertIn("nunca emitir rutas absolutas", self.skill)

    def test_judge_guide_exercises_the_first_hard_stop(self) -> None:
        self.assertIn("HARD STOP 1", self.judge_guide)
        self.assertIn("must not propose alternatives", self.judge_guide)


if __name__ == "__main__":
    unittest.main()
