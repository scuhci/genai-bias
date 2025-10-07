import json
import batch_utils

def main():
    batch_id = ""
    with open(batch_id, 'r') as file:
        batch_id = file.readlines()[0]
    
    batch_utils.check_batch(batch_id)
    
if __name__=="__main__":
    main()