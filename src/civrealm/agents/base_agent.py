# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod

import random
from civrealm.freeciv.utils.freeciv_logging import fc_logger


class BaseAgent(ABC):
    def __init__(self, batch_size=1):
        self.turn = [None]*batch_size
        self.planned_actor_ids = [[]]*batch_size

    def set_agent_seed(self, seed: int):
        """
        Parameters
        ----------
        seed: int, seed of the agent
        """
        self.agent_seed = seed
        random.seed(self.agent_seed)
        fc_logger.info(f"Agent seed set to {self.agent_seed}.")

    @abstractmethod
    def act(self, observation, info):
        return None

    def get_next_valid_actor(self, observations, info, desired_ctrl_type=None, env_id=0):
        """
        Return the first actable actor_id and its valid_action_dict that has not been planned in this turn.
        """

        # TODO: Do we need the turn variable for Agent class?
        if info['turn'] != self.turn[env_id]:
            self.planned_actor_ids[env_id] = []
            self.turn[env_id] = info['turn']

        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if desired_ctrl_type and desired_ctrl_type != ctrl_type:
                continue

            for actor_id, action_dict in available_actions[ctrl_type].items():
                if actor_id in self.planned_actor_ids[env_id]:
                    # We have planned an action for this actor in this turn.
                    continue
                fc_logger.debug(f'Trying to operate actor_id {actor_id} by {ctrl_type}_ctrl, actions: {action_dict}')

                for action_name in list(action_dict.keys()):
                    if not action_dict[action_name]:
                        del action_dict[action_name]

                self.planned_actor_ids[env_id].append(actor_id)
                return actor_id, action_dict

        return None, None
