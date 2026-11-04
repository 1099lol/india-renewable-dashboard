"""
app.py — Deconstructing India's Clean Energy Transition
=========================================================
Interactive Streamlit dashboard for the WAS Group 3 project.

How it works (in plain English)
-------------------------------
1. `data_loader.py` reads the Excel workbook that sits next to this file.
2. Every statistical result (PCA, K-Means clusters, regression line) is READ
   from the workbook. Nothing is re-estimated here.
3. Streamlit turns this Python script into a web page. Each time a visitor
   changes a dropdown or slider, Streamlit re-runs the script and redraws
   the charts (Plotly) with the new selection.

Run locally:   streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure Python can find data_loader.py (it sits in the same folder as this file),
# however the app is started.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from data_loader import (
    CATEGORY_COLUMNS,
    WORKBOOK_NAME,
    WorkbookError,
    category_totals_by_year,
    cluster_shares,
    load_project_data,
)

# ==========================================================================
# 1. PAGE SETUP AND VISUAL STYLE
# ==========================================================================
st.set_page_config(
    page_title="India Renewable Energy | State Profiles Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Colour palette: soft sage, white and charcoal with a leaf-green accent
# (greentech aesthetic). Variable names are kept from the first version so the
# rest of the code did not need to change: NAVY now holds the charcoal text colour.
NAVY = "#1E211D"          # main text / charcoal
NAVY_SOFT = "#3B403A"     # secondary charcoal (lines, dark fills)
INK_MUTED = "#6D736B"     # muted text
GREEN = "#6BA539"         # leaf-green accent (fills, lines)
GREEN_DARK = "#4A7A22"    # darker green for text on light backgrounds
GREEN_TINT = "#EAF3E0"    # pale green chip / note background
SAGE = "#CFD9CB"          # hero panel
PAGE = "#EEF0EC"          # page background
GRID = "#E9ECE6"          # chart gridlines and hairlines
AMBER = "#E0902B"         # Cluster 4 / caution

# Colours for the five energy categories (meaningful, not decorative):
# sunlit lime for solar, charcoal for wind (the lime/charcoal pairing of the
# aesthetic), deep leaf for biomass, mist blue for water, stone for waste.
CATEGORY_COLORS = {
    "Solar": "#9BC53D",
    "Wind": "#2E332D",
    "Biomass": "#4E7F2E",
    "Small hydro": "#7FA7B3",
    "Waste-to-energy": "#BFB197",
}
# Colours for the four K-Means clusters. Cluster 4 (the key finding) is amber.
CLUSTER_COLORS = {1: GREEN, 2: "#AEB4AB", 3: "#2E332D", 4: AMBER}
CLUSTER_TINTS = {1: (GREEN_TINT, GREEN_DARK), 2: ("#EDEFEC", "#4F554D"),
                 3: ("#E6E8E5", "#1E211D"), 4: ("#FCEFDD", "#8A5410")}

# Simple line icons (drawn as SVG) for the overview KPI cards.
_SVG = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{}</svg>')
ICONS = {
    "bolt": _SVG.format('<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>'),
    "pin": _SVG.format('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
    "groups": _SVG.format('<circle cx="7" cy="7" r="3"/><circle cx="17" cy="7" r="3"/>'
                          '<circle cx="7" cy="17" r="3"/><circle cx="17" cy="17" r="3"/>'),
    "layers": _SVG.format('<path d="M12 3 2 8l10 5 10-5-10-5z"/><path d="m2 16 10 5 10-5"/>'),
}

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&display=swap');

html, body, .stApp, button, input, textarea, select {{
  font-family: 'Geist', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
.stApp {{ background: {PAGE}; color: {NAVY}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container, [data-testid="stMainBlockContainer"] {{
  padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1380px;
}}
h1, h2, h3, h4 {{ color: {NAVY}; letter-spacing: -0.015em; font-weight: 500; }}
p, li {{ line-height: 1.55; }}

/* ---------- Hero panel (sage, with a frosted card) ---------- */
.hero {{
  background: {SAGE}; border-radius: 26px; padding: 30px 34px 28px; margin-bottom: 18px;
  display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 34px; align-items: end;
}}
.hero .crumb {{ color: #5A6357; font-size: 0.85rem; margin: 0 0 14px; }}
.hero h1 {{ color: {NAVY}; font-size: 2.35rem; line-height: 1.08; font-weight: 300;
           letter-spacing: -0.03em; margin: 0 0 12px; padding: 0; }}
.hero .sub {{ color: #4E574B; font-size: 0.98rem; margin: 0; }}
.glass {{ background: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.85);
          border-radius: 20px; padding: 18px 20px; }}
.glass .g-label {{ color: #4E574B; font-size: 0.85rem; }}
.glass .g-val {{ font-size: 2.2rem; font-weight: 400; letter-spacing: -0.03em; color: {NAVY};
                 font-variant-numeric: tabular-nums; margin: 2px 0 12px; }}
.glass .g-val span {{ font-size: 1rem; color: #4E574B; margin-left: 4px; }}
.mix-bar {{ display: flex; height: 12px; border-radius: 6px; overflow: hidden; background: {NAVY}; gap: 2px; }}
.mix-bar span {{ display: block; min-width: 3px; }}
.mix-legend {{ display: flex; flex-wrap: wrap; gap: 6px 14px; margin-top: 10px; font-size: 0.8rem; color: #4E574B; }}
.mix-legend i {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
.mix-legend b {{ color: {NAVY}; font-weight: 500; font-variant-numeric: tabular-nums; }}
@media (max-width: 900px) {{ .hero {{ grid-template-columns: 1fr; }} .hero h1 {{ font-size: 1.8rem; }} }}

/* ---------- KPI cards ---------- */
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 4px 0 14px; }}
.kpi {{ background: #fff; border-radius: 20px; padding: 16px 18px 14px; position: relative; }}
.kpi .label {{ color: {INK_MUTED}; font-size: 0.84rem; margin-bottom: 6px; padding-right: 40px; }}
.kpi .label .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px; }}
.kpi .value {{ color: {NAVY}; font-size: 1.75rem; font-weight: 400; letter-spacing: -0.025em;
              font-variant-numeric: tabular-nums; line-height: 1.2; }}
.kpi .note {{ color: {INK_MUTED}; font-size: 0.78rem; margin-top: 6px; line-height: 1.4; }}
.kpi .icon {{ position: absolute; top: 14px; right: 14px; width: 34px; height: 34px; border-radius: 50%;
             background: {PAGE}; color: {NAVY}; display: flex; align-items: center; justify-content: center; }}
.kpi.guide .text {{ color: {NAVY}; font-size: 1.02rem; font-weight: 500; line-height: 1.4; }}

/* ---------- Pills / chips ---------- */
.chip {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px;
         font-size: 0.8rem; font-weight: 500; }}
.chip i {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; }}

/* ---------- Cluster cards ---------- */
.cluster-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; margin: 6px 0 16px; }}
.ccard {{ background: #fff; border-radius: 20px; padding: 16px 18px; }}
.ccard .cname {{ color: {NAVY}; font-weight: 500; font-size: 1rem; margin: 10px 0 10px; line-height: 1.3; min-height: 2.6em; }}
.ccard table {{ width: 100%; font-size: 0.84rem; border-collapse: collapse; }}
.ccard td {{ padding: 4px 0; color: {INK_MUTED}; border: none; border-top: 1px solid {GRID}; }}
.ccard td.v {{ text-align: right; color: {NAVY}; font-weight: 500; font-variant-numeric: tabular-nums; }}

/* ---------- Notes and callouts ---------- */
.note-box {{ background: #fff; border-radius: 16px; padding: 13px 18px; font-size: 0.9rem; color: {NAVY}; margin: 6px 0 14px; }}
.note-box.green {{ background: {GREEN_TINT}; }}
.note-box.amber {{ background: #FCEFDD; color: #4A3210; }}
.note-box b {{ font-weight: 600; }}
.state-head {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; margin: 8px 0 12px; }}
.state-head h2 {{ margin: 0; padding: 0; font-size: 1.9rem; font-weight: 400; letter-spacing: -0.025em; }}
.muted {{ color: {INK_MUTED}; font-size: 0.88rem; }}
.section-title {{ font-size: 1.2rem; font-weight: 500; color: {NAVY}; margin: 22px 0 2px; letter-spacing: -0.01em; }}
.section-sub {{ color: {INK_MUTED}; font-size: 0.88rem; margin: 0 0 10px; }}

/* ---------- Tabs as a pill switcher ---------- */
[data-testid="stTabs"] [role="tablist"] {{ gap: 4px; background: #fff; padding: 5px; border-radius: 999px;
  width: fit-content; max-width: 100%; border: none; box-shadow: none; }}
[data-testid="stTab"] {{ border-radius: 999px; padding: 8px 18px; border: none; }}
[data-testid="stTab"] p {{ font-size: 0.95rem; font-weight: 500; color: {INK_MUTED}; }}
[data-testid="stTab"][aria-selected="true"] {{ background: {NAVY}; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: #fff; }}
[data-testid="stTab"]::after, [data-testid="stTab"]::before {{ display: none; }}
[data-testid="stTabs"] .react-aria-SelectionIndicator,
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{ display: none; }}

/* ---------- Chart cards: every card() container gets a st-key-card_N class ---------- */
[class*="st-key-card_"] {{ background: #fff; border: none !important; border-radius: 22px; padding: 18px 20px; }}
[data-testid="stExpander"] details {{ background: #fff; border-radius: 16px; border-color: transparent; }}

/* ---------- Dark sidebar ---------- */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {{ color: #F2F4EF; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ==========================================================================
# 2. SMALL HELPERS (formatting, HTML blocks, chart styling)
# ==========================================================================
def html(block: str) -> None:
    """Render an HTML snippet. Lines are stripped so Markdown does not treat them as code."""
    st.markdown("".join(line.strip() for line in block.splitlines()), unsafe_allow_html=True)


def fmt_capacity(gw: float) -> str:
    """Show large values in GW and small values in MW so they stay readable."""
    if pd.isna(gw):
        return "Not reported"
    return f"{gw:,.2f} GW" if gw >= 1 else f"{gw * 1000:,.1f} MW"


def fmt_gsdp(lakh_crore: float) -> str:
    if pd.isna(lakh_crore):
        return "Not reported"
    if lakh_crore < 0.1:
        return f"₹{lakh_crore * 1e5:,.0f} crore"
    return f"₹{lakh_crore:,.2f} lakh crore"


def fmt_population(millions: float) -> str:
    if pd.isna(millions):
        return "Not reported"
    return f"{millions:,.2f} million" if millions >= 1 else f"{millions * 1000:,.0f} thousand"


def pct(value: float) -> str:
    """Percentage with one decimal, or two decimals for very small shares (e.g. 0.04%)."""
    return f"{value:.2f}%" if 0 < value < 0.1 else f"{value:.1f}%"


def kpi_cards(cards: list[tuple], accent: str | None = None) -> None:
    """
    cards = [(label, value, note), ...] or [(label, value, note, icon_name), ...]
    rendered as a responsive grid of rounded white cards. `accent` adds a
    coloured dot before each label (used for cluster colours).
    """
    dot = f'<span class="dot" style="background:{accent}"></span>' if accent else ""
    items = ""
    for card in cards:
        label, value, note_text = card[:3]
        icon = f'<div class="icon">{ICONS[card[3]]}</div>' if len(card) > 3 else ""
        items += (f'<div class="kpi">{icon}<div class="label">{dot}{label}</div>'
                  f'<div class="value">{value}</div><div class="note">{note_text}</div></div>')
    html(f'<div class="kpi-grid">{items}</div>')


_card_count = 0


def card():
    """A white rounded card for charts. Each gets a unique key so CSS can style it."""
    global _card_count
    _card_count += 1
    return st.container(border=True, key=f"card_{_card_count}")


def chip(text: str, cluster: int | None = None, color: str = GREEN) -> str:
    """Small rounded status pill, e.g. the cluster label next to a state name."""
    if cluster is not None:
        bg, fg = CLUSTER_TINTS[cluster]; color = CLUSTER_COLORS[cluster]
    else:
        bg, fg = GREEN_TINT, GREEN_DARK
    return f'<span class="chip" style="background:{bg};color:{fg}"><i style="background:{color}"></i>{text}</span>'


def note(text: str, kind: str = "") -> None:
    html(f'<div class="note-box {kind}">{text}</div>')


def section(title: str, subtitle: str = "") -> None:
    sub = f'<p class="section-sub">{subtitle}</p>' if subtitle else ""
    html(f'<div class="section-title">{title}</div>{sub}')


def style_fig(fig: go.Figure, height: int = 380, legend: bool = True) -> go.Figure:
    """Apply one consistent, clean look to every Plotly chart."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="Geist, system-ui, sans-serif", size=13, color=NAVY),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=10, r=16, t=40, b=10),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID, font_size=12),
        showlegend=legend,
        # Legends sit below the plot so they never collide with the chart title.
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0, title_text="",
                    traceorder="normal"),
        title=dict(font=dict(size=16, color=NAVY, weight=500), x=0, xanchor="left"),
        barcornerradius=5,          # softly rounded bars
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor=GRID, griddash="dot", zerolinecolor=GRID, linecolor=GRID, tickfont_color=INK_MUTED)
    fig.update_yaxes(gridcolor=GRID, griddash="dot", zerolinecolor=GRID, linecolor=GRID, tickfont_color=INK_MUTED)
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


