# Astrobot Agent Memory

## Critical Lessons from Longevity Analysis Failure (Yogeshwaran Case, 2026-02-21)

### The Case
- Native: Yogeshwaran, Mesham lagna, died at age 36.7 during Moon-Moon AD
- Previous estimate: 75-85 years -- WRONG by 40+ years
- See: `readings/yogeshwaran/2026-02-21_longevity_retrospective.md`

### Rules Learned (NON-NEGOTIABLE in future longevity readings)

1. **NEVER treat "survived maraka MD" as defusing death.** It is a DEFERRAL. Maraka energy transfers to future AD activations. Do NOT give it positive weight in scorecards.

2. **Debilitated planet in H8 running its own MD = PRIMARY death indicator.** Not "emotional difficulty" -- this is the chart's most lethal configuration. Give it maximum weight.

3. **Do NOT double-count ambivalent planets.** If Saturn is both longevity karaka (favorable) and baadhaka/maraka (unfavorable), score it on ONE side based on natal placement, or remove from both sides.

4. **Exalted malefic in dusthana = UNFAVORABLE.** Ketu exalted in H8 means death significations manifest powerfully, not "spiritual protection."

5. **Neecha bhanga from a maraka planet is NOT protection.** If Venus (double maraka) provides cancellation for Moon's debilitation, this is a LINKAGE to the death-dealer, not a shield.

6. **When Three Pairs floor age = dangerous dasha start, flag death at the floor as PRIMARY possibility.**

7. **Paramaayush ceiling is irrelevant when death indicators cluster at the floor.**

8. **Moon debilitated in H8 with Ketu = always flag mental health crisis as PRIMARY death risk.**

9. **Apply steel-man rule honestly.** If the steel-man against favorable is compelling, it should SHIFT the verdict.

## Scorecard Methodology Corrections
- Remove items from favorable side if the "protecting" planet is itself a maraka/baadhaka
- Do not score partial neecha bhanga as favorable when the cancelling planet is a maraka
- Double activation (MD-AD same planet in dusthana) must be scored as separate unfavorable item
- Timing convergence (dangerous dasha start at longevity floor) must be scored as unfavorable

## birth_data.yaml Enhancement (2026-02-22)

### Problem Identified
Readings missed Mercury's neecha bhanga raja yoga for Jagan Mohan (Mithuna lagna).
The June 2025 promotion during Rahu-Mercury AD was not predicted because:
- Readings over-emphasized Mercury's debilitation
- Neecha bhanga conditions were not checked rigorously
- The Rahu-Mercury AD career analysis was entirely skipped

### Solution: computed_analysis Section
`jyotish_calc.py` now generates a `computed_analysis` section in every birth_data.yaml:

```yaml
computed_analysis:
  functional_nature:     # Table 30 lookup per lagna
  badhaka:               # Table 31 rule-based
  marakas:               # 2nd and 7th lords
  neecha_bhanga:         # Condition-checked for each debilitated planet
  yogas:                 # Budha-Aditya, Gaja-Kesari, Pancha Mahapurusha, Vipareeta RY
  digbala:               # Directional strength check
  key_strengths:         # Summary of positive factors
  key_vulnerabilities:   # Summary of negative factors
```

### Rules for Reading Agents
1. **ALWAYS read computed_analysis before writing interpretations**
2. If neecha_bhanga status = CONFIRMED, do NOT describe the planet as simply "weak"
3. If a planet has both neecha bhanga AND digbala, treat it as career-positive
4. Analyze EVERY antardasha in the current/recent mahadasha -- never skip periods
5. Validate interpretations against known life events before predicting future
