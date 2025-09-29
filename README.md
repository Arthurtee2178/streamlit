# Historical Rate Explorer (Streamlit)

This small Streamlit app loads `HistoricalRateDetail.csv` (included) or an uploaded CSV with `Date` and `Value` columns and provides interactive charts and basic statistics.

Quick setup (Windows PowerShell):

```powershell
# 1. Create a venv in the project folder
python -m venv .venv

# 2. Activate the venv
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Run the Streamlit app
streamlit run app.py
```

If PowerShell prevents script execution, run (as admin) to allow the activation script once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

What the app provides
- Upload your own CSV or use the included `HistoricalRateDetail.csv`.
- Interactive time series (line/area/bar) and optional rolling mean.
- Resample to weekly/monthly/quarterly averages.
- Histogram and monthly boxplot.
- Quick summary statistics and downloadable filtered CSV.

Notes
- The loader tolerates a couple of metadata lines before the CSV header (as in the provided file). If your CSV has a different format, upload a cleaned CSV with a header line containing `Date,Value`.
