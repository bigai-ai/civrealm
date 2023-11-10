The game setting is specified in the "default_settings.yaml" file under the civrealm folder. The details of the game setting are as follows:

### Basic settings for game play

- username: the user name used to log in the game.

- max_turns: the maximum number of turns per game. Game will end after the turn number reaches this limit.

- host: the url that hosts the game.

- client_port: the port to be connected by the client. Used in the single-thread mode. For parallel running, the client port is chosen from available ports.

- multiplayer_game: whether to start a multiplayer game or single-player game. By default: True.

- hotseat_game: whether to use the hotseat mode in single-player game. By default: False.

- wait_for_observer: whether to wait for an observer join before start the game. By default: False. If set to True, the game will not start until a user observes the game through the browser.
 
- server_timeout: we consider the server is timeout after it does not respond any messages for server_timeout seconds. In pytest, we automatically set it as 5 in conftest.py.

- wait_for_timeout: sometimes we perform an invalid action and cannot receive the response to wait_for_packs. We wait for wait_for_timeout seconds and clear the wait_for_packs to prevent the process from stucking.

- begin_turn_timeout: sometimes the server is stucked for unknown reasons and will not return begin_turn packet. We wait for begin_turn_timeout seconds before we close the environment. This configuration should be CAREFULLY set when playing with human or llm agents because they may use more than 60 seconds for each of their turn. In those cases, the server will send begin_turn packet only after they finish their turns.

- pytest: whether in pytest mode. By default: False. In pytest, we automatically set it as True in conftest.py.

- self_play: whether start the self-play mode. By default: False. If set to True, the first player first log in the game will be the host and the following players will add increasing index to their username in order to log in the same game.

- score_window: the number of episode scores maintained in the ParallelTensorEnv.

- aifill: number of AI players to be initialized when a game starts.

- maxplayers: the maximum number of players allowed to join a game.

- minp: the minimum number of players needed for starting a game.

- allowtake: decides whether can take control/observe a player. Please check the details of this setting in the Freeciv instruction. By default: HAhadOo.

- autotoggle: whether allow an AI to control a player when the previous player disconnects. By default: disabled.

- endvictory: whether end the game when some players succeed under victory conditions, option: enabled, disabled. By default: enabled.

- victories: the options for victory condition. If a certain victory condition is not set, the calculation logic for that victory condition will be skipped. Available options: SPACERACE|ALLIED|CULTURE. By default: "SPACERACE|ALLIED".

- openchatbox: whether to open chatbox in the web interface, option: enabled, disabled. By default: enabled.

- ruleset: the ruleset to be used. By default: classic.

- runner_type: the type of runner. By default: "parallel".

### Settings for parallel running

- batch_size_run: how many envs run simultaneously to sample experience.

- epoch_num: how many epochs to run. Each epoch runs batch_size_run envs.

- port_start: the port used by the first env. The other parallel envs use those ports following this port.

### Settings for debug

- record_action_and_observation: records the game state and available actions at every step. By default: False. **Warning**: generates many log files if True. 

- take_screenshot: take screenshots during playing. By default: False. *wait_for_observer* flag should be set to True if enable screenshots. Exec "update_javascript_for_clean_screenshot" command first to get cleaner screenshots. **Warning**: generates many log files if True.

- global_view_screenshot: take the screenshot of global view. By default: True.

- sleep_time_after_turn: time to wait after each turn.

- autosave: by default: True. If set to true, automatically save game in the beginning of every turn. The save will be deleted in the end of that turn unless the program finds some issues in that turn.

- interrupt_save: by default: False. If set to true, will save the game when using KeyboardInterrupt. Note that when enabling this setting, we should disable autosave. Otherwise, the game will be saved in the beginning of every turn and cannot be saved again when using KeyboardInterrupt.

- password: password used to login to the freeciv web account. By default: civrealm.
  
- load_game: the name of save data to be loaded. By default: "". 

- randomly_generate_seeds: whether to use randomly generated seeds for running games. By default: True. If set to True, the following random seeds (mapseed, gameseed, agentseed) are ignored. 

- mapseed: the seed for generating a map. The same seed leads to the same map.

- gameseed: the seed for fixing the behavior of random outputs.

- agentseed: the seed for fixing the action sequence when game/map are fixed.

- tensor_debug: whether print debug information for tensor env. By default: False.

