import os
import csv

# Directory containing your CSV files
directory = "../profiles/deepseek/"  # <-- change this to your folder path

# Headers to insert
headers = ["name", "age", "gender", "ethnicity", "salary", "motivations", "biography"]

for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        filepath = os.path.join(directory, filename)

        # Read the existing content
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            content = f.readlines()

        # Check if the first line already has headers
        first_line = content[0].strip().split(",")
        if first_line == headers:
            print(f"Skipping {filename} (headers already present).")
            continue

        # Prepend headers
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            f.writelines(content)

        print(f"Headers added to {filename}")
