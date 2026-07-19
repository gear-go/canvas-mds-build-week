# Canvas MDS · Judge Experience

Canvas MDS helps a faculty member redesign assessment for the AI era: from grading only polished outputs to collecting evidence of framing, decisions, iteration, feedback response, individual contribution and responsible AI use.

The recommended experience has two parts:

1. an interactive GPT-5.6 pedagogical redesign in Codex;
2. a credential-free deterministic verification of the approved design and Canvas plan.

No Canvas account, token, student data or network access is required for the offline verification.

## What is genuinely generative

Canvas MDS is not a text splitter or format converter.

GPT-5.6 must:

- reconcile heterogeneous course evidence: learning outcomes, current assessment, rubric, AI guidance and faculty constraints;
- diagnose the assessment-validity gap before proposing a solution;
- identify learning processes that remain invisible in polished team products;
- ask up to three questions whose answers can materially change the design, then enforce HARD STOP 1 while any answer is missing;
- propose at least two viable alternatives with cohort workload, risks and trade-offs only after faculty answers;
- test the selected option against AI-without-understanding and unequal-team-contribution scenarios;
- explain concise, evidence-linked rationales.

The model does not make the final pedagogical decision. Two explicit hard stops prevent it from proposing alternatives before decision-changing answers or compiling artifacts before an option is selected. The faculty member confirms, modifies or rejects material choices. A deterministic engine then validates traceability, weights, learning-outcome coverage, feedback loops, individual evidence, accessible alternatives and Canvas safety gates.

## Part A · Interactive reasoning experience

### Requirements

- Codex with GPT-5.6.
- This repository available locally.
- The Canvas MDS plugin installed from **plugins/canvas-mds**, or the repository opened in Codex so the skill can be inspected.

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
~~~

### What to observe

A conforming run should:

1. read the course evidence and the UDD knowledge base;
2. separate documented facts, model proposals and faculty decisions;
3. explain why a polished AI-assisted product can conceal weak understanding;
4. ask no more than three consequential questions;
5. end the first turn after those questions (HARD STOP 1): it must not propose alternatives, provisional weights, adversarial simulations or files before faculty answers;
6. after the answers, offer at least two alternatives with trade-offs and a cohort-level faculty workload calculation;
7. request an explicit selection and stop again (HARD STOP 2) before compiling artifacts;
8. preserve the authentic final product while adding process evidence;
9. simulate adversarial validity failures only for the selected design;
10. produce an approved, traceable redesign only after faculty confirmation;
11. use repository-relative paths and avoid Canvas writes or student data.

For a time-bounded review, compare the interaction with the completed reference artifacts:

| Artifact | What it demonstrates |
| --- | --- |
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
Ran 20 tests
OK
~~~

The tests cover the read-only and protected-write engines, the P0.1 hard-stop contract, and the process-centered controls derived from the UDD knowledge base: learning-outcome references, self/peer assessment, cognitive demand, feedback actors and response loops.

### Step 2 · Run the judge demo

~~~text
python judge_demo.py
~~~

Expected opening:

~~~text
Canvas MDS Process-Centered Judge Demo
======================================
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

The remainder reports the role of GPT-5.6, the faculty member and the deterministic engine, followed by 20 PASS checks.

For a machine-readable result:

~~~text
python judge_demo.py --json
~~~

## Evidence flow

~~~text
Sanitized course evidence + UDD knowledge base
                    |
                    v
GPT-5.6 evidence-linked diagnosis + decision-changing questions
                    |
                    v
HARD STOP 1 -> faculty answers -> alternatives with workload
                    |
                    v
HARD STOP 2 -> faculty selects or modifies one option
                    |
                    v
GPT-5.6 adversarial simulation of the selected design
                    |
                    v
Traceable redesign artifact + portable course profile
                    |
                    v
Deterministic pedagogical and safety validation
                    |
                    v
Canvas dry-run plan with zero mutations
~~~

Production code used by the offline verification:

| File | Role |
| --- | --- |
| [judge_demo.py](judge_demo.py) | Credential-free English judge harness. |
| [process_evidence.py](plugins/canvas-mds/scripts/process_evidence.py) | Process-centered assessment validation and metrics. |
| [canvas_mds_apply.py](plugins/canvas-mds/scripts/canvas_mds_apply.py) | Profile validator and protected Canvas write engine. |
| [canvas_mds.py](plugins/canvas-mds/scripts/canvas_mds.py) | Read-only engine and dry-run planner. |
| [test_process_evidence.py](plugins/canvas-mds/scripts/test_process_evidence.py) | UDD-informed pedagogical guardrail tests. |
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
