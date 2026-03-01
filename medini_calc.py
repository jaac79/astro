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
    ctry_parser.add_argument("--name", help="Country name")

    # --- conjunction ---
    conj_parser = subparsers.add_parser(
        "conjunction",
        help="Find planetary conjunctions in a date range",
    )
    conj_parser.add_argument("--planets", help="Comma-separated planet pair")
    conj_parser.add_argument("--start", help="Start date YYYY-MM-DD")
    conj_parser.add_argument("--end", help="End date YYYY-MM-DD")

    # --- wars ---
    wars_parser = subparsers.add_parser(
        "wars",
        help="Find graha yuddha (planetary wars) in a date range",
    )
    wars_parser.add_argument("--start", help="Start date YYYY-MM-DD")
    wars_parser.add_argument("--end", help="End date YYYY-MM-DD")

    # --- retrogrades ---
    retro_parser = subparsers.add_parser(
        "retrogrades",
        help="List retrograde periods for a planet in a date range",
    )
    retro_parser.add_argument("--planet", help="Planet name")
    retro_parser.add_argument("--start", help="Start date YYYY-MM-DD")
    retro_parser.add_argument("--end", help="End date YYYY-MM-DD")

    # --- sign-changes ---
    sc_parser = subparsers.add_parser(
        "sign-changes",
        help="List rasi transit dates for a planet in a date range",
    )
    sc_parser.add_argument("--planet", help="Planet name")
    sc_parser.add_argument("--start", help="Start date YYYY-MM-DD")
    sc_parser.add_argument("--end", help="End date YYYY-MM-DD")

    # --- panchanga ---
    panch_parser = subparsers.add_parser(
        "panchanga",
        help="Compute panchanga for a date",
    )
    panch_parser.add_argument("--date", help="Date YYYY-MM-DD")

    # --- ashtakavarga ---
    ashta_parser = subparsers.add_parser(
        "ashtakavarga",
        help="Compute Sarvashtakavarga for current positions",
    )
    ashta_parser.add_argument("--date", help="Date YYYY-MM-DD")

    # --- sbc (Sarvatobhadra Chakra) ---
    sbc_parser = subparsers.add_parser(
        "sbc",
        help="Compute Sarvatobhadra Chakra for transit analysis",
    )
    sbc_parser.add_argument("--date", help="Date YYYY-MM-DD")

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
    "ingress": cmd_stub,
    "eclipse": cmd_eclipse,
    "eclipses": cmd_eclipses,
    "country": cmd_stub,
    "conjunction": cmd_stub,
    "wars": cmd_stub,
    "retrogrades": cmd_stub,
    "sign-changes": cmd_stub,
    "panchanga": cmd_stub,
    "ashtakavarga": cmd_stub,
    "sbc": cmd_stub,
}


def main(argv=None):
    args = parse_args(argv)
    handler = COMMAND_DISPATCH.get(args.command, cmd_stub)
    handler(args)


if __name__ == "__main__":
    main()
