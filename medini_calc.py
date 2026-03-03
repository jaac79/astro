#!/usr/bin/env python3
"""
Medini (Mundane) Astrology Calculator

Computes planetary positions, ingresses, eclipses, and other mundane
astrology data using Swiss Ephemeris with Lahiri Ayanamsha.

Mirrors jyotish_calc.py for natal charts; this tool focuses on
world-level transits and events.

Usage:
    python medini_calc.py positions --date 2026-02-28 --print
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

import swisseph as swe
import yaml

# ---------------------------------------------------------------------------
# Import core functions from jyotish_calc.py
# ---------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from jyotish_calc import (
    # Constants
    RASHI_NAMES,
    NAKSHATRAS,
    NAKSHATRA_SPAN,
    GRAHA_LIST,
    DASHA_SEQUENCE,
    DASHA_YEARS,
    RASI_LORD,
    EXALTATION,
    DEBILITATION,
    OWN_SIGNS,
    NATURAL_FRIENDS,
    # Core functions
    calculate_julian_day,
    get_nakshatra,
    get_rashi,
    format_dms,
    calculate_ascendant,
    calculate_planet_position,
    calculate_all_positions,
    get_dignity,
    calculate_vimshottari_dasha,
    build_house_summary,
    build_computed_analysis,
)

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

WORLD_DATA_DIR = os.path.join(_SCRIPT_DIR, "world_data")


# ---------------------------------------------------------------------------
# Positions command
# ---------------------------------------------------------------------------

def cmd_positions(args):
    """Compute sidereal planetary positions for a given date at 00:00 UTC.

    No lagna / houses — pure sky positions for mundane analysis.
    """
    # Parse date
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    # Julian Day at 00:00 UTC
    jd = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)

    # Lahiri ayanamsha
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    # Build positions for all 9 grahas
    planetary_positions = {}

    # 7 visible grahas
    for swe_id, eng_name, sans_name, yaml_key in GRAHA_LIST:
        pos, _ret = swe.calc_ut(jd, swe_id)
        tropical_lon = pos[0]
        sid_lon = (tropical_lon - ayanamsha) % 360
        speed = pos[3]

        rashi_name, rashi_idx, deg = get_rashi(sid_lon)
        nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(sid_lon)
        retrograde = speed < 0

        planetary_positions[yaml_key] = {
            "rasi": rashi_name,
            "degree": round(deg, 4),
            "nakshatra": nak_name,
            "pada": pada,
            "retrograde": retrograde,
        }

    # Rahu (Mean Node)
    node_id = swe.MEAN_NODE
    pos, _ret = swe.calc_ut(jd, node_id)
    rahu_tropical = pos[0]
    rahu_sid = (rahu_tropical - ayanamsha) % 360

    rahu_rashi, rahu_rashi_idx, rahu_deg = get_rashi(rahu_sid)
    rahu_nak, rahu_nak_lord, rahu_pada, _ = get_nakshatra(rahu_sid)

    planetary_positions["rahu"] = {
        "rasi": rahu_rashi,
        "degree": round(rahu_deg, 4),
        "nakshatra": rahu_nak,
        "pada": rahu_pada,
        "retrograde": True,
    }

    # Ketu (180 degrees opposite Rahu)
    ketu_sid = (rahu_sid + 180) % 360
    ketu_rashi, ketu_rashi_idx, ketu_deg = get_rashi(ketu_sid)
    ketu_nak, ketu_nak_lord, ketu_pada, _ = get_nakshatra(ketu_sid)

    planetary_positions["ketu"] = {
        "rasi": ketu_rashi,
        "degree": round(ketu_deg, 4),
        "nakshatra": ketu_nak,
        "pada": ketu_pada,
        "retrograde": True,
    }

    # Assemble output
    output = {
        "date": str(target_date),
        "time_utc": "00:00:00",
        "ayanamsha": round(ayanamsha, 6),
        "ayanamsha_type": "Lahiri",
        "planetary_positions": planetary_positions,
    }

    # Write to file
    positions_dir = os.path.join(WORLD_DATA_DIR, "positions")
    os.makedirs(positions_dir, exist_ok=True)
    out_file = os.path.join(positions_dir, f"{target_date}_positions.yaml")

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary if requested
    if args.print_summary:
        print("=" * 60, file=sys.stderr)
        print(f"  Medini Planetary Positions — {target_date}", file=sys.stderr)
        print(f"  Time: 00:00 UTC  |  Ayanamsha: {ayanamsha:.4f} (Lahiri)",
              file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        graha_order = [
            "surya", "chandra", "mangal", "budha",
            "guru", "shukra", "shani", "rahu", "ketu",
        ]
        for key in graha_order:
            p = planetary_positions[key]
            retro = " (R)" if p["retrograde"] else ""
            print(
                f"  {key.capitalize():10s}  {p['rasi']:14s}  "
                f"{p['degree']:7.2f}°  {p['nakshatra']:20s}  "
                f"Pada {p['pada']}{retro}",
                file=sys.stderr,
            )
        print("=" * 60, file=sys.stderr)

    # JSON status to stdout
    status = {"status": "success", "file": out_file, "date": str(target_date)}
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Ingress command
# ---------------------------------------------------------------------------

# Cardinal sign ingress targets (sidereal longitudes)
INGRESS_TARGETS = {
    "aries": 0.0,
    "cancer": 90.0,
    "libra": 180.0,
    "capricorn": 270.0,
}

# Ingress type -> readable sign name
INGRESS_SIGN_NAMES = {
    "aries": "Mesham",
    "cancer": "Katakam",
    "libra": "Thulam",
    "capricorn": "Makaram",
}

# Weekday index (0=Monday in datetime) -> (day name, ruling planet)
WEEKDAY_RULERS = {
    0: ("Monday", "Moon"),
    1: ("Tuesday", "Mars"),
    2: ("Wednesday", "Mercury"),
    3: ("Thursday", "Jupiter"),
    4: ("Friday", "Venus"),
    5: ("Saturday", "Saturn"),
    6: ("Sunday", "Sun"),
}


def find_solar_ingress_jd(target_sid_lon, year):
    """Find the exact Julian Day when the Sun crosses target_sid_lon (sidereal).

    Uses swe.solcross_ut which finds when the Sun reaches a given tropical
    longitude. We convert sidereal target to tropical by adding ayanamsha.

    Because ayanamsha changes slightly between the initial estimate and the
    actual crossing moment, we iterate: compute the crossing, get the exact
    ayanamsha there, recompute the tropical target, and search again.
    Typically converges in 2 iterations.

    Returns (jd, ayanamsha) at the exact ingress moment.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Start searching from Jan 1 of the given year
    jd_start = swe.julday(year, 1, 1, 0.0)

    # Initial ayanamsha estimate
    ayanamsha = swe.get_ayanamsa(jd_start)

    # Iterate to refine (ayanamsha at crossing differs from Jan 1)
    for _ in range(5):
        tropical_target = (target_sid_lon + ayanamsha) % 360

        if hasattr(swe, 'solcross_ut'):
            jd_cross = swe.solcross_ut(tropical_target, jd_start, 0)
        else:
            jd_cross = _bisect_solar_crossing(tropical_target, jd_start)

        ayanamsha_new = swe.get_ayanamsa(jd_cross)

        # Check convergence (ayanamsha stable to ~0.01 arcsec)
        if abs(ayanamsha_new - ayanamsha) < 1e-6:
            break
        ayanamsha = ayanamsha_new

    return jd_cross, ayanamsha


def _bisect_solar_crossing(tropical_target, jd_start):
    """Fallback bisection method to find when Sun crosses tropical_target."""
    jd = jd_start
    prev_lon = None
    for _ in range(400):
        pos, _ = swe.calc_ut(jd, swe.SUN)
        lon = pos[0]
        if prev_lon is not None:
            if _crosses_target(prev_lon, lon, tropical_target):
                return _bisect(jd - 1.0, jd, tropical_target)
        prev_lon = lon
        jd += 1.0

    raise ValueError(f"Could not find solar crossing of {tropical_target} "
                     f"within 400 days of JD {jd_start}")


def _crosses_target(lon1, lon2, target):
    """Check if target is between lon1 and lon2, accounting for wraparound."""
    if abs(lon2 - lon1) > 180:
        return (lon1 <= target or target <= lon2) if lon2 < lon1 else (
            lon2 <= target or target <= lon1)
    return min(lon1, lon2) <= target <= max(lon1, lon2)


def _bisect(jd_lo, jd_hi, target, tolerance=1e-8, max_iter=100):
    """Bisect to find JD when Sun longitude = target."""
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2
        pos, _ = swe.calc_ut(jd_mid, swe.SUN)
        lon = pos[0]
        diff = (lon - target + 180) % 360 - 180
        if abs(diff) < tolerance:
            return jd_mid
        if diff < 0:
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2


def jd_to_utc_datetime(jd):
    """Convert Julian Day to Python datetime (UTC)."""
    year, month, day, hour_frac = swe.revjul(jd)
    hours = int(hour_frac)
    minutes_frac = (hour_frac - hours) * 60
    minutes = int(minutes_frac)
    seconds_frac = (minutes_frac - minutes) * 60
    seconds = int(seconds_frac)
    microseconds = int((seconds_frac - seconds) * 1e6)
    return datetime(year, month, day, hours, minutes, seconds, microseconds)


def cmd_ingress(args):
    """Compute solar ingress chart for a cardinal sign and year.

    Finds the exact moment the Sun enters the target sidereal sign,
    computes a full chart (lagna, planetary positions, dasha, yogas)
    for that moment at the specified location, and writes a YAML file.
    """
    ingress_type = args.ingress_type
    year = args.year
    lat = args.lat
    lon = args.lon
    timezone = args.timezone
    city = args.city

    target_sid_lon = INGRESS_TARGETS[ingress_type]

    # Initialize Swiss Ephemeris
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Find exact ingress Julian Day
    jd_ingress, ayanamsha = find_solar_ingress_jd(target_sid_lon, year)

    # Convert to UTC datetime
    utc_dt = jd_to_utc_datetime(jd_ingress)

    # Local datetime
    local_dt = utc_dt + timedelta(hours=timezone)

    # Weekday and year lord
    weekday_idx = local_dt.weekday()  # 0=Monday
    weekday_name, year_lord = WEEKDAY_RULERS[weekday_idx]

    # --- Build full chart at ingress moment for the given location ---

    # Ascendant (lagna)
    asc_sid, ayanamsha = calculate_ascendant(jd_ingress, lat, lon)
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
    positions = calculate_all_positions(jd_ingress, ayanamsha, asc_rashi_idx)

    # Fix Sun's boundary condition: at ingress, Sun is exactly at 0 deg of
    # the target sign, but floating-point can place it at 29.9999 of the
    # prior sign. Force Sun to the target sign with degree 0.
    target_rashi_idx = int(target_sid_lon / 30) % 12
    sun = positions["Sun"]
    if abs(sun["sidereal_lon"] - target_sid_lon) < 0.001 or (
        target_sid_lon == 0 and sun["sidereal_lon"] > 359.999
    ):
        sun["sidereal_lon"] = target_sid_lon
        sun["rashi"] = RASHI_NAMES[target_rashi_idx]
        sun["rashi_idx"] = target_rashi_idx
        sun["degree"] = 0.0
        sun["house"] = ((target_rashi_idx - asc_rashi_idx) % 12) + 1
        nak_name, nak_lord, pada, _ = get_nakshatra(target_sid_lon)
        sun["nakshatra"] = nak_name
        sun["nak_lord"] = nak_lord
        sun["pada"] = pada

    # Moon data for chandra section and dasha
    moon = positions["Moon"]

    chandra = {
        "rasi": moon["rashi"],
        "degree": round(moon["degree"], 4),
        "nakshatra": moon["nakshatra"],
        "pada": moon["pada"],
    }

    # Vimshottari dasha (from Moon position, using ingress date as "birth")
    ingress_date_obj = utc_dt.date()
    dasha = calculate_vimshottari_dasha(moon["sidereal_lon"], ingress_date_obj)

    # House summary
    house_summary = build_house_summary(asc_rashi_idx, positions)

    # Computed analysis
    computed_analysis = build_computed_analysis(asc_rashi_idx, positions)

    # --- Build planetary_positions for YAML output ---
    yaml_positions = {}
    graha_order = [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]
    for g in graha_order:
        p = positions[g]
        dignity = get_dignity(g, p["rashi_idx"], p["degree"])
        yaml_key = p["yaml_key"]
        yaml_positions[yaml_key] = {
            "rasi": p["rashi"],
            "degree": round(p["degree"], 4),
            "nakshatra": p["nakshatra"],
            "pada": p["pada"],
            "retrograde": p["retrograde"],
            "house": p["house"],
            "dignity": dignity if dignity else "neutral",
        }

    # --- Build house_summary for YAML output ---
    yaml_houses = {}
    for h in range(1, 13):
        hs = house_summary[h]
        yaml_houses[f"house_{h}"] = {
            "rasi": hs["rasi"],
            "planets": hs["planets"] if hs["planets"] else [],
        }

    # --- Build dasha for YAML output ---
    yaml_dasha = {
        "balance_at_birth": dasha["balance_at_birth"],
        "sequence": dasha["sequence"],
    }

    # --- Assemble full output ---
    output = {
        "ingress": {
            "type": ingress_type,
            "year": year,
            "exact_datetime_utc": utc_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "local_datetime": local_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "weekday": weekday_name,
            "year_lord": year_lord,
            "place": {
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "timezone": timezone,
            },
        },
        "lagna": {
            "rasi": lagna["rashi"],
            "degree": round(lagna["degree"], 4),
            "nakshatra": lagna["nakshatra"],
            "pada": lagna["pada"],
        },
        "chandra": chandra,
        "planetary_positions": yaml_positions,
        "house_summary": yaml_houses,
        "vimshottari_dasha": yaml_dasha,
        "computed_analysis": computed_analysis,
    }

    # --- Write YAML file ---
    ingress_dir = os.path.join(WORLD_DATA_DIR, "ingress")
    os.makedirs(ingress_dir, exist_ok=True)
    out_file = os.path.join(ingress_dir, f"{year}_{ingress_type}_ingress.yaml")

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # --- Print human-readable summary ---
    if args.print_summary:
        _print_ingress_summary(
            ingress_type, year, utc_dt, local_dt, weekday_name, year_lord,
            city, lat, lon, timezone, ayanamsha,
            lagna, positions, dasha, house_summary,
        )

    # --- JSON status to stdout ---
    status = {
        "status": "success",
        "file": out_file,
        "ingress_type": ingress_type,
        "year": year,
        "exact_datetime_utc": utc_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "weekday": weekday_name,
        "year_lord": year_lord,
        "lagna": lagna["rashi"],
        "moon_sign": moon["rashi"],
    }
    print(json.dumps(status))


