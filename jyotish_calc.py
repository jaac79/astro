#!/usr/bin/env python3
"""
Jyotish Birth Chart Calculator

Computes Vedic astrological chart data using Swiss Ephemeris with Lahiri
Ayanamsha. Outputs structured YAML for downstream readings.

Usage:
    python jyotish_calc.py --name "Damodar Pai" --dob 1980-09-03 \
        --tob 08:35:00 --place "Mangalore, Karnataka, India" --timezone 5.5 \
        --lat 12.9141 --lon 74.8560 --print
"""

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timedelta

import swisseph as swe
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RASHI_NAMES = [
    "Mesham", "Rishabham", "Mithunam", "Katakam", "Simham", "Kanni",
    "Thulam", "Viruchikam", "Dhanusu", "Makaram", "Kumbham", "Meenam",
]

RASHI_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# (name, lord)
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

NAKSHATRA_SPAN = 13 + 1 / 3  # 13 deg 20 min = 13.33333...

# (swe_id, english_name, sanskrit_name, yaml_key)
GRAHA_LIST = [
    (swe.SUN, "Sun", "Surya", "surya"),
    (swe.MOON, "Moon", "Chandra", "chandra"),
    (swe.MARS, "Mars", "Mangal", "mangal"),
    (swe.MERCURY, "Mercury", "Budha", "budha"),
    (swe.JUPITER, "Jupiter", "Guru", "guru"),
    (swe.VENUS, "Venus", "Shukra", "shukra"),
    (swe.SATURN, "Saturn", "Shani", "shani"),
]

DASHA_SEQUENCE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

# ---------------------------------------------------------------------------
# Dignity Tables (Parashari)
# ---------------------------------------------------------------------------

# Exaltation: graha -> rasi index (0-based)
EXALTATION = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
    "Rahu": 1, "Ketu": 7,
}

# Debilitation: graha -> rasi index (0-based)
DEBILITATION = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
    "Rahu": 7, "Ketu": 1,
}

# Moolatrikona: graha -> (rasi index, start_deg, end_deg)
MOOLATRIKONA = {
    "Sun": (4, 0, 20),
    "Moon": (1, 3, 30),
    "Mars": (0, 0, 12),
    "Mercury": (5, 15, 20),
    "Jupiter": (8, 0, 10),
    "Venus": (6, 0, 15),
    "Saturn": (10, 0, 20),
}

# Own signs: graha -> list of rasi indices (0-based)
OWN_SIGNS = {
    "Sun": [4],
    "Moon": [3],
    "Mars": [0, 7],
    "Mercury": [2, 5],
    "Jupiter": [8, 11],
    "Venus": [1, 6],
    "Saturn": [9, 10],
}

# Natural friendships (Parashari Naisargika Maitri)
NATURAL_FRIENDS = {
    "Sun": {
        "friends": {"Moon", "Mars", "Jupiter"},
        "enemies": {"Venus", "Saturn"},
        "neutral": {"Mercury"},
    },
    "Moon": {
        "friends": {"Sun", "Mercury"},
        "enemies": set(),
        "neutral": {"Mars", "Jupiter", "Venus", "Saturn"},
    },
    "Mars": {
        "friends": {"Sun", "Moon", "Jupiter"},
        "enemies": {"Mercury"},
        "neutral": {"Venus", "Saturn"},
    },
    "Mercury": {
        "friends": {"Sun", "Venus"},
        "enemies": {"Moon"},
        "neutral": {"Mars", "Jupiter", "Saturn"},
    },
    "Jupiter": {
        "friends": {"Sun", "Moon", "Mars"},
        "enemies": {"Mercury", "Venus"},
        "neutral": {"Saturn"},
    },
    "Venus": {
        "friends": {"Mercury", "Saturn"},
        "enemies": {"Sun", "Moon"},
        "neutral": {"Mars", "Jupiter"},
    },
    "Saturn": {
        "friends": {"Mercury", "Venus"},
        "enemies": {"Sun", "Moon", "Mars"},
        "neutral": {"Jupiter"},
    },
}

# Rasi lords (0-indexed rasi -> graha english name)
RASI_LORD = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]


# ---------------------------------------------------------------------------
# Core Ephemeris Functions
# ---------------------------------------------------------------------------

def calculate_julian_day(year, month, day, hour, minute, second, timezone):
    """Convert local date/time to Julian Day via UT."""
    ut_hour = hour + minute / 60.0 + second / 3600.0 - timezone
    if ut_hour < 0:
        ut_hour += 24
        day -= 1
    elif ut_hour >= 24:
        ut_hour -= 24
        day += 1
    return swe.julday(year, month, day, ut_hour)


def get_nakshatra(longitude):
    """Return (name, lord, pada, degree_in_nakshatra) for sidereal longitude."""
    idx = int(longitude / NAKSHATRA_SPAN)
    if idx >= 27:
        idx = 26
    pada = int((longitude % NAKSHATRA_SPAN) / (NAKSHATRA_SPAN / 4)) + 1
    if pada > 4:
        pada = 4
    name, lord = NAKSHATRAS[idx]
    deg_in_nak = longitude % NAKSHATRA_SPAN
    return name, lord, pada, deg_in_nak


def get_rashi(longitude):
    """Return (rashi_name, rashi_index_0based, degree_in_rashi)."""
    idx = int(longitude / 30)
    if idx >= 12:
        idx = 11
    deg = longitude % 30
    return RASHI_NAMES[idx], idx, deg


def format_dms(degrees):
    """Format decimal degrees as D\u00b0MM'SS.ss\"."""
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = ((degrees - d) * 60 - m) * 60
    return f"{d}\u00b0{m:02d}'{s:05.2f}\""


def calculate_ascendant(jd, lat, lon):
    """Return (sidereal_asc_longitude, ayanamsha) using Placidus for ASC point."""
    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    ayanamsha = swe.get_ayanamsa(jd)
    asc_sid = (ascmc[0] - ayanamsha) % 360
    return asc_sid, ayanamsha


# ---------------------------------------------------------------------------
# Planetary Position Calculation
# ---------------------------------------------------------------------------

def calculate_planet_position(jd, planet_id, ayanamsha, lagna_rashi_idx):
    """Calculate sidereal position for a single graha.

    Returns dict with: sidereal_lon, rashi, rashi_idx, degree, nakshatra,
                       nak_lord, pada, house, retrograde.
    """
    pos, ret = swe.calc_ut(jd, planet_id)
    sid_lon = (pos[0] - ayanamsha) % 360
    rashi_name, rashi_idx, deg = get_rashi(sid_lon)
    nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(sid_lon)
    house = ((rashi_idx - lagna_rashi_idx) % 12) + 1
    retrograde = pos[3] < 0

    return {
        "sidereal_lon": sid_lon,
        "rashi": rashi_name,
        "rashi_idx": rashi_idx,
        "degree": deg,
        "nakshatra": nak_name,
        "nak_lord": nak_lord,
        "pada": pada,
        "house": house,
        "retrograde": retrograde,
    }


