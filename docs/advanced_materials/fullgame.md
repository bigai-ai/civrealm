## Initialize a Full-Game

By default, an environment specified by `civrealm/FreecivBase-v0` will run the full-game.

```python
from civrealm.agents import ControllerAgent
import gymnasium

env = gymnasium.make('civrealm/FreecivBase-v0')
agent = ControllerAgent()
observations, info = env.reset(client_port=fc_args['client_port'])
done = False
step = 0
while not done:
    try:
        action = agent.act(observations, info)
        observations, reward, terminated, truncated, info = env.step(
            action)
        print(
            f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
            f'Truncated: {truncated}, action: {action}')
        step += 1
        done = terminated or truncated
    except Exception as e:
        fc_logger.error(repr(e))
        raise e
env.close()
```

## Observations and Actions
To implement an agent that plays the full-game, it is important to understand the content of the observations returned by the environment and the format of the actions required by the environment.

### Unit Actions

|Action Class| Action Description                              | Parameter                |
|------------|-------------------------------------------------|-----------------------|
| ActGoto | Go to a target tile                                  | the target tile       |
| ActHutEnter | Enter a hut in the target tile for random events      | the target tile |
| ActEmbark | Embark on a target boat mooring in an ocean tile      | the target boat unit  |
| ActDisembark | Disembark from a target boat mooring in an ocean tile | the target boat unit  |
| ActUnloadUnit | Unload all units carried by the transporter unit  | -                     |
| ActBoard | Board a boat mooring in the city of the current tile  | -                     |
| ActDeboard | Deboard a boat mooring in the city of the current tile|    -                   |
| ActFortify | Fortify in the current tile                           | -                     |
| ActAttack | Attack the unit in a target tile                      | the target tile       |
| ActSpyBribeUnit | Bribe a unit of other players to join us              | the target unit       |
|ActConquerCity| Conquer a city belongs to other players              | the target city       |
|ActSpySabotageCity| Sabotage a city belongs to other players              | the target city       |
|ActSpyStealTech| Steal technology from a city belongs to other players | the target city       |
| ActMine | Mine in the current tile                              | -                     |
| ActIrrigation | Irrigate in the current tile                          |  -                     |
| ActBuildRoad | Build road in the current tile                        | -                      |
| ActBuildRailRoad | Build rail road in the current tile                        |      -                 |
| ActPlant | Plant trees in the current tile                       |   -                    |
| ActBuildCity | Build a city in the current tile                      |    -                   |
| ActAirbase | Build airbase in the current tile                     |     -                  |
| ActFortress | Build fortress in the current tile                    |    -                   |
| ActPollution | Remove pollution in the current tile                  |     -                  |
| ActTransform | Transform the terrain of the current tile             |      -                 |
| ActPillage | Pillage an infrastructure in the current tile         |          -             |
| ActCultivate | Cultivate the forest in the current tile into a plain  |              -         |
| ActUpgrade | Upgrade the unit                                      | -                     |
| ActDisband | Disband the unit itself to save cost                  |    -                   |
| ActKeepActivity | Keep the current activity in this turn                |    -                   |
| ActHomecity | Set the unit's home city as the city in the current tile |  -                   |
| ActJoinCity | Join the city in the current tile (increase city population) |  -                |
| ActMarketplace | Sell goods in the target city's marketplace           | the target city       |
| ActInvestigateSpend | Investigate a target city belongs to other players     | the target city    |
| ActEmbassyStay | Establish embassy in a target city belongs to other players |  the target city    |
| ActTradeRoute | Establish a trade route from the unit's home city to the target city | the target city |

### City Actions

| Action Class  | Action Description            | Parameter                        |
|--------|--------------------------------------|-------------------------------|
|        | Choose a working tile for city        | the target tile               |
|        | Do not work on a tile                 | the target tile               |
|        | Buy building or unit                 | -                             |
|        | Change the type of a specialist      | type of the target specialist |
|        | Sell a building                      | the target building           |
|        | Construct a building                 | the target building           |
|        | Produce a unit                       | the target unit               |

### Diplomacy Actions

| Action Class  | Action Description           | Parameter                          |
|--------|--------------------------|-----------------------------------------------|
|        | Start a negotiation      | target player ID                              |
|        | End a negotiation        | target player ID                              |
|        | Establish an embassy     | target player ID                              |
|        | Share vision             | target player ID                              |
|        | Cancel a treaty          | target player ID                              |
|        | Add a clause             | target player ID, target clause type or technology type |
|        | Remove a clause          | target player ID, target clause type or technology type |

### Government Actions

| Action Class  | Action Description           | Parameter                |
|--------|--------------------|-------------------------|
|        | Revolution         | the target Government   |
|        | Increase tax        | -                       |
|        | Increase science    | -                       |
|        | Increase luxury     | -                       |
|        | Decrease tax        | -                       |
|        | Decrease science    | -                       |
|        | Decrease luxury     | -                       |

### Technology Actions

| Action Class  | Action Description           | Parameter                |
|--------|--------------------|-------------------------|
|        | Set a current research goal         | the target technology   |
|        | Set a future research goal        | the target technology   |

Observation is a tuple of the current state of the game and the action_options. Both state and action_opt are themselves dictionaries describing different aspects of the game, namely:

* `city` - Overview on state of each individual city (improvements, production, etc.) and actions each city can take (work, unwork tiles, produce units/improvements, etc.)
* `client` - Contains information on the current client communicating with the server
* `dipl` - Currently deprecated information on diplomacy - see player
* `game` - Contains current game information - mostly irrelevant for training
* `gov` - Overview on government state - allows to change government forms
* `map` - Overview on map, i.e., status (known, visible, etc.), terrain types and potential extras
* `options` - Overview on additional options for the game that are active
* `rules` - Overview on all rules and detailed/static descriptions (tech types, unit types, etc.) that are relevant for the game
* `player` - Overview on player status (scores, etc.) and ability to take diplomatic actions (experimental stage)
* `tech` - Overview on currently active technologies as well as ability to change research goals or researching specific technologies
* `unit` - Overview on current unit status (health, moves left, etc.) and ability for moving/activity of units
