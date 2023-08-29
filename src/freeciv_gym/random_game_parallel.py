# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.envs.freeciv_parallel_env import FreecivParallelEnv
from freeciv_gym.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent
# from freeciv_gym.configs import fc_args
import freeciv_gym
# from freeciv_gym.runners import REGISTRY as r_REGISTRY
import gymnasium
import asyncio
# from functools import partial

import ray
from freeciv_gym.freeciv.utils.parallel_helper import CloudpickleWrapper
import warnings
# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings('ignore', message='.*The obs returned by the .* method.*')


def main():
    ray.init(local_mode=False)

    epoch_num = 2
    process_num = 10
    port = 6300
    for j in range(epoch_num):
        port_list = []
        env_list = []
        observation_list = []
        info_list = []
        # Store whether an env has terminated
        done_list = [False]*process_num
        # Store whether an env has closed its connection
        closed_list = [False]*process_num

        agent = ControllerAgent()
        # Initialize environments
        for i in range(process_num):
            temp_port = port+i
            port_list.append(temp_port)
            # env = FreecivDummyEnv.remote(temp_port)
            
            env_core = gymnasium.make('freeciv/FreecivBase-v0', client_port=temp_port)
            env = FreecivParallelEnv.remote(env_core, temp_port)
            env_list.append(env)

        result_ids = [env_list[i].reset.remote() for i in range(process_num)]
        results = ray.get(result_ids)
        for i in range(process_num):
            observation_list.append(results[i][0])
            info_list.append(results[i][1])
        print(info_list)
        
        while True:
            # Start the parallel running
            result_ids = []
            # key: index of result_ids, value: id of env
            id_env_map = {}
            for i in range(process_num):
                if not done_list[i]:
                    observations = observation_list[i]
                    info = info_list[i]
                    import random
                    if random.random() < 0.3:
                        action = 'pass'
                    else:
                        action = None
                    # if port_list[i] != 6301 and port_list[i] != 6302:
                    #     action = 'pass'
                    # else:
                        # action = agent.act(observations, info)
                    # if port_list[i] != 6301 and port_list[i] != 6302:
                    #     action = 'pass'
                    # else:
                    #     action = None
                    # action = None
                    # action = 'pass'
                    id = env_list[i].step.remote(action)
                    result_ids.append(id)
                    id_env_map[id] = i
            
            # The num_returns=1 ensures ready length is 1.
            ready, unready = ray.wait(result_ids, num_returns=1)
            while unready:
                # Get the env id corresponds to the given result id
                env_id = id_env_map[ready[0]]
                # print(f'env_id: {env_id}')
                try:
                    result = ray.get(ready[0])
                    # print(result)
                    observation_list[env_id] = result[0]
                    info_list[env_id] = result[4]
                    done_list[env_id] = result[3]
                    # , reward, terminated, truncated, info_list[env_id] = result[0], result[1], result[2], result[3], 
                except Exception as e:
                    print(str(e))
                    fc_logger.warning(repr(e))
                    done_list[env_id] = True
                ready, unready = ray.wait(unready, num_returns=1)

            # Handle the last ready result
            if ready:
                env_id = id_env_map[ready[0]]
                # print(f'env_id: {env_id}')
                try:
                    result = ray.get(ready[0])
                    # print(result)
                    observation_list[env_id] = result[0]
                    info_list[env_id] = result[4]
                    done_list[env_id] = result[3]
                except Exception as e:
                    fc_logger.warning(repr(e))
                    done_list[env_id] = True
            # print(f'done_list: {done_list}')
            print(f'observation_list: {observation_list}')
            # print(info_list)

            result_ids = []
            for i in range(process_num):
                if done_list[i] and not closed_list[i]:
                    result_ids.append(env_list[i].close.remote())
                    closed_list[i] = True
            
            ray.get(result_ids)

            all_done = all(done_list)
            if all_done:
                break
        
        import time
        time.sleep(10)

    ray.shutdown()


@ray.remote
class AsyncActor:
    async def get_env_reset_result(self, env):
        observation, info = await env.reset.remote()
        return observation, info

    async def get_env_step_result(self, env, action):
        observation, reward, terminated, truncated, info = await env.step.remote(action)
        return observation, reward, terminated, truncated, info
    
    async def get_env_close_result(self, env):
        res = await env.close.remote()
        return res

@ray.remote
def run_episode(port):
    env_list = []

    env = gymnasium.make('freeciv/FreecivBase-v0', client_port=port)
    agent = ControllerAgent()

    observations, info = env.reset()
    done = False
    while not done:
        try:
            action = agent.act(observations, info)
            if port != 6301 and port != 6302:
                action = 'pass'
            # action = ray.get(agent.x1().act.remote(observations, info))
            # print(action)
            observations, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        except Exception as e:
            fc_logger.warning(repr(e))
            break
    env.close()


if __name__ == '__main__':
    main()
