import os
import csv
import re
import pandas as pd

# ======== CONFIGURE THIS ========
DIR_PATH = "../profiles/mistral"  # <-- change to your folder
OUTPUT_CSV = "results_across_40/mistral_percentages_across_40_careers.csv"
DECIMALS = 1
# =================================

RACES = ["white", "black", "asian", "hispanic"]
RACE_SPLIT_RE = re.compile(r"\s*(?:,|/|;|\s+and\s+)\s*", flags=re.IGNORECASE)

def canonicalize_occupation(filename: str) -> str:
    """
    Convert 'buildinginspectorprofile_mistral.csv' → 'buildinginspector'
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    # Strip the fixed suffix if present
    if stem.endswith("profile_mistral"):
        stem = stem.replace("profile_mistral", "")
    # Clean up leftover underscores or hyphens
    stem = re.sub(r"[_\-]+$", "", stem).strip()
    return stem

def extract_races(cell: str):
    if not isinstance(cell, str) or not cell.strip():
        return set()
    parts = RACE_SPLIT_RE.split(cell.strip().lower())
    return {p for p in parts if p in RACES}

def pct(n, d):
    if d == 0:
        return 0.0
    return round(100.0 * n / d, DECIMALS)

def process_file(path: str):
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp1252")

    cols = {c.lower(): c for c in df.columns}
    gender_col = cols["gender"]
    eth_col = cols["ethnicity"]

    total_rows = len(df)
    gender_series = df[gender_col].astype(str).str.strip().str.lower()
    n_female = (gender_series == "female").sum()

    race_counts = {r: 0 for r in RACES}
    for val in df[eth_col]:
        races = extract_races(val)
        for r in races:
            race_counts[r] += 1

    return {
        "p_women": pct(n_female, total_rows),
        "p_white": pct(race_counts["white"], total_rows),
        "p_black": pct(race_counts["black"], total_rows),
        "p_asian": pct(race_counts["asian"], total_rows),
        "p_hispanic": pct(race_counts["hispanic"], total_rows),
    }

def main():
    rows = []
    for entry in sorted(os.listdir(DIR_PATH)):
        if entry.startswith(".") or not entry.lower().endswith(".csv"):
            continue
        path = os.path.join(DIR_PATH, entry)
        occupation = canonicalize_occupation(entry)
        metrics = process_file(path)
        rows.append({"occupation": occupation, **metrics})

    header = ["occupation", "p_women", "p_white", "p_black", "p_asian", "p_hispanic"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
