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

# Only need these columns now
REQUIRED_COLS = ["occupation", "diff_p_women"]

# Output paths (PDFs) — women only
OUTPUT_PDF_WOMEN_FULL = "occupational_bias_women_avgTop_jitter.pdf"
OUTPUT_PDF_WOMEN_AVG  = "occupational_bias_women_averages_only.pdf"

# ----------------------------
# Helpers
# ----------------------------
def nice_from_key(key: str) -> str:
    s = key.strip().replace("_", " ")
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = " ".join(s.split())
    return s.title()

# ----------------------------
# Load, validate, reshape (Women only)
# ----------------------------
frames = []
for model_key, file_path in MODEL_FILES.items():
    df = pd.read_csv(file_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{file_path} missing columns: {missing}")

    subset = df[["occupation", "diff_p_women"]].copy()
    subset["occ_key"] = subset["occupation"].astype(str).str.strip()
    subset["model"] = model_key

    g_women = subset[["occ_key", "model", "diff_p_women"]].copy()
    g_women["gender"] = "Women"
    g_women["diff"] = g_women["diff_p_women"]
    g_women.drop(columns=["diff_p_women"], inplace=True)
    g_women["model"] = g_women["model"].map(DISPLAY_NAMES)

    frames.append(g_women)

# Combine all models (women)
gender_all = pd.concat(frames, ignore_index=True)

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

# Build mapping from sorted occ_keys -> provided labels
unique_keys = sorted(gender_all["occ_key"].unique())
if len(unique_keys) != len(OCCUPATION_LABELS):
    print(f"Warning: {len(unique_keys)} unique occ_keys vs {len(OCCUPATION_LABELS)} labels; zipping to the shorter length.")
clean_label_map = {k: v.title() for k, v in zip(unique_keys, OCCUPATION_LABELS)}

# ----------------------------
# Ordering by Women (overrepresented -> underrepresented)
# ----------------------------
ORDER_BY_WOMEN = True
if ORDER_BY_WOMEN:
    women_means = gender_all.groupby("occ_key")["diff"].mean().sort_values(ascending=False)
    ordered_occ_keys = list(women_means.index)
else:
    # Fallback (if you ever want to keep previous behavior): alphabetical
    ordered_occ_keys = sorted(gender_all["occ_key"].unique())

# ----------------------------
# Averages (for separate viz + top row)
# ----------------------------
avg_top_women = gender_all.groupby(["gender", "model"])["diff"].mean().reset_index()

# ----------------------------
# Prepare wide table for women (index = occ_key; columns = model)
# ----------------------------
sub = gender_all  # only women present
wide = sub.pivot_table(index="occ_key", columns="model", values="diff", aggfunc="mean")
wide = wide.reindex(ordered_occ_keys)

for m in DISPLAY_ORDER:
    if m not in wide.columns:
        wide[m] = np.nan
wide = wide[DISPLAY_ORDER]

avg_row = (
    avg_top_women[avg_top_women["gender"] == "Women"]
    .set_index("model")["diff"]
    .reindex(DISPLAY_ORDER)
    .rename("__AVG__")
    .to_frame().T
)

by_women = pd.concat([avg_row, wide], axis=0)

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

def plot_matrix_women(by_women, title, outfile, xlab="Difference from BLS (percentage-point difference)"):
    # Single panel, women only
    fig, ax = plt.subplots(1, 1, figsize=(5, 18), sharey=True)

    wide = by_women  # index: ["__AVG__", *occ_keys]
    ykeys   = ["__AVG__"] + [k for k in wide.index if k != "__AVG__"]
    ylabels = ["Average"] + [clean_label_map.get(k, nice_from_key(k)) for k in ordered_occ_keys]

    wide = wide.reindex(ykeys)
    y = np.arange(len(ykeys))

    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlim(-100, 100)
    ax.set_title("Women", fontsize=14, pad=8)
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
                label=m if key == "__AVG__" else None
            )

    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.55)
    ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

    # Title + shared x-label
    fig.suptitle(title, fontsize=40, fontweight="bold", y=0.965)
    fig.supxlabel(xlab, fontsize=20, y=0.06)

    # Single shared legend under the title, left
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles, labels,
        title="Model",
        loc="upper left",
        bbox_to_anchor=(0.01, 0.90),
        frameon=True
    )

    plt.tight_layout(rect=[0.03, 0.08, 0.98, 0.93])
    plt.savefig(outfile, bbox_inches="tight")
    print(f"Saved figure: {Path(outfile).resolve()}")

def plot_averages_only_women(by_women, title, outfile, xlab="Difference from BLS (percentage-point difference)"):
    fig, ax = plt.subplots(1, 1, figsize=(4, 4), sharey=True)
    row = by_women.loc["__AVG__"].reindex(DISPLAY_ORDER)
    ax.axvline(0, linewidth=1, linestyle="--")
    ax.set_xlim(-100, 100)
    ax.set_title("Women", fontsize=12, pad=6)
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
            label=m
        )
    ax.grid(axis="x", linestyle=":", linewidth=0.8, alpha=0.7)

    fig.suptitle(title, fontsize=16, fontweight="bold", y=1.05)
    fig.supxlabel(xlab, fontsize=12, y=0.02)

    handles2, labels2 = ax.get_legend_handles_labels()
    fig.legend(handles2, labels2, title="Model", loc="upper left", bbox_to_anchor=(0.5, 1.02), frameon=True, fontsize=9)

    plt.tight_layout()
    plt.savefig(outfile, bbox_inches="tight")
    print(f"Saved figure: {Path(outfile).resolve()}")

# ----------------------------
# PLOT: Women only
# ----------------------------
plot_matrix_women(
    by_women=by_women,
    title="Women’s Representation Across 41 Occupations",
    outfile=OUTPUT_PDF_WOMEN_FULL,
)

plot_averages_only_women(
    by_women=by_women,
    title="Women’s Representation Across 41 Occupations — Averages Only",
    outfile=OUTPUT_PDF_WOMEN_AVG,
)
