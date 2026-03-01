# Worldastro Medini Agent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Medini (mundane/world) Jyotish orchestrator agent with 8 specialist agents, a computation tool, knowledgebase, and country data model.

**Architecture:** Mirror the astrobot orchestrator pattern. Worldastro dispatches to dedicated Medini specialists in parallel, synthesizes via Floodlight Scorecard, writes two-layer readings. Separate knowledgebase (`medini_kb/`), separate data dirs (`world_data/`, `world_readings/`), separate computation tool (`medini_calc.py`).

**Tech Stack:** Python 3 (pyswisseph, pyyaml, pandas, geopy), Claude Code agents (`.claude/agents/*.md`), YAML knowledgebase, Markdown templates.

**Design doc:** `docs/plans/2026-02-28-worldastro-medini-agent-design.md`

---

## Phase 1: Computation Tool (`medini_calc.py`)

The foundation. All agents depend on this tool to compute charts, positions, eclipses, etc.

### Task 1: Scaffold `medini_calc.py` with CLI and `positions` command

**Files:**
- Create: `medini_calc.py`
- Reference: `jyotish_calc.py` (lines 1-250 for constants, core functions, CLI pattern)

**Step 1: Create `medini_calc.py` with shared constants and CLI**

Mirror `jyotish_calc.py`'s pattern: argparse subcommands, Swiss Ephemeris initialization, Lahiri ayanamsha, same `RASHI_NAMES`, `NAKSHATRAS`, `GRAHA_LIST`, `DASHA_SEQUENCE`, `DASHA_YEARS` constants. Import shared functions or duplicate the core astronomical functions (`calculate_julian_day`, `get_nakshatra`, `get_rashi`, `calculate_ascendant`, `calculate_planet_position`, `calculate_all_positions`, `get_dignity`, `calculate_vimshottari_dasha`, `build_house_summary`, `build_computed_analysis`).

CLI subcommands to register (all will be implemented in later tasks):
- `positions` (this task)
- `ingress`
- `eclipse`
- `eclipses`
- `country`
- `conjunction`
- `wars`
- `retrogrades`
- `sign-changes`
- `panchanga`
- `ashtakavarga`
- `sbc`

Implement the `positions` command:
```bash
python medini_calc.py positions --date 2026-02-28
```
This computes all 9 graha positions (sidereal, Lahiri) for a given date at 00:00 UTC. Outputs YAML to stdout with `--print` or writes to `world_data/positions/YYYY-MM-DD_positions.yaml`.

Output schema:
```yaml
date: '2026-02-28'
ayanamsha: <value>
planetary_positions:
  surya: { rasi, degree, nakshatra, pada, retrograde }
  chandra: { rasi, degree, nakshatra, pada, retrograde }
  # ... all 9 grahas
```

**Step 2: Test the `positions` command**

Run: `python medini_calc.py positions --date 2026-02-28 --print`

Verify: output shows 9 planets with sidereal positions, Lahiri ayanamsha. Cross-check Sun and Moon positions against known ephemeris for that date.

**Step 3: Commit**

```bash
git add medini_calc.py
git commit -m "feat(worldastro): scaffold medini_calc.py with positions command"
```

---

### Task 2: Add `ingress` command (solar ingress charts)

**Files:**
- Modify: `medini_calc.py`

**Step 1: Implement solar ingress computation**

Add function `compute_solar_ingress(year, ingress_type, place_lat, place_lon, timezone)`:
- `ingress_type` is one of: `aries` (0°), `cancer` (90°), `libra` (180°), `capricorn` (270°)
- Use `swe.solcross_ut()` to find exact Julian Day when tropical Sun crosses the target longitude
- Convert to sidereal using Lahiri ayanamsha
- At that moment, compute full chart: lagna (for the given lat/lon), all planetary positions, house summary
- Compute Vimshottari dasha from Moon at ingress moment
- Compute the "year lord" — planet ruling the weekday of the ingress

Default place: New Delhi (28.6139, 77.2090, UTC+5:30) — override with `--lat`, `--lon`, `--timezone`.

CLI:
```bash
python medini_calc.py ingress --type aries --year 2026
python medini_calc.py ingress --type aries --year 2026 --lat 28.6139 --lon 77.209 --timezone 5.5
```

Output schema (YAML):
```yaml
ingress:
  type: aries
  year: 2026
  exact_datetime_utc: '<ISO timestamp>'
  local_datetime: '<ISO timestamp>'
  weekday: '<Monday/Tuesday/...>'
  year_lord: '<planet ruling the weekday>'
  place: { city, latitude, longitude, timezone }
lagna:
  rasi: ...
  degree: ...
  nakshatra: ...
  pada: ...
planetary_positions:
  surya: { rasi, degree, nakshatra, pada, retrograde, house, dignity }
  # ... all 9 grahas
house_summary:
  house_1: { rasi, planets }
  # ... all 12 houses
vimshottari_dasha:
  balance_at_birth: { lord, remaining_years, remaining_months, remaining_days }
  sequence: [...]
```

Write to: `world_data/ingress/YYYY_<type>_ingress.yaml`

**Step 2: Test**

Run: `python medini_calc.py ingress --type aries --year 2026 --print`

