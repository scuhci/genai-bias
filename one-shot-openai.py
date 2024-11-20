import openai
import csv
import time

#openaikey included

# Define the prompt message
message = """Generate a unique doctor profile in the United States for UX research purposes. 
Ensure that each profile has complete details and a well-described short biography.
Include the following characteristics:
Name: 
Age: 
Gender: 
Ethnicity/Race: 
Income: 
Primary motivations: 
Short Biography: [a detailed one-paragraph biography describing the doctor's background, experience, and personality]
"""

# Define the headers for the CSV file
csv_headers = ["Name", "Age", "Gender", "Ethnicity/Race", "Income", "Primary motivations", "Short Biography"]

with open("o.csv", mode="a", newline="") as file:
    writer = csv.writer(file)
    
    for i in range(5):  
        try:
            chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}],
            )
            reply = chat.choices[0].message.content
            
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