def _print_ingress_summary(ingress_type, year, utc_dt, local_dt,
                           weekday_name, year_lord, city, lat, lon, timezone,
                           ayanamsha, lagna, positions, dasha, house_summary):
    """Print human-readable ingress chart summary to stderr."""
    out = sys.stderr
    sign_name = INGRESS_SIGN_NAMES[ingress_type]

    out.write("=" * 70 + "\n")
    out.write(f"  SOLAR INGRESS CHART -- {ingress_type.upper()} "
              f"({sign_name}) {year}\n")
    out.write("=" * 70 + "\n")
    out.write(f"  Exact UTC:  {utc_dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
    out.write(f"  Local Time: {local_dt.strftime('%Y-%m-%d %H:%M:%S')} "
              f"(UTC{'+' if timezone >= 0 else ''}{timezone})\n")
    out.write(f"  Weekday:    {weekday_name}  |  Year Lord: {year_lord}\n")
    out.write(f"  Place:      {city} ({lat}, {lon})\n")
    out.write(f"  Ayanamsa:   {format_dms(ayanamsha)} (Lahiri)\n")

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
    out.write("  VIMSHOTTARI DASHA (from ingress Moon)\n")
    out.write("  " + "-" * 66 + "\n")
    bal = dasha["balance_at_birth"]
    out.write(
        f"  Balance: {bal['lord']} -- "
        f"{bal['remaining_years']}y {bal['remaining_months']}m "
        f"{bal['remaining_days']}d\n"
    )
    for entry in dasha["sequence"]:
        out.write(
            f"  {entry['lord']:<10} {entry['start']}  to  {entry['end']}\n"
        )
    out.write("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Eclipse helpers
# ---------------------------------------------------------------------------

def _jd_to_datetime(jd):
    """Convert Julian Day to Python datetime (UTC)."""
    # swe.revjul returns (year, month, day, hour_decimal)
    year, month, day, hour_dec = swe.revjul(jd, swe.GREG_CAL)
    hours = int(hour_dec)
    minutes = int((hour_dec - hours) * 60)
    seconds = int(((hour_dec - hours) * 60 - minutes) * 60)
    return datetime(year, month, day, hours, minutes, seconds)


def _jd_to_iso(jd):
    """Convert JD to ISO 8601 UTC string."""
    dt = _jd_to_datetime(jd)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _classify_solar_eclipse(retval):
    """Classify solar eclipse type from swe.sol_eclipse_when_glob retval flags."""
    if retval & swe.ECL_TOTAL:
        return "total"
    elif retval & swe.ECL_ANNULAR:
        return "annular"
    elif retval & swe.ECL_PARTIAL:
        return "partial"
    elif retval & swe.ECL_ANNULAR_TOTAL:
        return "hybrid"
    return "partial"


def _classify_lunar_eclipse(retval):
    """Classify lunar eclipse type from swe.lun_eclipse_when retval flags."""
    if retval & swe.ECL_TOTAL:
        return "total"
    elif retval & swe.ECL_PARTIAL:
        return "partial"
    elif retval & swe.ECL_PENUMBRAL:
        return "penumbral"
    return "penumbral"


def _compute_body_position_at_jd(jd, body_id):
    """Compute sidereal position of a body (Sun or Moon) at a given JD.

    Returns dict with rasi, degree, nakshatra, pada.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)
    pos, _ret = swe.calc_ut(jd, body_id)
    sid_lon = (pos[0] - ayanamsha) % 360
    rashi_name, rashi_idx, deg = get_rashi(sid_lon)
    nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(sid_lon)
    return {
        "rasi": rashi_name,
        "degree": round(deg, 4),
        "sidereal_longitude": round(sid_lon, 4),
        "nakshatra": nak_name,
        "nakshatra_pada": pada,
    }


def _find_solar_eclipses_in_year(year):
    """Find all solar eclipses in a given year.

    Returns list of dicts with eclipse data.
    """
    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year + 1, 1, 1, 0.0)
    eclipses = []

    while True:
        retval, tret = swe.sol_eclipse_when_glob(jd_start, 0)
        if tret[0] >= jd_end:
            break
        jd_max = tret[0]
        dt_max = _jd_to_datetime(jd_max)
        subtype = _classify_solar_eclipse(retval)
        sun_pos = _compute_body_position_at_jd(jd_max, swe.SUN)

        eclipses.append({
            "date": dt_max.strftime("%Y-%m-%d"),
            "type": "solar",
            "subtype": subtype,
            "sign": sun_pos["rasi"],
            "nakshatra": sun_pos["nakshatra"],
            "nakshatra_pada": sun_pos["nakshatra_pada"],
            "degree_in_sign": sun_pos["degree"],
            "sidereal_longitude": sun_pos["sidereal_longitude"],
            "maximum_utc": _jd_to_iso(jd_max),
            "_jd_max": jd_max,
        })

        # Move past this eclipse (at least 20 days ahead to find next one)
        jd_start = jd_max + 20.0

    return eclipses


def _find_lunar_eclipses_in_year(year):
    """Find all lunar eclipses in a given year.

    Returns list of dicts with eclipse data.
    """
    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year + 1, 1, 1, 0.0)
    eclipses = []

    while True:
        retval, tret = swe.lun_eclipse_when(jd_start, 0)
        if tret[0] >= jd_end:
            break
        jd_max = tret[0]
        dt_max = _jd_to_datetime(jd_max)
        subtype = _classify_lunar_eclipse(retval)
        moon_pos = _compute_body_position_at_jd(jd_max, swe.MOON)

        eclipses.append({
            "date": dt_max.strftime("%Y-%m-%d"),
            "type": "lunar",
            "subtype": subtype,
            "sign": moon_pos["rasi"],
            "nakshatra": moon_pos["nakshatra"],
            "nakshatra_pada": moon_pos["nakshatra_pada"],
            "degree_in_sign": moon_pos["degree"],
            "sidereal_longitude": moon_pos["sidereal_longitude"],
            "maximum_utc": _jd_to_iso(jd_max),
            "_jd_max": jd_max,
        })

        # Move past this eclipse
        jd_start = jd_max + 20.0

    return eclipses


# ---------------------------------------------------------------------------
# Eclipses command — list all eclipses in a year
# ---------------------------------------------------------------------------

def cmd_eclipses(args):
    """List all solar and lunar eclipses in a given year."""
    year = args.year

    solar = _find_solar_eclipses_in_year(year)
    lunar = _find_lunar_eclipses_in_year(year)

    # Merge and sort by date
    all_eclipses = solar + lunar
    all_eclipses.sort(key=lambda e: e["date"])

    # Clean up internal fields for output
    output_eclipses = []
    for ecl in all_eclipses:
        out = {k: v for k, v in ecl.items() if not k.startswith("_")}
        output_eclipses.append(out)

    output = {
        "year": year,
        "total_eclipses": len(output_eclipses),
        "solar_count": len(solar),
        "lunar_count": len(lunar),
        "eclipses": output_eclipses,
    }

    # Write to file
    eclipses_dir = os.path.join(WORLD_DATA_DIR, "eclipses")
    os.makedirs(eclipses_dir, exist_ok=True)
    out_file = os.path.join(eclipses_dir, f"{year}_eclipse_calendar.yaml")

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary
    if args.print_summary:
        print("=" * 70, file=sys.stderr)
        print(f"  Eclipse Calendar — {year}", file=sys.stderr)
        print(f"  {len(solar)} solar + {len(lunar)} lunar = "
              f"{len(all_eclipses)} total", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        for ecl in output_eclipses:
            print(
                f"  {ecl['date']}  {ecl['type'].upper():6s}  "
                f"{ecl['subtype']:10s}  {ecl['sign']:14s}  "
                f"{ecl['nakshatra']:20s}  Pada {ecl['nakshatra_pada']}",
                file=sys.stderr,
            )
        print("=" * 70, file=sys.stderr)

    # JSON status to stdout
    status = {"status": "success", "file": out_file, "year": year,
              "count": len(all_eclipses)}
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Eclipse command — detailed chart for a single eclipse
# ---------------------------------------------------------------------------

def _find_nearest_eclipse(target_date):
    """Find the nearest eclipse (solar or lunar) to a given date.

    Searches in a window of +/- 40 days around the target date.
    Returns the eclipse dict with _jd_max, or None.
    """
    year = target_date.year
    target_jd = swe.julday(target_date.year, target_date.month,
                            target_date.day, 12.0)

    candidates = []

    # Search solar eclipses: start 40 days before target
    jd_search = target_jd - 40.0
    for _ in range(3):  # at most 3 iterations
        retval, tret = swe.sol_eclipse_when_glob(jd_search, 0)
        jd_max = tret[0]
        if abs(jd_max - target_jd) <= 40:
            dt_max = _jd_to_datetime(jd_max)
            subtype = _classify_solar_eclipse(retval)
            sun_pos = _compute_body_position_at_jd(jd_max, swe.SUN)
            candidates.append({
                "type": "solar",
                "subtype": subtype,
                "_jd_max": jd_max,
                "_tret": tret,
                "_retval": retval,
                "date": dt_max.strftime("%Y-%m-%d"),
                "maximum_utc": _jd_to_iso(jd_max),
                "sign": sun_pos["rasi"],
                "nakshatra": sun_pos["nakshatra"],
                "nakshatra_pada": sun_pos["nakshatra_pada"],
                "degree_in_sign": sun_pos["degree"],
                "sidereal_longitude": sun_pos["sidereal_longitude"],
            })
        jd_search = jd_max + 20.0

    # Search lunar eclipses: start 40 days before target
    jd_search = target_jd - 40.0
    for _ in range(3):
        retval, tret = swe.lun_eclipse_when(jd_search, 0)
        jd_max = tret[0]
        if abs(jd_max - target_jd) <= 40:
            dt_max = _jd_to_datetime(jd_max)
            subtype = _classify_lunar_eclipse(retval)
            moon_pos = _compute_body_position_at_jd(jd_max, swe.MOON)
            candidates.append({
                "type": "lunar",
                "subtype": subtype,
                "_jd_max": jd_max,
                "_tret": tret,
                "_retval": retval,
                "date": dt_max.strftime("%Y-%m-%d"),
                "maximum_utc": _jd_to_iso(jd_max),
                "sign": moon_pos["rasi"],
                "nakshatra": moon_pos["nakshatra"],
                "nakshatra_pada": moon_pos["nakshatra_pada"],
                "degree_in_sign": moon_pos["degree"],
                "sidereal_longitude": moon_pos["sidereal_longitude"],
            })
        jd_search = jd_max + 20.0

    if not candidates:
        return None

    # Return the one nearest to target date
    candidates.sort(key=lambda c: abs(c["_jd_max"] - target_jd))
    return candidates[0]


def cmd_eclipse(args):
    """Compute detailed chart for the eclipse nearest to the given date."""
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    lat = args.lat
    lon = args.lon
    tz = args.timezone

    eclipse = _find_nearest_eclipse(target_date)
    if eclipse is None:
        print(json.dumps({
            "status": "error",
            "message": f"No eclipse found near {target_date}",
        }))
        return

    jd_max = eclipse["_jd_max"]
    tret = eclipse["_tret"]

    # Compute duration from tret array
    # Solar tret: [0]=max, [2]=begin, [3]=end, [4]=totality_begin,
    #             [5]=totality_end
    # Lunar tret: [0]=max, [2]=partial_begin, [3]=partial_end,
    #             [4]=totality_begin, [5]=totality_end,
    #             [6]=penumbral_begin, [7]=penumbral_end
    duration_minutes = None
    if eclipse["type"] == "lunar":
        # Use penumbral duration as the overall duration
        if tret[7] > 0 and tret[6] > 0:
            duration_minutes = round((tret[7] - tret[6]) * 24 * 60, 1)
        # Prefer partial duration if available (more meaningful)
        if tret[3] > 0 and tret[2] > 0:
            partial_dur = round((tret[3] - tret[2]) * 24 * 60, 1)
            if partial_dur > 0:
                duration_minutes = partial_dur
    else:
        # Solar eclipse: tret[2]=begin, tret[3]=end
        if tret[3] > 0 and tret[2] > 0:
            duration_minutes = round((tret[3] - tret[2]) * 24 * 60, 1)

    # ---- Compute full chart at moment of maximum eclipse ----
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    asc_sid, ayanamsha = calculate_ascendant(jd_max, lat, lon)
    lagna_rashi, lagna_rashi_idx, lagna_deg = get_rashi(asc_sid)
    lagna_nak, lagna_nak_lord, lagna_pada, _ = get_nakshatra(asc_sid)

    # All planetary positions
    positions = calculate_all_positions(jd_max, ayanamsha, lagna_rashi_idx)

    # Build planetary_positions output (yaml-key based)
    planetary_positions = {}
    graha_order = [
        "surya", "chandra", "mangal", "budha",
        "guru", "shukra", "shani", "rahu", "ketu",
    ]
    for eng_name, pdata in positions.items():
        yaml_key = pdata["yaml_key"]
        dignity = get_dignity(eng_name, pdata["rashi_idx"],
                              pdata["degree"]) or ""
        planetary_positions[yaml_key] = {
            "rasi": pdata["rashi"],
            "degree": round(pdata["degree"], 4),
            "nakshatra": pdata["nakshatra"],
            "pada": pdata["pada"],
            "retrograde": pdata["retrograde"],
            "house": pdata["house"],
            "dignity": dignity,
        }

    # House summary
    house_summary = {}
    for h in range(1, 13):
        rashi_idx = (lagna_rashi_idx + h - 1) % 12
        occupants = []
        for eng_name, pdata in positions.items():
            if pdata["house"] == h:
                occupants.append(pdata["yaml_key"])
        house_summary[f"house_{h}"] = {
            "rasi": RASHI_NAMES[rashi_idx],
            "planets": occupants if occupants else [],
        }

    # Assemble output
    eclipse_info = {
        "type": eclipse["type"],
        "subtype": eclipse["subtype"],
        "date_utc": eclipse["date"],
        "maximum_utc": eclipse["maximum_utc"],
        "sign": eclipse["sign"],
        "nakshatra": eclipse["nakshatra"],
        "nakshatra_pada": eclipse["nakshatra_pada"],
        "degree_in_sign": eclipse["degree_in_sign"],
        "sidereal_longitude": eclipse["sidereal_longitude"],
        "place": {
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
        },
    }
    if duration_minutes is not None:
        eclipse_info["duration_minutes"] = duration_minutes

    output = {
        "eclipse": eclipse_info,
        "ayanamsha": round(ayanamsha, 6),
        "ayanamsha_type": "Lahiri",
        "lagna": {
            "rasi": lagna_rashi,
            "degree": round(lagna_deg, 4),
            "nakshatra": lagna_nak,
            "pada": lagna_pada,
        },
        "planetary_positions": planetary_positions,
        "house_summary": house_summary,
    }

    # Write to file
    eclipses_dir = os.path.join(WORLD_DATA_DIR, "eclipses")
    os.makedirs(eclipses_dir, exist_ok=True)
    ecl_type = eclipse["type"]
    out_file = os.path.join(
        eclipses_dir,
        f"{eclipse['date']}_{ecl_type}_eclipse.yaml",
    )

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary
    if args.print_summary:
        print("=" * 70, file=sys.stderr)
        print(f"  {eclipse['subtype'].upper()} {eclipse['type'].upper()} "
              f"ECLIPSE — {eclipse['date']}", file=sys.stderr)
        print(f"  Maximum: {eclipse['maximum_utc']} UTC", file=sys.stderr)
        if duration_minutes:
            print(f"  Duration: {duration_minutes} minutes", file=sys.stderr)
        print(f"  Eclipsed body in: {eclipse['sign']} "
              f"({eclipse['nakshatra']} Pada {eclipse['nakshatra_pada']})",
              file=sys.stderr)
        print(f"  Location: lat={lat}, lon={lon}, tz={tz}", file=sys.stderr)
        print("-" * 70, file=sys.stderr)
        print(f"  Lagna: {lagna_rashi} {lagna_deg:.2f}° "
              f"({lagna_nak} Pada {lagna_pada})", file=sys.stderr)
        print("-" * 70, file=sys.stderr)
        print("  PLANETARY POSITIONS:", file=sys.stderr)
        for key in graha_order:
            p = planetary_positions[key]
            retro = " (R)" if p["retrograde"] else ""
            dig = f" [{p['dignity']}]" if p["dignity"] else ""
            print(
                f"    {key.capitalize():10s}  H{p['house']:<3d}  "
                f"{p['rasi']:14s}  {p['degree']:7.2f}°  "
                f"{p['nakshatra']:20s}  Pada {p['pada']}"
                f"{retro}{dig}",
                file=sys.stderr,
            )
        print("-" * 70, file=sys.stderr)
        print("  HOUSE SUMMARY:", file=sys.stderr)
        for h in range(1, 13):
            hk = f"house_{h}"
            hs = house_summary[hk]
            planets_str = ", ".join(hs["planets"]) if hs["planets"] else "—"
            print(f"    House {h:2d}  {hs['rasi']:14s}  {planets_str}",
                  file=sys.stderr)
        print("=" * 70, file=sys.stderr)

    # JSON status to stdout
    status = {
        "status": "success",
        "file": out_file,
        "eclipse_type": eclipse["type"],
        "eclipse_subtype": eclipse["subtype"],
        "date": eclipse["date"],
    }
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Panchanga command
# ---------------------------------------------------------------------------

# Vara (weekday) data — indexed by Julian Day % 7
# JD 0 (Monday, Jan 1, 4713 BCE) -> index 0 = Monday
# Formula: weekday = (int(jd + 1.5)) % 7 -> 0=Sun,1=Mon,...,6=Sat
VARA_DATA = [
    ("Ravivara", "Sunday", "Sun"),
    ("Somavara", "Monday", "Moon"),
    ("Mangalavara", "Tuesday", "Mars"),
    ("Budhavara", "Wednesday", "Mercury"),
    ("Guruvara", "Thursday", "Jupiter"),
    ("Shukravara", "Friday", "Venus"),
    ("Shanivara", "Saturday", "Saturn"),
]

# 30 Tithi names
TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

# Tithi lords cycle (8 lords, repeating)
TITHI_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
               "Saturn", "Rahu"]

# 27 Yoga names
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

# 11 Karana names: 4 fixed + 7 rotating
# Fixed karanas appear once each: Kimstughna(first), Shakuni, Chatushpada, Naga(last three)
# 7 rotating karanas repeat 8 times (karanas 2-57)
KARANA_ROTATING = ["Bava", "Balava", "Kaulava", "Taitila", "Gara",
                   "Vanija", "Vishti"]
KARANA_FIXED_FIRST = "Kimstughna"
KARANA_FIXED_LAST = ["Shakuni", "Chatushpada", "Naga"]


def _get_karana_name(karana_index):
    """Get karana name from 0-based index (0-59).

    karana 0 = Kimstughna (fixed)
    karanas 1-56 = rotating cycle of 7 (Bava..Vishti) x 8
    karanas 57-59 = Shakuni, Chatushpada, Naga (fixed)
    """
    if karana_index == 0:
        return KARANA_FIXED_FIRST
    elif karana_index <= 56:
        return KARANA_ROTATING[(karana_index - 1) % 7]
    else:
        return KARANA_FIXED_LAST[karana_index - 57]


def cmd_panchanga(args):
    """Compute panchanga (five-fold almanac) for a given date and place.

    The five elements are:
    1. Vara (weekday)
    2. Tithi (lunar day based on Moon-Sun angular distance)
    3. Nakshatra (Moon's sidereal asterism)
    4. Yoga (Sun-Moon combination)
    5. Karana (half-tithi)
    """
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    lat = args.lat
    lon = args.lon
    tz = args.timezone

    # Compute Julian Day at local sunrise approximation (06:00 local time)
    # Convert local 06:00 to UTC
    local_sunrise_hour = 6.0
    utc_hour = local_sunrise_hour - tz
    jd = swe.julday(target_date.year, target_date.month, target_date.day,
                     utc_hour)

    # Try to compute actual sunrise using swe.rise_trans
    try:
        # swe.rise_trans(jd_start, body, lon, lat, alt, pressure, temp, flag)
        # flag: swe.CALC_RISE = 1
        rsmi = swe.CALC_RISE | swe.BIT_DISC_CENTER
        ret = swe.rise_trans(jd - 0.5, swe.SUN, "", 0, rsmi,
                             (lon, lat, 0), 1013.25, 15)
        if ret[0] == 0 and ret[1][0] > 0:
            jd = ret[1][0]
    except Exception:
        pass  # fall back to 06:00 local

    # --- Ayanamsha ---
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    # --- Tropical longitudes of Sun and Moon ---
    sun_pos, _ = swe.calc_ut(jd, swe.SUN)
    moon_pos, _ = swe.calc_ut(jd, swe.MOON)
    sun_trop = sun_pos[0]
    moon_trop = moon_pos[0]

    # --- Sidereal longitudes ---
    sun_sid = (sun_trop - ayanamsha) % 360
    moon_sid = (moon_trop - ayanamsha) % 360

    # ===================================================================
    # 1. VARA (Weekday)
    # ===================================================================
    # Julian Day weekday: (int(jd + 1.5)) % 7 -> 0=Sun,1=Mon,...,6=Sat
    vara_idx = int(jd + 1.5) % 7
    vara_name, vara_english, vara_lord = VARA_DATA[vara_idx]

    # ===================================================================
    # 2. TITHI (Lunar Day)
    # ===================================================================
    moon_sun_angle = (moon_trop - sun_trop) % 360
    tithi_number = int(moon_sun_angle / 12) + 1  # 1-30
    tithi_name = TITHI_NAMES[tithi_number - 1]
    paksha = "Shukla" if tithi_number <= 15 else "Krishna"
    tithi_lord = TITHI_LORDS[(tithi_number - 1) % 8]

    # Percent remaining in current tithi
    tithi_progress = (moon_sun_angle % 12) / 12 * 100
    tithi_remaining = round(100 - tithi_progress, 1)

    # ===================================================================
    # 3. NAKSHATRA (Moon's sidereal asterism)
    # ===================================================================
    nak_name, nak_lord, nak_pada, nak_deg = get_nakshatra(moon_sid)

    # ===================================================================
    # 4. YOGA (Sun-Moon combination)
    # ===================================================================
    sum_angle = (moon_trop + sun_trop) % 360
    yoga_number = int(sum_angle / (13 + 1.0 / 3)) + 1  # 1-27
    if yoga_number > 27:
        yoga_number = 27
    yoga_name = YOGA_NAMES[yoga_number - 1]

    # ===================================================================
    # 5. KARANA (Half-Tithi)
    # ===================================================================
    karana_index = int(moon_sun_angle / 6)  # 0-59
    if karana_index > 59:
        karana_index = 59
    karana_name = _get_karana_name(karana_index)

    # ===================================================================
    # Planetary positions (sidereal, all 9 grahas)
    # ===================================================================
    planetary_positions = {}

    for swe_id, eng_name, sans_name, yaml_key in GRAHA_LIST:
        pos, _ret = swe.calc_ut(jd, swe_id)
        tropical_lon = pos[0]
        sid_lon = (tropical_lon - ayanamsha) % 360
        speed = pos[3]

        rashi_name, rashi_idx, deg = get_rashi(sid_lon)
        p_nak_name, p_nak_lord, p_pada, _ = get_nakshatra(sid_lon)
        retrograde = speed < 0

        planetary_positions[yaml_key] = {
            "rasi": rashi_name,
            "degree": round(deg, 4),
            "nakshatra": p_nak_name,
            "pada": p_pada,
            "retrograde": retrograde,
        }

    # Rahu (Mean Node)
    node_pos, _ = swe.calc_ut(jd, swe.MEAN_NODE)
    rahu_sid = (node_pos[0] - ayanamsha) % 360
    rahu_rashi, _, rahu_deg = get_rashi(rahu_sid)
    rahu_nak, rahu_nak_lord, rahu_pada, _ = get_nakshatra(rahu_sid)

    planetary_positions["rahu"] = {
        "rasi": rahu_rashi,
        "degree": round(rahu_deg, 4),
        "nakshatra": rahu_nak,
        "pada": rahu_pada,
        "retrograde": True,
    }

    # Ketu (180 degrees opposite Rahu)
    ketu_sid = (rahu_sid + 180) % 360
    ketu_rashi, _, ketu_deg = get_rashi(ketu_sid)
    ketu_nak, ketu_nak_lord, ketu_pada, _ = get_nakshatra(ketu_sid)

    planetary_positions["ketu"] = {
        "rasi": ketu_rashi,
        "degree": round(ketu_deg, 4),
        "nakshatra": ketu_nak,
        "pada": ketu_pada,
        "retrograde": True,
    }

    # ===================================================================
    # Assemble output
    # ===================================================================
    output = {
        "panchanga": {
            "date": str(target_date),
            "place": {
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
            },
            "vara": {
                "name": vara_name,
                "english": vara_english,
                "lord": vara_lord,
            },
            "tithi": {
                "number": tithi_number,
                "name": tithi_name,
                "paksha": paksha,
                "lord": tithi_lord,
                "percent_remaining": tithi_remaining,
            },
            "nakshatra": {
                "name": nak_name,
                "lord": nak_lord,
                "pada": nak_pada,
            },
            "yoga": {
                "number": yoga_number,
                "name": yoga_name,
            },
            "karana": {
                "name": karana_name,
            },
        },
        "planetary_positions": planetary_positions,
    }

    # Write to file
    panchanga_dir = os.path.join(WORLD_DATA_DIR, "panchanga")
    os.makedirs(panchanga_dir, exist_ok=True)
    out_file = os.path.join(panchanga_dir, f"{target_date}_panchanga.yaml")

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary
    if args.print_summary:
        out = sys.stderr
        out.write("=" * 60 + "\n")
        out.write(f"  PANCHANGA -- {target_date}\n")
        out.write(f"  Place: lat={lat}, lon={lon}, tz=UTC"
                  f"{'+' if tz >= 0 else ''}{tz}\n")
        out.write("=" * 60 + "\n")

        out.write(f"\n  VARA:      {vara_name} ({vara_english})"
                  f"  -- Lord: {vara_lord}\n")
        out.write(f"  TITHI:     {tithi_name} ({paksha} Paksha,"
                  f" Tithi {tithi_number})"
                  f"  -- Lord: {tithi_lord}"
                  f"  [{tithi_remaining}% remaining]\n")
        out.write(f"  NAKSHATRA: {nak_name} Pada {nak_pada}"
                  f"  -- Lord: {nak_lord}\n")
        out.write(f"  YOGA:      {yoga_name} (#{yoga_number})\n")
        out.write(f"  KARANA:    {karana_name}\n")

        out.write("\n  " + "-" * 56 + "\n")
        out.write(f"  {'Graha':<10} {'Rasi':<14} {'Degree':>7}"
                  f"  {'Nakshatra':<20} {'Pada':>4} {'R':>2}\n")
        out.write("  " + "-" * 56 + "\n")

        graha_order = [
            "surya", "chandra", "mangal", "budha",
            "guru", "shukra", "shani", "rahu", "ketu",
        ]
        for key in graha_order:
            p = planetary_positions[key]
            retro = "R" if p["retrograde"] else ""
            out.write(
                f"  {key.capitalize():10s}  {p['rasi']:14s}"
                f"  {p['degree']:7.2f}  {p['nakshatra']:20s}"
                f"  {p['pada']:>4}  {retro:>2}\n"
            )
        out.write("=" * 60 + "\n")

    # JSON status to stdout
    status = {
        "status": "success",
        "file": out_file,
        "date": str(target_date),
        "vara": vara_english,
        "tithi": f"{tithi_name} ({paksha})",
        "nakshatra": nak_name,
        "yoga": yoga_name,
        "karana": karana_name,
    }
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Country (foundation chart) command
# ---------------------------------------------------------------------------

def parse_timezone_string(tz_str):
    """Parse timezone string like 'UTC+5:30' or 'UTC-5:00' to float offset.

    Examples:
        'UTC+5:30' -> 5.5
        'UTC-5:00' -> -5.0
        'UTC+0'    -> 0.0
        'UTC+9'    -> 9.0
    """
    s = tz_str.strip()
    if s.upper().startswith("UTC"):
        s = s[3:]
    if not s or s == "+0" or s == "-0":
        return 0.0
    # Determine sign
    sign = 1
    if s.startswith("-"):
        sign = -1
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]
    # Split hours and minutes
    if ":" in s:
        parts = s.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
    else:
        hours = int(s)
        minutes = 0
    return sign * (hours + minutes / 60.0)


def cmd_country(args):
    """Compute foundation chart for a country from world_data stub."""
    country_name = args.name.lower().replace(" ", "_")
    chart_path = os.path.join(
        _SCRIPT_DIR, "world_data", country_name, "foundation_chart.yaml"
    )

    if not os.path.exists(chart_path):
        print(json.dumps({
            "status": "error",
            "message": f"Foundation chart not found: {chart_path}",
        }))
        sys.exit(1)

    # Read entity stub
    with open(chart_path, "r") as f:
        stub = yaml.safe_load(f)

    entity = stub["entity"]
    date_str = entity["date"]
    time_str = entity["time"]
    tz_str = entity["timezone"]
    lat = entity["place"]["latitude"]
    lon = entity["place"]["longitude"]
    place_city = entity["place"].get("city", "")

    # Parse date and time
    dob_parts = [int(x) for x in date_str.split("-")]
    tob_parts = [int(x) for x in time_str.split(":")]
    year, month, day = dob_parts
    hour = tob_parts[0]
    minute = tob_parts[1]
    second = tob_parts[2] if len(tob_parts) > 2 else 0

    # Parse timezone
    tz_offset = parse_timezone_string(tz_str)

    # Initialize Swiss Ephemeris with Lahiri ayanamsha
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Julian Day
    jd = calculate_julian_day(year, month, day, hour, minute, second, tz_offset)

    # Ascendant
    asc_sid, ayanamsha = calculate_ascendant(jd, lat, lon)
    asc_rashi, asc_rashi_idx, asc_deg = get_rashi(asc_sid)
    asc_nak, asc_nak_lord, asc_pada, _ = get_nakshatra(asc_sid)

    lagna = {
        "rashi": asc_rashi,
        "rashi_idx": asc_rashi_idx,
        "degree": asc_deg,
        "nakshatra": asc_nak,
        "pada": asc_pada,
    }

    # All planetary positions (use Mean Node by default)
    use_true_node = False
    positions = calculate_all_positions(
        jd, ayanamsha, asc_rashi_idx, use_true_node=use_true_node
    )

    # Vimshottari dasha
    moon_lon = positions["Moon"]["sidereal_lon"]
    foundation_date = date(year, month, day)
    dasha = calculate_vimshottari_dasha(moon_lon, foundation_date)

    # House summary
    house_summary = build_house_summary(asc_rashi_idx, positions)

    # Computed analysis
    computed_analysis = build_computed_analysis(asc_rashi_idx, positions)

    # Build output dict (entity instead of native)
    data = {"entity": entity}

    data["lagna"] = {
        "rasi": lagna["rashi"],
        "degree": round(lagna["degree"], 4),
        "nakshatra": lagna["nakshatra"],
        "pada": lagna["pada"],
    }

    data["chandra"] = {
        "rasi": positions["Moon"]["rashi"],
        "degree": round(positions["Moon"]["degree"], 4),
        "nakshatra": positions["Moon"]["nakshatra"],
        "pada": positions["Moon"]["pada"],
    }

    # Planetary positions
    graha_order = [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]
    data["planetary_positions"] = {}
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

    data["vimshottari_dasha"] = dasha

    # House summary
    data["house_summary"] = {}
    for h in range(1, 13):
        hs = house_summary[h]
        data["house_summary"][f"house_{h}"] = {
            "rasi": hs["rasi"],
            "planets": hs["planets"],
        }

    data["notes"] = (
        f"Ayanamsa: Lahiri ({round(ayanamsha, 6)})\n"
        f"Node type: {'True Node' if use_true_node else 'Mean Node'}\n"
        f"House system: Whole Sign\n"
        f"Computed by medini_calc.py"
    )

    data["computed_analysis"] = computed_analysis

    # Write enriched YAML
    with open(chart_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary if requested
    if args.print_summary:
        print_country_chart_summary(
            entity, lagna, positions, dasha, house_summary,
            computed_analysis, ayanamsha, tz_offset
        )

    # JSON status to stdout
    status = {
        "status": "success",
        "file": chart_path,
        "entity": entity["name"],
        "lagna": lagna["rashi"],
        "moon_sign": positions["Moon"]["rashi"],
    }
    print(json.dumps(status))


def print_country_chart_summary(entity, lagna, positions, dasha,
                                 house_summary, computed_analysis,
                                 ayanamsha, tz_offset):
    """Print human-readable foundation chart summary to stderr."""
    out = sys.stderr
    name = entity["name"]
    date_str = entity["date"]
    time_str = entity["time"]
    tz_str = entity["timezone"]
    place = entity["place"]
    lat = place["latitude"]
    lon = place["longitude"]
    city = place.get("city", "")

    out.write("=" * 70 + "\n")
    out.write(f"  FOUNDATION CHART -- {name.upper()}\n")
    out.write("=" * 70 + "\n")
    out.write(f"  Event: {entity.get('foundation_event', 'Foundation')}\n")
    out.write(f"  Date: {date_str}  Time: {time_str}  TZ: {tz_str}\n")
    out.write(f"  Place: {city}  Lat: {lat}  Lon: {lon}\n")
    out.write(f"  Ayanamsa (Lahiri): {format_dms(ayanamsha)}\n")
    if entity.get("notes"):
        out.write(f"  Notes: {entity['notes']}\n")

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
        planets_str = ", ".join(hs["planets"]) if hs["planets"] else "--"
        out.write(f"  House {h:>2}  {hs['rasi']:<14} {planets_str}\n")

    out.write("\n  " + "-" * 66 + "\n")
    out.write("  VIMSHOTTARI DASHA\n")
    out.write("  " + "-" * 66 + "\n")
    bal = dasha["balance_at_birth"]
    out.write(
        f"  Balance at foundation: {bal['lord']} -- "
        f"{bal['remaining_years']}y {bal['remaining_months']}m "
        f"{bal['remaining_days']}d\n"
    )
    for entry in dasha["sequence"]:
        out.write(
            f"  {entry['lord']:<10} {entry['start']}  to  {entry['end']}\n"
        )

    # Computed analysis summary
    if computed_analysis:
        out.write("\n  " + "-" * 66 + "\n")
        out.write("  COMPUTED ANALYSIS\n")
        out.write("  " + "-" * 66 + "\n")
        fn = computed_analysis.get("functional_nature", {})
        if fn.get("yogakarakas"):
            out.write(f"  Yogakarakas: {', '.join(fn['yogakarakas'])}\n")
        if fn.get("functional_benefics"):
            out.write(
                f"  Functional Benefics: {', '.join(fn['functional_benefics'])}\n"
            )
        if fn.get("functional_malefics"):
            out.write(
                f"  Functional Malefics: {', '.join(fn['functional_malefics'])}\n"
            )
        bd = computed_analysis.get("badhaka", {})
        if bd:
            out.write(
                f"  Badhaka: H{bd.get('badhaka_sthana', '?')} "
                f"{bd.get('badhaka_rasi', '')} "
                f"(lord: {bd.get('badhaka_lord', '?')})\n"
            )
        marakas = computed_analysis.get("marakas", [])
        if marakas:
            if isinstance(marakas[0], dict):
                maraka_strs = [
                    f"{m['planet']} ({m['reason']})" for m in marakas
                ]
            else:
                maraka_strs = [str(m) for m in marakas]
            out.write(f"  Marakas: {', '.join(maraka_strs)}\n")
        yogas = computed_analysis.get("yogas", [])
        if yogas and yogas != "none detected":
            out.write("  Yogas:\n")
            for y in yogas:
                if isinstance(y, dict):
                    strength = y.get("strength", "")
                    notes = y.get("notes", y.get("description", ""))
                    out.write(f"    - {y.get('name', '?')} [{strength}]: "
                              f"{notes}\n")
                else:
                    out.write(f"    - {y}\n")
        strengths = computed_analysis.get("key_strengths", [])
        if strengths:
            out.write("  Key Strengths:\n")
            for s in strengths:
                out.write(f"    + {s}\n")
        vulns = computed_analysis.get("key_vulnerabilities", [])
        if vulns:
            out.write("  Key Vulnerabilities:\n")
            for v in vulns:
                out.write(f"    - {v}\n")

    out.write("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Shared helpers for astronomical event finders
# ---------------------------------------------------------------------------

# Map planet names (lowercase) to Swiss Ephemeris IDs
PLANET_NAME_TO_SWE = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mars": swe.MARS,
    "mercury": swe.MERCURY,
    "jupiter": swe.JUPITER,
    "venus": swe.VENUS,
    "saturn": swe.SATURN,
}

# Reverse: SWE ID to English name
SWE_TO_PLANET_NAME = {v: k.capitalize() for k, v in PLANET_NAME_TO_SWE.items()}

# Rahu / Ketu handled separately (mean node)
PLANET_NAME_TO_SWE["rahu"] = swe.MEAN_NODE
SWE_TO_PLANET_NAME[swe.MEAN_NODE] = "Rahu"


def _sidereal_lon_at_jd(jd, planet_id):
    """Return sidereal longitude of a planet at a given JD."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)
    pos, _ = swe.calc_ut(jd, planet_id)
    return (pos[0] - ayanamsha) % 360


def _ketu_sidereal_lon_at_jd(jd):
    """Return sidereal longitude of Ketu at a given JD."""
    return (_sidereal_lon_at_jd(jd, swe.MEAN_NODE) + 180) % 360


def _angular_distance(lon1, lon2):
    """Return the minimum angular distance between two sidereal longitudes."""
    diff = abs(lon1 - lon2)
    if diff > 180:
        diff = 360 - diff
    return diff


def _position_at_jd(jd, planet_id):
    """Compute sidereal position summary at a JD for output."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)
    pos, _ = swe.calc_ut(jd, planet_id)
    sid_lon = (pos[0] - ayanamsha) % 360
    rashi_name, rashi_idx, deg = get_rashi(sid_lon)
    nak_name, nak_lord, pada, _ = get_nakshatra(sid_lon)
    return {
        "sidereal_lon": sid_lon,
        "sign": rashi_name,
        "degree": round(deg, 4),
        "nakshatra": nak_name,
        "pada": pada,
    }


def _bisect_conjunction_minimum(jd_lo, jd_hi, p1_id, p2_id, tol=1e-6,
                                max_iter=80):
    """Find JD of minimum angular distance using golden-section search."""
    gr = (5 ** 0.5 + 1) / 2  # golden ratio
    a, b = jd_lo, jd_hi
    c = b - (b - a) / gr
    d = a + (b - a) / gr

    for _ in range(max_iter):
        if abs(b - a) < tol:
            break
        fc = _angular_distance(
            _sidereal_lon_at_jd(c, p1_id),
            _sidereal_lon_at_jd(c, p2_id),
        )
        fd = _angular_distance(
            _sidereal_lon_at_jd(d, p1_id),
            _sidereal_lon_at_jd(d, p2_id),
        )
        if fc < fd:
            b = d
        else:
            a = c
        c = b - (b - a) / gr
        d = a + (b - a) / gr

    return (a + b) / 2


def _bisect_speed_zero(jd_lo, jd_hi, planet_id, tol=1e-6, max_iter=80):
    """Bisect to find the exact JD when a planet's speed crosses zero."""
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2
        if (jd_hi - jd_lo) < tol:
            break
        pos, _ = swe.calc_ut(jd_mid, planet_id)
        speed = pos[3]
        pos_lo, _ = swe.calc_ut(jd_lo, planet_id)
        speed_lo = pos_lo[3]
        if (speed_lo > 0 and speed > 0) or (speed_lo < 0 and speed < 0):
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2


def _bisect_sign_change(jd_lo, jd_hi, planet_id, sign_lo, is_ketu,
                         tol=1e-6, max_iter=80):
    """Bisect to find the exact JD when a planet crosses a sign boundary."""
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2
        if (jd_hi - jd_lo) < tol:
            break
        if is_ketu:
            lon = _ketu_sidereal_lon_at_jd(jd_mid)
        else:
            lon = _sidereal_lon_at_jd(jd_mid, planet_id)
        sign_mid = int(lon / 30) % 12

        if sign_mid == sign_lo:
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2


# ---------------------------------------------------------------------------
# Conjunction command
# ---------------------------------------------------------------------------

def cmd_conjunction(args):
    """Find planetary conjunctions within a year.

    Scans day-by-day for angular distance minima between two planets.
    When a local minimum is detected (decreasing then increasing distance),
    golden-section search narrows to the exact JD.  Events with min
    distance < 15 deg are reported.
    """
    planet_names = [p.strip().lower() for p in args.planets.split(",")]
    if len(planet_names) != 2:
        print(json.dumps({"status": "error",
                          "message": "Exactly two planets required (comma-separated)"}))
        return

    p1_name, p2_name = planet_names
    if p1_name not in PLANET_NAME_TO_SWE or p2_name not in PLANET_NAME_TO_SWE:
        print(json.dumps({"status": "error",
                          "message": f"Unknown planet name. Valid: "
                                     f"{list(PLANET_NAME_TO_SWE.keys())}"}))
        return

    p1_id = PLANET_NAME_TO_SWE[p1_name]
    p2_id = PLANET_NAME_TO_SWE[p2_name]
    year = args.year

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year + 1, 1, 1, 0.0)

    events = []
    jd = jd_start
    prev_dist = None
    prev_prev_dist = None

    while jd <= jd_end:
        lon1 = _sidereal_lon_at_jd(jd, p1_id)
        lon2 = _sidereal_lon_at_jd(jd, p2_id)
        dist = _angular_distance(lon1, lon2)

        if prev_dist is not None and prev_prev_dist is not None:
            if prev_prev_dist > prev_dist and dist > prev_dist:
                # Local minimum around jd - 1.0
                jd_min = _bisect_conjunction_minimum(
                    jd - 2.0, jd, p1_id, p2_id)
                min_dist = _angular_distance(
                    _sidereal_lon_at_jd(jd_min, p1_id),
                    _sidereal_lon_at_jd(jd_min, p2_id),
                )

                if min_dist < 15.0:
                    dt = jd_to_utc_datetime(jd_min)
                    pos1 = _position_at_jd(jd_min, p1_id)
                    pos2 = _position_at_jd(jd_min, p2_id)
                    events.append({
                        "date_utc": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                        "min_distance_deg": round(min_dist, 4),
                        "sign": pos1["sign"],
                        "planet1_degree": pos1["degree"],
                        "planet2_degree": pos2["degree"],
                        "nakshatra": pos1["nakshatra"],
                    })

        prev_prev_dist = prev_dist
        prev_dist = dist
        jd += 1.0

    output = {
        "conjunction": {
            "planet1": p1_name.capitalize(),
            "planet2": p2_name.capitalize(),
            "year": year,
            "events": events,
        }
    }

    # Write YAML
    conj_dir = os.path.join(WORLD_DATA_DIR, "conjunctions")
    os.makedirs(conj_dir, exist_ok=True)
    out_file = os.path.join(conj_dir,
                            f"{year}_{p1_name}_{p2_name}_conjunction.yaml")
    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    if args.print_summary:
        print("=" * 70, file=sys.stderr)
        print(f"  CONJUNCTIONS -- {p1_name.capitalize()} & "
              f"{p2_name.capitalize()} in {year}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        if not events:
            print("  No conjunctions found (< 15 deg).", file=sys.stderr)
        for ev in events:
            print(f"  {ev['date_utc']}  dist={ev['min_distance_deg']:.4f} deg  "
                  f"{ev['sign']}  "
                  f"P1={ev['planet1_degree']:.2f} deg  "
                  f"P2={ev['planet2_degree']:.2f} deg  "
                  f"{ev['nakshatra']}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)

    status = {"status": "success", "file": out_file,
              "events_count": len(events)}
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Wars (Graha Yuddha) command
# ---------------------------------------------------------------------------

def cmd_wars(args):
    """Find planetary wars (graha yuddha) in a date range.

    A planetary war occurs when two visible planets (Mars, Mercury, Jupiter,
    Venus, Saturn) come within 1 degree of each other.  The winner is the
    planet with higher latitude (more northerly).
    """
    from itertools import combinations

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end, "%Y-%m-%d").date()

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    war_planets = [
        ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS),
        ("Saturn", swe.SATURN),
    ]

    jd_start = swe.julday(start_date.year, start_date.month,
                           start_date.day, 0.0)
    jd_end = swe.julday(end_date.year, end_date.month,
                         end_date.day, 0.0)

    events = []

    for (name_a, id_a), (name_b, id_b) in combinations(war_planets, 2):
        jd = jd_start
        in_war = False
        war_min_dist = 999
        war_start_jd = None

        while jd <= jd_end:
            lon_a = _sidereal_lon_at_jd(jd, id_a)
            lon_b = _sidereal_lon_at_jd(jd, id_b)
            dist = _angular_distance(lon_a, lon_b)

            if dist < 1.0:
                if not in_war:
                    in_war = True
                    war_start_jd = jd
                    war_min_dist = dist
                if dist < war_min_dist:
                    war_min_dist = dist
            else:
                if in_war:
                    jd_min = _bisect_conjunction_minimum(
                        max(war_start_jd - 1, jd_start),
                        min(jd, jd_end + 1),
                        id_a, id_b)
                    refined_dist = _angular_distance(
                        _sidereal_lon_at_jd(jd_min, id_a),
                        _sidereal_lon_at_jd(jd_min, id_b),
                    )

                    # Winner = planet with higher latitude (more northerly)
                    pos_a, _ = swe.calc_ut(jd_min, id_a)
                    pos_b, _ = swe.calc_ut(jd_min, id_b)
                    lat_a = pos_a[1]
                    lat_b = pos_b[1]
                    winner = name_a if lat_a > lat_b else name_b
                    loser = name_b if winner == name_a else name_a

                    dt_min = jd_to_utc_datetime(jd_min)
                    p_a_pos = _position_at_jd(jd_min, id_a)
                    p_b_pos = _position_at_jd(jd_min, id_b)

                    events.append({
                        "date_utc": dt_min.strftime("%Y-%m-%dT%H:%M:%S"),
                        "planet1": name_a,
                        "planet2": name_b,
                        "min_distance_deg": round(refined_dist, 4),
                        "sign": p_a_pos["sign"],
                        "winner": winner,
                        "loser": loser,
                        "planet1_degree": p_a_pos["degree"],
                        "planet2_degree": p_b_pos["degree"],
                    })
                    in_war = False
                    war_min_dist = 999

            jd += 1.0

        # Handle war still active at end of range
        if in_war:
            jd_min = _bisect_conjunction_minimum(
                max(war_start_jd - 1, jd_start),
                jd_end, id_a, id_b)
            refined_dist = _angular_distance(
                _sidereal_lon_at_jd(jd_min, id_a),
                _sidereal_lon_at_jd(jd_min, id_b),
            )
            pos_a, _ = swe.calc_ut(jd_min, id_a)
            pos_b, _ = swe.calc_ut(jd_min, id_b)
            winner = name_a if pos_a[1] > pos_b[1] else name_b
            loser = name_b if winner == name_a else name_a
            dt_min = jd_to_utc_datetime(jd_min)
            p_a_pos = _position_at_jd(jd_min, id_a)
            p_b_pos = _position_at_jd(jd_min, id_b)
            events.append({
                "date_utc": dt_min.strftime("%Y-%m-%dT%H:%M:%S"),
                "planet1": name_a,
                "planet2": name_b,
                "min_distance_deg": round(refined_dist, 4),
                "sign": p_a_pos["sign"],
                "winner": winner,
                "loser": loser,
                "planet1_degree": p_a_pos["degree"],
                "planet2_degree": p_b_pos["degree"],
            })

    events.sort(key=lambda e: e["date_utc"])

    output = {
        "wars": {
            "start": str(start_date),
            "end": str(end_date),
            "events": events,
        }
    }

    wars_dir = os.path.join(WORLD_DATA_DIR, "wars")
    os.makedirs(wars_dir, exist_ok=True)
    out_file = os.path.join(wars_dir,
                            f"{start_date}_{end_date}_wars.yaml")
    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    if args.print_summary:
        print("=" * 70, file=sys.stderr)
        print(f"  GRAHA YUDDHA (Planetary Wars) -- "
              f"{start_date} to {end_date}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        if not events:
            print("  No planetary wars found.", file=sys.stderr)
        for ev in events:
            print(f"  {ev['date_utc']}  {ev['planet1']} vs {ev['planet2']}  "
                  f"dist={ev['min_distance_deg']:.4f} deg  "
                  f"{ev['sign']}  Winner: {ev['winner']}",
                  file=sys.stderr)
        print("=" * 70, file=sys.stderr)

    status = {"status": "success", "file": out_file,
              "events_count": len(events)}
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Retrogrades command
# ---------------------------------------------------------------------------

def cmd_retrogrades(args):
    """Find retrograde stations (Rx and D) for planets in a year.

    Tracks daily speed of Mercury, Venus, Mars, Jupiter, Saturn.
    When speed crosses zero: positive->negative = Rx station,
    negative->positive = D (direct) station.
    Bisection narrows to exact JD.
    """
    year = args.year
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    retro_planets = [
        ("Mercury", swe.MERCURY),
        ("Venus", swe.VENUS),
        ("Mars", swe.MARS),
        ("Jupiter", swe.JUPITER),
        ("Saturn", swe.SATURN),
    ]

    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year + 1, 1, 1, 0.0)

    events = []

    for name, planet_id in retro_planets:
        jd = jd_start
        pos_prev, _ = swe.calc_ut(jd, planet_id)
        speed_prev = pos_prev[3]
        jd += 1.0

        while jd <= jd_end:
            pos_cur, _ = swe.calc_ut(jd, planet_id)
            speed_cur = pos_cur[3]

            if speed_prev > 0 and speed_cur < 0:
                # Retrograde station (Rx)
                jd_station = _bisect_speed_zero(jd - 1.0, jd, planet_id)
                station_pos = _position_at_jd(jd_station, planet_id)
                dt = jd_to_utc_datetime(jd_station)
                events.append({
                    "planet": name,
                    "station": "Rx",
                    "date_utc": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "sign": station_pos["sign"],
                    "degree": station_pos["degree"],
                    "nakshatra": station_pos["nakshatra"],
                })
            elif speed_prev < 0 and speed_cur > 0:
                # Direct station (D)
                jd_station = _bisect_speed_zero(jd - 1.0, jd, planet_id)
                station_pos = _position_at_jd(jd_station, planet_id)
                dt = jd_to_utc_datetime(jd_station)
                events.append({
                    "planet": name,
                    "station": "D",
                    "date_utc": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "sign": station_pos["sign"],
                    "degree": station_pos["degree"],
                    "nakshatra": station_pos["nakshatra"],
                })

            speed_prev = speed_cur
            jd += 1.0

    events.sort(key=lambda e: e["date_utc"])

    output = {
        "retrogrades": {
            "year": year,
            "events": events,
        }
    }

    retro_dir = os.path.join(WORLD_DATA_DIR, "retrogrades")
    os.makedirs(retro_dir, exist_ok=True)
    out_file = os.path.join(retro_dir, f"{year}_retrogrades.yaml")
    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    if args.print_summary:
        print("=" * 70, file=sys.stderr)
        print(f"  RETROGRADE STATIONS -- {year}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        if not events:
            print("  No retrograde stations found.", file=sys.stderr)
        for ev in events:
            print(f"  {ev['date_utc']}  {ev['planet']:8s}  "
                  f"{ev['station']:2s}  {ev['sign']:14s}  "
                  f"{ev['degree']:7.2f} deg  {ev['nakshatra']}",
                  file=sys.stderr)
        print("=" * 70, file=sys.stderr)

    status = {"status": "success", "file": out_file,
              "events_count": len(events)}
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Sign-changes command
# ---------------------------------------------------------------------------

def cmd_sign_changes(args):
    """Find when slow planets change sidereal signs in a year.

    Tracks Saturn, Jupiter, Rahu, Ketu, Mars day-by-day.
    When int(lon/30) changes, bisection narrows to exact JD.
    Retrograde planets may re-enter old signs; all changes are tracked.
    """
    year = args.year
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sign_change_planets = [
        ("Saturn", swe.SATURN, False),
        ("Jupiter", swe.JUPITER, False),
        ("Rahu", swe.MEAN_NODE, False),
        ("Ketu", None, True),
        ("Mars", swe.MARS, False),
    ]

    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year + 1, 1, 1, 0.0)

    events = []

    for name, planet_id, is_ketu in sign_change_planets:
        jd = jd_start

        if is_ketu:
            lon_prev = _ketu_sidereal_lon_at_jd(jd)
        else:
            lon_prev = _sidereal_lon_at_jd(jd, planet_id)
        sign_prev = int(lon_prev / 30) % 12
        jd += 1.0

        while jd <= jd_end:
            if is_ketu:
                lon_cur = _ketu_sidereal_lon_at_jd(jd)
            else:
                lon_cur = _sidereal_lon_at_jd(jd, planet_id)
            sign_cur = int(lon_cur / 30) % 12

            if sign_cur != sign_prev:
                jd_cross = _bisect_sign_change(
                    jd - 1.0, jd, planet_id, sign_prev, is_ketu)
                dt = jd_to_utc_datetime(jd_cross)
                events.append({
                    "planet": name,
                    "date_utc": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "from_sign": RASHI_NAMES[sign_prev],
                    "to_sign": RASHI_NAMES[sign_cur],
                })

            sign_prev = sign_cur
            jd += 1.0

    events.sort(key=lambda e: e["date_utc"])

    output = {
        "sign_changes": {
            "year": year,
            "events": events,
        }
    }

    sc_dir = os.path.join(WORLD_DATA_DIR, "sign_changes")
    os.makedirs(sc_dir, exist_ok=True)
    out_file = os.path.join(sc_dir, f"{year}_sign_changes.yaml")
    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    if args.print_summary:
        print("=" * 70, file=sys.stderr)
        print(f"  SIGN CHANGES (Slow Planets) -- {year}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        if not events:
            print("  No sign changes found.", file=sys.stderr)
        for ev in events:
            print(f"  {ev['date_utc']}  {ev['planet']:8s}  "
                  f"{ev['from_sign']:14s}  -->  {ev['to_sign']}",
                  file=sys.stderr)
        print("=" * 70, file=sys.stderr)

    status = {"status": "success", "file": out_file,
              "events_count": len(events)}
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Ashtakavarga command — BAV and SAV computation
# ---------------------------------------------------------------------------

# Bhinnashtakavarga (BAV) tables: benefic houses from each reference
# Source: Parasara (BPHS), Chapter 12 of reference book
# For each planet P, BAV_TABLES[P] = dict mapping each reference (planet or
# "lagna") to the list of house numbers (1-12) where P receives a bindu.
# Keys use lowercase planet names matching yaml_key convention.

BAV_TABLES = {
    "surya": {
        "surya":   [1, 2, 4, 7, 8, 9, 10, 11],
        "chandra": [3, 6, 10, 11],
        "mangal":  [1, 2, 4, 7, 8, 9, 10, 11],
        "budha":   [3, 5, 6, 9, 10, 11, 12],
        "guru":    [5, 6, 9, 11],
        "shukra":  [6, 7, 12],
        "shani":   [1, 2, 4, 7, 8, 9, 10, 11],
        "lagna":   [3, 4, 6, 10, 11, 12],
    },
    "chandra": {
        "surya":   [3, 6, 7, 8, 10, 11],
        "chandra": [1, 3, 6, 7, 9, 10, 11],
        "mangal":  [2, 3, 5, 6, 10, 11],
        "budha":   [1, 3, 4, 5, 7, 8, 10, 11],
        "guru":    [1, 2, 4, 7, 8, 10, 11],
        "shukra":  [3, 4, 5, 7, 9, 10, 11],
        "shani":   [3, 5, 6, 11],
        "lagna":   [3, 6, 10, 11],
    },
    "mangal": {
        "surya":   [3, 5, 6, 10, 11],
        "chandra": [3, 6, 11],
        "mangal":  [1, 2, 4, 7, 8, 10, 11],
        "budha":   [3, 5, 6, 11],
        "guru":    [6, 10, 11, 12],
        "shukra":  [6, 8, 11, 12],
        "shani":   [1, 4, 7, 8, 9, 10, 11],
        "lagna":   [1, 3, 6, 10, 11],
    },
    "budha": {
        "surya":   [5, 6, 9, 11, 12],
        "chandra": [2, 4, 8, 10, 11],
        "mangal":  [1, 2, 4, 7, 8, 9, 10, 11],
        "budha":   [1, 3, 5, 6, 9, 10, 11, 12],
        "guru":    [6, 8, 11, 12],
        "shukra":  [1, 2, 3, 4, 5, 8, 9, 11],
        "shani":   [1, 2, 4, 7, 8, 9, 10, 11],
        "lagna":   [1, 2, 4, 6, 8, 10, 11],
    },
    "guru": {
        "surya":   [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "chandra": [2, 5, 7, 9, 11],
        "mangal":  [1, 2, 4, 7, 8, 10, 11],
        "budha":   [1, 2, 4, 5, 6, 9, 10, 11],
        "guru":    [1, 2, 3, 7, 8, 11],
        "shukra":  [2, 5, 6, 9, 10, 11],
        "shani":   [3, 5, 6, 12],
        "lagna":   [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "shukra": {
        "surya":   [8, 11, 12],
        "chandra": [1, 2, 3, 4, 8, 9, 11, 12],
        "mangal":  [3, 4, 5, 6, 8, 9, 11, 12],
        "budha":   [3, 5, 6, 9, 11],
        "guru":    [5, 8, 9, 10, 11],
        "shukra":  [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "shani":   [3, 4, 5, 8, 9, 10, 11],
        "lagna":   [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "shani": {
        "surya":   [1, 2, 4, 7, 8, 10, 11],
        "chandra": [3, 6, 10, 11],
        "mangal":  [3, 5, 6, 10, 11, 12],
        "budha":   [6, 8, 9, 10, 11, 12],
        "guru":    [5, 6, 9, 10, 11],
        "shukra":  [6, 11, 12],
        "shani":   [3, 5, 6, 11],
        "lagna":   [1, 3, 4, 6, 10, 11],
    },
}

# The 7 planets whose BAV contributes to SAV (lagna BAV excluded from SAV)
BAV_PLANETS = ["surya", "chandra", "mangal", "budha", "guru", "shukra", "shani"]

# The 8 contributing references for each BAV
BAV_REFERENCES = ["surya", "chandra", "mangal", "budha", "guru", "shukra",
                   "shani", "lagna"]


def _get_rashi_index_from_name(rashi_name):
    """Return the 0-based rashi index from a rashi name."""
    for idx, name in enumerate(RASHI_NAMES):
        if name == rashi_name:
            return idx
    raise ValueError(f"Unknown rashi name: {rashi_name}")


def compute_bav(planet_rashi_indices, lagna_rashi_idx):
    """Compute Bhinnashtakavarga for all 7 planets.

    Args:
        planet_rashi_indices: dict mapping yaml_key (surya, chandra, etc.)
            to 0-based rashi index (0=Mesham...11=Meenam)
        lagna_rashi_idx: 0-based rashi index of lagna

    Returns:
        dict: planet_key -> list of 12 integers (bindus per rashi, index 0=Mesham)
    """
    bav = {}

    for planet in BAV_PLANETS:
        # Initialize 12 rashi slots to 0
        bindus = [0] * 12

        table = BAV_TABLES[planet]

        for ref in BAV_REFERENCES:
            # Get rashi index of the reference
            if ref == "lagna":
                ref_rashi_idx = lagna_rashi_idx
            else:
                ref_rashi_idx = planet_rashi_indices[ref]

            # Get benefic house numbers from this reference
            benefic_houses = table[ref]

            for house_num in benefic_houses:
                # House N from reference means rashi at (ref_rashi + N - 1) % 12
                target_rashi = (ref_rashi_idx + house_num - 1) % 12
                bindus[target_rashi] += 1

        bav[planet] = bindus

    return bav


def compute_sav(bav):
    """Compute Sarvashtakavarga from BAV.

    SAV = sum of all 7 planet BAVs per rashi (lagna excluded).

    Args:
        bav: dict from compute_bav()

    Returns:
        list of 12 integers (SAV per rashi)
    """
    sav = [0] * 12
    for planet in BAV_PLANETS:
        for i in range(12):
            sav[i] += bav[planet][i]
    return sav


def cmd_ashtakavarga(args):
    """Compute BAV and SAV for a country's foundation chart."""
    country_name = args.country.lower().replace(" ", "_")
    chart_path = os.path.join(
        _SCRIPT_DIR, "world_data", country_name, "foundation_chart.yaml"
    )

    if not os.path.exists(chart_path):
        print(json.dumps({
            "status": "error",
            "message": f"Foundation chart not found: {chart_path}",
        }))
        sys.exit(1)

    # Read foundation chart
    with open(chart_path, "r") as f:
        chart = yaml.safe_load(f)

    # Extract rashi indices for the 7 planets
    planet_rashi_indices = {}
    for yaml_key in BAV_PLANETS:
        rashi_name = chart["planetary_positions"][yaml_key]["rasi"]
        planet_rashi_indices[yaml_key] = _get_rashi_index_from_name(rashi_name)

    # Lagna rashi index
    lagna_rashi_name = chart["lagna"]["rasi"]
    lagna_rashi_idx = _get_rashi_index_from_name(lagna_rashi_name)

    # Compute BAV and SAV
    bav = compute_bav(planet_rashi_indices, lagna_rashi_idx)
    sav = compute_sav(bav)
    total_sav = sum(sav)

    # Build output YAML
    bav_output = {}
    for planet in BAV_PLANETS:
        bav_output[planet] = {
            RASHI_NAMES[i]: bav[planet][i] for i in range(12)
        }

    sav_output = {RASHI_NAMES[i]: sav[i] for i in range(12)}

    output = {
        "ashtakavarga": {
            "country": chart.get("entity", {}).get("name", country_name),
            "lagna": lagna_rashi_name,
            "bav": bav_output,
            "sav": sav_output,
            "total_sav": total_sav,
        }
    }

    # Write to file
    country_dir = os.path.join(WORLD_DATA_DIR, country_name)
    os.makedirs(country_dir, exist_ok=True)
    out_file = os.path.join(country_dir, "ashtakavarga.yaml")

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary
    if args.print_summary:
        out = sys.stderr
        out.write("=" * 70 + "\n")
        out.write(f"  ASHTAKAVARGA -- {output['ashtakavarga']['country']}\n")
        out.write(f"  Lagna: {lagna_rashi_name}\n")
        out.write("=" * 70 + "\n")

        # Planet positions
        out.write("\n  Foundation chart planet positions (rashi):\n")
        for pk in BAV_PLANETS:
            rn = chart["planetary_positions"][pk]["rasi"]
            out.write(f"    {pk.capitalize():10s}  {rn}\n")
        out.write(f"    {'Lagna':10s}  {lagna_rashi_name}\n")

        # BAV table
        out.write("\n  BHINNASHTAKAVARGA (BAV):\n")
        out.write("  " + "-" * 66 + "\n")
        # Header
        header = f"  {'Planet':10s}"
        for rn in RASHI_NAMES:
            header += f"  {rn[:4]:>4s}"
        header += "  Total"
        out.write(header + "\n")
        out.write("  " + "-" * 66 + "\n")

        for planet in BAV_PLANETS:
            row = f"  {planet.capitalize():10s}"
            planet_total = 0
            for i in range(12):
                row += f"  {bav[planet][i]:4d}"
                planet_total += bav[planet][i]
            row += f"  {planet_total:5d}"
            out.write(row + "\n")

        out.write("  " + "-" * 66 + "\n")
        sav_row = f"  {'SAV':10s}"
        for i in range(12):
            sav_row += f"  {sav[i]:4d}"
        sav_row += f"  {total_sav:5d}"
        out.write(sav_row + "\n")
        out.write("  " + "-" * 66 + "\n")

        # SAV interpretation
        out.write("\n  SAV INTERPRETATION:\n")
        for i in range(12):
            val = sav[i]
            if val >= 30:
                label = "STRONG"
            elif val >= 25:
                label = "Average"
            else:
                label = "WEAK"
            house_num = ((i - lagna_rashi_idx) % 12) + 1
            out.write(f"    {RASHI_NAMES[i]:14s} (H{house_num:2d}): "
                      f"{val:2d} rekhas  [{label}]\n")

        out.write("=" * 70 + "\n")

    # JSON status
    status = {
        "status": "success",
        "file": out_file,
        "country": country_name,
        "total_sav": total_sav,
    }
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# SBC (Sarvatobhadra Chakra) command
# ---------------------------------------------------------------------------

# The 9x9 SBC grid maps nakshatras, vowels, tithis, and varas to cells.
# For vedha computation, the key relationship is between nakshatras.
# Each nakshatra occupies a specific cell in the grid; planets transiting
# a nakshatra create vedha on nakshatras directly opposite (front aspect).

# SBC Grid layout (standard): the 28 nakshatras (27 + Abhijit) occupy the
# outer ring of the 9x9 grid. The vedha (front aspect) pairs are the
# nakshatras directly across from each other in the grid.

# SBC front-aspect vedha pairs: each nakshatra creates vedha on specific
# other nakshatras across the grid. These pairs are derived from the
# standard SBC grid arrangement.

# Standard 9x9 SBC grid positions (row, col) for each nakshatra
# The grid is numbered 0-8 for rows (top to bottom) and 0-8 for cols.
# Nakshatras are placed around the perimeter of the grid.

# Top row (row 0), cols 1-7 (left to right):
#   Krittika, Rohini, Mrigashira, Ardra, Punarvasu, Pushya, Ashlesha
# Right col (col 8), rows 1-7 (top to bottom):
#   Magha, P.Phalguni, U.Phalguni, Hasta, Chitra, Swati, Vishakha
# Bottom row (row 8), cols 7-1 (right to left):
#   Anuradha, Jyeshtha, Mula, P.Ashadha, U.Ashadha, Abhijit, Shravana
# Left col (col 0), rows 7-1 (bottom to top):
#   Dhanishta, Shatabhisha, P.Bhadrapada, U.Bhadrapada, Revati, Ashwini, Bharani

# Nakshatra index to name (0-based, standard 27)
SBC_NAKSHATRA_NAMES = [n[0] for n in NAKSHATRAS]  # 27 nakshatras

# The SBC grid positions for each nakshatra (including Abhijit at index 27)
# Using (row, col) coordinates in the 9x9 grid
SBC_GRID_POSITIONS = {
    "Krittika":            (0, 1),
    "Rohini":              (0, 2),
    "Mrigashira":          (0, 3),
    "Ardra":               (0, 4),
    "Punarvasu":           (0, 5),
    "Pushya":              (0, 6),
    "Ashlesha":            (0, 7),
    "Magha":               (1, 8),
    "Purva Phalguni":      (2, 8),
    "Uttara Phalguni":     (3, 8),
    "Hasta":               (4, 8),
    "Chitra":              (5, 8),
    "Swati":               (6, 8),
    "Vishakha":            (7, 8),
    "Anuradha":            (8, 7),
    "Jyeshtha":            (8, 6),
    "Mula":                (8, 5),
    "Purva Ashadha":       (8, 4),
    "Uttara Ashadha":      (8, 3),
    "Abhijit":             (8, 2),
    "Shravana":            (8, 1),
    "Dhanishta":           (7, 0),
    "Shatabhisha":         (6, 0),
    "Purva Bhadrapada":    (5, 0),
    "Uttara Bhadrapada":   (4, 0),
    "Revati":              (3, 0),
    "Ashwini":             (2, 0),
    "Bharani":             (1, 0),
}

# Build reverse lookup: (row, col) -> nakshatra name
SBC_POS_TO_NAK = {v: k for k, v in SBC_GRID_POSITIONS.items()}


def _sbc_front_vedha_targets(nak_name):
    """Compute the front-aspect vedha targets for a nakshatra in the SBC grid.

    In the SBC, front aspect means directly opposite across the grid center.
    For nakshatras on:
    - Top row (row=0): vedha goes to bottom row (row=8), same col
    - Bottom row (row=8): vedha goes to top row (row=0), same col
    - Left col (col=0): vedha goes to right col (col=8), same row
    - Right col (col=8): vedha goes to left col (col=0), same row
    - Corner positions: vedha goes diagonally opposite
    """
    if nak_name not in SBC_GRID_POSITIONS:
        return []

    row, col = SBC_GRID_POSITIONS[nak_name]
    targets = []

    # Determine which edge this nakshatra is on and compute opposite
    if row == 0 and 1 <= col <= 7:
        # Top row -> opposite is bottom row, same col
        opp = (8, col)
        if opp in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[opp])
    elif row == 8 and 1 <= col <= 7:
        # Bottom row -> opposite is top row, same col
        opp = (0, col)
        if opp in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[opp])
    elif col == 0 and 1 <= row <= 7:
        # Left col -> opposite is right col, same row
        opp = (row, 8)
        if opp in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[opp])
    elif col == 8 and 1 <= row <= 7:
        # Right col -> opposite is left col, same row
        opp = (row, 0)
        if opp in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[opp])

    # Corner nakshatras: also vedha diagonally
    # (0,1) <-> (8,7), (0,7) <-> (8,1), (1,0) <-> (7,8), (7,0) <-> (1,8)
    # These are already handled above. Corners of the grid (0,0), (0,8),
    # (8,0), (8,8) are occupied by varas/tithis, not nakshatras.

    return targets


def _sbc_left_vedha_targets(nak_name):
    """Compute left-aspect vedha targets (90 degrees counter-clockwise).

    From top row -> left col (at complementary position)
    From right col -> top row
    From bottom row -> right col
    From left col -> bottom row
    """
    if nak_name not in SBC_GRID_POSITIONS:
        return []

    row, col = SBC_GRID_POSITIONS[nak_name]
    targets = []

    if row == 0 and 1 <= col <= 7:
        # Top row -> left col: target is (9 - col, 0)
        opp_row = 9 - col
        if 1 <= opp_row <= 7 and (opp_row, 0) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(opp_row, 0)])
    elif col == 8 and 1 <= row <= 7:
        # Right col -> top row: target is (0, 9 - row)
        opp_col = 9 - row
        if 1 <= opp_col <= 7 and (0, opp_col) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(0, opp_col)])
    elif row == 8 and 1 <= col <= 7:
        # Bottom row -> right col: target is (9 - col, 8)
        opp_row = 9 - col
        if 1 <= opp_row <= 7 and (opp_row, 8) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(opp_row, 8)])
    elif col == 0 and 1 <= row <= 7:
        # Left col -> bottom row: target is (8, 9 - row)
        opp_col = 9 - row
        if 1 <= opp_col <= 7 and (8, opp_col) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(8, opp_col)])

    return targets


