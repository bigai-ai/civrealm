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
from civrealm.freeciv.utils.freeciv_logging import ray_logger_setup

from civrealm.configs import fc_args
from civrealm.envs.freeciv_parallel_env import FreecivParallelEnv
from civrealm.freeciv.utils.port_utils import Ports

@ray.remote
class SelfPlayEnv():
    def __init__(self, env_id, *args, **kwargs):
        if fc_args['minp'] <= 1:
            assert False, 'self_play_number should be larger than 1'
        # ray.init(
        #     local_mode=False,
        #     runtime_env={"worker_process_setup_hook": ray_logger_setup},
        # )
        # logger = ray_logger_setup()

        self.env = []
        # Append self-play players in self.env
        self.env.append(FreecivParallelEnv.remote(env_id))
        for i in range(1, fc_args['minp']):
            self.env.append(FreecivParallelEnv.remote(env_id, username=f"{fc_args['username']}{i}"))
        
        # Store the username of the current active player
        self.username = ""
        # Store the id of the current active player
        self.env_id = None
        # The map between result_id and env index in self.env. Store the current result_id waiting for retrieval.
        self.id_env_map = {}
        # Whether it is the first step after reset()
        self.first_step = [True]*fc_args['minp']
        self.step_list = [0]*fc_args['minp']

    def reset(self, **kwargs):
        self.id_env_map.clear()
        self.first_step = [True]*fc_args['minp']
        self.step_list = [0]*fc_args['minp']
        self.client_port = Ports.get()

        result_ids = []
        for i in range(fc_args['minp']):
            # Both perform reset() to login. But the results (observations and infos) of reset() are returned sequentially due to turn-based game.
            id = self.env[i].reset.remote(client_port=self.client_port,**kwargs)
            result_ids.append(id)
            self.id_env_map[id] = i
        
        ready, unready = ray.wait(result_ids, num_returns=1)
        env_id = self.id_env_map[ready[0]]
        self.env_id = env_id
        del self.id_env_map[ready[0]]
        self.username = ray.get(self.env[env_id].get_username.remote())
        self.first_step[env_id] = False
        # We use ray.get() here to make API consistent with other envs. However, we may just return a result_id instead and use get() in non-remote process. This would save some communication resources.
        result = ray.get(result_ids[env_id])
        return result
        # observation = result[0]
        # info = result[1]
        # return observation, info


    # In self-play turn-based mode, every step will get one observation-info from a certain player.
    def step(self, action):
        # If action is None, the play will end the current turn. Need to get the observation and info from next player.
        if action == None:
            result_id = self.env[self.env_id].step.remote(action)
            print(f'{self.username} end turn. Port: {self.client_port}')
            pre_result_ids = list(self.id_env_map.keys())
            # Store result_id after obtaining pre_result_ids to ensure that the env which just ends turn will not return earlier (e.g., caused by defeated) than other envs. 
            self.id_env_map[result_id] = self.env_id
            # Get result from the next player
            ready, unready = ray.wait(pre_result_ids, num_returns=1)
            env_id = self.id_env_map[ready[0]]
            self.env_id = env_id
            del self.id_env_map[ready[0]]
            self.username = ray.get(self.env[env_id].get_username.remote())
            result = ray.get(ready[0])
            if self.first_step[env_id]:
                self.first_step[env_id] = False
                # The reset() only return observation and info
                observation = result[0]
                info = result[1]
                reward = 0
                terminated = False
                truncated = False
            else:
                observation, reward, terminated, truncated, info = result[0], result[1], result[2], result[3], result[4]
                print(
                    f'Player: {self.username}, Step: {self.step_list[env_id]}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                    f'Truncated: {truncated}, action: {None}. Port: {self.client_port}')
                self.step_list[env_id] += 1
        else:
            result = ray.get(self.env[self.env_id].step.remote(action))
            observation, reward, terminated, truncated, info = result[0], result[1], result[2], result[3], result[4]
            print(
                f'Player: {self.username}, Step: {self.step_list[self.env_id]}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                f'Truncated: {truncated}, action: {action}. Port: {self.client_port}')
            self.step_list[self.env_id] += 1

        return observation, reward, terminated, truncated, info, self.env_id, self.username


    def close(self):
        # The current player closes first because other players are in the loop.
        ray.get(self.env[self.env_id].close.remote())
        results = []
        for id in range(fc_args['minp']):
            if id != self.env_id:
                results.append(self.env[id].close.remote())
                # ray.get(self.env[id].close.remote())
        ray.get(results)

    def get_port(self):
        return ray.get(self.env[0].get_port.remote())

    def get_username(self):
        return ray.get(self.env[0].get_username.remote())

    def getattr(self, attr):
        return ray.get(self.env[0].getattr.remote(attr))

    def get_final_score(self):
        results = {}
        for i in range(fc_args['minp']):
            playerid = ray.get(self.env[i].get_playerid.remote())
            results[playerid] = ray.get(self.env[i].get_final_score.remote())
        return results
    
    def plot_game_scores(self):
        results = []
        for i in range(fc_args['minp']):
            results.append(self.env[i].plot_game_scores.remote())
        return ray.get(results)
    
    def get_game_results(self):
        results = []
        for i in range(fc_args['minp']):
            results.append(self.env[i].get_game_results.remote())
        return ray.get(results)