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


import gymnasium
import ray
import os
# Disable log deduplication of Ray. This ensures the print messages from all actors can be shown.
os.environ['RAY_DEDUP_LOGS'] = '0'
from civrealm.freeciv.utils.freeciv_logging import fc_logger

from civrealm.freeciv.utils.freeciv_logging import fc_logger

@ray.remote
class FreecivParallelEnv():
    def __init__(self, env_id, *args, **kwargs):
        # Note that when the env_id is FreecivTensor-v0, it will call its reset() inside the make process. Therefore, the FreecivTensor-v0 has already connected to the server after initializing the environment.
        self.env = gymnasium.make(env_id, *args, **kwargs)
        # print(f'FreecivParallelEnv: {self.env.get_username()}')
        # self.port = port

    def step(self, action):
        # import time
        # time.sleep(3)
        # action = None
        return self.env.step(action)


    def reset(self, **kwargs):
        # print('FreecivParallelEnv.reset...')
        try:
            return self.env.reset(**kwargs)
        except Exception as e:
            # print(repr(e))
            fc_logger.error(f'FreecivParallelEnv: {repr(e)}')

    def close(self):
        self.env.close()

    def get_port(self):
        return self.env.unwrapped.get_port()

    def get_username(self):
        return self.env.unwrapped.get_username()
    
    def get_playerid(self):
        return self.env.unwrapped.get_playerid()

    def getattr(self, attr):
        return getattr(self.env, attr)

    def get_final_score(self):
        return self.env.unwrapped.get_final_score()
    
    def plot_game_scores(self):
        return self.env.unwrapped.plot_game_scores()
    
    def get_game_results(self):
        return self.env.unwrapped.get_game_results()
