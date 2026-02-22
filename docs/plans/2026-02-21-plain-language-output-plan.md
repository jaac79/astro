# Plain Language Output Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make all astrobot readings accessible to a common person by adding a plain-language layer above every technical section, with jyotish details in collapsible blocks.

**Architecture:** The astrobot orchestrator receives raw technical findings from specialists (unchanged) and translates them into two-layer output: plain language first, collapsible technical basis second. Reading templates enforce this structure.

**Tech Stack:** Markdown agent configuration files, Markdown reading templates.

---

## Task 1: Add Two-Layer Output Rules to Astrobot Orchestrator

**Files:**
- Modify: `.claude/agents/astrobot.md:113-121` (after "Output Format" section, before "Convergence & Confidence")

**Step 1: Add the Two-Layer Output Rules section**

Insert the following new section after line 160 (after the `---` separator following "When User Provides Birth Details") and before the "Convergence & Confidence" section in `.claude/agents/astrobot.md`:

```markdown
## Two-Layer Output Rules

Every prediction, finding, and assessment in the final reading MUST use a two-layer format. This is NON-NEGOTIABLE. The reading is for a common person, not a jyotish practitioner.

### Layer 1: Plain Language (MANDATORY, shown first)
- Written for someone with ZERO jyotish knowledge
- No Sanskrit terms, no abbreviations (Ra-Ve, H8, PD, MD, AD)
- No house numbers — say "your career zone" not "10th house"
- No planet dignities — say "your career planet is at its strongest" not "Jupiter exalted in Katakam"
- No dasha terminology — say "the current planetary period" not "Rahu-Venus bhukti"
- Dates in plain format: "June 2026" not "2026-06-13"
- Use life-domain language: money, career, relationships, travel, health
- State WHAT happens, WHEN, and HOW CONFIDENT you are
- Tone: professional, clear, direct. Like a financial advisor writing to a client.
- Classification markers stay: FAVORABLE / MIXED / DIFFICULT

### Layer 2: Technical Basis (collapsible, shown after each plain section)
- Contains all jyotish terminology, dasha codes, house numbers, dignities
- Wrapped in HTML details/summary tags:
  ```
  <details><summary>Technical basis</summary>

  [jyotish content here]

  </details>
  ```
- Lists which systems agree (Parashari, Nadi, Transit, Jaimini, KP)
- Shows the scorecard data that produced the plain-language conclusion
- Scorecard tables go HERE, not in the plain layer

### The "Why this matters now" Bridge
Between the plain prediction and the collapsible technical section, include a 1-2 sentence bridge in a blockquote:
- Uses SIMPLIFIED astrological language — not raw jyotish, not fully plain
- Connects the prediction to its underlying logic for curious readers
- Example: "Your career planet enters its strongest position in 12 years, landing in your money zone" (not "Jupiter exalted in Katakam H2")

### Translation Dictionary
When writing Layer 1, translate these concepts:

| Jyotish Term | Plain Language |
|---|---|
| Mahadasha / MD | your major life period / the 18-year cycle |
| Antardasha / AD / bhukti | the current sub-period / the phase within that cycle |
| Pratyantardasha / PD | the current micro-phase |
| Rahu MD | the current 18-year life cycle (focused on ambition and unconventional paths) |
| Venus bhukti | a 3-year phase focused on creativity, relationships, and financial growth |
| Saturn bhukti | a phase focused on discipline, restructuring, and hard-won gains |
| Mercury bhukti | a phase focused on skills, communication, and career rebuilding |
| H1 / 1st house / lagna | your personality and health zone |
| H2 / 2nd house | your money and family zone |
| H3 / 3rd house | your effort, communication, and courage zone |
| H4 / 4th house | your home and emotional foundation zone |
| H5 / 5th house | your creativity, children, and intelligence zone |
| H6 / 6th house | your competition and health challenges zone |
| H7 / 7th house | your partnerships and marriage zone |
| H8 / 8th house | your transformation and hidden resources zone |
| H9 / 9th house | your fortune, higher learning, and long-distance zone |
| H10 / 10th house | your career and public reputation zone |
| H11 / 11th house | your gains and fulfillment zone |
| H12 / 12th house | your foreign connections and spiritual growth zone |
| Exalted | at its strongest position |
| Debilitated | at its weakest position |
| Own sign | in its home territory |
| Friend sign | in a supportive position |
| Enemy sign | in an uncomfortable position |
| Neecha Bhanga Raja Yoga | a weakness that converts into unexpected strength |
| Sade Sati | a 7.5-year period of restructuring (Saturn's influence on your mind and finances) |
| Kantaka Shani | a period of career pressure from Saturn |
| Transit | a planet's current position in the sky (vs. where it was at birth) |
| Rahu | the shadow planet driving ambition, foreign connections, and unconventional paths |
| Ketu | the shadow planet driving detachment, spirituality, and past-life patterns |
| Yogakaraka | the single most beneficial planet for your chart |
| Functional benefic | a planet that naturally helps your specific chart |
| Functional malefic | a planet that creates challenges for your specific chart |
| Nakshatra | the star-constellation a planet occupies (finer than zodiac sign) |
| Drishti / aspect | a planet's gaze or influence on another area of your chart |
| Conjunction | two planets sitting together, amplifying each other |
| Retrograde | a planet in intensified mode (appears to move backward) |
| Combust | a planet too close to the Sun, losing its independent voice |
| Upachaya | a zone where challenges improve over time |
| Dusthana | a zone of difficulty (health, conflict, or transformation) |
| Trikona | a zone of good fortune (luck, creativity, or dharma) |
| Kendra | a pillar zone (self, home, partnerships, or career) |

### Two-Layer Format Examples

**Example 1: Timeline prediction**

```markdown
## June 2026: A Major Financial Turning Point

Your best financial period in years begins here. Expect a noticeable
improvement in income -- possibly from a new role, a raise, or
foreign-sourced revenue. Creative and intellectual work pays off
especially well during this window.

This momentum sustains through December 2026. Opportunities that
present themselves during this window deserve serious evaluation.

**Confidence:** HIGH (3 systems agree)