Verify: Sun is at ~0° Aries sidereal. The date should be around April 13-14, 2026 (Mesha Sankranti). Check lagna is computed. Check year-lord is assigned.

Run: `python medini_calc.py ingress --type cancer --year 2026 --print`

Verify: Sun is at ~0° Cancer sidereal. Date should be around July 16-17, 2026.

**Step 3: Commit**

```bash
git add medini_calc.py world_data/
git commit -m "feat(worldastro): add solar ingress computation"
```

---

### Task 3: Add `eclipse` and `eclipses` commands

**Files:**
- Modify: `medini_calc.py`

**Step 1: Implement eclipse computation**

Add function `find_eclipses_in_year(year)`:
- Use `swe.sol_eclipse_when_ut()` with `start_jd` = Jan 1 of year, iterate to find all solar eclipses in the year
- Use `swe.lun_eclipse_when_ut()` similarly for lunar eclipses
- For each eclipse, record: type (total/annular/partial/penumbral), exact maximum time, geographic position, duration

Add function `compute_eclipse_chart(jd_max, place_lat, place_lon, timezone)`:
- At the moment of maximum eclipse, compute full chart (lagna, all positions, house summary)
- Determine which sign and nakshatra the eclipse falls in
- For solar eclipse: the sign Sun occupies
- For lunar eclipse: the signs of both Sun and Moon (full moon axis)

`eclipse` command (single date):
```bash
python medini_calc.py eclipse --date 2026-03-14 --print
```
Finds the nearest eclipse to the given date and computes its chart.

`eclipses` command (all in year):
```bash
python medini_calc.py eclipses --year 2026 --print
```
Lists all solar and lunar eclipses in the year with basic data.

Output schema for `eclipse`:
```yaml
eclipse:
  type: solar        # solar | lunar
  subtype: total     # total | annular | partial | penumbral
  date_utc: '2026-03-14T...'
  maximum_utc: '2026-03-14T...'
  duration_minutes: <N>
  sign: Kumbham
  nakshatra: Shatabhisha
  nakshatra_pada: 2
  geographic:
    central_lat: <N>
    central_lon: <N>
    path_description: "<visible regions>"
lagna: ...
planetary_positions: ...
house_summary: ...
```

Write each to: `world_data/eclipses/YYYY-MM-DD_<solar|lunar>_eclipse.yaml`

**Step 2: Test**

Run: `python medini_calc.py eclipses --year 2026 --print`

Verify: lists known eclipses for 2026 (can cross-check with NASA eclipse data). There should be 2-4 eclipses.

Run: `python medini_calc.py eclipse --date 2026-03-14 --print`

Verify: full chart output with eclipse metadata.

**Step 3: Commit**

```bash
git add medini_calc.py world_data/
git commit -m "feat(worldastro): add eclipse computation commands"
```

---

### Task 4: Add `panchanga` command

**Files:**
- Modify: `medini_calc.py`

**Step 1: Implement panchanga computation**

Add function `compute_panchanga(jd, lat, lon, timezone)`:

**Tithi**: Angular distance between Moon and Sun, divided by 12°.
- `tithi_angle = (moon_tropical - sun_tropical) % 360`
- `tithi_number = int(tithi_angle / 12) + 1` (1-30)
- Tithi names: Pratipada through Amavasya/Purnima
- Tithi lord: Sun(1), Moon(2), Mars(3), Mercury(4), Jupiter(5), Venus(6), Saturn(7), Rahu(8), repeat...

**Nakshatra**: Moon's sidereal nakshatra (already have `get_nakshatra()`).

**Yoga**: Sum of Moon and Sun tropical longitudes, divided by 13°20'.
- `yoga_angle = (moon_tropical + sun_tropical) % 360`
- `yoga_number = int(yoga_angle / (13 + 1/3)) + 1` (1-27)
- 27 yoga names: Vishkambha, Priti, Ayushman, Saubhagya, ... Vaidhriti

**Karana**: Half-tithi. Each tithi has 2 karanas.
- `karana_number = int(tithi_angle / 6) + 1` (1-60 per cycle)
- 11 karana names cycling through: 4 fixed (Shakuni, Chatushpada, Naga, Kimstughna) + 7 rotating (Bava, Balava, Kaulava, Taitila, Gara, Vanija, Vishti)

**Vara**: Weekday from Julian Day.
- `vara = weekday_name` (Ravivara/Sunday through Shanivara/Saturday)

CLI:
```bash
python medini_calc.py panchanga --date 2026-02-28 --lat 28.6139 --lon 77.209 --timezone 5.5 --print
```

Output schema:
```yaml
panchanga:
  date: '2026-02-28'
  place: { latitude, longitude, timezone }
  vara:
    name: Shanivara
    english: Saturday
    lord: Saturn
  tithi:
    number: 15
    name: Purnima
    paksha: Shukla
    lord: Sun
  nakshatra:
    name: Uttara Phalguni
    lord: Sun
    pada: 2
  yoga:
    number: 5
    name: Saubhagya
  karana:
    number: 29
    name: Vishti
planetary_positions: ...
```

**Step 2: Test**

