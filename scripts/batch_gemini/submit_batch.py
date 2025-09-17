# make_and_submit.py — build the JSONL inside batch_utils, upload, submit job, save ID
import os
import json
from pathlib import Path
import batch_utils as bu

# ---- Choose ONE of the following input styles ----
# A) Uniform count per occupation:
occupations = [
    # list of occupations
]
per_occupation = 10000

# B) Or: specific missing counts per occupation:
# missing_counts = {"police officer": 213, "roofer": 87}

LOCAL_JSONL = "requests/demographic_requests5.jsonl"

#change everything below this point to fit the project
GCS_INPUT_URI = os.getenv("INPUT_GCS_URI", "gs://my-gemini-input-bucket-1/demographic_requests.jsonl") 
GCS_OUTPUT_DIR = os.getenv("OUTPUT_GCS_DIR", "gs://my-gemini-output-bucket-1/gemini_demographic_results/")
PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0808814869")
REGION = os.getenv("REGION", "us-central1")
MODEL_ID = os.getenv("MODEL_ID", "gemini-2.5-pro")
JOB_IDS_DIR = "job_ids"

def main():
    Path("requests").mkdir(exist_ok=True)
    Path(JOB_IDS_DIR).mkdir(exist_ok=True)

    # Build JSONL
    bu.build_jsonl_from_list(occupations, LOCAL_JSONL, per_occupation=per_occupation)
    # OR:
    # bu.build_jsonl_from_dict(missing_counts, LOCAL_JSONL)

    # Upload to GCS
    bu.upload_to_gcs(LOCAL_JSONL, GCS_INPUT_URI)

    # Submit batch
    job = bu.submit_batch(
        gcs_input_uri=GCS_INPUT_URI,
        gcs_output_prefix=GCS_OUTPUT_DIR,
        project_id=PROJECT_ID,
        region=REGION,
        model_id=MODEL_ID,
        display_name="gemini-demographic-batch"
    )
    print(job.resource_name)

    # Save job id for convenience
    job_id_path = os.path.join(JOB_IDS_DIR, "latest_job_id.txt")
    with open(job_id_path, "w") as f:
        f.write(job.resource_name)
    print(f"Saved Job ID → {job_id_path}")

if __name__ == "__main__":
    main()
