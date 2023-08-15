# Copyright (C) 2023  The Freeciv-gym project
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

from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv


class FreecivTensorEnv(FreecivBaseEnv):
    """ Freeciv gym environment with code actions """

    def __init__(self):
        super().__init__()

    def _get_observation(self):
        self.civ_controller.lock_control()
        self.civ_controller.turn_manager.get_observation()
        turn_manager = self.civ_controller.turn_manager

        observations = {}
        for ctrl_type, ctrl in turn_manager._turn_ctrls.items():
            if ctrl_type == 'unit':
                observations[ctrl_type] = self.civ_controller.controller_list['map'].prop_state._state['terrain']
            else:
                observations[ctrl_type] = turn_manager._turn_state[ctrl_type]

        return observations
