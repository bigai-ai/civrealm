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
from civrealm.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent, RandomLLMAgent, DQNAgent
import civrealm
import gymnasium


def main():
    port = 6300
    epoch_num = 4
    for i in range(epoch_num):
        run(port+i)
        import time
        time.sleep(1)


def run(port):
    env = gymnasium.make('civrealm/FreecivBase-v0')
    agent = RandomAgent()

    observations, info = env.reset(client_port=port)
    done = False
    step = 0

    while not done:
        try:
            action = agent.act(observations, info)
            observations, reward, terminated, truncated, info = env.step(
                action)
            print(
                f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                f'Truncated: {truncated}, action: {action}')
            step += 1
            done = terminated or truncated
        except Exception as e:
            fc_logger.warning(repr(e))
            break
    env.close()

    '''
    players, tags, turns, evaluations = env.evaluate_game()
    '''
    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)


if __name__ == '__main__':
    main()