> **Why this matters now:** Your career planet enters its strongest
> position in 12 years, landing in your money zone. Meanwhile, the
> phase ruling your life shifts to your most beneficial planet.

<details><summary>Technical basis</summary>

- Dasha: Ra-Ve-Venus PD (Venus own sub-period in Venus bhukti)
- Venus: 5th/12th lord in H8 (Makaram), sole functional benefic for Mithunam lagna
- Transit: Jupiter exalted in Katakam (H2 -- wealth house)
- Venus bhukti begins Jun 13, 2026
- Systems: Parashari, Nadi, Transit | Confidence: HIGH

</details>
```

**Example 2: Year summary**

```markdown
## 2024: Career Crystallization

This year marks a decisive career shift. The professional direction
that began forming in late 2022 reaches a clear resolution between
April and September 2024.

Key developments:
- A significant career decision in the April-September window, likely
  involving technology or international connections
- Financial improvement following the career move, with a 3-4 month lag
- Year-end income exceeds year-start levels

This is an action window. Opportunities that present themselves should
be evaluated seriously.

**Overall: FAVORABLE | Confidence: HIGH**

> **Why this matters now:** The planet driving your 18-year ambition
> cycle activates its own micro-phase within a career-focused period.
> Your career planet's transit supports gains from new directions.

<details><summary>Technical basis</summary>

**Active dasha:** Rahu-Mercury (full year)
**Key PDs:** Ra-Me-Rahu (Apr-Sep) -- pivotal; Ra-Me-Jupiter (Sep-Jan 2025) -- protective
**Saturn transit:** Kumbham (H9 from lagna, H3 from Moon)
**Jupiter transit:** Mesham (H11) then Rishabham (H12) from lagna

| # | Finding | Classification | Systems |
|---|---------|---------------|---------|
| 1 | Rahu PD in Mercury bhukti = triple Rahu activation | FAVORABLE | Pa, Na |
| 2 | Transit Rahu on natal H10 (Sun+Mercury) | FAVORABLE | Pa, Tr |
| 3 | Jupiter H11 from lagna (gains) first half | FAVORABLE | Pa, Tr |
| 4 | Jupiter H12 (expenses) second half | UNFAVORABLE | Pa, Tr |

</details>
```

**Example 3: Caution window**

```markdown
## October-November 2025: Exercise Caution

This is a high-risk window for accidents, impulsive decisions, and
unnecessary conflict. The aggressive and disruptive energies in your
chart are simultaneously activated. Drive carefully, avoid
confrontational situations, and postpone risky physical activities.

**Confidence:** HIGH (3 systems agree) | **Severity:** SEVERE

> **Why this matters now:** Two conflict-prone planets that sit together
> in your chart are simultaneously activated by the current planetary
> period, creating a concentrated window of volatile energy.

<details><summary>Technical basis</summary>

- Dasha: Ra-Ke-Mars PD
- Mars conjunct Ketu natally in H9 (Kumbham)
- Mars = 6th+11th lord (competition, conflict, gains through battle)
- Transit nodal return (Rahu-Ketu on natal axis)
- Systems: Parashari, Nadi, Transit | Confidence: HIGH

</details>
```
```

**Step 2: Update Step 6 in the Workflow section**

In the same file, modify Step 6 "Write the Reading" (around line 114-121) to reference the two-layer format. Replace:

```markdown
### Step 6: Write the Reading
1. Select the appropriate template from `.claude_kb/templates/`
2. Fill in all structured sections
3. Write the narrative — it EXPLAINS the scorecard, it does not override it
4. Merge remedials from all specialists — flag cross-system agreements
5. Write the Final Reflection (self-critique, weakest assumption, genuine ambiguity)
6. Save to `readings/<person>/YYYY-MM-DD_<type>.md`
```

With:

```markdown
### Step 6: Write the Reading
1. Select the appropriate template from `.claude_kb/templates/`
2. **Apply Two-Layer Output Rules for EVERY section** (see above):
   - Write the plain-language layer FIRST — no jyotish terms, no abbreviations
   - Add the "Why this matters now" bridge in a blockquote
   - Put scorecard tables and technical details in a collapsible `<details>` block
3. The plain narrative EXPLAINS the scorecard verdict — it does not override it
4. Merge remedials from all specialists — present remedials in plain language with technical basis collapsible
5. Write the Final Reflection (self-critique, weakest assumption, genuine ambiguity) — this section can use simplified astro language since it is meta-commentary
6. Save to `readings/<person>/YYYY-MM-DD_<type>.md`
```

**Step 3: Commit**

```bash
git add .claude/agents/astrobot.md
git commit -m "feat: add two-layer output rules to astrobot orchestrator

Adds translation dictionary, format examples, and bridge explanation
rules so all readings have plain language first with collapsible
technical details."
```

---

## Task 2: Update Full Reading Template

**Files:**
- Modify: `.claude_kb/templates/full_reading.md`

**Step 1: Rewrite the template with two-layer structure**

Replace the entire content of `.claude_kb/templates/full_reading.md` with the two-layer version. Key changes:
- Every section gets a plain-language summary comment/instruction FIRST
- Technical tables move into `<details>` blocks
- "The Honest Assessment" and "Practical Guidance" stay as-is (already plain)

The new template should be:

```markdown
# Full Birth Chart Reading

**Data sources:** `birth_data.yaml` (natal positions) | `current_positions.yaml` (transits and dasha at reading time)

<!-- TWO-LAYER FORMAT: Every section below MUST have:
     1. Plain language summary (no jyotish terms) — FIRST
     2. "Why this matters" bridge (simplified astro language) — in blockquote
     3. Technical details — in <details> block
     See astrobot.md "Two-Layer Output Rules" for the translation dictionary. -->

---

## Who You Are — Personality and Life Direction

<!-- Plain language: Describe the native's core personality, life direction, strengths, and challenges.
     Write as if explaining to a friend who knows nothing about astrology.
     Cover: temperament, natural abilities, how others perceive them, core drive in life. -->

> **Why this matters:** <!-- 1-2 sentences connecting personality to the rising sign and its lord -->

<details><summary>Technical basis: Lagna and Lagna Lord</summary>

| Factor | Detail |
|--------|--------|
| Lagna rasi | |
| Degree & nakshatra/pada | |
| Lagna lord | |
| Lord placement (rasi, bhava, nakshatra) | |
| Dispositorship chain | rasi lord -> nakshatra lord -> condition |
| Dignity | |
| Shadbala rank | |
| Ashtakavarga (individual bindus / bhava SAV) | |
| Aspects received (Parashari + Jaimini) | |

</details>

---

## Your Mind and Emotional Nature

<!-- Plain language: How the native thinks, processes emotions, what makes them happy/anxious,
     their mental constitution, emotional patterns. -->

> **Why this matters:** <!-- Connect to Moon's sign, nakshatra, and house -->

<details><summary>Technical basis: Chandra</summary>

| Factor | Detail |
|--------|--------|
| Moon rasi, bhava, nakshatra, pada | |
| Paksha Bala (Shukla/Krishna) | |
| Waxing / waning | |
| Dispositorship chain | |
| Aspects on Moon | |

</details>

---

## Planetary Strengths and Challenges

<!-- Plain language: Summarize which life areas are naturally strong and which face challenges.
     E.g., "Career is well-supported but relationships require more effort."
     Do NOT list planets — describe life outcomes. -->

> **Why this matters:** <!-- Brief explanation of how planetary positions create these patterns -->

<details><summary>Technical basis: Graha Assessment</summary>

| Graha | Rasi | Bhava | Nakshatra/Pada | Dignity | Retro | Combust | Shadbala | AV Bindus | Navamsa | Vargottama |
|-------|------|-------|----------------|---------|-------|---------|----------|-----------|---------|------------|
| Surya | | | | | | | | | | |
| Chandra | | | | | | | | | | |
| Mangal | | | | | | | | | | |
| Budha | | | | | | | | | | |
| Guru | | | | | | | | | | |
| Shukra | | | | | | | | | | |
| Shani | | | | | | | | | | |
| Rahu | | | | | — | — | — | | | |
| Ketu | | | | | — | — | — | | | |

### Dispositorship Chains
<!-- For each graha: rasi lord -> nakshatra lord -> that lord's condition -->

### Interaction Web
<!-- Key mutual aspects, shared nakshatra lords, tension axes -->

</details>

---

## Life Areas in Detail

<!-- For each relevant life area, write a plain-language assessment FIRST.
     Cover: Career, Finances, Relationships, Health, Family, Travel/Foreign, Spirituality.
     Only include areas relevant to the reading.
     Technical bhava analysis goes in collapsible blocks. -->

### Career and Professional Life

<!-- Plain language: What kind of career suits them, current trajectory, timing of key shifts -->

> **Why this matters:** <!-- Connect to career-related planetary positions -->

<details><summary>Technical basis: Bhava 10, 6, 2, 7</summary>

| Bhava | Rasi | Occupants | Lord | Lord placement | Kaaraka | Kaaraka strength | SAV | Key aspects | Argala |
|-------|------|-----------|------|---------------|---------|-----------------|-----|-------------|--------|
| | | | | | | | | | |

</details>

### Finances and Wealth

<!-- Plain language: Earning patterns, financial strengths/weaknesses, timing of gains -->

<details><summary>Technical basis: Bhava 2, 11, 5</summary>
<!-- Technical table -->
</details>

### Relationships and Marriage

<!-- Plain language: Relationship patterns, compatibility factors, timing -->

<details><summary>Technical basis: Bhava 7, 5, 4</summary>
<!-- Technical table -->
</details>

### Health and Vitality

<!-- Plain language: Vulnerable areas, overall constitution, periods to watch -->

<details><summary>Technical basis: Bhava 1, 6, 8</summary>
<!-- Technical table -->
</details>

### Family and Home

<!-- Plain language: Family dynamics, property, domestic life -->

<details><summary>Technical basis: Bhava 4, 2, 5</summary>
<!-- Technical table -->
</details>

---

## Special Strengths in Your Chart

<!-- Plain language: Describe yogas as life-advantages, not technical formations.
     E.g., "You have a rare combination that converts early-career struggles into unexpected success"
     NOT "Neecha Bhanga Raja Yoga formed by Mercury debilitated with Jupiter exalted as dispositor" -->

> **Why this matters:** <!-- Simplified explanation of yoga mechanics -->

<details><summary>Technical basis: Yoga Assessment</summary>

| Yoga | Grahas involved | Bhavas | Status | Yoga lord Shadbala | Navamsa dignity | Activation dasha | Source |
|------|----------------|--------|--------|-------------------|-----------------|-----------------|--------|
| | | | FULLY_FORMED_STRONG / FORMED_BUT_WEAKENED / BROKEN_CANCELLED | | | | |

</details>

---

## Current Life Phase and Timing

<!-- Plain language: What period of life are they in? What does it mean?
     Describe the current phase, what's coming next, and when the energy shifts.
     Use month/year dates, not ISO dates. -->

> **Why this matters:** <!-- Connect to current dasha period -->

<details><summary>Technical basis: Dasha Analysis & Convergence</summary>

| System | Current Period | Period Lord Natal Strength | Theme | Window |
|--------|---------------|---------------------------|-------|--------|
| Vimshottari | MD / AD / PD | | | |
| Yogini | | | | |
| Chara (Jaimini) | | | | |
| Narayana | | | | |

**Convergence:** <!-- HIGH / MODERATE / LOW -->

</details>

---

## What's Happening in the Sky Right Now

<!-- Plain language: How current planetary movements affect the native.
     E.g., "Saturn's current position is putting pressure on your career zone,
     but Jupiter's position is protecting your finances." -->

<details><summary>Technical basis: Transit Overlay</summary>

<!-- Current transit positions, dasha-transit activation, hot zones, special timing -->

</details>

---

## Multi-System Confidence

<!-- Plain language: "This reading was analyzed using N independent systems.
     They agree on X. They disagree on Y. Overall confidence is Z." -->

<details><summary>Technical basis: System details</summary>

| System | Consulted | Data Available | Confidence |
|--------|-----------|---------------|------------|
| Parashari | YES/NO | | HIGH/MED/LOW |
| Jaimini | YES/NO | | HIGH/MED/LOW |
| KP | YES/NO | | HIGH/MED/LOW |
| Nadi | YES/NO | | HIGH/MED/LOW |
| Tajaka | YES/NO | | HIGH/MED/LOW |

</details>

---

## The Honest Assessment

<!-- This section stays in plain language — it already is accessible.
     What is genuinely going well and WHY.
     What is genuinely difficult and WHY, with timing.
     What the native should be alert to. -->

---

## Practical Guidance

<!-- This section stays in plain language.
     WORK ON: specific actions supported by current timing.
     WAIT/SURRENDER: areas where patience serves better.
     REMEDIALS: presented in plain language with classical basis in collapsible block. -->

**WORK ON:**
<!-- controllable actions -->

**WAIT / SURRENDER:**
<!-- karmic timing areas -->

**REMEDIALS:**
<!-- Plain language remedial recommendations -->

<details><summary>Technical basis for remedials</summary>

| Remedy | Type | Target graha | When to begin | Duration | Classical basis |
|--------|------|-------------|--------------|----------|---------------|
| | | | | | |

</details>

---

## Final Reflection

<!-- Meta-commentary: weakest assumption, thinnest evidence, coherence assessment.
     This section can use simplified astro language since it is self-critique. -->
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/full_reading.md
git commit -m "feat: update full reading template with two-layer format

Plain language summaries first, technical details in collapsible blocks."
```

