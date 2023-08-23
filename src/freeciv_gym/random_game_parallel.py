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
from freeciv_gym.envs.freeciv_base_env import FreecivParallelBaseEnv
from freeciv_gym.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent, ParallelControllerAgent
# from freeciv_gym.configs import fc_args
import freeciv_gym
# from freeciv_gym.runners import REGISTRY as r_REGISTRY
import gymnasium
import ray
import asyncio
# from functools import partial
from ray.util.multiprocessing import Pool
from freeciv_gym.freeciv.utils.parallel_helper import CloudpickleWrapper
import warnings
# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings('ignore', message='.*The obs returned by the .* method.*')


def main():
    ray.init(local_mode=True)
    epoch_num = 2
    process_num = 1
    port = 6300
    pool = Pool()
    for i in range(epoch_num):
        # pool.apply(run, (process_num, port+i*process_num))
        run(process_num, port+i*process_num)
        import time
        time.sleep(1)

def run(process_num, port):
    print(f'Port: {port}')
    agent = ControllerAgent()
    env_list = []
    observation_list = []
    info_list = []
    done_list = [False]*process_num
    # Initialize environments
    for i in range(process_num):
        temp_port = port+i
        env = FreecivParallelBaseEnv.remote()
        env.set_client_port.remote(temp_port)
        env_list.append(env)
        # wrapped_env = CloudpickleWrapper(env)
        # wrapped_env.x.set_client_port.remote(temp_port)
        # env_list.append(wrapped_env)

    result_ids = []
    for i in range(process_num):
        result_ids.append(env_list[i].reset.remote())
        # result_ids.append(env_list[i].x.reset.remote())
        # observation_list.append(observations)
        # info_list.append(info)
    results = ray.get(result_ids)
    for i in range(process_num):
        observation_list.append(results[i][0])
        info_list.append(results[i][1])
    print(observation_list)
    # print(info_list)
    while True:
        # Start the parallel running
        result_ids = []
        index = 0
        # key: index of result_ids, value: id of env
        index_id_map = {}
        for i in range(process_num):
            if not done_list[i]:
                observations = observation_list[i]
                info = info_list[i]
                import random
                if random.random() < 0.01:
                    action = 'pass'
                else:
                    action = None
                result_ids.append(env_list[i].step.remote(action))
                # result_ids.append(env_list[i].x.step.remote(action))
                index_id_map[index] = i
                index += 1
        # print(f'index_id_map: {index_id_map}')
        # The num_returns=1 ensures ready length is 1. ray.wait will also preserve the ordering of the input list.
        ready, unready = ray.wait(result_ids, num_returns=1)
        index = 0
        while unready:
            # Get the env id corresponds to the given result index
            env_id = index_id_map[index]
            # print(f'env_id: {env_id}')
            try:
                result = ray.get(ready)
                # The result is a list (length is one) of tuple.
                observation_list[env_id] = result[0][0]
                info_list[env_id] = result[0][4]
                done_list[env_id] = result[0][3]
                # , reward, terminated, truncated, info_list[env_id] = result[0], result[1], result[2], result[3], 
            except Exception as e:
                fc_logger.warning(repr(e))
                done_list[env_id] = True
            index += 1
            ready, unready = ray.wait(unready, num_returns=1)

        # Handle the last ready result
        if ready:
            env_id = index_id_map[index]
            # print(f'env_id: {env_id}')
            try:
                result = ray.get(ready)
                observation_list[env_id] = result[0][0]
                info_list[env_id] = result[0][4]
                done_list[env_id] = result[0][3]
            except Exception as e:
                fc_logger.warning(repr(e))
                done_list[env_id] = True

        print(observation_list)
        # print(info_list)
        result_ids = []
        for i in range(process_num):
            if done_list[i]:
                result_ids.append(env_list[i].end_game.remote())

        ray.get(result_ids)

        result_ids = []
        for i in range(process_num):
            if done_list[i]:
                result_ids.append(env_list[i].close.remote())
                # env_list[i].x.end_game.remote()
                # env_list[i].x.close.remote()
        
        ray.get(result_ids)

        all_done = all(done_list)
        if all_done:
            break

    # actor = AsyncActor.remote()
    # # regular ray.get
    # ray.get([actor.get_result.remote(port+i) for i in range(5)])

# @ray.remote
# class AsyncActor:
#     # multiple invocation of this method can be running in
#     # the event loop at the same time
#     async def get_result(self, port):
#         run_process = CloudpickleWrapper(run)
#         await (run_process.x.remote(port))

# @ray.remote
# def run(port):
#     env_list = []

#     env = gymnasium.make('freeciv/FreecivBase-v0')
#     env.set_client_port(port)
#     # agent = CloudpickleWrapper(ControllerAgentParallel.remote())
#     agent = ControllerAgent()

#     observations, info = env.reset()
#     done = False
#     while not done:
#         try:
#             action = agent.act(observations, info)
#             # action = ray.get(agent.x1().act.remote(observations, info))
#             # print(action)
#             observations, reward, terminated, truncated, info = env.step(action)
#             done = terminated or truncated
#         except Exception as e:
#             fc_logger.warning(repr(e))
#             break
#     env.end_game()
#     env.close()


if __name__ == '__main__':
    main()
