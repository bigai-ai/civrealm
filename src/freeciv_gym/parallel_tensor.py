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


from freeciv_gym.envs.freeciv_parallel_env import FreecivParallelEnv
from freeciv_gym.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent
from civtensor.models.agent import Agent

from freeciv_gym.configs import fc_args
from freeciv_gym.runners import ParallelTensorRunner

import warnings
# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings('ignore', message='.*The obs returned by the .* method.*')
import gymnasium

def main():
    if fc_args['batch_size_run'] == 1:
        warnings.warn('batch_size_run is 1. Please use random_game.py for batch_size_run = 1.')

    epoch_num = fc_args['epoch_num']
    for i in range(epoch_num):
        # agent = Agent()
        agent = None
        # env = gymnasium.make('freeciv/FreecivTensor-v0', client_port=6301)
        # runner = ParallelTensorRunner('freeciv/FreecivTensor-v0', agent, None, i)
        runner = ParallelTensorRunner('freeciv/FreecivBase-v0', agent, None, i)
        # runner.run()

        import time
        time.sleep(3)


if __name__ == '__main__':
    main()


