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
import pandas as pd
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent
from civrealm.configs import fc_args
import civrealm
import gymnasium


def main():
    env = gymnasium.make('freeciv/FreecivMinitask-v0')
    agent = ControllerAgent()

    observations, info = env.reset()
    done = False
    step = 0
    while not done:
        try:
            action = agent.act(observations, info)
            observations, reward, terminated, truncated, info = env.step(action)
            print(
                f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}, Action: {action}')
            print(f'\tMinitask Info: {info["minitask"]}')
            step += 1
            done = terminated or truncated
        except Exception as e:
            fc_logger.error(repr(e))
            print(e)
            raise e
    env.close()
    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)


if __name__ == '__main__':
    main()
