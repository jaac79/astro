# Astrobot Multi-Agent Redesign

**Date**: 2026-02-21
**Status**: Approved design — pending implementation plan

---

## Problem Statement

The current astrobot is a monolithic 498-line agent prompt that attempts to be expert in Parashari, Jaimini, KP, Nadi, and Tajaka traditions simultaneously. In practice, this causes:

1. **Shallow analysis** — the agent skips steps, gives surface-level interpretations, doesn't trace dispositorship chains or check multiple dasha systems as instructed.
2. **Bias accumulation in long sessions** — four types observed:
   - *Confirmation bias*: early conclusions bend all subsequent analysis
   - *Recency bias*: focus shifts to the last topic discussed
   - *People-pleasing drift*: classifications soften over time (DIFFICULT → MIXED)
   - *User-frame anchoring*: leading questions shape the analysis direction

**Root causes**:
- 498 lines of instructions → signal dilution over long conversations
- No structural enforcement of the protocol — just exhortation
- All analysis happens in one continuous context → bias compounds
- The Floodlight Scorecard (the anti-bias defense) gets skipped or done shallowly

---

## Solution: Multi-Agent Architecture

Replace the monolithic astrobot with an orchestrator + 7 specialist agents, each expert in one Jyotish tradition. Bias is prevented architecturally: each specialist starts with clean context and returns structured data, not narrative.

### Agent Hierarchy

```
User → astrobot (orchestrator + synthesizer)
         ├→ astropdf   (reference lookup)       [EXISTS - unchanged]
         ├→ parashari  (BPHS + Vimshottari/Yogini dashas)
         ├→ jaimini    (Chara karakas, rasi drishti, Chara/Narayana dashas, arudhas)
         ├→ kp         (Sub-lord theory, cuspal analysis, ruling planets)
         ├→ nadi       (Nakshatra-level analysis, parivritti dasha)
         ├→ tajaka     (Annual charts, solar return, Tajaka yogas, sahams)
         ├→ prashna    (Horary astrology — moment-based charts)
         └→ muhurta    (Electional astrology — auspicious timing selection)
```

### Dispatch Rule

**Consult every specialist whose data is available** in birth_data.yaml + extensions.yaml. No selective filtering — more perspectives = better convergence analysis.

**Exceptions**:
- **prashna**: Only when the user explicitly asks a horary (moment-based) question
- **muhurta**: Only when the user asks for auspicious timing

---

## Data Architecture

### Per-Person Storage (unchanged directory structure)

```
readings/
  <person_name>/
    birth_data.yaml              # Core positions — filled ONCE (template unchanged)
    extensions.yaml              # NEW: System-specific computed data
    YYYY-MM-DD_current_positions.yaml   # Transit snapshot per reading
    YYYY-MM-DD_<type>.md                # Readings (unchanged)
```

### birth_data.yaml (unchanged)

Keeps the current template: native info, lagna, chandra, 9 planetary positions (rasi, degree, nakshatra, pada, retrograde), Vimshottari dasha sequence.

### extensions.yaml (NEW)

System-specific pre-computed data, filled once from jyotish software:

```yaml
# KP System
kp_cusps:
  cusp_1: {sign: , degree: , star_lord: , sub_lord: }
  # ... through cusp_12

kp_planet_positions:
  surya: {star_lord: , sub_lord: , sub_sub_lord: }
  # ... for all 9 grahas

# Jaimini
chara_karakas:
  atmakaraka: {graha: , degree: }
  amatyakaraka: {graha: , degree: }
  bhratrukaraka: {graha: , degree: }
  matrukaraka: {graha: , degree: }
  putrakaraka: {graha: , degree: }
  gnatikaraka: {graha: , degree: }
  darakaraka: {graha: , degree: }

chara_dasha:
  sequence:
    - {rasi: , start: , end: }

narayana_dasha:
  sequence:
    - {rasi: , start: , end: }

# Divisional Charts
navamsa:
  lagna: {rasi: , degree: }
  surya: {rasi: }
  chandra: {rasi: }
  # ... all 9 grahas

dasamsa:
  lagna: {rasi: , degree: }
  # ... all 9 grahas

# Additional divisional charts as needed (D-2, D-4, D-7, D-12, D-24, D-60)

# Ashtakavarga
ashtakavarga:
  sav: [b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12]
  bav:
    surya: [12 scores]
    chandra: [12 scores]
    mangal: [12 scores]
    budha: [12 scores]
    guru: [12 scores]
    shukra: [12 scores]
    shani: [12 scores]

# Shadbala
shadbala:
  surya: {total: , rank: }
  chandra: {total: , rank: }
  mangal: {total: , rank: }
  budha: {total: , rank: }
  guru: {total: , rank: }
  shukra: {total: , rank: }
  shani: {total: , rank: }

# Additional Dasha Systems
yogini_dasha:
  sequence:
    - {yogini: , lord: , start: , end: }

# Arudha Padas
arudha_padas:
  AL: {rasi: }
  A2: {rasi: }
  A3: {rasi: }
  A4: {rasi: }
  A5: {rasi: }
  A6: {rasi: }
  A7: {rasi: }
  A8: {rasi: }
  A9: {rasi: }
  A10: {rasi: }
  A11: {rasi: }
  A12: {rasi: }
  UL: {rasi: }
```

