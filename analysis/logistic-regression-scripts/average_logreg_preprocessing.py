import pandas as pd
from pathlib import Path

# ----------------------------
# CONFIG
# ----------------------------
DATA_DIR = Path("results/csvs")  # update this to your directory
OUTPUT_FILE = "averaged_logreg.csv"

# ----------------------------
# Load all CSVs
# ----------------------------
all_files = list(DATA_DIR.glob("*.csv"))
dfs = [pd.read_csv(f) for f in all_files]

# Concatenate all model outputs
combined = pd.concat(dfs, ignore_index=True)

# ----------------------------
# Columns to average vs keep
# ----------------------------
avg_cols = [
    "genai_p_women",
    "genai_p_white",
    "genai_p_black",
    "genai_p_hispanic",
    "genai_p_asian"
]

# Group by career
averaged = (
    combined.groupby("career", as_index=False)
    .agg({
        # average these columns
        **{col: "mean" for col in avg_cols},
        # take first (same across models) for everything else
        "genai_n": "first",
        "genai_women": "first",
        "genai_white": "first",
        "genai_black": "first",
        "genai_hispanic": "first",
        "genai_asian": "first",
        "n_employed": "first",
        "bls_p_women": "first",
        "bls_p_white": "first",
        "bls_p_black": "first",
        "bls_p_asian": "first",
        "bls_p_hispanic": "first"
    })
)

# Round averages to 1 decimal place
averaged[avg_cols] = averaged[avg_cols].round(1)

# ----------------------------
# Reorder columns as requested
# ----------------------------
ordered_cols = [
    "career",
    "genai_n", "genai_women", "genai_white", "genai_black", "genai_hispanic", "genai_asian",
    "genai_p_women", "genai_p_white", "genai_p_black", "genai_p_hispanic", "genai_p_asian",
    "n_employed",
    "bls_p_women", "bls_p_white", "bls_p_black", "bls_p_asian", "bls_p_hispanic"
]
averaged = averaged[ordered_cols]

# ----------------------------
# Save result
# ----------------------------
averaged.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Saved averaged results with all columns to {OUTPUT_FILE}")
