# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# # Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License 
# for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.utils.fc_types as fc_types
import freeciv_gym.freeciv.map.map_const as map_const


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T154_2023-07-25-09_52_diplunit')
    yield controller
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_get_action_pro_spy(controller):
    fc_logger.info("test_get_action_pro_spy_bribe")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]        
        if unit_id == 1164:
            # The agent cannot move to sea.
            assert(unit_focus.action_prob[map_const.DIR8_SOUTHWEST][fc_types.ACTION_SPY_BRIBE_UNIT] == {'min': 200, 'max': 200})


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T154_2023-07-25-09_52_diplunit')
    test_get_action_pro_spy(controller)


if __name__ == '__main__':
    main()