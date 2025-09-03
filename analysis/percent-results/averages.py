import pandas as pd
from pathlib import Path

# ----------------------------
# CONFIG
# ----------------------------
DATA_DIR = Path("results_vs_BLS")  # update this to your directory
OUTPUT_FILE = "results_vs_BLS/averaged_differences_vs_BLS.csv"

# ----------------------------
# Load all CSVs
# ----------------------------
all_files = list(DATA_DIR.glob("*.csv"))

dfs = []
for f in all_files:
    df = pd.read_csv(f)
    dfs.append(df)

# Concatenate all 4 model outputs
combined = pd.concat(dfs, ignore_index=True)

# ----------------------------
# Group by occupation and average
# ----------------------------
averaged = (
    combined.groupby("occupation")[["diff_p_women", "diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"]]
    .mean()
    .round(1)   # round to 1 decimal place
    .reset_index()
)

# ----------------------------
# Save result
# ----------------------------
averaged.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Saved averaged results to {OUTPUT_FILE}")

