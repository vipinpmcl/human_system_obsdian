# Human System — Obsidian-First PRD (v2)

## Product Name
**Human System (Obsidian Edition)**

---

# 1. Purpose

Human System is an Obsidian-first personal observation framework for tracking human states over time and determining when a real-life problem becomes stable enough to stop thinking about.

It exists to answer one question:

> "Is this problem stable enough that I can stop tracking it and move on?"

Unlike habit trackers, analytics dashboards, or productivity systems, Human System is not built for optimization. It is a structured reflection and *sufficiency* framework: tracking ends when enough understanding exists.

Persistence is markdown inside Obsidian. Evaluation is performed by lightweight Python scripts that read the markdown and emit signals — never verdicts.

---

# 2. Philosophy & Non-Goals

## 2.1 Principles

1. **Sufficiency over optimization.** The goal is to stop tracking, not to perfect a metric.
2. **Human judgment is final.** Scripts emit signals; humans graduate problems.
3. **Local-first.** The vault is the source of truth. The user owns the data and is responsible for its backup.
4. **Markdown-native.** All persistence is human-readable text. Data must remain legible in 5–10 years without the original tooling.
5. **Reflective, not reactive.** The system encourages clarity and notes, not real-time feedback loops.
6. **Lapse-tolerant.** Pausing logging is a normal lifecycle state, not a failure.

## 2.2 Non-Goals

Human System is **not**:
- a habit tracker
- an analytics or quantified-self dashboard
- a productivity or goal-setting tool
- a journaling app (though notes are welcome)
- a real-time feedback or coaching system
- a multi-user or social platform
- an optimization or progress-maximization engine

Drift toward any of the above should be treated as a scope violation.

> Final design principle:
> simple enough to trust, lightweight enough to sustain, meaningful enough to matter.

---

# 3. Personas & Use Cases

## 3.1 Persona — *The Reflective Practitioner*

A self-aware individual with intermittent concerns (sleep, energy, focus, mood) who wants to:
- understand whether a concern is real and persistent
- decide when to stop worrying about it
- avoid building yet another optimization treadmill

Comfortable with markdown and Obsidian. Not a quantified-self enthusiast.

## 3.2 Archetypal Use Cases

1. **Open a new problem.** Notice a recurring issue → define it as a Problem → identify its States → start logging.
2. **Graduate a stable problem.** Review evaluation signals → confirm with personal judgment → archive the Problem with a written *why*.
3. **Revive a regressed problem.** A graduated problem returns → reopen without losing prior history → resume logging.
4. **Pause gracefully.** Life intervenes → logging stops for weeks → resume without guilt or data corruption.

---

# 4. Glossary

| Term | Canonical meaning |
|---|---|
| **Observation** | A single recorded value for a single state at a single point in time. |
| **State** | A measurable atomic signal (e.g. headache severity, sleep quality). Owns observations and definition. |
| **Problem** | A semantic grouping of states that names a real-life concern. Owns intent and success criteria, not observations. |
| **Slot** | A recurring observation context (e.g. Morning Check-in). The Slot *note* is the definition; a slot section in a daily log is an *instance*. |
| **Daily Log** | One markdown file per day containing slot instances and reflective notes. |
| **Window** | A rolling time range used for evaluation (e.g. last 55 days). |
| **Criterion** | One rule contributing to a state's "good enough" assessment. |
| **Good Enough** | A *signal* (not a verdict) indicating a state's criteria are currently satisfied. |
| **Stability** | A property of a state across a window: all criteria satisfied with sufficient observations. |
| **Graduation** | The human act of retiring an active Problem after deciding stability is sufficient. |
| **Revival** | Reopening a graduated Problem after regression, preserving its prior history. |
| **Insufficient Data** | A first-class evaluation outcome when a window has too few observations to judge. |

---

# 5. Conceptual Model

The four entities, ordered top-down by intent:

```
Problem ──groups──▶ State ──observed-via──▶ Slot ──instantiated-in──▶ Daily Log
                                                                       │
                                                                       └──▶ Observation
```