def calculate_all_positions(jd, ayanamsha, lagna_rashi_idx, use_true_node=False):
    """Calculate positions for all 9 grahas (7 planets + Rahu + Ketu).

    Returns dict keyed by English name.
    """
    positions = {}

    for swe_id, eng_name, sans_name, yaml_key in GRAHA_LIST:
        p = calculate_planet_position(jd, swe_id, ayanamsha, lagna_rashi_idx)
        p["sanskrit"] = sans_name
        p["yaml_key"] = yaml_key
        positions[eng_name] = p

    # Rahu
    node_id = swe.TRUE_NODE if use_true_node else swe.MEAN_NODE
    rahu_pos = calculate_planet_position(jd, node_id, ayanamsha, lagna_rashi_idx)
    rahu_pos["retrograde"] = True  # nodes are always retrograde
    rahu_pos["sanskrit"] = "Rahu"
    rahu_pos["yaml_key"] = "rahu"
    positions["Rahu"] = rahu_pos

    # Ketu (180 degrees opposite Rahu)
    ketu_lon = (rahu_pos["sidereal_lon"] + 180) % 360
    ketu_rashi, ketu_rashi_idx, ketu_deg = get_rashi(ketu_lon)
    ketu_nak, ketu_nak_lord, ketu_pada, _ = get_nakshatra(ketu_lon)
    ketu_house = ((ketu_rashi_idx - lagna_rashi_idx) % 12) + 1

    positions["Ketu"] = {
        "sidereal_lon": ketu_lon,
        "rashi": ketu_rashi,
        "rashi_idx": ketu_rashi_idx,
        "degree": ketu_deg,
        "nakshatra": ketu_nak,
        "nak_lord": ketu_nak_lord,
        "pada": ketu_pada,
        "house": ketu_house,
        "retrograde": True,
        "sanskrit": "Ketu",
        "yaml_key": "ketu",
    }

    return positions


# ---------------------------------------------------------------------------
# Dignity Determination
# ---------------------------------------------------------------------------

def get_dignity(graha_name, rashi_idx, degree_in_rashi):
    """Determine planetary dignity.

    Returns one of: exalted, moolatrikona, own, friend, neutral, enemy,
    debilitated, or None (for Rahu/Ketu with no special dignity).
    """
    # Exaltation (whole sign)
    if graha_name in EXALTATION and rashi_idx == EXALTATION[graha_name]:
        return "exalted"

    # Debilitation (whole sign)
    if graha_name in DEBILITATION and rashi_idx == DEBILITATION[graha_name]:
        return "debilitated"

    # Rahu/Ketu only get exaltation/debilitation
    if graha_name in ("Rahu", "Ketu"):
        return None

    # Moolatrikona (specific degree range)
    if graha_name in MOOLATRIKONA:
        mt_rashi, mt_start, mt_end = MOOLATRIKONA[graha_name]
        if rashi_idx == mt_rashi and mt_start <= degree_in_rashi < mt_end:
            return "moolatrikona"

    # Own sign
    if graha_name in OWN_SIGNS and rashi_idx in OWN_SIGNS[graha_name]:
        return "own"

    # Friendship with sign lord
    sign_lord = RASI_LORD[rashi_idx]
    if sign_lord == graha_name:
        return "own"

    if graha_name in NATURAL_FRIENDS:
        rel = NATURAL_FRIENDS[graha_name]
        if sign_lord in rel["friends"]:
            return "friend"
        if sign_lord in rel["enemies"]:
            return "enemy"
        return "neutral"

    return None


# ---------------------------------------------------------------------------
# Vimshottari Dasha
# ---------------------------------------------------------------------------

def calculate_vimshottari_dasha(moon_lon, birth_date_obj):
    """Calculate Vimshottari dasha balance at birth and full 9-period sequence.

    Returns dict with 'balance_at_birth' and 'sequence' (list of 9 periods).
    """
    nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(moon_lon)
    start_index = DASHA_SEQUENCE.index(nak_lord)

    # Balance of first dasha
    proportion_remaining = 1 - (deg_in_nak / NAKSHATRA_SPAN)
    first_years = DASHA_YEARS[nak_lord]
    balance_years = first_years * proportion_remaining

    # Convert to years / months / days
    total_days_balance = balance_years * 365.25
    bal_y = int(balance_years)
    remaining_frac = (balance_years - bal_y) * 365.25
    bal_m = int(remaining_frac / 30.4375)
    bal_d = int(remaining_frac - bal_m * 30.4375)

    balance = {
        "lord": nak_lord,
        "remaining_years": bal_y,
        "remaining_months": bal_m,
        "remaining_days": bal_d,
    }

    # Build 9-period sequence
    sequence = []
    current = birth_date_obj + timedelta(days=total_days_balance)

    # First (partial) dasha
    sequence.append({
        "lord": nak_lord,
        "start": birth_date_obj.isoformat(),
        "end": current.isoformat(),
    })

    # Remaining 8 dashas
    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(start_index + i) % 9]
        years = DASHA_YEARS[lord]
        start_dt = current
        current = start_dt + timedelta(days=years * 365.25)
        sequence.append({
            "lord": lord,
            "start": start_dt.isoformat(),
            "end": current.isoformat(),
        })

    return {"balance_at_birth": balance, "sequence": sequence}


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

def geocode_place(place_name):
    """Geocode a place name to (latitude, longitude) using geopy Nominatim."""
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="jyotish_calc")
    location = geolocator.geocode(place_name)
    if location is None:
        raise ValueError(f"Could not geocode place: {place_name}")
    return location.latitude, location.longitude


# ---------------------------------------------------------------------------
# House Summary
# ---------------------------------------------------------------------------

def build_house_summary(lagna_rashi_idx, positions):
    """Build house-to-planets mapping using whole sign houses."""
    summary = {}
    for h in range(1, 13):
        rashi_idx = (lagna_rashi_idx + h - 1) % 12
        occupants = [name for name, p in positions.items() if p["house"] == h]
        summary[h] = {
            "rasi": RASHI_NAMES[rashi_idx],
            "planets": occupants if occupants else [],
        }
    return summary


# ---------------------------------------------------------------------------
# Computed Analysis: Functional Nature, Badhaka, Maraka, Neecha Bhanga, Yogas
# ---------------------------------------------------------------------------

# Functional nature per lagna (Table 30) - indexed by lagna rasi index (0-11)
# Each entry: (yogakarakas, benefics, malefics, neutrals)
FUNCTIONAL_NATURE_TABLE = {
    0: ([], ["Sun", "Mars", "Jupiter"], ["Mercury", "Venus", "Saturn"], []),  # Mesham
    1: (["Saturn"], ["Sun", "Mercury", "Saturn"], ["Moon", "Jupiter", "Venus"], ["Mars"]),  # Rishabham
    2: ([], ["Venus"], ["Mars", "Jupiter"], ["Moon", "Mercury", "Saturn"]),  # Mithunam
    3: (["Mars"], ["Moon", "Mars", "Jupiter"], ["Mercury", "Venus"], ["Sun", "Saturn"]),  # Katakam
    4: (["Mars"], ["Sun", "Mars", "Jupiter"], ["Mercury", "Venus", "Saturn"], ["Moon"]),  # Simham
    5: ([], ["Mercury", "Venus"], ["Moon", "Mars", "Jupiter"], ["Sun", "Saturn"]),  # Kanni
    6: (["Saturn"], ["Mercury", "Venus", "Saturn"], ["Sun", "Mars", "Jupiter"], []),  # Thulam
    7: ([], ["Moon", "Jupiter"], ["Mercury", "Venus", "Saturn"], ["Sun", "Mars"]),  # Viruchikam
    8: ([], ["Sun", "Mars"], ["Venus", "Saturn"], ["Moon", "Mercury", "Jupiter"]),  # Dhanusu
    9: (["Venus"], ["Venus", "Mercury", "Saturn"], ["Moon", "Mars", "Jupiter"], ["Sun"]),  # Makaram
    10: (["Venus"], ["Venus", "Saturn"], ["Moon", "Mars", "Jupiter"], ["Sun", "Mercury"]),  # Kumbham
    11: ([], ["Moon", "Mars"], ["Sun", "Mercury", "Venus", "Saturn"], ["Jupiter"]),  # Meenam
}

