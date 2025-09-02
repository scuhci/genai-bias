import os
import pandas as pd
import chardet
from pathlib import Path
import csv


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

directory_path = "../profiles/openai/csvs"
with open('output.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['career', 'search_n', 'search_women', 'search_white', 'search_black', 'search_hispanic', 'search_asian', 'search_p_women', 'search_p_white', 'search_p_black', 'search_p_hispanic', 'search_p_asian'])
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if filename.endswith('.csv'):
            try:
                try:
                    df = pd.read_csv(file_path)
                except UnicodeDecodeError:
                    detected_encoding = detect_encoding(file_path)
                    df = pd.read_csv(file_path, encoding=detected_encoding)
                
                search_women = len(df[df['gender'] == 'Female'])
                search_n = len(df)
                search_p_women = round(round(search_women/search_n, 4) * 100, 2)
            
                ethnicity_series = df['ethnicity'].str.split(', ').explode()
                counts = ethnicity_series.value_counts()
                search_white = search_black = search_asian = search_hispanic = 0
                search_p_white = search_p_black = search_p_asian = search_p_hispanic = 0
                for ethnicity, count in counts.items():
                    if ethnicity == 'White':
                        search_white = count
                        search_p_white = round(round(search_white/search_n, 4) * 100, 2)
                    if ethnicity == 'Black':
                        search_black = count
                        search_p_black = round(round(search_black/search_n, 4) * 100, 2)
                    if ethnicity == 'Hispanic':
                        search_hispanic = count
                        search_p_hispanic = round(round(search_hispanic/search_n, 4) * 100, 2)
                    if ethnicity == 'Asian':
                        search_asian = count
                        search_p_asian = round(round(search_asian/search_n, 4) * 100, 2)
                        
                writer.writerow([filename, search_n, search_women, search_white, search_black, search_hispanic, search_asian, search_p_women, search_p_white, search_p_black, search_p_hispanic, search_p_asian]) 
            except Exception as e:
                print(f"Other error with {filename}: {e}")