# ==========================================================================
# 3. LOAD THE DATA (cached, refreshes automatically if the workbook changes)
# ==========================================================================
DATA_PATH = Path(__file__).parent / WORKBOOK_NAME


@st.cache_data(show_spinner="Reading the project workbook…")
def get_data(path_str: str, modified_time: float):
    # `modified_time` is part of the cache key: replacing the workbook refreshes the data.
    return load_project_data(Path(path_str))


try:
    mtime = DATA_PATH.stat().st_mtime if DATA_PATH.exists() else 0.0
    data = get_data(str(DATA_PATH), mtime)
except WorkbookError as err:
    st.error(f"**The dashboard could not read the workbook.** {err}")
    st.stop()
except Exception as err:  # unexpected problem: show details to help troubleshooting
    st.error("**Unexpected error while reading the workbook.**")
    st.exception(err)
    st.stop()

history = data.history
states = data.states
reg = data.regression
clusters = data.cluster_summary.set_index("Cluster")
CLUSTER_NAMES = clusters["Plain-English profile"].to_dict()
shares = cluster_shares(states)
national = category_totals_by_year(history)
pca = data.pca_variance.set_index("Component")

LATEST_YEAR = int(history["Year"].max())        # 2024
FIRST_YEAR = int(history["Year"].min())         # 2006
total_gw = states["Capacity GW"].sum()
n_states = states["State / UT"].nunique()
k = states["Cluster"].nunique()
pc1_var = pca.loc["PC1", "Variance %"] * 100
pc2_var = pca.loc["PC2", "Variance %"] * 100
pca_retained = pca.loc["PC2", "Cumulative %"] * 100
sil_k = data.silhouette.set_index("Chosen K")["Silhouette score"]