---

## Task 3: Update Dasha Reading Template

**Files:**
- Modify: `.claude_kb/templates/dasha_reading.md`

**Step 1: Rewrite with two-layer structure**

Replace entire content of `.claude_kb/templates/dasha_reading.md`:

```markdown
# Dasha Reading — Life Period Analysis

**Data sources:** `birth_data.yaml` (natal positions) | `current_positions.yaml` (transits and dasha at reading time)
**Period analyzed:** <!-- e.g., "The current 3-year phase (June 2026 - May 2029)" -->

<!-- TWO-LAYER FORMAT: See astrobot.md "Two-Layer Output Rules" -->

---

## What This Period Means for Your Life

<!-- Plain language: 2-3 paragraphs explaining what this life phase is about.
     What themes dominate? What life areas are activated? What is the overall trajectory?
     E.g., "You're entering a 3-year phase focused on financial growth and creative expression.
     After years of restructuring, this is when things start paying off." -->

**Overall direction:** FAVORABLE / MIXED / DIFFICULT
**Duration:** <!-- "Month Year to Month Year (N years)" -->

> **Why this matters now:** <!-- Connect the period to the native's broader life cycle -->

<details><summary>Technical basis: Dasha Lords</summary>

| Factor | Mahadasha Lord | Antardasha Lord |
|--------|---------------|-----------------|
| Graha | | |
| Rasi / Bhava | | |
| Nakshatra / Pada | | |
| Dignity | | |
| Retrograde | | |
| Houses owned | | |
| Shadbala (total / rank) | | |
| AV bindus / bhava SAV | | |
| Navamsa (rasi / dignity) | | |
| Dispositorship chain | | |
| Aspects given | | |
| Aspects received | | |

### Dasha Lord Interaction
| Factor | Detail |
|--------|--------|
| MD-AD natal relationship | |
| Mutual position | |
| Shared nakshatra lord | |
| Support or undermine | |

</details>

---

## Life Areas Activated in This Period

<!-- Plain language for each area. Only include areas this dasha activates. -->

### Career
<!-- What happens to your career during this period? -->

### Finances
<!-- Income trajectory, investment climate, spending patterns -->

### Relationships
<!-- Partnership dynamics, family, social life -->

### Health
<!-- What to watch, vulnerable windows -->

<details><summary>Technical basis: Bhava Activation</summary>

| Bhava | Activated by | Theme | SAV strength |
|-------|-------------|-------|-------------|
| | lord ownership / placement / aspect | | |

</details>

---

## Sub-Period Timeline

<!-- For each sub-period, write a plain-language summary.
     Use month/year dates. State what happens, not which planet rules. -->

### [Month Year] - [Month Year]: [Plain Title]

<!-- E.g., "June - December 2026: Financial Breakthrough Window"
     Plain description of what this sub-period brings. -->

**Confidence:** HIGH / MODERATE / LOW

> **Why this matters now:** <!-- 1-sentence bridge -->

<details><summary>Technical basis</summary>

<!-- PD lord details, transit triggers, scorecard snippet -->

</details>

<!-- Repeat for each sub-period -->

---

## Strengths Active in This Period

<!-- Plain language: What special advantages does this period unlock?
     E.g., "A rare combination in your chart — where early struggle converts to unexpected success —
     is fully activated during this phase." -->

<details><summary>Technical basis: Yoga Activation</summary>

| Yoga | Activated by | Status | Peak period |
|------|-------------|--------|-------------|
| | | | |

</details>

---

## Scorecard Summary

**Overall: FAVORABLE / MIXED / DIFFICULT**
**Confidence:** HIGH / MODERATE / LOW
**Strongest factor working FOR you:** <!-- plain language -->
**Strongest factor working AGAINST you:** <!-- plain language -->

<details><summary>Technical basis: Floodlight Scorecard</summary>

### Favorable Indicators
| # | Indicator | Graha/Bhava | Dignity | Base | Modifiers | Score |
|---|-----------|-------------|---------|------|-----------|-------|
| | | | | | | |

### Unfavorable Indicators
| # | Indicator | Graha/Bhava | Dignity | Base | Modifiers | Score |
|---|-----------|-------------|---------|------|-----------|-------|
| | | | | | | |

| Favorable Total | Unfavorable Total | NET | MARGIN | Confidence | Direction |
|-----------------|-------------------|-----|--------|------------|-----------|
| | | | | | |

</details>

---

## The Honest Assessment
<!-- Plain language: what this period genuinely offers, demands, peak challenge windows -->

---

## Practical Guidance

**WORK ON:**
<!-- Actions aligned with this period's energy -->

**WAIT / SURRENDER:**
<!-- What requires patience during this period -->

**REMEDIALS:**
<!-- Plain language remedials -->

<details><summary>Technical basis for remedials</summary>
<!-- Remedy table with classical basis -->
</details>

---

## What Comes Next

<!-- Plain language: When does this period end? What follows? How to prepare? -->
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/dasha_reading.md
git commit -m "feat: update dasha reading template with two-layer format"
```

