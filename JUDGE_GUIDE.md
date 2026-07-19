# AssessTrace — Evidence by Design · Judge Experience

**AssessTrace — evidence by design.** It redesigns assessment so the learning process leaves evidence: the instructor decides; the tool traces. **Canvas MDS** is its first adapter.

The recommended experience has two parts:

1. an interactive GPT-5.6 pedagogical redesign in Codex;
2. a credential-free deterministic verification of the approved design and Canvas plan.

No Canvas account, token, student data or network access is required for the offline verification.

## What is genuinely generative

AssessTrace is not a text splitter or format converter.

GPT-5.6 must:

- reconcile heterogeneous course evidence: learning outcomes, current assessment, rubric, AI guidance and faculty constraints;
- diagnose the assessment-validity gap before proposing a solution;
- distinguish a demonstrable objective from an activity agenda;
- propose observable objective alternatives and stop for faculty confirmation when no approved objective exists;
- derive and audit objective → indicator → evidence → instrument → procedure before calendarizing activities;
- identify learning processes that remain invisible in polished team products;
- ask up to three questions whose answers can materially change the design;
- propose at least two viable alternatives with workload, risks and trade-offs;
- test the selected option against AI-without-understanding and unequal-team-contribution scenarios;
- explain concise, evidence-linked rationales.

The model does not make the final pedagogical decision. The faculty member confirms, modifies or rejects material choices. A deterministic engine then validates traceability, weights, learning-outcome coverage, feedback loops, individual evidence, accessible alternatives and Canvas safety gates.

## Part A · Interactive reasoning experience

### Requirements

- Codex with GPT-5.6.
- This repository available locally.
- The **AssessTrace · Canvas MDS** plugin installed from **plugins/canvas-mds**, or the repository opened in Codex so the skill can be inspected.

### Prompt

From the repository root, ask Codex:

~~~text
Use $canvas-mds-redisenar to analyze the sanitized course evidence in
plugins/canvas-mds/assets/judge-case/input.

Diagnose whether the current assessment can establish student learning in an
AI-rich course. Use the packaged UDD active-learning knowledge base where
relevant. Do not inspect the reference solution yet. First show me the
evidence-linked diagnosis and ask only the decision-changing faculty questions
you need before proposing a redesign.

If the evidence does not contain an approved objective, propose two or three
observable objective alternatives. Stop after the objective alternatives and
wait for my explicit confirmation before deriving indicators or activities.
~~~

### What to observe

A conforming run should:

1. read the course evidence and the UDD knowledge base;
2. separate documented facts, model proposals and faculty decisions;
3. explain why a polished AI-assisted product can conceal weak understanding;
4. ask no more than three consequential questions;
5. enforce HARD STOP 1 while consequential questions remain unanswered; it must not propose alternatives, weights, simulations or files in that turn;
6. preserve approved outcomes or distinguish a proposed objective from activities;
7. enforce ALIGNMENT STOP until a new or revised objective is explicitly confirmed;
8. derive 4–6 indicators, concrete evidence, three compared instruments, realistic workload and a feedback procedure;
9. offer at least two redesign alternatives with workload and trade-offs;
10. enforce HARD STOP 2 until one option is selected or modified;
11. preserve the authentic final product while adding process evidence;
12. simulate adversarial validity failures;
13. produce artifacts only after faculty confirmation;
14. avoid Canvas writes and student data.

For a time-bounded review, compare the interaction with the completed reference artifacts:

| Artifact | What it demonstrates |
| --- | --- |
| [planning-alignment.json](plugins/canvas-mds/assets/judge-case/reference/planning-alignment.json) | Confirmed objective, indicators, evidence, compared instruments, workload and feedback procedure. |
| [pedagogical-redesign.json](plugins/canvas-mds/assets/judge-case/reference/pedagogical-redesign.json) | Evidence-linked diagnosis, questions, decisions, alternatives and adversarial tests. |
| [before-after.md](plugins/canvas-mds/assets/judge-case/reference/before-after.md) | Concise explanation of the assessment paradigm shift. |
| [entornos-digitales-2026.json](plugins/canvas-mds/assets/profiles/entornos-digitales-2026.json) | Approved design compiled into a portable Canvas MDS profile. |
| [metodologias-activas-udd.md](plugins/canvas-mds/skills/canvas-mds-redisenar/references/metodologias-activas-udd.md) | Institutional pedagogical knowledge used as traceable guidance. |

