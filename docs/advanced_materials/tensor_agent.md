# Tensor Agent

Welcome to Civrealm Tensor Agent!
This documentation will guide you through the process of training tensor-based agents,
specifically using the Proximal Policy Optimization (PPO), in the Civrealm Environment.
We will first provide an overview of the Civrealm Tensor Env,
followed by instructions on how to use the civrealm-tensor-baseline repository
to train a PPO agent on this environment.

## 🌏 Civrealm Tensor Environment

The Civrealm Tensor Environment is a reinforcement learning environment wrapped
upon Civrealm Base Env specifically designed for training agents using tensor-based algorithms.
This environment

- offer immutable spaces for mutable observation and actions,
- provides flattened, tensorized observation and action spaces,
- restrict available actions in order to reduce meaningless actions,
- offers delta game score as a basic reward for RL agents,
- provide parallel environments with batched inputs and outputs for efficient training,

and various modular wrappers which are open to customize your own environment.

Start a tensor environment :
````python
    env = gymnasium.make("freeciv/FreecivTensor-v0", client_port=Ports.get())
    obs, info = env.reset()
````

###  Observation

The observation space is a gymnasium.Dict() consisting of 9 subspaces with keys listed below.

Observations can be immutable and mutable.

**Immutable Obs**: `map`, `player`, `rules`. 

They have fixed dimensions through the game-play. 

???- note "Immutable Observations"

    <table> <thead> <tr> <th>Immutables</th> <th>Field</th> <th>Dimension</th> </tr> </thead> <tr> <th rowspan="1">rules</th> <td>build_cost</td> <td>(120,)</td> </tr> <tr> <th rowspan="8">map</th> <td>status</td> <td>(84, 56, 3)</td> </tr> <tr> <td>terrain</td> <td>(84, 56, 14)</td> </tr> <tr> <td>extras</td> <td>(84, 56, 34)</td> </tr> <tr> <td>output</td> <td>(84, 56, 6)</td> </tr> <tr> <td>tile_owner</td> <td>(84, 56, 1)</td> </tr> <tr> <td>city_owner</td> <td>(84, 56, 1)</td> </tr> <tr> <td>unit</td> <td>(84, 56, 52)</td> </tr> <tr> <td>unit_owner</td> <td>(84, 56, 1)</td> </tr> <tr> <th rowspan="16">player</th> <td>score</td> <td>(1,)</td> </tr> <tr> <td>is_alive</td> <td>(1,)</td> </tr> <tr> <td>turns_alive</td> <td>(1,)</td> </tr> <tr> <td>government</td> <td>(6,)</td> </tr> <tr> <td>target_government</td> <td>(7,)</td> </tr> <tr> <td>tax</td> <td>(1,)</td> </tr> <tr> <td>science</td> <td>(1,)</td> </tr> <tr> <td>luxury</td> <td>(1,)</td> </tr> <tr> <td>gold</td> <td>(1,)</td> </tr> <tr> <td>culture</td> <td>(1,)</td> </tr> <tr> <td>revolution_finishes</td> <td>(1,)</td> </tr> <tr> <td>science_cost</td> <td>(1,)</td> </tr> <tr> <td>tech_upkeep</td> <td>(1,)</td> </tr> <tr> <td>techs_researched</td> <td>(1,)</td> </tr> <tr> <td>total_bulbs_prod</td> <td>(1,)</td> </tr> <tr> <td>techs</td> <td>(87,)</td> </tr> </table>

**Mutable Obs**: `unit`, `city`, `others_unit`, `others_city`, `others_player`, `dipl`.

The number of units, cities, and other mutable observations are constantly changing. 
Nevertheless, we truncate or pad mutable entities to a fixed size.

| Mutables      | Size  |
|---------------|-------|
| unit          | 128   |
| city          | 32    |
| others_unit   | 128   |
| others_city   | 64    |
| others_player | 10    |
| dipl          | 10    |


