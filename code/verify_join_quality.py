#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce the three matching rates reported in this repo.

Only the Python standard library is required: the join is an attribute join, so
geometry is not needed. The script reads the GADM `.dbf` attribute table and the
2025 county population slice.

Usage
-----
    python code/verify_join_quality.py \
        --gadm-dbf /path/to/gadm41_USA_2.dbf \
        --population-csv data/population_2025_counties.csv

Expected (with the data used in this repo)
------------------------------------------
    GADM features        : 3148
    2025 county rows     : 3145
    baseline  (naive)    : 2978 matched / 170 unmatched
    cleaned   (rules)    : 3082 matched / 66 unmatched
    agent     (POP_2025) : 3123 matched / 25 unmatched
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import struct
import sys
from collections import Counter

STATE_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
    "PR": "Puerto Rico",
}

# Suffixes removed by the rule-based GeoPandas pipeline (round 2).
RULES_SUFFIXES = [" COUNTY", " PARISH", " BOROUGH", " CENSUS AREA", " CITY", " MUNICIPALITY"]


def read_dbf(path: str) -> list[dict]:
    """Minimal dBase III reader, enough for GADM attribute tables."""
    with open(path, "rb") as fh:
        data = fh.read()
    n_records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]

    fields: list[tuple[str, str, int]] = []
    offset = 32
    while data[offset] != 0x0D:
        name = data[offset:offset + 11].split(b"\x00")[0].decode("latin-1")
        ftype = chr(data[offset + 11])
        flen = data[offset + 16]
        fields.append((name, ftype, flen))
        offset += 32

    rows = []
    for i in range(n_records):
        record = data[header_len + i * record_len: header_len + (i + 1) * record_len]
        if not record or record[0:1] == b"*":  # deleted
            continue
        pos, row = 1, {}
        for name, ftype, flen in fields:
            raw = record[pos:pos + flen].decode("latin-1", "replace").strip()
            pos += flen
            if ftype in "NF":
                try:
                    row[name] = float(raw)
                except ValueError:
                    row[name] = None
            else:
                row[name] = raw
        rows.append(row)
    return rows


def naive_key(county: str) -> str:
    """Round 1: only strip ' County', uppercase."""
    return county.upper().replace(" COUNTY", "").strip()


def clean_key(county: str) -> str:
    """Round 2: uppercase, drop type suffixes, normalise abbreviations."""
    key = county.upper().strip()
    for suffix in RULES_SUFFIXES:
        key = key.replace(suffix, "")
    key = key.replace("ST. ", "SAINT ").replace("FT. ", "FORT ").replace("MT. ", "MOUNT ")
    return re.sub(r"\s+", " ", key).strip()


def load_population(path: str) -> list[dict]:
    """Return 2025 county rows from either the slice or the original CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            year = str(row.get("Year", "2025")).strip()
            fips = str(row.get("Countyfips", "")).strip()
            if year != "2025":
                continue
            try:
                if int(fips or 0) <= 0:
                    continue
            except ValueError:
                continue
            desc = row["Description"].strip()
            if ", " not in desc:  # national / state summary rows
                continue
            county, abbr = desc.rsplit(", ", 1)
            rows.append({
                "county": county,
                "state": STATE_ABBR.get(abbr.strip(), abbr.strip()),
                "population": float(row["Total Population"]),
            })
    return rows


def build_index(rows: list[dict], keyfunc) -> dict[tuple[str, str], float]:
    """(state, county) -> population. Duplicate keys keep the first value."""
    index: dict[tuple[str, str], float] = {}
    for row in rows:
        key = (row["state"].upper(), keyfunc(row["county"]))
        index.setdefault(key, row["population"])
    return index


def report(label: str, features: list[dict], matched: int) -> None:
    total = len(features)
    print(f"{label:<22}: {matched} matched / {total - matched} unmatched "
          f"({matched / total * 100:.2f}%)")


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

USAGE_HELP = """\
找不到数据文件。这个仓库刻意没有收录 GADM 边界（许可 + 体积原因）。

请先下载:
    https://gadm.org/download_country.html
    选择 USA -> Level 2 -> Shapefile，解压后把 gadm41_USA_2.dbf
    放到 data/ 目录（与 population_2025_counties.csv 同级）。

