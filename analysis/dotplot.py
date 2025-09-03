import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ----------------------------
# CONFIG: paths to your 4 CSVs
# ----------------------------
MODEL_FILES = {
    "ChatGPT":  "percent-results/results_vs_BLS/openai_differences_vs_bls.csv",
    "Gemini":   "percent-results/results_vs_BLS/gemini_differences_vs_bls.csv",
    "DeepSeek": "percent-results/results_vs_BLS/deepseek_differences_vs_bls.csv",
    "Mistral":  "percent-results/results_vs_BLS/mistral_differences_vs_bls.csv",
}

# Desired display names (and plotting order)
DISPLAY_NAMES = {
    "ChatGPT":  "GPT 4.0",
    "DeepSeek": "DeepSeek V3.1",
    "Gemini":   "Gemini 2.5",
    "Mistral":  "Mistral-medium",
}
DISPLAY_ORDER = ["GPT 4.0", "DeepSeek V3.1", "Gemini 2.5", "Mistral-medium"]

# Races in the order you want shown (and used for White-based sorting)
RACES = ["White", "Hispanic", "Black", "Asian"]

# Column names in the CSVs (expected)
REQUIRED_COLS = [
    "occupation",
    "diff_p_women", "diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"
]

# Output paths
OUTPUT_PDF_FULL = "occupational_bias_multirace_avgTop_jitter.pdf"
OUTPUT_PDF_AVG  = "occupational_bias_averages_only.pdf"
# ----------------------------
# Load, validate, and reshape
# ----------------------------
frames = []
for model_key, file_path in MODEL_FILES.items():
    df = pd.read_csv(file_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{file_path} missing columns: {missing}")

    subset = df[["occupation", "diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"]].copy()
    subset["model"] = model_key  # internal key

    long = subset.melt(
        id_vars=["occupation", "model"],
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
    long = long.drop(columns=["race_col"])

    # Map internal key -> display name
    long["model"] = long["model"].map(DISPLAY_NAMES)

    frames.append(long)

all_long = pd.concat(frames, ignore_index=True)
all_long = all_long[all_long["race"].isin(RACES)].copy()

# Ensure occupations are consistent across models (intersection)
occ_by_model = {
    k: set(all_long[all_long["model"] == DISPLAY_NAMES[k]]["occupation"].unique())
    for k in MODEL_FILES.keys()
}
common_occupations = set.intersection(*occ_by_model.values())
if not common_occupations:
    raise ValueError("No common occupations across the four model CSVs.")
if any(len(v) != len(common_occupations) for v in occ_by_model.values()):
    all_long = all_long[all_long["occupation"].isin(common_occupations)].copy()

# ----------------------------
# Order occupations by White avg across models (under → over)
# ----------------------------
white_only = all_long[all_long["race"] == "White"]
white_means = (
    white_only.groupby("occupation")["diff"]
    .mean()
    .sort_values(ascending=True)
)
ordered_occupations = list(white_means.index)

# ----------------------------
# Compute per-race, per-model averages (for separate viz + top row)
# ----------------------------
avg_top = (
    all_long.groupby(["race", "model"])["diff"]
    .mean()
    .reset_index()
)

# ----------------------------
# Build wide tables per race (index=occupation; columns=model)
# then prepend an "Average" row as index 0
# ----------------------------
by_race = {}
for race in RACES:
    sub = all_long[all_long["race"] == race]
    wide = sub.pivot_table(index="occupation", columns="model", values="diff", aggfunc="mean")
    wide = wide.reindex(ordered_occupations)

    # Ensure columns in display order
    for mname in DISPLAY_ORDER:
        if mname not in wide.columns:
            wide[mname] = np.nan
    wide = wide[DISPLAY_ORDER]

    # Average row
    avg_row = (
        avg_top[avg_top["race"] == race]
        .set_index("model")["diff"]
        .rename("Average")
        .reindex(DISPLAY_ORDER)
        .to_frame().T
    )
    # Prepend Average explicitly
    wide_with_top = pd.concat([avg_row, wide], axis=0)
    by_race[race] = wide_with_top

# ----------------------------
# Plot helpers: smart jitter only for overlaps / near-equals
# ----------------------------
def smart_offsets(values_dict, tol=3.0, base_jitter=0.18):
    """
    values_dict: {model_name: x_value}
    tol: closeness in percentage points to consider "overlapping"
    base_jitter: vertical offset unit
    """
    keys = list(values_dict.keys())
    used = set()
    groups = []
    for i, k in enumerate(keys):
        if k in used:
            continue
        group = [k]
        used.add(k)
        for j in range(i+1, len(keys)):
            k2 = keys[j]
            if k2 in used:
                continue
            xv, xw = values_dict[k], values_dict[k2]
            if pd.notna(xv) and pd.notna(xw) and abs(xv - xw) <= tol:
                group.append(k2)
                used.add(k2)
        groups.append(group)

    offsets = {k: 0.0 for k in keys}
    for g in groups:
        k = len(g)
        if k == 1:
            continue
        # symmetric offsets around 0
        start = -(k/2 - 0.5) if k % 2 == 0 else -(k//2)
        for idx, name in enumerate(sorted(g)):  # deterministic order
            offsets[name] = (start + idx) * base_jitter
    return offsets

# ----------------------------
# MAIN FIGURE (Average row at the TOP)
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

for ax, race in zip(axes, RACES):
    wide = by_race[race]  # index: ["Average", *occupations]

    # Make sure "Average" is first in labels and in data
    ylabels = ["Average"] + [i for i in wide.index if i != "Average"]
    wide = wide.reindex(ylabels)

    y = np.arange(len(ylabels))

    # Axes / scales
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlim(-100, 100)
    ax.set_title(race, fontsize=13, pad=8)
    ax.set_yticks(y)
    ax.set_yticklabels(ylabels, fontsize=9)
    ax.set_xlabel("Δ from BLS (percentage points)")

    # HARD-SET the y-limits so index 0 ("Average") is at the visual TOP
    ax.set_ylim(len(ylabels) - 0.5, -0.5)

    # Bold the "Average" label
    for tick in ax.yaxis.get_ticklabels():
        if tick.get_text() == "Average":
            tick.set_fontweight("bold")

    # Plot with smart jitter per row
    for yi, occ in enumerate(ylabels):
        row_vals = {m: float(wide.loc[occ, m]) if pd.notna(wide.loc[occ, m]) else np.nan
                    for m in DISPLAY_ORDER}
        offsets = smart_offsets(row_vals, tol=3.0, base_jitter=0.18)
        for m in DISPLAY_ORDER:
            if pd.isna(row_vals[m]):
                continue
            ax.scatter(
                row_vals[m],
                yi + offsets[m],
                marker=markers[m],
                s=55 if occ == "Average" else 42,
                color=colors[m],
                edgecolor="black",
                linewidths=0.4,
                zorder=3,
                label=m if (race == "White" and occ == "Average") else None
            )

    # Faint separator below the Average row (y=0.5 because Average is at y=0)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.55)
    ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

# Single legend
axes[0].legend(
    title="Model",
    loc="upper left", 
    bbox_to_anchor=(0.5, 1),  # nudges it just above the axes, left-aligned
    frameon=True
)

plt.suptitle(
    "Occupational Representation vs. BLS by Race — Average Row at Top\n(negative = underrepresented, positive = overrepresented)",
    y=0.92, fontsize=14
)
plt.tight_layout(rect=[0.05, 0.01, 0.98, 0.92])

plt.savefig(OUTPUT_PDF_FULL, dpi=220, bbox_inches="tight")
print(f"Saved figure to: {Path(OUTPUT_PDF_FULL).resolve()}")
# ----------------------------
# SEPARATE FIGURE: AVERAGES ONLY
# ----------------------------
# Build a compact figure with just the averages per race
fig2, axes2 = plt.subplots(1, 4, figsize=(16, 4), sharey=True)

for ax, race in zip(axes2, RACES):
    # One row: "Average", columns are models
    row = by_race[race].loc["Average"].reindex(DISPLAY_ORDER)

    # y=0 line, place points with slight markers; show y label as "Average"
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlim(-100, 100)
    ax.set_title(f"{race}", fontsize=12, pad=6)
    ax.set_yticks([0])
    ax.set_yticklabels(["Average"])
    ax.set_xlabel("Δ from BLS (pp)")
    ax.set_ylim(0.5, -0.5)  # put "Average" at top (single row)

    # Scatter the averages
    for m in DISPLAY_ORDER:
        val = row[m]
        if pd.isna(val):
            continue
        ax.scatter(
            val, 0,
            marker=markers[m],
            s=70,
            color=colors[m],
            edgecolor="black",
            linewidths=0.5,
            zorder=3,
            label=m if race == "White" else None  # legend only once
        )
    ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

# Single legend for the averages figure
axes2[0].legend(
    title="Model",
    loc="upper left",
    bbox_to_anchor=(0, 1.05),
    frameon=True,
    fontsize=9
)
plt.suptitle("Averages Only — Δ from BLS by Race", y=1.05, fontsize=13)
plt.tight_layout()

# Save averages-only figure
plt.savefig(OUTPUT_PDF_AVG, dpi=220, bbox_inches="tight")
print(f"Saved figure to: {Path(OUTPUT_PDF_AVG).resolve()}")