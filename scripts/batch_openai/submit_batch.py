import json
from openai import OpenAI
import batch_utils

# ./venv/scripts/activate

client = OpenAI(api_key)
def main():
    occupations = [
        "chief executive officer",
        "computer programmer",
        "software developer",
        "engineer",
        "drafter",
        "biologist",
        "chemist",
        "primary school teacher"
    ]

    batch_fname = "batch_test"

    batch = batch_utils.create_and_submit_batch(occupations, batch_fname + ".jsonl")
    print(f"Submitted batch {batch_fname} \n")

    print(batch)

    with open(f"../../profiles/openai/jsonls{batch_fname}_id.txt", 'w') as file:
        file.write(batch.id)

if __name__=="__main__":
    main()