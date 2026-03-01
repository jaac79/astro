# Medini Specialist Output Format (YAML)

All Medini specialist agents MUST return their analysis as a YAML block in this exact schema.
Return structured data, NOT narrative. The worldastro orchestrator writes the narrative.

Each specialist analyzes the data purely from their analytical focus.
The orchestrator handles cross-specialist synthesis, contradiction resolution, and bias checks.

---

## Schema

```yaml
system: "<Medini-Transit | Medini-Eclipse | Medini-Ingress | Medini-Cycles | Medini-Country | Medini-Financial>"
query: "<Neutral restatement of the question — strip emotional framing>"

# --- METADATA ---
# Context-specific metadata depending on the specialist type.

metadata:
  # Medini-Transit: slow planet summary
  # Medini-Eclipse: eclipse details
  # Medini-Ingress: year_lord, ingress_lagna, ingress_date
  # Medini-Cycles: current_cycle, conjunction_year, element, era
  # Medini-Country: country, foundation_date, lagna, current_dasha
  # Medini-Financial: analysis_period, key_sectors

# --- CORE FINDINGS ---
# Group every finding by what it does: contributes, negates, or is mixed/neutral.

favorable:
  - planet: "<graha name>"
    sign: "<current sign (for transits) or natal sign (for foundation chart)>"
    house: <house number in foundation chart, if applicable>
    dignity: "<exalted | moolatrikona | own | friend | neutral | enemy | debilitated>"
    domain: "<Political Stability | Economy | Natural Events | Military/Conflict | Public Health | Foreign Relations | Markets/Finance>"
    affected_countries: [<list of countries affected, from country_sign_rulerships.yaml>]
    mechanism: "<1-2 sentence explanation of WHY this is favorable — cite the specific rule>"
    strength: "<HIGH | MED | LOW>"
    rule_ref: "<knowledgebase reference: file, section, classical source>"

unfavorable:
  - planet: "<graha name>"
    sign: "<sign>"
    house: <house number, if applicable>
    dignity: "<dignity>"
    domain: "<domain>"
    affected_countries: [<list>]
    mechanism: "<WHY this is unfavorable>"
    strength: "<HIGH | MED | LOW>"
    rule_ref: "<reference>"

mixed:
  - planet: "<graha name>"
    sign: "<sign>"
    house: <house number, if applicable>
    dignity: "<dignity>"
    domain: "<domain>"
    affected_countries: [<list>]
    contributes: "<what positive effect>"
    negates: "<what negative effect>"
    net_lean: "<SLIGHTLY_FAVORABLE | NEUTRAL | SLIGHTLY_UNFAVORABLE>"
    mechanism: "<WHY this is mixed — explain the conflict>"
    strength: "<HIGH | MED | LOW>"
    rule_ref: "<reference>"

# --- ECLIPSE FINDINGS (Medini-Eclipse only) ---
# Eclipse-specific fields when analyzing eclipse impact.

eclipse_findings:
  - eclipse_type: "<solar_total | solar_partial | solar_annular | lunar_total | lunar_partial | lunar_penumbral>"
    date: "<YYYY-MM-DD>"
    sign: "<sidereal sign>"
    nakshatra: "<nakshatra name>"
    duration_hours: <decimal hours>
    manifestation_window:
      start: "<YYYY-MM-DD>"
      end: "<YYYY-MM-DD>"
    affected_countries: [<list>]
    domain: "<domain>"
    mechanism: "<classical rule applied>"
    rule_ref: "<eclipse_rules.yaml section>"

# --- DASHA ASSESSMENT (Medini-Country only) ---
# Cover the country's active dasha periods.

dasha:
  - level: "<Mahadasha | Antardasha | Pratyantardasha>"
    lord: "<planet>"
    sign: "<lord's natal sign>"
    house: <lord's natal house in foundation chart>
    dignity: "<dignity>"
    houses_owned: [<list of houses owned>]
    domain_activation: [<list of domains this lord activates>]
    theme: "<1-line summary of what this period activates for the country>"
    start: "<YYYY-MM-DD>"
    end: "<YYYY-MM-DD>"

# --- TIMING WINDOWS ---
# Specific date ranges where a mundane theme intensifies.

timing:
  - label: "<descriptive name>"
    start: "<YYYY-MM-DD>"
    end: "<YYYY-MM-DD>"
    domain: "<domain>"
    nature: "<FAVORABLE | CAUTION>"
    trigger: "<what transit, eclipse, or dasha shift causes this window>"
    affected_countries: [<list>]

# --- CYCLE ASSESSMENT (Medini-Cycles only) ---

cycle:
  - cycle_name: "<Saturn-Jupiter | Saturn-Rahu | Jupiter-Rahu | Saturn Return | etc.>"
    current_phase: "<early | middle | late | approaching>"
    last_event_date: "<YYYY-MM-DD>"
    next_event_date: "<YYYY-MM-DD>"
    sign: "<sign of last conjunction/event>"
    element: "<fire | earth | air | water>"
    historical_parallel: "<brief description of what happened during a similar phase>"
    domain_impact: [<list of domains affected>]
    mechanism: "<classical rule>"

# --- COMMODITY/SECTOR (Medini-Financial only) ---

commodities:
  - planet: "<ruling planet>"
    commodity_or_sector: "<gold | silver | oil | technology | etc.>"
    price_tendency: "<UP | DOWN | VOLATILE>"
    mechanism: "<why — planet dignity, transit, aspect>"
    timing: "<when the tendency peaks>"
    strength: "<HIGH | MED | LOW>"

# --- CONFIDENCE ---

confidence:
  level: "<HIGH | MODERATE | LOW>"
  data_available: [<list of data sources used>]
  data_missing: [<list of data that was unavailable>]
  key_assumption: "<single most important assumption>"
  limitations: "<what this specialist cannot assess that others might>"
```

---

## Field Rules

### Strength
- **HIGH**: Planet in own/exalted/moolatrikona, multiple reinforcing factors, historical precedent
- **MED**: Planet in friend/neutral sign, single supporting factor
- **LOW**: Planet in enemy/debilitated sign, or finding rests on thin evidence

### Domain Values
Use exactly one of: `Political Stability`, `Economy`, `Natural Events`, `Military/Conflict`, `Public Health`, `Foreign Relations`, `Markets/Finance`

### Affected Countries
Always populated from `medini_kb/reference/country_sign_rulerships.yaml`. If no country mapping applies (global effect), use `["global"]`.

### Mixed Findings
Use `mixed` when a transit genuinely helps one domain but hurts another, or helps one set of countries but hurts another. The `net_lean` field gives the orchestrator a direction.

### Omit Empty Sections
If a section has no entries (e.g., no eclipse_findings for a transit specialist), omit the section key entirely.

### No Narrative
The `mechanism` field is for concise factual explanation, not storytelling. State the rule, cite the reference, and stop.
