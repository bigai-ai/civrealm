# Mini-Game

Due to the multifaceted aspects of a full game, including economic expansion, military development, diplomatic negotiations, cultural construction, and technological research, we have devised mini games to address each component individually. Each mini-game is designed with specific objectives, varying difficulty levels, step-based rewards, and an overall game score. The designed details could be found in the [paper](https://openreview.net/forum?id=UBVNwD3hPN).

By the end of this tutorial, you will be able to

* Understand the basic setting of mini-game
* Initialize mini-game by using API for random initialization or manual specification
* Create a new mini-game by several methods

## 🎮 Setting
### 🏁 Game Status

To describe whether a mini-game is over, the game-ending conditions include:

* The game score being greater than or equal to the goal score
* Reaching the maximum number of rounds set for the game

The enumerated values are as follows:
```python title="src/civrealm/envs/freeciv_minitask_env.py"
@unique
class MinitaskGameStatus(ExtendedEnum):
    MGS_END_GAME = 1
    MGS_IN_GAME = 0
```

### 🔥 Game Difficulty
Based on the richness of terrain resources, the comparison of unit quantities, and other information, we designed the difficulty level of the mini-game.

The enumerated values are as follows:
```python title="src/civrealm/envs/freeciv_minitask_env.py"
@unique
class MinitaskDifficulty(ExtendedEnum):
    MD_EASY = 'easy'
    MD_NORMAL = 'normal'
    MD_HARD = 'hard'
```

### 🏆 Victory Status

In the mini-game, the player’s current victory status can be represented as: failure, success, and unknown. The unknown state signifies that the game has not yet concluded, while the determination of failure and success only occurs after the game ends.

The enumerated values are as follows:
```python title="src/civrealm/envs/freeciv_minitask_env.py"
@unique
class MinitaskPlayerStatus(ExtendedEnum):
    MPS_SUCCESS = 1
    MPS_FAIL = 0
    MPS_UNKNOWN = -1
```
### 🗺️ Supported Types

We have designed the following 10 types of mini-games:

<table>
    <tr> 
        <td bgcolor="Lavender"><b>Category</b></td>
        <td bgcolor="Lavender"><b>ID</b></td>
        <td bgcolor="Lavender"><b>Name</b></td>
        <td bgcolor="Lavender"><b>Introduction</b></td>
    </tr>
    <tr> 
        <td rowspan="4">Development</td>
        <td>1</td>
        <td>development_build_city</td>
        <td>Move settler to suitable areas for building a city.</td>
    </tr>
    <tr> 
        <td>2</td>
        <td>development_build_infra</td>
        <td>Command workers to build infrastructures for improving cities.</td>
    </tr>
    <tr> 
        <td>3</td>
        <td>development_citytile_wonder</td>
        <td>Arrange work tiles to speed up producing a world wonder.</td>
    </tr>
    <tr> 
        <td>4</td>
        <td>development_transport</td>
        <td>Transport settlers by ships to another continent and build cities.</td>
    </tr>
    <tr> 
        <td rowspan="5">Battle</td>
        <td>5</td>
        <td>battle_[ancient_era,industry_era,<br>info_era,medieval,modern_era]</td>
        <td>Defeat enemy units on land tiles (units from various ages).</td>
    </tr>
    <tr> 
        <td>6</td>
        <td>battle_attack_city</td>
        <td>Conquer an enemy city.</td>
    </tr>
    <tr> 
        <td>7</td>
        <td>battle_defend_city</td>
        <td>Against enemy invasion for a certain number of turns.</td>
    </tr>
    <tr> 
        <td>8</td>
        <td>battle_naval</td>
        <td>Defeat enemy fleet on the ocean (with Middle Times frigates).</td>
    </tr>
    <tr> 
        <td>9</td>
        <td>battle_naval_modern</td>
        <td>Defeat enemy fleet on the ocean (with several classes of modern ships).</td>
    </tr>
    <tr> 
        <td>Diplomacy</td>
        <td>10</td>
        <td>diplomacy_trade_tech</td>
        <td>Trade technologies with another civilization.</td>
    </tr>

</table>

The enumerated values are as follows:
```python title="src/civrealm/envs/freeciv_minitask_env.py"
@unique
class MinitaskType(ExtendedEnum):
    MT_DEVELOPMENT_BUILD_CITY = "development_build_city"
    MT_DEVELOPMENT_CITYTILE_WONDER = "development_citytile_wonder"
    MT_DEVELOPMENT_BUILD_INFRA = "development_build_infra"
    MT_DEVELOPMENT_TRANSPORT = "development_transport"
    MT_BATTLE_ANCIENT = "battle_ancient_era"
    MT_BATTLE_INDUSTRY = "battle_industry_era"
    MT_BATTLE_INFO = "battle_info_era"
    MT_BATTLE_MEDIEVAL = "battle_medieval"
    MT_BATTLE_MODERN = "battle_modern_era"
    MT_BATTLE_NAVAL_MODERN = "battle_naval_modern"
    MT_BATTLE_NAVAL = "battle_naval"
    MT_BATTLE_ATTACK_CITY = "battle_attack_city"
    MT_BATTLE_DEFEND_CITY = "battle_defend_city"
    MT_DIPLOMACY_TRADE_TECH = "diplomacy_trade_tech"
```


## Prepare Dataset

<b>Before you start the mini-game</b>, you need to load the mini-game designed archives into the server’s laoding archive path.

The steps are as follows:

<b>Step 1: </b> find your used version on the releases page, and download the data files for the mini-game to your local path such as `/tmp/minigame/`

<b>Step 2: </b> copy the data files, and extract them into the corresponding docker savegame path. If the docker image is `freeciv-web`, and the tomcat version is `10`, then execute the following commands:
```bash
#!/bin/bash
image="freeciv-web"
tomcat_version="tomcat10"
local_path="/tmp/minigame/"

mkdir $local_path
cd $local_path
docker exec -it $image rm -r /var/lib/$tomcat_version/webapps/data/savegames/minitask/
docker exec -it $image mkdir -p /var/lib/$tomcat_version/webapps/data/savegames/minitask/
for minitask_zip in `ls`
do
    docker cp $minitask_zip $image:/var/lib/$tomcat_version/webapps/data/savegames/minitask/
    docker exec -it $image unzip -o /var/lib/$tomcat_version/webapps/data/savegames/minitask/$minitask_zip -d /var/lib/$tomcat_version/webapps/data/savegames/minitask/
    docker exec -it $image rm /var/lib/$tomcat_version/webapps/data/savegames/minitask/$minitask_zip
done
```

## Initialize Random Mini-Game

`freeciv/FreecivMinitask-v0` is the environment of mini-game. When the mini game is launched, its internal design will randomly select a game of any type and any difficulty.

```python
from civrealm.agents import ControllerAgent
import gymnasium

env = gymnasium.make('freeciv/FreecivMinitask-v0')
agent = ControllerAgent()
observations, info = env.reset()
```

## Choose Specific Mini-Game

Inside `reset` method of environment, you can use the parameter `minitask_pattern` to choose specific mini-game.

`type`: the type of mini-game, see the available options MinitaskType

`level`: the difficulty of mini-game, see the available options MinitaskDifficulty

`id`: the id of mini-game, the available range is 0 to MAX_ID

For example, if you want to set the type as `development_build_city` and the difficulty as `easy`, then the code is as follows:
```python
from civrealm.agents import ControllerAgent
import gymnasium

env = gymnasium.make("freeciv/FreecivMinitask-v0")
observations, info = env.reset(minitask_pattern={
    "type": "development_build_city", 
    "level": "easy"})
```

## Create a new Mini-Game

### Modify the sav file directly

### Use gtk

### Using the freeciv-sav api