The reference case moves from **95% final-product evidence / 0% process evidence** to **40% final-product evidence / 60% process evidence**, with a separate **5% individual instrument**.

## Part B · Automated verification

### Requirements

- Python 3.10 or newer.
- The Python package **requests**.

~~~text
python -m pip install requests
~~~

No OpenAI API key, Canvas token or Canvas account is required.

### Step 1 · Run the tests

~~~text
python -m unittest discover -s plugins/canvas-mds/scripts -p "test_*.py" -v
~~~

Expected result:

~~~text
Ran 29 tests
OK
~~~

The tests cover the read-only and protected-write engines, the P0.1 hard-stop contract, cohort-level workload and portable paths, plus objective/activity separation, the P0.2 alignment stop, bidirectional evidence mappings, instrument selection, workload arithmetic, usable feedback, and the process-centered UDD controls.

### Step 2 · Run the judge demo

~~~text
python judge_demo.py
~~~

Expected opening:

~~~text
AssessTrace - Evidence by Design Judge Demo
===========================================
Status: PASS
Profile: entornos-digitales-digital-innovation-studio-2026
Canvas connection used: no
Credentials required: no
Canvas mutations: 0

Assessment evidence shift:
- Final product: 95% -> 40.0%
- Process evidence: 0% -> 60.0%
- Individual evidence: 5% -> 5.0%
~~~

The remainder reports the role of GPT-5.6, the faculty member and the deterministic engine, followed by 21 PASS checks, including the live P0.2 alignment gate.

For a machine-readable result:

~~~text
python judge_demo.py --json
~~~

## Evidence flow

~~~text
Sanitized course evidence + UDD knowledge base
                    |
                    v
AssessTrace + GPT-5.6: evidence-linked diagnosis + questions
                    |
                    v
HARD STOP 1 -> faculty answers
                    |
                    v
Confirmed objective or objective alternatives -> ALIGNMENT STOP
                    |
                    v
Indicators -> evidence -> compared instruments -> procedure
                    |
                    v
Redesign alternatives with cohort workload -> HARD STOP 2
                    |
                    v
Faculty selection -> adversarial simulation
                    |
                    v
Traceable redesign artifact + portable course profile
                    |
                    v
AssessTrace: deterministic pedagogical and safety validation
                    |
                    v
Canvas MDS adapter: dry-run plan with zero mutations
~~~

Production code used by the offline verification:

| File | Role |
| --- | --- |
| [judge_demo.py](judge_demo.py) | Credential-free English judge harness. |
| [process_evidence.py](plugins/canvas-mds/scripts/process_evidence.py) | Process-centered assessment validation and metrics. |
| [planning_alignment.py](plugins/canvas-mds/scripts/planning_alignment.py) | Deterministic P0.2 alignment gate and workload validation. |
| [canvas_mds_apply.py](plugins/canvas-mds/scripts/canvas_mds_apply.py) | Profile validator and protected Canvas write engine. |
| [canvas_mds.py](plugins/canvas-mds/scripts/canvas_mds.py) | Read-only engine and dry-run planner. |
| [test_process_evidence.py](plugins/canvas-mds/scripts/test_process_evidence.py) | UDD-informed pedagogical guardrail tests. |
| [test_planning_alignment.py](plugins/canvas-mds/scripts/test_planning_alignment.py) | Objective, evidence, instrument, procedure and alignment-stop regression tests. |
| [test_skill_contract.py](plugins/canvas-mds/scripts/test_skill_contract.py) | P0.1 regression tests for decision hard stops, cohort workload and portable paths. |

## Why the Canvas snapshot is synthetic

A live Canvas snapshot could expose internal course structure. The synthetic snapshot contains no people, submissions, grades, enrollments, tokens or institutional identifiers.

Only the read boundary is synthetic. The redesign validator, production profile validator, action planner, object counts, unpublished-state checks and zero-mutation verification are real production functions.

## What this experience does not claim

It does not prove that:

- a judge account has access to an institutional Canvas instance;
- every endpoint is enabled in a specific Canvas installation;
- final teaching content or rubrics have received local faculty approval;
- any course is ready to publish;
- GPT-5.6 should grade students or infer authorship.

Those remain explicit operational, institutional and faculty-review gates.

## Optional live sandbox path

A judge with a disposable Canvas sandbox and teacher-level permissions can follow [the optional connected verification](README.md#optional-canvas-connected-verification).

The live path remains read-only through **doctor**, **snapshot**, **audit** and **dry-run**. Protected creation is optional, requires explicit course confirmation and creates unpublished objects only.
