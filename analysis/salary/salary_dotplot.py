import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re

# ----------------------------
# INPUT
# ----------------------------
INPUT_CSV = "results/combined_models_comparison.csv"

DISPLAY_ORDER = ["GPT 4.0", "DeepSeek V3.1", "Gemini 2.5", "Mistral-medium"]

MODEL_COLS = {
    "GPT 4.0": "openai",
    "Gemini 2.5": "gemini",
    "DeepSeek V3.1": "deepseek",
    "Mistral-medium": "mistral"
}

OUTPUT_PDF = "occupational_salary_bias_dotplot.pdf"
OUTPUT_CSV = "occupational_salary_bias_points.csv"

# ----------------------------
# Helpers
# ----------------------------
OCCUPATION_DISPLAY = {
    "administrativeassistant": "Administrative Assistant",
    "author": "Author",
    "bartender": "Bartender",
    "biologist": "Biologist",
    "buildinginspector": "Building Inspector",
    "busdriver": "Bus Driver",
    "butcher": "Butcher",
    "chef": "Chef",
    "chemist": "Chemist",
    "chiefexecutiveofficer": "Chief Executive Officer",
    "childcareworker": "Childcare Worker",
    "computerprogrammer": "Computer Programmer",
    "constructionworker": "Construction Worker",
    "cook": "Cook",
    "craneoperator": "Crane Operator",
    "custodian": "Custodian",
    "customerservicerepresentative": "Customer Service Representative",
    "doctor": "Doctor",
    "drafter": "Drafter",
    "electrician": "Electrician",
    "engineer": "Engineer",
    "garbagecollector": "Garbage Collector",
    "housekeeper": "Housekeeper",
    "insurancesalesagent": "Insurance Sales Agent",
    "labtech": "Lab Tech",
    "librarian": "Librarian",
    "mailcarrier": "Mail Carrier",
    "nurse": "Nurse",
    "nursepractitioner": "Nurse Practitioner",
    "pharmacist": "Pharmacist",
    "pilot": "Pilot",
    "plumber": "Plumber",
    "policeofficer": "Police Officer",
    "primaryschoolteacher": "Primary School Teacher",
    "receptionist": "Receptionist",
    "roofer": "Roofer",
    "securityguard": "Security Guard",
    "softwaredeveloper": "Software Developer",
    "specialedteacher": "Special Ed Teacher",
    "truckdriver": "Truck Driver",
    "welder": "Welder",
}

def nice_from_key(key: str):
    """Map raw occupation key to a human-readable display name."""
    s = key.strip().lower()
    if s in OCCUPATION_DISPLAY:
        return OCCUPATION_DISPLAY[s]
    # Fallback: insert spaces between case transitions, underscores, then title-case
    fallback = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key.strip())
    fallback = fallback.replace("_", " ")
    return fallback.title()

# ----------------------------
# Load data
# ----------------------------
df = pd.read_csv(INPUT_CSV)

# Remove empty last row if present
df = df.dropna(subset=["occupation"])

# ----------------------------
# Convert to long format
# ----------------------------
rows = []

for _, r in df.iterrows():

    occ = r["occupation"]
    bls = r["bls"]

    for model, col in MODEL_COLS.items():

        ai_salary = r[col]

        pct_diff = ((ai_salary - bls) / bls) * 100

        rows.append({
            "occupation": occ,
            "model": model,
            "pct_diff": pct_diff
        })

long = pd.DataFrame(rows)

# ----------------------------
# Order occupations by mean bias
# ----------------------------
occ_means = (
    long.groupby("occupation")["pct_diff"]
    .mean()
    .sort_values(ascending=False)
)

ordered_occs = list(occ_means.index)

# ----------------------------
# Create wide table
# ----------------------------
wide = long.pivot_table(
    index="occupation",
    columns="model",
    values="pct_diff"
)

wide = wide.reindex(ordered_occs)

for m in DISPLAY_ORDER:
    if m not in wide.columns:
        wide[m] = np.nan

wide = wide[DISPLAY_ORDER]

# Average row
avg_row = wide.mean().to_frame().T
avg_row.index = ["__AVG__"]

wide = pd.concat([avg_row, wide])

# ----------------------------
# Smart jitter
# ----------------------------
def smart_offsets(values_dict, tol=3.0, base_jitter=0.18):

    keys = list(values_dict.keys())
    offsets = {k:0 for k in keys}

    used = set()

    for i,k in enumerate(keys):

        if k in used:
            continue

        group=[k]
        used.add(k)

        for j in range(i+1,len(keys)):
            k2=keys[j]

            if k2 in used:
                continue

            if abs(values_dict[k]-values_dict[k2]) <= tol:
                group.append(k2)
                used.add(k2)

        if len(group)>1:

            start = -(len(group)/2 - 0.5)

            for idx,name in enumerate(sorted(group)):
                offsets[name]=(start+idx)*base_jitter

    return offsets

# ----------------------------
# Plot
# ----------------------------
fig, ax = plt.subplots(figsize=(10,16))

markers = {
    "GPT 4.0": "o",
    "DeepSeek V3.1": "D",
    "Gemini 2.5": "s",
    "Mistral-medium": "^"
}

colors = {
    "GPT 4.0": "#0072B2",
    "DeepSeek V3.1": "#009E73",
    "Gemini 2.5": "#E69F00",
    "Mistral-medium": "#CC79A7",
}

ykeys = ["__AVG__"] + ordered_occs
ylabels = ["Average"] + [nice_from_key(o) for o in ordered_occs]

wide = wide.reindex(ykeys)

y = np.arange(len(ykeys))

ax.axvline(0, linestyle="--")

points=[]

for yi,key in enumerate(ykeys):

    row_vals = {
        m:wide.loc[key,m] for m in DISPLAY_ORDER
    }

    offsets = smart_offsets(row_vals)

    for m in DISPLAY_ORDER:

        val=row_vals[m]

        if pd.isna(val):
            continue

        y_pos = yi + offsets[m]

        ax.scatter(
            val,
            y_pos,
            marker=markers[m],
            s=60 if key=="__AVG__" else 42,
            color=colors[m],
            edgecolor="black",
            linewidths=0.4,
            label=m if key=="__AVG__" else None
        )

        points.append({
            "occupation": "Average" if key=="__AVG__" else nice_from_key(key),
            "model": m,
            "percent_difference": val
        })

ax.set_yticks(y)
ax.set_yticklabels(ylabels)

ax.set_xlim(-100,100)

fig.suptitle(
    "Per Occupation Salary Medians vs BLS",
    fontsize=22,
    fontweight="bold",
    y=0.97,
    x=0.5
)

fig.supxlabel(
    "Difference from BLS (percentage-point difference)",
    fontsize=20,
    y=0.05
)
ax.grid(axis="x", linestyle=":")

handles,labels=ax.get_legend_handles_labels()
fig.legend(
    handles, labels,
    title="Model",
    loc="upper left",              # anchor legend's top-left corner
    bbox_to_anchor=(1.00, 0.9),   # push right + near top
    fontsize=14,
    title_fontsize=18
)

plt.tight_layout(rect=[0.03, 0.08, 0.98, 0.98])
plt.savefig(OUTPUT_PDF, bbox_inches="tight")

print("Saved:",Path(OUTPUT_PDF).resolve())

pd.DataFrame(points).to_csv(OUTPUT_CSV,index=False)

print("Saved:",Path(OUTPUT_CSV).resolve())