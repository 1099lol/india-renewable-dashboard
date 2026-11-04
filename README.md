# Deconstructing India's Clean Energy Transition

An interactive dashboard for the WAS Group 3 project *State-Level Renewable Energy Profiles, Capacity and Economic Scale*.

It presents the completed 2024 analysis of 34 Indian states and Union Territories (PCA, K-Means with K = 4, and simple linear regression), plus a descriptive 2006–2024 history. Every statistical result is **read from the project workbook**; nothing is re-estimated by the dashboard.

## What is in this folder

| File | What it does | Edit it? |
| --- | --- | --- |
| `app.py` | The dashboard: layout, the four tabs, charts and filters. | Only for design or text changes. |
| `data_loader.py` | Reads the Excel workbook and checks that the expected sheets and columns exist. | Rarely. |
| `India_Renewable_Energy_PCA_KMeans_Regression_Easy_Scroll.xlsx` | All data and results. The dashboard's single source of truth. | Yes, this is how you update numbers. |
| `requirements.txt` | The list of Python packages the website installs. | No. |
| `.streamlit/config.toml` | Theme: sage, white and charcoal with leaf-green accents, Geist font, dark sidebar. | Optional. |
| `.gitignore` | Tells GitHub to ignore temporary files. | No. |
| `DEPLOYMENT_GUIDE.md` | Step-by-step instructions for publishing the Streamlit version. | No. |
| `docs/`, `build_site.py`, `site_template.html` | The always-on website version (see below). | Re-run `build_site.py` after workbook changes. |

Keep all of these in the same folder and **do not rename the Excel file**.

## The four tabs

1. **National overview:** 2024 totals, top 10 states, the five-category mix and a filterable ranking table.
2. **State explorer:** pick any state or UT to see its 2024 profile, cluster, PCA coordinates, regression fitted value and residual, and its 2006–2024 history.
3. **Cluster analysis:** the four K-Means profiles, the PCA map coloured by cluster, the Cluster 4 spotlight and member lists.
4. **Historical trends:** national, state-wise and category trends from 2006 to 2024, with the coverage limitation disclosed.

## The always-on website version (GitHub Pages)

The `docs/` folder holds a second, **server-free** version of the same dashboard: same four tabs, same design, same numbers, with all charts and filters running in the visitor's browser. Because nothing runs on a server, it never sleeps and loads instantly every time.

| File | What it does |
| --- | --- |
| `docs/index.html` | The website. Generated automatically; do not edit by hand. |
| `docs/plotly.min.js` | The charting library, stored locally so the site needs no outside code. |
| `site_template.html` | The design and interactivity of the website version. |
| `build_site.py` | Reads the workbook and regenerates `docs/index.html`. |

**If the workbook changes**, regenerate the site (with your virtual environment active):

```
python build_site.py
```

Then upload the new `docs/index.html` to GitHub. The website updates within a minute or two.

**Turning it on (one time):** in the GitHub repository go to **Settings → Pages**, set **Source** to *Deploy from a branch*, choose branch **main** and folder **/docs**, then click **Save**. The address will be `https://<your-username>.github.io/india-renewable-dashboard/`.

## Run it on your own computer (optional)

You only need this if you want to test changes before publishing. The online version does not need it.

**Windows**
1. Install Python 3.12 from https://www.python.org/downloads/ and tick **Add Python to PATH** during installation.
2. Open this folder in File Explorer, click the address bar, type `cmd` and press Enter.
3. Run: `py -m pip install -r requirements.txt`
4. Run: `py -m streamlit run app.py`
5. Your browser opens at http://localhost:8501. To stop the dashboard, close the black command window.

**Mac**
1. Install Python 3.12 from https://www.python.org/downloads/.
2. Open Terminal, type `cd ` (with a space), drag this folder into the Terminal window and press Enter.
3. Run: `python3 -m pip install -r requirements.txt`
4. Run: `python3 -m streamlit run app.py`

## Updating the dashboard

- **Numbers changed?** Edit the workbook in Excel, **save it**, and upload the new version with the same file name. The dashboard reads values Excel has saved, so the file must be saved in Excel (not just edited in another tool).
- **Text or design changes?** Edit `app.py`. Each section is labelled with comments.
- Once the website is live, uploading a changed file to GitHub updates the website automatically within a minute or two.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| "The workbook ... was not found next to app.py" | The Excel file is missing or renamed. Put it back with its original name. |
| "Sheet ... is missing these expected column(s)" | A column heading in the workbook was renamed. Restore the original heading. |
| "The capacity formulas ... have no stored values" | Open the workbook in Excel, press Save, and upload it again. |
| Red buttons, a white sidebar or square corners | The `.streamlit` folder did not upload. See the deployment guide, step 3. |

## Data scope and limitations

- Source: India Renewable Energy Dataset (Kaggle, chrisjaimyantony), as prepared in the project workbook.
- Five categories only: solar, wind, biomass, small hydro and waste-to-energy. Large hydro is excluded.
- PCA, K-Means and the regression use the 2024 cross-section only. The regression is a descriptive association, not a forecast or causal estimate.
- Historical coverage varies: 32 states/UTs in 2006–2008, 33 in 2009–2013 and all 34 from 2014. Historical charts are descriptive.
- Zero or very low reported capacities (for example Lakshadweep, Meghalaya and Nagaland in 2024) should be verified against official records.
- This is an academic screening aid, not an investment recommendation.
