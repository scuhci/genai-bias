import json
import os
import requests
import batch_utils 

def main():
    # path where you store the batch ID
    batch_id_file = "../../profiles/mistral/batch_ids/batch9_id.txt"

    if not os.path.exists(batch_id_file):
        raise FileNotFoundError(f"Missing batch ID file: {batch_id_file}")

    with open(batch_id_file, 'r') as file:
        batch_id = file.readline().strip()

    batch_utils.check_batch(batch_id)

if __name__ == "__main__":
    main()