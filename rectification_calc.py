#!/usr/bin/env python3
"""
Birth time rectification calculator.
Computes detailed Vimshottari MD/AD/PD for all life events at two candidate times.
Also computes divisional charts (D-3, D-4, D-6, D-7, D-9, D-10).
"""

from datetime import date, timedelta
import json

# Dasha sequence and years
DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

RASHI_NAMES = [
    "Mesham", "Rishabham", "Mithunam", "Katakam", "Simham", "Kanni",
    "Thulam", "Viruchikam", "Dhanusu", "Makaram", "Kumbham", "Meenam",
]

NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

NAKSHATRA_SPAN = 13 + 1/3  # 13 deg 20 min


def compute_full_dashas(moon_lon, birth_date):
    """Compute full MD/AD/PD structure from Moon longitude."""
    nak_idx = int(moon_lon / NAKSHATRA_SPAN)
    if nak_idx >= 27:
        nak_idx = 26
    nak_name, nak_lord = NAKSHATRAS[nak_idx]
    deg_in_nak = moon_lon % NAKSHATRA_SPAN

    start_index = DASHA_SEQUENCE.index(nak_lord)
    proportion_remaining = 1 - (deg_in_nak / NAKSHATRA_SPAN)
    first_years = DASHA_YEARS[nak_lord]
    balance_days = first_years * proportion_remaining * 365.25

    # Build full MD sequence
    md_list = []

    # First (partial) MD
    md_start = birth_date
    md_end = birth_date + timedelta(days=balance_days)
    md_list.append({"lord": nak_lord, "start": md_start, "end": md_end, "years": first_years * proportion_remaining})

    # Remaining 8 MDs
    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(start_index + i) % 9]
        years = DASHA_YEARS[lord]
        md_start = md_end
        md_end = md_start + timedelta(days=years * 365.25)
        md_list.append({"lord": lord, "start": md_start, "end": md_end, "years": years})

    # For each MD, compute ADs
    all_periods = []
    for md in md_list:
        md_lord = md["lord"]
        md_start_idx = DASHA_SEQUENCE.index(md_lord)
        md_total_days = (md["end"] - md["start"]).days

        ad_start = md["start"]
        for j in range(9):
            ad_lord = DASHA_SEQUENCE[(md_start_idx + j) % 9]
            ad_proportion = DASHA_YEARS[ad_lord] / 120.0
            ad_days = md_total_days * ad_proportion
            ad_end = ad_start + timedelta(days=ad_days)

            # For each AD, compute PDs
            pd_list = []
            ad_start_idx = DASHA_SEQUENCE.index(ad_lord)
            ad_total_days = ad_days
            pd_start = ad_start
            for k in range(9):
                pd_lord = DASHA_SEQUENCE[(ad_start_idx + k) % 9]
                pd_proportion = DASHA_YEARS[pd_lord] / 120.0
                pd_days = ad_total_days * pd_proportion
                pd_end = pd_start + timedelta(days=pd_days)
                pd_list.append({"lord": pd_lord, "start": pd_start, "end": pd_end})
                pd_start = pd_end

            all_periods.append({
                "md": md_lord,
                "ad": ad_lord,
                "md_start": md["start"],
                "md_end": md["end"],
                "ad_start": ad_start,
                "ad_end": ad_end,
                "pds": pd_list
            })

            ad_start = ad_end

    return all_periods, md_list


def find_dasha_at_date(all_periods, target_date):
    """Find MD/AD/PD running at a given date."""
    for period in all_periods:
        if period["ad_start"] <= target_date <= period["ad_end"]:
            # Find PD
            for pd in period["pds"]:
                if pd["start"] <= target_date <= pd["end"]:
                    return {
                        "md": period["md"],
                        "ad": period["ad"],
                        "pd": pd["lord"],
                        "md_range": f"{period['md_start'].isoformat()} to {period['md_end'].isoformat()}",
                        "ad_range": f"{period['ad_start'].isoformat()} to {period['ad_end'].isoformat()}",
                        "pd_range": f"{pd['start'].isoformat()} to {pd['end'].isoformat()}"
                    }
            # If no exact PD match (edge case), return MD/AD only
            return {
                "md": period["md"],
                "ad": period["ad"],
                "pd": "?",
                "md_range": f"{period['md_start'].isoformat()} to {period['md_end'].isoformat()}",
                "ad_range": f"{period['ad_start'].isoformat()} to {period['ad_end'].isoformat()}",
                "pd_range": "?"
            }
    return None


