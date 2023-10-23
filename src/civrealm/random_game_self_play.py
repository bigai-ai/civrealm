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


from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.envs.freeciv_wrapper import LLMWrapper
from civrealm.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent, RandomLLMAgent
from civrealm.envs.freeciv_parallel_env import FreecivParallelEnv
from civrealm.configs import fc_args
import civrealm
import gymnasium
import ray
import os
# Disable log deduplication of Ray. This ensures the print messages from all actors can be shown.
os.environ['RAY_DEDUP_LOGS'] = '0'
from civrealm.freeciv.utils.freeciv_logging import ray_logger_setup
from civrealm.freeciv.utils.port_utils import Ports

def main():
    if fc_args['minp'] <= 1:
        assert False, 'self_play_number should be larger than 1'
    ray.init(
            local_mode=False,
            runtime_env={"worker_process_setup_hook": ray_logger_setup},
        )
    logger = ray_logger_setup()
    
    client_port = Ports.get()
    envs = []
    envs.append(FreecivParallelEnv.remote('freeciv/FreecivBase-v0'))
    for i in range(1, fc_args['minp']):
        envs.append(FreecivParallelEnv.remote('freeciv/FreecivBase-v0', username=f"{fc_args['username']}{i}"))
    
    agent = ControllerAgent()
    # env = LLMWrapper(env)
    # agent = RandomLLMAgent()

    observation_list = [None]*fc_args['minp']
    info_list = [None]*fc_args['minp']
    # reward_list = [0]*fc_args['minp']
    # terminated_list = [False]*fc_args['minp']
    # truncated_list = [False]*fc_args['minp']
    # done_list = [False]*fc_args['minp']
    step_list = [0]*fc_args['minp']
    # Whether it is the first step after reset()
    first_step = [True]*fc_args['minp']

    result_ids = []
    id_env_map = {}
    # Perform the reset step
    for i in range(fc_args['minp']):
        # Both perform reset() to login. But the results (observations and infos) of reset() are returned sequentially due to turn-based game.
        id = envs[i].reset.remote(client_port=client_port, minitask_pattern=None)
        result_ids.append(id)
        id_env_map[id] = i

    done = False
    while True:
        unready = result_ids.copy()
        unfinished = True
        while unfinished:
            # The order of players is uncertain after initialization. So we use wait to get the currently returned result.
            ready, unready = ray.wait(unready, num_returns=1)
            # Get the env id corresponds to the given result id
            env_id = id_env_map[ready[0]]
            del id_env_map[ready[0]]
            username = ray.get(envs[env_id].get_username.remote())
            result = ray.get(result_ids[env_id])
            # Get observation, info one by one
            
            if first_step[env_id]:
                first_step[env_id] = False
                # The reset() only return observation and info
                observation_list[env_id] = result[0]
                info_list[env_id] = result[1]
            else:
                observation_list[env_id], reward, terminated, truncated, info_list[env_id] = result[0], result[1], result[2], result[3], result[4]
                print(
                    f'Player: {username}, Step: {step_list[env_id]}, Turn: {info_list[env_id]["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                    f'Truncated: {truncated}, action: {None}')
                step_list[env_id] += 1
                done = terminated or truncated
            
            # Loop until the player ends turn
            while not done:
                try:
                    action = agent.act(observation_list[env_id], info_list[env_id])
                    # If action is None, will end the current turn.
                    if action == None:
                        # When end turn, the step() will not return until other players finish and receive start phase packet. So we store the result_id for later use.
                        result_ids[env_id] = envs[env_id].step.remote(action)
                        # Record the env_id corresponding to the result
                        id_env_map[result_ids[env_id]] = env_id
                        print(f'{username} end turn')
                        break
                    else:
                        result = ray.get(envs[env_id].step.remote(action))
                        observation_list[env_id], reward, terminated, truncated, info_list[env_id] = result[0], result[1], result[2], result[3], result[4]
                        print(
                            f'Player: {username}, Step: {step_list[env_id]}, Turn: {info_list[env_id]["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                            f'Truncated: {truncated}, action: {action}')
                        step_list[env_id] += 1
                        done = terminated or truncated
                except Exception as e:
                    fc_logger.error(repr(e))
                    raise e
            
            if done:
                ray.get(envs[env_id].close.remote())

            if not unready:
                unfinished = False

        if done:
            break
    
    for env_id in range(fc_args['minp']):
        '''
        players, tags, turns, evaluations = env.evaluate_game()
        '''
        ray.get(envs[env_id].plot_game_scores.remote())
        game_results = ray.get(envs[env_id].get_game_results.remote())
        print('game results:', game_results)


if __name__ == '__main__':
    main()
