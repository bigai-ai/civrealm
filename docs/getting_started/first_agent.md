## Write your first agent

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