# 2024 category mix comes from the CLEAN DATA rows for the latest year.
mix_latest = national.set_index("Year").loc[LATEST_YEAR, list(CATEGORY_COLORS)]


def cluster_label(c: int) -> str:
    return f"Cluster {c}: {CLUSTER_NAMES[c]}"


# ==========================================================================
# 4. HEADER BAND (title + 2024 capacity mix strip)
# ==========================================================================
segments = "".join(
    f'<span style="flex:{v:.4f};background:{CATEGORY_COLORS[c]}" title="{c}: {v:,.2f} GW"></span>'
    for c, v in mix_latest.items()
)
legend_items = "".join(
    f'<span><i style="background:{CATEGORY_COLORS[c]}"></i>{c} <b>{v / total_gw * 100:.1f}%</b></span>'
    for c, v in mix_latest.items()
)
html(f"""
<div class="hero">
  <div>
    <p class="crumb">WAS Group 3 project dashboard</p>
    <h1>Deconstructing India's Clean Energy Transition</h1>
    <p class="sub">State-level renewable energy profiles, capacity and economic scale across {n_states} states and UTs</p>
  </div>
  <div class="glass">
    <div class="g-label">Reported renewable capacity, {LATEST_YEAR}</div>
    <div class="g-val">{total_gw:,.2f}<span>GW</span></div>
    <div class="mix-bar">{segments}</div>
    <div class="mix-legend">{legend_items}</div>
  </div>
</div>
""")


# ==========================================================================
# 5. SIDEBAR: method summary, scope and limitations (for first-time viewers)
# ==========================================================================
with st.sidebar:
    st.markdown("### About this dashboard")
    st.markdown(
        "This dashboard presents a completed academic analysis of renewable energy "
        f"capacity across India's states and Union Territories. All statistical results "
        f"are read directly from the project workbook."
    )
    st.markdown("#### The three methods")
    st.markdown(
        f"1. **PCA** reduces GSDP, population and capacity per million people (all logged and "
        f"standardised) to two scores that keep **{pca_retained:.2f}%** of the variation.\n"
        f"2. **K-Means (K = {k})** groups states on those two scores into descriptive profiles.\n"
        f"3. **Simple regression** describes how 2024 capacity relates to GSDP "
        f"(R² = {reg['r2']:.4f}). It is an association, not a forecast."
    )
    st.markdown("#### Data scope")
    st.markdown(
        f"- {LATEST_YEAR} cross-section of {n_states} states/UTs for all three methods.\n"
        f"- {FIRST_YEAR}–{LATEST_YEAR} history is shown for description only.\n"
        "- Five categories: solar, wind, biomass, small hydro, waste-to-energy. **Large hydro is excluded.**"
    )
    with st.expander("Limitations (from the workbook)"):
        for item in data.limitations:
            st.markdown(f"- {item.split('. ', 1)[-1]}")
    if data.source_note:
        st.caption(data.source_note.replace("•", "|"))


# ==========================================================================
# 6. TABS
# ==========================================================================
tab_overview, tab_state, tab_cluster, tab_history = st.tabs(
    ["National overview", "State explorer", "Cluster analysis", "Historical trends"]
)

