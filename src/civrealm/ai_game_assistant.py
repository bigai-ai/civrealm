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
import civrealm
import gymnasium

def main():
    env = gymnasium.make('civrealm/FreecivBase-v0')
    env = LLMWrapper(env)

    observations, info = env.reset(client_port=fc_args['client_port'])
    done = False
    step = 0

    while not done:
        try:
            # send request and wait for response
            my_player_id = env.civ_controller.my_player_id
            # require image >= 1.4.1
            env.civ_controller.ws_client.send_request({'pid': 261, 'playerno': my_player_id}, (262, my_player_id))
            action = env.civ_controller.get_unit_assistant
            observations, reward, terminated, truncated, info = env.step(action)
            print(
                f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                f'Truncated: {truncated}, action: {action}')
            step += 1
            done = terminated or truncated
        except Exception as e:
            fc_logger.error(repr(e))
            raise e
    env.close()

    '''
    players, tags, turns, evaluations = env.evaluate_game()
    '''
    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)


if __name__ == '__main__':
    main()
