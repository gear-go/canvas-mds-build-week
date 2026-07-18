# Canvas MDS · Process-Centered Course Design with AI

> A safe Codex plugin that turns course documents, institutional AI guidance, and faculty decisions into reviewable Canvas LMS blueprints.

[Versión en español](README.es.md)

Canvas MDS helps faculty design and scaffold courses around the **learning process**, not only the final deliverable. It combines the interpretive capabilities of **Codex with GPT-5.6** with a deterministic Python engine that inspects Canvas, produces zero-mutation dry-runs, and can create only explicitly approved, unpublished course structures.

The MVP was designed for faculty in the Universidad del Desarrollo (UDD) Master's in Data Science ecosystem, but its profile-based architecture can be adapted to other courses and institutions.

## The problem

Generative AI changes what a final assignment can prove. Faculty need a practical way to redesign activities, checkpoints, individual evidence, AI-use policies, and assessment sequences without manually rebuilding every Canvas course or delegating pedagogical decisions to an automated system.

Canvas MDS separates:

- shared institutional and program-level guidance;
- evidence extracted from an approved syllabus and course plan;
- decisions that still require the instructor;
- deterministic Canvas operations that can be reviewed before execution.

## What the MVP does

- Reads course structure without retrieving student submissions, grades, or enrollment data.
- Produces structural snapshots, provisional audits, and zero-mutation dry-runs.
- Converts course documents and confirmed faculty decisions into a portable JSON course profile.
- Creates or reuses assignment groups, a team category, pages, assignments, one Classic Quiz, and modules.
- Requires the instructor to confirm the exact Canvas course ID before any write.
- Creates everything as **unpublished** and verifies that state after execution.
- Refuses to write when the profile has pending decisions, incompatible weights, an identity mismatch, or a published target object.

It intentionally does **not** publish or delete content, change enrollments, download submissions, post comments, or write grades.

## How it works

| Layer | Responsibility |
| --- | --- |
| Course evidence | Approved syllabus, schedule, institutional guidance, and explicit faculty decisions. |
| Codex + GPT-5.6 | Interprets documents, identifies contradictions and missing decisions, helps the instructor create a traceable course profile, and orchestrates the three plugin skills. |
| JSON course profile | Stores learning outcomes, assessment weights, process evidence, dates, AI/data policies, pages, modules, and pending decisions without Canvas credentials or IDs. |
| Deterministic Python engine | Validates invariants, reads Canvas structure, calculates a dry-run, applies the narrowly authorized plan, and verifies the result. |
| Canvas LMS API | Receives read requests by default and protected POST/PUT requests only after explicit confirmation. |

GPT-5.6 is used through Codex as the reasoning and orchestration layer. The Python engine does not make a hidden model call: its role is to make safety rules testable and predictable.

## The three skills

| Skill | Purpose | Write behavior |
| --- | --- | --- |
| **$canvas-mds-configurar** | Configure the Canvas URL, course ID, local reports, and secure credential source; then run connection diagnostics. | Local configuration only. Never asks for a token in chat. |
| **$canvas-mds-adaptar** | Turn course documents and instructor decisions into a reviewable JSON profile. | Writes a local profile; never changes Canvas. |
| **$canvas-mds-gestionar** | Inspect, audit, dry-run, and—only after precise approval—create an unpublished Canvas structure. | Read-only by default; protected and idempotent unpublished creation is the only Canvas write path. |

## How Codex and GPT-5.6 were used

During Build Week, Codex with GPT-5.6 accelerated the transition from educational requirements to a working plugin:

- translated teaching, AI-policy, privacy, and assessment constraints into a three-skill architecture;
- helped separate instructor judgment from operations that could be automated safely;
- implemented and iterated on the read-only and protected-write Python engines;
- generated tests for origin validation, zero-mutation dry-runs, pending-decision gates, time-zone conversion, and quiz question mapping;
- packaged the plugin, example profile, local marketplace, distribution ZIP, and reproducible provenance.

Key product decisions remained human decisions: focus on process evidence, keep instructors in control, prohibit publication and destructive operations, exclude student data, and require explicit course identity confirmation.

At runtime, GPT-5.6 helps faculty reason over course evidence and construct the profile. Deterministic validation then prevents the model layer from bypassing the approved scope.

## Safety model