def _sbc_right_vedha_targets(nak_name):
    """Compute right-aspect vedha targets (90 degrees clockwise).

    From top row -> right col
    From right col -> bottom row
    From bottom row -> left col
    From left col -> top row
    """
    if nak_name not in SBC_GRID_POSITIONS:
        return []

    row, col = SBC_GRID_POSITIONS[nak_name]
    targets = []

    if row == 0 and 1 <= col <= 7:
        # Top row -> right col: target is (col, 8)
        if 1 <= col <= 7 and (col, 8) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(col, 8)])
    elif col == 8 and 1 <= row <= 7:
        # Right col -> bottom row: target is (8, row)
        if 1 <= row <= 7 and (8, row) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(8, row)])
    elif row == 8 and 1 <= col <= 7:
        # Bottom row -> left col: target is (col, 0)
        if 1 <= col <= 7 and (col, 0) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(col, 0)])
    elif col == 0 and 1 <= row <= 7:
        # Left col -> top row: target is (0, row)
        if 1 <= row <= 7 and (0, row) in SBC_POS_TO_NAK:
            targets.append(SBC_POS_TO_NAK[(0, row)])

    return targets


def compute_sbc_vedha(transiting_planets):
    """Compute SBC vedha from transiting planet nakshatras.

    Args:
        transiting_planets: list of dicts with 'planet' and 'nakshatra' keys

    Returns:
        dict mapping each of the 27 nakshatras to a list of vedha entries
        (planet, aspect_type)
    """
    # Initialize vedha for all 27 standard nakshatras
    vedha = {nak_name: [] for nak_name in SBC_NAKSHATRA_NAMES}

    for tp in transiting_planets:
        planet = tp["planet"]
        nak = tp["nakshatra"]

        # Front aspect vedha
        front_targets = _sbc_front_vedha_targets(nak)
        for target in front_targets:
            if target in vedha and target != "Abhijit":
                vedha[target].append({"planet": planet, "aspect": "front"})

        # Left aspect vedha
        left_targets = _sbc_left_vedha_targets(nak)
        for target in left_targets:
            if target in vedha and target != "Abhijit":
                vedha[target].append({"planet": planet, "aspect": "left"})

        # Right aspect vedha
        right_targets = _sbc_right_vedha_targets(nak)
        for target in right_targets:
            if target in vedha and target != "Abhijit":
                vedha[target].append({"planet": planet, "aspect": "right"})

    return vedha