???- note "Mutable Observations for a Single Entity"

    <table><thead> <tr> <th>Mutables</th> <th>Field</th> <th>Dimension per Entity</th> </tr> </thead> <tr> <th rowspan="37">city</th> <td>owner</td> <td>(1,)</td> </tr> <tr> <td>size</td> <td>(1,)</td> </tr> <tr> <td>x</td> <td>(1,)</td> </tr> <tr> <td>y</td> <td>(1,)</td> </tr> <tr> <td>food_stock</td> <td>(1,)</td> </tr> <tr> <td>granary_size</td> <td>(1,)</td> </tr> <tr> <td>granary_turns</td> <td>(1,)</td> </tr> <tr> <td>production_value</td> <td>(120,)</td> </tr> <tr> <td>city_radius_sq</td> <td>(1,)</td> </tr> <tr> <td>buy_cost</td> <td>(1,)</td> </tr> <tr> <td>shield_stock</td> <td>(1,)</td> </tr> <tr> <td>disbanded_shields</td> <td>(1,)</td> </tr> <tr> <td>caravan_shields</td> <td>(1,)</td> </tr> <tr> <td>last_turns_shield_surplus</td> <td>(1,)</td> </tr> <tr> <td>improvements</td> <td>(68,)</td> </tr> <tr> <td>luxury</td> <td>(1,)</td> </tr> <tr> <td>science</td> <td>(1,)</td> </tr> <tr> <td>prod_food</td> <td>(1,)</td> </tr> <tr> <td>surplus_food</td> <td>(1,)</td> </tr> <tr> <td>prod_gold</td> <td>(1,)</td> </tr> <tr> <td>surplus_gold</td> <td>(1,)</td> </tr> <tr> <td>prod_shield</td> <td>(1,)</td> </tr> <tr> <td>surplus_shield</td> <td>(1,)</td> </tr> <tr> <td>prod_trade</td> <td>(1,)</td> </tr> <tr> <td>surplus_trade</td> <td>(1,)</td> </tr> <tr> <td>bulbs</td> <td>(1,)</td> </tr> <tr> <td>city_waste</td> <td>(1,)</td> </tr> <tr> <td>city_corruption</td> <td>(1,)</td> </tr> <tr> <td>city_pollution</td> <td>(1,)</td> </tr> <tr> <td>state</td> <td>(5,)</td> </tr> <tr> <td>turns_to_prod_complete</td> <td>(1,)</td> </tr> <tr> <td>prod_process</td> <td>(1,)</td> </tr> <tr> <td>ppl_angry</td> <td>(6,)</td> </tr> <tr> <td>ppl_unhappy</td> <td>(6,)</td> </tr> <tr> <td>ppl_content</td> <td>(6,)</td> </tr> <tr> <td>ppl_happy</td> <td>(6,)</td> </tr> <tr> <td>before_change_shields</td> <td>(1,)</td> </tr> <tr> <th rowspan="22">unit</th> <td>owner</td> <td>(1,)</td> </tr> <tr> <td>health</td> <td>(1,)</td> </tr> <tr> <td>veteran</td> <td>(1,)</td> </tr> <tr> <td>x</td> <td>(1,)</td> </tr> <tr> <td>y</td> <td>(1,)</td> </tr> <tr> <td>type_rule_name</td> <td>(52,)</td> </tr> <tr> <td>type_attack_strength</td> <td>(1,)</td> </tr> <tr> <td>type_defense_strength</td> <td>(1,)</td> </tr> <tr> <td>type_firepower</td> <td>(1,)</td> </tr> <tr> <td>type_build_cost</td> <td>(1,)</td> </tr> <tr> <td>type_convert_time</td> <td>(1,)</td> </tr> <tr> <td>type_obsoleted_by</td> <td>(53,)</td> </tr> <tr> <td>type_hp</td> <td>(1,)</td> </tr> <tr> <td>type_move_rate</td> <td>(1,)</td> </tr> <tr> <td>type_vision_radius_sq</td> <td>(1,)</td> </tr> <tr> <td>type_worker</td> <td>(1,)</td> </tr> <tr> <td>type_can_transport</td> <td>(1,)</td> </tr> <tr> <td>home_city</td> <td>(1,)</td> </tr> <tr> <td>moves_left</td> <td>(1,)</td> </tr> <tr> <td>upkeep_food</td> <td>(1,)</td> </tr> <tr> <td>upkeep_shield</td> <td>(1,)</td> </tr> <tr> <td>upkeep_gold</td> <td>(1,)</td> </tr> <tr> <th rowspan="9">others_city</th> <td>owner</td> <td>(1,)</td> </tr> <tr> <td>size</td> <td>(1,)</td> </tr> <tr> <td>improvements</td> <td>(68,)</td> </tr> <tr> <td>style</td> <td>(10,)</td> </tr> <tr> <td>capital</td> <td>(1,)</td> </tr> <tr> <td>occupied</td> <td>(1,)</td> </tr> <tr> <td>walls</td> <td>(1,)</td> </tr> <tr> <td>happy</td> <td>(1,)</td> </tr> <tr> <td>unhappy</td> <td>(1,)</td> </tr> <tr> <th rowspan="11">others_unit</th> <td>owner</td> <td>(1,)</td> </tr> <tr> <td>veteran</td> <td>(1,)</td> </tr> <tr> <td>x</td> <td>(1,)</td> </tr> <tr> <td>y</td> <td>(1,)</td> </tr></tr> <tr> <td>type</td> <td>(52,)</td> </tr> <tr> <td>occupied</td> <td>(1,)</td> </tr> <tr> <td>transported</td> <td>(1,)</td> </tr> <tr> <td>hp</td> <td>(1,)</td> </tr> <tr> <td>activity</td> <td>(1,)</td> </tr> <tr> <td>activity_tgt</td> <td>(1,)</td> </tr> <tr> <td>transported_by</td> <td>(1,)</td> </tr> <tr> <th rowspan="5">others_player</th> <td>score</td> <td>(1,)</td> </tr> <tr> <td>is_alive</td> <td>(2,)</td> </tr> <tr> <td>love</td> <td>(12,)</td> </tr> <tr> <td>diplomatic_state</td> <td>(8,)</td> </tr> <tr> <td>techs</td> <td>(87,)</td> </tr> <tr> <th rowspan="5">dipl</th> <td>type</td> <td>(20,)</td> </tr> <tr> <td>give_city</td> <td>(32,)</td> </tr> <tr> <td>ask_city</td> <td>(64,)</td> </tr> <tr> <td>give_gold</td> <td>(16,)</td> </tr> <tr> <td>ask_gold</td> <td>(16,)</td> </tr> </table>


