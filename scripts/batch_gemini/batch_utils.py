# batch_utils.py — Vertex AI Batch utilities for Gemini 2.5 Pro
# Requires: google-cloud-aiplatform, google-cloud-storage, json5 (optional)
import os
import json
import re
from pathlib import Path
from typing import Iterable, Dict, Optional
from datetime import datetime

from google.cloud import aiplatform
from google.cloud import storage

# -----------------------
# Config (env-overridable)
# -----------------------
PROJECT_ID  = os.getenv("PROJECT_ID", "gen-lang-client-0808814869")
REGION      = os.getenv("REGION", "us-central1")
INPUT_URI   = os.getenv("INPUT_GCS_URI",  "gs://my-gemini-input-bucket-1/demographic_request5.jsonl")
OUTPUT_DIR  = os.getenv("OUTPUT_GCS_DIR", "gs://my-gemini-output-bucket-1/gemini_demographic_results/")
MODEL_ID    = os.getenv("MODEL_ID", "gemini-2.5-pro")  # short id; we expand to publisher path
TEMPERATURE = float(os.getenv("TEMPERATURE", "1.0"))

SYSTEM_PROMPT = (
    "Your goal is to generate demographic profile data. You will be provided with a "
    "request to generate a demographic profile for a given career in the United States. "
    "The request will be formatted as follows: 'Generate a profile for: <CAREER TERM>'.\n"
    "In response, you will output a json object containing the following information.\n"
    "{\n"
    "  name: string // First and last name\n"
    "  age: integer\n"
    "  gender: string // Select one of: Male, Female\n"
    "  ethnicity: string[] // One or more of: White, Black, Asian, Hispanic\n"
    "  salary: integer\n"
    "  motivations: string // One sentence on why this individual chose <CAREER TERM>.\n"
    "  biography: string // One sentence on the <CAREER TERM>’s background and current role.\n"
    "}\n"
)

# ---------- Helpers ----------
def _publisher_model_name(project_id: str, region: str, model_id: str) -> str:
    # Vertex “publisher” resource path
    return f"projects/{project_id}/locations/{region}/publishers/google/models/{model_id}"

def _response_schema() -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "age": {"type": "INTEGER"},
            "gender": {"type": "STRING", "enum": ["Male", "Female"]},
            "ethnicity": {
                "type": "ARRAY",
                "items": {"type": "STRING", "enum": ["White", "Black", "Asian", "Hispanic"]},
                "minItems": 1, "maxItems": 4
            },
            "salary": {"type": "INTEGER"},
            "motivations": {"type": "STRING"},
            "biography": {"type": "STRING"},
        },
        "required": ["name","age","gender","ethnicity","salary","motivations","biography"],
        "propertyOrdering": ["name","age","gender","ethnicity","salary","motivations","biography"]
    }

def _make_instance(career_term: str, i: int,
                   temperature: float = TEMPERATURE,
                   use_schema: bool = True) -> dict:
    """
    Build one Vertex-compliant JSONL instance.
    NOTE: Vertex expects a top-level 'request' object.
    """
    custom_id = f"{career_term.replace(' ', '')}_profile_{i}"
    gen_cfg = {
        "temperature": float(temperature),
        "response_mime_type": "application/json",
    }
    if use_schema:
        gen_cfg["response_schema"] = _response_schema()

    return {
        "instance_id": custom_id,
        "request": {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {"role": "user", "parts": [{"text": f"Generate a profile for: {career_term}"}]}
            ],
            "generation_config": gen_cfg
        }
    }


# ---------- JSONL builders ----------
def build_jsonl_from_list(occupations: Iterable[str],
                          local_path: str,
                          per_occupation: int = 10000,
                          temperature: float = TEMPERATURE,
                          use_schema: bool = True) -> str:
    """
    Write N requests per occupation to one JSONL file.
    """
    Path(os.path.dirname(local_path) or ".").mkdir(parents=True, exist_ok=True)
    n = 0
    with open(local_path, "w", encoding="utf-8") as f:
        for occ in occupations:
            for i in range(1, per_occupation + 1):
                f.write(json.dumps(_make_instance(occ, i, temperature, use_schema)) + "\n")
                n += 1
    print(f"📝 Wrote {n} requests → {local_path}")
    return local_path

def build_jsonl_from_dict(missing_counts: Dict[str, int],
                          local_path: str,
                          temperature: float = TEMPERATURE,
                          use_schema: bool = True) -> str:
    """
    Write requests for a dict like: {"police officer": 213, "roofer": 87}
    """
    Path(os.path.dirname(local_path) or ".").mkdir(parents=True, exist_ok=True)
    n = 0
    with open(local_path, "w", encoding="utf-8") as f:
        for occ, count in missing_counts.items():
            c = int(count)
            if c <= 0:
                continue
            for i in range(1, c + 1):
                f.write(json.dumps(_make_instance(occ, i, temperature, use_schema)) + "\n")
                n += 1
    print(f"📝 Wrote {n} requests → {local_path}")
    return local_path

