# freeciv-bot

Summary
--------

Freeciv-bot allows to steer freeciv via Python and build automated bots that can ultimately beat human players. The main goal is to foster AI research using a round-based strategy game like freeciv.

Looking for contributors, AI and Freeciv enthusiasts. 

Motivation
--------

Pace of AI research is ever increasing. Recent breakthroughs by AlphaZero, AlphaGo show capabilities of current systems to master "simple" board games via reinforcement learning and Montecarlo tree search (MCTS). OpenAI and Deepmind already start tackling more complex strategy games like Dota 2 and Starcraft 2. The key challenges when switching from board games to strategy games is:

a) Knowledge of state of board is incomplete - therefore information has a cost: Due to fog of war (and unclear worklists, resources) position/status of the enemy and overall map is not fully known - hence risky investments (explorer teams) are required to gain information
 
b) Number of actors/actions is unlimited: Buildings, Cities, Units can be produced infinitely - hence the data model and learning method for neural networks etc. needs to be more dynamic and will face more sparce option spaces

c) More long-term consequences: In many cases, effect of actions and decisions can only be seen after several rounds, minutes of play. The longer an effect takes to materialize, mapping the actions/decisions to the very effect gets more complicated. Hence, "naive" greedy approaches to improving a single score (e.g., Flipper, Super Mario, etc.) won't cut it.  

On top of these challenges real-time strategy games due their continuous time and space add another layer of complexity (e.g., optimal formation of units, evade balistic projectiles or missiles).

In order to focus on a) b) and c) only, round-based games like Freeciv are a potential intermediate step for developing AI before jumping to real-time strategy games. 


API
--------

Example Bot
--------
A simple bot can move units randomly, create cities and auto-explores territory.

Just run
```
python civclient.py
```
On the bottom of the file you will see, the key interface on how to connect to the server and
to link the bot to the server.

```
my_bot = FreeCivBot()
my_civ_client = CivClient(my_bot, client_port=6000)
clinet.CivConnection(my_civ_client)
```

Prerequisites
--------

In order to test the overall bot, kindly follow the docker installation instructions on https://github.com/freeciv/freeciv-web.

Building your own bot
--------