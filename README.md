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
python template.py
```
On the bottom of the file you will see, the key interface on how to connect to the server and
to link the bot to the server.

Create the SimpleBot instance - which is a simple bot that randomly moves units and builds cities

```
my_bot = SimpleBot()
```
Create the CivClient instance - which handles all controllers (i.e., state, potential actions and processing server messages)

```
my_civ_client = CivClient(my_bot, "chrisrocks", client_port=6000)
```

Create the CivConnection - which establishes a handshake to the freeciv server on http://localhost and hands over control to CivClient my_civ_client and its controllers once handshake is complete

```
CivConnection(my_civ_client, 'http://localhost')
```

Prerequisites
--------

In order to test the overall bot on http://localhost, kindly follow the docker installation instructions on https://github.com/freeciv/freeciv-web.

Building your own bot
--------

The file template.py gives an initial example on how a bot should work. The basic idea is that a bot is only responsible for calculating the "action_want" of a certain action given the full state of the board. In SimpleBot, only unit_actions have been defined.

```
class SimpleBot(BaseBot):
    def calculate_unit_actions(self, turn_no, full_state, a_options):
        action_wants = {}
```

The overwritten function needs to return a dictionary with the "action_want" for each action of each unit (or more general an actor - see utils.base_action.ActionList as reference). Hence, one needs to iterate over all units punit and all action_optoins a_option.

```
        for punit in a_options: 
            action_wants[punit] = {}
            for a_option in a_options[punit]:
```

First one needs to ensure that the action is actually valid.

```
        if a_options[punit][a_option] is None:
            continue
```
Than likelihood/wantedness of moves needs to be set.

Example 1: Enable Auto-explore - 

a_option[0] refers to the type of action the unit should conduct
a_option[1] refers to the direction the unit should move/act 

```
				if a_option[1] == DIR8_STAY and a_option[0] in ["explore"]:
					action_wants[punit][a_option] = ACTION_WANTED
```
                
Example 2: Move randomly in all directions, i.e., set random likelihood for moves that are not DIR8_STAY

```
                elif a_option[1] != DIR8_STAY and a_option[0] == "goto":
                    action_wants[punit][a_option] = ACTION_WANTED*random()*0.25
```

Example 3: Build city with high likelihood

```
                elif a_option[1] == DIR8_STAY and a_option[0] == "build":
                    action_wants[punit][a_option] = ACTION_WANTED*random()*0.75
```