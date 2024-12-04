import anthropic
import re
import csv

client = anthropic.Anthropic(api_key=["API KEY"])

message = """Generate a unique doctor profile in the United States for UX research purposes. Try to not have the same names and each persona should be independent of each other.
Ensure that each profile has complete details and a well-described short biography.
Keep the formatting of each response consistent please.
Include the following characteristics:
Name: 
Age: 
Gender: 
Ethnicity/Race: 
Income: 
Primary motivations: [a short one-paragraph biography describing the doctor's reasons for becoming a doctor]
Short Biography: [a detailed one-paragraph biography describing the doctor's background, experience, and personality]
"""

# CSV headers
csv_headers = ["Name", "Age", "Gender", "Ethnicity/Race", "Income", "Primary motivations", "Short Biography"]

# regex patterns to extract only  required fields
patterns = {
    "Name": r"^Name:\s*(.+)$",  
    "Age": r"^Age:\s*(\d+)$",  
    "Gender": r"^Gender:\s*(.+)$",  
    "Ethnicity/Race": r"^Ethnicity/Race:\s*(.+)$",  
    "Income": r"^Income:\s*(.+)$",  
    "Primary motivations": r"^Primary motivations:\s*(.+?)(?=\n[A-Z]|$)",  
    "Short Biography": r"^Short Biography:\s*(.+)$"  
}

output_file = "doctor_profiles_anthropic.csv"

with open(output_file, mode="a", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
    writer.writeheader()  

    for i in range(9189):  
        try:
            print(f"Generating profile {i}...")
            reply = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": message}]
            )

            
            if hasattr(reply, 'content') and isinstance(reply.content, list):
                text = ""
                for block in reply.content:
                    if hasattr(block, 'text'):
                        text = block.text.strip()
                        break
                if not text:
                    raise ValueError("No valid text content found in reply.")
            else:
                raise ValueError("Reply content is not a valid list.")

            data = {header: "" for header in csv_headers}  
            for header, pattern in patterns.items():
                match = re.search(pattern, text, re.MULTILINE)  
                if match:
                    data[header] = match.group(1).strip()

            writer.writerow(data)

        except Exception as e:
            print(f"Error during API call for profile {i}: {e}")
            writer.writerow({key: "Error" for key in csv_headers})
