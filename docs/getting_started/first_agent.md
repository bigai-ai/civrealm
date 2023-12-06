# Write Your First Agent

## Write a simple rule-based agent

At each step, agent chooses the first valid actor who has done nothing yet in the current turn. If there is not such an actor, agent ends the current turn. Otherwise, if the chosen actor can build a city, agent generates an action "build a city" for the actor with probability 0.8; else, agent randomly chooses a valid "move" action for the actor.

```python
import random

from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.agents.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def random_action_by_name(self, valid_action_dict, name):
        # Assume input actions are valid, and return a random choice of the actions whose name contains the input name.
        action_choices = [
            key for key in valid_action_dict.keys() if name in key]
        if action_choices:
            return random.choice(action_choices)
        else:
            return None

    def act(self, observations, info):
        unit_actor, unit_action_dict = self.get_next_valid_actor(
            observations, info, 'unit')
        fc_logger.info(f'Valid actions: {unit_action_dict}')
        if not unit_actor:
            return None

        # Try to build a city
        build_action = self.random_action_by_name(unit_action_dict, 'build')
        if build_action and random.random() > 0.2:
            return 'unit', unit_actor, build_action

        # Try to move
        return 'unit', unit_actor, self.random_action_by_name(unit_action_dict, 'goto')

```
!!! note "Base Environment"

    You should use "Base Environment" to test "RandomAgent"

    ```python
    import gymnasium
    env = gymnasium.make('civrealm/FreecivBase-v0')
    ```

!!! success
    Now, if we run the script, we should see outputs:

    ```bash
    Step: 0, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 101, 'build_road')
    Step: 1, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 105, 'goto_2')
    Step: 2, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 106, 'build_road')
    Step: 3, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 107, 'build_road')
    Step: 4, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 108, 'goto_5')
    Step: 5, Turn: 2, Reward: 0, Terminated: False, Truncated: False, action: None
    Step: 6, Turn: 2, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 101, 'build_city')
    ```

## Write a random LLM agent

At each step, agent chooses the first valid actor who has done nothing yet in the current turn. If there is not such an actor, agent ends the current turn. Otherwise, agent randomly chooses a valid action for the actor.

```python
class RandomLLMAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        if fc_args["debug.randomly_generate_seeds"]:
            agentseed = os.getpid()
            self.set_agent_seed(agentseed)
        else:
            if "debug.agentseed" in fc_args:
                self.set_agent_seed(fc_args["debug.agentseed"])

    def act(self, observation, info):
        if info['turn'] != self.turn:
            self.planned_actor_ids = []
            self.turn = info['turn']

        for ctrl_type, actors_dict in info['llm_info'].items():
            for actor_id in actors_dict.keys():
                if actor_id in self.planned_actor_ids:
                    continue
                available_actions = actors_dict[actor_id]['available_actions']
                if available_actions:
                    action_name = random.choice(available_actions)
                    self.planned_actor_ids.append(actor_id)
                    return (ctrl_type, actor_id, action_name)
```
!!! note "LLM Environment"

    You should Use "LLM Environment" to test "RandomLLMAgent"  

    ```python
    import gymnasium
    from civrealm.envs.freeciv_wrapper import LLMWrapper
    env = gymnasium.make('civrealm/FreecivBase-v0')
    env = LLMWrapper(env)
    ```

!!! success
    Now, if we run the script, we should see outputs:

    ```bash
    Step: 0, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 103, 'move East')
    Step: 1, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 113, 'move West')
    Step: 2, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 114, 'move North')
    Step: 3, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 115, 'move North')
    Step: 4, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 116, 'move NorthEast')
    Step: 5, Turn: 2, Reward: 0, Terminated: False, Truncated: False, action: None
    Step: 6, Turn: 2, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 103, 'move South')
    ```
