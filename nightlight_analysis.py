"""
nightlight_analysis.py
-----------------------
Part of Riftic — The Ghotki Industrial Conversion Atlas.

Compares night-time light radiance (a standard economic-activity proxy) between
Ghotki's industrial zones (FFC-III, Mari/Engro Daharki, Qadirpur/OGDCL) and the
villages that sit right next to them, using NASA/NOAA VIIRS VNP46A2 monthly data,
2016-2026.

TWO MODES
=========
1. REAL MODE  (--mode real)
   Pulls actual VIIRS radiance via Google Earth Engine. Requires:
     pip install earthengine-api geemap
     earthengine authenticate   (one-time, needs a free Earth Engine account:
     https://signup.earthengine.google.com/)
   This mode needs internet access to Earth Engine servers.

2. DEMO MODE  (--mode demo, default)
   Generates a *labelled synthetic* dataset with the same shape, columns, and
   growth-trend logic real VIIRS output would have, so you can build and test
   the rest of the pipeline (scoring, dashboard) right now, before you have
   an Earth Engine account. Swap in real data later with zero changes
   downstream -- the CSV schema is identical.

OUTPUT
======
data/nightlight_scores.csv with columns:
    year, zone_id, zone_name, zone_type (industrial/village), mean_radiance,
    pct_change_from_2016
"""

import argparse
import os
import random
import csv

# ---------------------------------------------------------------------------
# Real Areas of Interest (AOIs) for Ghotki district, Sindh, Pakistan.
# Coordinates sourced from public records (Wikipedia / Global Energy Monitor).
# Each industrial site is paired with a nearby village for direct comparison.
# ---------------------------------------------------------------------------
AOIS = [
    # zone_id, name, type, lat, lon, buffer_meters
    ("ffc3",       "FFC-III Fertilizer Plant (Mirpur Mathelo)", "industrial", 28.0256, 69.5864, 1500),
    ("mmathelo",   "Mirpur Mathelo town",                        "village",    28.0170, 69.5330, 1500),
    ("qadirpur",   "Qadirpur Gas Field (OGDCL)",                  "industrial", 28.0469, 69.3631, 1500),
    ("ghotki_town","Ghotki town (near Qadirpur field)",           "village",    28.0072, 69.3175, 1500),
    ("daharki_ind","Daharki Industrial Cluster (Mari/Engro)",     "industrial", 28.1670, 69.7330, 2000),
    ("daharki_vil","Rural settlements outside Daharki",           "village",    28.1950, 69.6900, 1500),
]

YEARS = list(range(2016, 2027))


def fetch_real_viirs(aoi, years):
    """
    Pulls monthly VIIRS VNP46A2/VCMSLCFG composites for an AOI and returns the
    annual mean radiance (nW/cm^2/sr). Requires earthengine-api + geemap and
    prior `earthengine authenticate`.
    """
    try:
        import ee
        import geemap  # noqa: F401
    except ImportError as e:
        raise SystemExit(
            "Real mode needs earthengine-api and geemap.\n"
            "Run: pip install earthengine-api geemap\n"
            "Then: earthengine authenticate\n"
            f"(import error: {e})"
        )

    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()

    zone_id, name, ztype, lat, lon, buffer_m = aoi
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(buffer_m)

    results = []
    collection = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
    for year in years:
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        yearly_mean_img = collection.filterDate(start, end).select("avg_rad").mean()
        stat = yearly_mean_img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=500, maxPixels=1e9
        )
        val = stat.get("avg_rad").getInfo()
        results.append((year, val))
    return results


def generate_demo_series(aoi, years, seed):
    """
    Synthetic-but-realistic radiance series: industrial zones show strong
    compounding growth (new plants, flaring, expansion); villages stay flat
    with mild noise. This mirrors the real-world pattern the project expects
    to find, WITHOUT claiming to be real measured data.
    """
    rng = random.Random(seed)
    zone_id, name, ztype, lat, lon, buffer_m = aoi
    base = rng.uniform(8, 15) if ztype == "industrial" else rng.uniform(0.5, 2.0)
    annual_growth = rng.uniform(0.06, 0.11) if ztype == "industrial" else rng.uniform(-0.01, 0.02)

    series = []
    value = base
    for i, year in enumerate(years):
        noise = rng.uniform(-0.05, 0.05)
        value = value * (1 + annual_growth + noise) if i > 0 else value
        series.append((year, round(value, 3)))
    return series


def build_dataset(mode="demo"):
    rows = []
    for idx, aoi in enumerate(AOIS):
        zone_id, name, ztype, lat, lon, buffer_m = aoi
        if mode == "real":
            series = fetch_real_viirs(aoi, YEARS)
        else:
            series = generate_demo_series(aoi, YEARS, seed=idx)

        base_val = series[0][1] if series[0][1] else 1e-6
        for year, val in series:
            pct_change = None if val is None else round(((val - base_val) / base_val) * 100, 2)
            rows.append({
                "year": year,
                "zone_id": zone_id,
                "zone_name": name,
                "zone_type": ztype,
                "mean_radiance": val,
                "pct_change_from_2016": pct_change,
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Ghotki VIIRS nightlight analysis")
    parser.add_argument("--mode", choices=["demo", "real"], default="demo",
                         help="demo = synthetic data for pipeline testing; real = live Earth Engine pull")
    parser.add_argument("--out", default="data/nightlight_scores.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    rows = build_dataset(mode=args.mode)

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "year", "zone_id", "zone_name", "zone_type",
            "mean_radiance", "pct_change_from_2016"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{args.mode.upper()}] Wrote {len(rows)} rows to {args.out}")
    print("Zones covered:")
    for aoi in AOIS:
        print(f"  - {aoi[1]} ({aoi[2]}) @ {aoi[3]}, {aoi[4]}")


if __name__ == "__main__":
    main()
