# LLM Agent

Welcome to Civrealm LLM Agent！ This documentation will guide you through the process of building LLM agents in CivRealm Environment. We will first provide an overview of CivRealm LLM Env, followed by instruction on how to use the civrealm-llm-baseline repository to build a llm agent **Mastaba** on this environment.

## 🌏 Civrealm Tensor Environment

The Civrealm LLM Environment is a LLM environment wrapped
upon Civrealm Base Env specifically designed for building LLM agents. This environment

- provides observations of each actor in natural language
- provides valid actions of each actor in natural language
- restricts valid actions in order to reduce meaningless actions
- executes actions described by natural language

Besides, a LLM wrapper is open to customize your own environment.


### Quick Start
Start a single FreecivLLM environment :

````python
env = gymnasium.make("freeciv/FreecivLLMEnv-v0", client_port=Ports.get())
obs, info = env.reset()
````

### LLM Info
Observations and actions in natural language are stored in llm_info as:

````python
info["llm_info"]
````

llm_info is a Dict consisting of 2 subspaces with keys "unit" and "city". Subspace of "unit" is a Dict with keys of unit_id, and subspace of "city" is a Dict with keys of city_id, describing "name", "available_actions", and "observations" of the corresponding unit and city.

Read llm_info of "unit 121" by:

````python
info["info_info"]['unit']['121']
````


### Observation

Read observations of "unit 121" by:  

````python
info['llm_info']['unit']['121']['observations']
````

### Action

Read valid action of "unit 121" by:

````python
info['llm_info']['unit']['121']['available_actions']
````


## 🤖 Architecture of Mastaba

Mastaba requires Python version >=3.8.
Additional packages (and versions) are listed in
`requirements.txt`.

### LLM Preparations

Before running the agents, several environment variables should be set:

```
# Group 1
export OPENAI_API_TYPE=<api-type>                           # e.g. 'azure'
export OPENAI_API_VERSION='<openai-api-version>'
export OPENAI_API_BASE=<openai-api-base>                    # e.g. 'https://xxx.openai.azure.com'
export OPENAI_API_KEY=<openai-api-key>
export DEPLOYMENT_NAME=<deployment-name>                    # e.g. 'gpt-35-turbo-16k'
# Group 2
export AZURE_OPENAI_API_TYPE=<azure-openai-api-type>        # e.g. 'azure'
export AZURE_OPENAI_API_VERSION=<azure-openai-api-version>  # e.g. '2023-05-15'
export AZURE_OPENAI_API_BASE=<azure-openai-api-base>
export AZURE_OPENAI_API_KEY=<azure-openai-api-key>
# Group 3
export LOCAL_LLM_URL=<local-llm-url>                        # You may choose to use local LLM.
# Pinecone
export MY_PINECONE_API_KEY=<pinecone-api-key>               # Necessary. Free account is enough.
export MY_PINECONE_ENV=<pinecone-env>                       # e.g. 'gcp-starter'
```

The above Groups are independent. One may set only one group and just use that group. OpenAI GPT is preferred.

After setting the above variables, run `python main.py`

### Choosing Models

In file `main.py`, function `main()`, set `agent=BaseLangAgent()` or `agent=MastabaAgent()` to switch
between agents **BaseLang** and **Mastaba**

### Run the model

After the above configuration, `python run.py` can make the LLM agent run on single-player (vs rule-based AI of freeciv) mode. You may monitor the game via Freeciv-Web in web browser: visit `http://localhost:8888`, find the multiplayer game according to the **port id** which you can find in the console. Then input `/observe` in chatbox to start observing the game.
