import os
import json
import requests

API_KEY = os.getenv("MISTRAL_API_KEY", "put api key here")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
UPLOAD_URL = "https://api.mistral.ai/v1/files"
BATCH_URL = "https://api.mistral.ai/v1/batch/jobs"
BATCH_STATUS_URL = "https://api.mistral.ai/v1/batch/jobs/{}"
BATCH_RESULT_URL = "https://api.mistral.ai/v1/files/{}"

# System prompt shared across all tasks
system_prompt = '''
Your goal is to generate demographic profile data. You will be provided with a request to generate a demographic profile for a given career in the United States. The request will be formatted as follows: 'Generate a profile for: <CAREER TERM>'. 
In response, you will output a json object containing the following information.
{
    name: string // First and last name
    age: integer 
    gender: string // Select one of the following : Male, Female
    ethnicity: string // Select one or more of the following: White, Black, Asian, Hispanic
    salary: integer 
    motivations: string // In one sentence, describe why this individual chose to become a <CAREER TERM>.
    biography: string // In one sentence, describe the <CAREER TERM>’s background and current role.
}
'''

def make_batch_entry(career_term, i):
    return {
        "custom_id": f"{career_term.replace(' ', '')}_profile_{i}",
        "body": {
            "model": "mistral-medium-latest",
            "temperature": 1,
            "max_tokens": 500,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a profile for: {career_term}"}
            ]
        }
    }

def create_and_submit_batch(occupations, batch_fname, num_per_job=10000):
    os.makedirs("requests", exist_ok=True)
    request_path = os.path.join("requests", batch_fname)

    # Step 1: Write request file
    with open(request_path, 'w') as file:
        for career_term in occupations:
            for i in range(num_per_job):
                file.write(json.dumps(make_batch_entry(career_term, i + 1)) + '\n')

    # Step 2: Upload file to Mistral with purpose=batch
    with open(request_path, 'rb') as f:
        files = {
            'file': (batch_fname, f, 'application/jsonl'),
            'purpose': (None, 'batch')  # REQUIRED
        }
        response = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files=files
        )
        response.raise_for_status()
        file_id = response.json()["id"]

    # Step 3: Submit batch job
    batch_body = {
        "input_files": [file_id],
        "model": "mistral-small-latest",
        "endpoint": "/v1/chat/completions",
        "metadata": {"job_type": "demographic_profiles"}
    }

    response = requests.post(
        BATCH_URL,
        headers={**HEADERS, "Content-Type": "application/json"},
        json=batch_body
    )
    response.raise_for_status()
    return response.json()

def check_batch(batch_id):
    response = requests.get(BATCH_STATUS_URL.format(batch_id), headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    print(json.dumps(data, indent=2))

def retrieve_results(batch_id):
    response = requests.get(BATCH_STATUS_URL.format(batch_id), headers=HEADERS)
    response.raise_for_status()
    batch = response.json()

    if batch["status"] in ["SUCCESS", "FAILED", "TIMEOUT_EXCEEDED"]:
        file_id = batch["output_file"]
        result_resp = requests.get(f"{BATCH_RESULT_URL.format(file_id)}/content", headers=HEADERS)
        result_resp.raise_for_status()

        os.makedirs("../../profiles/mistral/jsonls", exist_ok=True)
        output_path = f'../../profiles/mistral/jsonls/{batch_id}.jsonl'
        with open(output_path, 'wb') as f:
            f.write(result_resp.content)
        print(f"Saved to {output_path}")
    else:
        print(f"Batch not ready. Status: {batch['status']}")