## 5.1 Problem

A Problem is a semantic page describing a real-life concern. It owns:
- a written goal
- links to its States
- success criteria in prose
- lifecycle status (active / graduated / revived)

A Problem does **not** own observations.

## 5.2 State

A State is the atomic measurable unit. It owns:
- measurement type (see §10.2)
- definition (levels, units, semantics)
- criteria (per-state evaluation rules)
- observation history (via daily logs)
- a *primary* Problem (for organization) and optionally additional related Problems

A State may belong to multiple Problems but has exactly one primary Problem.

## 5.3 Slot

A Slot defines a recurring observation context: a name, a target time, and the states expected. The Slot note is the *definition*. A heading in a daily log is an *instance* of that slot for that day.

A Slot owns no data. It is organizational only.

## 5.4 Observation

An Observation is one recorded value for one state at one moment, captured inside a slot instance in a daily log.

---

# 6. Entity Lifecycles

## 6.1 Observation Lifecycle

- **create** — recorded inline in a daily log slot section.
- **modify** — edit in place. Corrections are overwrites; the user may add an inline note explaining the change. No mandatory audit trail.
- **missing** — if no value is recorded, the observation is *unknown*, never *zero*. Evaluation must distinguish.
- **retire** — never. Observations are immutable history.

## 6.2 State Lifecycle

- **create** — add a state note under `States/` with definition and criteria.
- **active** — observations accumulate via daily logs.
- **modify** — non-trivial changes (level redefinition, type change, criteria change) require a versioning note (§16).
- **retire** — set frontmatter `status: retired`. Historical observations remain queryable; retired states are excluded from evaluation.
- **revive** — flip status back to active.

## 6.3 Problem Lifecycle

- **create** — add a problem note under `Problems/`, linked to its States, with a written goal.
- **active** — states are observed; evaluation produces signals.
- **graduated** — the user decides stability is sufficient. The user **must** write a one-paragraph *why graduated* note. The note then moves to `Problems/Graduated/` or gains `status: graduated`.
- **revived** — flip status back to active. The prior *why graduated* note is preserved as historical record.

A Problem is never deleted.

## 6.4 Evaluation Lifecycle

- **trigger** — manual, on-demand. Typically run during weekly review.
- **input** — daily log observations and state criteria.
- **output** — per-state signals (`good-enough`, `not-yet`, `insufficient-data`) and per-problem aggregations.
- **authority** — signals never graduate a problem. Only the user does. This boundary is structural: evaluation output uses the word "signal", never "verdict".

---

# 7. Vault Architecture

```
HumanSystem/
├── DailyLogs/YYYY/MM/YYYY-MM-DD.md     [required]
├── States/                              [required]
├── Problems/                            [required]
│   └── Graduated/                       [conventional]
├── Slots/                               [required]
├── Templates/                           [conventional]
├── Dashboards/                          [conventional]
├── Scripts/                             [conventional]
├── Reviews/                             [conventional]
└── PRD.md                               [conventional]
```

**Required** folders define the data contract — evaluation depends on them. **Conventional** folders are organizational and may be adapted without breaking evaluation.

---

# 8. Note Structures

## 8.1 State Note

`States/headache.md`:

```markdown
---
type: ordinal
status: active
primary_problem: "Energy Problem"
related_problems: []
schema_version: 1
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
```

## 8.2 Problem Note

`Problems/Energy Problem.md`:

```markdown
---
status: active
created: 2026-04-01
---

# Energy Problem

Goal:
Reach stable energy levels without daily concern.

States:
- [[headache]]
- [[sleep_quality]]
- [[movement_efficiency]]

Success Criteria:
All linked states stable, with no severe headache events in 8 weeks.

Notes:
Energy feels stable when afternoon crashes disappear.
```

When graduated, append:

```markdown
Why Graduated (2026-09-12):
Three months without afternoon crashes. Sleep stabilized at 7h+. Headaches rare and mild. I no longer think about this daily.
```

## 8.3 Slot Note

`Slots/Morning Checkin.md`:

