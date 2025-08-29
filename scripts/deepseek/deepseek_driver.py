from openai import OpenAI
import csv
import time
import json
import utils

# Code to synchronously generate 1,000 profiles via DeepSeek for 40 career terms.
career_list = [
    "chiefexecutiveofficer",
    "computerprogrammer",
    "softwaredeveloper",
    "engineer",
    "drafter",
    "biologist",
    "chemist",
    "primaryschoolteacher",
    "specialedteacher",
    "librarian"
    # "author",
    # "pharmacist",
    # "doctor",
    # "nurse",
    # "nursepractitioner",
    # "labtech",
    # "policeofficer",
    # "securityguard",
    # "chef",
    # "cook",
    # "bartender",
    # "custodian",
    # "childcareworker",
    # "insurancesalesagent",
    # "customerservicerepresentative",
    # "receptionist",
    # "mailcarrier",
    # "administrativeassistant",
    # "constructionworker",
    # "electrician",
    # "plumber",
    # "roofer",
    # "buildinginspector",
    # "butcher",
    # "welder",
    # "housekeeper",
    # "pilot",
    # "busdriver",
    # "truckdriver",
    # "craneoperator",
    # "garbagecollector"
]

csv_headers = ["name", "age", "gender", "ethnicity", "salary", "motivations", "biography"]

for career_term in career_list:
    with open(f"../../profiles/deepseek/{career_term}_deepseek.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        for i in range(1000):  
            try:
                response = utils.get_response(f"Generate a profile for: {career_term}").choices[0].message.content
                result = json.loads(response.strip())
                print(f"Generated and loaded profile #{i} for career {career_term}")
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