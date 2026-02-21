# Astrobot Memory

## Jagan Mohan Key Facts
- Currently in Seattle, USA (confirmed Feb 2026)
- Got married in 8 Sep 2003
- Moved from Pondicherry to Bangalore ~2004
- Moved from Bangalore to Seattle most likely Aug-Sep 2023
- Elder daughter Lavanthika born Bangalore, Jan 18, 2005
- Younger daughter Geethana born Bangalore, Nov 4, 2011
- Rahu MD: 2015-01-24 to 2033-01-23
- Guru MD: 2033-01-23 to 2049-01-23

## Project Structure
- Birth data: `readings/<person_name>/birth_data.yaml`
- Readings: `readings/<person_name>/YYYY-MM-DD_<type>.md`
- Templates: `.claude_kb/templates/`
- Calculator: `jyotish_calc.py` (Swiss Ephemeris, Lahiri ayanamsa, whole sign)
- Calculator computes: positions, nakshatras, dignity, Vimshottari MD sequence
- Calculator does NOT compute: antardashas, pratyantardashas, transits, divisional charts
- For AD/PD computation: use inline Python (see dasha computation code in readings)
