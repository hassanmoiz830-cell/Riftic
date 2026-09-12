"""
conversion_index.py
--------------------
Part of Riftic — The Ghotki Industrial Conversion Atlas.

Combines the two data layers into one number per company/year:

    Ghotki Industrial Conversion Index (GICI)
    = 0.5 * (Structural CSR Ratio)  +  0.5 * (Local Growth Capture Score)

Usage:
    python conversion_index.py \
        --nightlight data/nightlight_scores.csv \
        --csr data/csr_disclosures.csv \
        --out data/conversion_index.csv
"""

import argparse
import csv
from collections import defaultdict

ZONE_PAIRS = {
    "ffc3":       {"village": "mmathelo",    "company": "FFC"},
    "qadirpur":   {"village": "ghotki_town", "company": "OGDCL"},
    "daharki_ind":{"village": "daharki_vil", "company": "MariPetroleum"},
}


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def structural_csr_ratio(csr_rows):
    totals = defaultdict(lambda: {"structural": 0.0, "superficial": 0.0})
    for row in csr_rows:
        if row["category"] != "csr":
            continue
        amt = row.get("amount_pkr_million")
        if not amt:
            continue
        amt = float(amt)
        cls = row["classification"]
        if cls in ("structural", "superficial"):
            totals[row["company"]][cls] += amt

    ratios = {}
    for company, vals in totals.items():
        total = vals["structural"] + vals["superficial"]
        ratios[company] = round(vals["structural"] / total, 3) if total > 0 else None
    return ratios


def growth_by_zone(nightlight_rows):
    latest = defaultdict(lambda: (-1, None))
    for row in nightlight_rows:
        year = int(row["year"])
        pct = row["pct_change_from_2016"]
        pct = float(pct) if pct not in (None, "") else None
        if year > latest[row["zone_id"]][0]:
            latest[row["zone_id"]] = (year, pct)
    return {zone: val[1] for zone, val in latest.items()}


def local_capture_score(growth):
    scores = {}
    for industrial_zone, meta in ZONE_PAIRS.items():
        village_zone = meta["village"]
        ind_growth = growth.get(industrial_zone)
        vil_growth = growth.get(village_zone)
        if ind_growth is None or vil_growth is None or ind_growth <= 0:
            scores[meta["company"]] = None
            continue
        ratio = max(0.0, vil_growth) / ind_growth
        scores[meta["company"]] = round(min(ratio, 1.0), 3)
    return scores


def main():
    parser = argparse.ArgumentParser(description="Compute Ghotki Industrial Conversion Index")
    parser.add_argument("--nightlight", default="data/nightlight_scores.csv")
    parser.add_argument("--csr", default="data/csr_disclosures.csv")
    parser.add_argument("--out", default="data/conversion_index.csv")
    args = parser.parse_args()

    nightlight_rows = load_csv(args.nightlight)
    csr_rows = load_csv(args.csr)

    csr_ratios = structural_csr_ratio(csr_rows)
    growth = growth_by_zone(nightlight_rows)
    capture_scores = local_capture_score(growth)

    companies = set(csr_ratios) | set(capture_scores)
    out_rows = []
    for company in sorted(companies):
        csr_r = csr_ratios.get(company)
        cap_s = capture_scores.get(company)
        if csr_r is not None and cap_s is not None:
            gici = round(0.5 * csr_r + 0.5 * cap_s, 3)
        else:
            gici = None
        out_rows.append({
            "company": company,
            "structural_csr_ratio": csr_r,
            "local_growth_capture_score": cap_s,
            "ghotki_industrial_conversion_index": gici,
        })

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "company", "structural_csr_ratio", "local_growth_capture_score",
            "ghotki_industrial_conversion_index"
        ])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} company scores to {args.out}\n")
    for row in out_rows:
        print(f"  {row['company']:<15} GICI = {row['ghotki_industrial_conversion_index']}"
              f"  (structural CSR: {row['structural_csr_ratio']}, local capture: {row['local_growth_capture_score']})")


if __name__ == "__main__":
    main()
