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
from datetime import date, timedelta

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
# YAML Output
# ---------------------------------------------------------------------------

def build_birth_data_dict(args, lagna, ayanamsha, positions, dasha,
                          house_summary, use_true_node):
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
        description="Jyotish Birth Chart Calculator"
    )
    parser.add_argument("--name", required=True,
                        help="Name of the native")
    parser.add_argument("--dob", required=True,
                        help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--tob", required=True,
                        help="Time of birth (HH:MM:SS)")
    parser.add_argument("--place", required=True,
                        help="Place of birth (city, state, country)")
    parser.add_argument("--timezone", required=True, type=float,
                        help="Timezone offset from UTC (e.g. 5.5 for IST)")
    parser.add_argument("--lat", type=float, default=None,
                        help="Latitude (geocodes from place if omitted)")
    parser.add_argument("--lon", type=float, default=None,
                        help="Longitude (geocodes from place if omitted)")
    parser.add_argument("--gender", default=None,
                        help="Gender of the native")
    parser.add_argument("--relationship", default=None,
                        help="Relationship (self, spouse, child, etc.)")
    parser.add_argument("--true-node", action="store_true",
                        help="Use True Node for Rahu (default: Mean Node)")
    parser.add_argument("--print", dest="print_summary", action="store_true",
                        help="Print human-readable summary to stderr")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

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

    # Build and write YAML
    birth_data = build_birth_data_dict(
        args, lagna, ayanamsha, positions, dasha,
        house_summary, args.true_node
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


if __name__ == "__main__":
    main()
