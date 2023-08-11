import os
import openai
import time
import random
import json
import requests
import warnings

from freeciv_gym.agents.civ_autogpt.utils.num_tokens_from_messages import num_tokens_from_messages
from freeciv_gym.agents.civ_autogpt.arguments import *
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory

import pinecone
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain




warnings.filterwarnings('ignore')

USE_API2D = False


if USE_API2D:
    url = "https://openai.api2d.net/v1/chat/completions"
    headers = {
      'Content-Type': 'application/json',
      'x-api2d-no-cache': '1',
      'Authorization': 'Bearer fk197355-JjePlHbuNVLQWD1Tp6dGGVeF857kxtxV'#'Bearer fkxxxx' # <-- 把 fkxxxxx 替换成你自己的 Forward Key，注意前面的 Bearer 要保留，并且和 Key 中间有一个空格。
    }
else:
    url = ""
    headers = {"":""}


cwd = os.getcwd()
openai_keys_file = os.path.join(cwd, "src/freeciv_gym/agents/civ_autogpt/openai_keys.txt")
task_prompt_file = os.path.join(cwd, "src/freeciv_gym/agents/civ_autogpt/prompts/task_prompt.txt")
state_prompt_file = os.path.join(cwd, "src/freeciv_gym/agents/civ_autogpt/prompts/state_prompt.txt")


TOKEN_LIMIT_TABLE = {
    "gpt-4": 8192,
    "gpt-4-0314": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0314": 32768,
    "gpt-3.5-turbo-0301": 4096,
    "gpt-3.5-turbo": 4096,
    "text-davinci-003": 4080,
    "code-davinci-002": 8001,
    "text-davinci-002": 2048
}




