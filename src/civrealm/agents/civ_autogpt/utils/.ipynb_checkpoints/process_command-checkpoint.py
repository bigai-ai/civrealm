import os
import openai
import pinecone
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain


pinecone.init(
    api_key="a0f60dc9-dd3e-40d3-ab5d-983421854662",
    environment="asia-southeast1-gcp-free"
)

os.environ["OPENAI_API_KEY"] = "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"
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
index = Pinecone.from_existing_index(index_name='langchain-demo', embedding=OpenAIEmbeddings())#, namespace='github-llama-index')

def get_similiar_docs(query, index = index, k=2, score=False):
    if score:
        similar_docs = index.similarity_search_with_score(query, k=k)
    else:
        similar_docs = index.similarity_search(query, k=k)
    return similar_docs



# model_name = "text-davinci-003"
model_name = "gpt-3.5-turbo"
# model_name = "gpt-4"
llm = OpenAI(model_name=model_name)
 
chain = load_qa_chain(llm, chain_type="stuff")
 
def get_answer(query):
    similar_docs = get_similiar_docs(query)
    answer = chain.run(input_documents=similar_docs, question=query)
    return answer

# query = "What is the paper like things on the game screen?"
# answer = get_answer(query)
# print(answer)

def process_command(command_json, ga, obs_input_prompt, current_unit_name, current_avail_actions):
    '''
    manualAndHistorySearch
    ask
    askCurrentGameInformation
    finalDecision
    ga is the GPTAgent Object
    '''
    command_name = command_json['name']
    command_input = command_json['input']
    if command_json['name'] == 'finalDecision' and command_input['action']:
        # Here to implement controller
        while True:
            print(command_input['action'])
            if command_input['action'] not in current_avail_actions:
                ga.update_dialogue(obs_input_prompt, pop_num = 2)
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
        ga.dialogue.append({'role': 'user', 'content': answer})
        ga.memory.save_context({'assistant': query}, {'user': answer})
    else:
        # ipdb.set_trace()
        print('error')
        print(command_json)
        ga.dialogue.pop(-1)
        # return 'error'






