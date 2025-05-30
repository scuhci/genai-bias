import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

dir_path = "../profiles/openai/csvs/"
baseline_dir_path = "../profiles/openai/bls-baselines.csv"

baselines_data = pd.read_csv(baseline_dir_path)

for career_profiles in os.listdir(dir_path):

  datapath = os.path.join(dir_path, career_profiles)
  print(datapath)
  genai_data = pd.read_csv(datapath, encoding="cp1252")

  # genai_data = pd.read_csv("../profiles/openai/csvs/biologistprofiles_openai.csv")

  # get baseline data
  this_career_term = career_profiles.split("profiles_openai.csv")[0]
  print(this_career_term)
  # this_career_term = "biologist"
  this_career_baseline_df = baselines_data[baselines_data["genai_bias_search_term"] == this_career_term]
  print(this_career_baseline_df)

  eth_cols = ["p_white","p_black","p_asian","p_hispanic"]

  # tidy her into a nice little array
  this_career_baseline_df = (
      this_career_baseline_df[eth_cols]                                 # pick only the pct columns
        .rename(columns=lambda c: c.replace("p_",""))  # optional: drop the "p_" prefix
        .melt(var_name="ethnicity", value_name="percent")
  )
      
  # get the gender and race percentages into arrays
  genai_race_df = (
      genai_data["ethnicity"]
        .str.lower()
        .value_counts(normalize=True)   # proportions
        .mul(100)                       # → percentages
        .reset_index(name="percent")    # make it a DF with column “percent”
        .rename(columns={"index":"ethnicity"})
  )

  # 2) gender percentages DF
  genai_gender_df = (
      genai_data["gender"]
        .str.lower()   
        .value_counts(normalize=True)
        .mul(100)
        .reset_index(name="percent")
        .rename(columns={"index":"gender"})
  )

  diff_df = (
      genai_race_df
        .merge(this_career_baseline_df,
              on="ethnicity",
              how="outer",
              suffixes=("_genai", "_baseline"))
        .fillna({"percent_genai": 0, "percent_baseline": 0})
        .assign(difference=lambda df: 
                  df["percent_genai"] - df["percent_baseline"])
        [["ethnicity", "difference"]]
  )

  # print(diff_df)
      
  # # 1) define your main categories
  # main_eth = ["white", "black", "hispanic", "asian"]

  # # 2) filter diff_df
  # plot_df = diff_df[diff_df["ethnicity"].isin(main_eth)]

  # # 3) (optional) enforce a specific order
  # plot_df["ethnicity"] = pd.Categorical(
  #     plot_df["ethnicity"],
  #     categories=main_eth,
  #     ordered=True
  # )

  # # 4) build the over–under bar chart
  # fig = px.bar(
  #     plot_df,
  #     x="ethnicity",
  #     y="difference",
  #     color="difference",
  #     color_continuous_scale=["#d62728","#1fb451"],
  #     category_orders={"ethnicity": main_eth},
  #     labels={"difference":"% Deviation from BLS Baseline"},
  #     title=f"GenAI vs BLS Baselines - Racial And Gender Distributions <br> Career Term: {this_career_term}"
  # )

  # fig.update_layout(coloraxis_showscale=False)
  # # format axis and add zero line
  # fig.update_yaxes(tickformat=",.1f%", ticksuffix="%")
  # fig.update_layout(shapes=[dict(
  #     type="line", x0=-0.5, x1=len(plot_df)-0.5,
  #     y0=0, y1=0, line=dict(color="black", dash="dash")
  # )])

  # fig.write_image(f"overunder-openai/{this_career_term}.png")

  # import plotly.express as px

  # cmp = (
  #     genai_race_df
  #       .merge(this_career_baseline_df,
  #             on="ethnicity",
  #             how="outer",
  #             suffixes=("_genai","_baseline"))
  #       .fillna(0)    # missing → 0%
  # )
  # print(cmp)

  # cmp = cmp[cmp["ethnicity"].isin(main_eth)]

  # cmp["ethnicity"] = pd.Categorical(
  #     cmp["ethnicity"],
  #     categories=main_eth,
  #     ordered=True
  # )

  # # 2) compute error‐bar extents
  # cmp["err_up"]   = (cmp["percent_genai"]    - cmp["percent_baseline"]).clip(lower=0)
  # cmp["err_down"] = (cmp["percent_baseline"] - cmp["percent_genai"]   ).clip(lower=0)

  # fig = go.Figure()

  # # 1) BLS (baseline) points + asymmetric error bars + labels
  # fig.add_trace(go.Scatter(
  #     x=cmp["ethnicity"],
  #     y=cmp["percent_baseline"],
  #     error_y=dict(
  #         type="data",
  #         array=cmp["err_up"],
  #         arrayminus=cmp["err_down"],
  #         thickness=1.5,
  #         width=3
  #     ),
  #     mode="markers+text",
  #     name="BLS",
  #     text=cmp["percent_baseline"].map(lambda x: f"{x:.1f}%"),
  #     textposition="top center",
  #     marker=dict(symbol="circle", size=10)
  # ))

  # # 2) GenAI points + labels
  # fig.add_trace(go.Scatter(
  #     x=cmp["ethnicity"],
  #     y=cmp["percent_genai"],
  #     mode="markers+text",
  #     name="GenAI",
  #     text=cmp["percent_genai"].map(lambda x: f"{x:.1f}%"),
  #     textposition="bottom center",
  #     marker=dict(symbol="square", size=10)
  # ))

  # # 3) Layout tweaks
  # fig.update_yaxes(tickformat=",.1f%", ticksuffix="%")
  # fig.update_layout(
  #     title=f"GenAI vs BLS Baselines -  Racial And Gender Distributions <br> Career Term: {this_career_term}",
  #     xaxis_title="Ethnicity",
  #     yaxis_title="Percent",
  #     legend_title="Dataset",
  #     width=800, height=800
  # )

  # fig.write_image(f"diffchart-openai/{this_career_term}.png")
