import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
import plotly.graph_objects as go
import pandas as pd
import os
import re

dir_path = "../profiles/openai/csvs/"
baseline_dir_path = "../profiles/openai/bls-baselines.csv"

baselines_data = pd.read_csv(baseline_dir_path)

for career_profiles in os.listdir(dir_path):

  datapath = os.path.join(dir_path, career_profiles)
  print(datapath)
  gpt4_data = pd.read_csv(datapath, encoding="cp1252")

  # gpt4_data = pd.read_csv("../profiles/openai/csvs/biologistprofiles_openai.csv")

  # get baseline data
  this_career_term = career_profiles.split("profiles_openai.csv")[0]
  print("Generating visualizations for... " + this_career_term)
  # this_career_term = "biologist"
  this_career_baseline_df = baselines_data[baselines_data["genai_bias_search_term"] == this_career_term]

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
      gpt4_data["ethnicity"]
        .str.lower()
        .str.split(",", expand=False)          # e.g. ["hispanic", " white"]
        .apply(lambda lst: [x.strip() for x in lst])  
        .explode()                              # now one ethnicity per row
    )
    
  gpt4_race_df = (
        merge_races
          .str.lower()
          .value_counts(normalize=True)   # proportions
          .mul(100)                       # → percentages
          .reset_index(name="percent")    # make it a DF with column “percent”
          .rename(columns={"index":"ethnicity"})
    )

  print("gpt4 Ethnicity Data") 
  print(gpt4_race_df)

  race_diff_df = (
      gpt4_race_df
        .merge(this_career_baseline_race_df,
              on="ethnicity",
              how="outer",
              suffixes=("_gpt4", "_baseline"))
        .fillna({"percent_gpt4": 0, "percent_baseline": 0})
        .assign(difference=lambda df: 
                  df["percent_gpt4"] - df["percent_baseline"])
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

  gpt4_gender_df = (
      gpt4_data["gender"]
        .str.lower()   
        .value_counts(normalize=True)
        .mul(100)
        .reset_index(name="percent")
        .rename(columns={"index":"gender"})
  )

  print("gpt4 Gender Data") 
  print(gpt4_gender_df)
  gender_diff_df = (
      gpt4_gender_df
        .merge(this_career_baseline_gender_df,
              on="gender",
              how="outer",
              suffixes=("_gpt4", "_baseline"))
        .fillna({"percent_gpt4": 0})
        .assign(difference=lambda df: 
                  df["percent_gpt4"] - df["percent_baseline"])
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
      color_continuous_scale=["#d62728","#1f77b4"],
      category_orders={"ethnicity": main_eth},
      labels={"difference":"% Deviation from BLS Baseline"},
      title=f"GPT 4.0 vs BLS Baselines - Ethnicity Distributions <br> Career Term: {this_career_term}"
  )

  fig.update_traces(
    marker_line_width=0.5,
    marker_line_color="black",
    texttemplate="%{y:.1f}%",         # ← one decimal plus a single “%”
    textposition="outside"               # place labels above each bar
  )
  
  fig.update_layout(coloraxis_showscale=False)
  # format axis and add zero line
  fig.update_yaxes(range=[-111, 111], tickformat=",.1f%", ticksuffix="%")
  fig.update_layout(shapes=[dict(
      type="line", x0=-0.5, x1=len(plot_df)-0.5,
      y0=0, y1=0, line=dict(color="black", dash="dash")
  )])

  print(f"Saved ethnicity over-under bar chart for: {this_career_term}")
  fig.write_image(f"overunder-openai/{this_career_term}-eth.pdf", scale=2)

  '''
  2. Double Bar Charts
  These are fancy error plots.
  '''
  eth_merge = (
    this_career_baseline_race_df
      .merge(
          gpt4_race_df,
          on="ethnicity",
          how="outer"
      )
      .fillna(0)
      .rename(columns={
          "percent_x": "percent_baseline",
          "percent_y": "percent_gpt4"
      })
    )
  print(eth_merge)
  fig_eth = px.bar(
      eth_merge,
      x="ethnicity",
      y=["percent_baseline","percent_gpt4"],
      labels={
          "value": "% of Sample",
          "variable": "Source"
      },
      title=f"GPT 4.0 vs. BLS Baselines: Ethnicity <br> Career Term: {this_career_term}",
      barmode="group",           # side–by–side bars
      category_orders={"ethnicity": ["white","black","asian","hispanic"]}
  )

  fig_eth.update_traces(
      marker_line_width=0.5,
      marker_line_color="black",
      texttemplate="%{y:.1f}%",        # one decimal + “%”
      textposition="outside"          # places each label above its bar
  )

  fig_eth.update_yaxes(range=[0, 111], tickformat=",.1f%", ticksuffix="%")
  fig_eth.update_layout(
      font=dict(
          family="Arial, sans-serif",
          size=24        # base font size for labels, legend, hover, etc.
      ),
      title_font_size=28,          # title only
      legend_title_font_size=24,
      legend_font_size=24,
      width=1000,                   # bump up width/height for better export
      height=600
  )

  # 2) Tweak axes title & tick labels
  fig_eth.update_xaxes(
      title_font=dict(size=24),    # x-axis title
      tickfont=dict(size=24)       # x-axis tick labels
  )
  fig_eth.update_yaxes(
      title_font=dict(size=24),    # y-axis title
      tickfont=dict(size=24),      # y-axis tick labels
      range=[0, 111],
      tickformat=",.1f%",
      ticksuffix="%"
  )
  fig_eth.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5,
        font=dict(size=24),           # legend item labels
        title_font=dict(size=24)      # legend title
    ),
    margin=dict(
        l=40, r=40, t=80,
        b=120    # ensure enough space under the plot
    )
    )
  # 3) Export with a higher “scale” factor to improve pdf quality
  #    (requires kaleido; scale=2 doubles the pixel density)
  output_path = f"dbarchart-openai/{this_career_term}-eth.pdf"
  fig_eth.write_image(output_path, scale=2)

  print(f"Saved ethnicity double bar chart for: {this_career_term}")
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
      color_continuous_scale=["#d62728","#1f77b4"],
      category_orders={"gender": gender},
      labels={"difference":"% Deviation from BLS Baseline"},
      title=f"GPT 4.0 vs BLS Baselines - Gender Distributions <br> Career Term: {this_career_term}"
  )

  fig.update_layout(coloraxis_showscale=False)
  # format axis and add zero line
  fig.update_yaxes(range=[-111, 111], tickformat=",.1f%", ticksuffix="%")
  fig.update_layout(shapes=[dict(
      type="line", x0=-0.5, x1=len(plot_df)-0.5,
      y0=0, y1=0, line=dict(color="black", dash="dash")
  )])
  
  fig.update_traces(
    marker_line_width=0.5,
    marker_line_color="black",
    texttemplate="%{y:.1f}%",         # ← one decimal plus a single “%”
    textposition="outside"               # place labels above each bar
  )

  print(f"Saved gender over-under bar chart for: {this_career_term}")
  fig.write_image(f"overunder-openai/{this_career_term}-gender.pdf", scale=2)

  '''
  2. Double Bar charts
  '''
  gender_merge = (
    this_career_baseline_gender_df
      .merge(
          gpt4_gender_df,
          on="gender",
          how="outer"
      )
      .fillna(0)
      .rename(columns={
          "percent_x": "percent_baseline",
          "percent_y": "percent_gpt4"
      })
  )
  print(gender_merge)

  # -- 4d) Plot grouped bar chart for gender
  fig_gen = px.bar(
      gender_merge,
      x="gender",
      y=["percent_baseline","percent_gpt4"],
      labels={
          "value": "% of Sample",
          "variable": "Source"
      },
      title=f"GPT 4.0 vs. BLS Baselines: Gender <br> Career Term: {this_career_term}",
      barmode="group",
      category_orders={"gender": ["female", "male"]},
  )
  fig_gen.update_traces(
      marker_line_width=0.5,
      marker_line_color="black",
      texttemplate="%{y:.1f}%",        # one decimal + “%”
      textposition="outside"          # places each label above its bar
  )
  fig_gen.update_layout(
      font=dict(
          family="Arial, sans-serif",
          size=24        # base font size for labels, legend, hover, etc.
      ),
      title_font_size=28,          # title only
      legend_title_font_size=24,
      legend_font_size=24,
      width=1000,                   # bump up width/height for better export
      height=600
  )

  # 2) Tweak the axis label & tick fonts
  fig_gen.update_xaxes(
      title_font=dict(size=24),
      tickfont=dict(size=24)
  )
  fig_gen.update_yaxes(
      title_font=dict(size=24),
      tickfont=dict(size=24),
      range=[0, 111],         # gives a bit of headroom above 100%
      tickformat=",.1f%",
      ticksuffix="%"
  )
  fig_gen.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5,
        font=dict(size=24),           # legend item labels
        title_font=dict(size=24)      # legend title
    ),
    margin=dict(
        l=40, r=40, t=80,
        b=120    # ensure enough space under the plot
    )
    )

  # 3) Export as a high-res pdf (scale=2 doubles pixel density)
  output_path = f"dbarchart-openai/{this_career_term}-gender.pdf"
  fig_gen.write_image(output_path, scale=2)
  print(f"Saved gender double bar chart for: {this_career_term}")
  '''
  =============================================================
  '''

  # 1. Remove common honorifics (Dr., Mr., Mrs., Ms.) at the start of the string
  clean_names = gpt4_data["name"].str.replace(
      r'^(?:dr|mr|mrs|ms)\.\s*',   # match title + dot + any spaces
      '',                          # drop it
      flags=re.IGNORECASE,
      regex=True
  )

  # Split full names into first/last
  split_names = clean_names.str.split(expand=True)
  first_names = split_names[0]
  last_names = split_names[1]
  first_counts = first_names.value_counts().head(5).reset_index()
  first_counts.columns = ["First Name", "Count"]
  total_first = len(first_names)
  first_counts["Percent of Dataset"] =(first_counts["Count"] / 10000)

  last_counts = last_names.value_counts().head(5).reset_index()
  last_counts.columns = ["Last Name", "Count"]
  total_last = len(last_names)
  last_counts["Percent of Dataset"] =(last_counts["Count"] / 10000)
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
  fig_first.write_image(f"first-name-tables/{this_career_term}.pdf", width=800, height=800)

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
  fig_last.write_image(f"last-name-tables/{this_career_term}.pdf", width=800, height=800)


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
  fig.write_image(f"wordcloud-openai/{this_career_term}.pdf", scale=2)
  print(f"Saved word cloud for: {this_career_term}")