### Action

In tensor environment, the complete action space is
````
spaces.Dict(
            {
                "actor_type": spaces.Discrete(len(self.actor_type_list)),
                "city_id": spaces.Discrete(self.action_config["resize"]["city"]),
                "city_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["city"].values())
                ),
                "unit_id": spaces.Discrete(self.action_config["resize"]["unit"]),
                "unit_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["unit"].values())
                ),
                "dipl_id": spaces.Discrete(self.action_config["resize"]["dipl"]),
                "dipl_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["dipl"].values())
                ),
                "gov_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["gov"].values())
                ),
                "tech_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["tech"].values())
                ),
            }
        )
````
The `actor_type` indicate which actor type this action belongs to, the value $\in [0\dots5]$ indicating `city`,`unit`,`gov`,`dipl`,`tech`,`end-turn` respectively.

For a mutable type `$mutable`, `${mutable}_id` indicates the position of the unit to take this action in the list of entities. For example, `unit_id=0` might indicate a `Settler` located at a specific tile.

`${actor_type}_action_type` is an action index which can be translated into a specific action, for example `goto_8` or `stop_negotiation`.

???+tip 

    Although the full action space is a Cartesion product of 9 subspaces, the `actor_type` will determine which category of entity should execute this action, and `${actor_type}_id` will determine which entity should execute a specific action `${actor_type}_action_type`.

    Thus it suffices for the env to only look at 3 tuples: `(actor_type, ${actor_type}_id, ${actor_type}_action_type)`, and it's legitimate to pass a 3-tuple if their values and types are compatible.

