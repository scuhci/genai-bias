import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path

# ----------------------------
# CONFIG: paths to your CSVs
# ----------------------------
MODEL_FILES = {
    "ChatGPT":  "percent-results/results_vs_BLS/openai_differences_vs_bls.csv",
    "Gemini":   "percent-results/results_vs_BLS/gemini_differences_vs_bls.csv",
    "DeepSeek": "percent-results/results_vs_BLS/deepseek_differences_vs_bls.csv",
    "Mistral":  "percent-results/results_vs_BLS/mistral_differences_vs_bls.csv",
}

# BLS baselines (used only to map clean occupation labels)
# Must include columns: "Occupation", "genai_bias_search_term"
BLS_BASELINES = "../profiles/bls-baselines.csv"  # <-- update this if needed

# Desired display names and plotting order
DISPLAY_NAMES = {
    "ChatGPT":  "GPT 4.0",
    "DeepSeek": "DeepSeek V3.1",
    "Gemini":   "Gemini 2.5",
    "Mistral":  "Mistral-medium",
}
DISPLAY_ORDER = ["GPT 4.0", "DeepSeek V3.1", "Gemini 2.5", "Mistral-medium"]

# Races (ordering) and required model-diff columns
RACES = ["White", "Hispanic", "Black", "Asian"]
REQUIRED_COLS = [
    "occupation",
    "diff_p_women", "diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"
]

# Output paths (PDFs + CSVs)
OUTPUT_PDF_FULL = "occupational_bias_multirace_avgTop_jitter.pdf"
OUTPUT_PDF_AVG  = "occupational_bias_averages_only.pdf"
OUTPUT_CSV_FULL = "occupational_bias_multirace_avgTop_jitter_points.csv"
OUTPUT_CSV_AVG  = "occupational_bias_averages_only_points.csv"

# ----------------------------
# Helpers
# ----------------------------
def nice_from_key(key: str) -> str:
    """Fallback cleaner if a BLS mapping is missing."""
    s = key.strip()
    s = s.replace("_", " ")
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = " ".join(s.split())
    return s.title()

# ----------------------------
# Load BLS label map
# ----------------------------
bls_df = pd.read_csv(BLS_BASELINES)
bls_df["genai_bias_search_term"] = bls_df["genai_bias_search_term"].astype(str).str.strip()
bls_df["Occupation"] = bls_df["Occupation"].astype(str).str.strip()
LABEL_MAP = dict(zip(bls_df["genai_bias_search_term"], bls_df["Occupation"]))