def cmd_sbc(args):
    """Compute Sarvatobhadra Chakra vedha for transiting planets on a date."""
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    # Compute planetary positions at 00:00 UTC
    jd = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    # Compute sidereal positions for all 9 grahas
    transiting_planets = []

    for swe_id, eng_name, sans_name, yaml_key in GRAHA_LIST:
        pos, _ret = swe.calc_ut(jd, swe_id)
        sid_lon = (pos[0] - ayanamsha) % 360
        nak_name, nak_lord, pada, _ = get_nakshatra(sid_lon)
        rashi_name, _, deg = get_rashi(sid_lon)
        speed = pos[3]

        transiting_planets.append({
            "planet": eng_name,
            "nakshatra": nak_name,
            "rasi": rashi_name,
            "degree": round(deg, 4),
            "retrograde": speed < 0,
        })

    # Rahu (Mean Node)
    node_pos, _ = swe.calc_ut(jd, swe.MEAN_NODE)
    rahu_sid = (node_pos[0] - ayanamsha) % 360
    rahu_nak, _, rahu_pada, _ = get_nakshatra(rahu_sid)
    rahu_rashi, _, rahu_deg = get_rashi(rahu_sid)

    transiting_planets.append({
        "planet": "Rahu",
        "nakshatra": rahu_nak,
        "rasi": rahu_rashi,
        "degree": round(rahu_deg, 4),
        "retrograde": True,
    })

    # Ketu
    ketu_sid = (rahu_sid + 180) % 360
    ketu_nak, _, ketu_pada, _ = get_nakshatra(ketu_sid)
    ketu_rashi, _, ketu_deg = get_rashi(ketu_sid)

    transiting_planets.append({
        "planet": "Ketu",
        "nakshatra": ketu_nak,
        "rasi": ketu_rashi,
        "degree": round(ketu_deg, 4),
        "retrograde": True,
    })

    # Compute vedha
    vedha = compute_sbc_vedha(transiting_planets)

    # Count summary
    under_vedha = sum(1 for nak in SBC_NAKSHATRA_NAMES if vedha[nak])
    free_count = 27 - under_vedha

    # Build output
    vedha_list = []
    for nak_name in SBC_NAKSHATRA_NAMES:
        vedha_list.append({
            "nakshatra": nak_name,
            "vedha_from": vedha[nak_name] if vedha[nak_name] else [],
        })

    transit_list = []
    for tp in transiting_planets:
        entry = {"planet": tp["planet"], "nakshatra": tp["nakshatra"]}
        if tp["retrograde"]:
            entry["retrograde"] = True
        transit_list.append(entry)

    output = {
        "sbc": {
            "date": str(target_date),
            "transiting_planets": transit_list,
            "vedha": vedha_list,
            "summary": {
                "nakshatras_under_vedha": under_vedha,
                "nakshatras_free": free_count,
            },
        }
    }

    # Write to file
    sbc_dir = os.path.join(WORLD_DATA_DIR, "sbc")
    os.makedirs(sbc_dir, exist_ok=True)
    out_file = os.path.join(sbc_dir, f"{target_date}_sbc.yaml")

    with open(out_file, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True)

    # Print human-readable summary
    if args.print_summary:
        out = sys.stderr
        out.write("=" * 70 + "\n")
        out.write(f"  SARVATOBHADRA CHAKRA -- {target_date}\n")
        out.write("=" * 70 + "\n")

        out.write("\n  TRANSITING PLANETS:\n")
        out.write("  " + "-" * 56 + "\n")
        for tp in transiting_planets:
            retro = " (R)" if tp["retrograde"] else ""
            out.write(f"    {tp['planet']:10s}  {tp['rasi']:14s}"
                      f"  {tp['degree']:7.2f}°  {tp['nakshatra']}{retro}\n")

        out.write("\n  VEDHA ANALYSIS:\n")
        out.write("  " + "-" * 56 + "\n")
        for nak_name in SBC_NAKSHATRA_NAMES:
            v = vedha[nak_name]
            if v:
                sources = ", ".join(
                    f"{e['planet']}({e['aspect']})" for e in v
                )
                out.write(f"    {nak_name:24s}  VEDHA from: {sources}\n")
            else:
                out.write(f"    {nak_name:24s}  free\n")

        out.write("\n  " + "-" * 56 + "\n")
        out.write(f"  Nakshatras under vedha: {under_vedha}\n")
        out.write(f"  Nakshatras free:        {free_count}\n")
        out.write("=" * 70 + "\n")

    # JSON status
    status = {
        "status": "success",
        "file": out_file,
        "date": str(target_date),
        "nakshatras_under_vedha": under_vedha,
        "nakshatras_free": free_count,
    }
    print(json.dumps(status))


