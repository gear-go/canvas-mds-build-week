# Canvas MDS · Five-Minute Judge Experience

This guide provides a reproducible way to evaluate Canvas MDS without a Canvas account, API token, network connection, or rebuild.

The offline harness calls the same production profile validator and dry-run planner used by the plugin. It supplies a synthetic empty Canvas snapshot only at the boundary where the live workflow would normally read course structure.

## What you can verify

In approximately five minutes, you can confirm that Canvas MDS:

- loads a realistic course profile;
- rejects structurally unsafe profiles through the production validator;
- checks that assessment groups sum to 100%;
- requires a distinctive course identity and exactly one Classic Quiz;
- requires zero pending faculty decisions;
- keeps default publication disabled;
- creates a dry-run with **canvas_mutations: 0**;
- marks every planned page, assignment, and module as unpublished;
- performs the experience without credentials or HTTP requests.

The sample course content is in Spanish because the target deployment context is UDD in Chile. The judge interface, commands, output, and this guide are in English.

## Requirements

- Python 3.10 or newer.
- The Python package **requests**.

From the repository root:

~~~text
python -m pip install requests
~~~

No OpenAI API key, Canvas token, Canvas account, or Codex installation is required for this offline path.

## Step 1: run the automated tests

~~~text
python -m unittest discover -s plugins/canvas-mds/scripts -p "test_*.py" -v
~~~

Expected result:

~~~text
Ran 7 tests
OK
~~~

These tests cover the deterministic engine, including origin validation, dry-run behavior, pending-decision gates, Canvas time-zone conversion, and Classic Quiz mapping.

## Step 2: run the offline judge demo

~~~text
python judge_demo.py
~~~

Expected summary:

~~~text
Canvas MDS Offline Judge Demo
=============================
Status: PASS
Profile: entornos-digitales-digital-innovation-studio-2026
Canvas connection used: no
Credentials required: no
Canvas mutations: 0

Proposed course structure:
- Modules: 9
- Unique pages: 36
- Assignments: 10
- Assignment groups: 3
~~~

The remainder of the output lists ten individual PASS checks.

For a machine-readable result:

~~~text
python judge_demo.py --json
~~~

## Step 3: inspect the evidence flow

The offline path uses these repository artifacts:

| Artifact | Role |
| --- | --- |
| [judge_demo.py](judge_demo.py) | Credential-free judge harness and English summary. |
| [entornos-digitales-2026.json](plugins/canvas-mds/assets/profiles/entornos-digitales-2026.json) | Realistic, non-secret sample course profile. |
| [canvas_mds_apply.py](plugins/canvas-mds/scripts/canvas_mds_apply.py) | Production profile validator and protected Canvas write engine. |
| [canvas_mds.py](plugins/canvas-mds/scripts/canvas_mds.py) | Production read-only engine and dry-run planner. |
| [test_canvas_mds.py](plugins/canvas-mds/scripts/test_canvas_mds.py) | Read-only, audit, origin, and dry-run tests. |
| [test_canvas_mds_apply.py](plugins/canvas-mds/scripts/test_canvas_mds_apply.py) | Protected-write validation tests. |

The flow is:

~~~text
Sample course profile
        |
        v
Production blueprint validator
        |
        v
Synthetic empty Canvas snapshot
        |
        v
Production dry-run planner
        |
        v
English PASS summary (zero mutations)
~~~

## Why the snapshot is synthetic

A live Canvas snapshot would require access to a real institutional course and could expose internal course structure. The synthetic snapshot contains no people, submissions, grades, enrollments, tokens, or institutional identifiers.

Only the snapshot boundary is synthetic. Profile validation, action planning, object counts, unpublished-state checks, and zero-mutation verification use production functions directly.

## Safety checks performed

The judge harness exits with status code 1 if any of these conditions fails:

1. The profile is valid.
2. **default_publish** is false.
3. **manual_decisions** is empty.
4. Assignment groups sum to 100%.
5. Exactly one Classic Quiz is present.
6. The dry-run reports zero Canvas mutations.
7. Every planned object remains unpublished.
8. An empty snapshot requires all proposed objects to be created.
9. No network or Canvas access is used.
10. No credentials are required.

## What this offline experience does not claim

The offline demo does not prove:

- that a particular judge account has permission to a Canvas instance;
- that a specific institutional Canvas configuration enables every endpoint;
- that macOS or Linux keyring integration has been validated;
- that final teaching content, accessibility, links, or rubrics have received faculty approval;
- that any course is ready to publish.

Those are intentionally separate operational and faculty-review gates.

## Optional live sandbox path

A judge with a disposable Canvas sandbox and teacher-level permissions can follow the optional connected verification in [README.md](README.md#optional-canvas-connected-verification).

The live path remains read-only through **doctor**, **snapshot**, **audit**, and **dry-run**. The protected creation command is optional, requires the exact course ID twice in the workflow, and can create only unpublished objects.

## Exit codes

| Code | Meaning |
| ---: | --- |
| 0 | Every offline judge check passed. |
| 1 | The profile could not be read, validation failed, or a safety invariant failed. |

## Suggested judging focus

After running the experience, review:

- how course evidence becomes a portable profile;
- how Codex with GPT-5.6 supports interpretation and faculty decision-making;
- how deterministic validation constrains the model-assisted workflow;
- how process evidence, checkpoints, and individual reflection appear in the sample profile;
- how the project avoids student data and destructive Canvas operations.