def compute_divisional(sidereal_lon, divisor):
    """Compute divisional chart rasi for a planet.

    For D-n: multiply the degree within the rasi by n,
    and the resulting sign from the original sign gives the D-n position.

    Standard formula: floor(degree_in_sign * divisor / 30) signs from the base.
    Base depends on the divisional chart type.
    """
    rasi_idx = int(sidereal_lon / 30)
    deg_in_rasi = sidereal_lon % 30

    # D-1: same as rasi
    if divisor == 1:
        return rasi_idx

    # D-9 (Navamsa): Each 3d20m = one navamsa. Starting from movable sign of element.
    if divisor == 9:
        navamsa_num = int(deg_in_rasi / (30/9))  # 0-8
        # Fire signs (0,4,8) start from Mesham (0)
        # Earth signs (1,5,9) start from Makaram (9)
        # Air signs (2,6,10) start from Thulam (6)
        # Water signs (3,7,11) start from Katakam (3)
        element = rasi_idx % 4
        base = [0, 9, 6, 3][element]
        return (base + navamsa_num) % 12

    # D-3 (Drekkana): Each 10 degrees = one drekkana
    if divisor == 3:
        drekkana_num = int(deg_in_rasi / 10)  # 0, 1, 2
        # 1st drekkana: same sign
        # 2nd drekkana: 5th from sign
        # 3rd drekkana: 9th from sign
        offsets = [0, 4, 8]
        return (rasi_idx + offsets[drekkana_num]) % 12

    # D-7 (Saptamsa): Each 4d17m8.57s = one saptamsa
    if divisor == 7:
        saptamsa_num = int(deg_in_rasi * 7 / 30)  # 0-6
        # Odd signs: count from same sign
        # Even signs: count from 7th sign
        if rasi_idx % 2 == 0:  # odd sign (0-indexed even = 1st,3rd,5th etc)
            return (rasi_idx + saptamsa_num) % 12
        else:
            return (rasi_idx + 6 + saptamsa_num) % 12

    # D-4 (Chaturthamsa): Each 7.5 degrees
    if divisor == 4:
        chaturthamsa_num = int(deg_in_rasi * 4 / 30)  # 0-3
        # Starts from same sign, counts by kendras (every 3 signs = quadrant)
        return (rasi_idx + chaturthamsa_num * 3) % 12

    # D-10 (Dasamsa): Each 3 degrees
    if divisor == 10:
        dasamsa_num = int(deg_in_rasi * 10 / 30)  # 0-9
        # Odd signs: count from same sign
        # Even signs: count from 9th sign
        if rasi_idx % 2 == 0:  # odd sign
            return (rasi_idx + dasamsa_num) % 12
        else:
            return (rasi_idx + 8 + dasamsa_num) % 12

    # D-6 (Shashthamsa): Each 5 degrees
    if divisor == 6:
        shashthamsa_num = int(deg_in_rasi * 6 / 30)  # 0-5
        # Same sign onwards
        return (rasi_idx + shashthamsa_num) % 12 if rasi_idx % 2 == 0 else (rasi_idx + 6 + shashthamsa_num) % 12

    # Generic fallback
    part = int(deg_in_rasi * divisor / 30)
    return (rasi_idx + part) % 12


# ============================================================================
# CHART DATA
# ============================================================================

# 12:30 PM chart
moon_lon_1230 = 258.0992  # Dhanusu 18.0992 = (8*30) + 18.0992 = 258.0992
# Wait, Dhanusu = index 8 (0-based), so 8*30 + 18.0992 = 258.0992

# 12:45 PM chart
moon_lon_1245 = 258.2458  # Dhanusu 18.2458

# Planet sidereal longitudes for 12:30 PM
planets_1230 = {
    "Sun": 337.4938,     # Meenam (11*30) + 7.4938
    "Moon": 258.0992,    # Dhanusu (8*30) + 18.0992
    "Mars": 324.108,     # Kumbham (10*30) + 24.108
    "Mercury": 341.711,  # Meenam (11*30) + 11.711
    "Jupiter": 95.4614,  # Katakam (3*30) + 5.4614
    "Venus": 298.2895,   # Makaram (9*30) + 28.2895
    "Saturn": 135.3954,  # Simham (4*30) + 15.3954
    "Rahu": 143.4068,    # Simham (4*30) + 23.4068
    "Ketu": 323.4068,    # Kumbham (10*30) + 23.4068
    "Lagna": 74.8785,    # Mithunam (2*30) + 14.8785
}

