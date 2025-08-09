import json
import os
import batch_utils

def main():
    occupations = [
        "garbage collector"
    ]

    batch_fname = "batch9"

    batch = batch_utils.create_and_submit_batch(occupations, batch_fname + ".jsonl")
    print(f"Submitted batch {batch_fname}\n")
    print(json.dumps(batch, indent=2))

    os.makedirs("../../profiles/mistral/batch_ids", exist_ok=True)
    batch_id_path = f"../../profiles/mistral/batch_ids/{batch_fname}_id.txt"
    with open(batch_id_path, 'w') as file:
        file.write(batch["id"])

if __name__ == "__main__":
    main()
