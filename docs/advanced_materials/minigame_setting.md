
# Setting

## 🏁 Game Status

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

## 🔥 Game Difficulty

Based on the richness of terrain resources, the comparison of unit quantities, and other information, we designed the difficulty level of the mini-game.

The enumerated values are as follows:

```python title="src/civrealm/envs/freeciv_minitask_env.py"
@unique
class MinitaskDifficulty(ExtendedEnum):
    MD_EASY = 'easy'
    MD_NORMAL = 'normal'
    MD_HARD = 'hard'
```

## 🏆 Victory Status

In the mini-game, the player’s current victory status can be represented as: failure, success, and unknown. The unknown state signifies that the game has not yet concluded, while the determination of failure and success only occurs after the game ends.

The enumerated values are as follows:

```python title="src/civrealm/envs/freeciv_minitask_env.py"
@unique
class MinitaskPlayerStatus(ExtendedEnum):
    MPS_SUCCESS = 1
    MPS_FAIL = 0
    MPS_UNKNOWN = -1
```

## 🗺️ Supported Types

We have designed the following 14 types of mini-games:

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
        <td rowspan="9">Battle</td>
        <td>5</td>
        <td>battle_ancient_era</td>
        <td>Defeat enemy units on land tiles in ancient era.</td>
    </tr>
    <tr>
        <td>6</td>
        <td>battle_industry_era</td>
        <td>Defeat enemy units on land tiles in industry era.</td>
    </tr>
    <tr>
        <td>7</td>
        <td>battle_info_era</td>
        <td>Defeat enemy units on land tiles in infomation era.</td>
    </tr>
    <tr>
        <td>8</td>
        <td>battle_medieval</td>
        <td>Defeat enemy units on land tiles in medieval.</td>
    </tr>
    <tr>
        <td>9</td>
        <td>battle_modern_era</td>
        <td>Defeat enemy units on land tiles in modern era.</td>
    </tr>
    <tr>
        <td>10</td>
        <td>battle_attack_city</td>
        <td>Conquer an enemy city.</td>
    </tr>
    <tr>
        <td>11</td>
        <td>battle_defend_city</td>
        <td>Against enemy invasion for a certain number of turns.</td>
    </tr>
    <tr>
        <td>12</td>
        <td>battle_naval</td>
        <td>Defeat enemy fleet on the ocean (with Middle Times frigates).</td>
    </tr>
    <tr>
        <td>13</td>
        <td>battle_naval_modern</td>
        <td>Defeat enemy fleet on the ocean (with several classes of modern ships).</td>
    </tr>
    <tr>
        <td>Diplomacy</td>
        <td>14</td>
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
