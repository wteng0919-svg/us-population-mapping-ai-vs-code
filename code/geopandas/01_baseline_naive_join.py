#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 1 - the naive join: only strip " County" and uppercase both sides.

This is the baseline that produced 2,978 / 3,148 matches (170 unmatched) and
48 state maps (Alaska, Connecticut and Louisiana were skipped entirely).

    python code/geopandas/01_baseline_naive_join.py \
        --gadm data/gadm41_USA_2.shp \
        --pop data/population_2025_counties.csv \
        --out outputs/baseline
"""

from __future__ import annotations

import argparse
import os

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
    pop["County"] = pop["County"].str.upper().str.replace(" COUNTY", "", regex=False).str.strip()
    return pop


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gadm", required=True, help="gadm41_USA_2.shp")
    parser.add_argument("--pop", required=True, help="population CSV (full table or 2025 slice)")
    parser.add_argument("--out", default="outputs/baseline")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    gdf = gpd.read_file(args.gadm)
    pop = load_population(args.pop)
    gdf["NAME_1"] = gdf["NAME_1"].str.upper().str.strip()
    gdf["NAME_2"] = gdf["NAME_2"].str.upper().str.strip()

    merged = gdf.merge(pop, left_on=["NAME_1", "NAME_2"], right_on=["State", "County"], how="left")
    matched = int(merged["Population"].notna().sum())
    print(f"matched {matched} / {len(merged)} - unmatched {len(merged) - matched}")

    skipped = []
    for state, data in merged.groupby("NAME_1"):
        if data["Population"].isna().all():
            skipped.append(state.title())
            continue
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        data.plot(
            column="Population", cmap="Reds", linewidth=0.5, ax=ax,
            edgecolor="0.5", legend=True,
            legend_kwds={"label": "Total Population (2025)", "orientation": "horizontal"},
        )
        ax.set_title(f"{state.title()} County Population (2025)", fontsize=16)
        ax.set_axis_off()
        fig.savefig(os.path.join(args.out, f"{state.title()}_pop_2025.png"),
                    dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"skipped states without any match: {skipped}")

    fig, ax = plt.subplots(1, 1, figsize=(20, 12))
    merged.plot(column="Population", cmap="Reds", scheme="Quantiles", k=7,
                ax=ax, edgecolor="0.8", linewidth=0.1)
    ax.set_axis_off()
    ax.set_title("USA County Population 2025 (naive join)", fontsize=18)
    fig.savefig(os.path.join(args.out, "USA_Population_Map.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
