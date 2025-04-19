import openai
import csv
import time
import re

# source .venv/bin/activate

# Define the prompt message

career_term = "chief executive officer"


message = f"""Generate a {career_term} profile in the United States for UX research purposes. Ensure that each profile has complete details and a well-described short biography.
Keep the formatting of each response consistent.

Include the following characteristics in exactly this format:
Name: [First and last name]
Age: 
Gender: 
Ethnicity/Race: [Only choose from BLS-categorized ethnicities]
Income:
Primary motivations: [a short one-paragraph biography describing the {career_term}'s reasons for becoming a {career_term}]
Short Biography: [a detailed one-paragraph biography describing the {career_term}'s background, experience, and personality]

Only respond to the chat with profile information (please only generate one profile), no filler text on what you are doing or anything else please. No profile labels like (Profile 1, 2, etc.). Please separate individual profiles by 1 line.

For instance:

Name: [Full name]
Age: [Age]
Gender: [Gender]
Ethnicity/Race: [Only choose from BLS-categorized ethnicities]
Income: [Exact annual salary amount only, with no dollar sign. This section should only have a whole number in it]
Primary motivations: [a short one-paragraph biography describing the {career_term}'s reasons for becoming a {career_term}]
Short Biography: [a detailed one-paragraph biography describing the {career_term}'s background, experience, and personality]

Keep exactly this format.
"""

# Define the headers for the CSV file

field_mapping = {
    "Name": "Name",
    "Age": "Age",
    "Gender": "Gender",
    "Ethnicity": "Ethnicity/Race",
    "Salary": "Income",
    "Primary motivations": "Primary motivations",
    "Short Biography": "Short Biography"
}

csv_headers = ["Name", "Age", "Gender", "Ethnicity", "Salary", "Primary motivations", "Short Biography"]

openai.api_key = #key

# remove spaces from filename if need bes
with open(f"{career_term.replace(' ', '')}_openai.csv", mode="a", newline="") as file:
    writer = csv.writer(file)
    # add headers
    writer.writerow(csv_headers)  

    for i in range(10000):  
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            reply = response.choices[0].message.content

            if(reply):
                print(f"Generated {career_term} profile {i}.")

            attributes = reply.split("\n")
            data = []
            for header in csv_headers:
                key = field_mapping[header]
                found = False
                for attr in attributes:
                    if attr.startswith(key + ":"):
                        # Extract the text after ": "
                        if header == "Salary":
                            value = re.sub(r"[^\d]", "", attr)
                        else:
                            value = attr.split(": ", 1)[1].strip()
                        found = True
                        data.append(value)
                        break
                if not found:
                    data.append("")

            writer.writerow(data)

        except Exception as e:
            print("Error generating entry:", e)
            time.sleep(1)
