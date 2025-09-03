#!/usr/bin/env python3
import os
import glob
import pandas as pd

# ---- Configuration ----
INPUT_GLOB = "results_across_40/gemini_percentages_across_40_careers.csv"   # model files
BLS_FILE   = "../profiles/bls-baselines.csv"                     # BLS baseline file
OUT_FILE   = "results_vs_BLS/gemini_differences_vs_bls.csv"                # single combined output

DEMO_COLS = ["p_women", "p_white", "p_black", "p_asian", "p_hispanic"]

def clean_occ(df, col):
    df[col] = (
        df[col].astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )
    return df

def ensure_numeric(df, cols):
    """Coerce columns to numeric (handles strings like '40.0' or '40%')."""
    for c in cols:
        if c in df.columns:
            df[c] = (
                df[c]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def load_bls(path):
    bls = pd.read_csv(path)
    if "genai_bias_search_term" not in bls.columns:
        raise ValueError("bls_baselines.csv must contain a 'genai_bias_search_term' column.")
    missing_demo = [c for c in DEMO_COLS if c not in bls.columns]
    if missing_demo:
        raise ValueError(f"bls_baselines.csv missing columns: {missing_demo}")
    bls = clean_occ(bls, "genai_bias_search_term")
    bls = ensure_numeric(bls, DEMO_COLS)
    return bls[["genai_bias_search_term"] + DEMO_COLS].rename(
        columns={"genai_bias_search_term": "occupation", **{c: f"bls_{c}" for c in DEMO_COLS}}
    )

def extract_model_name(filename):
    base = os.path.basename(filename)
    suffix = "_percentages_across_40_careers.csv"
    return base[: -len(suffix)] if base.endswith(suffix) else os.path.splitext(base)[0]

def main():
    if not os.path.exists(BLS_FILE):
        raise FileNotFoundError(f"Missing required file: {BLS_FILE}")
    bls = load_bls(BLS_FILE)

    model_files = sorted(glob.glob(INPUT_GLOB))
    if not model_files:
        raise FileNotFoundError(f"No model CSVs matched pattern: {INPUT_GLOB}")

    out_rows = []

    for path in model_files:
        model_name = extract_model_name(path)
        df = pd.read_csv(path)

        if "occupation" not in df.columns:
            raise ValueError(f"{path} must contain an 'occupation' column.")
        missing_demo = [c for c in DEMO_COLS if c not in df.columns]
        if missing_demo:
            raise ValueError(f"{path} missing columns: {missing_demo}")

        df = clean_occ(df, "occupation")
        df = ensure_numeric(df, DEMO_COLS)
        df = df[["occupation"] + DEMO_COLS]

        merged = df.merge(bls, on="occupation", how="left", validate="many_to_one")

        if merged[[f"bls_{c}" for c in DEMO_COLS]].isna().any().any():
            missing = merged[merged[f"bls_{DEMO_COLS[0]}"].isna()]["occupation"].unique()
            raise ValueError(f"BLS baselines missing for occupations in {path}: {missing}")

        # Differences in percentage points: BLS − model
        diff = pd.DataFrame()
        diff["occupation"] = merged["occupation"]
        diff["model_name"] = model_name
        for c in DEMO_COLS:
            diff[f"diff_{c}"] = merged[f"bls_{c}"] - merged[c]

        out_rows.append(diff)

    out = pd.concat(out_rows, ignore_index=True)
    out["occupation"] = out["occupation"].str.title()  # optional prettify

    cols = ["occupation", "model_name"] + [f"diff_{c}" for c in DEMO_COLS]
    out = out[cols]

    # 🔹 Round numeric columns to 2 decimal places
    for c in [f"diff_{col}" for col in DEMO_COLS]:
        out[c] = out[c].round(2)

    out.to_csv(OUT_FILE, index=False)
    print(f"Wrote {OUT_FILE} with {len(out)} rows from {len(model_files)} model file(s).")

if __name__ == "__main__":
    main()
