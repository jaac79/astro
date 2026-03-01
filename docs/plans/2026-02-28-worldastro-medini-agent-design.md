# Worldastro: Medini Jyotish Agent -- Design Document

**Date:** 2026-02-28
**Status:** Approved
**Author:** Jagan Mohan + Claude

## 1. Overview

Worldastro is a Medini (mundane/world) astrology orchestrator agent, architecturally mirroring the existing astrobot agent for natal astrology. It provides country predictions, global event analysis, financial/market astrology, and long-term cycle analysis using classical Medini Jyotish principles.

**Key difference from astrobot:** Astrobot analyzes individual birth charts. Worldastro analyzes country foundation charts, solar ingress charts, eclipse charts, planetary cycles, and their impact on nations, markets, and global events.

## 2. Architecture

### 2.1 Orchestrator Pattern

Worldastro follows the same orchestrator pattern as astrobot:
- Does NOT perform deep analysis itself
- Coordinates specialist agents in parallel
- Synthesizes findings via Floodlight Scorecard
- Writes two-layer output (plain language + technical)
- Runs critic agent for QA

### 2.2 Specialist Agents

8 dedicated Medini specialist agents, all in `.claude/agents/`:

| Agent | File | Dispatch Rule | Focus |
|---|---|---|---|
| `medini-transit` | medini-transit.md | ALWAYS | Major transit analysis: Saturn, Jupiter, Rahu-Ketu through signs, planetary wars, retrograde cycles |
| `medini-eclipse` | medini-eclipse.md | When eclipse occurs in query period | Solar/lunar eclipse analysis: path, sign, nakshatra, country impact, timing of manifestation |
| `medini-ingress` | medini-ingress.md | For annual/seasonal predictions | Solar ingress (Aries/Cancer/Libra/Capricorn entry) chart: year-lord, seasonal outlook, house activation for country |
| `medini-cycles` | medini-cycles.md | For long-term trends | Saturn-Jupiter 20-year cycles, Great Mutation, element rotation, Saturn-Rahu and other major conjunctions |
| `medini-country` | medini-country.md | When specific country queried | Country foundation chart analysis: dashas, transits to national chart, ashtakavarga transit strength |
| `medini-financial` | medini-financial.md | For market/economic queries | Market cycles, commodity rulerships, sector timing, boom/bust indicators |
| `medini-critic` | medini-critic.md | ALWAYS (post-synthesis) | QA: contradictions, overreach, missing context, historical validation |
| `medini-reference` | medini-reference.md | On-demand | Knowledgebase lookup for classical Medini principles |

### 2.3 Data Flow

```
User Query (country prediction / event analysis / market timing)
    |
    v
worldastro.md (orchestrator)
    |
    +---> medini_calc.py ---> Compute ingress/eclipse/transit/panchanga/SBC charts
    |
    +---> Load country chart (world_data/<country>/foundation_chart.yaml)
    |
    +---> Dispatch specialists (parallel)
    |     +-- medini-transit (ALWAYS)
    |     +-- medini-eclipse (if eclipse in period)
    |     +-- medini-ingress (if annual/seasonal query)
    |     +-- medini-cycles (if long-term query)
    |     +-- medini-country (if specific country)
    |     +-- medini-financial (if market query)
    |
    +---> Synthesize + Floodlight Scorecard
    |
    +---> medini-critic (QA)
    |
    +---> Write reading to world_readings/<topic>/YYYY-MM-DD_<type>.md
```

## 3. Knowledgebase (`medini_kb/`)

### 3.1 Reference Files (`medini_kb/reference/`)

| File | Content | Sources |
|---|---|---|
| `country_sign_rulerships.yaml` | Rasi-to-country/region mapping (classical + modern) | B.V. Raman, Varahamihira, web research |
| `planet_mundane_significations.yaml` | Planet meanings in Medini (Sun=king/govt, Moon=public, Mars=military, etc.) | Multiple classical sources |
| `house_mundane_significations.yaml` | 12 houses in mundane charts (1st=country, 2nd=economy, 3rd=comms, 4th=agriculture, 7th=foreign relations, 10th=govt) | Varahamihira, B.V. Raman |
| `eclipse_rules.yaml` | Eclipse interpretation: sign, nakshatra, duration -> event type, affected regions, manifestation timing | Brihat Samhita + modern |
| `ingress_rules.yaml` | Solar ingress interpretation: year-lord determination, seasonal charts, planetary hour | Classical Medini texts |
| `saturn_jupiter_cycles.yaml` | 20-year conjunction cycle, element rotation, Great Mutation theory | Historical + modern |
| `commodity_rulerships.yaml` | Planet-commodity mapping (Sun=gold, Moon=silver, Mars=iron, Mercury=trade, Jupiter=banking, Saturn=oil) | B.V. Raman + modern financial astrology |
| `nakshatra_mundane.yaml` | Nakshatra-level mundane significations (Ashlesha=epidemics, Ardra=storms, etc.) | Brihat Samhita |
| `natural_events.yaml` | Rules for earthquakes, floods, droughts, storms -- planetary combinations | Varahamihira's Brihat Samhita |
| `war_conflict_rules.yaml` | Combinations for war, political upheaval, regime change | Classical texts + historical patterns |
| `scorecards.yaml` | Medini-adapted Floodlight Scorecard: weighting for mundane predictions | Custom (adapted from natal) |

