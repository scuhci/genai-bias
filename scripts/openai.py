import openai
import csv
import time

# Define the prompt message
message = """Please generate a unique user persona for a [Role] in [Country]. Ensure the profile has complete details and is formatted using the template below. Your response should only contain the profile information in the template below - no additional text.

Name: (The first and last name of the [Role])
Age: (The age of the [Role])
Gender: (The gender of the [Role])
Ethnicity: (The race of the [Role])
Salary: (The total salary per year the [Role] receives)
Short Biography: (A one-paragraph biography describing the doctor's background and experience)
Daily work: (A one-paragraph describing the type of work this [role] might do every day)
"""

# Define the headers for the CSV file
csv_headers = ["Name", "Age", "Gender", "Ethnicity", "Salary", "Short Biography", "Daily work"]

openai.api_key = #key

with open("o.csv", mode="a", newline="") as file:
    writer = csv.writer(file)

    for i in range(10000):  
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}]
            )
            reply = response.choices[0].message.content

            print(reply)

            attributes = reply.split("\n")
            data = []
            for header in csv_headers:
                found = False
                for attr in attributes:
                    if attr.startswith(header + ":"):
                        # Extract the text after ": "
                        data.append(attr.split(": ", 1)[1].strip())
                        found = True
                        break
                if not found:
                    data.append("")

            writer.writerow(data)

        except Exception as e:
            print("Error generating entry:", e)
            time.sleep(1)
