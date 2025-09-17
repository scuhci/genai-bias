import pandas as pd
import os
import plotly.graph_objects as go

# Directory containing the GenAI CSVs
genai_dir = "../profiles/openai/csvs/"

# Path to the BLS baselines file (which has one row per ethnicity per career)
baseline_path = "../profiles/openai/bls-baselines.csv"

# Read the BLS baseline data: expect columns like
#   genai_bias_search_term | ethnicity | percent
baselines_data = pd.read_csv(baseline_path, encoding="cp1252")

mixed_data = []

for career_profiles in os.listdir(genai_dir):
    if not career_profiles.lower().endswith(".csv"):
        continue

    # 1) Read GenAI‐generated CSV
    genai_path = os.path.join(genai_dir, career_profiles)
    genai_data = pd.read_csv(genai_path, encoding="cp1252")

    # 2) Extract “career_term” from filename
    career_term = os.path.basename(career_profiles).split("profiles_openai.csv")[0]

    # 3) Compute GenAI mixed‐race % by counting commas in each “ethnicity” string
    if "ethnicity" not in genai_data.columns:
        continue
    genai_eth = genai_data["ethnicity"].fillna("").str.lower()
    genai_mixed_count = genai_eth.str.contains(",", regex=False).sum()
    genai_total = len(genai_eth)
    genai_mixed_pct = (
        round((genai_mixed_count / genai_total) * 100, 1)
        if genai_total > 0 else 0.0
    )

    # 4) Filter the BLS baseline rows for this career
    career_baseline = baselines_data[
        baselines_data["genai_bias_search_term"] == career_term
    ]
    career_baseline = (
      career_baseline[["p_white","p_black","p_asian","p_hispanic"]]
        .rename(columns=lambda c: c.replace("p_",""))  # drop the "p_" prefix
        .melt(var_name="ethnicity", value_name="percent")
    )
    # If there is no baseline entry or no “percent” column, assume 0% mixed
    if career_baseline.empty or "percent" not in career_baseline.columns:
        baseline_mixed_pct = 0.0
    else:
        # Sum the per‐ethnicity percents for this career
        total_baseline_pct = career_baseline["percent"].sum()
        # Any amount over 100% is “extra counts,” interpreted as mixed‐race
        baseline_mixed_pct = round(max(0, total_baseline_pct - 100), 1)
        
    mixed_data.append({
        "career": career_term,
        "percent_mixed_genai":     genai_mixed_pct,
        "percent_mixed_baseline":  baseline_mixed_pct
    })

# 5) Build a DataFrame and sort by career
mixed_df = pd.DataFrame(mixed_data).sort_values("career")

fig = go.Figure(data=[
    go.Table(
        header=dict(
            values=[
                "Career",
                "GenAI – % Mixed Race",
                "BLS Baseline – % Mixed Race"
            ],
            fill_color="lightgrey",
            align="left",
            font=dict(size=18)            # ← header font size
        ),
        cells=dict(
            values=[
                mixed_df["career"],
                mixed_df["percent_mixed_genai"],
                mixed_df["percent_mixed_baseline"]
            ],
            align="left",
            font=dict(size=14)            # ← cell font size
        )
    )
])

fig.update_layout(
    title_text="Mixed-Race % by Career (GenAI vs. BLS Baseline)",
    title_x=0.5,
    margin=dict(t=60, b=20, l=20, r=20)
)

fig.show()


# 7) Save as PNG
output_dir = "mixed_race_tables"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "mixed_race_by_career.pdf")
fig.write_image(output_path, width=800, height=1000)

print(f"Saved mixed-race percentages table to {output_path}")