# Sign types for badhaka computation
SIGN_TYPE = ["movable", "fixed", "dual"] * 4  # Me=mov, Ri=fix, Mi=dual, Ka=mov, ...

# Digbala (directional strength): planet -> house where it gets digbala
DIGBALA = {
    "Sun": 10, "Mars": 10,
    "Jupiter": 1, "Mercury": 1,
    "Moon": 4, "Venus": 4,
    "Saturn": 7,
}


def compute_functional_nature(lagna_rashi_idx):
    """Compute functional nature of planets for the given lagna (Table 30).

    Returns dict with yogakarakas, functional_benefics, functional_malefics,
    functional_neutrals.
    """
    yogakarakas, benefics, malefics, neutrals = FUNCTIONAL_NATURE_TABLE[lagna_rashi_idx]
    return {
        "yogakarakas": yogakarakas,
        "functional_benefics": benefics,
        "functional_malefics": malefics,
        "functional_neutrals": neutrals,
    }


def compute_badhaka(lagna_rashi_idx):
    """Compute badhaka sthana and lord for the given lagna (Table 31).

    Movable sign → 11th house; Fixed → 9th house; Dual → 7th house.
    """
    sign_type = SIGN_TYPE[lagna_rashi_idx]
    if sign_type == "movable":
        badhaka_house = 11
    elif sign_type == "fixed":
        badhaka_house = 9
    else:  # dual
        badhaka_house = 7

    badhaka_rashi_idx = (lagna_rashi_idx + badhaka_house - 1) % 12
    badhaka_lord = RASI_LORD[badhaka_rashi_idx]
    return {
        "lagna_sign_type": sign_type,
        "badhaka_sthana": badhaka_house,
        "badhaka_rasi": RASHI_NAMES[badhaka_rashi_idx],
        "badhaka_lord": badhaka_lord,
    }


def compute_marakas(lagna_rashi_idx):
    """Compute maraka planets (2nd and 7th lords)."""
    second_rashi_idx = (lagna_rashi_idx + 1) % 12
    seventh_rashi_idx = (lagna_rashi_idx + 6) % 12
    second_lord = RASI_LORD[second_rashi_idx]
    seventh_lord = RASI_LORD[seventh_rashi_idx]

    marakas = []
    marakas.append({"planet": seventh_lord, "reason": f"7th lord ({RASHI_NAMES[seventh_rashi_idx]})"})
    if second_lord != seventh_lord:
        marakas.append({"planet": second_lord, "reason": f"2nd lord ({RASHI_NAMES[second_rashi_idx]})"})

    return marakas


def detect_neecha_bhanga(positions, lagna_rashi_idx):
    """Detect neecha bhanga raja yoga for debilitated planets.

    Checks these conditions:
    1. Lord of debilitation sign is exalted in the chart
    2. Debilitated planet is in a kendra (H1, H4, H7, H10) from lagna
    3. Lord of the sign occupied by debilitated planet is in a kendra from lagna
    """
    kendra_houses = {1, 4, 7, 10}
    results = []

    for name, pos in positions.items():
        if name in ("Rahu", "Ketu"):
            continue
        dignity = get_dignity(name, pos["rashi_idx"], pos["degree"])
        if dignity != "debilitated":
            continue

        conditions = []
        deb_rashi_idx = pos["rashi_idx"]
        deb_house = pos["house"]

        # Condition 1: Lord of the debilitation sign is exalted
        sign_lord = RASI_LORD[deb_rashi_idx]
        if sign_lord in positions:
            lord_dignity = get_dignity(
                sign_lord,
                positions[sign_lord]["rashi_idx"],
                positions[sign_lord]["degree"],
            )
            if lord_dignity == "exalted":
                conditions.append(
                    f"{sign_lord} (lord of {RASHI_NAMES[deb_rashi_idx]}) is exalted"
                    f" in {positions[sign_lord]['rashi']}"
                )

        # Condition 2: Debilitated planet in kendra from lagna
        if deb_house in kendra_houses:
            conditions.append(
                f"{name} in kendra (House {deb_house}) from lagna"
            )

        # Condition 3: Dispositor (lord of occupied sign) in kendra from lagna
        dispositor = RASI_LORD[deb_rashi_idx]
        if dispositor in positions and positions[dispositor]["house"] in kendra_houses:
            conditions.append(
                f"{dispositor} (dispositor) in kendra"
                f" (House {positions[dispositor]['house']}) from lagna"
            )

        if conditions:
            results.append({
                "planet": name,
                "debilitated_in": RASHI_NAMES[deb_rashi_idx],
                "house": deb_house,
                "conditions_met": conditions,
                "status": "CONFIRMED" if len(conditions) >= 2 else "LIKELY",
            })

    return results


