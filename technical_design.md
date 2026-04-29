# Technical Design — Human System (Obsidian Edition)

## Context

The PRD (`human_system_obsidian.md`, v2) defines an Obsidian-first reflection
framework: markdown vault as source of truth, lightweight Python scripts that
read the vault and emit *signals* (never verdicts) about state stability. The
PRD specifies the vault layout and philosophical boundaries clearly but leaves
the Python implementation, the criterion data format, and the output medium
underspecified.

This design pins down those gaps so implementation can begin. It deliberately
stays minimal — the PRD's "lightweight enough to sustain" principle is the
primary constraint. No frameworks, no install step, no DSLs.

**Decisions locked with user:**
- Scripts live inside the vault at `HumanSystem/Scripts/` (no install).
- Criteria are authored in YAML frontmatter; body's `Criteria:` block is a
  human-readable mirror.
- Evaluation writes a markdown report to `HumanSystem/Reviews/` and prints a
  one-line summary to stdout.
- Toolchain: Python 3.10+ stdlib + PyYAML only.

---

## Architecture

```
HumanSystem/                                  HumanSystem/Scripts/
├── DailyLogs/YYYY/MM/YYYY-MM-DD.md  ──read──▶ ├── parser.py     observations + notes
├── States/<state>.md                ──read──▶ ├── model.py      dataclasses
├── Problems/<problem>.md            ──read──▶ ├── evaluate.py   per-type signals
├── Slots/<slot>.md                  ──read──▶ ├── report.py     markdown writer
├── Templates/                                  ├── evaluate_cli.py  entry point
├── Reviews/  ◀──write─ stability report ───── └── tests/
└── ...
```

One process: `python Scripts/evaluate_cli.py` walks the vault, parses, evaluates,
writes one report file, prints a summary. No daemons, no caches, no DB.

---

## Vault layout (per PRD §7, no changes)

`HumanSystem/{DailyLogs,States,Problems,Slots,Templates,Dashboards,Scripts,Reviews}`.
PRD.md sits at the root.

---

## Note schemas (concrete)

### State note — `States/<state>.md`

```markdown
---
type: ordinal              # ordinal | gaussian | boolean | count | duration
status: active             # active | retired
primary_problem: "Energy Problem"
related_problems: []
schema_version: 1
criteria:
  window_days: 55
  min_observations: 60
  # ordinal-specific
  max_severe_count: 0      # values >= severe_threshold
  severe_threshold: 2
  max_mild_ratio: 0.10     # values >= mild_threshold
  mild_threshold: 1
  # gaussian-specific (only when type=gaussian)
  # target_mean: [70.0, 72.0]
  # max_variance: 1.5
  # boolean-specific
  # min_rate: 0.7   (or max_rate)
  # count / duration
  # target_band: [0, 2]
  # min_streak_days: 7
---

# headache

Levels:
- 0 = none
- 1 = mild
- 2 = severe

Criteria:
- no severe values in the last 55 days
- mild ratio <= 10%
- minimum observations >= 60

Notes:
Captured at the morning slot; severity is what I notice on waking.

History:
- v1 — 2026-04-01 — initial definition
```

The body's `Criteria:` block is documentation only; the parser reads only
frontmatter. Type-specific keys are validated against `type` at load time;
unknown keys are warnings, not errors.

### Problem note — `Problems/<problem>.md`

```markdown
---
status: active             # active | graduated | revived
created: 2026-04-01
graduated: null            # YYYY-MM-DD when graduated
aggregation: all_good_enough   # all_good_enough (default) | future modes
---

# Energy Problem

Goal: ...

States:
- [[headache]]
- [[sleep_quality]]

Success Criteria: ...
Notes: ...

Why Graduated (YYYY-MM-DD): ...   # appended on graduation
```

State membership is parsed from the wikilinks under the `States:` heading.

### Slot note — `Slots/<slot>.md`

```markdown
---
time: "09:00"
---

# Morning Checkin

States:
- [[headache]]
- [[sleep_quality]]
```

Slot is organizational only; parser uses it to validate that observations in a
daily log slot section reference states the slot expects (warning, not error).

### Daily log — `DailyLogs/YYYY/MM/YYYY-MM-DD.md`

```markdown
# 2026-04-29

## Morning Slot

headache:: 1
sleep_quality:: 2
weight:: 71.2

Notes:
felt mentally tired after lunch

---

## Evening Slot

focus_quality:: 1
stress_level:: 2
```

The data contract: a `key:: value` line **inside** an H2 slot heading **inside**
a file named `YYYY-MM-DD.md`. Lines outside slot sections are ignored. Free
text is ignored. Frontmatter on daily logs is ignored.

---

## Data model — `Scripts/model.py`

