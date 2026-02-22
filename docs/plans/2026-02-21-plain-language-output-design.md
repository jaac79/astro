# Design: Plain Language Output for Astrobot Readings

**Date:** 2026-02-21
**Problem:** Readings are saturated with jyotish terminology (Ra-Sa-Ketu PD, H8 from lagna, Neecha Bhanga, etc.) making them inaccessible to a common reader.
**Goal:** Every reading has a plain-language layer first, with technical basis available separately.

---

## Design Decisions

1. **Specialist agents stay unchanged.** They remain pure technical data providers. No plain-language translation at the specialist level.
2. **Astrobot orchestrator does the translation.** It receives technical findings and produces two-layer output: plain first, technical collapsible.
3. **Reading templates enforce the format.** All templates updated to mandate the two-layer structure.
4. **Tone: Professional but accessible.** Clear, structured, informative. No jargon in the plain layer. Like a well-written financial advisor's letter.

---

## Changes Required

### Change 1: Astrobot Orchestrator (`astrobot.md`)

Add a new section **"Two-Layer Output Rules"** after the existing "Output Format" section.

**Content of the new section:**

```markdown
## Two-Layer Output Rules

Every prediction, finding, and assessment in the final reading MUST use a two-layer format:

### Layer 1: Plain Language (MANDATORY, shown first)
- Written for someone with ZERO jyotish knowledge
- No Sanskrit terms, no abbreviations (Ra-Ve, H8, PD, MD, AD)
- No house numbers (say "your career zone" not "10th house")
- No planet dignities (say "your career planet is at its strongest" not "Jupiter exalted in Katakam")
- No dasha terminology (say "the current planetary period" not "Rahu-Venus bhukti")
- Dates in plain format: "June 2026" not "2026-06-13"
- Use life-domain language: money, career, relationships, travel, health
- State WHAT happens, WHEN, and HOW CONFIDENT you are
- Tone: professional, clear, direct. Like a financial advisor writing to a client.

### Layer 2: Technical Basis (collapsible, shown after)
- Contains all jyotish terminology, dasha codes, house numbers, dignities
- Wrapped in HTML details/summary tags for collapsibility
- Lists which systems agree (Pa, Na, Tr, Ji, KP)
- Shows the scorecard data that produced the plain-language conclusion

### Translation Dictionary
When writing Layer 1, translate these concepts:

| Jyotish Term | Plain Language |
|---|---|
| Mahadasha / MD | your major life period / the 18-year cycle |
| Antardasha / AD / bhukti | the current sub-period / the phase within that cycle |
| Pratyantardasha / PD | the current micro-phase |
| Rahu MD | the current 18-year life cycle (focused on ambition and unconventional paths) |
| Venus bhukti | a 3-year phase focused on creativity, relationships, and financial growth |
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
| Sade Sati | a 7.5-year period of restructuring (Saturn's influence) |
| Kantaka Shani | a period of career pressure from Saturn |
| Transit | a planet's current position in the sky |
| Rahu/Ketu | the shadow planets that drive ambition and detachment |
| Yogakaraka | the single most beneficial planet for your chart |
| Functional benefic | a planet that naturally helps your chart |
| Functional malefic | a planet that creates challenges for your chart |
| Nakshatra | the star-constellation a planet occupies (deeper than zodiac sign) |
| Vimshottari dasha | the planetary period system used for timing predictions |
| Drishti / aspect | a planet's influence on another planet or zone |
| Conjunction | two planets sitting together in the same zone |
| Retrograde | a planet appearing to move backward (intensified energy) |
| Combust | a planet too close to the Sun (weakened visibility) |

### Format Example

For a timeline/prediction reading:

```
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
- Venus: 5th/12th lord in H8 (Makaram), sole functional benefic
- Transit: Jupiter exalted in Katakam (H2 -- wealth house)
- Venus bhukti begins Jun 13, 2026
- Systems: Parashari, Nadi, Transit | Confidence: HIGH

</details>
```

### Rules for the "Why this matters now" bridge
- This is a 1-2 sentence explanation that connects the plain prediction to the underlying logic
- Uses SIMPLIFIED astrological language (not raw jyotish, not fully plain either)
- Purpose: for readers who want to understand WHY without reading full technical details
- Example: "Your career planet enters its strongest position" (not "Jupiter exalted in Katakam")

### Scorecard tables
- Scorecard tables go in the Technical Basis section, NOT in the plain layer
- The plain layer only shows the VERDICT: "Overall: FAVORABLE" or "Overall: DIFFICULT"
- Confidence level always shown in plain layer
```

### Change 2: Reading Templates

Update all templates to use the two-layer format. The key templates to update:

#### `full_reading.md`
- Each section (Lagna Lord, Chandra, Bhava Analysis, etc.) gets a plain-language summary FIRST
- Technical tables move into collapsible sections
- "The Honest Assessment" stays as-is (already plain-ish)
- "Practical Guidance" stays as-is

#### `dasha_reading.md`
- "Period Overview" becomes plain language: what this period means for your life
- "Sub-Period Timeline" gets a plain column and a technical column
- Scorecard tables move to collapsible section

#### `annual_prediction.md`
- "Year at a Glance" stays plain (already is)
- Life Area Predictions: each area gets plain prediction first, scorecard in collapsible
- "Quarter-by-Quarter" stays plain (already is)

#### `transit_timeline.md` and `transit_reading.md`
- Same pattern: plain first, technical collapsible

#### NEW: `timeline_reading.md`
- Specifically for multi-year timeline predictions (like the Jagan Mohan reading)
- Year-by-year structure with:
  - Plain summary of the year (3-5 sentences)
  - Category-specific predictions (WEALTH/CAREER/FAMILY/PARADESA) in plain language
  - Collapsible technical basis per prediction
  - Consolidated summary tables at the end

#### `specialist_findings.md` -- NO CHANGE
- Stays purely technical (specialists unchanged per design decision)

---

## What Does NOT Change

1. Specialist agent files (parashari.md, nadi.md, jaimini.md, kp.md, tajaka.md, prashna.md, muhurta.md)
2. Specialist findings format (specialist_findings.md)
3. Anti-bias rules in astrobot.md
4. Scorecard framework (scorecards.yaml)
5. Knowledgebase reference files (.claude_kb/reference/)
6. Data storage format (birth_data.yaml, extensions.yaml)
7. Convergence and confidence rules

---

## Implementation Plan

### Step 1: Update `astrobot.md`
- Add "Two-Layer Output Rules" section with translation dictionary
- Add format examples
- Add rules for the "Why this matters now" bridge
- Modify Step 6 (Write the Reading) to reference two-layer format

### Step 2: Update reading templates
- `full_reading.md` -- add plain-language layer
- `dasha_reading.md` -- add plain-language layer
- `annual_prediction.md` -- add plain-language layer
- `transit_reading.md` -- add plain-language layer
- `transit_timeline.md` -- add plain-language layer

### Step 3: Create new template
- `timeline_reading.md` -- for multi-year categorized predictions

### Step 4: Test
- Re-run the Jagan Mohan timeline prediction using updated astrobot
- Verify output follows two-layer format
- Verify plain language is genuinely jargon-free

---

## Success Criteria

1. A person with zero jyotish knowledge can read the plain layer and understand every prediction
2. A jyotish practitioner can expand the technical sections and verify the reasoning
3. The "Why this matters now" bridge satisfies curious readers without overwhelming them
4. No jyotish abbreviations (Ra, Ve, H8, PD, MD) appear in the plain layer
5. Confidence levels are always visible in the plain layer
6. Dates are in human-readable format (month + year, not ISO)
