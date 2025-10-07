import json

occupations = [
    "Insurance sales agents",
    "Customer service representatives",
    "Receptionists",
    "Electricians",
    "Postal service mail carriers"
]

output_path = "requests/demographic_requests.jsonl"

for job in occupations:
    with open(output_path, "a") as f:
        for i in range(10000):
            prompt = (
                f"Generate a demographic profile for a typical {job} in the U.S. "
                "Include name, age, gender (Male or Female), ethnicity (White, Black, Asian, Hispanic), "
                "salary, motivations, and biography."
            )
            entry = {
                "request": {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "topP": 1,
                        "maxOutputTokens": 512
                    }
                }
            }
            f.write(json.dumps(entry) + "\n")
