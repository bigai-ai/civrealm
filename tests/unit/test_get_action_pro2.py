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


import pytest
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option
import civrealm.freeciv.utils.fc_types as fc_types
from civrealm.freeciv.utils.utility import byte_to_bit_array, find_set_bits
from BitVector import BitVector


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_get_action_pro2(controller):
    fc_logger.info("test_get_action_pro2")
    _, options = get_first_observation_option(controller)
    # for type_id in controller.rule_ctrl.unit_types:
    for type_id in range(0, 2):
        type = controller.rule_ctrl.unit_types[type_id]
        print(type['name'])
        print(type['utype_actions'])
        for i in range(len(type['utype_actions'])):
            if type['utype_actions'][i]:
                print(i)
    # Class: UnitActions
    unit_opt = options['unit']
    # Get all units (including those controlled by other players)
    # for unit_id in unit_opt.unit_ctrl.units.keys():
    # Get all unit type information
    # for type in unit_opt.rule_ctrl.unit_types:
    #     name = unit_opt.rule_ctrl.unit_types[type]['name']
    #     if name == 'Nuclear' or name == 'Helicopter' or name == 'Horsemen':
    #         print(unit_opt.rule_ctrl.unit_types[type])
    #         print('===============')
    # Get all units controlled by the current player
    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # print(
        #     f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}.")
        if unit_id == 140:
            # The agent cannot move to sea.
            assert (unit_focus.action_prob[map_const.DIR8_SOUTH][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            assert (unit_focus.action_prob[map_const.DIR8_NORTH][fc_types.ACTION_UNIT_MOVE] == {'min': 200, 'max': 200})

        # for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        #     if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
        #         print(f'index: {i}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_get_action_pro2(controller)


if __name__ == '__main__':
    main()