class GPTAgent:
    """
    This agent uses GPT-3 to generate actions.
    """
    def __init__(self, model = "gpt-3.5-turbo"):
        self.model = model
        self.dialogue = []
        self.agent_index = None
        self.message = ''

        self.openai_api_keys = self.load_openai_keys()
        self.state_prompt = self._load_state_prompt()
        self.task_prompt = self._load_task_prompt()
        self.update_key()

        llm = ChatOpenAI(temperature=0.0, openai_api_key = openai.api_key)
        self.memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=500)

        self.chain = load_qa_chain(OpenAI(model_name=model), chain_type="stuff")

        pinecone.init(
            api_key="a0f60dc9-dd3e-40d3-ab5d-983421854662", environment="asia-southeast1-gcp-free"
        )
        # # "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"
        # embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.index = Pinecone.from_existing_index(index_name='langchain-demo', embedding=OpenAIEmbeddings(model="text-embedding-ada-002"))

    def get_similiar_docs(self, query, index, k=2, score=False):
        index = self.index
        if score:
            similar_docs = index.similarity_search_with_score(query, k=k)
        else:
            similar_docs = index.similarity_search(query, k=k)
        return similar_docs

    def get_answer(self, query):
        similar_docs = get_similiar_docs(query)
        answer = chain.run(input_documents=similar_docs, question=query)
        return answer
        
    @staticmethod
    def load_openai_keys():
        with open(openai_keys_file, "r") as f:
            context = f.read()
        return context.split('\n')

    def _load_state_prompt(self):

        with open(state_prompt_file, "r") as f:
            self.state_prompt = f.read()

        self.dialogue.append({"role": "user", "content": self.state_prompt})

        return self.state_prompt

    def _load_task_prompt(self):
        # print("reading task prompt from {}".format(task_prompt_file))
        with open(task_prompt_file, "r") as f:
            self.task_prompt = f.read()
        # self.dialogue.append({"role": "user", "content": self.task_prompt})
        self.dialogue.append({"role": "user", "content": self.task_prompt})
        # self.dialogue.append(self.parse_response(self.query()))


    def update_key(self):
        curr_key = self.openai_api_keys[0]
        openai.api_key = os.environ["OPENAI_API_KEY"] = curr_key
        self.openai_api_keys.pop(0)
        self.openai_api_keys.append(curr_key)

    def process_command(self, command_json, obs_input_prompt, current_unit_name, current_avail_actions):
        '''
        manualAndHistorySearch
        ask
        askCurrentGameInformation
        finalDecision
        '''
        command_name = command_json['name']
        command_input = command_json['input']
        if command_json['name'] == 'finalDecision' and command_input['action']:
            # Here to implement controller
            while True:
                print(command_input['action'])
                if command_input['action'] not in current_avail_actions:
                    self.update_dialogue(obs_input_prompt, pop_num = 2)
                    continue
                else:
                    break

        elif command_json['name'] == 'ask' and command_input['question']:
            print(command_input)
            # return ''
        elif command_json['name'] == 'askCurrentGameInformation' and command_input['query']:
            print(command_input)

            # return ''
        elif command_json['name'] == 'manualAndHistorySearch' and command_input['look_for']:
            print(command_input)
            query = command_input['look_for']
            answer = get_answer(query)
            print('answer:', answer)
            self.dialogue.append({'role': 'user', 'content': answer})
            self.memory.save_context({'assistant': query}, {'user': answer})
        else:
            print('error')
            print(command_json)
            self.dialogue.pop(-1)
            # return 'error'


    # def query(self, model="gpt-3.5-turbo-0301"):
    def query(self, stop = None, temperature = 0.1):
        self.restrict_dialogue()
        # TODO add retreat mech to cope with rate limit
        self.update_key()
        
        if self.model in ['gpt-3.5-turbo-0301', 'gpt-3.5-turbo']:
            if USE_API2D:
                data = {
                  "model": self.model,
                  "messages": self.dialogue
                }
                response = requests.post(url, headers=headers, json=data)
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.dialogue
                )
        elif self.model in ['gpt-4-0314', 'gpt-4']:
            
            data = {
              "model": self.model,
              "messages": self.dialogue,
              "max_tokens": 128
            }
            response = requests.post(url, headers=headers, json=data)
            
            time.sleep(15)
        else:
            response = openai.Completion.create(
                        model=self.model,
                        prompt=str(self.dialogue),
                        max_tokens=1024,
                        stop=stop,
                        temperature=temperature,
                        n = 1,
                        top_p = 0.95
                    )

        return response

    def update_dialogue(self, chat_content, pop_num = 0):
        if pop_num != 0:
            for i in range(pop_num):
                self.dialogue.pop(-1)
        
        return self.communicate(chat_content)

    # @staticmethod
    def parse_response(self, response):
        if self.model in ['gpt-3.5-turbo-0301', 'gpt-3.5-turbo', 'gpt-4', 'gpt-4-0314']:
            if USE_API2D:
                return response.json()["choices"][0]["message"]
            else:
                
                return dict(response["choices"][0]["message"])
            
            # return response.json()["choices"][0]["message"]
        else:
            # self.model in ['text-davinci-003', 'code-davinci-002']
            
            return {'role': 'assistant', 'content': response["choices"][0]["text"][2:]}

    def restrict_dialogue(self):
        limit = TOKEN_LIMIT_TABLE[self.model]
        
        """
        The limit on token length for gpt-3.5-turbo-0301 is 4096.
        If token length exceeds the limit, we will remove the oldest messages.
        """
        # TODO validate that the messages removed are obs and actions
        while num_tokens_from_messages(self.dialogue) >= limit:
            temp_message = {}
            user_tag = 0
            if self.dialogue[-1]['role'] == 'user':
                temp_message = self.dialogue[-1]
                user_tag = 1

            while len(self.dialogue) >= 3:
                self.dialogue.pop(-1)

            self.dialogue.append({'role': 'user', 'content': 'The former chat history can be summarized as: \n' + self.memory.load_memory_variables({})['history']})
            

            if user_tag == 1:
                self.dialogue.append(temp_message)
                user_tag = 0
            

    def communicate(self, content, parse_choice_tag = False):
        self.dialogue.append({"role": "user", "content": content})
        pop_flag = 0
        while True:
            try:
                raw_response = self.query()
                self.message = self.parse_response(raw_response)
                self.dialogue.append(self.message)

                response = self.message["content"]

                try:
                    json.loads(response)
                except Exception as e:
                    # self.dialogue.pop(-1)
                    print(e)
                    self.dialogue.append({"role": "user", \
                        "content": "You should only respond in JSON format as described"})
                    print('Not response json, retrying...')
                    continue
                break

            except Exception as e:
                print(e)
                print("retrying...")
                # self.dialogue.pop(-1)
                # self.dialogue.pop(-1)
                continue
        return response

    def reset(self):
        # super().reset()
        self.dialogue = []
        self.agent_index = None
        self.message = ''
        # self.gpt_extractor.reset()

        self.openai_api_keys = self.load_openai_keys()
        self.state_prompt = self._load_state_prompt()
        self.task_prompt = self._load_task_prompt()
 


