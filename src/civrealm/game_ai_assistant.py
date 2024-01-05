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

import time
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.envs.freeciv_wrapper import LLMWrapper
from civrealm.configs import fc_args
from civrealm.freeciv.utils.port_utils import Ports
import civrealm
import gymnasium
from civrealm.freeciv.utils.data_handler import H5pyWriter

# whether to save dataset
fc_args['openchatbox'] = 'disabled'
fc_args['debug.headless'] = True
fc_args['debug.take_screenshot'] = False
#fc_args['debug.window_size_x'] = 320
#fc_args['debug.window_size_y'] = 320
fc_args['debug.get_webpage_image'] = ['map_tab']

# whether to use ai assistant
fc_args['advisor'] = 'enabled'

def main():
    env = gymnasium.make('civrealm/FreecivMinitask-v0', client_port=Ports.get())
    writer = H5pyWriter("development_build_city")
    step = 0
    for gid in range(1):
        observations, info = env.reset(minitask_pattern={
            "type": [
                "development_build_city"]
        })
        done = False
        while not done:
            try:
                # require image >= 1.4.3
                # record the last obs, info
                old_observations, old_info = observations, info
                # get assistant action
                action = env.civ_controller.get_assistant_action()
                fc_logger.info(f"Prepare to act: {action}")
                # env step
                observations, reward, terminated, truncated, info = env.step(action)
                # insert data to writer
                if action is None:
                    action = ['game', -1, 'end_turn']
                artifical_obs = {
                    'entity_type': action[0],
                    'action_name': action[2],
                    'step_reward': reward,
                    'mini_goal': old_info['minitask']['mini_goal'],
                    'mini_score': old_info['minitask']['mini_score'],
                    'game_id': gid
                }
                writer.insert([artifical_obs, old_info, old_observations])
                print(
                    f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                    f'Truncated: {truncated}, action: {action}')
                step += 1
                done = terminated or truncated
            except Exception as e:
                fc_logger.error(repr(e))
                raise e
        game_results = env.get_game_results()
        print('game results:', game_results)
        writer.insert(game_results, key=f'game_result/{gid}')

    env.close()
    writer.close()

if __name__ == '__main__':
    main()
