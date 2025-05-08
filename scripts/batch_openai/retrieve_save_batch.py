import json
from openai import OpenAI
import batch_utils

def main():
    # batch_id = ""
    # with open("batchid_test.txt", 'r') as file:
    #     batch_id = file.readlines()[0]
    
    batch_utils.retrieve_results("batch_681aef1d591481908f6b3aa94e17806a")
    
if __name__=="__main__":
    main()