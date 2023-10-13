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
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.utility import byte_to_bit_array, find_set_bits
from BitVector import BitVector


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T82_attack')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_get_action_pro(controller):
    fc_logger.info("test_get_action_pro")
    _, options = get_first_observation_option(controller)
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
        if unit_id == 396:
            # 396 unit has not move left. It can do nothing.
            assert (len(unit_focus.action_prob) == 0)
        if unit_id == 250:
            assert (unit_focus.action_prob[map_const.DIR8_NORTHEAST]
                    [fc_types.ACTION_UNIT_MOVE] == {'min': 200, 'max': 200})
            # Attack pros are different given different targets.
            assert (unit_focus.action_prob[map_const.DIR8_NORTHWEST]
                    [fc_types.ACTION_ATTACK] == {'min': 200, 'max': 200})
            assert (unit_focus.action_prob[map_const.DIR8_SOUTHEAST][fc_types.ACTION_ATTACK] == {'min': 1, 'max': 2})
            # Cannot move to sea (north and west).
            assert (unit_focus.action_prob[map_const.DIR8_NORTH][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            assert (unit_focus.action_prob[map_const.DIR8_WEST][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            # Cannot move to east. TODO: figure out why. Maybe because an enemy unit is doing fortify.
            assert (unit_focus.action_prob[map_const.DIR8_EAST][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            # Can move to own units.
            assert (unit_focus.action_prob[map_const.DIR8_SOUTH][fc_types.ACTION_UNIT_MOVE])
        if unit_id == 126:
            # Cannot move to enemy unit. Explorer also cannot attack enemy.
            assert (unit_focus.action_prob[map_const.DIR8_EAST][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            assert (unit_focus.action_prob[map_const.DIR8_EAST][fc_types.ACTION_ATTACK] == {'min': 0, 'max': 0})
        #     ptile = unit_focus.ptile
        #     tile = unit_opt.map_ctrl.mapstep(ptile, map_const.DIR8_NORTH)
        #     extra = tile['extras']
        #     extra[16] = 1
        #     print(extra)
        #     print(extra.count_bits_sparse())
        #     extra_id = find_set_bits(extra)
        #     print(find_set_bits(extra))
        #     # print((unit_opt.rule_ctrl.extras))
        #     for id in extra_id:
        #         print(unit_opt.rule_ctrl.extras[id]['name'])

    controller.send_end_turn()
    print('end turn')
    controller.get_info_and_observation()
    options = controller.turn_manager.turn_actions
    unit_opt = options['unit']
    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # In last turn, Unit 207 has a goal. Afer end turn, it reaches the goal and its action_decision_want becomes non_zero. We will clear its action_decision_want and query its action pro in this case.
        if unit_id == 207:
            assert (len(unit_focus.action_prob) > 0)

    controller.send_end_turn()
    print('end turn')
    controller.get_info_and_observation()
    options = controller.turn_manager.turn_actions
    unit_opt = options['unit']
    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # In last turn, we clear unit 207's action_decision_want by action_decision_clear_want() and we query its action pro in this turn.
        if unit_id == 207:
            assert (len(unit_focus.action_prob) > 0)
            assert (unit_focus.action_prob[map_const.DIR8_NORTH]
                    [fc_types.ACTION_CONQUER_CITY] == {'min': 200, 'max': 200})


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T82_attack')
    test_get_action_pro(controller)


if __name__ == '__main__':
    main()
