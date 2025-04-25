import json
from openai import OpenAI
import batch_utils

client = OpenAI(api_key)

def main():
    batch_id = ""
    with open("batch_1_id.txt", 'r') as file:
        batch_id = file.readlines()[0]
    
    batch_utils.retrieve_results(batch_id)
    
if __name__=="__main__":
    main()