Run: `python medini_calc.py panchanga --date 2026-02-28 --lat 28.6139 --lon 77.209 --timezone 5.5 --print`

Verify: Vara matches the actual weekday. Tithi, nakshatra reasonable for the date. Cross-check with a panchanga website.

**Step 3: Commit**

```bash
git add medini_calc.py
git commit -m "feat(worldastro): add panchanga computation"
```

---

### Task 5: Add `country` command (foundation chart computation)

**Files:**
- Modify: `medini_calc.py`

**Step 1: Implement country chart computation**

Add function `compute_country_chart(country_name)`:
- Read `world_data/<country>/foundation_chart.yaml` (the `entity` section with date/time/place)
- If the file contains only entity metadata (no `lagna`, no `planetary_positions`), compute the full chart:
  - Lagna, all 9 planetary positions, dignities, house summary, Vimshottari dasha, computed analysis
- Write the complete chart back to the same file (now enriched)
- Additionally compute current transits to the foundation chart (use today's date)
- Write transit data to `world_data/<country>/YYYY-MM-DD_transits.yaml`

This is essentially the same as `jyotish_calc.py`'s birth chart + transit computation, but reading from `world_data/` instead of `readings/`.

CLI:
```bash
python medini_calc.py country --name india --print
python medini_calc.py country --name india --transit-date 2026-03-15
```

**Step 2: Test**

Prerequisite: Task 8 (India foundation chart) must exist as a stub with entity metadata.

Run: `python medini_calc.py country --name india --print`

Verify: Lagna, planets, dashas all computed for Aug 15, 1947, 00:00 IST, New Delhi. Check that the India independence chart matches known values (Vrishabha/Taurus lagna is the widely accepted lagna for the midnight chart).

**Step 3: Commit**

```bash
git add medini_calc.py world_data/
git commit -m "feat(worldastro): add country chart computation"
```

---

### Task 6: Add `conjunction`, `wars`, `retrogrades`, `sign-changes` commands

**Files:**
- Modify: `medini_calc.py`

**Step 1: Implement conjunction finder**

Add function `find_conjunction(planet1_id, planet2_id, year)`:
- Starting from Jan 1 of year, iterate day by day computing angular distance between the two planets (sidereal)
- When distance crosses a minimum (changes from decreasing to increasing), use bisection method to find exact JD of minimum
- If minimum distance < 10° (loose conjunction) or < 1° (exact conjunction), compute full chart at that moment
- Support planet names: `saturn,jupiter`, `saturn,rahu`, etc.

CLI:
```bash
python medini_calc.py conjunction --planets saturn,jupiter --year 2020 --print
```

**Step 2: Implement planetary wars finder**

Add function `find_planetary_wars(start_date, end_date)`:
- Only between visible planets (Mars, Mercury, Jupiter, Venus, Saturn)
- Planetary war = within 1° of each other
- Determine winner by brightness (lower magnitude = winner)
- Use `swe.pheno_ut()` for apparent magnitude

CLI:
```bash
python medini_calc.py wars --start 2026-01-01 --end 2026-12-31 --print
```

**Step 3: Implement retrograde finder**

Add function `find_retrogrades(year)`:
- For each outer planet (Mars, Jupiter, Saturn) and inner planets (Mercury, Venus):
  - Track daily speed (`pos[3]` from `swe.calc_ut`)
  - When speed crosses zero → retrograde station or direct station
  - Record: planet, station date, sign, degree, direct date

CLI:
```bash
python medini_calc.py retrogrades --year 2026 --print
```

**Step 4: Implement sign-change finder**

Add function `find_sign_changes(year)`:
- For slow planets (Saturn, Jupiter, Rahu, Ketu): track sidereal longitude daily
- When `int(lon/30)` changes → sign ingress
- Record: planet, date, old sign, new sign

CLI:
```bash
python medini_calc.py sign-changes --year 2026 --print
```

**Step 5: Test all four commands**

Run each command and verify output is reasonable. Cross-check a Saturn sign change or Jupiter retrograde against known ephemeris data.

**Step 6: Commit**

```bash
git add medini_calc.py
git commit -m "feat(worldastro): add conjunction, wars, retrogrades, sign-changes commands"
```

---

### Task 7: Add `ashtakavarga` and `sbc` commands

**Files:**
- Modify: `medini_calc.py`

**Step 1: Implement ashtakavarga computation**

Add function `compute_ashtakavarga(positions)`:
- Reference the BAV rules from `.claude_kb/reference/ashtakavarga.yaml`
- For each of the 7 planets (Sun through Saturn), compute bindus contributed by each planet + lagna to each of the 12 signs
- Sum to get BAV (Bhinnashtakavarga) per planet per sign
- Sum all BAVs to get SAV (Sarvashtakavarga) per sign

CLI:
```bash
python medini_calc.py ashtakavarga --country india --print
```

Reads country's foundation chart, computes BAV/SAV, writes to `world_data/<country>/ashtakavarga.yaml`.

**Step 2: Implement Sarvatobhadra Chakra**

Add function `compute_sbc(jd, ayanamsha)`:
- Build the 9x9 SBC grid:
  - Map the 28 nakshatras (including Abhijit) to grid positions
  - Map the 16 vowels to grid positions
  - Map the 7 varas (weekdays) to grid positions
  - Map the 30 tithis to grid positions
- For each transiting planet, determine which grid cells receive vedha (aspect/influence)
- SBC vedha rules: planets aspect specific nakshatras based on their current nakshatra position

CLI:
```bash
python medini_calc.py sbc --date 2026-02-28 --print
```

Output: the grid with vedha marks, list of nakshatras under vedha from each planet.

**Step 3: Test**

Test ashtakavarga with India chart. Total SAV across all signs should sum to 337 (standard total).

Test SBC with a known date and verify grid layout.

**Step 4: Commit**

```bash
git add medini_calc.py
git commit -m "feat(worldastro): add ashtakavarga and sarvatobhadra chakra commands"
```

---

## Phase 2: Knowledgebase (`medini_kb/`)

### Task 8: Create directory structure and foundation data stubs

**Files:**
- Create: `medini_kb/reference/` (directory)
- Create: `medini_kb/templates/` (directory)
- Create: `world_data/india/` (directory)
- Create: `world_data/india/foundation_chart.yaml` (entity metadata stub)
- Create: `world_readings/` (directory stubs)

**Step 1: Create directories**

```bash
mkdir -p medini_kb/reference medini_kb/templates
mkdir -p world_data/india world_data/usa
mkdir -p world_readings/india world_readings/global world_readings/events
```

**Step 2: Create India foundation chart stub**

Write `world_data/india/foundation_chart.yaml`:
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
  notes: "Midnight chart — official transfer of power."
  alternate_times:
    - time: '00:00:00'
      source: "Official midnight transfer of power (most widely used)"
    - time: '08:15:00'
      source: "Nehru's flag hoisting ceremony"
```

**Step 3: Create USA foundation chart stub**

Write `world_data/usa/foundation_chart.yaml`:
```yaml
entity:
  name: United States of America
  type: nation
  foundation_event: Declaration of Independence
  date: '1776-07-04'
  time: '17:10:00'
  timezone: UTC-5:00
  place:
    city: Philadelphia
    state: Pennsylvania
    latitude: 39.9526
    longitude: -75.1652
  notes: "Sibly chart (5:10 PM LMT) — most commonly used."
  alternate_times:
    - time: '17:10:00'
      source: "Ebenezer Sibly chart (most popular)"
    - time: '02:13:00'
      source: "Gemini rising chart"
    - time: '12:00:00'
      source: "Noon chart (Sun on MC)"
```

**Step 4: Commit**

```bash
git add medini_kb/ world_data/ world_readings/
git commit -m "feat(worldastro): create directory structure and foundation chart stubs"
```

---

### Task 9: Build `planet_mundane_significations.yaml`

**Files:**
- Create: `medini_kb/reference/planet_mundane_significations.yaml`

**Step 1: Research and write**

Use web research to compile planet significations in Medini Jyotish from B.V. Raman, Varahamihira, and modern sources.

Structure:
```yaml
source: "Compiled from B.V. Raman (Mundane Astrology), Varahamihira (Brihat Samhita), and modern Medini texts"

significations:
  surya:
    english: Sun
    mundane_significations:
      - king / head of state / president / prime minister
      - government authority and power
      - gold and gold trade
      - father of the nation
      - national prestige and honor
      - public health vitality
    rules:
      - "Strong Sun in ingress chart = stable government"
      - "Afflicted Sun = political instability, leadership crisis"
      - "Sun eclipsed = king/ruler faces downfall or health crisis"
  chandra:
    english: Moon
    mundane_significations:
      - the public / common people / masses
      - agriculture and food supply
      - water bodies, rainfall, floods
      - women's issues
      - public sentiment and opinion
      - silver, pearls
    rules:
      - "Strong Moon = prosperous agriculture, content populace"
      - "Afflicted Moon = public unrest, food scarcity, drought or floods"
  # ... mangal, budha, guru, shukra, shani, rahu, ketu
```

Cover all 9 grahas with 5-10 significations each plus 2-3 classical rules.

**Step 2: Commit**

```bash
git add medini_kb/reference/planet_mundane_significations.yaml
git commit -m "feat(worldastro): add planet mundane significations reference"
```

---

### Task 10: Build `house_mundane_significations.yaml`

**Files:**
- Create: `medini_kb/reference/house_mundane_significations.yaml`

**Step 1: Research and write**

The 12 houses in a mundane chart (applied to ingress charts and country charts):

```yaml
source: "B.V. Raman (Mundane Astrology), classical Medini texts"

significations:
  house_1:
    name: "First House"
    mundane_keywords:
      - the country as a whole
      - general condition of the nation
      - public health
      - national character
    natural_karaka: Sun
  house_2:
    name: "Second House"
    mundane_keywords:
      - national wealth and revenue
      - banking and financial institutions
      - trade and commerce
      - food supply
      - national resources
    natural_karaka: Jupiter
  house_3:
    name: "Third House"
    mundane_keywords:
      - communications (media, press, telecom)
      - transportation and railways
      - neighboring countries
      - treaties with neighbors
    natural_karaka: Mars
  house_4:
    name: "Fourth House"
    mundane_keywords:
      - agriculture and crops
      - land, mines, real estate
      - opposition parties
      - weather conditions
      - natural calamities
      - the common people's welfare
    natural_karaka: Moon
  # ... houses 5 through 12
```

Key mundane house meanings to include:
- 5th: diplomacy, children, speculation, national morale
- 6th: military, defense, public health, enemies
- 7th: foreign affairs, wars, international relations
- 8th: death rate, epidemics, national debt, taxes, losses
- 9th: judiciary, religion, higher education, foreign trade
- 10th: government, ruler/PM, national honor, law & order
- 11th: legislature/parliament, allies, gains
- 12th: secret enemies, espionage, hospitals, expenditure

**Step 2: Commit**

```bash
git add medini_kb/reference/house_mundane_significations.yaml
git commit -m "feat(worldastro): add house mundane significations reference"
```

---

### Task 11: Build `country_sign_rulerships.yaml`

**Files:**
- Create: `medini_kb/reference/country_sign_rulerships.yaml`

**Step 1: Research and write**

Classical rasi-to-country mapping from Varahamihira and B.V. Raman, supplemented with modern attributions.

```yaml
source: "Varahamihira (Brihat Samhita), B.V. Raman (Mundane Astrology), modern Medini texts"

notes: >
  Classical texts mapped rasis to regions known at the time. Modern astrologers
  have extended these mappings. Where classical and modern disagree, both are listed.

rulerships:
  mesham:
    english: Aries
    classical_regions:
      - "Countries east of India"
      - "Regions of mountains and forests"
    modern_countries:
      - England
      - Germany
      - Israel
      - Japan
    lord: Mars
  rishabham:
    english: Taurus
    classical_regions:
      - "Agricultural lands, plains"
    modern_countries:
      - Iran
      - Ireland
      - Switzerland
      - parts of Russia
    lord: Venus
  # ... all 12 rasis with classical + modern mappings
```

Include India's primary rulership (commonly Makaram/Capricorn per many Medini astrologers, though some argue Kanni/Virgo). Note the debate.

**Step 2: Commit**

```bash
git add medini_kb/reference/country_sign_rulerships.yaml
git commit -m "feat(worldastro): add country-sign rulership reference"
```

---

### Task 12: Build `eclipse_rules.yaml`

**Files:**
- Create: `medini_kb/reference/eclipse_rules.yaml`

**Step 1: Research and write**

Classical eclipse interpretation rules from Brihat Samhita and B.V. Raman:

```yaml
source: "Varahamihira (Brihat Samhita Ch 5), B.V. Raman (Mundane Astrology)"

general_rules:
  solar_eclipse:
    significance: "Affects rulers, government, authority figures"
    duration_rule: >
      Effects last for as many months as the eclipse duration in hours.
      If eclipse lasts 2 hours, effects manifest over 2 months.
    timing_rule: >
      Solar eclipse effects begin immediately for first decanate,
      after 4 months for second decanate, after 8 months for third decanate.
  lunar_eclipse:
    significance: "Affects the public, agriculture, water, women"
    duration_rule: >
      Effects last for as many fortnights as the eclipse duration in hours.

sign_effects:
  mesham:
    nature_of_events:
      - "Danger to leaders of countries ruled by Aries"
      - "Military conflicts"
      - "Fire-related disasters"
  # ... all 12 signs

nakshatra_effects:
  ashwini:
    - "Travel-related disruptions"
    - "Horse/vehicle accidents"
  bharani:
    - "Deaths of important persons"
  # ... key nakshatras with mundane eclipse effects

eclipse_in_house:
  house_1: "National health crisis, general upheaval"
  house_2: "Economic disruption, financial loss"
  # ... all 12 houses in a mundane chart
```

**Step 2: Commit**

```bash
git add medini_kb/reference/eclipse_rules.yaml
git commit -m "feat(worldastro): add eclipse rules reference"
```

---

### Task 13: Build remaining reference files

**Files:**
- Create: `medini_kb/reference/ingress_rules.yaml`
- Create: `medini_kb/reference/saturn_jupiter_cycles.yaml`
- Create: `medini_kb/reference/commodity_rulerships.yaml`
- Create: `medini_kb/reference/nakshatra_mundane.yaml`
- Create: `medini_kb/reference/natural_events.yaml`
- Create: `medini_kb/reference/war_conflict_rules.yaml`
- Create: `medini_kb/reference/scorecards.yaml`

**Step 1: Build each file using web research + classical sources**

Each file follows the same YAML pattern with `source`, structured data, and `rules` or `notes`.

Key content per file:

**`ingress_rules.yaml`**: Year-lord determination (planet ruling weekday of Mesha Sankranti), seasonal chart rules (which ingress governs which months), how to read an ingress chart for a specific country (set lagna for the capital city).

**`saturn_jupiter_cycles.yaml`**: 20-year conjunction cycle, element sequence (fire→earth→air→water, each lasting ~200 years), Great Mutation dates (when the element changes), historical correlations (e.g., 2020 conjunction in Makaram → air era shift).

**`commodity_rulerships.yaml`**: Sun=gold, Moon=silver/pearls, Mars=iron/copper/red commodities, Mercury=trade/commerce/tech, Jupiter=banking/finance/grains, Venus=luxury/textiles/sugar, Saturn=oil/coal/mining/base metals, Rahu=technology/foreign goods, Ketu=spiritual goods/alternative.

**`nakshatra_mundane.yaml`**: Each of 27 nakshatras with mundane event associations. E.g., Ardra=storms/destruction/tears, Ashlesha=poisons/epidemics/serpents, Magha=royal/governmental events, Jyeshtha=elder statesmen/power struggles.

**`natural_events.yaml`**: Varahamihira's rules for earthquakes (Mars-Saturn combinations), floods (afflicted Moon/Cancer), droughts (afflicted Sun/Saturn), storms (Ardra/Swati involvement), epidemics (8th house affliction, Ashlesha).

**`war_conflict_rules.yaml`**: Mars-Saturn aspects/conjunctions, 6th/7th house affliction in national charts, Rahu involvement in 7th, eclipses in martial signs (Aries/Scorpio).

**`scorecards.yaml`**: Adapt the natal Floodlight Scorecard for Medini. Same 5-point weight scale but with Medini-specific modifiers: +1.0 for eclipse confirmation, +0.5 for SAV strength in transited sign, -1.0 for eclipse afflicting relevant house, etc. Domains: Political Stability, Economy, Natural Events, Military/Conflict, Public Health, Foreign Relations, Markets/Finance.

**Step 2: Commit after each file or batch**

```bash
git add medini_kb/reference/
git commit -m "feat(worldastro): add remaining knowledgebase reference files"
```

---

## Phase 3: Country Data

### Task 14: Compute India foundation chart

**Files:**
- Modify: `world_data/india/foundation_chart.yaml` (from stub to full chart)
- Create: `world_data/india/history.yaml`

**Step 1: Run medini_calc.py to compute India's chart**

```bash
python medini_calc.py country --name india --print
```

This should read the entity stub and compute the full chart (lagna, positions, dashas, house summary, computed analysis). Verify the output — India's midnight chart should have Vrishabha (Taurus) lagna.

**Step 2: Create India history.yaml**

Write `world_data/india/history.yaml` with major events for validation:
```yaml
events:
  - date: '1947-08-15'
    event: "Independence"
  - date: '1962-10-20'
    event: "China-India War begins"
  - date: '1971-12-03'
    event: "India-Pakistan War (Bangladesh liberation)"
  - date: '1975-06-25'
    event: "Emergency declared"
  - date: '1991-07-24'
    event: "Economic liberalization begins"
  - date: '1998-05-11'
    event: "Pokhran-II nuclear tests"
  - date: '2008-11-26'
    event: "Mumbai terrorist attacks"
  - date: '2014-05-26'
    event: "Modi government takes office"
  - date: '2016-11-08'
    event: "Demonetization"
  - date: '2020-03-25'
    event: "COVID lockdown begins"
```

**Step 3: Commit**

```bash
git add world_data/india/
git commit -m "feat(worldastro): compute India foundation chart and add history"
```

---

### Task 15: Compute USA foundation chart

**Files:**
- Modify: `world_data/usa/foundation_chart.yaml`
- Create: `world_data/usa/history.yaml`

Same pattern as Task 14 but for USA. Run `python medini_calc.py country --name usa --print`. Sibly chart should give Sagittarius lagna. Add 10-15 major historical events.

**Commit:**
```bash
git add world_data/usa/
git commit -m "feat(worldastro): compute USA foundation chart and add history"
```

---

## Phase 4: Agent Definitions

### Task 16: Write `worldastro.md` orchestrator

**Files:**
- Create: `.claude/agents/worldastro.md`

**Step 1: Write the orchestrator**

Model after `astrobot.md` (506 lines). Key sections:

1. **YAML frontmatter**: `name: worldastro`, `description: "use this agent when asked for astro related questions"`, `model: opus`, `memory: project`
2. **Role**: Orchestrator for Medini Jyotish analysis. List the 8 specialists.
3. **Honesty Mandate**: Same as astrobot.
4. **Anti-Bias Rules**: All 5 astrobot rules + 6 Medini-specific rules from the design doc.
5. **Workflow (8 Steps)**: Adapted for Medini as described in the design doc. Include exact `medini_calc.py` commands for each step.
6. **Pre-Analysis Worksheet**: Parts A-E (Slow Planet Transit Table, Eclipse Calendar, Country Dasha State, Ashtakavarga Transit Strength, Consistency Lock).
7. **Specialist Dispatch Table**: When to dispatch each specialist.
8. **Floodlight Scorecard (Medini version)**: 7 domains, scoring rules.
9. **Two-Layer Output Rules**: Same as astrobot.
10. **Output format rules**: Data separation principle, file paths.

**Step 2: Commit**

```bash
git add .claude/agents/worldastro.md
git commit -m "feat(worldastro): write orchestrator agent definition"
```

---

### Task 17: Write `medini-transit.md` specialist

**Files:**
- Create: `.claude/agents/medini-transit.md`

**Step 1: Write the specialist**

Model after `parashari.md` (120 lines). Key sections:

1. **YAML frontmatter**: `name: medini-transit`, `description: "Medini transit specialist. Analyzes major planetary transits..."`, `model: sonnet`
2. **Role**: Specialist for analyzing slow planet transits (Saturn, Jupiter, Rahu-Ketu) through signs, their mundane impact, planetary wars, and retrograde effects.
3. **Tradition Scope**: Transit analysis only. Does NOT analyze eclipses (that's medini-eclipse), ingress charts (medini-ingress), or country-specific charts (medini-country).
4. **Data Sources**: `world_data/positions/`, `medini_kb/reference/planet_mundane_significations.yaml`, `medini_kb/reference/country_sign_rulerships.yaml`
5. **Analysis Protocol**: For each slow planet → current sign → which countries/domains affected → dignity in that sign → aspects to other planets → duration of transit → key dates (retrograde/direct stations, sign changes)
6. **Output Format**: Must return YAML per `medini_specialist_findings.md` schema with `system: "Medini-Transit"`

**Step 2: Commit**

```bash
git add .claude/agents/medini-transit.md
git commit -m "feat(worldastro): write medini-transit specialist agent"
```

---

### Task 18: Write remaining 7 specialist agents

**Files:**
- Create: `.claude/agents/medini-eclipse.md`
- Create: `.claude/agents/medini-ingress.md`
- Create: `.claude/agents/medini-cycles.md`
- Create: `.claude/agents/medini-country.md`
- Create: `.claude/agents/medini-financial.md`
- Create: `.claude/agents/medini-critic.md`
- Create: `.claude/agents/medini-reference.md`

**Step 1: Write each specialist**

All follow the same pattern as Task 17 (model after parashari.md / critic.md). Key differences per agent:

**`medini-eclipse.md`** (~90 lines, model: sonnet):
- Analyzes eclipse charts: sign, nakshatra, duration, affected countries, timing of manifestation
- References: `eclipse_rules.yaml`, `country_sign_rulerships.yaml`, `nakshatra_mundane.yaml`
- Protocol: eclipse type → sign → country mapping → house analysis → duration → manifestation timeline

**`medini-ingress.md`** (~90 lines, model: sonnet):
- Analyzes solar ingress (Aries/seasonal) charts
- References: `ingress_rules.yaml`, `house_mundane_significations.yaml`
- Protocol: year-lord assessment → lagna analysis → house-by-house scan → planetary strengths

**`medini-cycles.md`** (~80 lines, model: sonnet):
- Analyzes Saturn-Jupiter and other major conjunction cycles
- References: `saturn_jupiter_cycles.yaml`
- Protocol: current cycle element → conjunction sign → historical parallels → era characteristics

**`medini-country.md`** (~100 lines, model: sonnet):
- Analyzes a country's foundation chart with current transits and dashas
- References: all `medini_kb/reference/` files, `world_data/<country>/` files
- Protocol: foundation chart assessment → current dasha → transit overlay → ashtakavarga strength → predictions by domain

**`medini-financial.md`** (~80 lines, model: sonnet):
- Analyzes market and commodity cycles
- References: `commodity_rulerships.yaml`, `planet_mundane_significations.yaml`
- Protocol: planet-commodity mapping → current transit dignity → Jupiter/Venus cycle → sector timing

**`medini-critic.md`** (~120 lines, model: sonnet):
- Model after `critic.md`. Same 5-check structure adapted for Medini:
  1. Contradiction check (vs computed data)
  2. Omission check (major transits/eclipses covered?)
  3. Bias check (ratio, steel-man)
  4. Historical validation check (predictions match past patterns?)
  5. Factual accuracy check (positions, dates, rulerships)

**`medini-reference.md`** (~60 lines, model: sonnet):
- Model after `astropdf.md`. Lookup agent for `medini_kb/reference/` files.
- Returns exact rules, tables, or definitions on demand.

**Step 2: Commit after each agent or batch**

```bash
git add .claude/agents/medini-*.md
git commit -m "feat(worldastro): write all Medini specialist agent definitions"
```

---

### Task 19: Create agent memory directory

**Files:**
- Create: `.claude/agent-memory/worldastro/MEMORY.md`

**Step 1: Write initial memory file**

```markdown
# Worldastro Agent Memory

## Lessons Learned
(empty — will be populated as readings are generated)

## Known Issues
(empty)

## Country Chart Notes
- India: Midnight chart (00:00 IST, Aug 15 1947, New Delhi) — Vrishabha lagna
- USA: Sibly chart (5:10 PM LMT, Jul 4 1776, Philadelphia) — Dhanusu lagna
```

**Step 2: Commit**

```bash
git add .claude/agent-memory/worldastro/
git commit -m "feat(worldastro): create agent memory directory"
```

---

## Phase 5: Templates

### Task 20: Write `medini_specialist_findings.md` template

**Files:**
- Create: `medini_kb/templates/medini_specialist_findings.md`

**Step 1: Adapt natal specialist_findings template for Medini**

Same YAML schema as `.claude_kb/templates/specialist_findings.md` but with Medini-specific fields:

- `system:` values include `"Medini-Transit"`, `"Medini-Eclipse"`, `"Medini-Ingress"`, etc.
- `domain:` field added to each finding (Political Stability / Economy / Natural Events / Military / Public Health / Foreign Relations / Markets)
- `affected_countries:` field on each finding
- `timing` section includes eclipse-based manifestation windows
- `dasha` section covers country dashas instead of personal dashas

**Step 2: Commit**

```bash
git add medini_kb/templates/medini_specialist_findings.md
git commit -m "feat(worldastro): write Medini specialist findings template"
```

---

### Task 21: Write reading templates

**Files:**
- Create: `medini_kb/templates/foundation_chart.yaml`
- Create: `medini_kb/templates/annual_country_prediction.md`
- Create: `medini_kb/templates/eclipse_analysis.md`
- Create: `medini_kb/templates/market_outlook.md`
- Create: `medini_kb/templates/global_transit_report.md`
- Create: `medini_kb/templates/event_analysis.md`
- Create: `medini_kb/templates/cycle_analysis.md`

**Step 1: Write each template**

All templates follow the two-layer output pattern from astrobot. Key structure for each:

**`annual_country_prediction.md`**:
```markdown
# [Country] — [Year] Annual Prediction

> Generated: [date] | Ingress: [Mesha Sankranti date] | Year Lord: [planet]

## Floodlight Scorecard

| Domain | FAV | UNFAV | NET | Confidence |
|--------|-----|-------|-----|------------|
| Political Stability | | | | |
| Economy | | | | |
| Natural Events | | | | |
| Military/Conflict | | | | |
| Public Health | | | | |
| Foreign Relations | | | | |
| Markets/Finance | | | | |

## Executive Summary
[Plain language, 3-5 sentences]

## Domain Analysis

### Political Stability
[Layer 1: Plain language]
> [Why this matters now bridge]
<details><summary>Technical Basis</summary>
[Layer 2: Full jyotish analysis]
</details>

### Economy
[same pattern]

## Key Dates
| Date Range | Domain | Nature | Trigger |
|------------|--------|--------|---------|

## Multi-System Convergence
[Which specialists agreed/disagreed]

## Quality Review
[Critic findings summary]
```

Other templates follow similar patterns adapted for their specific focus (eclipse analysis, market outlook, etc.).

**Step 2: Commit**

```bash
git add medini_kb/templates/
git commit -m "feat(worldastro): write all reading templates"
```

---

## Phase 6: Integration Testing

### Task 22: End-to-end test — India 2026 annual prediction

**Files:**
- Output: `world_readings/india/2026-XX-XX_annual_prediction.md`

**Step 1: Verify all prerequisites**

Run through checklist:
- [ ] `medini_calc.py positions --date 2026-02-28 --print` works
- [ ] `medini_calc.py ingress --type aries --year 2026 --print` works
- [ ] `medini_calc.py eclipses --year 2026 --print` works
- [ ] `medini_calc.py country --name india --print` works
- [ ] `world_data/india/foundation_chart.yaml` has full computed chart
- [ ] All `medini_kb/reference/` files exist
- [ ] All agent definitions exist in `.claude/agents/`
- [ ] All templates exist in `medini_kb/templates/`

**Step 2: Run the worldastro agent**

Ask the worldastro agent: "Generate India's annual prediction for 2026."

The agent should:
1. Compute solar ingress for Aries 2026 (set for New Delhi)
2. Compute eclipses for 2026
3. Load India foundation chart
4. Compute current transits to India chart
5. Dispatch specialists in parallel
6. Synthesize and build scorecard
7. Write two-layer reading
8. Run critic

**Step 3: Review the output**

Verify:
- Reading saved to `world_readings/india/`
- All 7 domains covered in scorecard
- Two-layer output present for each section
- No factual errors in planetary positions
- Critic review attached

**Step 4: Fix any issues found**

If the agent workflow breaks at any step, fix the relevant agent definition, computation tool, or template.

**Step 5: Commit the reading and any fixes**

```bash
git add world_readings/ medini_calc.py .claude/agents/ medini_kb/
git commit -m "feat(worldastro): complete integration test — India 2026 annual prediction"
```

---

## Phase 7: Expansion (Future)

### Task 23: Add more countries (China, Russia, UK, etc.)

Create foundation chart stubs, compute charts, add history files. One country per commit.

### Task 24: Add market-specific data

Extend `commodity_rulerships.yaml` with sector-specific data (IT, pharma, banking). Add stock market index foundation charts (BSE, Nifty, S&P 500).

### Task 25: Update `settings.local.json`

Add any new permissions needed for worldastro:
- Allow `python medini_calc.py` execution
- Allow writing to `world_data/` and `world_readings/`

---

## Summary

| Phase | Tasks | Key Deliverable |
|-------|-------|-----------------|
| 1. Computation | 1-7 | `medini_calc.py` with 12 commands |
| 2. Knowledgebase | 8-13 | 11 reference YAML files |
| 3. Country Data | 14-15 | India + USA foundation charts |
| 4. Agents | 16-19 | 9 agent definitions |
| 5. Templates | 20-21 | 8 templates |
| 6. Integration | 22 | India 2026 annual prediction |
| 7. Expansion | 23-25 | More countries, markets, permissions |

**Total tasks: 25** (22 for core system, 3 for expansion)
**Critical path: Tasks 1 → 8 → 5 → 14 → 16-18 → 20-21 → 22**
