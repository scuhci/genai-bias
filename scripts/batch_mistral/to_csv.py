import json
import csv
import os
import re

# Input JSONL file from Mistral
jsonl_file = "80afda06-04f9-4dbe-a9ba-8ede992d2281.jsonl"
input_path = f"../../profiles/mistral/jsonls/{jsonl_file}"
results = []

with open(input_path, 'r') as file:
    for line in file:
        json_object = json.loads(line.strip())
        results.append(json_object)

csv_headers = ["name", "age", "gender", "ethnicity", "salary", "motivations", "biography"]

# Ensure output directory exists
os.makedirs("../../profiles/mistral/csvs", exist_ok=True)

prev_career_term = ''.join([c for c in results[0]['custom_id'] if c.isalpha()])
print(f"Parsing results for: {prev_career_term}\n")
headers_written = False

for res in results:
    current_career_term = ''.join([c for c in res['custom_id'] if c.isalpha()])
    if current_career_term != prev_career_term:
        print(f"Parsing results for: {current_career_term}")
        prev_career_term = current_career_term
        headers_written = False

    csv_path = f"../../profiles/mistral/csvs/{current_career_term}_mistral.csv"
    with open(csv_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not headers_written:
            writer.writerow(csv_headers)
            headers_written = True

        try:
            content = res["response"]["body"]["choices"][0]["message"]["content"]

            # Remove ```json ... ``` wrapper if present
            cleaned = re.sub(r"^```json\s*|\s*```$", "", content.strip(), flags=re.DOTALL)

            result = json.loads(cleaned)

            name = result.get("name", "")
            age = result.get("age", "")
            gender = result.get("gender", "")
            ethnicity = ",".join(result["ethnicity"]) if isinstance(result.get("ethnicity"), list) else result.get("ethnicity", "")
            salary = result.get("salary", "")
            motivations = result.get("motivations", "")
            biography = result.get("biography", "")

            writer.writerow([name, age, gender, ethnicity, salary, motivations, biography])

        except Exception as e:
            print(f"Error processing result {res.get('custom_id', 'unknown')}: {e}")