# ----------------------------
# Load, validate, reshape model diffs
# ----------------------------
frames = []
for model_key, file_path in MODEL_FILES.items():
    df = pd.read_csv(file_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{file_path} missing columns: {missing}")

    subset = df[["occupation", "diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"]].copy()
    subset["occ_key"] = subset["occupation"].astype(str).str.strip()
    subset["model"] = model_key

    long = subset.melt(
        id_vars=["occ_key", "model"],
        value_vars=["diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"],
        var_name="race_col",
        value_name="diff"
    )

    race_map = {
        "diff_p_white": "White",
        "diff_p_black": "Black",
        "diff_p_asian": "Asian",
        "diff_p_hispanic": "Hispanic",
    }
    long["race"] = long["race_col"].map(race_map)
    long.drop(columns=["race_col"], inplace=True)

    long["model"] = long["model"].map(DISPLAY_NAMES)
    frames.append(long)

all_long = pd.concat(frames, ignore_index=True)
all_long = all_long[all_long["race"].isin(RACES)].copy()

# ----------------------------
# Occupation label mapping
# ----------------------------
OCCUPATION_LABELS = [
    "administrative assistant",
    "author",
    "bartender",
    "biologist",
    "building inspector",
    "bus driver",
    "butcher",
    "chef",
    "chemist",
    "chief executive officer",
    "childcare worker",
    "computer programmer",
    "construction worker",
    "cook",
    "crane operator",
    "custodian",
    "customer service representative",
    "doctor",
    "drafter",
    "electrician",
    "engineer",
    "garbage collector",
    "housekeeper",
    "insurance sales agent",
    "lab tech",
    "librarian",
    "mail carrier",
    "nurse",
    "nurse practitioner",
    "pharmacist",
    "pilot",
    "plumber",
    "police officer",
    "primary school teacher",
    "receptionist",
    "roofer",
    "security guard",
    "software developer",
    "special ed teacher",
    "truck driver",
    "welder",
]

clean_label_map = {}
for key, nice in zip(sorted(all_long["occ_key"].unique()), OCCUPATION_LABELS):
    clean_label_map[key] = nice.title()

# Ordering: by White average across models, using occ_key
white_only = all_long[all_long["race"] == "White"]
white_means = white_only.groupby("occ_key")["diff"].mean().sort_values(ascending=True)
ordered_occ_keys = list(white_means.sort_values(ascending=False).index)

# Averages for separate viz + top row
avg_top = all_long.groupby(["race", "model"])["diff"].mean().reset_index()

# Prepare wide tables by race (index = occ_key; columns = model)
by_race = {}
for race in RACES:
    sub = all_long[all_long["race"] == race]
    wide = sub.pivot_table(index="occ_key", columns="model", values="diff", aggfunc="mean")
    wide = wide.reindex(ordered_occ_keys)
    for m in DISPLAY_ORDER:
        if m not in wide.columns:
            wide[m] = np.nan
    wide = wide[DISPLAY_ORDER]

    avg_row = (
        avg_top[avg_top["race"] == race]
        .set_index("model")["diff"]
        .reindex(DISPLAY_ORDER)
        .rename("__AVG__")
        .to_frame().T
    )
    wide_with_top = pd.concat([avg_row, wide], axis=0)
    by_race[race] = wide_with_top

# ----------------------------
# Smart jitter for overlaps
# ----------------------------
def smart_offsets(values_dict, tol=3.0, base_jitter=0.18):
    keys = list(values_dict.keys())
    used, groups = set(), []
    for i, k in enumerate(keys):
        if k in used:
            continue
        group = [k]; used.add(k)
        for j in range(i + 1, len(keys)):
            k2 = keys[j]
            if k2 in used:
                continue
            xv, xw = values_dict[k], values_dict[k2]
            if pd.notna(xv) and pd.notna(xw) and abs(xv - xw) <= tol:
                group.append(k2); used.add(k2)
        groups.append(group)

    offsets = {k: 0.0 for k in keys}
    for g in groups:
        k = len(g)
        if k == 1:
            continue
        start = -(k/2 - 0.5) if k % 2 == 0 else -(k//2)
        for idx, name in enumerate(sorted(g)):  # deterministic
            offsets[name] = (start + idx) * base_jitter
    return offsets

# ----------------------------
# MAIN FIGURE (Average at TOP) + CAPTURE PLOTTED DATA
# ----------------------------
fig, axes = plt.subplots(1, 4, figsize=(20, 18), sharey=True)

markers = {
    "GPT 4.0":         "o",
    "DeepSeek V3.1":   "D",
    "Gemini 2.5":      "s",
    "Mistral-medium":  "^",
}
colors  = {
    "GPT 4.0":         "#1f77b4",
    "DeepSeek V3.1":   "#2ca02c",
    "Gemini 2.5":      "#ff7f0e",
    "Mistral-medium":  "#d62728",
}

# Will store every point rendered in the main figure
full_points_rows = []

for ax, race in zip(axes, RACES):
    wide = by_race[race]  # index: ["__AVG__", *occ_keys]
    ykeys   = ["__AVG__"] + [k for k in wide.index if k != "__AVG__"]
    ylabels = ["Average"] + [clean_label_map[k] for k in ordered_occ_keys]

    # Ensure data aligned to keys
    wide = wide.reindex(ykeys)
    y = np.arange(len(ykeys))

    # Axes / scales
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlim(-100, 100)
    ax.set_title(race, fontsize=14, pad=8)
    ax.set_yticks(y)
    ax.set_yticklabels(ylabels, fontsize=9)
    ax.set_ylim(len(y) - 0.5, -0.5)  # Average at top

    for yi, key in enumerate(ykeys):
        row_vals = {m: float(wide.loc[key, m]) if pd.notna(wide.loc[key, m]) else np.nan
                    for m in DISPLAY_ORDER}
        offsets = smart_offsets(row_vals, tol=3.0, base_jitter=0.18)

        for m in DISPLAY_ORDER:
            val = row_vals[m]
            if pd.isna(val):
                continue
            y_off = offsets[m]
            y_pos = yi + y_off

            # Draw the point
            ax.scatter(
                val,
                y_pos,
                marker=markers[m],
                s=55 if key == "__AVG__" else 42,
                color=colors[m],
                edgecolor="black",
                linewidths=0.4,
                zorder=3,
                label=m if (race == "White" and key == "__AVG__") else None
            )

            # Record the point (for CSV)
            full_points_rows.append({
                "race": race,
                "is_average": (key == "__AVG__"),
                "occ_key": key,
                "occupation": "Average" if key == "__AVG__" else clean_label_map.get(key, nice_from_key(key)),
                "y_index": yi,
                "y_label": "Average" if key == "__AVG__" else clean_label_map.get(key, nice_from_key(key)),
                "model": m,
                "diff": val,                     # x on the plot
                "jitter_offset": y_off,          # vertical jitter applied
                "x": val,                        # alias for clarity
                "y": y_pos                       # final plotted y position
            })

    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.55)
    ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

# ---- Title (large + bold) and shared x-label ----
fig.suptitle("Per-Occupation Racial Representation vs. BLS", fontsize=40, fontweight="bold", y=0.97)
fig.supxlabel("Difference from BLS (percentage-point difference)", fontsize=20, y=0.06)

# Single shared legend at top-left under the title
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, title="Model", loc="upper left", bbox_to_anchor=(0.01, 0.955), frameon=True)