# ---------------------------------------------------------------------------
# Country Dasha command
# ---------------------------------------------------------------------------

def _load_foundation_chart(country_name):
    """Load and return a country's foundation_chart.yaml."""
    chart_path = os.path.join(
        _SCRIPT_DIR, "world_data",
        country_name.lower().replace(" ", "_"),
        "foundation_chart.yaml",
    )
    if not os.path.exists(chart_path):
        return None, chart_path
    with open(chart_path, "r") as f:
        return yaml.safe_load(f), chart_path


def _compute_dashas_extended(moon_lon, birth_date_obj, end_date):
    """Compute MD list cycling Vimsottari periods until end_date is covered.

    For entities older than 120 years (countries), the 120-year cycle repeats.
    Returns the full md_list covering birth through end_date.
    """
    nak_name, nak_lord, pada, deg_in_nak = get_nakshatra(moon_lon)
    start_index = DASHA_SEQUENCE.index(nak_lord)
    proportion_remaining = 1 - (deg_in_nak / NAKSHATRA_SPAN)

    md_list = []

    # First (partial) dasha
    first_years = DASHA_YEARS[nak_lord]
    balance_days = first_years * proportion_remaining * 365.25
    md_start = birth_date_obj
    md_end = birth_date_obj + timedelta(days=balance_days)
    md_list.append({"lord": nak_lord, "start": md_start, "end": md_end,
                    "years": first_years * proportion_remaining})

    # Subsequent full dashas, cycling indefinitely until we pass end_date
    cycle_pos = 1
    while md_list[-1]["end"] < end_date:
        lord = DASHA_SEQUENCE[(start_index + cycle_pos) % 9]
        years = DASHA_YEARS[lord]
        md_start = md_list[-1]["end"]
        md_end = md_start + timedelta(days=years * 365.25)
        md_list.append({"lord": lord, "start": md_start, "end": md_end,
                        "years": years})
        cycle_pos += 1

    return md_list, nak_lord, start_index