---

## Task 4: Update Annual Prediction Template

**Files:**
- Modify: `.claude_kb/templates/annual_prediction.md`

**Step 1: Rewrite with two-layer structure**

Replace entire content of `.claude_kb/templates/annual_prediction.md`:

```markdown
# Annual Prediction

**Data sources:** `birth_data.yaml` (natal positions) | `current_positions.yaml` (transits and dasha at reading time)
**Prediction year:** <!-- e.g., 2026 -->

<!-- TWO-LAYER FORMAT: See astrobot.md "Two-Layer Output Rules" -->

---

## Year at a Glance

<!-- Plain language: one paragraph summarizing this year. Already plain — keep it that way. -->

**Year rating:** <!-- 1-10, with plain meaning: 1-3 = challenging, 4-6 = mixed, 7-8 = favorable, 9-10 = exceptional -->
**Best quarter:** <!-- Q1 / Q2 / Q3 / Q4 -->
**Hardest quarter:** <!-- Q1 / Q2 / Q3 / Q4 -->
**Defining theme:** <!-- One sentence -->

---

## The Planetary Weather This Year

<!-- Plain language: "Saturn is putting pressure on your career zone this year, but Jupiter
     is boosting your finances. The overall weather is mixed but trending positive." -->

> **Why this matters:** <!-- Simplified explanation of key transits -->

<details><summary>Technical basis: Dasha and Transits</summary>

### Dasha periods active this year
| Period | Lord | Start | End | Lord natal (rasi/bhava/dignity) | Houses owned | Theme |
|--------|------|-------|-----|---------------------------------|-------------|-------|
| | | | | | | |

### Major transits
| Graha | Rasi at year start | Sign changes | From Chandra | From Lagna | Key contacts |
|-------|-------------------|-------------|-------------|-----------|-------------|
| Shani | | | | | |
| Guru | | | | | |
| Rahu | | | | | |
| Ketu | | | | | |

### Eclipses
| Date | Type | Rasi | Natal impact | Significance |
|------|------|------|-------------|-------------|
| | | | | |

</details>

---

## Life Area Predictions

### Career and Professional Life

<!-- Plain language: What happens to your career this year?
     Peak months, what to pursue, what to avoid.
     E.g., "The April-September window is your strongest career period.
     A decision you make here defines the next 3 years." -->

**Overall: FAVORABLE / MIXED / DIFFICULT**
**Peak months:** | **Caution months:**
**Confidence:** HIGH / MODERATE / LOW

> **Why this matters:** <!-- Career planet positions -->

<details><summary>Technical basis</summary>

| # | Indicator | Direction | Weight | Score |
|---|-----------|-----------|--------|-------|
| | | FAV / UNFAV | | |

Favorable total: XX | Unfavorable total: YY | Margin: 0.XX

</details>

### Finances and Wealth

<!-- Plain language: Income trajectory, investment climate, spending patterns this year. -->

**Overall: FAVORABLE / MIXED / DIFFICULT**
**Peak months:** | **Caution months:**

<details><summary>Technical basis</summary>
<!-- Scorecard table -->
</details>

### Health and Vitality

<!-- Plain language: Vulnerable periods, what to watch, preventive guidance. -->

**Overall: FAVORABLE / MIXED / DIFFICULT**
**Vulnerable months:** | **Watch areas:**

<details><summary>Technical basis</summary>
<!-- Scorecard table -->
</details>

### Relationships and Marriage

<!-- Plain language: Partnership dynamics, romantic developments, family. -->

**Overall: FAVORABLE / MIXED / DIFFICULT**

<details><summary>Technical basis</summary>
<!-- Scorecard table -->
</details>

### Family and Home

<!-- Plain language: Family dynamics, property, domestic life. -->

**Overall: FAVORABLE / MIXED / DIFFICULT**

<details><summary>Technical basis</summary>
<!-- Scorecard table -->
</details>

### Travel and Foreign Connections

<!-- Plain language: Likely travel periods, international opportunities. -->

**Overall: FAVORABLE / MIXED / DIFFICULT**

<details><summary>Technical basis</summary>
<!-- Scorecard table -->
</details>

---

## Quarter-by-Quarter Summary

### Q1 (January - March)
<!-- Plain language: Tone, key developments, action or wait. Already plain — keep it. -->

### Q2 (April - June)
<!-- Plain language -->

### Q3 (July - September)
<!-- Plain language -->

### Q4 (October - December)
<!-- Plain language -->

---

## Multi-System Confidence

<!-- Plain language: how many systems were consulted, where they agree/disagree -->

<details><summary>Technical basis: System details</summary>

| System | Consulted | Data Available | Confidence |
|--------|-----------|---------------|------------|
| Parashari | YES/NO | | |
| Jaimini | YES/NO | | |
| KP | YES/NO | | |
| Nadi | YES/NO | | |
| Tajaka | YES/NO | | |

</details>

---

## The Honest Assessment
<!-- Plain language: best and hardest things about this year, the one thing to focus on -->

---

## Remedials for the Year

<!-- Plain language: what to do, when, and why. -->

<details><summary>Technical basis</summary>

| Graha | Weakness | Remedy type | Remedy | When to start | Duration |
|-------|----------|------------|--------|--------------|----------|
| | | | | | |

</details>

---

## Key Dates to Mark
<!-- Bullet list in plain language: "June 2026 — your financial momentum begins" -->
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/annual_prediction.md
git commit -m "feat: update annual prediction template with two-layer format"
```

---

## Task 5: Update Transit Reading Template

**Files:**
- Modify: `.claude_kb/templates/transit_reading.md`

**Step 1: Rewrite with two-layer structure**

Replace entire content of `.claude_kb/templates/transit_reading.md`:

```markdown
# Transit Reading — Current Planetary Weather

**Data sources:** `birth_data.yaml` (natal positions) | `current_positions.yaml` (transits and dasha at reading time)

<!-- TWO-LAYER FORMAT: See astrobot.md "Two-Layer Output Rules" -->

---

## The Current Weather

<!-- Plain language: What's the overall energy right now?
     E.g., "Right now, there's strong career pressure from Saturn, but Jupiter is protecting
     your finances. The shadow planets are activating your ambition-vs-purpose axis,
     creating a sense of being at a crossroads." -->

**Overall tone:** FAVORABLE / MIXED / DIFFICULT

---

## Saturn's Influence — The Restructuring Force

<!-- Plain language: Where is Saturn putting pressure? How long does it last?
     E.g., "Saturn is currently in your career zone, adding responsibilities and testing
     your professional foundation. This lasts until mid-2027. It's heavy but productive." -->

<details><summary>Technical basis</summary>
<!-- Saturn transit details, sade sati status, house position, duration -->
</details>

---

## Jupiter's Influence — The Expansion Force

<!-- Plain language: Where is Jupiter expanding/blessing?
     E.g., "Jupiter is in your money zone at its strongest possible position — a once-in-12-years
     event. This is your strongest financial transit in years." -->

<details><summary>Technical basis</summary>
<!-- Jupiter transit details -->
</details>

---

## The Shadow Planets — Karmic Pressure Points

<!-- Plain language: What life areas are Rahu and Ketu activating?
     E.g., "The shadow planets are currently on your ambition-detachment axis,
     creating tension between what you want and what you're ready to let go of." -->

<details><summary>Technical basis</summary>
<!-- Rahu-Ketu axis, natal contacts -->
</details>

---

## When Events Trigger

<!-- Plain language: Specific windows where the current planetary weather
     creates event-level timing.
     E.g., "The April-September window is when the career pressure crystallizes
     into a specific event — likely a job change or major project decision." -->

<details><summary>Technical basis: Dasha-Transit Activation</summary>

| Transit Graha | Natal Contact | Dasha Relevance | Event Window |
|--------------|---------------|-----------------|-------------|
| | | | |

</details>

---

## Scorecard

**Overall: FAVORABLE / MIXED / DIFFICULT**
**Confidence:** HIGH / MODERATE / LOW
**Strongest factor FOR you:** <!-- plain -->
**Strongest factor AGAINST you:** <!-- plain -->

<details><summary>Technical basis: Floodlight Scorecard</summary>

### Favorable Indicators
| # | Indicator | Graha/Bhava | Base | Modifiers | Score |
|---|-----------|-------------|------|-----------|-------|

### Unfavorable Indicators
| # | Indicator | Graha/Bhava | Base | Modifiers | Score |
|---|-----------|-------------|------|-----------|-------|

| Favorable Total | Unfavorable Total | NET | MARGIN | Confidence | Direction |
|-----------------|-------------------|-----|--------|------------|-----------|

</details>

---

## Special Timing Flags

<!-- Plain language: "You are currently in/approaching/leaving a 7.5-year Saturn restructuring period." -->

<details><summary>Technical basis</summary>

| Flag | Status | Phase | Duration |
|------|--------|-------|----------|
| Sade Sati | | | |
| Ashtama Shani | | | |
| Kantaka Shani | | | |

</details>

---

## The Honest Assessment
<!-- Plain language: what transits favor, what they challenge -->

---

## Practical Guidance

**Favorable windows:** <!-- dates and what they're good for -->
**Caution windows:** <!-- dates and what to avoid -->
**Remedials:** <!-- plain language -->

<details><summary>Technical basis for remedials</summary>
<!-- Remedy table -->
</details>

---

## What Changes Next
<!-- Plain language: upcoming shifts in the next 3-6 months and how to prepare -->
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/transit_reading.md
git commit -m "feat: update transit reading template with two-layer format"
```

---

## Task 6: Update Transit Timeline Template

**Files:**
- Modify: `.claude_kb/templates/transit_timeline.md`

**Step 1: Rewrite with two-layer structure**

Replace entire content of `.claude_kb/templates/transit_timeline.md`:

```markdown
# Transit Timeline

**Data sources:** `birth_data.yaml` (natal positions) | `current_positions.yaml` (transits and dasha at reading time)
**Timeline:** <!-- "Month Year to Month Year" -->

<!-- TWO-LAYER FORMAT: See astrobot.md "Two-Layer Output Rules" -->

---

## Where You Stand Today

<!-- Plain language: snapshot of your current situation astrologically.
     What phase of life? What planetary weather? What's the starting point? -->

<details><summary>Technical basis</summary>

**Current dasha:** MD / AD / PD

| Graha | Rasi | From Chandra | From Lagna |
|-------|------|-------------|-----------|
| Shani | | | |
| Guru | | | |
| Rahu | | | |
| Ketu | | | |

</details>

---

## The Road Ahead — Overview

<!-- Plain language: Is the next period trending up, down, or mixed? Where are the turning points?
     E.g., "The next two years trend strongly positive after a difficult start.
     June 2026 is the major turning point." -->

---

## Month-by-Month Walkthrough

### [Month Year] — [Plain Title]

<!-- Plain language: What happens this month? What to do or avoid?
     E.g., "February 2026 — The Heavy Stretch: Career feels stuck. Administrative obstacles pile up.
     This is not the month for bold moves — focus on patience and execution." -->

**Tone:** FAVORABLE / MIXED / DIFFICULT
**Action or wait:** ACT / WAIT / MIXED

> **Why this matters:** <!-- 1-sentence bridge -->

<details><summary>Technical basis</summary>

**Dasha:** <!-- MD-AD-PD -->
**Key transit:** <!-- most significant -->
**Hot zones:** <!-- bhavas receiving dual activation -->
**Scorecard:** F:XX vs U:YY | Margin: 0.XX | Confidence

</details>

<!-- Repeat for each month -->

---

## Best Windows — When to Act

<!-- Plain language table -->

| Window | What it's good for | Confidence |
|--------|-------------------|-----------|
| <!-- Month Year - Month Year --> | career moves / financial decisions / relationships / travel | |

<details><summary>Technical basis</summary>

| Window | Favorable factors | Systems agreeing |
|--------|------------------|-----------------|
| | | |

</details>

---

## Caution Windows — When to Wait

<!-- Plain language table -->

| Window | What to watch out for | Severity |
|--------|----------------------|----------|
| <!-- Month Year - Month Year --> | accidents / conflict / financial pressure / health | mild / moderate / severe |

<details><summary>Technical basis</summary>

| Window | Challenging factors | Remedials |
|--------|-------------------|-----------|
| | | |

</details>

---

## Turning Points

<!-- Plain language -->

| When | What Changes | From → To |
|------|-------------|-----------|
| <!-- Month Year --> | <!-- plain description --> | difficult → favorable / favorable → mixed / etc. |

<details><summary>Technical basis</summary>

| Date | Trigger | Technical detail |
|------|---------|-----------------|
| | transit ingress / dasha change | |

</details>

---

## The Honest Assessment
<!-- Plain language: overall trajectory, promises vs demands -->

---

## Key Dates to Mark
<!-- Plain language bullet list: "June 2026 — financial momentum begins" -->
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/transit_timeline.md
git commit -m "feat: update transit timeline template with two-layer format"
```

