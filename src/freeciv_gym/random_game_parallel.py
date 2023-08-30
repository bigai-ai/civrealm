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
from freeciv_gym.envs.freeciv_parallel_env import FreecivParallelEnv
from freeciv_gym.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent
# from freeciv_gym.configs import fc_args
import freeciv_gym
from freeciv_gym.runners import REGISTRY as r_REGISTRY
from freeciv_gym.configs import fc_args
import gymnasium
import asyncio
# from functools import partial

import ray
from freeciv_gym.freeciv.utils.parallel_helper import CloudpickleWrapper
import warnings
# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings('ignore', message='.*The obs returned by the .* method.*')


def main():
    epoch_num = 2
    agent = ControllerAgent()
    runner = r_REGISTRY[fc_args['runner']]('freeciv/FreecivBase-v0', agent, None)
    for i in range(epoch_num):
        batchs = runner.run()
        for batch in batchs:
            print(batch)
        import time
        time.sleep(10)
    runner.close()

if __name__ == '__main__':
    main()