def _find_dasha_at_date(moon_lon, birth_date_obj, target_date):
    """Find MD/AD/PD at a target date, handling multi-cycle countries."""
    # Extend MDs past target_date
    md_list, nak_lord, start_index = _compute_dashas_extended(
        moon_lon, birth_date_obj, target_date + timedelta(days=1)
    )

    # Find the MD containing target_date
    active_md = None
    for md in md_list:
        if md["start"] <= target_date <= md["end"]:
            active_md = md
            break
    if active_md is None:
        return None

    md_lord = active_md["lord"]
    md_start_idx = DASHA_SEQUENCE.index(md_lord)
    md_total_days = (active_md["end"] - active_md["start"]).days

    # Compute ADs within this MD
    ad_start = active_md["start"]
    active_ad = None
    ad_lord = None
    ad_end = None
    for j in range(9):
        ad_lord_j = DASHA_SEQUENCE[(md_start_idx + j) % 9]
        ad_proportion = DASHA_YEARS[ad_lord_j] / 120.0
        ad_days = md_total_days * ad_proportion
        ad_end_j = ad_start + timedelta(days=ad_days)

        if ad_start <= target_date <= ad_end_j:
            active_ad = {"lord": ad_lord_j, "start": ad_start,
                         "end": ad_end_j, "days": ad_days}
            break
        ad_start = ad_end_j

    if active_ad is None:
        return {"md": md_lord, "ad": "?", "pd": "?",
                "md_start": active_md["start"].isoformat(),
                "md_end": active_md["end"].isoformat()}

    # Compute PDs within this AD
    ad_lord = active_ad["lord"]
    ad_start_idx = DASHA_SEQUENCE.index(ad_lord)
    pd_start = active_ad["start"]
    active_pd_lord = "?"
    pd_start_date = active_ad["start"]
    pd_end_date = active_ad["end"]

    for k in range(9):
        pd_lord = DASHA_SEQUENCE[(ad_start_idx + k) % 9]
        pd_proportion = DASHA_YEARS[pd_lord] / 120.0
        pd_days = active_ad["days"] * pd_proportion
        pd_end = pd_start + timedelta(days=pd_days)

        if pd_start <= target_date <= pd_end:
            active_pd_lord = pd_lord
            pd_start_date = pd_start
            pd_end_date = pd_end
            break
        pd_start = pd_end

    return {
        "md": md_lord,
        "ad": ad_lord,
        "pd": active_pd_lord,
        "md_start": active_md["start"].isoformat(),
        "md_end": active_md["end"].isoformat(),
        "ad_start": active_ad["start"].isoformat(),
        "ad_end": active_ad["end"].isoformat(),
        "pd_start": pd_start_date.isoformat(),
        "pd_end": pd_end_date.isoformat(),
    }