---

## Task 7: Update Quick Query Template

**Files:**
- Modify: `.claude_kb/templates/quick_query.md`

**Step 1: Rewrite with two-layer structure**

Replace entire content of `.claude_kb/templates/quick_query.md`:

```markdown
# Quick Query

**Data sources:** `birth_data.yaml` (natal positions) | `current_positions.yaml` (transits and dasha at reading time)
**Query:** <!-- The specific question being answered -->

<!-- TWO-LAYER FORMAT: See astrobot.md "Two-Layer Output Rules" -->

---

## The Answer

<!-- Plain language: Direct answer to the question. 2-4 sentences.
     State the verdict, the timing, and the confidence level.
     E.g., "Yes, this is a favorable period for a job change. The April-September window
     is the strongest. Act during this window rather than waiting." -->

**Verdict:** FAVORABLE / MIXED / DIFFICULT
**Confidence:** HIGH / MODERATE / LOW

---

## The Reasoning

<!-- Plain language: Why does the chart indicate this answer?
     3-5 bullet points explaining the key factors in life-domain language.
     E.g., "Your career planet is in a strong position supporting change."
     NOT "10th lord Jupiter exalted in H2 aspects H10" -->

> **Why this matters now:** <!-- Bridge explanation -->

<details><summary>Technical basis</summary>

### Relevant Chart Factors

#### Grahas bearing on this query
| Graha | Why relevant | Rasi | Bhava | Dignity | Dispositorship chain |
|-------|-------------|------|-------|---------|---------------------|
| | | | | | |

#### Bhavas bearing on this query
| Bhava | Why relevant | Lord | Lord placement | SAV |
|-------|-------------|------|---------------|-----|
| | | | | |

#### Relevant yogas
| Yoga | Status | Activation |
|------|--------|-----------|
| | | |

</details>

---

## Scorecard

**In favor:** <!-- plain 1-liner: "Strong career support, good timing, protective financial transit" -->
**Against:** <!-- plain 1-liner: "Some competitive pressure, expenses may increase" -->
**Net:** FAVORABLE / UNFAVORABLE — Confidence: HIGH / MODERATE / LOW

<details><summary>Technical basis: Floodlight Scorecard</summary>

### Favorable Indicators
| # | Indicator | Graha/Bhava | Base | Modifiers | Score |
|---|-----------|-------------|------|-----------|-------|

### Unfavorable Indicators
| # | Indicator | Graha/Bhava | Base | Modifiers | Score |
|---|-----------|-------------|------|-----------|-------|

| Favorable Total | Unfavorable Total | NET | MARGIN | Confidence | Direction |
|-----------------|-------------------|-----|--------|------------|-----------|

</details>

---

## Timing

**Best window:** <!-- "Month Year to Month Year — good for [action]" -->
**Caution window:** <!-- "Month Year to Month Year — avoid [action]" -->

<details><summary>Technical basis</summary>

**Current dasha:** <!-- MD / AD -->
| Transit graha | Impact on query | Window |
|--------------|-----------------|--------|
| | | |

</details>

---

## The Honest Answer
<!-- Plain language: direct, unvarnished. Classification: FAVORABLE / MIXED / DIFFICULT -->

---

## What To Do
<!-- Plain language: specific actions, timing, what to avoid -->

<details><summary>Technical basis for remedials</summary>
<!-- If remedials are recommended -->
</details>
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/quick_query.md
git commit -m "feat: update quick query template with two-layer format"
```

---

## Task 8: Create Timeline Reading Template (NEW)

**Files:**
- Create: `.claude_kb/templates/timeline_reading.md`

**Step 1: Write the new template**

Create `.claude_kb/templates/timeline_reading.md`:

