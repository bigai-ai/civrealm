# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import gym

from freecivbot.utils.freeciv_logging import logger
import gym_freeciv_web
from gym_freeciv_web.configs import args
from gym_freeciv_web.agents.random_agent import RandomAgent


def main():
    env = gym.make(args['gym_env'])
    env.seed(0)

    agent = RandomAgent()

    episode_count = 1
    try:
        for episode_i in range(episode_count):
            logger.info(f'Starting episode {episode_i}')

            observation, info = env.reset()

            for _ in range(100):
                obs, reward, done, info = env.step(agent._last_action)
                action = agent.act(obs, reward, done)
                if action == None:
                    env.end_turn()
                else:
                    agent.take_action(action)
                env.civ_controller.lock_control()
            env.close()
    finally:
        env.close()


if __name__ == '__main__':
    main()