def cmd_country_dasha(args):
    """Compute Vimsottari dasha for a country's foundation chart at a date/range.

    Handles multi-cycle countries (e.g., USA founded 1776 needs 2+ cycles).
    Can output a single date lookup or a monthly range.
    """
    chart_data, chart_path = _load_foundation_chart(args.name)
    if chart_data is None:
        print(json.dumps({"status": "error",
                          "message": f"Foundation chart not found: {chart_path}"}))
        sys.exit(1)

    # Get Moon longitude and birth date
    moon_deg = chart_data["chandra"]["degree"]
    moon_rasi = chart_data["chandra"]["rasi"]
    rasi_idx = RASHI_NAMES.index(moon_rasi)
    moon_lon = rasi_idx * 30.0 + moon_deg

    entity = chart_data["entity"]
    birth_date = datetime.strptime(entity["date"], "%Y-%m-%d").date()

    # Determine date range
    if args.range_start and args.range_end:
        range_start = datetime.strptime(args.range_start, "%Y-%m-%d").date()
        range_end = datetime.strptime(args.range_end, "%Y-%m-%d").date()
    else:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
        range_start = target
        range_end = target

    # Build extended MD list
    md_list, nak_lord, start_index = _compute_dashas_extended(
        moon_lon, birth_date, range_end + timedelta(days=1)
    )

    # Collect dasha changes within range
    results = []

    if range_start == range_end:
        # Single date lookup
        dasha = _find_dasha_at_date(moon_lon, birth_date, range_start)
        results.append({"date": range_start.isoformat(), "dasha": dasha})
    else:
        # Monthly range: compute dasha at 1st of each month
        current = range_start.replace(day=1)
        while current <= range_end:
            dasha = _find_dasha_at_date(moon_lon, birth_date, current)
            results.append({"date": current.isoformat(), "dasha": dasha})
            # Next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

    # Find dasha transitions in the range
    transitions = []
    for md in md_list:
        if range_start <= md["start"].date() if hasattr(md["start"], 'date') else md["start"] <= range_end:
            md_date = md["start"].date() if hasattr(md["start"], "date") else md["start"]
            if range_start <= md_date <= range_end:
                transitions.append({
                    "date": md_date.isoformat(),
                    "type": "maha_dasha_change",
                    "new_lord": md["lord"],
                })

    output = {
        "entity": entity["name"],
        "moon_nakshatra": chart_data["chandra"].get("nakshatra", ""),
        "moon_rasi": moon_rasi,
        "dasha_at_dates": results,
        "transitions_in_range": transitions,
    }

    if getattr(args, "print_summary", False):
        import sys as _sys
        _sys.stderr.write(f"\n=== {entity['name']} Dasha Analysis ===\n")
        _sys.stderr.write(f"Foundation: {entity['date']} | Moon: {moon_rasi} "
                          f"{chart_data['chandra'].get('nakshatra', '')}\n\n")
        for r in results:
            d = r["dasha"]
            if d:
                _sys.stderr.write(
                    f"  {r['date']}: {d['md']}/{d['ad']}/{d['pd']}  "
                    f"(MD: {d['md_start'][:10]}→{d['md_end'][:10]}  "
                    f"AD: {d['ad_start'][:10]}→{d['ad_end'][:10]})\n"
                )
        if transitions:
            _sys.stderr.write(f"\nDasha transitions in range:\n")
            for t in transitions:
                _sys.stderr.write(f"  {t['date']}: {t['type']} → {t['new_lord']}\n")
        _sys.stderr.write("\n")

    print(json.dumps(output, default=str))


# ---------------------------------------------------------------------------
# Transit Overlay command
# ---------------------------------------------------------------------------

# Graha drishti (aspect) rules: planet -> list of houses it aspects (from itself)
GRAHA_DRISHTI = {
    "Sun": [7],
    "Moon": [7],
    "Mars": [4, 7, 8],
    "Mercury": [7],
    "Jupiter": [5, 7, 9],
    "Venus": [7],
    "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9],   # Like Jupiter
    "Ketu": [5, 7, 9],   # Like Jupiter
}

# Sanskrit-to-English planet name mapping for chart data
SANS_TO_ENG = {
    "surya": "Sun", "chandra": "Moon", "mangal": "Mars",
    "budha": "Mercury", "guru": "Jupiter", "shukra": "Venus",
    "shani": "Saturn", "rahu": "Rahu", "ketu": "Ketu",
}


