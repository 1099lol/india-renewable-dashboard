# Publishing the dashboard as a website

Time needed: about 20–30 minutes the first time. Cost: free. No coding required.

## How it works (one paragraph)

Your dashboard is a Python program. **GitHub** stores the files online. **Streamlit Community Cloud** (free) reads those files from GitHub, runs the Python program on its own server, and gives you a public link ending in `.streamlit.app`. When someone opens the link, the server builds the page and sends it to their browser as ordinary web content (HTML). When they change a dropdown or slider, the browser tells the server, the server re-runs the Python code for that selection, and the updated charts appear. Visitors do not need Python, an account or any installation.

```
Your files  ──upload──▶  GitHub repository  ──read by──▶  Streamlit Community Cloud  ──link──▶  Anyone's browser
```

---

## Step 1: Create a GitHub account

1. Go to https://github.com and click **Sign up**.
2. Use an email you can access, choose a username, and verify your email.

Your username appears in your website address if you do not choose a custom one, so pick something sensible.

## Step 2: Create a repository (an online project folder)

1. When signed in to GitHub, click the **+** at the top right, then **New repository**.
2. **Repository name:** `india-renewable-dashboard`
3. Choose **Public**. (A public repository lets anyone open the website link. The code and workbook will also be visible. The data is already public on Kaggle.)
4. Leave every other option unticked. Do **not** add a README (you already have one).
5. Click **Create repository**.

## Step 3: Upload the project files

1. Unzip `india-renewable-dashboard.zip` on your computer. You get a folder called `india-renewable-dashboard`.
2. On the new repository page, click the link **uploading an existing file**.
3. Open the unzipped folder, select **everything inside it** (not the folder itself) and drag it into the GitHub upload box. You should see:
   - `app.py`
   - `data_loader.py`
   - `India_Renewable_Energy_PCA_KMeans_Regression_Easy_Scroll.xlsx`
   - `requirements.txt`
   - `README.md`
   - `DEPLOYMENT_GUIDE.md`
   - `.gitignore`
   - `.streamlit/config.toml`
4. Scroll down and click **Commit changes**.

**Check the `.streamlit` folder arrived.** After uploading, the repository's file list should show a folder named `.streamlit`.

- **On a Mac** this folder is hidden in Finder. Press **Cmd + Shift + .** (full stop) in the Finder window to show it, then drag it in.
- **If it still does not appear**, create it directly on GitHub: click **Add file → Create new file**, type `.streamlit/config.toml` as the file name (typing the `/` creates the folder), open `config.toml` from the unzipped folder in Notepad or TextEdit, copy everything, paste it into GitHub, and click **Commit changes**.

Without this file the dashboard still works, but uses Streamlit's default red accent instead of green.

## Step 4: Connect Streamlit Community Cloud

1. Go to https://share.streamlit.io.
2. Click **Continue with GitHub** and sign in with the GitHub account from Step 1.
3. Click **Authorize** when GitHub asks for permission. This lets Streamlit read your repository.

## Step 5: Deploy

1. In your Streamlit workspace, click **Create app** (top right).
2. When asked "Do you already have an app?", click **Yup, I have an app**.
3. Fill in:
   - **Repository:** `your-username/india-renewable-dashboard`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL (optional):** choose something memorable, for example `india-clean-energy-was3`. Your link becomes `https://india-clean-energy-was3.streamlit.app`.
4. Click **Advanced settings**, set **Python version** to **3.12**, and click **Save**. (3.12 is the default and is what the dashboard was tested on.)
5. Click **Deploy**.

The first launch takes a few minutes while the server installs the packages. You can watch progress in the log panel. When the dashboard appears, copy the address from your browser's address bar. **That is your public link.**

## Step 6: Test the public link

Before sharing it:

1. Open the link in a private or incognito browser window (this is how your professor will see it).
2. Click through all four tabs.
3. In **State explorer**, choose two or three states.
4. In **Cluster analysis**, switch clusters and turn on state names on the map.
5. In **Historical trends**, move the year slider and add a state to the comparison.

If all of that works, the site is live.

---

## Updating the dashboard later

1. Open your repository on GitHub.
2. Click **Add file → Upload files** and drag in the changed file (for example a corrected workbook with the **same file name**).
3. Click **Commit changes**.

The website picks up the change automatically, usually within a minute or two. Refresh the page to see it.

## Good to know

- **Sleeping apps.** Free apps go to sleep after a period with no visitors. The first person to open a sleeping app sees a button to wake it, and it takes about a minute to start. **Open the link yourself 5–10 minutes before any presentation.**
- **Who can edit?** Only you (the GitHub account owner). Visitors can use the dashboard but cannot change it.
- **Logs.** If the site shows an error, open the app while signed in, click **Manage app** at the bottom right, and read the log panel. Copy the red error text and send it to whoever is helping you.

## Troubleshooting

| Problem | Likely cause and fix |
| --- | --- |
| "ModuleNotFoundError" in the logs | `requirements.txt` was not uploaded. Upload it, then click **Manage app → ⋮ → Reboot app**. |
| "The workbook ... was not found" | The Excel file is missing or was renamed. Upload it with its original name. |
| Red accents instead of green | The `.streamlit/config.toml` file is missing. See Step 3. |
| App stuck on "Your app is in the oven" for more than 10 minutes | Click **Manage app → ⋮ → Reboot app**. |
| Wrong Python version | **Manage app → ⋮ → Settings** shows the current version. If it is not 3.12, delete the app and deploy again with 3.12 selected in Advanced settings (the version cannot be changed on an existing app). |