def detect_yogas(positions, lagna_rashi_idx):
    """Detect common yogas in the chart.

    Detects: Budha-Aditya, Gaja-Kesari, Pancha Mahapurusha,
    Vipareeta Raja Yoga, and basic conjunctions.
    """
    kendra_houses = {1, 4, 7, 10}
    yogas = []

    # 1. Budha-Aditya Yoga: Sun + Mercury in same sign
    if positions["Sun"]["rashi_idx"] == positions["Mercury"]["rashi_idx"]:
        # Check combustion (Mercury within 14 deg of Sun if retro, 12 deg if direct)
        sep = abs(positions["Sun"]["sidereal_lon"] - positions["Mercury"]["sidereal_lon"])
        if sep > 180:
            sep = 360 - sep
        combust_limit = 14 if positions["Mercury"]["retrograde"] else 12
        combust = sep < combust_limit
        strength = "WEAKENED" if combust else "STRONG"
        yogas.append({
            "name": "Budha-Aditya Yoga",
            "planets": ["Sun", "Mercury"],
            "house": positions["Sun"]["house"],
            "strength": strength,
            "notes": f"Sun-Mercury conjunction in H{positions['Sun']['house']}."
                     + (f" Mercury combust ({sep:.1f} deg separation)." if combust else ""),
        })

    # 2. Gaja-Kesari Yoga: Jupiter in kendra from Moon
    moon_rashi = positions["Moon"]["rashi_idx"]
    jup_rashi = positions["Jupiter"]["rashi_idx"]
    dist_from_moon = (jup_rashi - moon_rashi) % 12
    if dist_from_moon in (0, 3, 6, 9):  # 1st, 4th, 7th, 10th from Moon
        yogas.append({
            "name": "Gaja-Kesari Yoga",
            "planets": ["Jupiter", "Moon"],
            "house": positions["Jupiter"]["house"],
            "strength": "STRONG" if get_dignity(
                "Jupiter", jup_rashi, positions["Jupiter"]["degree"]
            ) in ("exalted", "own", "moolatrikona") else "MODERATE",
            "notes": f"Jupiter in kendra from Moon (house {dist_from_moon + 1} from Moon).",
        })

    # 3. Pancha Mahapurusha Yogas (Mars/Mercury/Jupiter/Venus/Saturn in
    #    own/exalted/moolatrikona AND in kendra from lagna)
    mahapurusha_names = {
        "Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
        "Venus": "Malavya", "Saturn": "Sasa",
    }
    for planet, yoga_name in mahapurusha_names.items():
        pos = positions[planet]
        dignity = get_dignity(planet, pos["rashi_idx"], pos["degree"])
        if dignity in ("exalted", "own", "moolatrikona") and pos["house"] in kendra_houses:
            yogas.append({
                "name": f"{yoga_name} Yoga (Pancha Mahapurusha)",
                "planets": [planet],
                "house": pos["house"],
                "strength": "STRONG",
                "notes": f"{planet} {dignity} in kendra (H{pos['house']}).",
            })

    # 4. Vipareeta Raja Yoga: 6L/8L/12L in 6th/8th/12th houses
    dusthana_houses = {6, 8, 12}
    dusthana_lords = {}
    for h in [6, 8, 12]:
        rashi_idx = (lagna_rashi_idx + h - 1) % 12
        lord = RASI_LORD[rashi_idx]
        dusthana_lords[h] = lord

    for h, lord in dusthana_lords.items():
        if lord in positions and positions[lord]["house"] in dusthana_houses:
            yogas.append({
                "name": "Vipareeta Raja Yoga",
                "planets": [lord],
                "house": positions[lord]["house"],
                "strength": "MODERATE",
                "notes": f"{lord} (lord of H{h}) in H{positions[lord]['house']} (dusthana in dusthana).",
            })

    return yogas


def compute_digbala(positions):
    """Check which planets have directional strength (digbala)."""
    results = []
    for planet, target_house in DIGBALA.items():
        if planet in positions and positions[planet]["house"] == target_house:
            results.append({
                "planet": planet,
                "house": target_house,
            })
    return results


def build_computed_analysis(lagna_rashi_idx, positions):
    """Build the full computed_analysis section for birth_data.yaml."""
    fn = compute_functional_nature(lagna_rashi_idx)
    badhaka = compute_badhaka(lagna_rashi_idx)
    marakas = compute_marakas(lagna_rashi_idx)
    neecha_bhanga = detect_neecha_bhanga(positions, lagna_rashi_idx)
    yogas = detect_yogas(positions, lagna_rashi_idx)
    digbala = compute_digbala(positions)

    # Build key strengths and vulnerabilities summary
    strengths = []
    vulnerabilities = []

    for db in digbala:
        strengths.append(f"{db['planet']}: digbala in H{db['house']}")

    for nb in neecha_bhanga:
        strengths.append(
            f"{nb['planet']}: neecha bhanga raja yoga ({nb['status']})"
        )

    for y in yogas:
        if y["strength"] in ("STRONG", "MODERATE"):
            strengths.append(f"{y['name']} ({', '.join(y['planets'])})")

    for name, pos in positions.items():
        if name in ("Rahu", "Ketu"):
            continue
        dignity = get_dignity(name, pos["rashi_idx"], pos["degree"])
        if dignity == "debilitated":
            # Check if neecha bhanga applies
            has_bhanga = any(nb["planet"] == name for nb in neecha_bhanga)
            if has_bhanga:
                vulnerabilities.append(
                    f"{name}: debilitated in {pos['rashi']} (neecha bhanga applies)"
                )
            else:
                vulnerabilities.append(
                    f"{name}: debilitated in {pos['rashi']}"
                )
        elif dignity == "enemy":
            vulnerabilities.append(
                f"{name}: in enemy sign ({pos['rashi']})"
            )

    # Check sole benefic
    if len(fn["functional_benefics"]) == 1:
        sole = fn["functional_benefics"][0]
        if sole in positions:
            h = positions[sole]["house"]
            vulnerabilities.append(
                f"{sole}: sole functional benefic, in H{h}"
            )

    return {
        "functional_nature": fn,
        "badhaka": badhaka,
        "marakas": marakas,
        "neecha_bhanga": neecha_bhanga if neecha_bhanga else "none",
        "yogas": yogas if yogas else "none detected",
        "digbala": digbala if digbala else "none",
        "key_strengths": strengths if strengths else ["none identified"],
        "key_vulnerabilities": vulnerabilities if vulnerabilities else ["none identified"],
    }


# ---------------------------------------------------------------------------
# Vimshottari Dasha: Full MD/AD/PD Computation
# ---------------------------------------------------------------------------

def compute_full_dashas(moon_lon, birth_date_obj):
    """Compute full MD/AD/PD structure from Moon longitude.

    Returns (all_periods, md_list) where all_periods is a flat list of
    {md, ad, md_start, md_end, ad_start, ad_end, pds: [{lord, start, end}]}.
    """
    nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(moon_lon)
    start_index = DASHA_SEQUENCE.index(nak_lord)
    proportion_remaining = 1 - (deg_in_nak / NAKSHATRA_SPAN)
    first_years = DASHA_YEARS[nak_lord]
    balance_days = first_years * proportion_remaining * 365.25

    md_list = []
    md_start = birth_date_obj
    md_end = birth_date_obj + timedelta(days=balance_days)
    md_list.append({"lord": nak_lord, "start": md_start, "end": md_end,
                    "years": first_years * proportion_remaining})

    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(start_index + i) % 9]
        years = DASHA_YEARS[lord]
        md_start = md_end
        md_end = md_start + timedelta(days=years * 365.25)
        md_list.append({"lord": lord, "start": md_start, "end": md_end,
                        "years": years})

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

            pd_list = []
            ad_start_idx = DASHA_SEQUENCE.index(ad_lord)
            pd_start = ad_start
            for k in range(9):
                pd_lord = DASHA_SEQUENCE[(ad_start_idx + k) % 9]
                pd_proportion = DASHA_YEARS[pd_lord] / 120.0
                pd_days = ad_days * pd_proportion
                pd_end = pd_start + timedelta(days=pd_days)
                pd_list.append({"lord": pd_lord, "start": pd_start,
                                "end": pd_end})
                pd_start = pd_end

            all_periods.append({
                "md": md_lord, "ad": ad_lord,
                "md_start": md["start"], "md_end": md["end"],
                "ad_start": ad_start, "ad_end": ad_end,
                "pds": pd_list,
            })
            ad_start = ad_end

    return all_periods, md_list


