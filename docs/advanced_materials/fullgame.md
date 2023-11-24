## Observations and actions

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
