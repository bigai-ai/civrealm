## Observations
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

### Observations of Map

<table>
    <tr>
        <td bgcolor="Lavender"><b>Fields</b></td>
        <td bgcolor="Lavender"><b>Attributes</b></td>
        <td bgcolor="Lavender"><b>Value domains</b></td>
        <td bgcolor="Lavender"><b>Descriptions</b></td>
    </tr>
    <tr>
        <td rowspan="5" style="vertical-align : middle;">Basic map</td>
        <td>Status</td>
        <td>[0, 2]</td>
        <td rowspan="3" style="vertical-align : middle;">Size: M * N</td>
    </tr>
    <tr>
        <td>Type of terrain</td>
        <td>[0, 13]</td>
    </tr>
    <tr>
        <td>Owner of tiles</td>
        <td>[0, 255]</td>
    </tr>
    <tr>
        <td>Infrastructures</td>
        <td rowspan="2" style="vertical-align : middle;">0 or 1</td>
        <td>34 layers of size M * N</td>
    </tr>
    <tr>
        <td>Output</td>
        <td>6 layers of size M * N for 6 output types</td>
    </tr>
    <tr>
        <td rowspan="3" style="vertical-align : middle;">Units and city on each tile</td>
        <td>Unit owner</td>
        <td rowspan="3" style="vertical-align : middle;">[0, 255]</td>
        <td rowspan="2" style="vertical-align : middle;">Size: M * N</td>
    </tr>
    <tr>
        <td>City owner</td>
    </tr>
    <tr>
        <td>Unit distribution</td>
        <td>52 layers of size M * N for 52 unit types</td>
    </tr>
</table>

### Observations of Unit

<table>
    <tr>
        <td bgcolor="Lavender"><b>Fields</b></td>
        <td bgcolor="Lavender"><b>Attributes</b></td>
        <td bgcolor="Lavender"><b>Value domains</b></td>
        <td bgcolor="Lavender"><b>Descriptions</b></td>
    </tr>
    <tr>
        <td rowspan="12" style="vertical-align : middle;">Common unit field</td>
        <td>X</td>
        <td>[0, M]</td>
        <td>X-coordinate</td>
    </tr>
    <tr>
        <td>Y</td>
        <td>[0, N]</td>
        <td>Y-coordinate</td>
    </tr>
    <tr>
        <td>Owner</td>
        <td>[0, 255]</td>
        <td>Player the unit belongs to</td>
    </tr>
    <tr>
        <td >HP</td>
        <td rowspan="2" style="vertical-align : middle;">[0, 65535]</td>
        <td>Health point of the unit</td>
    </tr>
    <tr>
        <td>Produce cost</td>
        <td>Cost needed to produce this type of unit</td>
    </tr>
    <tr>
        <td >Veteran</td>
        <td rowspan="2" style="vertical-align : middle;">0 or 1</td>
        <td>Whether the unit is veteran</td>
    </tr>
    <tr>
        <td>Can transport</td>
        <td>Whether the unit can transport other units</td>
    </tr>
    <tr>
        <td>Unit type</td>
        <td rowspan="2" style="vertical-align : middle;">[0, 51]</td>
        <td>One of 52 unit types</td>
    </tr>
    <tr>
        <td>Obsoleted by</td>
        <td>The unit type this unit can upgrade to</td>
    </tr>
    <tr>
        <td >Attack strength</td>
        <td rowspan="3" style="vertical-align : middle;">[0, 65535]</td>
        <td rowspan="2" style="vertical-align : middle;">Affect the attack success rate</td>
    </tr>
    <tr>
        <td>Defense strength</td>
    </tr>
    <tr>
        <td>Firepower</td>
        <td>The damage of a successful attack</td>
    </tr>
    <tr>
        <td rowspan="6" style="vertical-align : middle;">My unit field</td>
        <td>Unit ID</td>
        <td rowspan="6" style="vertical-align : middle;">[0, 32767]</td>
        <td>The ID of the unit</td>
    </tr>
    <tr>
        <td>Moves left</td>
        <td >Actions the unit can take in this turn</td>
    </tr>
    <tr>
        <td>Home city</td>
        <td>City that supports this unit</td>
    </tr>
    <tr>
        <td>Upkeep shield</td>
        <td rowspan="3" style="vertical-align : middle;">Resources needed to support this unit</td>
    </tr>
    <tr>
        <td>Upkeep gold</td>
    </tr>
    <tr>
        <td>Upkeep food</td>
    </tr>
</table>

### Observations of Diplomacy

