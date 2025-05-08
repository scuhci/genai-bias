import json
import batch_utils

def main():
    batch_id = ""
    with open("/home/lonalynn/HCI/genai-bias/profiles/openai/batch_ids/batch_3_compprog_to_bio_id.txt", 'r') as file:
        batch_id = file.readlines()[0]
    
    batch_utils.check_batch(batch_id)
    
if __name__=="__main__":
    main()