### 3.2 Templates (`medini_kb/templates/`)

| Template | Use |
|---|---|
| `foundation_chart.yaml` | Schema for country/entity charts |
| `medini_specialist_findings.md` | Standard output for Medini specialists (YAML schema) |
| `annual_country_prediction.md` | Full year prediction for a country |
| `eclipse_analysis.md` | Eclipse event analysis |
| `market_outlook.md` | Financial/market reading |
| `global_transit_report.md` | Major transit impact report |
| `event_analysis.md` | Specific event analysis |
| `cycle_analysis.md` | Long-term cycle (Saturn-Jupiter) analysis |

## 4. Country Data Model (`world_data/`)

### 4.1 Directory Structure

```
world_data/
+-- india/
|   +-- foundation_chart.yaml     # Independence: Aug 15, 1947, 00:00 IST, Delhi
|   +-- republic_chart.yaml       # Republic Day: Jan 26, 1950
|   +-- alternate_charts.yaml     # Other proposed charts
|   +-- history.yaml              # Known major events with dates (for validation)
+-- usa/
|   +-- foundation_chart.yaml     # July 4, 1776 (multiple proposed times)
|   +-- history.yaml
+-- china/
+-- russia/
+-- uk/
+-- ...
```

### 4.2 Foundation Chart Schema

```yaml
entity:
  name: India
  type: nation
  foundation_event: Independence
  date: '1947-08-15'
  time: '00:00:00'
  timezone: UTC+5:30
  place:
    city: New Delhi
    latitude: 28.6139
    longitude: 77.2090
  notes: "Midnight chart. Some astrologers use other times."
  alternate_times:
    - time: '00:00:00'
      source: "Official midnight transfer of power"
    - time: '08:15:00'
      source: "Nehru's flag hoisting"
lagna:
  rasi: ...
  degree: ...
  nakshatra: ...
  pada: ...
chandra:
  rasi: ...
  degree: ...
  nakshatra: ...
  pada: ...
planetary_positions:
  surya: { rasi, degree, nakshatra, pada, retrograde, house, dignity }
  # ... all 9 grahas
vimshottari_dasha:
  balance_at_birth: { lord, remaining_years, remaining_months, remaining_days }
  sequence: [...]
house_summary:
  house_1: { rasi, planets }
  # ... all 12 houses
computed_analysis:
  functional_nature: { yogakarakas, benefics, malefics, neutrals }
  badhaka: { sign_type, sthana, rasi, lord }
  marakas: [...]
  yogas: [...]
  ashtakavarga:
    sav: { Ar: N, Ta: N, ... }  # SAV bindus per sign
    bav:
      surya: { Ar: N, Ta: N, ... }
      # ... per planet
```

### 4.3 Output Readings (`world_readings/`)

```
world_readings/
+-- india/
|   +-- 2026-03-01_annual_prediction.md
|   +-- 2026-03-01_eclipse_impact.md
+-- global/
|   +-- 2026-03-01_saturn_jupiter_cycle.md
|   +-- 2026-03-01_market_outlook.md
+-- events/
    +-- 2026-03-01_eclipse_analysis.md
```

## 5. Computation Tool (`medini_calc.py`)

### 5.1 Commands

```bash
# Solar ingress charts (Sun entering cardinal signs)
python medini_calc.py ingress --type aries --year 2026
python medini_calc.py ingress --type cancer --year 2026
python medini_calc.py ingress --type libra --year 2026
python medini_calc.py ingress --type capricorn --year 2026

# Eclipse computation
python medini_calc.py eclipse --date 2026-03-14           # Single eclipse
python medini_calc.py eclipses --year 2026                 # All eclipses in year

# Country chart (foundation chart + current transits + dashas)
python medini_calc.py country --name india

# Planetary conjunction chart
python medini_calc.py conjunction --planets saturn,jupiter --year 2020

# Current planetary positions
python medini_calc.py positions --date 2026-02-28

# Planetary war dates in a period
python medini_calc.py wars --start 2026-01-01 --end 2026-12-31

# Retrograde periods for outer planets
python medini_calc.py retrogrades --year 2026

# Sign change dates (when slow planets change signs)
python medini_calc.py sign-changes --year 2026

# Panchanga for a date/place
python medini_calc.py panchanga --date 2026-02-28 --place delhi

# Ashtakavarga for country chart
python medini_calc.py ashtakavarga --country india

# Sarvatobhadra Chakra
python medini_calc.py sbc --date 2026-02-28
```

