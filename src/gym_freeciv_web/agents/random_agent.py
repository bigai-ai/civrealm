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

import time

from freecivbot.civ_controller import CivController
from gym_freeciv_web.agents.base_agent import BaseAgent
from gym_freeciv_web.configs import args


class RandomAgent(BaseAgent):
    def __init__(self, gym_env):
        super().__init__()
        self._env = gym_env
        self._last_action = None

    def calculate_next_move(self):
        obs, self._env.reward, self._env.done, _ = self._env.step(self._last_action)
        if self._env.done:
            pass
        action = self._env.gym_agent.act(obs, self._env.reward, self._env.done)
        if action == None:
            time.sleep(2)
            self._env.end_turn()
            return
        else:
            self.take_action(action)

    def reset(self):
        self._env.gym_agent.reset()

    def take_action(self, action):
        action_list = action[0]
        action_list.trigger_validated_action(action[1])

        self._last_action = action