def find_dasha_at_date(all_periods, target_date):
    """Find MD/AD/PD running at a given date.

    Returns dict with md, ad, pd lords and their start/end dates,
    or None if target_date is outside the computed range.
    """
    for period in all_periods:
        if period["ad_start"] <= target_date <= period["ad_end"]:
            for pd in period["pds"]:
                if pd["start"] <= target_date <= pd["end"]:
                    return {
                        "md": period["md"], "ad": period["ad"],
                        "pd": pd["lord"],
                        "md_start": period["md_start"].isoformat(),
                        "md_end": period["md_end"].isoformat(),
                        "ad_start": period["ad_start"].isoformat(),
                        "ad_end": period["ad_end"].isoformat(),
                        "pd_start": pd["start"].isoformat(),
                        "pd_end": pd["end"].isoformat(),
                    }
            return {
                "md": period["md"], "ad": period["ad"], "pd": "?",
                "md_start": period["md_start"].isoformat(),
                "md_end": period["md_end"].isoformat(),
                "ad_start": period["ad_start"].isoformat(),
                "ad_end": period["ad_end"].isoformat(),
                "pd_start": "?", "pd_end": "?",
            }
    return None


# ---------------------------------------------------------------------------
# Vedha Table (Table 63 from transits.yaml)
# ---------------------------------------------------------------------------