# Planet sidereal longitudes for 12:45 PM
planets_1245 = {
    "Sun": 337.5042,
    "Moon": 258.2458,
    "Mars": 324.1161,
    "Mercury": 341.7027,
    "Jupiter": 95.4612,
    "Venus": 298.3019,
    "Saturn": 135.3946,
    "Rahu": 143.4063,
    "Ketu": 323.4063,
    "Lagna": 78.2887,    # Mithunam (2*30) + 18.2887
}

birth = date(1979, 3, 22)

# ============================================================================
# LIFE EVENTS
# ============================================================================
events = [
    {"name": "Lost younger brother", "date": date(1983, 9, 1), "approx": True,
     "houses": "H3 (younger siblings), H8 (death)", "notes": "Age 4-5, ~1983-1984"},
    {"name": "Younger sibling born", "date": date(1986, 3, 15), "approx": True,
     "houses": "H3 (younger siblings), H5 (children/progeny)", "notes": "March 1986"},
    {"name": "College started", "date": date(1996, 4, 1), "approx": True,
     "houses": "H4 (education), H5 (higher learning), H9 (higher education)", "notes": "April 1996"},
    {"name": "College graduated / First job", "date": date(2000, 5, 1), "approx": True,
     "houses": "H10 (career), H4 (education completion)", "notes": "May 2000"},
    {"name": "Marriage", "date": date(2003, 9, 15), "approx": True,
     "houses": "H7 (marriage), D-9", "notes": "September 2003"},
    {"name": "First child", "date": date(2005, 1, 15), "approx": True,
     "houses": "H5 (children), D-7", "notes": "January 2005"},
    {"name": "Kidney stone surgery", "date": date(2007, 6, 1), "approx": True,
     "houses": "H6 (disease), H8 (surgery)", "notes": "2007"},
    {"name": "First property purchase", "date": date(2010, 6, 1), "approx": True,
     "houses": "H4 (property), D-4", "notes": "2010, through loan"},
    {"name": "Second child", "date": date(2011, 11, 15), "approx": True,
     "houses": "H5 (children), H9 (5th from 5th), D-7", "notes": "November 2011"},
    {"name": "Father hernia surgery", "date": date(2017, 6, 1), "approx": True,
     "houses": "H9 (father), H6 from H9=H2 (father's disease)", "notes": "~2017"},
    {"name": "Land purchase attempt (stuck)", "date": date(2020, 6, 1), "approx": True,
     "houses": "H4 (land/property), H12 (loss)", "notes": "2020, never handed over"},
    {"name": "Brother-in-law died + debts", "date": date(2021, 5, 15), "approx": True,
     "houses": "H3 from H7=H9 (spouse's sibling), H8 (death), H6 (debts)", "notes": "May 2021, ~1 crore debt"},
    {"name": "Property sold", "date": date(2023, 6, 1), "approx": True,
     "houses": "H4 (property), H12 from H4=H3 (loss of property)", "notes": "2023"},
    {"name": "Landed in US", "date": date(2023, 10, 6), "approx": False,
     "houses": "H12 (foreign land), H9 (long distance travel), H3 (travel)", "notes": "October 6, 2023"},
    {"name": "Property purchase early 2025", "date": date(2025, 2, 1), "approx": True,
     "houses": "H4 (property), D-4", "notes": "2025, ongoing"},
    {"name": "50 lakhs for MIL house", "date": date(2025, 6, 1), "approx": True,
     "houses": "H4 from H7=H10 (spouse's mother's home), H12 (expenditure)", "notes": "2025"},
    {"name": "House purchase through loan", "date": date(2026, 2, 1), "approx": True,
     "houses": "H4 (property), H6 (loan), D-4", "notes": "Feb 2026, wife signed GPA"},
    {"name": "Father frozen shoulder surgery", "date": date(2018, 6, 1), "approx": True,
     "houses": "H9 (father), H6 from H9=H2 (father's health)", "notes": "Year unspecified, ~2018"},
]

# ============================================================================
# COMPUTE AND DISPLAY
# ============================================================================

print("=" * 120)
print("BIRTH TIME RECTIFICATION: VIMSHOTTARI DASHA COMPARISON")
print("=" * 120)
print()