# ---------- GCS helpers ----------
def _split_gs(gs_uri: str):
    assert gs_uri.startswith("gs://"), "GCS URI must start with gs://"
    rest = gs_uri[5:]
    bucket, _, path = rest.partition("/")
    return bucket, path

def upload_to_gcs(local_path: str, gcs_uri: str) -> str:
    bucket_name, blob_path = _split_gs(gcs_uri)
    storage.Client().bucket(bucket_name).blob(blob_path).upload_from_filename(local_path)
    print(f"⬆️  Uploaded {local_path} → {gcs_uri}")
    return gcs_uri

def download_prefix(gcs_prefix: str, local_dir: str) -> int:
    bucket_name, prefix = _split_gs(gcs_prefix)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    n = 0
    for blob in client.list_blobs(bucket, prefix=prefix):
        if blob.name.endswith("/"):
            continue
        out = os.path.join(local_dir, os.path.basename(blob.name))
        blob.download_to_filename(out)
        n += 1
    print(f"⬇️  Downloaded {n} files from {gcs_prefix} → {local_dir}")
    return n

# ---------- Vertex BatchPrediction ----------
def submit_batch(gcs_input_uri: str = INPUT_URI,
                 gcs_output_prefix: str = OUTPUT_DIR,
                 project_id: str = PROJECT_ID,
                 region: str = REGION,
                 model_id: str = MODEL_ID,
                 display_name: Optional[str] = None):
    """
    Submit a Vertex BatchPredictionJob for Gemini.
    """
    aiplatform.init(project=project_id, location=region)
    if not display_name:
        display_name = f"gemini-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = _publisher_model_name(project_id, region, model_id)
    job = aiplatform.BatchPredictionJob.create(
        job_display_name=display_name,
        model_name=model_name,
        gcs_source=gcs_input_uri,
        gcs_destination_prefix=gcs_output_prefix,
        instances_format="jsonl",
        predictions_format="jsonl",
    )
    print(f"✅ Submitted: {job.resource_name}")
    print(f"   Output:    {gcs_output_prefix}")
    return job

def get_job(job_name: str, project_id: str = PROJECT_ID, region: str = REGION):
    aiplatform.init(project=project_id, location=region)
    # Constructor fetches the job resource
    return aiplatform.BatchPredictionJob(job_name)

def print_status(job_name: str, project_id: str = PROJECT_ID, region: str = REGION):
    job = get_job(job_name, project_id, region)
    # job.state can be an enum or int depending on version; handle both
    state = getattr(job.state, "name", str(job.state))
    print("Job:", job.resource_name)
    print("State:", state)
    if getattr(job, "error", None):
        print("Error:", job.error)
    outdir = job.output_info.gcs_output_directory if job.output_info else None
    print("Output Dir:", outdir)
    return job


def download_results(job_name: str,
                     local_parent_dir: str = "./vertex_outputs",
                     project_id: str = PROJECT_ID,
                     region: str = REGION) -> str | None:
    """
    Download Vertex batch results into a unique subfolder inside local_parent_dir.
    The subfolder name mirrors the GCS output folder (e.g., 'prediction-model-...').
    Returns the absolute path to the created local folder, or None if not ready.
    """
    aiplatform.init(project=project_id, location=region)
    job = aiplatform.BatchPredictionJob(job_name)

    # Ensure job succeeded
    state = getattr(job.state, "name", str(job.state))
    if state != "JOB_STATE_SUCCEEDED":
        print("Job not finished. State:", state)
        return None

    # Determine the remote output dir
    gcs_outdir = getattr(job.output_info, "gcs_output_directory", None)
    if not gcs_outdir:
        print("No output directory found on the job.")
        return None

    # Derive a stable local subfolder name
    # Prefer the last path component of the GCS directory (prediction-model-...)
    out_suffix = gcs_outdir.rstrip("/").split("/")[-1] if "/" in gcs_outdir else None
    if not out_suffix:
        # Fallback to job id if for some reason suffix can't be parsed
        out_suffix = job_name.split("/")[-1]

    local_out_dir = os.path.join(local_parent_dir, out_suffix)
    Path(local_out_dir).mkdir(parents=True, exist_ok=True)

    # Download everything under that GCS prefix into the new subfolder
    download_prefix(gcs_outdir, local_out_dir)

    abs_path = os.path.abspath(local_out_dir)
    print(f"✅ Saved results to: {abs_path}")
    return abs_path