# For each planet, auspicious houses from Moon with their vedha (obstruction)
# houses. If another planet transits the vedha house, the auspicious transit
# is obstructed.
VEDHA_TABLE = {
    "Sun":     {3: 9, 6: 12, 10: 4, 11: 5},
    "Moon":    {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Mars":    {3: 12, 6: 9, 11: 5},
    "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Venus":   {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    "Saturn":  {3: 12, 6: 9, 11: 5},
}

# Vedha exceptions: father-son pairs don't obstruct each other
VEDHA_EXCEPTIONS = [
    frozenset({"Sun", "Saturn"}),
    frozenset({"Moon", "Mercury"}),
]


# ---------------------------------------------------------------------------
# Transit Computation
# ---------------------------------------------------------------------------

def compute_transit_positions(target_jd, ayanamsha, natal_lagna_idx,
                              natal_moon_idx):
    """Compute sidereal positions of all 9 grahas at a target Julian Day.

    Returns dict keyed by English name, each with rasi, degree, nakshatra,
    pada, house_from_lagna, house_from_moon, retrograde.
    """
    positions = {}

    for swe_id, eng_name, sans_name, yaml_key in GRAHA_LIST:
        pos, ret = swe.calc_ut(target_jd, swe_id)
        sid_lon = (pos[0] - ayanamsha) % 360
        rashi_name, rashi_idx, deg = get_rashi(sid_lon)
        nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(sid_lon)
        house_from_lagna = ((rashi_idx - natal_lagna_idx) % 12) + 1
        house_from_moon = ((rashi_idx - natal_moon_idx) % 12) + 1
        retrograde = pos[3] < 0

        positions[eng_name] = {
            "sidereal_lon": sid_lon,
            "rashi": rashi_name,
            "rashi_idx": rashi_idx,
            "degree": deg,
            "nakshatra": nak_name,
            "nak_lord": nak_lord,
            "pada": pada,
            "house_from_lagna": house_from_lagna,
            "house_from_moon": house_from_moon,
            "retrograde": retrograde,
            "sanskrit": sans_name,
            "yaml_key": yaml_key,
        }

    # Rahu
    node_id = swe.MEAN_NODE
    pos, ret = swe.calc_ut(target_jd, node_id)
    sid_lon = (pos[0] - ayanamsha) % 360
    rashi_name, rashi_idx, deg = get_rashi(sid_lon)
    nak_name, nak_lord, pada, _ = get_nakshatra(sid_lon)
    positions["Rahu"] = {
        "sidereal_lon": sid_lon,
        "rashi": rashi_name, "rashi_idx": rashi_idx, "degree": deg,
        "nakshatra": nak_name, "nak_lord": nak_lord, "pada": pada,
        "house_from_lagna": ((rashi_idx - natal_lagna_idx) % 12) + 1,
        "house_from_moon": ((rashi_idx - natal_moon_idx) % 12) + 1,
        "retrograde": True, "sanskrit": "Rahu", "yaml_key": "rahu",
    }

    # Ketu (180 opposite Rahu)
    ketu_lon = (positions["Rahu"]["sidereal_lon"] + 180) % 360
    ketu_rashi, ketu_rashi_idx, ketu_deg = get_rashi(ketu_lon)
    ketu_nak, ketu_nak_lord, ketu_pada, _ = get_nakshatra(ketu_lon)
    positions["Ketu"] = {
        "sidereal_lon": ketu_lon,
        "rashi": ketu_rashi, "rashi_idx": ketu_rashi_idx, "degree": ketu_deg,
        "nakshatra": ketu_nak, "nak_lord": ketu_nak_lord, "pada": ketu_pada,
        "house_from_lagna": ((ketu_rashi_idx - natal_lagna_idx) % 12) + 1,
        "house_from_moon": ((ketu_rashi_idx - natal_moon_idx) % 12) + 1,
        "retrograde": True, "sanskrit": "Ketu", "yaml_key": "ketu",
    }

    return positions


def detect_sade_sati(transit_saturn_rashi_idx, natal_moon_rashi_idx):
    """Detect Sade Sati (7.5-year Saturn transit over Moon).

    Saturn in 12th, 1st, or 2nd from natal Moon = Sade Sati.
    Returns dict with active flag and phase, or inactive.
    """
    house_from_moon = ((transit_saturn_rashi_idx - natal_moon_rashi_idx) % 12) + 1
    if house_from_moon == 12:
        return {"active": True, "phase": "rising"}
    elif house_from_moon == 1:
        return {"active": True, "phase": "peak"}
    elif house_from_moon == 2:
        return {"active": True, "phase": "setting"}
    return {"active": False, "phase": None}


def detect_ashtama_shani(transit_saturn_rashi_idx, natal_moon_rashi_idx):
    """Detect Ashtama Shani (Saturn in 8th from Moon)."""
    house_from_moon = ((transit_saturn_rashi_idx - natal_moon_rashi_idx) % 12) + 1
    return house_from_moon == 8


def detect_kantaka_shani(transit_saturn_rashi_idx, natal_lagna_rashi_idx):
    """Detect Kantaka Shani (Saturn in kendra from Lagna: 1, 4, 7, 10)."""
    house_from_lagna = ((transit_saturn_rashi_idx - natal_lagna_rashi_idx) % 12) + 1
    return house_from_lagna in (1, 4, 7, 10)


def check_vedha(planet_name, house_from_moon, transit_positions,
                natal_moon_rashi_idx):
    """Check if a planet's auspicious transit is obstructed by vedha.

    Returns dict with obstructed flag, obstructing planet, and vedha house.
    """
    if planet_name not in VEDHA_TABLE:
        return {"obstructed": False}

    vedha_pairs = VEDHA_TABLE[planet_name]
    if house_from_moon not in vedha_pairs:
        return {"obstructed": False}

    vedha_house = vedha_pairs[house_from_moon]

    # Check if any planet is in the vedha house
    for other_name, other_pos in transit_positions.items():
        if other_name == planet_name:
            continue
        if other_name in ("Rahu", "Ketu"):
            continue  # Nodes not typically considered for vedha
        other_house = other_pos["house_from_moon"]
        if other_house == vedha_house:
            # Check exception pairs
            pair = frozenset({planet_name, other_name})
            if pair in VEDHA_EXCEPTIONS:
                continue
            return {
                "obstructed": True,
                "obstructing_planet": other_name,
                "vedha_house": vedha_house,
            }

    return {"obstructed": False}


def compute_transits(birth_data_path, target_date_str, reading_type="transit_reading"):
    """Compute full transit data for a person at a target date.

    Args:
        birth_data_path: Path to the person's birth_data.yaml
        target_date_str: Target date as YYYY-MM-DD string
        reading_type: Type of reading (for metadata)

    Returns:
        (transit_data_dict, output_path) where transit_data_dict matches
        the current_positions.yaml template.
    """
    # Load birth data
    with open(birth_data_path, "r") as f:
        birth_data = yaml.safe_load(f)

    # Extract natal references
    natal_lagna_rashi = birth_data["lagna"]["rasi"]
    natal_lagna_idx = RASHI_NAMES.index(natal_lagna_rashi)
    natal_moon_rashi = birth_data["chandra"]["rasi"]
    natal_moon_idx = RASHI_NAMES.index(natal_moon_rashi)

    # Extract Moon longitude for dasha computation
    moon_pos = birth_data["planetary_positions"]["chandra"]
    moon_lon = natal_moon_idx * 30 + moon_pos["degree"]

    # Parse birth date
    dob = birth_data["native"]["date_of_birth"]
    if isinstance(dob, date):
        birth_date_obj = dob
    else:
        birth_date_obj = date.fromisoformat(str(dob))

    # Parse target date
    target_date = date.fromisoformat(target_date_str)

    # Initialize Swiss Ephemeris
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Compute Julian Day for target date at noon UT (transit positions are
    # location-independent; noon gives a representative mid-day snapshot)
    target_jd = swe.julday(target_date.year, target_date.month,
                           target_date.day, 12.0)
    ayanamsha = swe.get_ayanamsa(target_jd)

    # Compute transit positions
    transit_pos = compute_transit_positions(
        target_jd, ayanamsha, natal_lagna_idx, natal_moon_idx
    )

    # Compute current dasha (MD/AD/PD)
    all_periods, md_list = compute_full_dashas(moon_lon, birth_date_obj)
    current_dasha = find_dasha_at_date(all_periods, target_date)

    # Detect special Saturn timing
    saturn_rashi_idx = transit_pos["Saturn"]["rashi_idx"]
    sade_sati = detect_sade_sati(saturn_rashi_idx, natal_moon_idx)
    ashtama_shani = detect_ashtama_shani(saturn_rashi_idx, natal_moon_idx)
    kantaka_shani = detect_kantaka_shani(saturn_rashi_idx, natal_lagna_idx)

    # Check vedha for all planets
    vedha_results = {}
    for planet_name, pos in transit_pos.items():
        vedha = check_vedha(planet_name, pos["house_from_moon"],
                            transit_pos, natal_moon_idx)
        if vedha["obstructed"]:
            vedha_results[planet_name] = vedha

    # Build output dict matching current_positions.yaml template
    graha_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                   "Venus", "Saturn", "Rahu", "Ketu"]

    transit_section = {}
    for name in graha_order:
        p = transit_pos[name]
        transit_section[p["yaml_key"]] = {
            "rasi": p["rashi"],
            "degree": round(p["degree"], 4),
            "nakshatra": p["nakshatra"],
            "pada": p["pada"],
            "retrograde": p["retrograde"],
            "house_from_lagna": p["house_from_lagna"],
            "house_from_moon": p["house_from_moon"],
        }

    # Build dasha section
    dasha_section = {}
    if current_dasha:
        dasha_section = {
            "mahadasha": {
                "lord": current_dasha["md"],
                "start": current_dasha["md_start"],
                "end": current_dasha["md_end"],
            },
            "antardasha": {
                "lord": current_dasha["ad"],
                "start": current_dasha["ad_start"],
                "end": current_dasha["ad_end"],
            },
            "pratyantardasha": {
                "lord": current_dasha["pd"],
                "start": current_dasha["pd_start"],
                "end": current_dasha["pd_end"],
            },
        }

    # Build all ADs for current MD (for worksheet Part B)
    all_ads_for_md = []
    if current_dasha:
        for period in all_periods:
            if (period["md"] == current_dasha["md"]
                    and period["md_start"].isoformat() == current_dasha["md_start"]):
                ad_entry = {
                    "lord": period["ad"],
                    "start": period["ad_start"].isoformat(),
                    "end": period["ad_end"].isoformat(),
                }
                if (period["ad_start"] <= target_date <= period["ad_end"]):
                    ad_entry["status"] = "ACTIVE"
                elif (target_date - period["ad_end"]).days <= 1095:  # ~3 years
                    if period["ad_end"] < target_date:
                        ad_entry["status"] = "RECENT"
                all_ads_for_md.append(ad_entry)

    output = {
        "reading_date": target_date_str,
        "reading_type": reading_type,
        "birth_data_file": os.path.basename(os.path.dirname(birth_data_path))
                           + "/birth_data.yaml",
        "current_dasha": dasha_section,
        "all_antardashas_in_current_md": all_ads_for_md,
        "transit_positions": transit_section,
        "transit_houses_from_moon": {
            p["yaml_key"]: p["house_from_moon"]
            for name, p in transit_pos.items()
            for g in graha_order if g == name
        },
        "special_timing": {
            "sade_sati": sade_sati,
            "ashtama_shani": ashtama_shani,
            "kantaka_shani": kantaka_shani,
        },
        "vedha": vedha_results if vedha_results else "none",
        "notes": (
            f"Transit snapshot for {target_date_str}\n"
            f"Ayanamsa: Lahiri ({round(ayanamsha, 6)})\n"
            f"Natal Lagna: {natal_lagna_rashi} | Natal Moon: {natal_moon_rashi}\n"
            f"Computed by jyotish_calc.py"
        ),
    }

    # Write to file
    person_dir = os.path.dirname(birth_data_path)
    output_filename = f"{target_date_str}_current_positions.yaml"
    output_path = os.path.join(person_dir, output_filename)

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    return output, output_path


# ---------------------------------------------------------------------------
# YAML Output
# ---------------------------------------------------------------------------

def build_birth_data_dict(args, lagna, ayanamsha, positions, dasha,
                          house_summary, use_true_node, computed_analysis=None):
    """Build the full birth_data dict matching the YAML template."""
    # Parse place into city / state / country
    place_parts = [p.strip() for p in args.place.split(",")]
    city = place_parts[0] if len(place_parts) >= 1 else args.place
    state = place_parts[1] if len(place_parts) >= 2 else ""
    country = place_parts[2] if len(place_parts) >= 3 else ""

    # Timezone string
    tz_val = args.timezone
    if tz_val == int(tz_val):
        tz_str = f"UTC+{int(tz_val)}" if tz_val >= 0 else f"UTC{int(tz_val)}"
    else:
        hours = int(tz_val)
        minutes = int(abs(tz_val - hours) * 60)
        sign = "+" if tz_val >= 0 else "-"
        tz_str = f"UTC{sign}{abs(hours)}:{minutes:02d}"

    data = {
        "native": {
            "name": args.name,
            "relationship": args.relationship or "",
            "gender": args.gender or "",
            "date_of_birth": args.dob,
            "time_of_birth": args.tob,
            "timezone": tz_str,
            "place_of_birth": {
                "city": city,
                "state": state,
                "country": country,
                "latitude": round(args.lat, 4),
                "longitude": round(args.lon, 4),
            },
        },
        "lagna": {
            "rasi": lagna["rashi"],
            "degree": round(lagna["degree"], 4),
            "nakshatra": lagna["nakshatra"],
            "pada": lagna["pada"],
        },
        "chandra": {
            "rasi": positions["Moon"]["rashi"],
            "degree": round(positions["Moon"]["degree"], 4),
            "nakshatra": positions["Moon"]["nakshatra"],
            "pada": positions["Moon"]["pada"],
        },
        "planetary_positions": {},
        "vimshottari_dasha": dasha,
        "house_summary": {},
        "notes": (
            f"Ayanamsa: Lahiri ({round(ayanamsha, 6)})\n"
            f"Node type: {'True Node' if use_true_node else 'Mean Node'}\n"
            f"House system: Whole Sign\n"
            f"Computed by jyotish_calc.py"
        ),
    }

    # Planetary positions
    graha_order = [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]
    for name in graha_order:
        p = positions[name]
        dignity = get_dignity(name, p["rashi_idx"], p["degree"])
        entry = {
            "rasi": p["rashi"],
            "degree": round(p["degree"], 4),
            "nakshatra": p["nakshatra"],
            "pada": p["pada"],
            "retrograde": p["retrograde"],
            "house": p["house"],
        }
        if dignity:
            entry["dignity"] = dignity
        data["planetary_positions"][p["yaml_key"]] = entry

    # House summary
    for h in range(1, 13):
        hs = house_summary[h]
        data["house_summary"][f"house_{h}"] = {
            "rasi": hs["rasi"],
            "planets": hs["planets"],
        }

    # Computed analysis (if provided)
    if computed_analysis:
        data["computed_analysis"] = computed_analysis

    return data


def write_birth_data_yaml(data, name):
    """Write birth_data.yaml to readings/<person_name>/."""
    folder_name = name.lower().replace(" ", "_")
    dir_path = os.path.join("readings", folder_name)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "birth_data.yaml")

    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    return file_path


# ---------------------------------------------------------------------------
# Human-Readable Print
# ---------------------------------------------------------------------------

def print_chart_summary(lagna, positions, dasha, house_summary,
                        ayanamsha, name, args):
    """Print human-readable chart summary to stderr (keeps stdout clean for JSON)."""
    out = sys.stderr

    out.write("=" * 70 + "\n")
    out.write(f"  VEDIC BIRTH CHART \u2014 {name.upper()}\n")
    out.write("=" * 70 + "\n")
    out.write(f"  Date: {args.dob}  Time: {args.tob}  Place: {args.place}\n")
    out.write(f"  Lat: {args.lat}  Lon: {args.lon}  TZ: {args.timezone}\n")
    out.write(f"  Ayanamsa (Lahiri): {format_dms(ayanamsha)}\n")

    out.write(f"\n  LAGNA: {lagna['rashi']} {format_dms(lagna['degree'])}\n")
    out.write(f"         {lagna['nakshatra']} Pada {lagna['pada']}\n")

    out.write("\n  " + "-" * 66 + "\n")
    out.write(
        f"  {'Graha':<10} {'Rashi':<14} {'Degree':<14} {'Nakshatra':<20} "
        f"{'Pada':>4} {'H':>3} {'R':>2} {'Dignity'}\n"
    )
    out.write("  " + "-" * 66 + "\n")

    graha_order = [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]
    for g in graha_order:
        p = positions[g]
        dignity = get_dignity(g, p["rashi_idx"], p["degree"]) or ""
        retro = "R" if p["retrograde"] else ""
        out.write(
            f"  {g:<10} {p['rashi']:<14} {format_dms(p['degree']):<14} "
            f"{p['nakshatra']:<20} {p['pada']:>4} {p['house']:>3} "
            f"{retro:>2} {dignity}\n"
        )

    out.write("\n  " + "-" * 66 + "\n")
    out.write("  HOUSE SUMMARY (Whole Sign)\n")
    out.write("  " + "-" * 66 + "\n")
    for h in range(1, 13):
        hs = house_summary[h]
        planets_str = ", ".join(hs["planets"]) if hs["planets"] else "\u2014"
        out.write(f"  House {h:>2}  {hs['rasi']:<14} {planets_str}\n")

    out.write("\n  " + "-" * 66 + "\n")
    out.write("  VIMSHOTTARI DASHA\n")
    out.write("  " + "-" * 66 + "\n")
    bal = dasha["balance_at_birth"]
    out.write(
        f"  Balance at birth: {bal['lord']} \u2014 "
        f"{bal['remaining_years']}y {bal['remaining_months']}m "
        f"{bal['remaining_days']}d\n"
    )
    for entry in dasha["sequence"]:
        out.write(
            f"  {entry['lord']:<10} {entry['start']}  to  {entry['end']}\n"
        )
    out.write("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Jyotish Birth Chart & Transit Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- birth subcommand (default behavior) ---
    birth_parser = subparsers.add_parser("birth", help="Compute birth chart")
    birth_parser.add_argument("--name", required=True,
                              help="Name of the native")
    birth_parser.add_argument("--dob", required=True,
                              help="Date of birth (YYYY-MM-DD)")
    birth_parser.add_argument("--tob", required=True,
                              help="Time of birth (HH:MM:SS)")
    birth_parser.add_argument("--place", required=True,
                              help="Place of birth (city, state, country)")
    birth_parser.add_argument("--timezone", required=True, type=float,
                              help="Timezone offset from UTC (e.g. 5.5)")
    birth_parser.add_argument("--lat", type=float, default=None,
                              help="Latitude (geocodes from place if omitted)")
    birth_parser.add_argument("--lon", type=float, default=None,
                              help="Longitude (geocodes from place if omitted)")
    birth_parser.add_argument("--gender", default=None,
                              help="Gender of the native")
    birth_parser.add_argument("--relationship", default=None,
                              help="Relationship (self, spouse, child, etc.)")
    birth_parser.add_argument("--true-node", action="store_true",
                              help="Use True Node for Rahu (default: Mean Node)")
    birth_parser.add_argument("--print", dest="print_summary",
                              action="store_true",
                              help="Print human-readable summary to stderr")

    # --- transit subcommand ---
    transit_parser = subparsers.add_parser(
        "transit", help="Compute transit positions for a person at a date"
    )
    transit_parser.add_argument(
        "--person", required=True,
        help="Person folder name under readings/ (e.g., jagan_mohan)"
    )
    transit_parser.add_argument(
        "--date", dest="target_date", default=None,
        help="Target date (YYYY-MM-DD). Defaults to today."
    )
    transit_parser.add_argument(
        "--type", dest="reading_type", default="transit_reading",
        help="Reading type (transit_reading, full_reading, etc.)"
    )
    transit_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable transit summary to stderr"
    )

    # For backward compatibility: if no subcommand given, check for --name
    # which indicates old-style birth chart usage
    args = parser.parse_args(argv)
    if args.command is None:
        # Legacy mode: re-parse as birth command
        sys.argv.insert(1, "birth")
        args = parser.parse_args()

    return args


def print_transit_summary(transit_data, person_name):
    """Print human-readable transit summary to stderr."""
    out = sys.stderr

    out.write("=" * 70 + "\n")
    out.write(f"  TRANSIT POSITIONS \u2014 {person_name.upper()}\n")
    out.write(f"  Date: {transit_data['reading_date']}\n")
    out.write("=" * 70 + "\n")

    # Current dasha
    dasha = transit_data.get("current_dasha", {})
    if dasha:
        md = dasha.get("mahadasha", {})
        ad = dasha.get("antardasha", {})
        pd = dasha.get("pratyantardasha", {})
        out.write(f"\n  ACTIVE DASHA: {md.get('lord', '?')}-"
                  f"{ad.get('lord', '?')}-{pd.get('lord', '?')}\n")
        out.write(f"    MD: {md.get('lord', '?')} "
                  f"({md.get('start', '?')} to {md.get('end', '?')})\n")
        out.write(f"    AD: {ad.get('lord', '?')} "
                  f"({ad.get('start', '?')} to {ad.get('end', '?')})\n")
        out.write(f"    PD: {pd.get('lord', '?')} "
                  f"({pd.get('start', '?')} to {pd.get('end', '?')})\n")

    # Transit positions
    out.write("\n  " + "-" * 66 + "\n")
    out.write(
        f"  {'Graha':<10} {'Rashi':<14} {'Degree':<10} "
        f"{'Nakshatra':<20} {'H(Lg)':>5} {'H(Mo)':>5} {'R':>2}\n"
    )
    out.write("  " + "-" * 66 + "\n")

    for yaml_key, pos in transit_data["transit_positions"].items():
        retro = "R" if pos.get("retrograde") else ""
        out.write(
            f"  {yaml_key:<10} {pos['rasi']:<14} "
            f"{pos['degree']:>8.4f}  "
            f"{pos['nakshatra']:<20} "
            f"{pos['house_from_lagna']:>5} "
            f"{pos['house_from_moon']:>5} "
            f"{retro:>2}\n"
        )

    # Special timing
    special = transit_data.get("special_timing", {})
    out.write("\n  " + "-" * 66 + "\n")
    out.write("  SPECIAL TIMING\n")
    out.write("  " + "-" * 66 + "\n")

    sade = special.get("sade_sati", {})
    if sade.get("active"):
        out.write(f"  Sade Sati: ACTIVE ({sade['phase']})\n")
    else:
        out.write("  Sade Sati: inactive\n")

    out.write(f"  Ashtama Shani: "
              f"{'YES' if special.get('ashtama_shani') else 'no'}\n")
    out.write(f"  Kantaka Shani: "
              f"{'YES' if special.get('kantaka_shani') else 'no'}\n")

    # Vedha
    vedha = transit_data.get("vedha", "none")
    if vedha != "none" and vedha:
        out.write("\n  VEDHA (Obstructions):\n")
        for planet, info in vedha.items():
            out.write(f"    {planet}: obstructed by {info['obstructing_planet']}"
                      f" in house {info['vedha_house']} from Moon\n")

    # All ADs in current MD
    all_ads = transit_data.get("all_antardashas_in_current_md", [])
    if all_ads:
        out.write("\n  " + "-" * 66 + "\n")
        out.write(f"  ALL ANTARDASHAS IN CURRENT MAHADASHA "
                  f"({dasha.get('mahadasha', {}).get('lord', '?')})\n")
        out.write("  " + "-" * 66 + "\n")
        for ad in all_ads:
            status = ad.get("status", "")
            marker = f" <<< {status}" if status else ""
            out.write(f"  {ad['lord']:<10} {ad['start']}  to  "
                      f"{ad['end']}{marker}\n")

    out.write("=" * 70 + "\n")


def main_birth(args):
    """Handle birth chart computation."""
    # Parse date and time
    dob_parts = [int(x) for x in args.dob.split("-")]
    tob_parts = [int(x) for x in args.tob.split(":")]
    year, month, day = dob_parts
    hour = tob_parts[0]
    minute = tob_parts[1]
    second = tob_parts[2] if len(tob_parts) > 2 else 0

    # Geocode if lat/lon not provided
    if args.lat is None or args.lon is None:
        args.lat, args.lon = geocode_place(args.place)

    # Initialize Swiss Ephemeris with Lahiri ayanamsha
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Julian Day
    jd = calculate_julian_day(year, month, day, hour, minute, second,
                              args.timezone)

    # Ascendant
    asc_sid, ayanamsha = calculate_ascendant(jd, args.lat, args.lon)
    asc_rashi, asc_rashi_idx, asc_deg = get_rashi(asc_sid)
    asc_nak, asc_nak_lord, asc_pada, _ = get_nakshatra(asc_sid)

    lagna = {
        "rashi": asc_rashi,
        "rashi_idx": asc_rashi_idx,
        "degree": asc_deg,
        "nakshatra": asc_nak,
        "pada": asc_pada,
    }

    # All planetary positions
    positions = calculate_all_positions(
        jd, ayanamsha, asc_rashi_idx, use_true_node=args.true_node
    )

    # Vimshottari dasha
    moon_lon = positions["Moon"]["sidereal_lon"]
    birth_date_obj = date(year, month, day)
    dasha = calculate_vimshottari_dasha(moon_lon, birth_date_obj)

    # House summary
    house_summary = build_house_summary(asc_rashi_idx, positions)

    # Computed analysis
    computed_analysis = build_computed_analysis(asc_rashi_idx, positions)

    # Build and write YAML
    birth_data = build_birth_data_dict(
        args, lagna, ayanamsha, positions, dasha,
        house_summary, args.true_node, computed_analysis
    )
    file_path = write_birth_data_yaml(birth_data, args.name)

    # Print human-readable summary if requested
    if args.print_summary:
        print_chart_summary(
            lagna, positions, dasha, house_summary,
            ayanamsha, args.name, args
        )

    # JSON status to stdout
    status = {
        "status": "success",
        "file": file_path,
        "lagna": lagna["rashi"],
        "moon_sign": positions["Moon"]["rashi"],
    }
    print(json.dumps(status))


def main_transit(args):
    """Handle transit computation."""
    target_date = args.target_date or date.today().isoformat()
    person = args.person
    birth_data_path = os.path.join("readings", person, "birth_data.yaml")

    if not os.path.exists(birth_data_path):
        print(json.dumps({
            "status": "error",
            "message": f"Birth data not found: {birth_data_path}",
        }))
        sys.exit(1)

    transit_data, output_path = compute_transits(
        birth_data_path, target_date, args.reading_type
    )

    if args.print_summary:
        print_transit_summary(transit_data, person)

    print(json.dumps({
        "status": "success",
        "file": output_path,
        "date": target_date,
        "dasha": (f"{transit_data['current_dasha']['mahadasha']['lord']}-"
                  f"{transit_data['current_dasha']['antardasha']['lord']}-"
                  f"{transit_data['current_dasha']['pratyantardasha']['lord']}"
                  if transit_data.get("current_dasha") else "unknown"),
    }))


def main(argv=None):
    args = parse_args(argv)

    if args.command == "transit":
        main_transit(args)
    else:
        main_birth(args)


if __name__ == "__main__":
    main()