然后运行（两种写法都可以）:
    python code/verify_join_quality.py
    python code/verify_join_quality.py --gadm-dbf data/gadm41_USA_2.dbf --population-csv data/population_2025_counties.csv

预期结果:
    GADM features        : 3148
    2025 county rows     : 3145
    baseline  (naive)    : 2978 matched / 170 unmatched
    cleaned   (rules)    : 3082 matched / 66 unmatched
    agent     (POP_2025) : 3123 matched / 25 unmatched
"""


def find_first(paths: list[str]) -> str | None:
    for path in paths:
        if path and os.path.isfile(path):
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gadm-dbf", default=None,
                        help="path to gadm41_USA_2.dbf (default: data/gadm41_USA_2.dbf)")
    parser.add_argument("--population-csv", default=None,
                        help="2025 county CSV (default: data/population_2025_counties.csv)")
    parser.add_argument("--dump-dir", default=None, help="optional folder for unmatched CSV files")
    args = parser.parse_args()

    gadm = args.gadm_dbf or find_first([
        os.path.join(REPO_ROOT, "data", "gadm41_USA_2.dbf"),
        os.path.join(os.getcwd(), "data", "gadm41_USA_2.dbf"),
        os.path.join(os.getcwd(), "gadm41_USA_2.dbf"),
    ])
    population_csv = args.population_csv or find_first([
        os.path.join(REPO_ROOT, "data", "population_2025_counties.csv"),
        os.path.join(os.getcwd(), "data", "population_2025_counties.csv"),
    ])

    if not gadm or not population_csv:
        print(USAGE_HELP, file=sys.stderr)
        return 2

    try:
        features = read_dbf(gadm)
    except Exception as exc:  # noqa: BLE001 - the message is the point
        print(f"[!] 读取 DBF 失败: {gadm}\n    {exc}\n"
              "    请确认这是 gadm41_USA_2.dbf，而不是 .shp 或压缩包。", file=sys.stderr)
        return 1

    try:
        population = load_population(population_csv)
    except Exception as exc:  # noqa: BLE001
        print(f"[!] 读取人口 CSV 失败: {population_csv}\n    {exc}\n"
              "    请确认文件包含 Description / Countyfips / Total Population 三列。", file=sys.stderr)
        return 1

    print(f"GADM features        : {len(features)}")
    print(f"2025 county rows     : {len(population)}")

    naive = build_index(population, naive_key)
    cleaned = build_index(population, clean_key)

    def count_matches(index, keyfunc=clean_key):
        missing = []
        for feature in features:
            key = (feature["NAME_1"].upper(), keyfunc(feature["NAME_2"]))
            if key not in index:
                missing.append(feature)
        return len(features) - len(missing), missing

    naive_matched, naive_missing = count_matches(naive, naive_key)
    clean_matched, clean_missing = count_matches(cleaned, clean_key)
    agent_missing = [f for f in features if f.get("POP_2025") is None]
    agent_matched = len(features) - len(agent_missing)

    report("baseline  (naive)", features, naive_matched)
    report("cleaned   (rules)", features, clean_matched)
    report("agent     (POP_2025)", features, agent_matched)

    # The agent's field must exist; otherwise the DBF is not the joined one.
    if "POP_2025" not in features[0]:
        print("\n[!] No POP_2025 field: this DBF is not the post-join version, "
              "so the third line above is meaningless.", file=sys.stderr)

    print("\nUnmatched by state (cleaned):")
    for state, count in Counter(f["NAME_1"] for f in clean_missing).most_common():
        print(f"  {state:<22} {count}")

    if args.dump_dir:
        os.makedirs(args.dump_dir, exist_ok=True)
        for name, rows in (("unmatched_baseline.csv", naive_missing),
                           ("unmatched_geopandas.csv", clean_missing),
                           ("unmatched_qgis.csv", agent_missing)):
            path = os.path.join(args.dump_dir, name)
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.DictWriter(fh, fieldnames=["GID_2", "NAME_1", "NAME_2", "TYPE_2"])
                writer.writeheader()
                writer.writerows({k: f.get(k) for k in writer.fieldnames} for f in rows)
            print(f"wrote {path} ({len(rows)} rows)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
