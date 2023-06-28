# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import warnings
# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings('ignore', message='.*The obs returned by the .* method.*')

import gymnasium
import freeciv_gym

from freeciv_gym.configs import fc_args
from freeciv_gym.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent


def main():
    env = gymnasium.make(fc_args['gym_env'])
    agent = ControllerAgent()

    observations, info = env.reset()
    done = False
    while not done:
        action = agent.act(observations, info)
        observations, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
    env.close()


if __name__ == '__main__':
    main()