plt.tight_layout(rect=[0.03, 0.08, 0.98, 0.93])
plt.savefig(OUTPUT_PDF_FULL, bbox_inches="tight")
print(f"Saved figure: {Path(OUTPUT_PDF_FULL).resolve()}")

# Write plotted data for the main figure
full_points_df = pd.DataFrame(full_points_rows)
full_points_df.to_csv(OUTPUT_CSV_FULL, index=False)
print(f"Saved plotted points CSV: {Path(OUTPUT_CSV_FULL).resolve()}")

# ----------------------------
# SEPARATE FIGURE: AVERAGES ONLY + CAPTURE DATA
# ----------------------------
fig2, axes2 = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
avg_points_rows = []

for ax, race in zip(axes2, RACES):
    row = by_race[race].loc["__AVG__"].reindex(DISPLAY_ORDER)
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlim(-100, 100)
    ax.set_title(race, fontsize=12, pad=6)
    ax.set_yticks([0])
    ax.set_yticklabels(["Average"])
    ax.set_ylim(0.5, -0.5)  # show Average at top

    for m in DISPLAY_ORDER:
        val = row[m]
        if pd.isna(val):
            continue

        # Plot point
        ax.scatter(
            val, 0,
            marker=markers[m],
            s=70,
            color=colors[m],
            edgecolor="black",
            linewidths=0.5,
            zorder=3,
            label=m if race == "White" else None
        )

        # Record for CSV
        avg_points_rows.append({
            "race": race,
            "model": m,
            "is_average": True,
            "diff": float(val),
            "x": float(val),
            "y": 0.0,
            "y_label": "Average"
        })

    ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

fig2.suptitle("Racial Representation Across 41 Occupations — Averages Only", fontsize=16, fontweight="bold", y=1.05)
fig2.supxlabel("Difference from BLS (percentage-point difference)", fontsize=12, y=0.02)

handles2, labels2 = axes2[0].get_legend_handles_labels()
fig2.legend(handles2, labels2, title="Model", loc="upper left", bbox_to_anchor=(0.01, 1.02), frameon=True, fontsize=9)

plt.tight_layout()
plt.savefig(OUTPUT_PDF_AVG, bbox_inches="tight")
print(f"Saved figure: {Path(OUTPUT_PDF_AVG).resolve()}")

# Write averages-only plotted data CSV
avg_points_df = pd.DataFrame(avg_points_rows)
avg_points_df.to_csv(OUTPUT_CSV_AVG, index=False)
print(f"Saved averages-only points CSV: {Path(OUTPUT_CSV_AVG).resolve()}")