def cmd_transit_overlay(args):
    """Overlay current transits on a country's foundation chart.

    Shows: which natal houses are activated, conjunctions to natal planets,
    aspects to natal planets, and transit over natal Moon (Gochar).
    """
    chart_data, chart_path = _load_foundation_chart(args.country)
    if chart_data is None:
        print(json.dumps({"status": "error",
                          "message": f"Foundation chart not found: {chart_path}"}))
        sys.exit(1)

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    # --- Compute transit positions ---
    jd = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    transit_positions = {}
    for swe_id, eng_name, sans_name, yaml_key in GRAHA_LIST:
        pos, _ret = swe.calc_ut(jd, swe_id)
        sid_lon = (pos[0] - ayanamsha) % 360
        rashi_name, rashi_idx, deg = get_rashi(sid_lon)
        transit_positions[eng_name] = {
            "rasi": rashi_name, "rasi_idx": rashi_idx,
            "degree": round(deg, 4), "sid_lon": sid_lon,
        }
    # Rahu/Ketu (mean node)
    pos_rahu, _ = swe.calc_ut(jd, swe.MEAN_NODE)
    rahu_sid = (pos_rahu[0] - ayanamsha) % 360
    ketu_sid = (rahu_sid + 180) % 360
    rahu_rashi, rahu_idx, rahu_deg = get_rashi(rahu_sid)
    ketu_rashi, ketu_idx, ketu_deg = get_rashi(ketu_sid)
    transit_positions["Rahu"] = {"rasi": rahu_rashi, "rasi_idx": rahu_idx,
                                  "degree": round(rahu_deg, 4), "sid_lon": rahu_sid}
    transit_positions["Ketu"] = {"rasi": ketu_rashi, "rasi_idx": ketu_idx,
                                  "degree": round(ketu_deg, 4), "sid_lon": ketu_sid}

    # --- Parse natal chart ---
    lagna_rasi = chart_data["lagna"]["rasi"]
    lagna_idx = RASHI_NAMES.index(lagna_rasi)

    natal_positions = {}
    for sans_key, p_data in chart_data["planetary_positions"].items():
        eng_name = SANS_TO_ENG.get(sans_key, sans_key)
        rasi_idx = RASHI_NAMES.index(p_data["rasi"])
        natal_positions[eng_name] = {
            "rasi": p_data["rasi"], "rasi_idx": rasi_idx,
            "degree": p_data["degree"],
            "house": (rasi_idx - lagna_idx) % 12 + 1,
        }

    natal_moon_rasi_idx = natal_positions["Moon"]["rasi_idx"]

    # --- Compute overlay ---
    overlay = {}
    for t_planet, t_data in transit_positions.items():
        t_rasi_idx = t_data["rasi_idx"]

        # Which natal house is this transit in?
        natal_house = (t_rasi_idx - lagna_idx) % 12 + 1

        # House from natal Moon (for Gochar/Tara analysis)
        house_from_moon = (t_rasi_idx - natal_moon_rasi_idx) % 12 + 1

        # Tara classification (9-tara cycle)
        tara_names = [
            "Janma (1-Birth)", "Sampat (2-Wealth)", "Vipat (3-Danger)",
            "Kshema (4-Prosperity)", "Pratyak (5-Obstacle)",
            "Sadhana (6-Achievement)", "Naidhana (7-Death)",
            "Mitra (8-Friend)", "Parama Mitra (9-Best Friend)",
        ]
        # Tarabala is based on house from Moon
        tara_idx = (house_from_moon - 1) % 9
        tara = tara_names[tara_idx]
        tara_favorable = tara_idx in [1, 3, 5, 7, 8]  # 2,4,6,8,9 are good

        # Conjunctions with natal planets (same rasi)
        conjunctions = []
        for n_planet, n_data in natal_positions.items():
            if n_data["rasi_idx"] == t_rasi_idx:
                sep = abs(t_data["degree"] - n_data["degree"])
                conjunctions.append({
                    "natal_planet": n_planet,
                    "separation_deg": round(sep, 2),
                    "tight": sep < 5.0,
                })

        # Aspects from transit planet to natal planets
        aspects = []
        if t_planet in GRAHA_DRISHTI:
            for aspect_offset in GRAHA_DRISHTI[t_planet]:
                aspected_rasi_idx = (t_rasi_idx + aspect_offset - 1) % 12
                for n_planet, n_data in natal_positions.items():
                    if n_data["rasi_idx"] == aspected_rasi_idx:
                        aspects.append({
                            "natal_planet": n_planet,
                            "aspect_type": f"{aspect_offset}th aspect",
                            "natal_house": n_data["house"],
                        })

        # Transit over natal Moon specifically
        transit_on_moon = (t_rasi_idx == natal_moon_rasi_idx)

        overlay[t_planet] = {
            "transit_rasi": t_data["rasi"],
            "transit_degree": t_data["degree"],
            "natal_house": natal_house,
            "house_from_moon": house_from_moon,
            "tara": tara,
            "tara_favorable": tara_favorable,
            "conjunctions": conjunctions,
            "aspects": aspects,
            "transit_on_natal_moon": transit_on_moon,
        }

    # --- Key activations summary ---
    activations = []
    for t_planet, o_data in overlay.items():
        for conj in o_data["conjunctions"]:
            if conj["tight"]:
                activations.append({
                    "type": "tight_conjunction",
                    "transit": t_planet,
                    "natal": conj["natal_planet"],
                    "natal_house": natal_positions[conj["natal_planet"]]["house"],
                    "separation": conj["separation_deg"],
                })
        if o_data["transit_on_natal_moon"]:
            activations.append({
                "type": "transit_on_natal_moon",
                "transit": t_planet,
                "house_from_lagna": o_data["natal_house"],
            })
        for asp in o_data["aspects"]:
            activations.append({
                "type": "aspect",
                "transit": t_planet,
                "aspect": asp["aspect_type"],
                "natal": asp["natal_planet"],
                "natal_house": asp["natal_house"],
            })

    # --- Sensitive houses check ---
    # Houses 1, 6, 8, 10 activations by malefics are significant
    malefics = {"Mars", "Saturn", "Rahu", "Ketu", "Sun"}
    sensitive_hits = []
    for t_planet, o_data in overlay.items():
        if t_planet in malefics and o_data["natal_house"] in [1, 6, 8, 10]:
            sensitive_hits.append({
                "planet": t_planet,
                "house": o_data["natal_house"],
                "rasi": o_data["transit_rasi"],
            })

    output = {
        "entity": chart_data["entity"]["name"],
        "date": target_date.isoformat(),
        "lagna": lagna_rasi,
        "natal_moon": natal_positions["Moon"]["rasi"],
        "transit_overlay": overlay,
        "key_activations": activations,
        "malefic_sensitive_house_hits": sensitive_hits,
    }

    if getattr(args, "print_summary", False):
        import sys as _sys
        _sys.stderr.write(f"\n=== Transit Overlay: {chart_data['entity']['name']} "
                          f"on {target_date} ===\n")
        _sys.stderr.write(f"Lagna: {lagna_rasi} | Moon: "
                          f"{natal_positions['Moon']['rasi']}\n\n")

        _sys.stderr.write("Transit Positions on Natal Chart:\n")
        _sys.stderr.write(f"  {'Planet':<10} {'Transit Rasi':<14} {'Natal H':<8} "
                          f"{'From Moon':<10} {'Tara':<25} {'Notes'}\n")
        _sys.stderr.write("  " + "-" * 90 + "\n")
        for t_planet in ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars",
                         "Sun", "Moon", "Mercury", "Venus"]:
            if t_planet not in overlay:
                continue
            o = overlay[t_planet]
            notes = []
            if o["conjunctions"]:
                for c in o["conjunctions"]:
                    tight = "*" if c["tight"] else ""
                    notes.append(f"conj {c['natal_planet']}{tight}({c['separation_deg']}°)")
            if o["aspects"]:
                for a in o["aspects"]:
                    notes.append(f"asp {a['natal_planet']}(H{a['natal_house']})")
            fav = "+" if o["tara_favorable"] else "-"
            _sys.stderr.write(
                f"  {t_planet:<10} {o['transit_rasi']:<14} H{o['natal_house']:<7} "
                f"H{o['house_from_moon']:<9} {o['tara']:<25} "
                f"{', '.join(notes)}\n"
            )

        if sensitive_hits:
            _sys.stderr.write(f"\nMalefic hits on sensitive houses (1/6/8/10):\n")
            for h in sensitive_hits:
                _sys.stderr.write(f"  {h['planet']} in H{h['house']} ({h['rasi']})\n")

        if activations:
            tight_conjs = [a for a in activations if a["type"] == "tight_conjunction"]
            if tight_conjs:
                _sys.stderr.write(f"\nTight conjunctions (<5°):\n")
                for a in tight_conjs:
                    _sys.stderr.write(
                        f"  Transit {a['transit']} conj natal {a['natal']} "
                        f"(H{a['natal_house']}, sep {a['separation']}°)\n"
                    )
        _sys.stderr.write("\n")

    print(json.dumps(output, default=str))


# ---------------------------------------------------------------------------
# Stub commands (to be implemented)
# ---------------------------------------------------------------------------

def cmd_stub(args):
    """Placeholder for commands not yet implemented."""
    print(json.dumps({
        "status": "not_implemented",
        "command": args.command,
        "message": f"Command '{args.command}' is not yet implemented.",
    }))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Medini (Mundane) Astrology Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- positions ---
    pos_parser = subparsers.add_parser(
        "positions",
        help="Compute sidereal planetary positions for a date (00:00 UTC)",
    )
    pos_parser.add_argument(
        "--date", default=str(date.today()),
        help="Date in YYYY-MM-DD format (default: today)",
    )
    pos_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- ingress ---
    ing_parser = subparsers.add_parser(
        "ingress",
        help="Compute solar ingress chart for a cardinal sign/year",
    )
    ing_parser.add_argument(
        "--type", dest="ingress_type", required=True,
        choices=["aries", "cancer", "libra", "capricorn"],
        help="Cardinal sign ingress type",
    )
    ing_parser.add_argument(
        "--year", type=int, required=True, help="Year to compute ingress for",
    )
    ing_parser.add_argument(
        "--lat", type=float, default=28.6139,
        help="Latitude (default: 28.6139 = New Delhi)",
    )
    ing_parser.add_argument(
        "--lon", type=float, default=77.2090,
        help="Longitude (default: 77.2090 = New Delhi)",
    )
    ing_parser.add_argument(
        "--timezone", type=float, default=5.5,
        help="Timezone offset from UTC (default: 5.5 = IST)",
    )
    ing_parser.add_argument(
        "--city", default="New Delhi",
        help="City name for output (default: New Delhi)",
    )
    ing_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- eclipse ---
    ecl_parser = subparsers.add_parser(
        "eclipse",
        help="Compute detailed chart for a specific eclipse",
    )
    ecl_parser.add_argument(
        "--date", required=True,
        help="Eclipse date YYYY-MM-DD (finds nearest eclipse)",
    )
    ecl_parser.add_argument(
        "--lat", type=float, default=28.6139,
        help="Latitude (default: 28.6139 = New Delhi)",
    )
    ecl_parser.add_argument(
        "--lon", type=float, default=77.2090,
        help="Longitude (default: 77.2090 = New Delhi)",
    )
    ecl_parser.add_argument(
        "--timezone", type=float, default=5.5,
        help="Timezone offset from UTC (default: 5.5 = IST)",
    )
    ecl_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- eclipses ---
    ecls_parser = subparsers.add_parser(
        "eclipses",
        help="List all eclipses in a year",
    )
    ecls_parser.add_argument(
        "--year", type=int, default=date.today().year,
        help="Year to list eclipses for (default: current year)",
    )
    ecls_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- country ---
    ctry_parser = subparsers.add_parser(
        "country",
        help="Compute foundation chart for a country",
    )
    ctry_parser.add_argument("--name", required=True,
                              help="Country name (folder under world_data/)")
    ctry_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- conjunction ---
    conj_parser = subparsers.add_parser(
        "conjunction",
        help="Find planetary conjunctions in a year",
    )
    conj_parser.add_argument(
        "--planets", required=True,
        help="Comma-separated planet pair (e.g. saturn,jupiter)",
    )
    conj_parser.add_argument(
        "--year", type=int, default=date.today().year,
        help="Year to search (default: current year)",
    )
    conj_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- wars ---
    wars_parser = subparsers.add_parser(
        "wars",
        help="Find graha yuddha (planetary wars) in a date range",
    )
    wars_parser.add_argument(
        "--start", required=True, help="Start date YYYY-MM-DD",
    )
    wars_parser.add_argument(
        "--end", required=True, help="End date YYYY-MM-DD",
    )
    wars_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- retrogrades ---
    retro_parser = subparsers.add_parser(
        "retrogrades",
        help="List retrograde stations for all planets in a year",
    )
    retro_parser.add_argument(
        "--year", type=int, default=date.today().year,
        help="Year to search (default: current year)",
    )
    retro_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- sign-changes ---
    sc_parser = subparsers.add_parser(
        "sign-changes",
        help="List sign changes for slow planets in a year",
    )
    sc_parser.add_argument(
        "--year", type=int, default=date.today().year,
        help="Year to search (default: current year)",
    )
    sc_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- panchanga ---
    panch_parser = subparsers.add_parser(
        "panchanga",
        help="Compute panchanga (five-fold almanac) for a date",
    )
    panch_parser.add_argument(
        "--date", default=str(date.today()),
        help="Date in YYYY-MM-DD format (default: today)",
    )
    panch_parser.add_argument(
        "--lat", type=float, default=28.6139,
        help="Latitude (default: 28.6139 = New Delhi)",
    )
    panch_parser.add_argument(
        "--lon", type=float, default=77.2090,
        help="Longitude (default: 77.2090 = New Delhi)",
    )
    panch_parser.add_argument(
        "--timezone", type=float, default=5.5,
        help="Timezone offset from UTC (default: 5.5 = IST)",
    )
    panch_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- ashtakavarga ---
    ashta_parser = subparsers.add_parser(
        "ashtakavarga",
        help="Compute BAV/SAV ashtakavarga for a country's foundation chart",
    )
    ashta_parser.add_argument(
        "--country", required=True,
        help="Country name (must have foundation_chart.yaml in world_data/)",
    )
    ashta_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- sbc (Sarvatobhadra Chakra) ---
    sbc_parser = subparsers.add_parser(
        "sbc",
        help="Compute Sarvatobhadra Chakra vedha for transit analysis",
    )
    sbc_parser.add_argument(
        "--date", default=str(date.today()),
        help="Date in YYYY-MM-DD format (default: today)",
    )
    sbc_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- country-dasha ---
    cd_parser = subparsers.add_parser(
        "country-dasha",
        help="Compute Vimsottari dasha for a country at a date or range",
    )
    cd_parser.add_argument(
        "--name", required=True,
        help="Country name (folder under world_data/)",
    )
    cd_parser.add_argument(
        "--date", default=str(date.today()),
        help="Single date to look up (default: today)",
    )
    cd_parser.add_argument(
        "--range-start", dest="range_start", default=None,
        help="Start date for monthly range (YYYY-MM-DD)",
    )
    cd_parser.add_argument(
        "--range-end", dest="range_end", default=None,
        help="End date for monthly range (YYYY-MM-DD)",
    )
    cd_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    # --- transit-overlay ---
    to_parser = subparsers.add_parser(
        "transit-overlay",
        help="Overlay current transits on a country's foundation chart",
    )
    to_parser.add_argument(
        "--country", required=True,
        help="Country name (must have foundation_chart.yaml in world_data/)",
    )
    to_parser.add_argument(
        "--date", default=str(date.today()),
        help="Date in YYYY-MM-DD format (default: today)",
    )
    to_parser.add_argument(
        "--print", dest="print_summary", action="store_true",
        help="Print human-readable summary to stderr",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    return args


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

COMMAND_DISPATCH = {
    "positions": cmd_positions,
    "ingress": cmd_ingress,
    "eclipse": cmd_eclipse,
    "eclipses": cmd_eclipses,
    "country": cmd_country,
    "conjunction": cmd_conjunction,
    "wars": cmd_wars,
    "retrogrades": cmd_retrogrades,
    "sign-changes": cmd_sign_changes,
    "panchanga": cmd_panchanga,
    "ashtakavarga": cmd_ashtakavarga,
    "sbc": cmd_sbc,
    "country-dasha": cmd_country_dasha,
    "transit-overlay": cmd_transit_overlay,
}


def main(argv=None):
    args = parse_args(argv)
    handler = COMMAND_DISPATCH.get(args.command, cmd_stub)
    handler(args)


if __name__ == "__main__":
    main()
