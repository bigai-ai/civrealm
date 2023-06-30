# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod

import random
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


class BaseAgent(ABC):
    def __init__(self):
        self.turn = None
        self.planned_actor_ids = []

    def set_agent_seed(self,seed: int):
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

    def get_ctrl_types(self, observations):
        return observations[1].keys()

    def get_next_valid_actor(self, observations, info, desired_ctrl_type=None):
        """
        Return the first actable actor_id and its valid_action_dict that has not been planned in this turn.
        """
        if info['turn'] != self.turn:
            self.planned_actor_ids = []
            self.turn = info['turn']

        for ctrl_type in self.get_ctrl_types(observations):
            if desired_ctrl_type and desired_ctrl_type != ctrl_type:
                continue

            action_list = observations[1][ctrl_type]
            for actor_id in action_list.get_actors():
                if actor_id in self.planned_actor_ids:
                    # We have planned an action for this actor in this turn.
                    continue

                if action_list._can_actor_act(actor_id):
                    fc_logger.debug(f'Trying to operate actor_id {actor_id} by {ctrl_type}_ctrl')
                    valid_action_dict = action_list.get_actions(actor_id, valid_only=True)
                    if not valid_action_dict:
                        continue

                    fc_logger.debug(
                        f'{ctrl_type}_ctrl: Valid actor_id {actor_id} with valid actions found {valid_action_dict}')
                    self.planned_actor_ids.append(actor_id)
                    return actor_id, valid_action_dict

        return None, None
