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

# Output paths (PDFs)
OUTPUT_PDF_FULL = "occupational_bias_multirace_avgTop_jitter.pdf"
OUTPUT_PDF_AVG  = "occupational_bias_averages_only.pdf"
OUTPUT_PDF_GENDER_FULL = "occupational_bias_gender_avgTop_jitter.pdf"
OUTPUT_PDF_GENDER_AVG  = "occupational_bias_gender_averages_only.pdf"

# ----------------------------
# Helpers
# ----------------------------
def nice_from_key(key: str) -> str:
    s = key.strip().replace("_", " ")
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = " ".join(s.split())
    return s.title()

# ----------------------------
# Load, validate, reshape model diffs
# ----------------------------
frames = []
for model_key, file_path in MODEL_FILES.items():
    df = pd.read_csv(file_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{file_path} missing columns: {missing}")

    subset = df[[
        "occupation",
        "diff_p_women", "diff_p_white", "diff_p_black", "diff_p_asian", "diff_p_hispanic"
    ]].copy()
    subset["occ_key"] = subset["occupation"].astype(str).str.strip()  # key for joins / ordering
    subset["model"] = model_key  # internal key

    # ----- RACE long -----
    race_long = subset.melt(
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
    race_long["race"] = race_long["race_col"].map(race_map)
    race_long.drop(columns=["race_col"], inplace=True)
    race_long["model"] = race_long["model"].map(DISPLAY_NAMES)
    race_long["kind"] = "race"

    # ----- GENDER long -----
    # Men is the inverse of Women: diff_p_men = -diff_p_women
    g_women = subset[["occ_key", "model", "diff_p_women"]].copy()
    g_women["gender"] = "Women"
    g_women["diff"] = g_women["diff_p_women"]

    g_men = subset[["occ_key", "model", "diff_p_women"]].copy()
    g_men["gender"] = "Men"
    g_men["diff"] = -g_men["diff_p_women"]  # inverse

    gender_long = pd.concat([g_women, g_men], ignore_index=True)
    gender_long.drop(columns=["diff_p_women"], inplace=True)
    gender_long["model"] = gender_long["model"].map(DISPLAY_NAMES)
    gender_long["kind"] = "gender"

    frames.append((race_long, gender_long))

# Combine all models
race_all   = pd.concat([r for r, _ in frames], ignore_index=True)
gender_all = pd.concat([g for _, g in frames], ignore_index=True)

# Keep only intended races (just in case)
race_all = race_all[race_all["race"].isin(RACES)].copy()

# ----------------------------
# Occupation label mapping (alphabetized list you provided)
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

# Map sorted occ_keys -> provided labels (Title Case for display)
unique_keys = sorted(race_all["occ_key"].unique())
if len(unique_keys) != len(OCCUPATION_LABELS):
    print(f"Warning: {len(unique_keys)} unique occ_keys vs {len(OCCUPATION_LABELS)} labels; zipping to the shorter length.")
clean_label_map = {k: v.title() for k, v in zip(unique_keys, OCCUPATION_LABELS)}

# ----------------------------
# Ordering by Men (overrepresented -> underrepresented)
# ----------------------------
men_only = gender_all[gender_all["gender"] == "Men"]
men_means = men_only.groupby("occ_key")["diff"].mean().sort_values(ascending=False)
ordered_occ_keys = list(men_means.index)

# ----------------------------
# Averages (for separate viz + top row)
# ----------------------------
avg_top_race = race_all.groupby(["race", "model"])["diff"].mean().reset_index()
avg_top_gender = gender_all.groupby(["gender", "model"])["diff"].mean().reset_index()

# ----------------------------
# Prepare wide tables by race (index = occ_key; columns = model)
# ----------------------------
by_race = {}
for race in RACES:
    sub = race_all[race_all["race"] == race]
    wide = sub.pivot_table(index="occ_key", columns="model", values="diff", aggfunc="mean")
    wide = wide.reindex(ordered_occ_keys)
    for m in DISPLAY_ORDER:
        if m not in wide.columns:
            wide[m] = np.nan
    wide = wide[DISPLAY_ORDER]

    avg_row = (
        avg_top_race[avg_top_race["race"] == race]
        .set_index("model")["diff"]
        .reindex(DISPLAY_ORDER)
        .rename("__AVG__")
        .to_frame().T
    )
    by_race[race] = pd.concat([avg_row, wide], axis=0)

# ----------------------------
# Prepare wide tables by gender (index = occ_key; columns = model)
# ----------------------------
GENDERS = ["Women", "Men"]
by_gender = {}
for g in GENDERS:
    sub = gender_all[gender_all["gender"] == g]
    wide = sub.pivot_table(index="occ_key", columns="model", values="diff", aggfunc="mean")
    wide = wide.reindex(ordered_occ_keys)
    for m in DISPLAY_ORDER:
        if m not in wide.columns:
            wide[m] = np.nan
    wide = wide[DISPLAY_ORDER]

    avg_row = (
        avg_top_gender[avg_top_gender["gender"] == g]
        .set_index("model")["diff"]
        .reindex(DISPLAY_ORDER)
        .rename("__AVG__")
        .to_frame().T
    )
    by_gender[g] = pd.concat([avg_row, wide], axis=0)

# ----------------------------
# Smart jitter for overlaps
# ----------------------------
def smart_offsets(values_dict, tol=3.0, base_jitter=0.18):
    keys = list(values_dict.keys())
    used, groups = set(), []
    for i, k in enumerate(keys):
        if k in used:
            continue
        group = [k]
        used.add(k)
        for j in range(i + 1, len(keys)):
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
        start = -(k/2 - 0.5) if k % 2 == 0 else -(k//2)
        for idx, name in enumerate(sorted(g)):
            offsets[name] = (start + idx) * base_jitter
    return offsets

# ----------------------------
# PLOTTING HELPERS
# ----------------------------
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

def plot_matrix(by_dim, dim_labels, title, outfile, xlab="Difference from BLS (percentage-point difference)"):
    n = len(dim_labels)
    fig, axes = plt.subplots(1, n, figsize=(5*n, 18), sharey=True)

    for ax, label in zip(axes, dim_labels):
        wide = by_dim[label]  # index: ["__AVG__", *occ_keys]
        ykeys   = ["__AVG__"] + [k for k in wide.index if k != "__AVG__"]
        ylabels = ["Average"] + [clean_label_map.get(k, nice_from_key(k)) for k in ordered_occ_keys]

        wide = wide.reindex(ykeys)
        y = np.arange(len(ykeys))

        ax.axvline(0, linewidth=1, linestyle="--")
        ax.set_xlim(-100, 100)
        ax.set_title(label, fontsize=14, pad=8)
        ax.set_yticks(y)
        ax.set_yticklabels(ylabels, fontsize=9)
        ax.set_ylim(len(y) - 0.5, -0.5)  # Average at top

        for tick in ax.yaxis.get_ticklabels():
            if tick.get_text() == "Average":
                tick.set_fontweight("bold")

        for yi, key in enumerate(ykeys):
            row_vals = {m: float(wide.loc[key, m]) if pd.notna(wide.loc[key, m]) else np.nan
                        for m in DISPLAY_ORDER}
            offsets = smart_offsets(row_vals, tol=3.0, base_jitter=0.18)
            for m in DISPLAY_ORDER:
                if pd.isna(row_vals[m]): continue
                ax.scatter(
                    row_vals[m], yi + offsets[m],
                    marker=markers[m],
                    s=55 if key == "__AVG__" else 42,
                    color=colors[m],
                    edgecolor="black",
                    linewidths=0.4,
                    zorder=3,
                    label=m if (label == dim_labels[0] and key == "__AVG__") else None
                )

        ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.55)
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

    # Title + shared x-label
    fig.suptitle(title, fontsize=40, fontweight="bold", y=0.97)
    fig.supxlabel(xlab, fontsize=20, y=0.06)

    # Single shared legend at top-left under the title
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
    handles, labels,
    title="Model",
    loc="upper left",
    bbox_to_anchor=(0.01, 0.90),   # moved down from 0.955
    frameon=True
    )
    fig.suptitle(title, fontsize=40, fontweight="bold", y=0.965)  # tiny nudge down
    plt.tight_layout(rect=[0.03, 0.08, 0.98, 0.90])  # leave room for legend

    plt.tight_layout(rect=[0.03, 0.08, 0.98, 0.93])
    plt.savefig(outfile, bbox_inches="tight")
    print(f"Saved figure: {Path(outfile).resolve()}")

def plot_averages_only(by_dim, dim_labels, title, outfile, xlab="Difference from BLS (percentage-point difference)"):
    n = len(dim_labels)
    fig, axes = plt.subplots(1, n, figsize=(4*n, 4), sharey=True)

    for ax, label in zip(axes, dim_labels):
        row = by_dim[label].loc["__AVG__"].reindex(DISPLAY_ORDER)
        ax.axvline(0, linewidth=1, linestyle="--")
        ax.set_xlim(-100, 100)
        ax.set_title(label, fontsize=12, pad=6)
        ax.set_yticks([0])
        ax.set_yticklabels(["Average"])
        ax.set_ylim(0.5, -0.5)

        for m in DISPLAY_ORDER:
            val = row[m]
            if pd.isna(val): continue
            ax.scatter(
                val, 0,
                marker=markers[m],
                s=70,
                color=colors[m],
                edgecolor="black",
                linewidths=0.5,
                zorder=3,
                label=m if label == dim_labels[0] else None
            )
        ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

    fig.suptitle(title, fontsize=16, fontweight="bold", y=1.05)
    fig.supxlabel(xlab, fontsize=12, y=0.02)

    handles2, labels2 = axes[0].get_legend_handles_labels()
    fig.legend(handles2, labels2, title="Model", loc="upper left", bbox_to_anchor=(0.5, 1.02), frameon=True, fontsize=9)

    plt.tight_layout()
    plt.savefig(outfile, bbox_inches="tight")
    print(f"Saved figure: {Path(outfile).resolve()}")

# ----------------------------
# PLOT: Race (existing)
# ----------------------------
plot_matrix(
    by_dim=by_race,
    dim_labels=RACES,
    title="Racial Representation Across 41 Occupations",
    outfile=OUTPUT_PDF_FULL,
)

plot_averages_only(
    by_dim=by_race,
    dim_labels=RACES,
    title="Racial Representation Across 41 Occupations — Averages Only",
    outfile=OUTPUT_PDF_AVG,
)

# ----------------------------
# PLOT: Gender (Women & Men) using p_women and inverse for Men
# ----------------------------
plot_matrix(
    by_dim=by_gender,
    dim_labels=GENDERS,
    title="Gender Representation Across 41 Occupations",
    outfile=OUTPUT_PDF_GENDER_FULL,
)

plot_averages_only(
    by_dim=by_gender,
    dim_labels=GENDERS,
    title="Gender Representation Across 41 Occupations — Averages Only",
    outfile=OUTPUT_PDF_GENDER_AVG,
)
