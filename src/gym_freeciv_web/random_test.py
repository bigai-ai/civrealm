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

from gym_freeciv_web.configs import args

import gym
from gym import wrappers
import gym_freeciv_web

from freecivbot.utils.freeciv_logging import logger
from gym_freeciv_web.agents.random_agent import RandomAgent


def main():
    env = gym.make(args['gym_env'])

    # You can provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    env = wrappers.Monitor(env, directory=args['out_dir'], force=True)
    env.seed(0)

    agent = RandomAgent(env.action_space)

    episode_count = 1
    try:
        for episode_i in range(episode_count):
            logger.info(f'Starting episode {episode_i}')
            # agent.perform_episode(env)
            
            env.env.gym_agent = agent
            observation, done = env.reset()

            for _ in range(100):
                # 100 steps is about 10 turns
                env.env.env_agent.calculate_next_move()
                env.env.civ_controller.lock_control()
            env.close()
        # Close the env and write monitor result info to disk
    finally:
        env.close()


if __name__ == '__main__':
    main()