# --------------------------------------------------------------------------
# TAB 1: NATIONAL OVERVIEW
# --------------------------------------------------------------------------
with tab_overview:
    kpi_cards([
        (f"Reported renewable capacity, {LATEST_YEAR}", f"{total_gw:,.2f} GW",
         "Solar, wind, biomass, small hydro and waste-to-energy. Large hydro excluded.", "bolt"),
        ("States and UTs analysed", f"{n_states}",
         f"One {LATEST_YEAR} observation each; used by all three methods.", "pin"),
        ("K-Means clusters", f"{k}",
         f"Silhouette score {sil_k.get(k, float('nan')):.3f} at K = {k}, with no single-state group.", "groups"),
        ("PCA variance retained", f"{pca_retained:.2f}%",
         f"PC1 {pc1_var:.2f}% (scale) + PC2 {pc2_var:.2f}% (intensity).", "layers"),
    ])

    left, right = st.columns([1.45, 1], gap="medium")
    with left:
        with card():
            latest = history[history["Year"] == LATEST_YEAR].copy()
            top10 = latest.nlargest(10, "Total capacity MW").iloc[::-1]
            fig = go.Figure()
            for col, name in CATEGORY_COLUMNS.items():
                fig.add_bar(
                    y=top10["State / UT"], x=top10[col] / 1000, name=name, orientation="h",
                    marker_color=CATEGORY_COLORS[name],
                    hovertemplate="<b>%{y}</b><br>" + name + ": %{x:,.2f} GW<extra></extra>",
                )
            fig.update_layout(barmode="stack", title=f"Top 10 states by reported capacity, {LATEST_YEAR}")
            fig.update_xaxes(title_text="Installed capacity (GW)")
            style_fig(fig, height=430)
            fig.update_layout(legend=dict(y=-0.2, yanchor="top", traceorder="normal"))
            show(fig)
            top10_share = top10["Total capacity MW"].sum() / 1000 / total_gw * 100
            st.caption(f"These ten states hold {top10_share:.1f}% of the {total_gw:,.2f} GW reported in {LATEST_YEAR}.")

    with right:
        with card():
            fig = go.Figure(go.Pie(
                labels=list(mix_latest.index), values=list(mix_latest.values), hole=0.58,
                marker=dict(colors=[CATEGORY_COLORS[c] for c in mix_latest.index], line=dict(color="#fff", width=2)),
                sort=False, direction="clockwise",
                text=[f"{v / total_gw * 100:.1f}%" if v / total_gw >= 0.03 else "" for v in mix_latest.values],
                textinfo="text",
                hovertemplate="<b>%{label}</b><br>%{value:,.2f} GW (%{percent})<extra></extra>",
            ))
            fig.update_layout(
                title=f"Capacity by category, {LATEST_YEAR}",
                annotations=[dict(text=f"<b>{total_gw:,.2f}</b><br>GW", x=0.5, y=0.5, showarrow=False,
                                  font=dict(size=18, color=NAVY))],
            )
            style_fig(fig, height=430)
            fig.update_layout(legend=dict(y=-0.12, yanchor="top"))
            show(fig)
            st.caption("Large hydro is not part of the dataset, so totals are lower than official all-renewable figures.")

    # ---------------- State ranking table ----------------
    section("State-wise ranking", f"All {n_states} states and UTs in {LATEST_YEAR}. Filter, sort by any column, or download.")
    metric_options = {
        "Renewable capacity (GW)": "Capacity GW",
        "Capacity per million people (MW)": "MW per million people",
        "GSDP (₹ lakh crore)": "GSDP ₹ lakh crore",
        "Population (million)": "Population millions",
    }
    c1, c2, c3 = st.columns([1.2, 1, 1.4])
    rank_by_label = c1.selectbox("Rank by", list(metric_options), key="rank_by")
    zones = sorted(states["Zone"].dropna().unique())
    zone_pick = c2.multiselect("Zone", zones, placeholder="All zones", key="rank_zone")
    cluster_pick = c3.multiselect(
        "Cluster", sorted(CLUSTER_NAMES), format_func=cluster_label, placeholder="All clusters", key="rank_cluster"
    )
    rank_col = metric_options[rank_by_label]

    table = states.copy()
    table["National rank"] = table[rank_col].rank(ascending=False, method="min").astype(int)
    if zone_pick:
        table = table[table["Zone"].isin(zone_pick)]
    if cluster_pick:
        table = table[table["Cluster"].isin(cluster_pick)]
    table = table.sort_values(rank_col, ascending=False)
    table = table[["National rank", "State / UT", "Zone", "Capacity GW", "MW per million people",
                   "GSDP ₹ lakh crore", "Population millions", "Cluster", "Cluster profile"]]

    if table.empty:
        st.info("No states match these filters. Clear a filter to see results.")
    else:
        max_val = float(states[rank_col].max())
        col_cfg = {
            "National rank": st.column_config.NumberColumn("Rank", width="small"),
            "Capacity GW": st.column_config.NumberColumn("Capacity (GW)", format="%.3f"),
            "MW per million people": st.column_config.NumberColumn("MW per million", format="%.2f"),
            "GSDP ₹ lakh crore": st.column_config.NumberColumn("GSDP (₹ lakh cr)", format="%.3f"),
            "Population millions": st.column_config.NumberColumn("Population (mn)", format="%.2f"),
            "Cluster": st.column_config.NumberColumn("Cluster", width="small"),
            "Cluster profile": st.column_config.TextColumn("Cluster profile"),
        }
        # Show the chosen ranking metric as an in-cell bar.
        col_cfg[rank_col] = st.column_config.ProgressColumn(
            rank_by_label, format="%.2f", min_value=0.0, max_value=max_val
        )
        st.dataframe(table, hide_index=True, width="stretch", column_config=col_cfg,
                     height=min(36 * (len(table) + 1) + 4, 520))
        st.download_button(
            "Download this table (CSV)", table.to_csv(index=False).encode("utf-8"),
            file_name=f"state_ranking_{LATEST_YEAR}.csv", mime="text/csv",
        )
    zero_states = states.loc[states["Capacity GW"] == 0, "State / UT"].tolist()
    if zero_states:
        note(f"<b>Data caution:</b> {', '.join(zero_states)} report zero capacity in {LATEST_YEAR}. "
             "These are kept as reported and should be verified against official records; "
             "they are not proof that no capacity exists.", "amber")


