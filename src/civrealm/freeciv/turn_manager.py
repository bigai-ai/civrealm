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
from typing import Dict

import gymnasium

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.base_action import Action, ActionList, NoActions

from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args

# import watchpoints
class TurnManager(object):
    def __init__(self, port) -> None:
        # NOTE: The server counts the turn number from 1.
        self._turn = 1
        self._last_score = 0
        self._sleep_time_after_turn = fc_args['debug.sleep_time_after_turn']

        self._turn_active = False
        # watchpoints.watch(self._turn_active)
        self._turn_player = None
        self._turn_ctrls = None
        self._turn_state = None
        self._turn_actions = None
        self._turn_info = None
        self._turn_history = []
        self._turn_messages = []
        self.client_port = port

    @property
    def turn(self):
        return self._turn

    @property
    def turn_active(self):
        return self._turn_active

    @property
    def turn_actions(self):
        return self._turn_actions

    @turn.setter
    def turn(self, value):
        self._turn = value

    def log_begin_turn(self):
        fc_logger.info('==============================================')
        fc_logger.info(
            f"============== Begin turn: {self._turn:04d}. Port: {self.client_port}. Player: {self._turn_ctrls['player'].my_player_id} ==============")
        fc_logger.info('==============================================')
        # print(f'\nBegin turn: {self._turn:04d}\n')

    def begin_turn(self, pplayer, info_controllers: Dict[str, CivPropController]):
        # self._turn_active = True
        self._turn_player = pplayer
        self._turn_ctrls: Dict[str, CivPropController] = info_controllers
        self._turn_state: Dict[str, Dict] = dict()
        self._turn_actions: Dict[str, ActionList] = dict()
        self._turn_info: Dict[str, Dict] = dict()
        if self._turn == 1 and fc_args['wait_for_observer']:
            import time
            time.sleep(8)

    def begin_phase(self):
        self._turn_active = True

    @property
    def action_space(self):
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
        if self._turn_ctrls is None:
            return gymnasium.spaces.Discrete(1)

        observation_space = dict()
        fc_logger.debug('Computing observation space for: ')
        for ctrl_type, ctrl in self._turn_ctrls.items():
            fc_logger.debug(f'....: {ctrl_type}')
            if ctrl_type not in ['map', 'player', 'unit', 'city', 'dipl']:
                # TODO: add observation spaces for all controllers
                observation_space[ctrl_type] = gymnasium.spaces.Discrete(1)
            else:
                observation_space[ctrl_type] = ctrl.get_observation_space()

        return gymnasium.spaces.Dict(observation_space)

    def get_observation(self):
        fc_logger.debug("Acquiring state for: ")
        for ctrl_type, ctrl in self._turn_ctrls.items():
            fc_logger.debug(f'....: {ctrl_type}')
            if ctrl_type == 'map':
                # Add city map and unit map to observations
                cities = self._turn_ctrls['city'].cities
                units = self._turn_ctrls['unit'].units
                self._turn_state[ctrl_type] = ctrl.get_current_state(
                    self._turn_player, cities, units)
            else:
                self._turn_state[ctrl_type] = ctrl.get_current_state(
                    self._turn_player)
        return self._turn_state

    def get_available_actions(self):
        """This function will send queries to the server to get the probabilities for probabilistic actions.
        """
        fc_logger.debug("Acquiring action for: ")
        for ctrl_type in self._turn_ctrls.keys():
            fc_logger.debug(f'....: {ctrl_type}')
            controller: CivPropController = self._turn_ctrls[ctrl_type]
            action_list: ActionList = controller.get_current_options(self._turn_player)
            self._turn_actions[ctrl_type] = action_list
        return self._turn_actions

    def get_info(self):
        """This function will return a dictionary of the availability information about the actions for each controller.
        NOTE: This function should be called after get_available_actions has sent probability queries, and we have processed the responses by civ_controller (using lock_control()). Otherwise, the availability information will be missing.
        """
        fc_logger.debug("Acquiring info for: ")
        for ctrl_type in self._turn_ctrls.keys():
            fc_logger.debug(f'....: {ctrl_type}')
            action_list: ActionList = self._turn_actions[ctrl_type]
            action_info = action_list.get_action_info()
            if len(action_info) == 0 and ctrl_type in self._turn_info:
                del self._turn_info[ctrl_type]
            elif len(action_info) > 0:
                self._turn_info[ctrl_type] = action_info
        return self._turn_info

    def perform_action(self, action, ws_client):
        ctrl_type, valid_actor_id, action_name = action
        self._turn_actions[ctrl_type].trigger_single_action(valid_actor_id, action_name)
        return

    def get_reward(self, current_score):
        # FIXME: this function gets called every time the agent takes an action. However, the score only changes between turns.
        reward = current_score - self._last_score
        self._last_score = current_score
        return reward

    def end_turn(self):
        fc_logger.info(
            f'============== Finish turn {self._turn:04d} ==============')
        fc_logger.info(f'Sleeping for {self._sleep_time_after_turn} seconds')
        self._turn_active = False
        self._turn_player = None
        self._turn_ctrls = None
        self._turn_state = None
        self._turn_actions = None
        self._turn_info = None
        time.sleep(self._sleep_time_after_turn)

    def add_message(self, message):
        if isinstance(message, dict):
            message['turn'] = self._turn
        self._turn_messages.append(message)
        return

    @property
    def turn_messages(self):
        return self._turn_messages