```python
@dataclass(frozen=True)
class Observation:
    date: date
    slot: str            # "Morning Slot"
    state: str           # "headache"
    raw: str             # original RHS text
    value: float | int | bool | None

@dataclass
class StateDef:
    name: str
    type: Literal["ordinal","gaussian","boolean","count","duration"]
    status: Literal["active","retired"]
    primary_problem: str | None
    related_problems: list[str]
    schema_version: int
    criteria: dict        # type-specific, validated at load
    history: list[dict]   # [{version, date, note}]

@dataclass
class ProblemDef:
    name: str
    status: Literal["active","graduated","revived"]
    state_names: list[str]
    aggregation: str
    graduated: date | None

@dataclass
class SlotDef:
    name: str
    time: str | None
    state_names: list[str]

@dataclass
class Signal:
    state: str
    status: Literal["good_enough","not_yet","insufficient_data"]
    observation_count: int
    window_days: int
    reasons: list[str]    # human-readable, e.g. "mild ratio 0.08 <= 0.10"
```

---

## Parser — `Scripts/parser.py`

Functions:
- `iter_daily_logs(vault) -> Iterable[Path]` — globs `DailyLogs/**/*.md`,
  filters by `YYYY-MM-DD.md` regex.
- `parse_daily_log(path, state_types) -> list[Observation], list[Warning]` —
  splits by `^## ` headings, extracts `key:: value` via
  `^([A-Za-z_][\w]*)::\s*(.+?)\s*$`, coerces by `state_types[key]`:
  - ordinal → `int(rhs)`
  - gaussian / count / duration → `float(rhs)`
  - boolean → `{"true","yes","1"} → True`, `{"false","no","0"} → False`
  Coercion failures become warnings; the line is dropped.
- `load_states(vault) -> dict[str, StateDef]`
- `load_problems(vault) -> dict[str, ProblemDef]`
- `load_slots(vault) -> dict[str, SlotDef]`

Frontmatter via PyYAML; body via plain string scanning. No regex on YAML.

Warnings are accumulated, not raised, and surfaced in the report's Warnings
section (PRD §14).

---

## Evaluation engine — `Scripts/evaluate.py`

One function per measurement type, all with the same signature:

```python
def evaluate_<type>(obs: list[Observation], crit: dict, today: date) -> Signal
```

Shared pipeline:
1. Filter to window `[today - window_days + 1, today]`.
2. Drop `value is None`.
3. If `count < min_observations` → `insufficient_data`.
4. Apply per-type rules:
   - **ordinal** — `severe_count <= max_severe_count` AND
     `mild_ratio <= max_mild_ratio` (where severe = `value >= severe_threshold`,
     mild = `value >= mild_threshold`).
   - **gaussian** — `mean ∈ target_mean` AND `variance <= max_variance`.
   - **boolean** — `rate >= min_rate` (or `<= max_rate`).
   - **count** / **duration** — `mean ∈ target_band` (and optional
     `min_streak_days` for duration).
5. Status: `good_enough` if all rules pass, else `not_yet`.
6. Always populate `reasons` with the actual computed numbers — the user reads
   the report, the report must show its work.

Retired states are skipped entirely.

### Schema versioning

If a `StateDef.history` exists, observations are filtered to those on/after the
*current* version's start date (most recent `History:` entry's date). Older
observations are excluded from evaluation but remain in the file. This is the
default policy; PRD §18 leaves a richer mapping policy open.

### Per-problem aggregation

Default `aggregation: all_good_enough`:
- If any state signal is `insufficient_data` → problem signal is
  `insufficient_data`.
- Else if all are `good_enough` → `good_enough`.
- Else → `not_yet`.

Retired states are dropped from aggregation. Graduated problems are still
evaluated (so the user can see if they regress) but flagged separately in the
report.

---

## Report — `Scripts/report.py`

Writes `Reviews/YYYY-MM-DD Stability Report.md`:

```markdown
# Stability Report — 2026-04-29

_Generated 2026-04-29 by Scripts/evaluate_cli.py. Signals, not verdicts._

## Active problems

| Problem | Signal | States |
|---|---|---|
| Energy Problem | not-yet | headache: good-enough, sleep_quality: not-yet, movement_efficiency: insufficient-data |

## Per-state signals

| State | Type | Signal | Obs (window) | Reasons |
|---|---|---|---|---|
| headache | ordinal | good-enough | 62 / 55d | severe_count 0 <= 0; mild_ratio 0.08 <= 0.10 |
| sleep_quality | ordinal | not-yet | 60 / 55d | mild_ratio 0.18 > 0.10 |
| movement_efficiency | gaussian | insufficient-data | 14 / 60 needed | window has too few observations |

## Graduated problems (regression watch)

| Problem | Graduated | Current Signal |
|---|---|---|

## Warnings

- DailyLogs/2026/04/2026-04-15.md:14 — could not parse `sleep_quality:: ok` as ordinal
```

