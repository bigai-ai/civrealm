We provide 2 styles of LLM based agents in the repository: **BaseLang** and **Mastaba**.

## System Requirements
BaseLang and Mastaba requires Python version >=3.8.
Additional packages (and versions) are listed in
`requirements.txt`.


## LLM Preparations
Before running the agents, several environment variables should be set:
```
# Group 1
export OPENAI_API_TYPE=<api-type>                           # e.g. 'azure'
export OPENAI_API_VERSION='<openai-api-version>'
export OPENAI_API_BASE=<openai-api-base>                    # e.g. 'https://xxx.openai.azure.com'
export OPENAI_API_KEY=<openai-api-key>
export DEPLOYMENT_NAME=<deployment-name>                    # e.g. 'gpt-35-turbo-16k'
# Group 2
export ASURE_OPENAI_API_TYPE=<asure-openai-api-type>        # e.g. 'azure'
export ASURE_OPENAI_API_VERSION=<asure-openai-api-version>  # e.g. '2023-05-15'
export ASURE_OPENAI_API_BASE=<asure-openai-api-base>
export ASURE_OPENAI_API_KEY=<asure-openai-api-key>
# Group 3
export LOCAL_LLM_URL=<local-llm-url>                        # You may choose to use local LLM.
# Pinecone
export MY_PINECONE_API_KEY=<pinecone-api-key>               # Necessary. Free account is enough.
export MY_PINECONE_ENV=<pinecone-env>                       # e.g. 'gcp-starter'
```
The above Group 1/2/3 are independent. One may set only one group and just use that group.

OpenAI GPT is preferred (results in the paper are most from model `gpt-35-turbo-16k`)

After setting the above variables, run `python main.py`

## Choosing Models
In file `main.py`, function `main()`, set `agent=BaseLangAgent()` or `agent=MastabaAgent()` to switch
between agents **BaseLang** and **Mastaba**

## Run the model
After the above configuration, `python run.py` can make the LLM agent run on single-player (vs rule-based AI of freeciv) mode. You may monitor the game via Freeciv-Web in web browser: visit `http://localhost:8888`, find the multiplayer game according to the **port id** which you can find in the console. Then input `/observe` in chatbox to start observing the game.

