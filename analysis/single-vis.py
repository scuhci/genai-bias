import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
import plotly.graph_objects as go
import pandas as pd
import os

career_profiles = "../profiles/openai/csvs/welderprofiles_openai.csv"
baseline_dir_path = "../profiles/openai/bls-baselines.csv"

baselines_data = pd.read_csv(baseline_dir_path)

genai_data = pd.read_csv(career_profiles)

# get baseline data
this_career_term = "welder"
print("Generating visualizations for... " + this_career_term)
this_career_baseline_df = baselines_data[baselines_data["genai_bias_search_term"] == this_career_term]

print(this_career_baseline_df)

eth_cols = ["p_white","p_black","p_asian","p_hispanic"]

# race percentages DF

this_career_baseline_race_df = (
    this_career_baseline_df[eth_cols]
      .rename(columns=lambda c: c.replace("p_",""))  # drop the "p_" prefix
      .melt(var_name="ethnicity", value_name="percent")
)

print("Baseline Ethnicity Data")
print(this_career_baseline_race_df)
    
# merge any multi (i.e. hispanic, white) -> be included in both categories.
merge_races = (
    genai_data["ethnicity"]
      .str.lower()
      .str.split(",", expand=False)          # e.g. ["hispanic", " white"]
      .apply(lambda lst: [x.strip() for x in lst])  
      .explode()                              # now one ethnicity per row
  )
  
genai_race_df = (
      merge_races
        .str.lower()
        .value_counts(normalize=True)   # proportions
        .mul(100)                       # → percentages
        .reset_index(name="percent")    # make it a DF with column “percent”
        .rename(columns={"index":"ethnicity"})
  )

print("GenAI Ethnicity Data") 
print(genai_race_df)

race_diff_df = (
    genai_race_df
      .merge(this_career_baseline_race_df,
            on="ethnicity",
            how="outer",
            suffixes=("_genai", "_baseline"))
      .fillna({"percent_genai": 0, "percent_baseline": 0})
      .assign(difference=lambda df: 
                df["percent_genai"] - df["percent_baseline"])
      [["ethnicity", "difference"]]
)

# gender percentages DF
this_career_baseline_gender_df = (
  this_career_baseline_df
    .loc[:, ["p_women"]]
    .assign(p_men=lambda df: 100 - df["p_women"])
    .rename(columns={"p_women": "female", "p_men": "male"})
    .melt(var_name="gender", value_name="percent")
)
print("Baseline Gender Data") 
print(this_career_baseline_gender_df)

genai_gender_df = (
    genai_data["gender"]
      .str.lower()   
      .value_counts(normalize=True)
      .mul(100)
      .reset_index(name="percent")
      .rename(columns={"index":"gender"})
)

print("GenAI Gender Data") 
print(genai_gender_df)
gender_diff_df = (
    genai_gender_df
      .merge(this_career_baseline_gender_df,
            on="gender",
            how="outer",
            suffixes=("_genai", "_baseline"))
      .fillna({"percent_genai": 0, "percent_baseline": 0})
      .assign(difference=lambda df: 
                df["percent_genai"] - df["percent_baseline"])
      [["gender", "difference"]]
)
'''
Ethnicity visualizations
=============================================================
'''
main_eth = ["white", "black", "hispanic", "asian"]

# filter race_diff_df
plot_df = race_diff_df[race_diff_df["ethnicity"].isin(main_eth)]

# enforce a specific order
plot_df["ethnicity"] = pd.Categorical(
    plot_df["ethnicity"],
    categories=main_eth,
    ordered=True
)
'''
1. Over-under bar charts
'''
# build the over–under bar chart
fig = px.bar(
    plot_df,
    x="ethnicity",
    y="difference",
    color="difference",
    color_continuous_scale=["#d62728","#1fb451"],
    category_orders={"ethnicity": main_eth},
    labels={"difference":"% Deviation from BLS Baseline"},
    title=f"GPT 4.0 vs BLS Baselines - Ethnicity Distributions <br> Career Term: {this_career_term}"
)

fig.update_layout(coloraxis_showscale=False)
# format axis and add zero line
fig.update_yaxes(tickformat=",.1f%", ticksuffix="%")
fig.update_layout(shapes=[dict(
    type="line", x0=-0.5, x1=len(plot_df)-0.5,
    y0=0, y1=0, line=dict(color="black", dash="dash")
)])

