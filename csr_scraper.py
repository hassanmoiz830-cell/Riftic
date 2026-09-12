"""
csr_scraper.py
---------------
Part of Riftic — The Ghotki Industrial Conversion Atlas.

Extracts profit and CSR-spend figures from company annual report PDFs
(OGDCL, Mari Petroleum, Engro, FFC) and classifies each CSR line item as
STRUCTURAL (long-term capability building) or SUPERFICIAL (short-term relief).

WHY THIS IS A LOCAL/MANUAL-DOWNLOAD STEP
=========================================
Annual reports are published as PDFs on each company's investor-relations
page. Download the PDFs yourself and drop them in a folder, e.g.:

    reports/
        OGDCL_2023_AnnualReport.pdf
        MariPetroleum_2023_AnnualReport.pdf
        Engro_2023_AnnualReport.pdf
        FFC_2023_AnnualReport.pdf

Then run:
    python csr_scraper.py --input_dir reports/ --out data/csr_disclosures.csv

DEMO MODE
=========
If --input_dir has no PDFs (or doesn't exist), the script falls back to a
small labelled demo dataset so you can test the rest of the pipeline today.
"""

import argparse
import csv
import os
import re
import glob

STRUCTURAL_KEYWORDS = [
    "technical college", "vocational training", "training center", "training centre",
    "skills development", "scholarship", "industrial institute", "polytechnic",
    "water supply scheme", "infrastructure development", "road construction",
    "gas supply scheme", "electrification", "hospital", "school building",
    "capacity building", "apprenticeship",
]

SUPERFICIAL_KEYWORDS = [
    "medical camp", "food distribution", "ration bags", "relief goods",
    "tree plantation drive", "blood donation", "iftar", "sports gala",
    "awareness session", "one-day", "annual donation", "sponsorship of event",
    "flood relief", "cash donation",
]

MONEY_PATTERN = re.compile(
    r"(?:PKR|Rs\.?|Rupees)?\s?([\d,]+(?:\.\d+)?)\s?(million|billion|mn|bn)?",
    re.IGNORECASE,
)


def classify_snippet(text):
    text_low = text.lower()
    structural_hits = sum(1 for k in STRUCTURAL_KEYWORDS if k in text_low)
    superficial_hits = sum(1 for k in SUPERFICIAL_KEYWORDS if k in text_low)
    if structural_hits == 0 and superficial_hits == 0:
        return "unclassified"
    return "structural" if structural_hits >= superficial_hits else "superficial"


def extract_money(text):
    match = MONEY_PATTERN.search(text)
    if not match:
        return None
    amount, unit = match.groups()
    try:
        value = float(amount.replace(",", ""))
    except ValueError:
        return None
    if unit and unit.lower() in ("billion", "bn"):
        value *= 1000
    return round(value, 2)


def parse_pdf(path):
    import pdfplumber

    company = os.path.basename(path).split("_")[0]
    year_match = re.search(r"(20\d{2})", os.path.basename(path))
    year = year_match.group(1) if year_match else "unknown"

    findings = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for para in text.split("\n"):
                para_low = para.lower()
                if "csr" in para_low or "corporate social responsibility" in para_low:
                    findings.append({
                        "company": company,
                        "year": year,
                        "category": "csr",
                        "snippet": para.strip()[:200],
                        "amount_pkr_million": extract_money(para),
                        "classification": classify_snippet(para),
                    })
                elif "profit after tax" in para_low or "net profit" in para_low:
                    findings.append({
                        "company": company,
                        "year": year,
                        "category": "profit",
                        "snippet": para.strip()[:200],
                        "amount_pkr_million": extract_money(para),
                        "classification": "n/a",
                    })
    return findings


DEMO_ROWS = [
    {"company": "FFC", "year": "2023", "category": "csr",
     "snippet": "FFC established a technical training center for youth in Mirpur Mathelo.",
     "amount_pkr_million": 45.0, "classification": "structural"},
    {"company": "FFC", "year": "2023", "category": "profit",
     "snippet": "Profit after tax for the year stood at PKR 34,500 million.",
     "amount_pkr_million": 34500.0, "classification": "n/a"},
    {"company": "MariPetroleum", "year": "2023", "category": "csr",
     "snippet": "Company distributed ration bags during a one-day medical camp in Daharki.",
     "amount_pkr_million": 8.2, "classification": "superficial"},
    {"company": "MariPetroleum", "year": "2023", "category": "profit",
     "snippet": "Net profit for the period was PKR 61,200 million.",
     "amount_pkr_million": 61200.0, "classification": "n/a"},
    {"company": "OGDCL", "year": "2023", "category": "csr",
     "snippet": "OGDCL funded a vocational training institute and gas supply scheme near Qadirpur.",
     "amount_pkr_million": 120.0, "classification": "structural"},
    {"company": "OGDCL", "year": "2023", "category": "profit",
     "snippet": "Net profit after tax amounted to PKR 88,900 million.",
     "amount_pkr_million": 88900.0, "classification": "n/a"},
    {"company": "Engro", "year": "2023", "category": "csr",
     "snippet": "Engro sponsored a tree plantation drive and annual sports gala in Daharki.",
     "amount_pkr_million": 5.5, "classification": "superficial"},
    {"company": "Engro", "year": "2023", "category": "profit",
     "snippet": "Profit after tax reported at PKR 40,100 million.",
     "amount_pkr_million": 40100.0, "classification": "n/a"},
]


def main():
    parser = argparse.ArgumentParser(description="Ghotki CSR/financial disclosure extractor")
    parser.add_argument("--input_dir", default="reports/")
    parser.add_argument("--out", default="data/csr_disclosures.csv")
    args = parser.parse_args()

    pdf_paths = glob.glob(os.path.join(args.input_dir, "*.pdf")) if os.path.isdir(args.input_dir) else []

    if not pdf_paths:
        print(f"No PDFs found in '{args.input_dir}'. Falling back to DEMO data "
              f"so you can test the pipeline. Drop real annual report PDFs "
              f"into that folder and re-run for real results.")
        rows = DEMO_ROWS
    else:
        rows = []
        for path in pdf_paths:
            print(f"Parsing {path} ...")
            rows.extend(parse_pdf(path))
        if not rows:
            print("No CSR/profit mentions found in the PDFs provided -- "
                  "check the extraction keywords or PDF text layer.")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "company", "year", "category", "snippet", "amount_pkr_million", "classification"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