```markdown
---
time: "09:00"
---

# Morning Checkin

States:
- [[sleep_quality]]
- [[headache]]
- [[weight]]
```

## 8.4 Daily Log Note

`DailyLogs/2026/04/2026-04-29.md`:

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

The `key:: value` lines are parser-visible. Free-text notes are human-only and are ignored by evaluation. See §11 for the data-model contract.

---

# 9. Logging Workflow

Daily:
1. Open today's daily note (auto-created from template).
2. Fill the Morning Slot section.
3. Fill the Evening Slot section.
4. Optionally add reflective notes.

Weekly:
1. Run the evaluation script.
2. Review per-state and per-problem signals.
3. For any problem that *feels* stable and shows good-enough signals, decide whether to graduate.
4. Record graduations or revivals.

Target: under 30 seconds per slot. The system should never feel heavy.

Pausing is acceptable. Resume by opening today's daily log; missed days remain blank.

---

# 10. Evaluation Model

## 10.1 Authority & Triggers

- Evaluation is **manual and on-demand**. The user invokes it.
- Evaluation produces **signals**, never verdicts. Graduation is a human act.
- Output uses the word `signal` to reinforce the boundary.

## 10.2 Measurement Types

| Type | Examples | Evaluation paradigm |
|---|---|---|
| **ordinal** | headache (0/1/2), focus quality | level-frequency rules |
| **gaussian** | weight, sleep duration | mean / variance over a window |
| **boolean** | meditated today | rate over a window |
| **count** | caffeine cups | bounded mean over a window |
| **duration** | minutes meditated | bounded mean / streak |

Free-text notes are not a measurement type; they are reflective context only.

## 10.3 "Good Enough" per Type

The PRD defines categories; concrete thresholds are chosen per state by the user.

- **Ordinal** — no values above a stated threshold inside the window; mild-frequency under a stated ratio; minimum-observation count met.
- **Gaussian** — posterior mean within a target range; variance below a stated bound; minimum-observation count met.
- **Boolean** — rate above (or below) a stated threshold; minimum-observation count met.
- **Count** — mean within a stated band; minimum-observation count met.
- **Duration** — mean within a stated band, or a stated streak length, depending on the state's intent.

## 10.4 Window & Minimum-Observation Semantics

- A **window** is a rolling number of days ending today.
- **Minimum observations** is a count of *non-missing* values inside the window.
- A criterion that lacks enough observations returns `insufficient-data`. It does **not** silently pass or fail.

## 10.5 Missing Data

- A skipped slot or skipped day is **unknown**, not zero.
- Unknown values are excluded from rate, mean, and frequency calculations.
- Evaluation surfaces the observation count alongside every signal so the user can judge confidence.

---

# 11. Required Obsidian Capabilities (tool-agnostic)

The PRD specifies *capabilities*, not specific plugins. Any tool providing these is acceptable.

- **Markdown editing** with frontmatter support.
- **Backlinks** between notes (Problem ↔ State ↔ Slot).
- **Inline metadata querying** — extracting `key:: value` pairs from daily logs.
- **Templating** for daily notes and slot sections.
- **Periodic note creation** for daily logs.

The data contract is plugin-independent: the canonical form of an observation is a `key:: value` line inside a slot heading inside a daily log file dated `YYYY-MM-DD.md`. Frontmatter is reserved for note-level metadata, not observations.

---

# 12. Dashboards & Reviews

Dashboards are **review-oriented**, not progress-oriented. They support reflection, not optimization.

```
Dashboards/
├── Active Problems.md
├── Stability Report.md
└── Weekly Review.md
```

A dashboard query is illustrative, not normative:

```dataview
TABLE headache, sleep_quality
FROM "DailyLogs"
SORT file.day DESC
LIMIT 30
```

Review cadence: weekly is the recommended rhythm. Skipping a review is acceptable.

---

# 13. Privacy & Trust Posture

- The vault contains intimate signals (health, mood, relationships). It is treated as sensitive data.
- **Local-first** is a deliberate privacy stance. No cloud sync is required by the system.
- The user is responsible for backup and for any sync mechanism they choose.
- Recommended plugins (Dataview, Templater, Meta Bind) execute code against the vault. The plugin set is a trust surface; prefer the smallest viable set.

