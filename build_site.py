"""
build_site.py
-------------
Builds the static, always-on version of the dashboard for GitHub Pages.

    python build_site.py

What it does
    1. Reads the project workbook with data_loader.py (the same reader the
       Streamlit app uses), so every number comes from the workbook.
    2. Packs the data into JSON and inserts it into site_template.html.
    3. Writes the finished website to the docs/ folder:
         docs/index.html     the dashboard
         docs/plotly.min.js  the charting library (stored locally, no CDN)

Nothing is re-estimated: PCA scores, clusters, regression coefficients,
fitted values and residuals are read from the workbook. Only simple
descriptive figures (totals, shares, ranks, coverage counts, adjusted R²
from the workbook's R² and n) are calculated here.

Run it again whenever the workbook changes, then upload the docs/ folder.
"""

from __future__ import annotations

import json
import math
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

from data_loader import (
    CATEGORY_COLUMNS,
    WORKBOOK_NAME,
    category_totals_by_year,
    cluster_shares,
    load_project_data,
)

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "site_template.html"
OUT_DIR = HERE / "docs"


def clean(value):
    """Make values JSON-safe (NaN -> None, numpy numbers -> Python numbers)."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def records(df: pd.DataFrame) -> list[dict]:
    return clean(df.to_dict(orient="records"))


def main() -> None:
    data = load_project_data(HERE / WORKBOOK_NAME)
    h, s = data.history, data.states
    cats = list(CATEGORY_COLUMNS)                     # workbook column names
    cat_names = list(CATEGORY_COLUMNS.values())       # display names
    first, last = int(h["Year"].min()), int(h["Year"].max())

    # ---- 2024 state profiles (one row per state/UT) ----
    state_cols = ["State / UT", "Zone", "GSDP ₹ lakh crore", "Population millions", "Capacity GW",
                  "MW per million people", "PC1 scaled", "PC2 scaled", "Cluster", "Reg. fitted GW",
                  "Actual − fitted GW", "Rank: capacity", "Rank: intensity", "Rank: GSDP", "Rank: population"]
    states = s[state_cols].rename(columns={
        "State / UT": "name", "Zone": "zone", "GSDP ₹ lakh crore": "gsdp", "Population millions": "pop",
        "Capacity GW": "cap", "MW per million people": "intensity", "PC1 scaled": "pc1", "PC2 scaled": "pc2",
        "Cluster": "cluster", "Reg. fitted GW": "fitted", "Actual − fitted GW": "resid",
        "Rank: capacity": "rCap", "Rank: intensity": "rInt", "Rank: GSDP": "rGsdp", "Rank: population": "rPop"})

    # ---- 2006–2024 panel, compact: per state, arrays indexed by year ----
    years = list(range(first, last + 1))
    hist = {}
    for name, g in h.groupby("State / UT"):
        g = g.set_index("Year").reindex(years)        # missing years stay blank (gaps)
        entry = {"total": g["Total capacity MW"].tolist(),
                 "intensity": g["Capacity MW / million people"].tolist(),
                 "zone": g["Zone"].dropna().iloc[0]}
        for col, disp in CATEGORY_COLUMNS.items():
            entry[disp] = g[col].tolist()
        flagged = h[(h["State / UT"] == name) & (h["Data note"] == "Negative reported change")]
        entry["flags"] = records(flagged[["Year", "Total capacity MW", "Annual net change MW"]].rename(
            columns={"Total capacity MW": "cap", "Annual net change MW": "change"}))
        entry["missing"] = [y for y in years if pd.isna(g.loc[y, "Total capacity MW"])]
        hist[name] = entry

    national = category_totals_by_year(h)
    nat = {"years": national["Year"].tolist(), "total": national["Total"].tolist(),
           "count": national["States / UTs reported"].tolist()}
    for disp in cat_names:
        nat[disp] = national[disp].tolist()

    # ---- coverage disclosure (computed from the data, not typed in) ----
    all_names = sorted(h["State / UT"].unique())
    cov = national.set_index("Year")["States / UTs reported"]
    gaps = []
    for count, yrs in cov.groupby(cov).groups.items():
        if count < len(all_names):
            yrs = sorted(yrs)
            gaps.append(f"{count} in {yrs[0]}–{yrs[-1]}" if len(yrs) > 1 else f"{count} in {yrs[0]}")
    missing_by_year = []
    for y in years:
        absent = sorted(set(all_names) - set(h.loc[h["Year"] == y, "State / UT"]))
        if absent:
            missing_by_year.append(f"{y}: {', '.join(absent)}")
    full_from = int(cov[cov == len(all_names)].index.min())

    # ---- data-quality notes ----
    flagged_all = h[h["Data note"] == "Negative reported change"].sort_values("Annual net change MW")
    dropped = []
    for name, g in h.sort_values("Year").groupby("State / UT"):
        prev = g["Total capacity MW"].shift()
        for _, r in g[(g["Total capacity MW"] == 0) & (prev > 0)].iterrows():
            dropped.append(f"{name} (from {prev.loc[r.name]:,.2f} MW in {int(r['Year']) - 1} to 0 in {int(r['Year'])})")

    pca = data.pca_variance.set_index("Component")
    clusters = data.cluster_summary
    shares = cluster_shares(s)
    latest = h[h["Year"] == last]

    payload = {
        "built": date.today().isoformat(),
        "firstYear": first, "lastYear": last, "years": years,
        "categories": cat_names,
        "states": records(states),
        "history": clean(hist),
        "national": clean(nat),
        "latestMix": clean({disp: float(latest[col].sum() / 1000) for col, disp in CATEGORY_COLUMNS.items()}),
        "clusters": records(clusters.rename(columns={
            "Cluster": "id", "Center PC1": "c1", "Center PC2": "c2", "States": "n", "Avg GSDP ₹ lakh cr": "gsdp",
            "Avg capacity GW": "cap", "Avg MW / million": "intensity", "Avg pop millions": "pop",
            "Plain-English profile": "profile"})),
        "shares": clean({int(k): v for k, v in shares.to_dict(orient="index").items()}),
        "guidance": clean({int(r["Cluster"]): {"check": r["What to check before investing"],
                                                "direction": r["Practical policy direction"]}
                           for _, r in data.cluster_guidance.iterrows()}),
        "silhouette": records(data.silhouette.rename(columns={
            "Chosen K": "k", "Silhouette score": "score", "Number of states in smallest group": "smallest"})[
            ["k", "score", "smallest"]]),
        "pca": clean({c: {"eig": pca.loc[c, "Eigenvalue"], "var": pca.loc[c, "Variance %"] * 100,
                          "cum": pca.loc[c, "Cumulative %"] * 100, "lG": pca.loc[c, "Loading: GSDP"],
                          "lP": pca.loc[c, "Loading: population"], "lI": pca.loc[c, "Loading: intensity"]}
                      for c in pca.index}),
        "regression": clean(data.regression),
        "coverage": {"gaps": gaps, "missingByYear": missing_by_year, "fullFrom": full_from, "nAll": len(all_names)},
        "quality": {"dropped": dropped, "flagged": records(flagged_all[["State / UT", "Year", "Total capacity MW",
                    "Annual net change MW"]].rename(columns={"State / UT": "name", "Year": "year",
                    "Total capacity MW": "cap", "Annual net change MW": "change"}))},
        "limitations": [x.split(". ", 1)[-1] for x in data.limitations],
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    marker = "/*__DATA__*/null"
    if marker not in html:
        raise SystemExit("site_template.html is missing the data marker.")
    html = html.replace(marker, json.dumps(payload, ensure_ascii=False))

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    (OUT_DIR / ".nojekyll").write_text("")            # tells GitHub Pages to serve files as-is
    import plotly
    shutil.copy(Path(plotly.__file__).parent / "package_data" / "plotly.min.js", OUT_DIR / "plotly.min.js")
    print(f"Built {OUT_DIR / 'index.html'} ({len(html) / 1024:.0f} KB) from {WORKBOOK_NAME}")


if __name__ == "__main__":
    main()
