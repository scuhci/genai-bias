import os
import re
import csv
import chardet
import pandas as pd
from pathlib import Path

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

# Paths
directory_path = "../../profiles/mistral"
bls_path = "../../profiles/bls-baselines.csv"

# Load BLS baseline data
bls_df = pd.read_csv(bls_path)
bls_df['genai_bias_search_term'] = bls_df['genai_bias_search_term'].astype(str).str.strip()

with open('output.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        'career',
        'genai_n', 'genai_women', 'genai_white', 'genai_black', 'genai_hispanic', 'genai_asian',
        'genai_p_women', 'genai_p_white', 'genai_p_black', 'genai_p_hispanic', 'genai_p_asian',
        'n_employed', 'bls_p_women', 'bls_p_white', 'bls_p_black', 'bls_p_asian', 'bls_p_hispanic'
    ])
    
    for filename in os.listdir(directory_path):
        if not filename.endswith('.csv'):
            continue

        file_path = os.path.join(directory_path, filename)
        try:
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                detected_encoding = detect_encoding(file_path)
                df = pd.read_csv(file_path, encoding=detected_encoding)
            
            genai_n = len(df)
            if genai_n == 0:
                continue  # skip empty files
            
            # Gender
            genai_women = (df['gender'] == 'Female').sum()
            genai_p_women = round(genai_women / genai_n, 4)

            # Ethnicity (multi-label split)
            ethnicity_series = df['ethnicity'].str.split(', ').explode()
            counts = ethnicity_series.value_counts()
            genai_white    = counts.get('White', 0)
            genai_black    = counts.get('Black', 0)
            genai_hispanic = counts.get('Hispanic', 0)
            genai_asian    = counts.get('Asian', 0)

            genai_p_white    = round(genai_white    / genai_n, 4)
            genai_p_black    = round(genai_black    / genai_n, 4)
            genai_p_hispanic = round(genai_hispanic / genai_n, 4)
            genai_p_asian    = round(genai_asian    / genai_n, 4)

            # ---- Strip "_deepseek.csv" to get search term ----
            career_key_raw = filename.replace("profile_mistral.csv", "")

            # Lookup BLS values
            bls_row = bls_df[bls_df['genai_bias_search_term'] == career_key_raw]
            if not bls_row.empty:
                # Convert percents in BLS data into decimals
                bls_vals = bls_row.iloc[0][[
                    'n_employed','p_women','p_white','p_black','p_asian','p_hispanic'
                ]].tolist()
                n_employed = bls_vals[0]
                bls_decimals = [round(val / 100, 4) if pd.notnull(val) else None for val in bls_vals[1:]]
                bls_vals = [n_employed] + bls_decimals
            else:
                bls_vals = [None, None, None, None, None, None]

            writer.writerow([
                career_key_raw,
                genai_n, genai_women, genai_white, genai_black, genai_hispanic, genai_asian,
                genai_p_women, genai_p_white, genai_p_black, genai_p_hispanic, genai_p_asian,
                *bls_vals
            ])

        except Exception as e:
            print(f"Other error with {filename}: {e}")
