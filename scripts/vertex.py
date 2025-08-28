from google.cloud import aiplatform

PROJECT_ID = "gen-lang-client-0162963299"
REGION = "us-central1"
MODEL_ID = "gemini-2.5-pro"
GCS_INPUT_URI = "gs://my-gemini-input-bucket-arnav-123/demographic_requests.jsonl"
GCS_OUTPUT_URI = "gs://my-gemini-output-bucket-arnav-123/"
JOB_DISPLAY_NAME = "gemini-demographic-batch"

aiplatform.init(project=PROJECT_ID, location=REGION)

batch_job = aiplatform.BatchPredictionJob.create(
    job_display_name=JOB_DISPLAY_NAME,
    model_name=MODEL_ID,
    gcs_source=GCS_INPUT_URI,
    gcs_destination_prefix=GCS_OUTPUT_URI,
    instances_format="jsonl",
    predictions_format="jsonl"
)

print(f"Batch job submitted: {batch_job.resource_name}")
print(f"State: {batch_job.state.name}")
