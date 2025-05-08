import json
import batch_utils

# ./venv/scripts/activate
# /home/lonalynn/HCI/genai-bias/.venv/bin/activate
# source .venv/bin/activate

def main():
    occupations = [
    "computer programmer",
    "software developer",
    "engineer",
    "drafter",
    "biologist",
    ]

    batch_fname = "batch_3_compprog_to_bio"

    batch = batch_utils.create_and_submit_batch(occupations, batch_fname + ".jsonl")
    print(f"Submitted batch {batch_fname} \n")

    print(batch)

    with open(f"../../profiles/openai/batch_ids/{batch_fname}_id.txt", 'w') as file:
        file.write(batch.id)

if __name__=="__main__":
    main()