### 5.2 Key Computations

| Computation | Swiss Ephemeris Function | Output |
|---|---|---|
| Solar ingress | `swe_solcross_ut` (Sun crossing 0/90/180/270 deg) | Full chart YAML for ingress moment at capital city |
| Eclipse chart | `swe_sol_eclipse_when_ut` / `swe_lun_eclipse_when_ut` | Eclipse type, exact time, path, sign, nakshatra, chart |
| Conjunction chart | Iterative search for minimum angular distance | Chart for exact conjunction moment |
| Country dashas | Standard Vimshottari from foundation chart Moon | Current mahadasha/antardasha/pratyantardasha |
| Planetary wars | Track inner planet angular distances < 1 deg | Winner/loser per brightness rules |
| Sign changes | Track longitude crossings for Saturn/Jupiter/Rahu | Ingress dates with charts |
| Panchanga | Moon-Sun angle (tithi), Moon's nakshatra, yoga, karana | 5-fold daily computation |
| Ashtakavarga | Standard BAV/SAV from foundation chart | Bindus per sign per planet |
| Sarvatobhadra Chakra | Map 28 nakshatras + vowels + tithis + varas to 9x9 grid | Vedha analysis from transiting planets |

### 5.3 Dependencies

- `pyswisseph` (already installed) -- astronomical engine
- `pandas` (already installed) -- data manipulation
- `pyyaml` (already installed) -- YAML I/O
- `geopy` (already installed) -- place geocoding

### 5.4 Output Format

All computations produce YAML files. Interpretive readings are Markdown (written by agents, not the calc tool). Same data separation principle as astrobot.

## 6. Worldastro Workflow (8 Steps)

### Step 1: Parse Query & Determine Scope
- Identify query type: country prediction, event analysis, market outlook, eclipse impact, cycle analysis
- Identify target: specific country, region, global, or financial market
- Identify time period: specific date, season, year, multi-year cycle

### Step 2: Compute Required Data
Run `medini_calc.py` for missing data:
- ALWAYS: current planetary positions (`positions`)
- If country query: foundation chart + transits + dashas + ashtakavarga (`country`, `ashtakavarga`)
- If annual: solar ingress chart for relevant capital (`ingress --type aries`)
- If seasonal: seasonal ingress (`ingress --type cancer/libra/capricorn`)
- If eclipse: eclipse chart (`eclipse`)
- If cycle: conjunction chart (`conjunction`)
- If event: panchanga + SBC for event date (`panchanga`, `sbc`)

### Step 3: Build Pre-Analysis Worksheet (Medini Version)
- **Part A**: Slow Planet Transit Table (Saturn, Jupiter, Rahu-Ketu -- current signs, degrees, upcoming sign changes)
- **Part B**: Eclipse Calendar (all eclipses in query period with sign, nakshatra, type)
- **Part C**: Country Dasha State (if country query -- mahadasha/antardasha/pratyantardasha)
- **Part D**: Ashtakavarga Transit Strength (SAV in currently transited signs)
- **Part E**: Consistency Lock Checklist

### Step 4: Dispatch to Specialists (Parallel)
Dispatch rule -- consult every specialist whose data is available:

| Specialist | Dispatch When |
|---|---|
| medini-transit | ALWAYS (always has planetary positions) |
| medini-eclipse | Eclipse occurs in query period |
| medini-ingress | Annual or seasonal query |
| medini-cycles | Long-term trend query or Saturn-Jupiter conjunction in period |
| medini-country | Specific country queried AND foundation chart exists |
| medini-financial | Market/economic/commodity query |

Each specialist receives:
1. Neutrally-framed query (emotional language stripped)
2. All relevant computed data (positions, charts, dashas)
3. Pre-Analysis Worksheet

Specialists return YAML per `medini_specialist_findings.md` schema.

### Step 5: Collect & Synthesize
- Wait for all specialist responses
- Merge findings (favorable/unfavorable/mixed across specialists)
- Deduplicate: same finding from multiple specialists -> add `confirmed_by` field
- Cross-check against Pre-Analysis Worksheet

### Step 6: Build Floodlight Scorecard (Medini Version)
Domains (instead of natal life-areas):

| Domain | What It Covers |
|---|---|
| Political Stability | Government strength, leadership changes, elections |
| Economy | GDP growth, inflation, trade, currency |
| Natural Events | Earthquakes, floods, droughts, storms, epidemics |
| Military/Conflict | Wars, border tensions, internal security |
| Public Health | Disease outbreaks, healthcare, public welfare |
| Foreign Relations | Diplomacy, treaties, international standing |
| Markets/Finance | Stock markets, commodities, banking |

