# Riftic — The Ghotki Industrial Conversion Atlas

![Python](https://img.shields.io/badge/python-3.12-blue)
![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active--development-orange)

**Live dashboard:** [riftic.streamlit.app](#) &nbsp;·&nbsp; **Author:** Hassaan Moiz

> Ghotki, Sindh produces an estimated 71% of Pakistan's natural gas — and receives back roughly 24.55% of the national fiscal pool. Riftic measures that gap using public satellite and financial data, and turns it into one comparable number per company: the **Ghotki Industrial Conversion Index (GICI)**.

---

## Table of Contents
- [What this is](#what-this-is)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Getting real data](#getting-real-data)
- [Project structure](#project-structure)
- [The index, explained](#the-index-explained)
- [Roadmap](#roadmap)
- [Sources](#sources)
- [License](#license)

## What this is

Ghotki hosts some of Pakistan's largest gas and fertilizer infrastructure — Mari Field, Qadirpur, and FFC's flagship plant — yet remains among the poorest, least industrialised districts in Sindh. Riftic is the technical backbone behind a research project measuring that gap directly, combining two public data sources into one auditable score per company:

1. **NASA/NOAA VIIRS nightlight radiance** (2016–2026), comparing industrial zones against their nearest villages
2. **Corporate CSR & financial disclosures** from OGDCL, Mari Petroleum, Engro, and FFC, classified as *structural* (durable local capability) vs. *superficial* (short-term relief)

## How it works

```
nightlight_analysis.py   →   data/nightlight_scores.csv
csr_scraper.py           →   data/csr_disclosures.csv
conversion_index.py      →   data/conversion_index.csv
dashboard/app.py         →   reads all three, renders the public dashboard
```

## Quick start

Runs today on labelled demo data — no accounts or downloads needed:

```bash
pip install -r requirements.txt

python nightlight_analysis.py --mode demo
python csr_scraper.py
python conversion_index.py

streamlit run dashboard/app.py
```

## Getting real data

See [`docs/real-data-setup.md`](#) for the full walkthrough — in short:
- **Nightlight data**: free Earth Engine account → `earthengine authenticate` → `python nightlight_analysis.py --mode real`
- **CSR data**: download annual report PDFs into `reports/` → `python csr_scraper.py --input_dir reports/`

## Project structure

```
riftic/
├── nightlight_analysis.py   # VIIRS satellite data pipeline
├── csr_scraper.py           # Corporate disclosure extraction
├── conversion_index.py      # Combines both into the GICI score
├── dashboard/
│   └── app.py                # Streamlit public dashboard
├── requirements.txt
├── LICENSE
└── README.md
```

## The index, explained

**Ghotki Industrial Conversion Index (GICI)** = 0.5 × Structural CSR Ratio + 0.5 × Local Growth Capture Score

| Component | What it measures |
|---|---|
| Structural CSR Ratio | Share of a company's CSR spend going to durable capability (training centres, infrastructure) vs. one-off relief |
| Local Growth Capture Score | How much of a company's own economic growth is mirrored in its nearest village's nightlight growth |

A low GICI is the resource-enclave signature this project is built to document: light and wealth stay inside the fence line.

## Roadmap

- [x] Working pipeline validated end-to-end on demo data
- [x] Public dashboard (3 tabs: nightlight, CSR, index)
- [ ] Real VIIRS data via Earth Engine
- [ ] Real CSR data from downloaded annual reports
- [ ] Public GitHub + live Streamlit deployment
- [ ] Policy brief distributed to Sindh Assembly & local media

## Sources

NASA/NOAA VIIRS · Pakistan Bureau of Statistics · National Finance Commission (NFC) Award, Government of Pakistan · Pakistan Poverty Alleviation Fund & Sustainable Development Policy Institute · Dawn · The Express Tribune

## License

MIT — see [LICENSE](LICENSE).
