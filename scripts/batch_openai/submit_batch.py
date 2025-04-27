import json
from openai import OpenAI
import batch_utils

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

    batch_fname = "batch_1.jsonl"

    batch = batch_utils.create_and_submit_batch(occupations, batch_fname)
    print(f"Submitted batch {batch_fname} \n")

    print(batch)

    with open("../../profiles/openai/jsonls/batch_1_id.txt", 'w') as file:
        file.write(batch.id)

if __name__=="__main__":
    main()