# Compute dashas for both times
periods_1230, md_list_1230 = compute_full_dashas(moon_lon_1230, birth)
periods_1245, md_list_1245 = compute_full_dashas(moon_lon_1245, birth)

# Print MD comparison
print("MAHADASHA COMPARISON:")
print(f"{'Period':<12} {'12:30 PM Start':<18} {'12:30 PM End':<18} {'12:45 PM Start':<18} {'12:45 PM End':<18} {'Diff (days)':<12}")
print("-" * 100)
for md1, md2 in zip(md_list_1230, md_list_1245):
    diff = (md1["start"] - md2["start"]).days
    print(f"{md1['lord']:<12} {md1['start'].isoformat():<18} {md1['end'].isoformat():<18} {md2['start'].isoformat():<18} {md2['end'].isoformat():<18} {diff:<12}")

print()
print("=" * 120)
print("LIFE EVENT DASHA ANALYSIS")
print("=" * 120)
print()

for event in events:
    d1230 = find_dasha_at_date(periods_1230, event["date"])
    d1245 = find_dasha_at_date(periods_1245, event["date"])

    print(f"EVENT: {event['name']}")
    print(f"  Date: {event['date'].isoformat()} | Houses: {event['houses']}")
    print(f"  Notes: {event['notes']}")

    if d1230:
        print(f"  12:30 PM: {d1230['md']}-{d1230['ad']}-{d1230['pd']}")
        print(f"    MD: {d1230['md_range']}")
        print(f"    AD: {d1230['ad_range']}")
        print(f"    PD: {d1230['pd_range']}")
    else:
        print(f"  12:30 PM: NOT FOUND")

    if d1245:
        print(f"  12:45 PM: {d1245['md']}-{d1245['ad']}-{d1245['pd']}")
        print(f"    MD: {d1245['md_range']}")
        print(f"    AD: {d1245['ad_range']}")
        print(f"    PD: {d1245['pd_range']}")
    else:
        print(f"  12:45 PM: NOT FOUND")

    # Highlight differences
    if d1230 and d1245:
        diffs = []
        if d1230["md"] != d1245["md"]:
            diffs.append(f"MD differs: {d1230['md']} vs {d1245['md']}")
        if d1230["ad"] != d1245["ad"]:
            diffs.append(f"AD differs: {d1230['ad']} vs {d1245['ad']}")
        if d1230["pd"] != d1245["pd"]:
            diffs.append(f"PD differs: {d1230['pd']} vs {d1245['pd']}")
        if diffs:
            print(f"  *** DIFFERENCE: {'; '.join(diffs)} ***")
        else:
            print(f"  (Same MD-AD-PD)")
    print()

# ============================================================================
# DIVISIONAL CHARTS
# ============================================================================
print("=" * 120)
print("DIVISIONAL CHART COMPARISON")
print("=" * 120)
print()

divs = {"D-3": 3, "D-4": 4, "D-6": 6, "D-7": 7, "D-9": 9, "D-10": 10}

for div_name, divisor in divs.items():
    print(f"\n{div_name} CHART:")
    print(f"{'Planet':<12} {'12:30 PM':<14} {'12:45 PM':<14} {'Same?':<8}")
    print("-" * 50)
    for planet in ["Lagna", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        lon1 = planets_1230[planet]
        lon2 = planets_1245[planet]
        div1 = compute_divisional(lon1, divisor)
        div2 = compute_divisional(lon2, divisor)
        same = "YES" if div1 == div2 else "*** NO ***"
        print(f"{planet:<12} {RASHI_NAMES[div1]:<14} {RASHI_NAMES[div2]:<14} {same}")

print()
print("=" * 120)
print("HOUSE LORDSHIP REFERENCE (Mithunam Lagna)")
print("=" * 120)
print("""
Mercury: 1L + 4L (lagna lord, property, education, mother)
Moon: 2L (wealth, family, speech) -- also maraka
Sun: 3L (younger siblings, courage, communication)
Mercury: 4L (see 1L above)
Venus: 5L + 12L (children, creativity, intelligence; foreign, losses, expenses)
Mars: 6L + 11L (enemies, disease, debts; gains, income, elder siblings) -- functional malefic
Jupiter: 7L + 10L (marriage, partnerships; career) -- functional malefic (natural benefic in kendra)
Saturn: 8L + 9L (longevity, transformation; father, fortune, dharma) -- mixed/neutral
Rahu: Co-lord 9L (if Kumbham as H9)
Ketu: Co-lord 6L (if Viruchikam as H6)
""")