# --------------------------------------------------------------------------
# TAB 2: STATE EXPLORER
# --------------------------------------------------------------------------
with tab_state:
    state_list = sorted(states["State / UT"].unique())
    default_idx = state_list.index("Gujarat") if "Gujarat" in state_list else 0
    sel = st.selectbox("Select a state or Union Territory", state_list, index=default_idx, key="state_pick")
    row = states.set_index("State / UT").loc[sel]
    c = int(row["Cluster"])
    resid = row["Actual − fitted GW"]

    html(f"""
    <div class="state-head">
      <h2>{sel}</h2>
      <span class="muted">{row['Zone']} zone</span>
      {chip(cluster_label(c), cluster=c)}
    </div>""")

    kpi_cards([
        ("GSDP", fmt_gsdp(row["GSDP ₹ lakh crore"]), f"Rank {row['Rank: GSDP']} of {n_states}"),
        ("Population", fmt_population(row["Population millions"]), f"Rank {row['Rank: population']} of {n_states}"),
        (f"Renewable capacity, {LATEST_YEAR}", fmt_capacity(row["Capacity GW"]),
         f"Rank {row['Rank: capacity']} of {n_states}; {row['Capacity GW'] / total_gw * 100:.2f}% of national total"),
        ("Capacity per million people", f"{row['MW per million people']:,.2f} MW",
         f"Rank {row['Rank: intensity']} of {n_states}"),
    ])
    kpi_cards([
        ("K-Means cluster", f"Cluster {c}", CLUSTER_NAMES[c]),
        ("PCA coordinates (scaled)", f"{row['PC1 scaled']:+.3f}, {row['PC2 scaled']:+.3f}",
         "PC1 = economic and population scale; PC2 = renewable intensity"),
        ("Regression fitted value", f"{row['Reg. fitted GW']:,.3f} GW",
         "Capacity the 2024 line associates with this GSDP"),
        ("Regression residual", f"{resid:+,.3f} GW",
         ("Above" if resid > 0 else "Below") + " the 2024 regression line (actual minus fitted)"),
    ], accent=CLUSTER_COLORS[c])

    if row["Reg. fitted GW"] < 0:
        st.caption("A negative fitted value is a mathematical feature of the straight line at very small GSDP; "
                   "it is not a realistic capacity estimate.")
    if row["Capacity GW"] == 0:
        note(f"<b>Data caution:</b> {sel} reports zero capacity in {LATEST_YEAR}. Treat this as a figure to verify "
             "against official MNRE/CEA records, not as confirmed absence of capacity.", "amber")

    view = st.radio("History chart shows", ["Total capacity", "By category"], horizontal=True, key="state_hist_view")
    left, right = st.columns([1.15, 1], gap="medium")

    # ---------------- Historical chart for the selected state ----------------
    with left:
        with card():
            hs = history[history["State / UT"] == sel].set_index("Year")
            all_years = range(FIRST_YEAR, LATEST_YEAR + 1)
            hs = hs.reindex(all_years)          # missing years become blank, so gaps stay visible
            missing_years = [y for y in all_years if pd.isna(hs.loc[y, "Total capacity MW"])]

            fig = go.Figure()
            if view == "Total capacity":
                fig.add_scatter(
                    x=list(all_years), y=hs["Total capacity MW"], mode="lines+markers", name="Total",
                    line=dict(color=GREEN, width=3), marker=dict(size=6), connectgaps=False,
                    fill="tozeroy", fillcolor="rgba(107,165,57,0.12)",
                    hovertemplate="%{x}: %{y:,.1f} MW<extra></extra>",
                )
            else:
                for col, name in CATEGORY_COLUMNS.items():
                    fig.add_bar(x=list(all_years), y=hs[col], name=name, marker_color=CATEGORY_COLORS[name],
                                hovertemplate="%{x}<br>" + name + ": %{y:,.1f} MW<extra></extra>")
                fig.update_layout(barmode="stack")
            fig.update_layout(title=f"{sel}: reported capacity, {FIRST_YEAR}–{LATEST_YEAR}")
            fig.update_yaxes(title_text="Capacity (MW)", rangemode="tozero", tickformat=",")
            fig.update_xaxes(dtick=2)
            style_fig(fig, height=400, legend=(view == "By category"))
            show(fig)
            caption = "Source: CLEAN DATA sheet. Descriptive history only; not part of the 2024 regression."
            if missing_years:
                caption += f" No record in the dataset for: {', '.join(map(str, missing_years))} (shown as gaps)."
            st.caption(caption)

    # ---------------- Where the state sits on the 2024 regression ----------------
    with right:
        with card():
            fig = go.Figure()
            x_line = [0, states["GSDP ₹ lakh crore"].max() * 1.05]
            fig.add_scatter(
                x=x_line, y=[reg["intercept"] + reg["slope"] * x for x in x_line], mode="lines",
                name="2024 regression line", line=dict(color=NAVY_SOFT, width=2, dash="dash"), hoverinfo="skip",
            )
            for cl in sorted(CLUSTER_NAMES):
                sub = states[(states["Cluster"] == cl) & (states["State / UT"] != sel)]
                fig.add_scatter(
                    x=sub["GSDP ₹ lakh crore"], y=sub["Capacity GW"], mode="markers", name=f"Cluster {cl}",
                    marker=dict(color=CLUSTER_COLORS[cl], size=9, opacity=0.75, line=dict(color="#fff", width=1)),
                    customdata=sub[["State / UT", "Reg. fitted GW", "Actual − fitted GW"]],
                    hovertemplate="<b>%{customdata[0]}</b><br>GSDP ₹%{x:.2f} lakh cr<br>Actual %{y:.2f} GW"
                                  "<br>Fitted %{customdata[1]:.2f} GW<br>Residual %{customdata[2]:+.2f} GW<extra></extra>",
                )
            fig.add_scatter(
                x=[row["GSDP ₹ lakh crore"]], y=[row["Capacity GW"]], mode="markers+text", name=sel,
                text=[sel], textposition="top center", textfont=dict(color=NAVY, size=13),
                marker=dict(color=CLUSTER_COLORS[c], size=16, line=dict(color=NAVY, width=2.5)), cliponaxis=False,
                hovertemplate=f"<b>{sel}</b><br>Actual %{{y:.2f}} GW<br>Fitted {row['Reg. fitted GW']:.2f} GW<extra></extra>",
            )
            # Vertical connector showing the residual for the selected state.
            fig.add_shape(type="line", x0=row["GSDP ₹ lakh crore"], x1=row["GSDP ₹ lakh crore"],
                          y0=row["Reg. fitted GW"], y1=row["Capacity GW"], line=dict(color=NAVY, width=1.5, dash="dot"))
            fig.update_layout(title="Where this state sits on the 2024 regression")
            fig.update_xaxes(title_text="GSDP (₹ lakh crore)")
            fig.update_yaxes(title_text="Capacity (GW)")
            style_fig(fig, height=400)
            fig.update_layout(legend=dict(y=-0.22, yanchor="top"))
            show(fig)
            st.caption(
                f"Capacity = {reg['intercept']:.4f} + {reg['slope']:.4f} × GSDP  |  r = {reg['r']:.4f}  |  "
                f"R² = {reg['r2']:.4f}  |  adj. R² = {reg['adj_r2']:.4f}  |  RMSE = {reg['rmse']:.3f} GW  |  n = {reg['n']}. "
                "Descriptive association for 2024, not a forecast or causal estimate."
            )

    with st.expander(f"Data notes for {sel}"):
        hs_notes = history[(history["State / UT"] == sel) & (history["Data note"] == "Negative reported change")]
        if hs_notes.empty:
            st.write("No year-on-year decreases in reported capacity are flagged for this state.")
        else:
            st.write("The workbook flags these year-on-year decreases in reported capacity. "
                     "They may reflect source revisions or reporting changes rather than real decommissioning:")
            st.dataframe(
                hs_notes[["Year", "Total capacity MW", "Annual net change MW"]].rename(
                    columns={"Total capacity MW": "Capacity (MW)", "Annual net change MW": "Change vs previous year (MW)"}),
                hide_index=True, width="stretch",
                column_config={"Year": st.column_config.NumberColumn(format="%d"),
                               "Capacity (MW)": st.column_config.NumberColumn(format="%.3f"),
                               "Change vs previous year (MW)": st.column_config.NumberColumn(format="%.3f")},
            )