Scoring:
- Base weight (1-5) per finding based on planetary dignity and classical authority
- Modifiers for transit strength (ashtakavarga SAV), eclipse proximity, dasha alignment
- Compute: FAV_TOTAL, UNFAV_TOTAL, NET, MARGIN, Confidence per domain

### Step 7: Write Reading
- Select template from `medini_kb/templates/`
- Two-layer output (mandatory for every section):
  - Layer 1: Plain language (no jyotish terms, accessible to general audience)
  - "Why this matters now" bridge in blockquote
  - Layer 2: Technical basis in collapsible `<details>` block
- Plain narrative EXPLAINS the scorecard verdict
- Save to `world_readings/<topic>/YYYY-MM-DD_<type>.md`

### Step 8: Critic Review
- Dispatch `medini-critic` with: completed reading + all source data + worksheet
- Critic returns structured issue list (CRITICAL/WARNING/INFO)
- If CRITICAL: fix and re-run critic (max 2 loops)
- If only WARNING/INFO: append "Quality Review" note to reading

## 7. Anti-Bias Rules

All astrobot anti-bias rules apply (User-Frame Quarantine, Scorecard-First Gate, Steel-Man Rule, Classification Lock, Reground Checkpoint), plus Medini-specific additions:

1. **No political bias** -- Predictions about governments based on chart analysis, not political views. State chart indicators neutrally.
2. **Probability language** -- Use "the chart indicates tendency toward" not "X will happen." Medini predictions are tendencies, not certainties.
3. **Historical validation** -- Where possible, cite past instances of similar configurations and what actually happened. Ground predictions in precedent.
4. **Multiple chart consideration** -- For countries with disputed foundation charts, analyze all major candidates and note divergences. Flag confidence level.
5. **No sensationalism** -- Do not amplify disaster predictions for dramatic effect. Present difficult indicators with the same measured tone as favorable ones.
6. **Temporal precision** -- Be explicit about timing uncertainty. "Q2 2026" is better than "soon." "Within 6 months of eclipse" is better than "after the eclipse."

## 8. Honesty Mandate

Same as astrobot:
- Be direct, truthful, unvarnished -- not feel-good predictions
- Distinguish severity: a single afflicted transit != multiple converging malefic indicators
- Deliver analysis first, then implications
- Flag alarming findings prominently with timing windows
- State counter-arguments (Steel-Man Rule)

## 9. Directory Structure (Final)

```
astro/
+-- .claude/
|   +-- agents/
|   |   +-- worldastro.md           # ORCHESTRATOR (new)
|   |   +-- medini-transit.md       # Transit specialist (new)
|   |   +-- medini-eclipse.md       # Eclipse specialist (new)
|   |   +-- medini-ingress.md       # Ingress specialist (new)
|   |   +-- medini-cycles.md        # Cycles specialist (new)
|   |   +-- medini-country.md       # Country specialist (new)
|   |   +-- medini-financial.md     # Financial specialist (new)
|   |   +-- medini-critic.md        # QA specialist (new)
|   |   +-- medini-reference.md     # Reference lookup (new)
|   |   +-- [existing astrobot agents unchanged]
|   +-- agent-memory/
|       +-- worldastro/MEMORY.md    # Persistent learning notes (new)
+-- medini_kb/
|   +-- reference/                   # 11 YAML reference files (new)
|   +-- templates/                   # 8 Markdown/YAML templates (new)
+-- world_data/
|   +-- india/                       # Foundation chart + history (new)
|   +-- usa/                         # Foundation chart + history (new)
|   +-- [other countries]
+-- world_readings/
|   +-- india/                       # Country-specific readings (new)
|   +-- global/                      # Global analysis readings (new)
|   +-- events/                      # Event-specific readings (new)
+-- medini_calc.py                   # Computation tool (new)
+-- [existing natal astrology files unchanged]
```

## 10. Implementation Order

1. **Phase 1 -- Foundation**: `medini_calc.py` (positions, ingress, eclipse, panchanga)
2. **Phase 2 -- Knowledgebase**: Build `medini_kb/reference/` YAML files from web research + classical texts
3. **Phase 3 -- Country Data**: India foundation chart first, then USA, expand later
4. **Phase 4 -- Agents**: Write all 9 agent definitions (orchestrator + 8 specialists)
5. **Phase 5 -- Templates**: Build output templates
6. **Phase 6 -- Integration**: End-to-end test with "India 2026 annual prediction"
7. **Phase 7 -- Expansion**: Add more countries, advanced computations (ashtakavarga, SBC), financial data