???-note "Action Space Details"

    <table> <tr> <th>Category</th> <th>Actions</th> <th>Count</th> </tr> <tr> <td rowspan="8">city</td> <td>city_work_None_</td> <td>4</td> </tr> <tr> <td>city_unwork_None_</td> <td>4</td> </tr> <tr> <td>city_work_</td> <td>20</td> </tr> <tr> <td>city_unwork_</td> <td>20</td> </tr> <tr> <td>city_buy_production</td> <td>1</td> </tr> <tr> <td>city_change_specialist_</td> <td>3</td> </tr> <tr> <td>city_sell</td> <td>35</td> </tr> <tr> <td>produce</td> <td>120</td> </tr> <tr> <td rowspan="37">unit</td> <td>transform_terrain</td> <td>1</td> </tr> <tr> <td>mine</td> <td>1</td> </tr> <tr> <td>cultivate</td> <td>1</td> </tr> <tr> <td>plant</td> <td>1</td> </tr> <tr> <td>fortress</td> <td>1</td> </tr> <tr> <td>airbase</td> <td>1</td> </tr> <tr> <td>irrigation</td> <td>1</td> </tr> <tr> <td>fallout</td> <td>1</td> </tr> <tr> <td>pollution</td> <td>1</td> </tr> <tr> <td>keep_activity</td> <td>1</td> </tr> <tr> <td>paradrop</td> <td>1</td> </tr> <tr> <td>build_city</td> <td>1</td> </tr> <tr> <td>join_city</td> <td>1</td> </tr> <tr> <td>fortify</td> <td>1</td> </tr> <tr> <td>build_road</td> <td>1</td> </tr> <tr> <td>build_railroad</td> <td>1</td> </tr> <tr> <td>pillage</td> <td>1</td> </tr> <tr> <td>set_homecity</td> <td>1</td> </tr> <tr> <td>airlift</td> <td>1</td> </tr> <tr> <td>upgrade</td> <td>1</td> </tr> <tr> <td>deboard</td> <td>1</td> </tr> <tr> <td>board</td> <td>1</td> </tr> <tr> <td>unit_unload</td> <td>1</td> </tr> <tr> <td>cancel_order</td> <td>1</td> </tr> <tr> <td>goto_</td> <td>8</td> </tr> <tr> <td>attack_</td> <td>8</td> </tr> <tr> <td>conquer_city_</td> <td>8</td> </tr> <tr> <td>spy_bribe_unit_</td> <td>8</td> </tr> <tr> <td>spy_steal_tech_</td> <td>8</td> </tr> <tr> <td>spy_sabotage_city_</td> <td>8</td> </tr> <tr> <td>hut_enter_</td> <td>8</td> </tr> <tr> <td>embark_</td> <td>8</td> </tr> <tr> <td>disembark_</td> <td>8</td> </tr> <tr> <td>trade_route_</td> <td>9</td> </tr> <tr> <td>marketplace_</td> <td>9</td> </tr> <tr> <td>embassy_stay_</td> <td>8</td> </tr> <tr> <td>investigate_spend_</td> <td>8</td> </tr> <tr> <td rowspan="24">dipl</td> <td>stop_negotiation_</td> <td>1</td> </tr> <tr> <td>accept_treaty_</td> <td>1</td> </tr> <tr> <td>cancel_treaty_</td> <td>1</td> </tr> <tr> <td>cancel_vision_</td> <td>1</td> </tr> <tr> <td>add_clause_ShareMap_</td> <td>2</td> </tr> <tr> <td>remove_clause_ShareMap_</td> <td>2</td> </tr> <tr> <td>add_clause_ShareSeaMap_</td> <td>2</td> </tr> <tr> <td>remove_clause_ShareSeaMap_</td> <td>2</td> </tr> <tr> <td>add_clause_Vision_</td> <td>2</td> </tr> <tr> <td>remove_clause_Vision_</td> <td>2</td> </tr> <tr> <td>add_clause_Embassy_</td> <td>2</td> </tr> <tr> <td>remove_clause_Embassy_</td> <td>2</td> </tr> <tr> <td>add_clause_Ceasefire_</td> <td>2</td> </tr> <tr> <td>remove_clause_Ceasefire_</td> <td>2</td> </tr> <tr> <td>add_clause_Peace_</td> <td>2</td> </tr> <tr> <td>remove_clause_Peace_</td> <td>2</td> </tr> <tr> <td>add_clause_Alliance_</td> <td>2</td> </tr> <tr> <td>remove_clause_Alliance_</td> <td>2</td> </tr> <tr> <td>trade_tech_clause_Advance_</td> <td>174</td> </tr> <tr> <td>remove_clause_Advance_</td> <td>174</td> </tr> <tr> <td>trade_gold_clause_TradeGold_</td> <td>30</td> </tr> <tr> <td>remove_clause_TradeGold_</td> <td>30</td> </tr> <tr> <td>trunc_trade_city_clause_TradeCity_</td> <td>96</td> </tr> <tr> <td>trunc_remove_clause_TradeCity_</td> <td>96</td> </tr> <tr> <td rowspan="7">gov</td> <td>change_gov_Anarchy</td> <td>1</td> </tr> <tr> <td>change_gov_Despotism</td> <td>1</td> </tr> <tr> <td>change_gov_Monarchy</td> <td>1</td> </tr> <tr> <td>change_gov_Communism</td> <td>1</td> </tr> <tr> <td>change_gov_Republic</td> <td>1</td> </tr> <tr> <td>change_gov_Democracy</td> <td>1</td> </tr> <tr> <td>set_sci_luax_tax</td> <td>66</td> </tr> <tr> <td>tech</td> <td>research</td> <td>87</td> </tr> </table>