---

## Specialist Interface — Standard Findings Format

All specialists return structured findings in this format (not narrative):

```markdown
## System: [Parashari/Jaimini/KP/Nadi/Tajaka]
## Query: [restated question — neutrally framed]

### Key Findings
| # | Finding | Classification | Strength | Evidence |
|---|---------|---------------|----------|----------|
| 1 | [specific finding] | FAVORABLE / UNFAVORABLE / NEUTRAL | HIGH/MED/LOW | [graha, bhava, rule citation] |

### Dasha Assessment (if applicable)
| Dasha System | Current Period | Theme | Supports Query? | Confidence |
|---|---|---|---|---|
| [system name] | [period] | [theme] | YES/NO/PARTIAL | HIGH/MED/LOW |

### Timing Windows
| Window | Dates | Nature | Trigger |
|---|---|---|---|
| [label] | [start - end] | FAVORABLE / CAUTION | [what activates it] |

### Remedials (system-specific)
| # | Remedy | Type | For which graha/issue | When to begin | Duration | Classical basis |
|---|--------|------|----------------------|---------------|----------|----------------|
| 1 | [specific remedy] | Mantra/Gem/Charity/Behavioral | [target] | [timing] | [how long] | [text reference] |

### Remedial Confidence
- Remedials above are prescribed per [system name] tradition
- Cross-system agreement needed before final prescription: YES/NO

### Confidence Statement
- System-level confidence: HIGH / MODERATE / LOW
- Data limitations: [what was missing or couldn't be assessed]
- Key assumption: [single most important assumption this analysis rests on]
```

---

## Astrobot Orchestrator Design (~200 lines)

### Responsibility 1: Query Analysis & Dispatch

1. Read the user's question
2. Restate it neutrally (strip emotional framing)
3. Read birth_data.yaml + check what's populated in extensions.yaml
4. Spawn all specialists whose data is available (in parallel)
5. Pass each specialist: the neutral question + relevant data sections

### Responsibility 2: Convergence & Scorecard

1. Collect structured findings from all specialists
2. Pool findings into the Floodlight Scorecard (FAVORABLE / UNFAVORABLE columns)
3. Count system convergence:
   - 3+ systems agree on direction → HIGH confidence
   - 2 systems agree → MODERATE
   - Only 1 supports → LOW
4. Compute: NET, MARGIN, Confidence (lower of margin-confidence and convergence-confidence), Direction
5. Merge remedials — flag where multiple systems prescribe the same remedy

### Responsibility 3: Reading Generation

1. Select appropriate template from `.claude_kb/templates/`
2. Write the reading:
   - Scorecard FIRST (mandatory — no narrative before scorecard)
   - Narrative EXPLAINS the scorecard verdict
   - Remedial plan with cross-system agreement markers
   - Final Reflection (self-critique, weakest assumption, genuine ambiguity)
3. Save to `readings/<person_name>/YYYY-MM-DD_<type>.md`

### Anti-Bias Rules (architectural + procedural)

**Architectural** (built into the multi-agent design):
- Each specialist starts with clean context — no access to other specialists' conclusions
- Specialists return structured data, not narrative — no story to confirm
- Convergence is mechanical — count agreements, report confidence

