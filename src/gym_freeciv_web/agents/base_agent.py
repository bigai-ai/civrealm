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

from freecivbot.utils.freeciv_logging import logger

class BaseAgent(ABC):
    def __init__(self):
        pass

    def get_ctrl_types(self, observations):
        return observations[1].keys()

    def get_next_action_dict(self, observations, ctrl_type):
        action_list = observations[1][ctrl_type]
        for actor_id in action_list.get_actors():
            if action_list._can_actor_act(actor_id):
                logger.debug(f'Trying to operate actor_id {actor_id} by {ctrl_type} controller')
                valid_action_dict = action_list.get_actions(actor_id, valid_only=True)
                return actor_id, valid_action_dict
        return None, None

    @abstractmethod
    def act(self, observation):
        return None