# --------------------------------------------------------------------------
# TAB 3: CLUSTER ANALYSIS
# --------------------------------------------------------------------------
with tab_cluster:
    note(f"States were grouped with <b>K-Means (K = {k})</b> on their two PCA scores. Cluster numbers are labels, "
         "<b>not a ranking</b>: a higher number does not mean better or worse performance.")

    # ---------------- Four cluster summary cards ----------------
    cards = ""
    for cl in sorted(CLUSTER_NAMES):
        r = clusters.loc[cl]
        cards += f"""
        <div class="ccard">
          {chip(f"Cluster {cl}", cluster=cl)}
          <div class="cname">{CLUSTER_NAMES[cl]}</div>
          <table>
            <tr><td>States / UTs</td><td class="v">{int(r['States'])}</td></tr>
            <tr><td>Average GSDP</td><td class="v">₹{r['Avg GSDP ₹ lakh cr']:.2f} lakh cr</td></tr>
            <tr><td>Average capacity</td><td class="v">{r['Avg capacity GW']:.2f} GW</td></tr>
            <tr><td>Average intensity</td><td class="v">{r['Avg MW / million']:.2f} MW/mn</td></tr>
            <tr><td>Share of national capacity</td><td class="v">{pct(shares.loc[cl, 'Capacity'])}</td></tr>
          </table>
        </div>"""
    html(f'<div class="cluster-grid">{cards}</div>')

    # ---------------- Side-by-side comparison bars ----------------
    with card():
        metrics = [("States", "Number of states", "{:.0f}"),
                   ("Avg GSDP ₹ lakh cr", "Average GSDP (₹ lakh cr)", "{:.2f}"),
                   ("Avg capacity GW", "Average capacity (GW)", "{:.2f}"),
                   ("Avg MW / million", "Average intensity (MW per million)", "{:.1f}")]
        fig = make_subplots(rows=1, cols=4, subplot_titles=[m[1] for m in metrics], horizontal_spacing=0.06)
        for i, (col, _, f) in enumerate(metrics, start=1):
            fig.add_bar(
                x=[f"C{cl}" for cl in clusters.index], y=clusters[col],
                marker_color=[CLUSTER_COLORS[cl] for cl in clusters.index],
                text=[f.format(v) for v in clusters[col]], textposition="outside", cliponaxis=False,
                customdata=[CLUSTER_NAMES[cl] for cl in clusters.index],
                hovertemplate="<b>%{customdata}</b><br>%{y:,.2f}<extra></extra>", row=1, col=i,
            )
            fig.update_yaxes(showticklabels=False, row=1, col=i,
                             range=[0, clusters[col].max() * 1.22])
        style_fig(fig, height=310, legend=False)
        fig.update_annotations(font=dict(size=13, color=NAVY))
        fig.update_layout(margin=dict(t=50))
        show(fig)
        st.caption("Values are read from the K-MEANS sheet of the workbook.")

    # ---------------- PCA map coloured by cluster ----------------
    left, right = st.columns([1.6, 1], gap="medium")
    with left:
        with card():
            show_labels = st.toggle("Show state names on the map", value=False, key="pca_labels")
            fig = go.Figure()
            for cl in sorted(CLUSTER_NAMES):
                sub = states[states["Cluster"] == cl]
                fig.add_scatter(
                    x=sub["PC1 scaled"], y=sub["PC2 scaled"], name=cluster_label(cl),
                    mode="markers+text" if show_labels else "markers",
                    text=sub["State / UT"], textposition="top center", textfont=dict(size=10, color=INK_MUTED),
                    marker=dict(color=CLUSTER_COLORS[cl], size=12, line=dict(color="#fff", width=1.2)),
                    customdata=sub[["State / UT", "Capacity GW", "MW per million people", "GSDP ₹ lakh crore"]],
                    hovertemplate="<b>%{customdata[0]}</b><br>PC1 %{x:+.3f} | PC2 %{y:+.3f}"
                                  "<br>Capacity %{customdata[1]:.2f} GW<br>Intensity %{customdata[2]:.1f} MW/mn"
                                  "<br>GSDP ₹%{customdata[3]:.2f} lakh cr<extra></extra>",
                )
            fig.add_scatter(
                x=clusters["Center PC1"], y=clusters["Center PC2"], mode="markers", name="Cluster centres",
                marker=dict(symbol="x-thin", size=16, line=dict(width=3, color=NAVY)),
                customdata=[f"Cluster {cl} centre" for cl in clusters.index],
                hovertemplate="<b>%{customdata}</b><br>PC1 %{x:+.3f} | PC2 %{y:+.3f}<extra></extra>",
            )
            fig.add_hline(y=0, line=dict(color="#C9CFC5", width=1))
            fig.add_vline(x=0, line=dict(color="#C9CFC5", width=1))
            fig.update_layout(title="States on the PCA map, coloured by K-Means cluster")
            fig.update_xaxes(title_text=f"PC1: economic and population scale ({pc1_var:.2f}% of variance)")
            fig.update_yaxes(title_text=f"PC2: renewable intensity ({pc2_var:.2f}%)")
            style_fig(fig, height=520)
            fig.update_layout(legend=dict(y=-0.16, yanchor="top"))
            show(fig)
    with right:
        with card():
            st.markdown("**How to read the map**")
            st.markdown(
                "Moving **right** means a larger economy and population. Moving **up** means more renewable "
                "capacity per person. Clusters 1 and 4 both sit on the right, but Cluster 1 is high and "
                "Cluster 4 is low: similar scale, very different reported intensity."
            )
            st.markdown("**PCA loadings (from the workbook)**")
            loadings = pca.loc[["PC1", "PC2"], ["Loading: GSDP", "Loading: population", "Loading: intensity"]].T
            loadings.index = ["GSDP", "Population", "Capacity per million"]
            st.dataframe(loadings.style.format("{:+.3f}"), width="stretch")
            var_tbl = pca[["Eigenvalue", "Variance %", "Cumulative %"]].copy()
            var_tbl[["Variance %", "Cumulative %"]] *= 100
            st.dataframe(var_tbl.style.format({"Eigenvalue": "{:.4f}", "Variance %": "{:.2f}%", "Cumulative %": "{:.2f}%"}),
                         width="stretch")
            st.caption("Scores are scaled by √eigenvalue so both dimensions carry equal weight in K-Means.")

    # ---------------- Cluster 4 spotlight ----------------
    section("Spotlight: Cluster 4, large economies with low reported renewable intensity",
            "Share of the national total held by each cluster, computed from the 2024 STATES sheet.")
    left, right = st.columns([1.4, 1], gap="medium")
    with left:
        with card():
            fig = go.Figure()
            measure_colors = {"GSDP": NAVY_SOFT, "Population": "#B9C2B5", "Capacity": GREEN}
            for m, colr in measure_colors.items():
                fig.add_bar(
                    x=[f"Cluster {cl}" for cl in shares.index], y=shares[m], name=f"Share of {m if m == 'GSDP' else m.lower()}",
                    marker_color=colr, text=[pct(v) for v in shares[m]], textposition="outside", cliponaxis=False,
                    hovertemplate="%{x}<br>" + m + " share: %{y:.1f}%<extra></extra>",
                )
            fig.update_layout(barmode="group", title="Share of national GSDP, population and capacity by cluster")
            fig.update_yaxes(title_text="% of national total", range=[0, 105])
            style_fig(fig, height=380)
            show(fig)
    with right:
        c4 = states[states["Cluster"] == 4]
        s4 = shares.loc[4]
        note(
            f"<b>Cluster 4</b> ({', '.join(sorted(c4['State / UT']))}) holds "
            f"<b>{s4['GSDP']:.1f}%</b> of GSDP and <b>{s4['Population']:.1f}%</b> of the population, "
            f"but only <b>{s4['Capacity']:.1f}%</b> of reported renewable capacity. Its average intensity is "
            f"<b>{clusters.loc[4, 'Avg MW / million']:.2f} MW per million</b>, against "
            f"<b>{clusters.loc[1, 'Avg MW / million']:.2f}</b> in Cluster 1, which holds "
            f"<b>{shares.loc[1, 'Capacity']:.1f}%</b> of capacity.", "amber")
        note(
            "<b>How to interpret this.</b> The gap between economic scale and reported capacity is an "
            "<b>area for further investigation</b>, not proof of an investment opportunity. The analysis does "
            "not test resource quality, land availability, grid and transmission access, project economics, "
            "state policy or data coverage, any of which could explain the gap.")

    # ---------------- Explore one cluster ----------------
    section("Explore a cluster", "Choose a cluster to see its member states and the workbook's suggested next checks.")
    chosen = st.selectbox("Cluster", sorted(CLUSTER_NAMES), format_func=cluster_label, index=3, key="cluster_pick")
    g = data.cluster_guidance.set_index("Cluster").loc[chosen]
    html(f"""
    <div class="kpi-grid">
      <div class="kpi guide">
        <div class="label">What to check first</div>
        <div class="text">{g['What to check before investing']}</div>
        <div class="note">From the START &amp; FINDINGS sheet of the workbook</div></div>
      <div class="kpi guide">
        <div class="label">Suggested direction</div>
        <div class="text">{g['Practical policy direction']}</div>
        <div class="note">Indicative only; any project would need a feasibility study</div></div>
    </div>""")
    members = states[states["Cluster"] == chosen].sort_values("MW per million people", ascending=False)
    st.dataframe(
        members[["State / UT", "Zone", "GSDP ₹ lakh crore", "Population millions", "Capacity GW",
                 "MW per million people", "PC1 scaled", "PC2 scaled"]],
        hide_index=True, width="stretch",
        column_config={
            "GSDP ₹ lakh crore": st.column_config.NumberColumn("GSDP (₹ lakh cr)", format="%.3f"),
            "Population millions": st.column_config.NumberColumn("Population (mn)", format="%.2f"),
            "Capacity GW": st.column_config.NumberColumn("Capacity (GW)", format="%.3f"),
            "MW per million people": st.column_config.NumberColumn("MW per million", format="%.2f"),
            "PC1 scaled": st.column_config.NumberColumn("PC1", format="%+.3f"),
            "PC2 scaled": st.column_config.NumberColumn("PC2", format="%+.3f"),
        },
    )
    if chosen == 2:
        st.caption("Several members report zero or very low capacity. Verify these figures before drawing conclusions.")
    if chosen == 3:
        st.caption("High intensity here rests on very small populations, so ratios should be read with caution.")

    with st.expander("Why K = 4? (silhouette scores from the workbook)"):
        sil = data.silhouette.copy()
        fig = go.Figure(go.Bar(
            x=[f"K = {int(v)}" for v in sil["Chosen K"]], y=sil["Silhouette score"],
            marker_color=[GREEN if int(v) == k else "#C9CFC5" for v in sil["Chosen K"]],
            text=[f"{s:.3f}<br>smallest group: {int(n)}" for s, n in
                  zip(sil["Silhouette score"], sil["Number of states in smallest group"])],
            textposition="outside", cliponaxis=False,
            hovertemplate="%{x}: %{y:.3f}<extra></extra>",
        ))
        fig.update_yaxes(title_text="Silhouette score", range=[0, sil["Silhouette score"].max() * 1.3])
        style_fig(fig, height=300, legend=False)
        show(fig)
        st.write("K = 5 scores marginally higher but isolates a single state. K = 4 gives clearly separated "
                 "groups with no single-state cluster, so it was selected.")


