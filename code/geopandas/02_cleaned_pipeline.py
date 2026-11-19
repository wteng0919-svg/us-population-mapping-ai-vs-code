#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 2 - rule-based name cleaning + quantile classification.

Produces 3,082 / 3,148 matches (66 unmatched) and 50 state maps
(Connecticut has no matching legacy county), plus a national map.

    python code/geopandas/02_cleaned_pipeline.py \
        --gadm data/gadm41_USA_2.shp \
        --pop data/population_2025_counties.csv \
        --out outputs/cleaned
"""

from __future__ import annotations

import argparse
import os
import re

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

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
}


def clean_name(name: str) -> str:
    """Normalise a county name so GADM names and CSV descriptions meet."""
    if pd.isna(name):
        return name
    key = str(name).upper().strip()
    for suffix in [" COUNTY", " PARISH", " BOROUGH", " CENSUS AREA", " CITY", " MUNICIPALITY"]:
        key = key.replace(suffix, "")
    key = key.replace("ST. ", "SAINT ").replace("FT. ", "FORT ").replace("MT. ", "MOUNT ")
    return re.sub(r"\s+", " ", key).strip()


def load_population(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")  # the shipped slice has a BOM
    if "Year" in df.columns:
        df = df[df["Year"] == 2025]
    fips = pd.to_numeric(df["Countyfips"], errors="coerce")
    df = df[fips.fillna(0) > 0].copy()

    split = df["Description"].str.split(", ", expand=True)
    df["County"] = split[0]
    df["State"] = split[1].str.strip().map(STATE_ABBR)

    pop = df[["State", "County", "Total Population"]].rename(columns={"Total Population": "Population"})
    pop["State"] = pop["State"].str.upper().str.strip()
    pop["County"] = pop["County"].apply(clean_name)
    return pop


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gadm", required=True, help="gadm41_USA_2.shp")
    parser.add_argument("--pop", required=True, help="population CSV (full table or 2025 slice)")
    parser.add_argument("--out", default="outputs/cleaned")
    parser.add_argument("--zoom-national", action="store_true",
                        help="crop the national map to CONUS (the default keeps the GADM extent)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    gdf = gpd.read_file(args.gadm)
    gdf["NAME_1"] = gdf["NAME_1"].str.upper().str.strip()
    gdf["NAME_2"] = gdf["NAME_2"].apply(clean_name)

    pop = load_population(args.pop)
    merged = gdf.merge(pop, left_on=["NAME_1", "NAME_2"], right_on=["State", "County"], how="left")

    matched = int(merged["Population"].notna().sum())
    print(f"matched rows {matched} / {len(merged)} - unmatched {len(merged) - matched}")

    for state, data in merged.groupby("NAME_1"):
        if data["Population"].isna().all():
            print(f"skip {state}: no matched county")
            continue
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        data.plot(
            column="Population", cmap="Reds", scheme="Quantiles", k=5,
            linewidth=0.5, ax=ax, edgecolor="0.5", legend=True,
            legend_kwds={"title": "Pop 2025", "loc": "lower right"},
        )
        ax.set_title(f"{state.title()} Population (Quantiles)", fontsize=16)
        ax.set_axis_off()
        fig.savefig(os.path.join(args.out, f"{state.title()}_pop.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)

    if args.zoom_national:
        merged = merged.cx[-125:-66, 24:50]  # CONUS only, avoids the 180-degree stretch

    fig, ax = plt.subplots(1, 1, figsize=(20, 12))
    merged.plot(column="Population", cmap="Reds", scheme="Quantiles", k=7,
                ax=ax, edgecolor="0.8", linewidth=0.1)
    ax.set_axis_off()
    ax.set_title("USA County Population 2025 (rule-cleaned join)", fontsize=18)
    fig.savefig(os.path.join(args.out, "USA_Population_Map.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
