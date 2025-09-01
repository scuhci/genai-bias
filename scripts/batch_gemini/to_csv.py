# to_csv.py — Vertex JSONL → per-career CSVs (supports response|predictions)
import os, re, json, csv, glob
from pathlib import Path

VERTEX_OUT_DIR = "./vertex_outputs"   # where you downloaded results
CSV_OUT_DIR = "./vertex_csvs"
CSV_HEADERS = ["name","age","gender","ethnicity","salary","motivations","biography"]

def strip_code_fences(s: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip())

def best_effort_json(s: str):
    s = strip_code_fences(s)
    # try strict json
    try:
        return json.loads(s)
    except Exception:
        pass
    # quote bare keys + remove trailing commas then retry
    s2 = re.sub(r'(?m)^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', s)
    s2 = re.sub(r',\s*([}\]])', r'\1', s2)
    return json.loads(s2)

def career_key_from_instance_id(instance_id: str) -> str:
    # e.g. "computerprogrammer_profile_42" -> "computerprogrammer"
    key = ''.join(ch for ch in instance_id if ch.isalpha()).lower()
    if key.endswith("profile"):
        key = key[:-7]
    return key

def extract_text_from_response_obj(response_obj: dict) -> str:
    """
    Handle the 'response' shape:
    {"response":{"candidates":[{"content":{"parts":[{"text":"..."}]}}]}}
    """
    try:
        return response_obj["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        # some variants
        try:
            return response_obj["candidates"][0]["content"][0]["text"]
        except Exception:
            return ""

def extract_text_from_predictions_list(preds) -> str:
    """
    Handle the 'predictions' shape (list or dict).
    """
    if isinstance(preds, dict):
        preds = [preds]
    if not preds:
        return ""
    p0 = preds[0]
    # A) candidates -> content -> parts -> text
    try:
        return p0["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass
    # B) candidates -> content (list) -> [0]["text"]
    try:
        return p0["candidates"][0]["content"][0]["text"]
    except Exception:
        pass
    # C) direct fields sometimes present
    for k in ("output_text", "text"):
        v = p0.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return ""

def find_instance_id(obj: dict) -> str:
    # Prefer top-level instance_id (your output)
    iid = obj.get("instance_id")
    if isinstance(iid, str) and iid:
        return iid
    # Fallback to nested shape
    inst = obj.get("instance", {})
    if isinstance(inst, dict):
        iid2 = inst.get("instance_id")
        if isinstance(iid2, str) and iid2:
            return iid2
    return "unknown"

def main():
    Path(CSV_OUT_DIR).mkdir(parents=True, exist_ok=True)

    files = glob.glob(os.path.join(VERTEX_OUT_DIR, "**", "*.jsonl"), recursive=True)
    # Prefer the main predictions.jsonl if present (incrementals can be partial/empty)
    main_preds = [p for p in files if os.path.basename(p) == "predictions.jsonl"]
    files = main_preds if main_preds else files

    print(f"Found {len(files)} JSONL files in {VERTEX_OUT_DIR}")
    if not files:
        return

    writers = {}  # career -> (fh, writer)
    total_lines = parsed_lines = 0

    for path in files:
        file_total = file_parsed = 0
        print(f"Reading: {path}")
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                total_lines += 1
                file_total += 1

                try:
                    obj = json.loads(line)
                except Exception:
                    continue

                # Get text payload from either 'response' or 'predictions'
                text = ""
                if "response" in obj:
                    text = extract_text_from_response_obj(obj["response"])
                elif "predictions" in obj or "prediction" in obj:
                    text = extract_text_from_predictions_list(obj.get("predictions") or obj.get("prediction"))
                else:
                    # unknown shape; skip
                    continue

                if not text:
                    continue

                # Parse the model's JSON text (fenced or loose)
                try:
                    data = best_effort_json(text)
                except Exception:
                    continue

                # Normalize ethnicity to CSV-friendly string
                eth = data.get("ethnicity", "")
                if isinstance(eth, list):
                    ethnicity = ",".join(str(x) for x in eth)
                else:
                    ethnicity = str(eth)

                row = [
                    data.get("name",""),
                    data.get("age",""),
                    data.get("gender",""),
                    ethnicity,
                    data.get("salary",""),
                    data.get("motivations",""),
                    data.get("biography",""),
                ]

                iid = find_instance_id(obj)
                key = career_key_from_instance_id(iid)

                out_path = os.path.join(CSV_OUT_DIR, f"{key}_gemini.csv")
                if key not in writers:
                    fh = open(out_path, "a", newline="", encoding="utf-8")
                    w = csv.writer(fh)
                    if os.path.getsize(out_path) == 0:
                        w.writerow(CSV_HEADERS)
                    writers[key] = (fh, w)

                writers[key][1].writerow(row)
                parsed_lines += 1
                file_parsed += 1

        print(f"Summary for {os.path.basename(path)}: {file_parsed}/{file_total} rows parsed")

    for fh, _ in writers.values():
        fh.close()

    print(f"\n✅ Done. Parsed {parsed_lines}/{total_lines} lines.")
    print(f"CSVs written to: {CSV_OUT_DIR}")

if __name__ == "__main__":
    main()
