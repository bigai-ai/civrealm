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

import time

import gymnasium

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args


class TurnManager(object):
    def __init__(self) -> None:
        # NOTE: The server counts the turn number from 1.
        self._turn = 0
        self._sleep_time_after_turn = fc_args['debug.sleep_time_after_turn']

        self._turn_active = False
        self._turn_player = None
        self._turn_ctrls = None
        self._turn_state = None
        self._turn_opts = None
        self._turn_history = []

    @property
    def turn(self):
        return self._turn

    @property
    def turn_active(self):
        return self._turn_active

    def set_turn(self, turn):
        self._turn = turn

    def log_begin_turn(self):
        fc_logger.info('==============================================')
        fc_logger.info(
            f'============== Begin turn: {self._turn:04d} ==============')
        fc_logger.info('==============================================')

    def begin_turn(self, pplayer, info_controls):
        self._turn += 1
        self._turn_active = True
        self._turn_ctrls = info_controls
        self._turn_player = pplayer
        self._turn_state = dict()
        self._turn_opts = dict()
        if self._turn == 1 and fc_args['wait_for_observer']:
            import time
            time.sleep(8)

    @property
    def action_space(self):
        # return gymnasium.spaces.Discrete(1)
        if self._turn_ctrls is None:
            return gymnasium.spaces.Discrete(1)

        action_space = dict()
        fc_logger.debug('Computing action space for: ')
        for ctrl_type, ctrl in self._turn_ctrls.items():
            if ctrl_type != 'tech':
                # TODO: add action spaces for all controllers
                action_space[ctrl_type] = gymnasium.spaces.Discrete(1)
                continue
            fc_logger.debug('....: %s', ctrl_type)
            action_space[ctrl_type] = ctrl.get_action_space(self._turn_player)

        return gymnasium.spaces.Dict(action_space)

    @property
    def observation_space(self):
        # return gymnasium.spaces.Discrete(1)
        if self._turn_ctrls is None:
            return gymnasium.spaces.Discrete(1)

        observation_space = dict()
        fc_logger.debug('Computing observation space for: ')
        for ctrl_type, ctrl in self._turn_ctrls.items():
            if ctrl_type not in ['map']:
                # TODO: add observation spaces for all controllers
                observation_space[ctrl_type] = gymnasium.spaces.Discrete(1)
                continue
            fc_logger.debug(f'....: {ctrl_type}')
            observation_space[ctrl_type] = ctrl.get_observation_space(
                self._turn_player)

        return gymnasium.spaces.Dict(observation_space)

    def get_observation(self):
        fc_logger.debug("Acquiring state for: ")
        for ctrl_type, ctrl in self._turn_ctrls.items():
            fc_logger.debug(f'....: {ctrl_type}')
            self._turn_state[ctrl_type] = ctrl.get_current_state(
                self._turn_player)
        return self._turn_state

    def get_available_actions(self):
        fc_logger.debug("Acquiring action for: ")
        for ctrl_type, ctrl in self._turn_ctrls.items():
            fc_logger.debug(f'....: {ctrl_type}')
            self._turn_opts[ctrl_type] = ctrl.get_current_options(
                self._turn_player)
        return self._turn_opts

    def get_reward(self):
        # FIXME: this function gets called every time the agent takes an action.
        # However, the reward should only be given at the end of the turn.
        return self._turn_state["player"]["my_score"]

    def end_turn(self):
        fc_logger.info(
            f'============== Finish turn {self._turn:04d} ==============')
        fc_logger.info(f'Sleeping for {self._sleep_time_after_turn} seconds')
        self._turn_active = False
        self._turn_ctrls = None
        self._turn_player = None
        self._turn_state = None
        self._turn_opts = None
        time.sleep(self._sleep_time_after_turn)
