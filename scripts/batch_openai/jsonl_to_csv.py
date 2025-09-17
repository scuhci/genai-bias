import json
import pandas as pd
import csv

results = []
jsonl_file = "" # batch fname
with open(f"../../profiles/openai/jsonls/{jsonl_file}", 'r') as file:
    for line in file:
        # Parsing the JSON string into a dict and appending to the list of results
        json_object = json.loads(line.strip())
        results.append(json_object)

csv_headers = ["name", "age", "gender", "ethnicity", "salary", "motivations", "biography"]

prev_career_term = ''.join([i for i in results[0]['custom_id'][:-1] if i.isalpha()])
print(f"Parsing results for: {prev_career_term}\n")
headers_written = False

for res in results:
    current_career_term = ''.join([i for i in res['custom_id'][:-1] if i.isalpha()]) #remove numeric tags off custom ids
    if current_career_term == prev_career_term:
        with open(f"../../profiles/openai/csvs/{current_career_term}_openai.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            if not headers_written:
                writer.writerow(csv_headers)  
                headers_written = True
            
            task_id = res['custom_id']
            try: 
                result = json.loads(res['response']['body']['choices'][0]['message']['content'])
                try:
                    
                    name = result['name']
                    age = result['age']
                    gender = result['gender']
                    ethnicity = "".join(result['ethnicity'])
                    salary = result['salary']
                    motivations = result['motivations']
                    biography = result['biography']
                    this_profile = [name, age, gender, ethnicity, salary, motivations, biography]

                    writer.writerow(this_profile)
                except:
                    print("Error processing this profile: ")
                    print(result)
            except Exception as e: 
                print("Error loading:")
                print(e)
    else:
        print(f"Parsing results for: {current_career_term}\n")
        prev_career_term = current_career_term
        headers_written = False
        with open(f"../../profiles/openai/csvs/{current_career_term}_openai.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            if not headers_written:
                writer.writerow(csv_headers)  
                headers_written = True
            
            task_id = res['custom_id']

            result = json.loads(res['response']['body']['choices'][0]['message']['content'])

            try:
                name = result['name']
                age = result['age']
                gender = result['gender']
                ethnicity = result['ethnicity']
                salary = result['salary']
                motivations = result['motivations']
                biography = result['biography']
                this_profile = [name, age, gender, ethnicity, salary, motivations, biography]

                writer.writerow(this_profile)
            except:
                print("Error processing this profile: ")
                print(result)
