"""
Riftic — The Ghotki Industrial Conversion Atlas -- public dashboard.
Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

st.set_page_config(page_title="Riftic — Ghotki Industrial Conversion Atlas", layout="wide")

BG = "#0E1116"
PANEL = "#161B22"
ACCENT = "#F2A65A"   # gas-flare amber
ACCENT2 = "#4C9F70"  # village green
TEXT = "#E6E6E6"
MUTED = "#8A93A3"

st.markdown(f"""
<style>
.stApp {{ background-color: {BG}; color: {TEXT}; }}
h1, h2, h3 {{ color: {TEXT}; font-family: 'Georgia', serif; }}
.metric-box {{
    background-color: {PANEL}; border-radius: 6px; padding: 1rem 1.2rem;
    border-left: 3px solid {ACCENT};
}}
</style>
""", unsafe_allow_html=True)

st.title("Riftic — The Ghotki Industrial Conversion Atlas")
st.caption("Mapping the gap between extractive wealth and local industrial capability "
           "in Pakistan's gas capital -- Ghotki District, Sindh.")


def load(path, cols):
    full = os.path.join(DATA_DIR, path)
    if not os.path.exists(full):
        st.warning(f"Missing `{path}` -- run the pipeline scripts first (see README).")
        return pd.DataFrame(columns=cols)
    return pd.read_csv(full)


night = load("nightlight_scores.csv",
             ["year", "zone_id", "zone_name", "zone_type", "mean_radiance", "pct_change_from_2016"])
csr = load("csr_disclosures.csv",
           ["company", "year", "category", "snippet", "amount_pkr_million", "classification"])
index_df = load("conversion_index.csv",
                 ["company", "structural_csr_ratio", "local_growth_capture_score",
                  "ghotki_industrial_conversion_index"])

tab1, tab2, tab3 = st.tabs(["Nightlight Growth", "CSR: Structural vs Superficial", "Conversion Index"])

with tab1:
    st.subheader("Industrial zones vs. neighboring villages, 2016-2026")
    if not night.empty:
        fig = px.line(
            night, x="year", y="mean_radiance", color="zone_name",
            line_dash="zone_type",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            plot_bgcolor=PANEL, paper_bgcolor=BG, font_color=TEXT,
            legend_title_text="", height=480,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Radiance in nW/cm²/sr, a standard proxy for local economic activity. "
                   "Dashed = village, solid = industrial zone.")
    else:
        st.info("No nightlight data yet.")

with tab2:
    st.subheader("How CSR spending breaks down by company")
    if not csr.empty:
        csr_only = csr[csr["category"] == "csr"].copy()
        csr_only["amount_pkr_million"] = pd.to_numeric(csr_only["amount_pkr_million"], errors="coerce")
        grouped = csr_only.groupby(["company", "classification"])["amount_pkr_million"].sum().reset_index()
        fig2 = px.bar(
            grouped, x="company", y="amount_pkr_million", color="classification",
            color_discrete_map={"structural": ACCENT2, "superficial": ACCENT, "unclassified": MUTED},
            barmode="stack",
        )
        fig2.update_layout(plot_bgcolor=PANEL, paper_bgcolor=BG, font_color=TEXT, height=440)
        st.plotly_chart(fig2, use_container_width=True)
        with st.expander("See extracted snippets"):
            st.dataframe(csr_only[["company", "year", "snippet", "amount_pkr_million", "classification"]],
                         use_container_width=True)
    else:
        st.info("No CSR data yet.")

with tab3:
    st.subheader("Ghotki Industrial Conversion Index (GICI)")
    st.caption("0.5 × Structural CSR Ratio + 0.5 × Local Growth Capture Score. "
               "Low = classic resource-enclave signature: wealth and light stay inside the fence line.")
    if not index_df.empty:
        cols = st.columns(len(index_df))
        for c, (_, row) in zip(cols, index_df.iterrows()):
            gici = row["ghotki_industrial_conversion_index"]
            gici_str = f"{gici:.2f}" if pd.notnull(gici) else "N/A"
            c.markdown(f"""
            <div class="metric-box">
                <div style="color:{MUTED};font-size:0.85rem;">{row['company']}</div>
                <div style="font-size:2rem;font-weight:bold;color:{ACCENT};">{gici_str}</div>
            </div>
            """, unsafe_allow_html=True)
        st.write("")
        fig3 = px.bar(index_df.sort_values("ghotki_industrial_conversion_index"),
                       x="ghotki_industrial_conversion_index", y="company", orientation="h",
                       color_discrete_sequence=[ACCENT])
        fig3.update_layout(plot_bgcolor=PANEL, paper_bgcolor=BG, font_color=TEXT, height=350)
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(index_df, use_container_width=True)
    else:
        st.info("No index data yet -- run conversion_index.py.")

st.divider()
st.caption("Founder: Hassaan Moiz · Data: NASA/NOAA VIIRS VNP46A2 (2016-2026), "
           "company annual report disclosures · Riftic — The Ghotki Industrial Conversion Atlas")
