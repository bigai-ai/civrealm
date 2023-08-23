import json
import requests
import ipdb
import re

pattern = r"```([\s\S]*?)```"

headers = {'Content-Type': 'application/json'}
url = 'http://10.2.32.5:54321/llm_inference'
tmp_dia = [{'role': 'user', 'content':'Hello, Who are you?'}, {'role': 'assistant', 'content':'I am LLM.'}, {'role': 'user', 'content':'Good, Give me an example about how to use you.'}]
tmp_config = {'temperature':0.7, 'top_p': 0.95, 'repetition_penalty': 1.1}

def send_message_to_llama(dialogue: list = tmp_dia, config = tmp_config):
    content = {'message': dialogue, 'config': config}
    response = requests.post(
                url=url, 
                headers = headers, 
                data = json.dumps(content)
                ).text
    # matches = re.findall(pattern, response.split('### Response:')[-1])
    # ipdb.set_trace()
    matches = response.split('### Response:')[-1]
    response = matches.split('json')[-1].split('</s>')[0].strip().replace('\n', '').replace('\r', '')
    # matches = response.split('ASSISTANT:')[-1]
    # response = matches.split('json')[-1].split('</s>')[0].strip().replace('\n', '').replace('\r', '')
    # ipdb.set_trace()
    return response


# print('test the connection (good if having output):', send_message_to_llama(dialogue))
# ipdb.set_trace()