You can copy the above HTML table and use it in your HTML file or any other HTML-supported platform.


## 🤖 Network Architecture for a Tensor Agent

![Tensor Architecture](../assets/tensor-architecture.png)

To effectively handle multi-source and variable-length inputs,
we draw inspiration from [AlphaStar](https://www.nature.com/articles/s41586-019-1724-z)
and implement a serialized hierarchical feature extraction and action selection approach,
as shown above.
This method involves generating layered actions and predicting value function outputs,
and our neural network architecture comprises three main components:
representation learning, action selection, and value estimation.

**Representation**.
At the representation level, we adopt a hierarchical structure.
In the lower layer, we extract controller features using various models like
MLP, Transformer, and CNN, depending on whether the input is a
single vector, sequence, or image-based.
These extracted features are then fed into a transformer to facilitate attention across different entities,
creating globally meaningful representations.
Additionally,
we utilize an RNN to combine the current-state features with the memory state,
enabling conditional policy decisions based on the state history.

**Action selection**.
At the action selection level, we leverage the learned representations to make decisions.
In the actor selection module,
we determine the primary action category to be executed,
including options like unit, city, government, technology, diplomacy, or termination.
Subsequently,
we employ a pointer network to select the specific action ID to be executed,
followed by the determination of the exact action to be performed.

**Value estimation**. To enable the use of an actor-critic algorithm,
we incorporate a value prediction head after the representation learning phase.
This shared representation part of the network benefits both the actor and critic,
enhancing training efficiency.

**Training**.
We use the [Proximal Policy Optimization (PPO)](https://arxiv.org/abs/1707.06347)
algorithm to train the agent.
To mitigate the on-policy sample complexity of PPO,
we harness [Ray](https://www.ray.io/) for parallelizing tensor environments,
optimizing training speed and efficiency.

## 🏃 Using civrealm-tensor-baseline Repository

The civrelam-tensor-baseline repository is a collection of code and utilities
that provide a baseline implementation for training reinforcement learning agents
using tensor-based algorithms.

It includes an implementation of the PPO algorithm,
which we will use to train our agents in the Civrealm Tensor Environment.

### 🏌️ Getting Started

To get started, follow these steps:

1. Clone the civrealm-tensor-baseline repository from GitHub and enter the directory:
   ```bash
   cd civrealm-tensor-baseline
   ```
2. Install the required dependencies by running:
   ```bash
   pip install -e .
   ```
3. Training
  PPO baseline for **fullgame**
  ```bash
  cd examples
  python train.py
  ```
  In default, this would start a runner with the config specified in `civrealm-tensor-baseline/civtensor/configs/`.
4. **OR** Train PPO baseline for **minitasks**:
  ```bash
  cd examples
  python run.py
  ```
  In default, this would start a sequence of runners each with a minitask config specified in `civrealm-tensor-baseline/examples/run_configs`.
  Either will start the training process, allowing the agent to interact with the environment,
  collect experiences, and update its policy using the PPO algorithm.
5. Monitor the training progress and evaluate the agent's performance,
using the provided metrics and visualization tools in
the civrealm-tensor-baseline repository.

    ```bash
    cd examples/results/freeciv_tensor_env/$game_type/ppo/installtest/seed-XXXXXXXXX
    # where $game_type = fullgame or minitask
    tensorboard --logdir logs/
    ```
  The output of the last command should return a url.
  ![Terminal Output](../assets/tensorboard.png)
  Visit this url with your favorite web browser, and you can view your agent performance in real time.
  ![Tensorboard Web](../assets/tensorboard-web.png)

  Congratulations!
  You have successfully set up the Civrealm Tensor Agent and
  started training a PPO agent on the Civrealm Tensor Environment,
  using the civrealm-tensor-baseline repository.

## Conclusion

In this guide, we introduced the Civrealm Tensor Environment and explained
how to use the civrealm-tensor-baseline repository to train a PPO agent on this environment.

We encourage you to explore the various features and customization options available,
and experiment with different reinforcement learning algorithms to
further enhance your agent's performance. Happy training!