**Procedural** (enforced in astrobot's prompt):
1. **Scorecard-first gate**: No narrative conclusion until scorecard numbers are computed
2. **Steel-man rule**: For each direction, state the strongest counter-argument
3. **Classification lock**: Classifications come from scorecard verdict, not narrative impression
4. **User-frame quarantine**: Restate the question neutrally before dispatching
5. **Reground checkpoint**: Re-read birth_data.yaml before synthesis

### What stays with astrobot:
- Honesty Mandate (classification markers, severity distinctions, unvarnished delivery)
- Output format rules (Markdown only, data separation principle)
- Template selection and storage conventions
- Final Reflection section
- Follow-up conversation handling

### What moves to specialists:
- All system-specific analysis
- Yoga identification and stress-testing → parashari
- Dasha computation/interpretation → each system's specialist
- Divisional chart analysis → parashari + jaimini
- Transit analysis → each system contributes its transit rules
- Arudha padas → jaimini
- KP sub-lord analysis → kp

---

## Specialist Agent Designs

### parashari.md (~150 lines)
- **Tradition**: BPHS (Brihat Parashara Hora Shastra)
- **Scope**: Graha drishti, bhava analysis, yoga identification + stress-testing, functional nature per lagna, divisional charts (D-9, D-10, etc.), Vimshottari + Yogini dasha interpretation
- **Data reads**: birth_data.yaml + extensions.yaml (AV, Shadbala, divisional charts, yogini_dasha)
- **Knowledgebase**: planets.yaml, houses.yaml, functional_nature.yaml, yogas.yaml, vimsottari_dasa.yaml, strength.yaml, divisional_charts.yaml, ashtakavarga.yaml
- **Can consult**: astropdf for rule verification
- **Returns**: Standard findings format

### jaimini.md (~120 lines)
- **Tradition**: Jaimini Sutras
- **Scope**: Chara karakas (AK through DK), rasi drishti, arudha padas (AL, A7, A10, UL), Chara dasha + Narayana dasha, Karakamsa analysis, argala/virodhargala
- **Data reads**: birth_data.yaml + extensions.yaml (chara_karakas, chara_dasha, narayana_dasha, arudha_padas, navamsa)
- **Knowledgebase**: karakas.yaml, aspects_argalas.yaml, arudha_padas.yaml, other_dasas.yaml
- **Returns**: Standard findings format

### kp.md (~120 lines)
- **Tradition**: Krishnamurti Paddhati
- **Scope**: Sub-lord analysis for all 12 cusps, significator mapping (planet → star lord → sub lord), ruling planets for timing, KP house groupings
- **Data reads**: birth_data.yaml + extensions.yaml (kp_cusps, kp_planet_positions)
- **Knowledgebase**: houses.yaml (significations), planets.yaml (relationships)
- **Returns**: Standard findings format

### nadi.md (~100 lines)
- **Tradition**: Nadi Jyotish (Bhrigu/Chandra Kala Nadi style)
- **Scope**: Nakshatra-level interpretation, conjunction analysis by nakshatra lord chains, parivritti dasha, nakshatra-based transit analysis
- **Data reads**: birth_data.yaml + extensions.yaml
- **Knowledgebase**: planets.yaml (nakshatra data), transits.yaml
- **Returns**: Standard findings format

### tajaka.md (~100 lines)
- **Tradition**: Tajaka (Varshaphala / Annual Chart)
- **Scope**: Solar return chart analysis, 16 Tajaka yogas, 36 sahams, Muntha, year lord
- **Data reads**: birth_data.yaml + solar return chart data
- **Knowledgebase**: tajaka.yaml
- **Returns**: Standard findings format

### prashna.md (~80 lines)
- **Tradition**: Horary Astrology
- **Scope**: Moment chart casting, aroodha analysis, mandi/gulika, immediate answer derivation
- **Data reads**: Moment of question (not birth_data.yaml)
- **Knowledgebase**: muhurta.yaml, houses.yaml
- **Returns**: Standard findings format
- **Dispatch**: Only on explicit horary questions

### muhurta.md (~100 lines)
- **Tradition**: Electional Astrology
- **Scope**: Panchanga shuddhi (tithi/vara/nakshatra/yoga/karana), tarabala, chandrabala, activity-specific timing rules, transit fitness
- **Data reads**: birth_data.yaml (natal Moon) + transit data
- **Knowledgebase**: muhurta.yaml, transits.yaml
- **Returns**: Standard findings format
- **Dispatch**: Only on timing/muhurta questions

---

## What Stays Unchanged

- `astropdf.md` — reference lookup agent (no changes)
- `.claude_kb/reference/` — all 22 YAML knowledgebase files (no changes)
- `.claude_kb/templates/` — reading templates (minor adjustments to add convergence sections)
- `readings/` directory structure and naming conventions
- `scorecards.yaml` — Floodlight Scorecard framework (used by astrobot orchestrator)

---

## Migration Path

1. Create extensions.yaml template
2. Create 7 specialist agent files
3. Rewrite astrobot.md as orchestrator (~200 lines)
4. Update templates to include convergence/multi-system sections
5. Enrich one existing person's data as a test case
6. Run a test reading through the new architecture
7. Iterate based on results
