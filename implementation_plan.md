# Implementation Plan — Human System (Obsidian Edition)

Sessions are scoped to minimize context needed. Each session is self-contained
and leaves the codebase in a runnable state.

Reference files: `technical_design.md`, `human_system_obsidian.md`

---

## Session 0 — Obsidian Shell Commands plugin setup

**Goal:** Wire the evaluation script to a single Obsidian command palette entry
so the user never needs a terminal.

Plugin: [Shell Commands](https://github.com/Taitava/obsidian-shellcommands)
Install via Obsidian → Settings → Community Plugins → Shell Commands.

Four shell commands to register, one per lifecycle operation:

| Alias | Script | Trigger |
|---|---|---|
| `Human System: Evaluate` | `evaluate_cli.py` | Weekly review |
| `Human System: Graduate Problem` | `graduate_cli.py` | When marking stable |
| `Human System: Revive Problem` | `revive_cli.py` | When regression detected |
| `Human System: Validate Vault` | `validate_cli.py` | After editing notes |

Each command template:
```
python "{{vault_path}}/Scripts/<script>.py" --vault "{{vault_path}}"
```

Plugin config (stored at `.obsidian/plugins/obsidian-shellcommands/data.json`):
- **Shell:** default system shell
- **Output:** show stdout in notification popup (brief summary)
- **Working directory:** `{{vault_path}}`

We will ship a pre-filled `data.json` so the user only needs to enable the
plugin — no manual configuration. File to create:
```
HumanSystem/.obsidian/plugins/obsidian-shellcommands/data.json
```

Verify: Open vault in Obsidian → `Cmd+P` → type "Human System" → all four
commands appear.

---

## Session 1 — Vault scaffold + data model

**Goal:** Create the folder skeleton and Python data model.

Files to create:
```
HumanSystem/
├── PRD.md                        (copy of human_system_obsidian.md)
├── States/   Problems/   Slots/
├── DailyLogs/   Reviews/   Dashboards/
├── Templates/   Scripts/
Scripts/
├── __init__.py
├── model.py                      (Observation, StateDef, ProblemDef, SlotDef, Signal)
├── requirements.txt              (PyYAML>=6)
└── tests/__init__.py
```

Key spec (from `technical_design.md` § Data model):
- `Observation(date, slot, state, raw, value)`
- `StateDef(name, type, status, primary_problem, related_problems, schema_version, criteria, history)`
- `ProblemDef(name, status, state_names, aggregation, graduated)`
- `SlotDef(name, time, state_names)`
- `Signal(state, status, observation_count, window_days, reasons)`

Verify: `python -c "from Scripts.model import Observation, Signal"` succeeds.

---

## Session 2 — Parser: load definitions (States, Problems, Slots)

**Goal:** Read and parse the three definition note types from vault.

File: `Scripts/parser.py`

Functions to implement:
- `load_states(vault: Path) -> dict[str, StateDef]`
- `load_problems(vault: Path) -> dict[str, ProblemDef]`
- `load_slots(vault: Path) -> dict[str, SlotDef]`

Each function:
1. Globs the relevant folder (`States/*.md`, `Problems/*.md`, `Slots/*.md`).
2. Splits frontmatter (PyYAML) from body.
3. Parses body for wikilinks `[[state_name]]` under the `States:` heading.
4. Returns typed dataclass instances.

Note schema (from `technical_design.md` § Note schemas):
- State frontmatter keys: `type, status, primary_problem, related_problems, schema_version, criteria`
- Problem frontmatter keys: `status, created, graduated, aggregation`
- Slot frontmatter keys: `time`

Verify: write a small fixture State/Problem/Slot note, call each loader, print result.

---

## Session 3 — Parser: daily log reading

**Goal:** Walk DailyLogs and extract Observations.

File: `Scripts/parser.py` (extend)

Functions to implement:
- `iter_daily_logs(vault: Path) -> Iterable[Path]`
  - Globs `DailyLogs/**/*.md`, filters by regex `\d{4}-\d{2}-\d{2}\.md`.
- `parse_daily_log(path: Path, state_types: dict[str,str]) -> tuple[list[Observation], list[str]]`
  - Splits by `^## ` headings → slot sections.
  - Extracts `key:: value` via `^([A-Za-z_]\w*)::[ \t]+(.+?)\s*$`.
  - Coerces value by state type:
    - `ordinal` → `int`
    - `gaussian / count / duration` → `float`
    - `boolean` → `True/False` from `{true,yes,1}` / `{false,no,0}`
  - Coercion failures → warning string (file:line — message), line dropped.
  - Lines outside any `## ` section are ignored.

Data contract: observation date is parsed from the filename, not the file content.

Verify: create a fixture daily log, parse it, assert expected Observations and warnings.

---

## Session 4 — Evaluation engine

**Goal:** Implement all five per-type evaluators and the per-problem aggregator.

File: `Scripts/evaluate.py`

Common signature:
```python
def evaluate_<type>(
    obs: list[Observation],
    state: StateDef,
    today: date
) -> Signal
```

Shared pipeline (before type-specific logic):
1. Filter observations to window `[today - window_days + 1, today]`.
2. If `StateDef.history` exists, also filter to `>= current version start date`.
3. Drop `value is None`.
4. If `len < min_observations` → return `Signal(..., status="insufficient_data")`.

Per-type rules (criteria keys from `technical_design.md` § Note schemas — State):
- **ordinal**: `severe_count <= max_severe_count` AND `mild_ratio <= max_mild_ratio`
- **gaussian**: `mean in target_mean` AND `variance <= max_variance`
- **boolean**: `rate >= min_rate` (or `<= max_rate` if key is `max_rate`)
- **count**: `mean in target_band`
- **duration**: `mean in target_band` AND (optionally) streak `>= min_streak_days`

Aggregator:
```python
def aggregate_problem(problem: ProblemDef, signals: dict[str, Signal]) -> Signal
```
- `all_good_enough` policy: any `insufficient_data` → problem `insufficient_data`; all `good_enough` → `good_enough`; else `not_yet`.
- Retired states excluded from signals dict before calling.

Verify: unit-test each evaluator with hand-crafted observation lists at boundary conditions.

---

## Session 5 — Report writer + all CLIs

**Goal:** Wire everything together — report writer and all four entry-point scripts.

Files:
- `Scripts/report.py`
- `Scripts/evaluate_cli.py`
- `Scripts/graduate_cli.py`
- `Scripts/revive_cli.py`
- `Scripts/validate_cli.py`

### report.py
`write_report(vault, today, state_signals, problem_signals, warnings) -> Path`:
- Writes `Reviews/YYYY-MM-DD Stability Report.md`.
- Sections: Active problems table, Per-state signals table, Graduated problems
  (regression watch), Warnings list.
- Header line: `_Signals, not verdicts._`
- Returns the path written.

### evaluate_cli.py
```
python Scripts/evaluate_cli.py [--vault PATH] [--today YYYY-MM-DD] [--problem NAME]
```
- Loads states, problems, slots.
- Parses all daily logs.
- Runs evaluators, aggregates per problem.
- Calls `write_report`.
- Prints one stdout line per problem + path to report.
- Exit code always 0 unless unhandled exception escapes.

### graduate_cli.py
```
python Scripts/graduate_cli.py --problem NAME [--vault PATH] [--why TEXT]
```
- Loads `Problems/<name>.md`, asserts `status: active` or `revived`.
- Appends `Why Graduated (YYYY-MM-DD): <why>` to the problem body.
- Sets frontmatter `status: graduated`, `graduated: YYYY-MM-DD`.
- Moves file to `Problems/Graduated/<name>.md`.
- Prints confirmation to stdout.
- If `--why` is omitted, prompts interactively (stdin) — required, not optional.

### revive_cli.py
```
python Scripts/revive_cli.py --problem NAME [--vault PATH]
```
- Loads `Problems/Graduated/<name>.md`, asserts `status: graduated`.
- Sets frontmatter `status: revived`, clears `graduated`.
- Moves file back to `Problems/<name>.md`.
- Preserves all prior history including the "Why Graduated" block.
- Prints confirmation to stdout.

### validate_cli.py
```
python Scripts/validate_cli.py [--vault PATH]
```
Checks and reports:
- Every state linked in a Problem exists as `States/<state>.md`.
- Every state listed in a Slot exists as `States/<state>.md`.
- Every state's `type` has the required criteria keys present.
- No `key:: value` in any daily log references an unknown state name.
- All graduated problems are in `Problems/Graduated/`.
- Prints a summary: `OK` or a list of issues with file:detail.

Verify: run each script against the fixture vault. Graduate a problem, check file
moved. Revive it, check it moved back. Validate with a broken link, confirm warning.

---

## Session 6 — Templates

**Goal:** Create the three vault templates.

Files:
- `HumanSystem/Templates/Daily Log.md`
- `HumanSystem/Templates/State.md`
- `HumanSystem/Templates/Problem.md`

`Daily Log.md`:
```markdown
# YYYY-MM-DD

## Morning Slot

state_name:: 

Notes:

## Evening Slot

state_name:: 
```

`State.md`: full frontmatter skeleton with all criteria keys (ordinal block
uncommented, others commented), plus `Levels: / Criteria: / Notes: / History:` body.

`Problem.md`: frontmatter skeleton, `Goal: / States: / Success Criteria: / Notes:` body.

Templates are documentation only — the parser never reads them.

---

## Session 7 — Tests

**Goal:** Test suite covering parser, evaluators, aggregation, and end-to-end.

Files under `Scripts/tests/`:
- `fixtures/vault/` — small toy vault:
  - One State (ordinal), one Problem, one Slot
  - ~30 daily logs spanning a window
  - One malformed line in a log
- `test_parser.py` — well-formed line, malformed line, line outside slot, empty
  file, missing state type, wikilink extraction from Problem body.
- `test_evaluate_ordinal.py` — insufficient data, good-enough boundary,
  not-yet boundary, schema-version cutoff, retired state skipped.
- `test_evaluate_gaussian.py` — same boundary cases for gaussian.
- `test_evaluate_boolean.py` — rate above/below threshold.
- `test_aggregation.py` — all combinations of state signals → problem signal.
- `test_graduate.py` — graduate a problem: file moves, frontmatter updated,
  "why" block appended; assert error if already graduated.
- `test_revive.py` — revive a graduated problem: file moves back, status
  flipped, prior "why" preserved; assert error if not graduated.
- `test_validate.py` — broken state link, missing criteria key, unknown state
  in daily log, graduated problem in wrong folder.
- `test_end_to_end.py` — run `evaluate_cli` on fixture vault, assert report
  file contents match snapshot.

Run all: `python -m unittest discover Scripts/tests`

---

## Completion checklist

- [ ] Session 0 — Shell Commands plugin config
- [ ] Session 1 — scaffold + model
- [ ] Session 2 — definition loaders
- [ ] Session 3 — daily log parser
- [ ] Session 4 — evaluators + aggregator
- [ ] Session 5 — report + all CLIs (evaluate, graduate, revive, validate)
- [ ] Session 6 — templates
- [ ] Session 7 — tests
