"""
data_loader.py
--------------
Reads everything the dashboard needs from the project workbook.

IMPORTANT DESIGN RULE
    This file does NOT recalculate PCA, K-Means or the regression.
    It only READS the results that are already stored in the workbook
    (sheets: CLEAN DATA, 2024 STATES, PCA, K-MEANS, REGRESSION,
    START & FINDINGS).

    The only things calculated here are simple descriptive figures,
    e.g. totals, shares (%), ranks, and the adjusted R² which is a
    one-line formula applied to the workbook's own R² and n.

Tables are found by searching for their header label in column A
(for example the row that starts with "Component" on the PCA sheet),
so the dashboard keeps working even if a row is inserted above a table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# File and sheet names
# --------------------------------------------------------------------------
WORKBOOK_NAME = "India_Renewable_Energy_PCA_KMeans_Regression_Easy_Scroll.xlsx"

SHEET_HISTORY = "CLEAN DATA"
SHEET_STATES = "2024 STATES"
SHEET_PCA = "PCA"
SHEET_KMEANS = "K-MEANS"
SHEET_REGRESSION = "REGRESSION"
SHEET_FINDINGS = "START & FINDINGS"

# The five renewable categories in the dataset (large hydro is NOT included).
CATEGORY_COLUMNS = {
    "Solar MW": "Solar",
    "Wind MW": "Wind",
    "Biomass MW": "Biomass",
    "Small Hydro MW": "Small hydro",
    "Waste-to-Energy MW": "Waste-to-energy",
}

# Columns the dashboard relies on. If any is missing, a clear error is shown.
REQUIRED_HISTORY_COLS = [
    "State / UT", "Year", "Zone", *CATEGORY_COLUMNS.keys(),
    "Population (people)", "GSDP (₹ crore)", "Total capacity MW",
    "Capacity MW / million people", "Annual net change MW", "Data note",
]
# Note: "Actual − fitted GW" uses the Unicode minus sign (−), exactly as in the workbook.
REQUIRED_STATE_COLS = [
    "State / UT", "Zone", "GSDP ₹ lakh crore", "Population millions",
    "Capacity GW", "MW per million people", "PC1 scaled", "PC2 scaled",
    "Cluster", "Reg. fitted GW", "Actual − fitted GW",
]


class WorkbookError(Exception):
    """Raised with a plain-English message when the workbook layout is not as expected."""


@dataclass
class ProjectData:
    """Everything the dashboard needs, in one container."""
    history: pd.DataFrame            # 2006–2024 panel (CLEAN DATA)
    states: pd.DataFrame             # 2024 cross-section, 34 rows (2024 STATES)
    pca_variance: pd.DataFrame       # PC1–PC3 eigenvalues, variance, loadings (PCA)
    cluster_summary: pd.DataFrame    # K-Means centres and averages (K-MEANS)
    silhouette: pd.DataFrame         # silhouette scores for K = 2..5 (K-MEANS)
    cluster_guidance: pd.DataFrame   # "what to check" / policy direction (START & FINDINGS)
    regression: dict                 # slope, intercept, r, R², RMSE, n (REGRESSION)
    limitations: list[str] = field(default_factory=list)
    source_note: str = ""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _find_row(raw: pd.DataFrame, label: str, sheet: str, contains: bool = False) -> int:
    """Return the index of the first row whose column-A text equals (or contains) `label`."""
    col_a = raw.iloc[:, 0].astype("string").str.strip()
    mask = col_a.str.contains(label, regex=False) if contains else (col_a == label)
    hits = raw.index[mask.fillna(False)]
    if len(hits) == 0:
        raise WorkbookError(f"Could not find the label '{label}' in column A of sheet '{sheet}'.")
    return int(hits[0])


def _read_table(raw: pd.DataFrame, header_label: str, sheet: str) -> pd.DataFrame:
    """
    Read a table whose header row starts with `header_label` in column A.
    The table ends at the first row where column A is blank.
    Columns with a blank header (e.g. side notes) are dropped.
    """
    start = _find_row(raw, header_label, sheet)
    header = raw.iloc[start].tolist()
    body = raw.iloc[start + 1:]
    blank_rows = body.index[body.iloc[:, 0].isna()]
    if len(blank_rows):
        body = body.loc[: blank_rows[0] - 1]   # keep rows up to the first blank one
    keep = [i for i, h in enumerate(header) if pd.notna(h) and str(h).strip()]
    table = body.iloc[:, keep].copy()
    table.columns = [str(header[i]).strip() for i in keep]
    return table.reset_index(drop=True)


def _check_columns(df: pd.DataFrame, required: list[str], sheet: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise WorkbookError(
            f"Sheet '{sheet}' is missing these expected column(s): {', '.join(missing)}. "
            "Check that the column headings in the workbook have not been renamed."
        )


def _to_numeric(df: pd.DataFrame, exclude: list[str]) -> pd.DataFrame:
    for col in df.columns:
        if col not in exclude:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# --------------------------------------------------------------------------
# Main loader
# --------------------------------------------------------------------------
def load_project_data(path: Path) -> ProjectData:
    if not path.exists():
        raise WorkbookError(
            f"The workbook '{path.name}' was not found next to app.py. "
            "Keep the Excel file in the same folder as app.py and do not rename it."
        )

    # Read every sheet once, without headers, using the values Excel last calculated.
    raw = pd.read_excel(path, sheet_name=None, header=None, engine="openpyxl")
    needed = [SHEET_HISTORY, SHEET_STATES, SHEET_PCA, SHEET_KMEANS, SHEET_REGRESSION, SHEET_FINDINGS]
    missing_sheets = [s for s in needed if s not in raw]
    if missing_sheets:
        raise WorkbookError(f"Missing sheet(s): {', '.join(missing_sheets)}. Found: {', '.join(raw)}.")

    # ---------------- CLEAN DATA: 2006–2024 panel ----------------
    history = _read_table(raw[SHEET_HISTORY], "State / UT", SHEET_HISTORY)
    _check_columns(history, REQUIRED_HISTORY_COLS, SHEET_HISTORY)
    history = _to_numeric(history, exclude=["State / UT", "Zone", "Data note"])
    history = history.dropna(subset=["State / UT", "Year"])
    history["Year"] = history["Year"].astype(int)
    if history["Total capacity MW"].isna().all():
        # Happens if the workbook was saved by a tool that does not store formula results.
        raise WorkbookError(
            "The capacity formulas in 'CLEAN DATA' have no stored values. "
            "Open the workbook in Excel, press Save, and try again."
        )

    # ---------------- 2024 STATES: the 34-row cross-section ----------------
    states = _read_table(raw[SHEET_STATES], "State / UT", SHEET_STATES)
    _check_columns(states, REQUIRED_STATE_COLS, SHEET_STATES)
    states = _to_numeric(states, exclude=["State / UT", "Zone"])
    states = states.dropna(subset=["State / UT"])
    states["Cluster"] = states["Cluster"].astype(int)

    # ---------------- PCA: variance explained and loadings ----------------
    pca = _read_table(raw[SHEET_PCA], "Component", SHEET_PCA)
    pca = _to_numeric(pca, exclude=["Component"])

    # ---------------- K-MEANS: cluster summary and silhouette ----------------
    clusters = _read_table(raw[SHEET_KMEANS], "Cluster", SHEET_KMEANS)
    clusters = _to_numeric(clusters, exclude=["Plain-English profile"])
    clusters["Cluster"] = clusters["Cluster"].astype(int)

    silhouette = _read_table(raw[SHEET_KMEANS], "Chosen K", SHEET_KMEANS)
    silhouette = _to_numeric(silhouette, exclude=["Interpretation"])

    # ---------------- START & FINDINGS: guidance per cluster + limitations ----------------
    guidance = _read_table(raw[SHEET_FINDINGS], "Cluster", SHEET_FINDINGS)
    guidance["Cluster"] = pd.to_numeric(guidance["Cluster"], errors="coerce").astype(int)

    fr = raw[SHEET_FINDINGS]
    lim_start = _find_row(fr, "LIMITATIONS", SHEET_FINDINGS, contains=True)
    limitations = []
    for value in fr.iloc[lim_start + 1:, 0]:
        if pd.isna(value):
            break
        limitations.append(str(value).strip())
    try:
        src_row = _find_row(fr, "SOURCE:", SHEET_FINDINGS, contains=True)
        source_note = str(fr.iloc[src_row, 0]).strip()
    except WorkbookError:
        source_note = ""

    # ---------------- REGRESSION: model statistics ----------------
    reg_table = _read_table(raw[SHEET_REGRESSION], "Metric", SHEET_REGRESSION)

    def reg_value(starts_with: str) -> float:
        rows = reg_table[reg_table["Metric"].astype(str).str.startswith(starts_with)]
        if rows.empty:
            raise WorkbookError(f"Regression metric starting with '{starts_with}' not found.")
        return float(rows.iloc[0]["2024 result"])

    n = int(reg_value("Number of states"))
    r2 = reg_value("R²")
    regression = {
        "n": n,
        "slope": reg_value("Slope (GW"),
        "intercept": reg_value("Intercept"),
        "r": reg_value("Correlation"),
        "r2": r2,
        # Adjusted R² is not stored in the workbook; it is the standard
        # one-predictor adjustment of the workbook's own R² (k = 1 predictor).
        "adj_r2": 1 - (1 - r2) * (n - 1) / (n - 1 - 1),
        "rmse": reg_value("Root mean squared"),
    }

    # ---------------- Derived, descriptive columns for display ----------------
    names = clusters.set_index("Cluster")["Plain-English profile"].to_dict()
    states["Cluster profile"] = states["Cluster"].map(names)
    for col, rank_col in [
        ("Capacity GW", "Rank: capacity"),
        ("MW per million people", "Rank: intensity"),
        ("GSDP ₹ lakh crore", "Rank: GSDP"),
        ("Population millions", "Rank: population"),
    ]:
        states[rank_col] = states[col].rank(ascending=False, method="min").astype(int)

    return ProjectData(
        history=history,
        states=states,
        pca_variance=pca,
        cluster_summary=clusters,
        silhouette=silhouette,
        cluster_guidance=guidance,
        regression=regression,
        limitations=limitations,
        source_note=source_note,
    )


def cluster_shares(states: pd.DataFrame) -> pd.DataFrame:
    """Share (%) of total GSDP, population and capacity held by each cluster (descriptive)."""
    cols = {"GSDP ₹ lakh crore": "GSDP", "Population millions": "Population", "Capacity GW": "Capacity"}
    totals = states[list(cols)].sum()
    shares = states.groupby("Cluster")[list(cols)].sum().div(totals).mul(100)
    return shares.rename(columns=cols)


def category_totals_by_year(history: pd.DataFrame) -> pd.DataFrame:
    """National reported capacity (GW) per category per year, plus state/UT coverage."""
    agg = history.groupby("Year")[list(CATEGORY_COLUMNS)].sum().div(1000)
    agg = agg.rename(columns=CATEGORY_COLUMNS)
    agg["Total"] = agg.sum(axis=1)
    agg["States / UTs reported"] = history.groupby("Year")["State / UT"].nunique()
    return agg.reset_index()