<table>
    <tr>
        <td bgcolor="Lavender"><b>General</b></td>
        <td bgcolor="Lavender"><b>Attributes</b></td>
        <td bgcolor="Lavender"><b>Values</b></td>
        <td bgcolor="Lavender"><b>Descriptions</b></td>
    </tr>
    <tr>
        <td rowspan="9" style="vertical-align: middle;">Common player field</td>
        <td>Player ID</td>
        <td rowspan="2" style="vertical-align: middle;">[0, 255]</td>
        <td > The ID of player</td>
    </tr>
    <tr>
        <td>Team</td>
        <td > The ID of team</td>
    </tr>
    <tr>
        <td>Name</td>
        <td>text</td>
        <td>The name of the player</td>
    </tr>
    <tr>
        <td>Is alive</td>
        <td>0 or 1</td>
        <td > Whether the player is alive or not</td>
    </tr>
    <tr>
        <td>Score</td>
        <td rowspan="2" style="vertical-align: middle;">[0, 65535]</td>
        <td>The score of the player</td>
    </tr>
    <tr>
        <td>Turns alive</td>
        <td>How many turns the player has lived for</td>
    </tr>
    <tr>
        <td>Nation</td>
        <td>[0, 559]</td>
        <td>The nation of the player</td>
    </tr>
    <tr>
        <td>Embassy text</td>
        <td rowspan="2" style="vertical-align: middle;">text</td>
        <td>Describe if there are embassies between players</td>
    </tr>
    <tr>
        <td>Love</td>
        <td>Describe players’ attitudes to others</td>
    </tr>
    <tr>
        <td rowspan="2" style="vertical-align: middle;">My player field</td>
        <td>Mood</td>
        <td>0 or 1</td>
        <td>Peaceful or Combat</td>
    </tr>
    <tr>
        <td>Diplomacy state</td>
        <td>[0, 6]</td>
        <td>A categorical vector of my diplomacy states with other players: armistice, war, ceasefire, etc.</td>
    </tr>
</table>


### Observations of Government

<table>
    <tr>
        <td bgcolor="Lavender"><b>General</b></td>
        <td bgcolor="Lavender"><b>Attributes</b></td>
        <td bgcolor="Lavender"><b>Values</b></td>
        <td bgcolor="Lavender"><b>Descriptions</b></td>
    </tr>
    <tr>
        <td rowspan="2" style="vertical-align: middle;">Common government fields</td>
        <td>Government ID</td>
        <td>[0, 6]</td>
        <td>The ID of the government</td>
    </tr>
    <tr>
        <td>Government name</td>
        <td>text</td>
        <td>The name of the government</td>
    </tr>
    <tr>
        <td rowspan="6" style="vertical-align: middle;">My government fields</td>
        <td>Goal government</td>
        <td>[0, 6]</td>
        <td>The goal of revolution</td>
    </tr>
    <tr>
        <td>Gold</td>
        <td rowspan="2" style="vertical-align: middle;">[0, 65535]</td>
        <td>Gold in treasury</td>
    </tr>
    <tr>
        <td>Revolution finishes</td>
        <td>Number of turns for current revolution to complete</td>
    </tr>
    <tr>
        <td>Science</td>
        <td rowspan="3" style="vertical-align: middle;">[0, 100]</td>
        <td rowspan="3" style="vertical-align: middle;">Government investment for each aspect. Sum to 100.</td>
    </tr>
    <tr>
        <td>Tax</td>
    </tr>
    <tr>
        <td>Luxury</td>
    </tr>
</table>

### Observations of City

