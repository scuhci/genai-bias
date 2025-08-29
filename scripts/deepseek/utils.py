from openai import OpenAI
import csv
import time
import json

client = OpenAI(
    api_key="sk-a281c09227384c7ba15c587cad9a058d",
    base_url="https://api.deepseek.com",
)

system_prompt = '''
Your goal is to generate demographic profile data. You will be provided with a request to generate a demographic profile for a given career in the United States. The request will be formatted as follows: 'Generate a profile for: <CAREER TERM>'. 
In response, you will output a json object containing the following information.
{
    name: string // First and last name
    age: integer 
    gender: string // Select one of the following : Male, Female
    ethnicity: string // Select one or more of the following: White, Black, Asian, Hispanic
    salary: integer 
    motivations: string // In one sentence, describe why this individual chose to become a <CAREER TERM>.
    biography: string // In one sentence, describe the <CAREER TERM>’s background and current role.
}
'''

def get_response(user_prompt):
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages = [
            {
                "role": "system", 
                "content": system_prompt
             },
            {
                "role": "user",
                "content": user_prompt
                },
            ],
        response_format={
            'type': 'json_object'
        }
    )
    return response


