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
from datetime import date, datetime

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
        help="Compute solar ingress chart for a rasi/year",
    )
    ing_parser.add_argument("--year", type=int, help="Year")
    ing_parser.add_argument("--rasi", help="Target rasi name")

    # --- eclipse ---
    ecl_parser = subparsers.add_parser(
        "eclipse",
        help="Compute chart for a specific eclipse",
    )
    ecl_parser.add_argument("--date", help="Eclipse date YYYY-MM-DD")

    # --- eclipses ---
    ecls_parser = subparsers.add_parser(
        "eclipses",
        help="List eclipses in a date range",
    )
    ecls_parser.add_argument("--start", help="Start date YYYY-MM-DD")
    ecls_parser.add_argument("--end", help="End date YYYY-MM-DD")

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
    "eclipse": cmd_stub,
    "eclipses": cmd_stub,
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