---

# 14. Failure Modes

| Failure mode | Expected behavior |
|---|---|
| Missing days / pauses | Treated as unknown; evaluation reports `insufficient-data` rather than failing. |
| Malformed daily log line | Parser skips the line, surfaces a warning in the next evaluation. |
| State definition change | Versioning note in the state file (§16); historical data flagged as pre-version-N. |
| Plugin breakage | Markdown remains readable; data is not lost. Evaluation may stall until the plugin is restored or replaced. |
| Multi-device merge conflict | Markdown conflict markers are visible to the user; resolution is manual. |
| Vault corruption | Restored from user-controlled backup. The system does not attempt automated recovery. |
| User abandonment | The vault remains a static record. Resuming requires no migration. |
| Long-term context loss | Mitigated by the *why graduated* note required at problem graduation. |

---

# 15. Success Criteria

The system succeeds, from the user's perspective, when:

- Logging takes under 30 seconds per slot for months.
- The user has graduated at least one Problem with a written *why*.
- The user has paused and resumed without losing or doubting the data.
- The vault remains readable and meaningful one year after creation.
- The user does not feel the system has become an optimization treadmill.

These are qualitative behavioral markers, not quantitative KPIs.

---

# 16. Versioning & Schema Evolution

- The PRD itself is versioned (`v1`, `v2`, …).
- Each State note carries `schema_version` in its frontmatter. When a state's levels, type, or criteria change materially, increment the version and append a `History:` block describing the change and its date.
- Daily log observations are never rewritten when a state's schema changes. Evaluation must understand the schema-version boundary and either skip pre-change data or apply a documented mapping.
- New measurement types may be added; existing types must not change semantics.

---

# 17. Migration Path (future renderer / web layer)

If a future renderer or web app is built:

- **Markdown remains the single source of truth.** The web layer is a read-only renderer over the vault.
- **No schema fork.** The web layer must consume the same `key:: value` data contract; no parallel data model.
- **Evaluation parity.** Web-side evaluation must produce the same signals as the local Python scripts for the same vault state.
- **Local-first remains the default.** Any web layer is opt-in and does not require uploading vault data.

This boundary protects the system from quietly becoming a SaaS optimization tool.

---

# 18. Open Questions & Long-Term Ideas

Open questions to resolve in future revisions:
- A canonical mapping policy when state schema versions change mid-history.
- Whether revived problems should branch their history or continue it linearly.
- Whether per-problem aggregation is plain AND of state signals or a richer composition.

Long-term ideas (explicitly not committed):
- Local visualization app or Flask viewer.
- AI-assisted weekly summaries (must remain reflective, never prescriptive).
- Graph-based relationship discovery between problems.

---

# Appendix A — Worked Example

Defining and graduating an *Energy Problem*:

1. Create `Problems/Energy Problem.md` with goal and links.
2. Create `States/headache.md`, `States/sleep_quality.md`, `States/movement_efficiency.md`, each with type and criteria.
3. Create `Slots/Morning Checkin.md` and `Slots/Evening Reflection.md`.
4. Log daily for 8–12 weeks.
5. Run the evaluation script weekly. Watch signals shift from `not-yet` / `insufficient-data` to `good-enough`.
6. When all three states show `good-enough` for several consecutive weeks *and* the user no longer thinks about energy daily, write a *why graduated* paragraph and move the Problem to `Problems/Graduated/`.

---

# Appendix B — Plugin Recommendations (informative, not normative)

These plugins satisfy the capabilities in §11 in current Obsidian. They are not part of the data contract.

- **Dataview** — inline metadata queries (`key:: value`).
- **Templater** — daily note and slot templates.
- **Periodic Notes** — automatic daily-note creation.
- **Tracker** — optional charting for review.
- **Meta Bind** — optional form-style editing.

If any of these is replaced or deprecated, the markdown vault remains intact and the data contract is unaffected.
