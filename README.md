# Freeciv Gym

Freeciv Gym is a reinforcement learning environment for the open-source strategy game [Freeciv-web](https://github.com/freeciv/freeciv-web) based on [Freeciv](https://www.freeciv.org/). The goal is to provide a simple interface for AI researchers to train agents on Freeciv. The interface is based on the [Gymnasium](https://gymnasium.farama.org/) and [Stable Baselines](https://stable-baselines.readthedocs.io/en/master/) framework.

## About

Freeciv Gym is a fork of [freeciv-bot](https://github.com/chris1869/freeciv-bot) that was initiated several years ago and is currently being developed by [BIGAI](https://www.bigai.ai/). Going forward, Freeciv Gym will be maintained in the long term.

## Motivation

Pace of AI research is ever increasing. Recent breakthroughs by AlphaZero, AlphaGo show capabilities of current systems to master "simple" board games via reinforcement learning and Montecarlo tree search (MCTS). OpenAI and Deepmind already start tackling more complex strategy games like Dota 2 and Starcraft 2. The key challenges when switching from board games to strategy games is:

a) Knowledge of state of board is incomplete - therefore information has a cost: Due to fog of war (and unclear worklists, resources) position/status of the enemy and overall map is not fully known - hence risky investments (explorer teams) are required to gain information

b) Number of actors/actions is unlimited: Buildings, Cities, Units can be produced infinitely - hence the data model and learning method for neural networks etc. needs to be more dynamic and will face more sparce option spaces

c) More long-term consequences: In many cases, effect of actions and decisions can only be seen after several rounds, minutes of play. The longer an effect takes to materialize, mapping the actions/decisions to the very effect gets more complicated. Hence, "naive" greedy approaches to improving a single score (e.g., Flipper, Super Mario, etc.) won't cut it.  

On top of these challenges real-time strategy games due their continuous time and space add another layer of complexity (e.g., optimal formation of units, evade balistic projectiles or missiles).

In order to focus on a) b) and c) only, round-based games like Freeciv are a potential intermediate step for developing AI before jumping to real-time strategy games.

## Prerequisites

In order to test the freeciv-gym on <http://localhost>, kindly follow the docker installation instructions on <https://github.com/freeciv/freeciv-web>.

### Set the command level of client to hack to allow running all commands for debugging

Replace the `pubscript_multiplayer.serv` and `pubscript_singleplayer.serv` file in `/docker/publite2/`:

```bash
cd modified_server_code
docker cp pubscript_multiplayer.serv freeciv-web:/docker/publite2/pubscript_multiplayer.serv
docker cp pubscript_singleplayer.serv freeciv-web:/docker/publite2/pubscript_singleplayer.serv
```

Commit the current container to save the change to image.

```bash
docker commit freeciv-web freeciv/freeciv-web
# Restart the docker container so that the change takes effect
docker compose down
docker compose up -d
```


### Custom freeciv-web to save game files for debugging

Replace the `DeleteSaveGame.java` and `ListSaveGames` file in `freeciv-web/src/main/java/org/freeciv/servlet`:

```bash
cd modified_server_code
docker cp DeleteSaveGame.java freeciv-web:/docker/freeciv-web/src/main/java/org/freeciv/servlet/DeleteSaveGame.java
docker cp ListSaveGames.java freeciv-web:/docker/freeciv-web/src/main/java/org/freeciv/servlet/ListSaveGames.java
```

Enter the freeciv-web docker:

```bash
docker exec -it freeciv-web bash
```

and compile the new file:

```bash
cd /docker/freeciv-web
sh build.sh
```

After that, commit the current `freeciv-web` container into a new image and use that image to build containers from now on.

For example:

```bash
docker commit freeciv-web freeciv/freeciv-web:v2
docker compose down
# manually modify the image in docker-compose.yml to freeciv/freeciv-web:v2
docker compose up -d
```


## Installation

Installation for freeciv-gym developers

```bash
cd freeciv-gym

pip install -e .
```

To test if the installation is successful, run

```bash
test_freeciv_gym 
```

To test with multiple players, run

```bash
test_freeciv_gym --minp=2 --username=myagent
```

Then in another terminal, run

```bash
test_freeciv_gym --username=myagent1
```

<!-- ### Using a different freeciv version

As a standard, the official docker image from the [official repository](https://github.com/freeciv/freeciv-web) will be pulled. If you want to create a custom freeciv server (e.g., different rulesets, customizations, etc.) you can use `build_freeciv_server` to create a custom docker image or run a separate image in parallel. In this case, you might need to adapt src/init_server.py -->

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


## Trouble shooting

The following are some common issues that you may encounter when running the code. If you encounter any other issues, please feel free to open an issue.

* If firefox keeps loading the page, please try to add the following line to `/etc/hosts`:

    ```bash
    127.0.0.1 maxcdn.bootstrapcdn.com
    127.0.0.1 cdn.webglstats.com
    ```

* If you encounter the following error when running `sudo civ_prep_selenium.sh`, please try [this solution](https://unix.stackexchange.com/questions/724518/the-following-packages-have-unmet-dependencies-containerd-io).

    ```bash
    ...
    The following packages have unmet dependencies:
    containerd.io : Conflicts: containerd
                    Conflicts: runc
    ...
    ```

* If you see the following error when running `test_freeciv_web_gym`,  please see [this solution](https://stackoverflow.com/questions/72405117/selenium-geckodriver-profile-missing-your-firefox-profile-cannot-be-loaded). If this does not solve the problem, please check `geckodriver.log` for more information.

    ```bash
    selenium.common.exceptions.WebDriverException: Message: Process unexpectedly closed with status 1
    ```

    One potential solution on Ubuntu 22.04 is:

    ```bash
    sudo apt install firefox-geckodriver
    ln -s /snap/bin/firefox.geckodriver geckodriver
    ```