```markdown
# Timeline Predictions

**Native:** <!-- Name -->
**Birth:** <!-- Date, Time, Place -->
**Timeline:** <!-- "Month Year to Month Year" -->
**Reading date:** <!-- Date -->

<!-- TWO-LAYER FORMAT: See astrobot.md "Two-Layer Output Rules"
     This template is for multi-year categorized timeline predictions.
     Categories: WEALTH, CAREER, FAMILY, PARADESA (foreign connections). -->

---

## Your Chart at a Glance

<!-- Plain language: 3-4 sentences summarizing who the native is astrologically.
     Personality type, core strengths, main life themes.
     E.g., "You are driven by intellectual curiosity and unconventional ambition.
     Your career path doesn't follow standard routes — it's built through self-effort
     and often involves foreign connections or technology." -->

<details><summary>Technical basis: Key chart factors</summary>

| Factor | Value | Category relevance |
|--------|-------|-------------------|
| Lagna | | |
| Lagna lord | | |
| Moon | | |
| Key yogas | | |
| Current MD | | |

</details>

---

## The Big Picture — Where You're Headed

<!-- Plain language: Overview of the entire timeline period.
     What's the trajectory? Where are the turning points?
     E.g., "The 2021-2025 period was about rebuilding after disruption.
     2026-2029 is the harvest. 2029-2032 is career authority at its peak.
     A fundamentally new chapter begins in late 2032." -->

---

## Year-by-Year Predictions

### [YEAR]

<!-- Plain language: 3-5 sentence summary of the year.
     What is the dominant theme? Is it a good year or tough year?
     What should you focus on? -->

**Year rating:** <!-- FAVORABLE / MIXED / DIFFICULT -->

<details><summary>Technical basis: Dasha and transits for this year</summary>

**Active dasha:** <!-- MD-AD -->
**Key PD transitions:** <!-- list -->
**Saturn transit:** <!-- position -->
**Jupiter transit:** <!-- position -->

</details>

#### Wealth

<!-- Plain language: Financial trajectory this year.
     Income changes, investment climate, spending patterns.
     Specific months where money moves. -->

**Trend:** FAVORABLE / MIXED / DIFFICULT
**Peak months:** <!-- e.g., "May - October" -->

> **Why this matters:** <!-- 1-sentence bridge -->

<details><summary>Technical basis</summary>

| # | Period | Event | Confidence | Systems |
|---|--------|-------|------------|---------|
| | | | | |

</details>

#### Career

<!-- Plain language: Professional developments this year.
     Job changes, promotions, skill development, recognition.
     Specific windows for action. -->

**Trend:** FAVORABLE / MIXED / DIFFICULT
**Peak months:**

<details><summary>Technical basis</summary>
<!-- Technical details -->
</details>

#### Family

<!-- Plain language: Family dynamics, relationships, domestic life.
     Celebrations, tensions, health of family members.
     Emotional climate at home. -->

**Trend:** FAVORABLE / MIXED / DIFFICULT

<details><summary>Technical basis</summary>
<!-- Technical details -->
</details>

#### Foreign Connections (Paradesa)

<!-- Plain language: International opportunities, travel, overseas income,
     foreign collaborations, immigration possibilities. -->

**Trend:** FAVORABLE / MIXED / DIFFICULT
**Peak months:**

<details><summary>Technical basis</summary>
<!-- Technical details -->
</details>

<!-- Repeat the year block for each year in the timeline -->

---

## Category Summaries

### Wealth Trajectory

<!-- Plain language table summarizing financial trend across all years -->

| Year | Trend | Key Development | Best Months |
|------|-------|----------------|-------------|
| | FAVORABLE / MIXED / DIFFICULT | <!-- 1-sentence --> | |

### Career Trajectory

| Year | Trend | Key Development | Best Months |
|------|-------|----------------|-------------|
| | | | |

### Family Trajectory

| Year | Trend | Key Development | Best Months |
|------|-------|----------------|-------------|
| | | | |

### Foreign Connections Trajectory

| Year | Trend | Key Development | Best Months |
|------|-------|----------------|-------------|
| | | | |

---

## Best Windows — When to Act

| Rank | Window | Best For | Confidence |
|------|--------|---------|-----------|
| 1 | <!-- Month Year - Month Year --> | <!-- wealth / career / family / foreign --> | |
| 2 | | | |
| 3 | | | |

<details><summary>Technical basis</summary>
<!-- Detailed factors for each window -->
</details>

---

## Caution Windows — When to Be Careful

| Rank | Window | Watch Out For | Severity |
|------|--------|--------------|----------|
| 1 | <!-- Month Year - Month Year --> | <!-- accidents / conflict / health / financial pressure --> | mild / moderate / severe |

<details><summary>Technical basis</summary>
<!-- Detailed factors for each window -->
</details>

---

## Turning Points

| When | What Changes | From → To |
|------|-------------|-----------|
| <!-- Month Year --> | <!-- plain description --> | difficult → favorable |

---

## Confidence and Limitations

<!-- Plain language: "This reading was analyzed using N systems.
     They agree strongly on X. The predictions for Y have lower confidence because Z.
     All dates have a margin of +/- 2-4 weeks." -->

<details><summary>Technical basis: Multi-system convergence</summary>

| Prediction | Systems agreeing | Confidence |
|-----------|-----------------|-----------|
| | | |

</details>

---

## The Honest Assessment
<!-- Plain language: the genuinely good news, the genuinely hard parts,
     and what the native should focus on. -->

---

## Remedials

<!-- Plain language remedial recommendations organized by period.
     E.g., "During the current difficult phase (until June 2026): practice patience,
     avoid impulsive decisions, and consider meditation for grounding." -->

<details><summary>Technical basis for remedials</summary>
<!-- Detailed remedy table with mantras, gemstones, classical basis -->
</details>

---

## Key Dates to Mark

<!-- Plain language bullet list.
     E.g., "- June 2026 — Your strongest financial period begins
            - December 2027 — The single best 5-month window in the next decade starts
            - October 2032 — A fundamentally new life chapter begins" -->
```

**Step 2: Commit**

```bash
git add .claude_kb/templates/timeline_reading.md
git commit -m "feat: create timeline reading template with two-layer format

New template for multi-year categorized predictions (WEALTH, CAREER,
FAMILY, PARADESA) with plain language first, technical basis collapsible."
```

---

## Task 9: Final Commit and Verification

**Step 1: Verify all files are consistent**

Check that all templates reference the Two-Layer Output Rules in astrobot.md:

```bash
grep -l "TWO-LAYER FORMAT" .claude_kb/templates/*.md
```

Expected: All updated templates should contain the reference comment.

**Step 2: Verify astrobot.md has the translation dictionary**

```bash
grep "Translation Dictionary" .claude/agents/astrobot.md
```

Expected: One match in the Two-Layer Output Rules section.

**Step 3: Create a summary commit if needed**

If individual commits were not made per task:

```bash
git add .claude/agents/astrobot.md .claude_kb/templates/
git commit -m "feat: implement two-layer output for all reading templates

- Add Two-Layer Output Rules to astrobot.md with translation dictionary
- Update full_reading, dasha_reading, annual_prediction, transit_reading,
  transit_timeline, quick_query templates
- Create new timeline_reading template for multi-year predictions
- Plain language first, collapsible technical basis second
- No jyotish terms in the plain layer"
```