# --------------------------------------------------------------------------
# TAB 4: HISTORICAL TRENDS
# --------------------------------------------------------------------------
with tab_history:
    # Build the coverage disclosure from the data itself.
    coverage = national.set_index("Year")["States / UTs reported"]
    all_names = set(history["State / UT"])
    gaps = []
    for count, years in coverage.groupby(coverage).groups.items():
        if count < len(all_names):
            yrs = sorted(years)
            span = f"{yrs[0]}–{yrs[-1]}" if len(yrs) > 1 else f"{yrs[0]}"
            gaps.append(f"{count} in {span}")
    missing_detail = []
    for y in sorted(coverage.index):
        absent = sorted(all_names - set(history.loc[history["Year"] == y, "State / UT"]))
        if absent:
            missing_detail.append(f"{y}: {', '.join(absent)}")
    full_from = int(coverage[coverage == len(all_names)].index.min())
    note(
        f"<b>Read these charts as descriptive history.</b> The number of states/UTs in the dataset varies in the "
        f"earlier years ({'; '.join(gaps)}; all {len(all_names)} from {full_from}). Totals for early years therefore "
        f"cover fewer geographies. These charts are <b>not part of the 2024 PCA, K-Means or regression</b>.", "amber")
    with st.expander("Which states/UTs are missing in which years?"):
        st.write("\n".join(f"- {line}" for line in missing_detail))

    # ---------------- National trend ----------------
    with card():
        nat_view = st.radio("View", ["Stacked by category", "Total only", "Category share (%)"],
                            horizontal=True, key="nat_view")
        fig = go.Figure()
        cats = list(CATEGORY_COLORS)
        if nat_view == "Total only":
            fig.add_scatter(
                x=national["Year"], y=national["Total"], mode="lines+markers", name="Total",
                line=dict(color=GREEN, width=3), fill="tozeroy", fillcolor="rgba(107,165,57,0.12)",
                customdata=national["States / UTs reported"],
                hovertemplate="%{x}: %{y:,.2f} GW<br>States/UTs reported: %{customdata}<extra></extra>",
            )
            y_title = "Reported capacity (GW)"
        else:
            share_mode = nat_view == "Category share (%)"
            for cat in cats:
                y = national[cat] / national["Total"] * 100 if share_mode else national[cat]
                fig.add_scatter(
                    x=national["Year"], y=y, name=cat, mode="lines", stackgroup="one",
                    line=dict(width=0.6, color=CATEGORY_COLORS[cat]), fillcolor=CATEGORY_COLORS[cat],
                    customdata=national["States / UTs reported"],
                    hovertemplate=f"{cat}: " + ("%{y:.1f}%" if share_mode else "%{y:,.2f} GW")
                                  + "<br>States/UTs reported: %{customdata}<extra></extra>",
                )
            y_title = "Share of reported capacity (%)" if share_mode else "Reported capacity (GW)"
        fig.update_layout(title=f"National reported renewable capacity, {FIRST_YEAR}–{LATEST_YEAR}", hovermode="x unified")
        fig.update_yaxes(title_text=y_title)
        fig.update_xaxes(dtick=2)
        style_fig(fig, height=420, legend=(nat_view != "Total only"))
        show(fig)

    # ---------------- Selected year ----------------
    section("Inspect a single year")
    years = [int(y) for y in sorted(history["Year"].unique())]
    c1, c2 = st.columns([3, 1])
    year = c1.select_slider("Year", options=years, value=LATEST_YEAR, key="year_pick")
    top_n = c2.selectbox("Show top", [5, 10, 15], index=1, key="top_n")
    yr = national.set_index("Year").loc[year]
    prev = national.set_index("Year").loc[year - 1] if (year - 1) in national["Year"].values else None
    change_txt = "No earlier year in the dataset"
    if prev is not None:
        change = yr["Total"] - prev["Total"]
        change_txt = f"{change:+,.2f} GW vs {year - 1}"
        if prev["States / UTs reported"] != yr["States / UTs reported"]:
            change_txt += " (coverage changed)"
    kpi_cards([
        (f"Reported capacity, {year}", f"{yr['Total']:,.2f} GW", change_txt),
        ("States / UTs in the data", f"{int(yr['States / UTs reported'])}", f"of {len(all_names)} in the full dataset"),
        ("Largest category", max(cats, key=lambda cc: yr[cc]),
         f"{max(yr[cc] for cc in cats) / yr['Total'] * 100:.1f}% of the year's total"),
        ("Solar share", f"{yr['Solar'] / yr['Total'] * 100:.1f}%", f"{yr['Solar']:,.2f} GW of solar reported"),
    ])
    with card():
        yd = history[history["Year"] == year].nlargest(top_n, "Total capacity MW").iloc[::-1]
        fig = go.Figure()
        for col, name in CATEGORY_COLUMNS.items():
            fig.add_bar(y=yd["State / UT"], x=yd[col] / 1000, name=name, orientation="h",
                        marker_color=CATEGORY_COLORS[name],
                        hovertemplate="<b>%{y}</b><br>" + name + ": %{x:,.2f} GW<extra></extra>")
        fig.update_layout(barmode="stack", title=f"Top {top_n} states by reported capacity, {year}")
        fig.update_xaxes(title_text="Capacity (GW)")
        style_fig(fig, height=max(320, 34 * top_n + 120))
        fig.update_layout(legend=dict(traceorder="normal"))
        show(fig)

    # ---------------- State-wise trends ----------------
    section("Compare states over time", "Pick states to compare. Years with no record appear as gaps.")
    c1, c2, c3 = st.columns([2.4, 1.2, 0.8])
    default_states = history[history["Year"] == LATEST_YEAR].nlargest(5, "Total capacity MW")["State / UT"].tolist()
    picked = c1.multiselect("States / UTs", sorted(all_names), default=default_states, key="trend_states")
    measure_map = {"Total capacity": "Total capacity MW", **{v: k_ for k_, v in CATEGORY_COLUMNS.items()},
                   "Capacity per million people": "Capacity MW / million people"}
    measure = c2.selectbox("Measure", list(measure_map), key="trend_measure")
    log_scale = c3.toggle("Log scale", value=False, key="trend_log",
                          help="Useful when comparing very large and very small states.")
    if not picked:
        st.info("Select at least one state or UT to draw the comparison.")
    else:
        with card():
            col = measure_map[measure]
            unit = "MW per million" if "million" in col else "MW"
            palette = [NAVY, GREEN, "#7FA7B3", AMBER, "#9BC53D", "#8C6E4E", "#AEB4AB", "#4E7F2E", "#C0573E", "#6E6A9E"]
            fig = go.Figure()
            for i, s in enumerate(picked):
                ts = history[history["State / UT"] == s].set_index("Year")[col].reindex(range(FIRST_YEAR, LATEST_YEAR + 1))
                y_vals = ts.where(ts > 0) if log_scale else ts   # log scale cannot show zero
                fig.add_scatter(x=ts.index, y=y_vals, name=s, mode="lines+markers", connectgaps=False,
                                line=dict(width=2.4, color=palette[i % len(palette)]), marker=dict(size=5),
                                hovertemplate=f"<b>{s}</b> %{{x}}: %{{y:,.1f}} {unit}<extra></extra>")
            fig.update_layout(title=f"{measure} by state, {FIRST_YEAR}–{LATEST_YEAR}", hovermode="x unified")
            fig.update_yaxes(title_text=unit, type="log" if log_scale else "linear", tickformat=",")
            fig.update_xaxes(dtick=2)
            style_fig(fig, height=430)
            show(fig)
            if log_scale:
                st.caption("Zero values cannot be shown on a log scale and are left blank.")

    # ---------------- Energy-category trends ----------------
    section("Energy-category trends", "National totals per category. Narrow to a zone to see regional patterns.")
    zone_choice = st.selectbox("Zone", ["All India"] + sorted(history["Zone"].dropna().unique()), key="cat_zone")
    hz = history if zone_choice == "All India" else history[history["Zone"] == zone_choice]
    cat_year = hz.groupby("Year")[list(CATEGORY_COLUMNS)].sum().div(1000).rename(columns=CATEGORY_COLUMNS)
    with card():
        fig = go.Figure()
        for cat in cats:
            fig.add_scatter(x=cat_year.index, y=cat_year[cat], name=cat, mode="lines+markers",
                            line=dict(color=CATEGORY_COLORS[cat], width=2.6), marker=dict(size=5),
                            hovertemplate=f"{cat}: %{{y:,.2f}} GW<extra></extra>")
        fig.update_layout(title=f"Reported capacity by category, {zone_choice}", hovermode="x unified")
        fig.update_yaxes(title_text="Capacity (GW)")
        fig.update_xaxes(dtick=2)
        style_fig(fig, height=400)
        show(fig)
        growth = cat_year.loc[LATEST_YEAR] - cat_year.loc[full_from]
        lead = growth.idxmax()
        st.caption(f"In {zone_choice}, {lead.lower()} added the most reported capacity between {full_from} and "
                   f"{LATEST_YEAR} (+{growth[lead]:,.2f} GW). {full_from} is used as the start because every "
                   "state/UT is present from that year.")

    with st.expander("Data quality notes for the historical series"):
        flagged = history[history["Data note"] == "Negative reported change"]
        dropped = []
        for s, g in history.sort_values("Year").groupby("State / UT"):
            prev_vals = g["Total capacity MW"].shift()
            hit = g[(g["Total capacity MW"] == 0) & (prev_vals > 0)]
            for _, r in hit.iterrows():
                dropped.append(f"{s} (from {prev_vals.loc[r.name]:,.2f} MW in {int(r['Year']) - 1} to 0 in {int(r['Year'])})")
        st.write(f"The workbook flags **{len(flagged)}** year-on-year decreases in reported capacity. "
                 "Most are tiny (rounding-level) changes; a few are large.")
        if dropped:
            st.write("Reported capacity falls to zero for: " + "; ".join(dropped) +
                     ". This supports the report's advice to verify zero values against official records.")
        st.dataframe(
            flagged[["State / UT", "Year", "Total capacity MW", "Annual net change MW"]]
            .sort_values("Annual net change MW")
            .rename(columns={"Total capacity MW": "Capacity (MW)", "Annual net change MW": "Change (MW)"}),
            hide_index=True, width="stretch",
            column_config={"Year": st.column_config.NumberColumn(format="%d"),
                           "Capacity (MW)": st.column_config.NumberColumn(format="%.3f"),
                           "Change (MW)": st.column_config.NumberColumn(format="%.3f")},
        )


# ==========================================================================
# 7. FOOTER
# ==========================================================================
st.divider()
st.caption(
    "Source: project workbook built from the India Renewable Energy Dataset (Kaggle, chrisjaimyantony). "
    "Figures are dataset-reported and cover five renewable categories; large hydro is excluded. "
    "PCA, K-Means and regression results are read from the workbook and describe 2024 only. "
    "This is an academic screening aid, not an investment recommendation or forecast."
)
