import pandas as pd
import argparse

def calculate_average_differences(input_csv, output_csv):
    # Load the input CSV
    df = pd.read_csv(input_csv)

    # Columns to average
    diff_columns = [
        "diff_p_women",
        "diff_p_white",
        "diff_p_black",
        "diff_p_asian",
        "diff_p_hispanic",
    ]

    # Compute averages
    avg_diffs = df[diff_columns].mean().reset_index()
    avg_diffs.columns = ["category", "average_percent_difference"]

    # Save to CSV
    avg_diffs.to_csv(output_csv, index=False)
    print(f"Averages saved to {output_csv}")


calculate_average_differences("results_vs_BLS/deepseek_differences_vs_bls.csv", "deepseek_averages.csv")
calculate_average_differences("results_vs_BLS/gemini_differences_vs_bls.csv", "gemini_averages.csv")
calculate_average_differences("results_vs_BLS/mistral_differences_vs_bls.csv", "mistral_averages.csv")
calculate_average_differences("results_vs_BLS/openai_differences_vs_bls.csv", "openai_averages.csv")
