## Actions


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


