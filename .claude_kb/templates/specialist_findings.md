# Standard Specialist Output Format (YAML)

All specialist agents MUST return their analysis as a YAML block in this exact schema.
Return structured data, NOT narrative. The orchestrator writes the narrative.

Each specialist analyzes the chart purely from their tradition's perspective.
The orchestrator handles cross-system synthesis, contradiction resolution, and bias checks.

---

## Schema

```yaml
system: "<Parashari | Jaimini | KP | Nadi | Tajaka | Prashna | Muhurta>"
query: "<Neutral restatement of the question — strip emotional framing>"

# --- CORE FINDINGS ---
# Group every finding by what it does: contributes, negates, or is mixed/neutral.

favorable:
  - planet: "<graha name>"
    house: <number>                  # house occupied (1-12)
    dignity: "<exalted | moolatrikona | own | friend | neutral | enemy | debilitated>"
    role: "<yogakaraka | functional_benefic | functional_malefic | neutral | maraka | badhaka>"
    houses_owned: [<list of houses owned>]
    mechanism: "<1-2 sentence explanation of WHY this is favorable — cite the specific rule or combination>"
    strength: "<HIGH | MED | LOW>"
    rule_ref: "<knowledgebase reference: table, chapter, page>"

unfavorable:
  - planet: "<graha name>"
    house: <number>
    dignity: "<dignity>"
    role: "<role>"
    houses_owned: [<list>]
    mechanism: "<WHY this is unfavorable>"
    strength: "<HIGH | MED | LOW>"
    rule_ref: "<reference>"

mixed:
  - planet: "<graha name>"
    house: <number>
    dignity: "<dignity>"
    role: "<role>"
    houses_owned: [<list>]
    contributes: "<what positive effect this planet produces>"
    negates: "<what negative effect this planet produces>"
    net_lean: "<SLIGHTLY_FAVORABLE | NEUTRAL | SLIGHTLY_UNFAVORABLE>"
    mechanism: "<WHY this is mixed — explain the conflict>"
    strength: "<HIGH | MED | LOW>"
    rule_ref: "<reference>"

# --- YOGAS ---
# List every yoga relevant to the query that this tradition identifies.

yogas:
  - name: "<yoga name>"
    planets_involved: [<list of planets>]
    houses_involved: [<list of houses>]
    status: "<FULLY_FORMED | FORMED_BUT_WEAKENED | BROKEN>"
    effect: "<what this yoga produces when active>"
    weakening_factors: "<what diminishes it, if any — omit if FULLY_FORMED>"
    rule_ref: "<reference>"

# --- DASHA ASSESSMENT ---
# Cover the active dasha period and relevant sub-periods from THIS tradition's dasha system.

dasha:
  - system: "<Vimshottari | Yogini | Chara | Narayana | Mudda | Parivritti>"
    current_period: "<e.g., Ra-Me or Simham>"
    period_lord: "<planet or rasi>"
    lord_dignity: "<dignity, including neecha_bhanga if applicable>"
    lord_house: <house number>
    lord_role: "<functional nature>"
    theme: "<1-line summary of what this period activates>"
    supports_query: "<YES | NO | PARTIAL>"
    confidence: "<HIGH | MED | LOW>"

# --- TIMING WINDOWS ---
# Specific date ranges where the query theme intensifies — favorable or cautionary.

timing:
  - label: "<descriptive name>"
    start: "<YYYY-MM-DD>"
    end: "<YYYY-MM-DD>"
    nature: "<FAVORABLE | CAUTION>"
    trigger: "<what dasha shift, transit, or activation causes this window>"

# --- REMEDIALS ---
# System-specific remedial measures. Only include if the tradition prescribes them.

remedials:
  - remedy: "<specific remedy>"
    type: "<mantra | gem | charity | behavioral | ritual>"
    target_planet: "<which graha>"
    target_issue: "<what problem this addresses>"
    when: "<timing guidance>"
    duration: "<how long>"
    basis: "<classical text/chapter reference>"

# --- CONFIDENCE ---

confidence:
  level: "<HIGH | MODERATE | LOW>"
  data_available: [<list of data sources used>]
  data_missing: [<list of data that was unavailable>]
  key_assumption: "<single most important assumption>"
  limitations: "<what this system cannot assess that others might>"
```

---

## Field Rules

### Strength
- **HIGH**: Planet in own/exalted/moolatrikona, yogakaraka, strong by Shadbala/AV, or multiple reinforcing factors
- **MED**: Planet in friend/neutral sign, moderate dignity, single supporting factor
- **LOW**: Planet in enemy/debilitated sign, combust, weak by Shadbala/AV, or finding rests on thin evidence

### Dignity values
Use exact terms: `exalted`, `moolatrikona`, `own`, `friend`, `neutral`, `enemy`, `debilitated`
Append modifiers as needed: `debilitated_neecha_bhanga`, `exalted_retrograde`, `own_combust`

### Role values
Use: `yogakaraka`, `functional_benefic`, `functional_malefic`, `neutral`, `maraka`, `badhaka`
A planet can have multiple roles — list the primary one, note others in mechanism.

### Mixed findings
Use the `mixed` section when a planet genuinely contributes AND negates. Do NOT force planets into favorable/unfavorable when the picture is conflicted. The `net_lean` field gives the orchestrator a direction without hiding the conflict.

### Omit empty sections
If a section has no entries (e.g., no remedials, no timing windows), omit the section key entirely rather than returning an empty list.

### No narrative
The `mechanism` field is for concise factual explanation, not storytelling. State the rule, cite the reference, and stop.