- Tokens are stored in the operating-system keyring or supplied through the temporary **CANVAS_API_TOKEN** environment variable.
- Tokens are never requested in chat, stored in a course profile, or committed to the repository.
- Local configuration and reports live under **.canvas/**, which is ignored by Git.
- API requests reject non-HTTPS Canvas URLs and redirects to a foreign origin.
- Read operations are the default.
- The write command requires both **--confirm-course-id &lt;id&gt;** and **--confirm-unpublished**.
- Mutations are not retried automatically.
- Existing published or incompatible target objects stop the operation.

See the complete [security guidance](plugins/canvas-mds/skills/canvas-mds-configurar/references/security.md).

## Repository layout

~~~text
.
├── .agents/plugins/marketplace.json
├── BUILD_WEEK_PROVENANCE.md
├── dist/
│   ├── canvas-mds-portable-0.1.0.sha256.txt
│   └── canvas-mds-portable-0.1.0.zip
└── plugins/canvas-mds/
    ├── .codex-plugin/plugin.json
    ├── assets/profiles/entornos-digitales-2026.json
    ├── scripts/
    └── skills/
~~~

## Requirements and supported platforms

- Codex with plugin marketplace support and GPT-5.6 selected.
- Python 3.10 or newer.
- Python package **requests**.
- Python package **keyring** for the recommended credential flow.
- A Canvas account with teacher-level access for live diagnostics or course creation.

The MVP is currently validated on **Windows with Python 3.12.4**. The Python code is designed to be portable to macOS and Linux, but those platforms have not yet been verified for this release.

## Installation

From the repository root:

~~~text
python -m pip install requests keyring
codex plugin marketplace add <absolute-path-to-this-repository>
~~~

Restart the ChatGPT desktop app after adding the marketplace. In Codex (or Work mode), open Plugins, choose the **Canvas MDS · Docentes** marketplace, and install **Canvas MDS**. Start a new Codex task, select GPT-5.6, and begin with:

~~~text
$canvas-mds-configurar
~~~

For marketplace behavior and local installation, see [OpenAI's plugin documentation](https://developers.openai.com/codex/plugins/build).

The packaged ZIP under **dist/** provides the same plugin without requiring a rebuild.

## Fast path for judges: no Canvas credentials required

Run the automated verification from the repository root:

~~~text
python -m pip install requests keyring
python -m unittest discover -s plugins/canvas-mds/scripts -p "test_*.py" -v
~~~

Expected result:

~~~text
Ran 7 tests
OK
~~~

Then run the complete credential-free judge experience:

~~~text
python judge_demo.py
~~~

It validates the sample profile with the production validator and generates an English PASS summary from a synthetic dry-run with zero network access and zero Canvas mutations. See the full [Five-Minute Judge Experience](JUDGE_GUIDE.md).

The tests exercise:

- HTTPS and same-origin enforcement;
- zero-mutation dry-run behavior;
- preservation of confirmed policies;
- pending-decision write rejection;
- Canvas dates generated in the course time zone;
- supported Classic Quiz role choices;
- structured provisional audit output.

Judges can also inspect the anonymized technical pattern in [entornos-digitales-2026.json](plugins/canvas-mds/assets/profiles/entornos-digitales-2026.json). It is a reference profile, not a profile to apply to an unrelated course.

## Optional Canvas-connected verification

1. Copy [local-config.example.json](plugins/canvas-mds/skills/canvas-mds-configurar/references/local-config.example.json) to **.canvas/local.json** and set only the non-secret Canvas URL, course ID, and keyring account.
2. Store the token interactively:

   ~~~text
   python plugins/canvas-mds/scripts/store_canvas_token.py --account <keyring-account>
   ~~~

3. Confirm read access:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds.py doctor
   ~~~

4. Use **$canvas-mds-adaptar** to create and approve a profile for that specific sandbox course.
5. Generate a dry-run with no mutations:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds.py dry-run --blueprint <course-profile.json>
   ~~~

6. Only after reviewing the plan and confirming the sandbox course ID, optionally create the unpublished structure:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds_apply.py --blueprint <course-profile.json> --confirm-course-id <id> --confirm-unpublished
   ~~~

No publication command exists in this MVP.

## Current limitations

- Canvas access is required for snapshots, audits, live dry-runs, and creation.
- The MVP supports one Classic Quiz per profile.
- Rubric approval and association remain a manual gate before publication.
- Pages are scaffolded as reviewable templates, not final teaching content.
- macOS and Linux validation is pending.
- Publishing, deletion, grades, enrollment changes, submissions, and comments are outside the supported scope.

## Build Week scope and provenance

The needs behind Canvas MDS came from earlier work in the UDD AI Workshop, university and faculty AI committees, institutional AI policy discussions, and leadership of the Master's in Data Science. That prior work established the problem and constraints; it is not presented as Build Week software.

Product ideation for this implementation began on July 16, 2026. The earliest recovered core technical session was created on July 17, 2026. The portable plugin, three skills, deterministic engine, seven tests, example profile, distribution package, and submission evidence were implemented for Build Week.

See [BUILD_WEEK_PROVENANCE.md](BUILD_WEEK_PROVENANCE.md) for the evidence record.

- Track: **Education**
- Core Codex /feedback Session ID: **019f6fdb-32dc-70a0-a353-8640c3a29f08**
- Distribution ZIP SHA-256: **7f863022d884e4003245850fffe80c6267ae35a3b28db628685273ac2e11486e**

## Author

- Germán Gómez
- Universidad del Desarrollo (UDD)
- gagomez@udd.cl
