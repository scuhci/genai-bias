from google import genai
import csv
import re

# do one shot, one api call 10,000 times

message = """Generate a bartender profile in the United States for UX research purposes. Try to not have the same names as the ones you generated earlier and each persona should be independent of each other.
Ensure that each profile has complete details and a well-described short biography.
Keep the formatting of each response consistent.

Include the following characteristics in exactly this format:
Name:
Age: 
Gender: 
Ethnicity/Race: [Only choose from BLS-categorized ethnicities]
Income:
Primary motivations: [a short one-paragraph biography describing the doctor's reasons for becoming a doctor]
Short Biography: [a detailed one-paragraph biography describing the doctor's background, experience, and personality]

Only respond to the chat with profile information (please only generate one profile), no filler text on what you are doing or anything else please. No profile labels like (Profile 1, 2, etc.). Please separate individual profiles by 1 line.

For instance:

Name: [Name]
Age: [Age]
Gender: [Gender]
Ethnicity/Race: [Only choose from BLS-categorized ethnicities]
Income: [Exact salary amount with no dollar sign]
Primary motivations: [a short one-paragraph biography describing the doctor's reasons for becoming a doctor. Don't skip a line between Primary motivations and Short Biography.]
Short Biography: [a detailed one-paragraph biography describing the doctor's background, experience, and personality]

Keep exactly this format. There should be no added new line characters between lines of the person's profile information.
"""

client = genai.Client(api_key="key")

# CSV headers
# csv_headers = ["Name", "Age", "Gender", "Ethnicity/Race", "Income", "Primary motivations", "Short Biography"]

output_text_file = "bartender_profiles.txt"

print("new iterations")

with open(output_text_file, mode="a", encoding="utf-8") as text_file:
    # writer = csv.writer(file)
    # writer.writerow(csv_headers)   
    for i in range(9272):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=message
            )
            reply = response.text
            print(reply)

            text_file.write(f"{reply}\n\n")
            
        except Exception as e:
            print(f"Error generating entry {i + 1}: {e}")