<table>
    <tr>
        <td bgcolor="Lavender"><b>General</b></td>
        <td bgcolor="Lavender"><b>Attributes</b></td>
        <td bgcolor="Lavender"><b>Value domains</b></td>
        <td bgcolor="Lavender"><b>Descriptions</b></td>
    </tr>
    <tr>
        <td rowspan="5" style="vertical-align: middle;">Common city field</td>
        <td>City name</td>
        <td>text</td>
        <td>The name of city</td>
    </tr>
    <tr>
        <td>X</td>
        <td>[0, M]</td>
        <td>X-Coordinate</td>
    </tr>
    <tr>
        <td>Y</td>
        <td>[0, N]</td>
        <td>Y-Coordinate</td>
    </tr>
    <tr>
        <td>Owner</td>
        <td rowspan="2" style="vertical-align: middle;">[0, 255]</td>
        <td >Player this city belongs to</td>
    </tr>
    <tr>
        <td>Size</td>
        <td >The size of this city</td>
    </tr>
    <tr>
        <td rowspan="32" style="vertical-align: middle;">My city field</td>
        <td>City ID</td>
        <td rowspan="16" style="vertical-align: middle;">[0, 32767]</td>
        <td>The ID of the city</td>
    </tr>
    <tr>
        <td>Food stock</td>
        <td>The food stock of the city</td>
    </tr>
    <tr>
        <td>Shield stock</td>
        <td>The shield stock of the city</td>
    </tr>
    <tr>
        <td>Granary size</td>
        <td>The granary size of the city</td>
    </tr>
    <tr>
        <td>Buy cost</td>
        <td>Cost to buy the undergoing production</td>
    </tr>
        <td>Turns to complete</td>
        <td>Number of turns to finish the current production</td>
    </tr>
    <tr>
        <td>Luxury</td>
        <td rowspan="7" style="vertical-align: middle;">Resource outputs in each turn</td>
    </tr>
    <tr>
        <td>Science</td>
    </tr>
    <tr>
        <td>Food</td>
    </tr>
    <tr>
        <td>Gold</td>
    </tr>
    <tr>
        <td>Shield</td>
    </tr>
    <tr>
        <td>Trade</td>
    </tr>
    <tr>
        <td>Bulbs</td>
    </tr>
    <tr>
        <td>City waste</td>
        <td>The waste of the city</td>
    </tr>
    <tr>
        <td>City corruption</td>
        <td>The corruption of the city</td>
    </tr>
    <tr>
        <td>City pollution</td>
        <td>The pollution of the city</td>
    </tr>
    <tr>
        <td>Growth in</td>
        <td>text</td>
        <td>Number of turns for city population to grow</td>
    </tr>
    <tr>
        <td>State</td>
        <td>[0, 2]</td>
        <td>City state: disorder, peace, etc.</td>
    </tr>
    <tr>
        <td>Production kind</td>
        <td>[0, 1]</td>
        <td>Unit or building</td>
    </tr>
    <tr>
        <td>Production value</td>
        <td>[0, 67]</td>
        <td>Unit or building type being produced</td>
    </tr>
    <tr>
        <td>People angry</td>
        <td rowspan="4" style="vertical-align: middle;">[0, 127]</td>
        <td rowspan="4" style="vertical-align: middle;">Number of people of each mood</td>
    </tr>
    <tr>
        <td>People unhappy</td>
    </tr>
    <tr>
        <td>People content</td>
    </tr>
    <tr>
        <td>People happy</td>
    </tr>
    <tr>
        <td>Surplus food</td>
        <td rowspan="4" style="vertical-align: middle;">[-32768, 32767]</td>
        <td rowspan="4" style="vertical-align: middle;">The surplus of the resource</td>
    </tr>
    <tr>
        <td>Surplus gold</td>
    </tr>
    <tr>
        <td>Surplus shield</td>
    </tr>
    <tr>
        <td>Surplus trade</td>
    </tr>
    <tr>
        <td>Can build unit</td>
        <td rowspan="3" style="vertical-align: middle;">0 or 1</td>
        <td rowspan="3" style="vertical-align: middle;">Binary vectors corresponding to units or buildings</td>
    </tr>
    <tr>
        <td>Can build building</td>
    </tr>
    <tr>
        <td>Having Buildings</td>
    </tr>
    <tr>
        <td>Last completion turn</td>
        <td>[0,32767]</td>
        <td>Turn Number when the city completed the last production</td>
    </tr>
</table>

### Observations of Technology

<table>
    <tr>
        <td bgcolor="Lavender"><b>General</b></td>
        <td bgcolor="Lavender"><b>Attributes</b></td>
        <td bgcolor="Lavender"><b>Values</b></td>
        <td bgcolor="Lavender"><b>Descriptions</b></td>
    </tr>
    <tr>
        <td rowspan="3" style="vertical-align: middle;">Common technology fields</td>
        <td>Research name</td>
        <td>text</td>
        <td>The name of research</td>
    </tr>
    <tr>
        <td>Researching</td>
        <td>[0, 87]</td>
        <td>The technology being researched</td>
    </tr>
    <tr>
        <td>Tech of each type</td>
        <td>0 or 1</td>
        <td>If each technology has been researched</td>
    </tr>
    <tr>
        <td rowspan="6" style="vertical-align: middle;">My technology fields</td>
        <td>Bulbs researched</td>
        <td rowspan="4" style="vertical-align: middle;">[0, 65535]</td>
        <td>Accumulated technology bulbs</td>
    </tr>
    <tr>
        <td>Tech upkeep</td>
        <td>Cost to keep current technologies</td>
    </tr>
    <tr>
        <td>Science cost</td>
        <td>-</td>
    </tr>
    <tr>
        <td>Researching cost</td>
        <td>-</td>
    </tr>
    <tr>
        <td>Tech goal</td>
        <td rowspan="2" style="vertical-align: middle;">[0, 87]</td>
        <td>The long-term research goal</td>
    </tr>
    <tr>
        <td>Techs researched</td>
        <td>Last researched technology</td>
    </tr>
</table>