print(f"Saved ethnicity over-under bar chart for: {this_career_term}")
fig.write_image(f"overunder-openai/{this_career_term}-eth.png")

'''
2. Diff Charts
These are fancy error plots.
'''
cmp = (
    genai_race_df
      .merge(this_career_baseline_race_df,
            on="ethnicity",
            how="outer",
            suffixes=("_genai","_baseline"))
      .fillna(0)    # missing → 0%
)

cmp = cmp[cmp["ethnicity"].isin(main_eth)]

cmp["ethnicity"] = pd.Categorical(
    cmp["ethnicity"],
    categories=main_eth,
    ordered=True
)

#compute error‐bar extents
cmp["err_up"]   = (cmp["percent_genai"]    - cmp["percent_baseline"]).clip(lower=0)
cmp["err_down"] = (cmp["percent_baseline"] - cmp["percent_genai"]   ).clip(lower=0)

fig = go.Figure()

# BLS (baseline) points + asymmetric error bars + labels
fig.add_trace(go.Scatter(
    x=cmp["ethnicity"],
    y=cmp["percent_baseline"],
    error_y=dict(
        type="data",
        array=cmp["err_up"],
        arrayminus=cmp["err_down"],
        thickness=1.5,
        width=3
    ),
    mode="markers+text",
    name="BLS",
    text=cmp["percent_baseline"].map(lambda x: f"{x:.1f}%"),
    textfont=dict(color="blue"), 
    textposition="middle right",
    marker=dict(symbol="circle", size=10)
))

# GenAI points + labels
fig.add_trace(go.Scatter(
    x=cmp["ethnicity"],
    y=cmp["percent_genai"],
    mode="markers+text",
    name="GenAI",
    text=cmp["percent_genai"].map(lambda x: f"{x:.1f}%"),
    textposition="middle left",
    textfont=dict(color="red"), 
    marker=dict(symbol="square", size=10)
))

# Layout tweaks
fig.update_yaxes(tickformat=",.1f%", ticksuffix="%")
fig.update_layout(
    title=f"GPT 4.0 vs BLS Baselines -  Ethnicity Distributions <br> Career Term: {this_career_term}",
    xaxis_title="Ethnicity",
    yaxis_title="Percent",
    legend_title="Dataset",
    width=1000, height=800
)

fig.write_image(f"diffchart-openai/{this_career_term}-eth.png")
print(f"Saved ethnicity diff chart for: {this_career_term}")
'''
=============================================================
'''
'''
Gender visualizations
=============================================================
'''

gender = ["male", "female"]

# filter gender_diff_df
plot_df = gender_diff_df[gender_diff_df["gender"].isin(gender)]

# enforce a specific order
plot_df["gender"] = pd.Categorical(
    plot_df["gender"],
    categories=gender,
    ordered=True
)
'''
1. Over-under bar charts
'''
# build the over–under bar chart
fig = px.bar(
    plot_df,
    x="gender",
    y="difference",
    color="difference",
    color_continuous_scale=["#d62728","#1fb451"],
    category_orders={"gender": gender},
    labels={"difference":"% Deviation from BLS Baseline"},
    title=f"GPT 4.0 vs BLS Baselines - Gender Distributions <br> Career Term: {this_career_term}"
)

fig.update_layout(coloraxis_showscale=False)
# format axis and add zero line
fig.update_yaxes(tickformat=",.1f%", ticksuffix="%")
fig.update_layout(shapes=[dict(
    type="line", x0=-0.5, x1=len(plot_df)-0.5,
    y0=0, y1=0, line=dict(color="black", dash="dash")
)])

print(f"Saved gender over-under bar chart for: {this_career_term}")
fig.write_image(f"overunder-openai/{this_career_term}-gender.png")

'''
2. Diff Charts
These are fancy error plots.
'''
cmp_gender = (
  genai_gender_df
    .merge(
        this_career_baseline_gender_df,
        on="gender",
        how="outer",
        suffixes=("_genai","_baseline")
    )
    .fillna(0)    # missing → 0%
)

# keep consistent order 
order = ["female", "male"]
cmp_gender["gender"] = pd.Categorical(
  cmp_gender["gender"],
  categories=order,
  ordered=True
)
#compute error‐bar extents
cmp_gender["err_up"]   = (cmp_gender["percent_genai"] - cmp_gender["percent_baseline"]).clip(lower=0)
cmp_gender["err_down"] = (cmp_gender["percent_baseline"] - cmp_gender["percent_genai"]).clip(lower=0)
fig = go.Figure()

