import openai
import csv
import time

# Define the prompt message
message = """Generate a maid/housekeeper profile in the United States for UX research purposes. Ensure that each profile has complete details and a well-described short biography.
Keep the formatting of each response consistent.

Include the following characteristics in exactly this format:
Name:
Age: 
Gender: 
Ethnicity/Race: [Only choose from BLS-categorized ethnicities]
Income:
Primary motivations: [a short one-paragraph biography describing the maid/housekeeper's reasons for becoming a maid/housekeeper]
Short Biography: [a detailed one-paragraph biography describing the maid/housekeeper's background, experience, and personality]

Only respond to the chat with profile information (please only generate one profile), no filler text on what you are doing or anything else please. No profile labels like (Profile 1, 2, etc.). Please separate individual profiles by 1 line.

For instance:

Name: [Name]
Age: [Age]
Gender: [Gender]
Ethnicity/Race: [Only choose from BLS-categorized ethnicities]
Income: [Exact salary amount with no dollar sign]
Primary motivations: [a short one-paragraph biography describing the maid/housekeeper's reasons for becoming a maid/housekeeper]
Short Biography: [a detailed one-paragraph biography describing the maid/housekeeper's background, experience, and personality]

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
                key = field_mapping[header]
                found = False
                for attr in attributes:
                    if attr.startswith(key + ":"):
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