Stdout summary: one line per problem, e.g.

```
Energy Problem: not-yet  (1 good, 1 not-yet, 1 insufficient)  →  Reviews/2026-04-29 Stability Report.md
```

Idempotent: re-running on the same day overwrites the same file.

---

## CLI — `Scripts/evaluate_cli.py`

```
python Scripts/evaluate_cli.py [--vault PATH] [--today YYYY-MM-DD] [--problem NAME]
```

- `--vault` defaults to the parent directory of the script.
- `--today` defaults to the system date (PRD says manual/on-demand; `--today`
  enables deterministic tests).
- `--problem` filters output (per-state evaluation still runs for all, but the
  report only includes the named problem).

Exit code is always 0 unless a parse exception escapes; signals never affect
exit code (signals are not verdicts — including not turning into a CI signal).

---

## Templates — `Templates/`

Three plain markdown templates, no Templater logic required:
- `Templates/Daily Log.md` — `## Morning Slot` + `## Evening Slot` skeletons
  with `state_name:: ` placeholders the user fills in. (Templater can wire up
  the date title later — the toolkit doesn't care.)
- `Templates/State.md` — full frontmatter skeleton with all criteria keys
  commented out, plus `Levels: / Criteria: / Notes: / History:` sections.
- `Templates/Problem.md` — frontmatter skeleton, `Goal: / States: / Success
  Criteria: / Notes:` sections.

Templates are documentation; the parser does not read them.

---

## Project layout (concrete files to create)

```
HumanSystem/
├── PRD.md                              (already exists, copy of human_system_obsidian.md)
├── Scripts/
│   ├── __init__.py
│   ├── model.py
│   ├── parser.py
│   ├── evaluate.py
│   ├── report.py
│   ├── evaluate_cli.py
│   ├── requirements.txt                (single line: PyYAML>=6)
│   └── tests/
│       ├── __init__.py
│       ├── fixtures/vault/             (small toy vault)
│       ├── test_parser.py
│       ├── test_evaluate_ordinal.py
│       ├── test_evaluate_gaussian.py
│       ├── test_evaluate_boolean.py
│       ├── test_aggregation.py
│       └── test_end_to_end.py
├── Templates/
│   ├── Daily Log.md
│   ├── State.md
│   └── Problem.md
├── States/                             (user-authored, empty initially)
├── Problems/
├── Slots/
├── DailyLogs/
├── Reviews/
└── Dashboards/                         (user-authored later)
```

`Scripts/` is self-contained: a user can `cd HumanSystem && pip install -r
Scripts/requirements.txt && python Scripts/evaluate_cli.py`.

---

## Testing strategy

- **Parser tests** — feed canned daily-log strings, assert observations and
  warnings. Cover: well-formed line, malformed line, line outside slot, mixed
  free text, frontmatter ignored, empty file.
- **Evaluator tests** — one file per measurement type. Cover: insufficient
  data, good-enough boundary, not-yet boundary, retired state skipped,
  schema-version cutoff.
- **Aggregation tests** — combinations of state signals → problem signal.
- **End-to-end test** — `tests/fixtures/vault/` is a 30-day toy vault; the test
  asserts the generated report matches a snapshot.

Run with `python -m unittest discover Scripts/tests` (no pytest dependency,
keeps "stdlib + PyYAML only" intact).

---

## Verification (how to test the implementation end-to-end)

1. `cd HumanSystem && pip install -r Scripts/requirements.txt`.
2. `python -m unittest discover Scripts/tests` — all green.
3. Hand-author one `States/headache.md`, one `Problems/Energy Problem.md`, one
   `Slots/Morning Checkin.md`, and a handful of daily logs across recent dates.
4. `python Scripts/evaluate_cli.py --today 2026-04-29` — verify
   `Reviews/2026-04-29 Stability Report.md` appears and contents match
   expectations.
5. Introduce a malformed line in one daily log, re-run, confirm the warning
   appears in the report and other observations still parse.
6. Set `status: retired` on the headache state, re-run, confirm it disappears
   from per-state and from problem aggregation.

---

## Critical files to create

All under `HumanSystem/Scripts/`:
- `model.py` — dataclasses above
- `parser.py` — vault walker + markdown extraction
- `evaluate.py` — five per-type evaluators + aggregator
- `report.py` — markdown report writer
- `evaluate_cli.py` — argparse entry point, glue
- `requirements.txt`
- `tests/` per the testing section

Plus three template files under `HumanSystem/Templates/`.

---

## Out of scope (explicitly deferred to PRD §18)

- Schema-version mapping policies beyond "skip pre-version data".
- Whether revived problems branch their history.
- Richer per-problem aggregations (weighted, OR, custom).
- Dashboards/Dataview queries — user-authored, not shipped by the toolkit.
- Any web renderer (PRD §17).