# BLS (baseline) points + asymmetric error bars + labels
fig.add_trace(go.Scatter(
  x=cmp_gender["gender"],
  y=cmp_gender["percent_baseline"],
  error_y=dict(
      type="data",
      array=cmp_gender["err_up"],
      arrayminus=cmp_gender["err_down"],
      thickness=1.5,
      width=3
  ),
  mode="markers+text",
  name="BLS Baseline",
  text=cmp_gender["percent_baseline"].map(lambda x: f"{x:.1f}%"),
  textfont=dict(color="blue"), 
  textposition="middle right",
  marker=dict(symbol="circle", size=10)
))

# 4b) GenAI points + value labels
fig.add_trace(go.Scatter(
  x=cmp_gender["gender"],
  y=cmp_gender["percent_genai"],
  mode="markers+text",
  name="GenAI",
  text=cmp_gender["percent_genai"].map(lambda x: f"{x:.1f}%"),
  textposition="middle left",
  textfont=dict(color="red"), 
  marker=dict(symbol="square", size=10)
))
fig.update_yaxes(tickformat=",.1f%", ticksuffix="%")
fig.update_layout(
  title=f"GPT 4.0 vs BLS Baselines - Gender Distributions <br> Career Term: {this_career_term}",
  xaxis_title="Gender",
  yaxis_title="Percent",
  legend_title="Dataset",
  width=1000, height=800
)

fig.write_image(f"diffchart-openai/{this_career_term}-gender.png")
print(f"Saved gender diff chart for: {this_career_term}")
'''
=============================================================
'''

# Split full names into first/last
split_names = genai_data["name"].str.split(expand=True)
first_names = split_names[0]
last_names = split_names[1]
first_counts = first_names.value_counts().head(5).reset_index()
first_counts.columns = ["First Name", "Count"]
total_first = len(first_names)
first_counts["Percent of Dataset"] =(first_counts["Count"] / 10000).round(1)

last_counts = last_names.value_counts().head(5).reset_index()
last_counts.columns = ["Last Name", "Count"]
total_last = len(last_names)
last_counts["Percent of Dataset"] =(last_counts["Count"] / 10000).round(1)
fig_first = go.Figure(data=[
  go.Table(
      header=dict(values=list(first_counts.columns), fill_color='lightgrey'),
      cells=dict(values=[first_counts["First Name"], first_counts["Count"], first_counts["Percent of Dataset"]])
  )
])
fig_first.update_layout(
  title_text=f"5 Most Frequent First Names: GPT 4.0 <br> Career Term: {this_career_term}",
  title_x=0.5,                  # centers the title
  margin=dict(t=80, b=100)       # add a bit of top margin so title isn’t too close
)
fig_first.write_image(f"first-name-tables/{this_career_term}.png", width=800, height=800)

# 5. Generate a Plotly table for top 5 last name counts
fig_last = go.Figure(data=[
    go.Table(
      header=dict(values=list(last_counts.columns), fill_color='lightgrey'),
      cells=dict(values=[last_counts["Last Name"], last_counts["Count"], first_counts["Percent of Dataset"]])
  )
])
fig_last.update_layout(
  title_text=f"5 Most Frequent Last Names: GPT 4.0 <br> Career Term: {this_career_term}",
  title_x=0.5,                  # centers the title
  margin=dict(t=80, b=40)       # add a bit of top margin so title isn’t too close
)
fig_last.write_image(f"last-name-tables/{this_career_term}.png", width=800, height=800)


print(f"Saved top 5 first-name counts table for: {this_career_term}")
print(f"Saved top 5 last-name counts table for: {this_career_term}")

# Word clouds
# 2. Flatten into a single list of first and last names
words = split_names.stack().tolist()

# 3. Count frequencies of each name part
freq = Counter(words)

# 4. Generate a word cloud image from frequencies
wc = WordCloud(width=800, height=800, background_color="white")
wc_image = wc.generate_from_frequencies(freq).to_array()

# 5. Display the word cloud using Plotly Graph Objects
fig = go.Figure(go.Image(z=wc_image))
fig.update_layout(
    title=f"Generative AI Name Cloud: {this_career_term}",
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    margin=dict(l=0, r=0, t=40, b=0)
)
fig.write_image(f"wordcloud-openai/{this_career_term}.png")
print(f"Saved word cloud for: {this_career_term}")