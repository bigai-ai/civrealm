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

Installation
------------

```
sudo pip install https://github.com/chris1869/freeciv-bot

sudo civ_prep_selenium.sh

sudo build_freeciv_server

test_freeciv_web_gym

```

Example Gym
------------

For an initial start on training models on freeciv-web - see the example installed by running

```
test_freeciv_web_gym

```

It will run gym_freeciv_web/random_test with the key class RandomAgent(object). The central function is

```
	def act(self, observation, reward, done):
```

It uses the current observation, reward of the last actions to calculate the next actions (in this case purely randomly).

``` 
        state = observation[0]
        action_opts = observation[1]
```
Observation is a tuple of the current state of the game and the action_options. Both state and action_opt are themselves dictionaries describing different aspects of the game, namely:

* city - Overview on state of each individual city (improvements, production, etc.) and actions each city can take (work, unwork tiles, produce units/improvements, etc.)
* client - Contains information on the current client communicating with the server
* dipl - Currently deprecated information on diplomacy - see player
* game - Contains current game information - mostly irrelevant for training
* gov - Overview on government state - allows to change government forms
* map - Overview on map, i.e., status (known, visible, etc.), terrain types and potential extras
* options - Overview on additional options for the game that are active
* rules - Overview on all rules and detailed/static descriptions (tech types, unit types, etc.) that are relevant for the game
* player - Overview on player status (scores, etc.) and ability to take diplomatic actions (experimental stage) 
* tech - Overview on currently active technologies as well as ability to change research goals or researching specific technologies
* unit - Overview on current unit status (health, moves left, etc.) and ability for moving/activity of units

A detailed description can be found in two json files (example_observation_turn15_state, example_observation_turn15_actions).

The main routine for applying a model will require iterating over all actors and select a certain action based on the given state.

```
     for actor_id in action_opts["unit"].get_actors():
         print("Trying Moving units or build city: %s" % actor_id)
```

Then one needs to check if the unit/city etc. can actually perform an action anymore and check which actions are actually possible.

```
         if action_opts["unit"]._can_actor_act(actor_id):
             pos_acts = action_opts["unit"].get_actions(actor_id, valid_only=True)
```

Then, one can apply the model, i.e., there is a 50% chance for a settler to build a city rather than move in a random direction

```
             if "build" in pos_acts.keys() and random.random() > 0.5:
                 return action_opts["unit"], pos_acts["build"]
             move_action = random.choice([key for key in pos_acts.keys() if "goto" in key])
             print("in direction %s" % move_action)
             return action_opts["unit"], pos_acts[move_action]
```

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
        for unit_id in a_options.get_actors(): 
            action_wants[unit_id] = {}
            actions =  a_options.get_actions(unit_id)
            for action_key in actions:
```

First one needs to ensure that the action is actually valid.

```
        if actions[action_key] is None:
            continue
```
Than likelihood/wantedness of moves needs to be set.

Example 1: Enable Auto-explore - 

action_key refers to the type of action the unit can do. Example: if explore is available - exploring is "WANTED"

```
                if action_key == "explore":
                    action_wants[unit_id][action_key] = ACTION_WANTED
```
                
Example 2: Move randomly in all directions, i.e., set random likelihood for moves that are not DIR8_STAY

```
				elif "goto" in action_key:
                    action_wants[unit_id][action_key] = ACTION_WANTED*random()*0.25
```

Example 3: Build city with high likelihood

```
                elif action_key == "build":
                    action_wants[unit_id][action_key] = ACTION_WANTED*random()*0.75
```
Example 4: Set all other actions to ACTION_UNWANTED

```
				else:
                    action_wants[unit_id][action_key] = ACTION_UNWANTED
```
