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


import ray
import os
# Disable log deduplication of Ray. This ensures the print messages from all actors can be shown.
os.environ['RAY_DEDUP_LOGS'] = '0'


@ray.remote
class FreecivA3CEnv():
    def __init__(self, env, agent, port):
        self.env = env
        self.port = port
        self.agent = agent

    def compute_action(self, observation, info):
        return self.agent.act(observation, info)

    def step(self, action):
        # import time
        # time.sleep(3)
        return self.env.step(action)

        observation, reward, terminated, truncated, info = self.env.step(action)
        return self.env.civ_controller.get_turn(), 0, False, truncated, self.env.civ_controller.get_turn()

    def reset(self):
        return self.env.reset()

        observation, info = self.env.reset()
        return self.env.civ_controller.get_turn(), self.env.civ_controller.get_turn()

    def close(self):
        self.env.close()
