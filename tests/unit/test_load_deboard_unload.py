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


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T376_load_deboard_unload')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_load_deboard_unload(controller):
    fc_logger.info("test_load_deboard_unload")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    # for unit_id in unit_opt.unit_data.keys():
    #     unit_focus = unit_opt.unit_data[unit_id]
    #     ptile = unit_focus.ptile
    #     if (ptile['x'] == 45 and ptile['y'] == 30) or (ptile['x'] == 46 and ptile['y'] == 30):
    #         print(
    #             f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}, activity: {unit_focus.punit['activity']}.")

    # if unit_id == 1912:
    #     for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
    #         if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
    #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    # print(f'Unit {unit_id}')
    # print(unit_focus.punit)
    # # if unit_id == 1817:
    # #     print(unit_focus.punit)
    # #     print(f"({unit_focus.ptile['x']}, {unit_focus.ptile['y']})")
    # #     print(unit_focus.ptype)
    # valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # print(f'valid actions: {valid_actions.keys()}')

    # Boats are in (45, 30) -- a tile with city
    boat_ids = [1549, 1099]
    # Transported units are in (45, 30)
    unit_ids = [886, 1964, 1912]
    action_list = []
    old_homecity = None

    unit_focus = unit_opt.unit_data[886]
    assert (unit_focus.punit['transported_by'] == 1549)
    valid_actions = unit_opt.get_actions(886, valid_only=True)
    print(f'Unit {886}, valid action keys: {valid_actions.keys()}')
    print(f'Unit {886} embark to 1099 from 1549')
    valid_actions['embark_4_1099'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    assert (unit_focus.punit['transported_by'] == 1099)

    valid_actions = unit_opt.get_actions(1549, valid_only=True)
    print(f"Transporter {1549} valid action: {valid_actions.keys()}")
    print(f"Transporter {1549} moves to south east")
    valid_actions['goto_7'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    valid_actions = unit_opt.get_actions(886, valid_only=True)
    print(f'Unit {886}, valid action keys: {valid_actions.keys()}')
    valid_actions['embark_6_1549'].trigger_action(controller.ws_client)
    print(f'Unit {886} embark to 1549 from 1099')
    controller.send_end_turn()
    controller.get_info_and_observation()

    valid_actions = unit_opt.get_actions(1549, valid_only=True)
    print(f"Transporter {1549} valid action: {valid_actions.keys()}")
    print(f"Transporter {1549} moves to north west")
    valid_actions['goto_0'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    valid_actions = unit_opt.get_actions(886, valid_only=True)
    print(f'Unit {886}, valid action keys: {valid_actions.keys()}')
    print(f'Unit {886} embark to 1099 from 1549')
    valid_actions['embark_4_1099'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    assert (unit_focus.punit['transported_by'] == 1099)

    for unit_id in boat_ids+unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        if unit_id == 1549:
            assert ('unit_unload' in valid_actions)
        if unit_id == 1099:
            # This unit is not in a city, cannot unload its units.
            assert ('unit_unload' not in valid_actions)
            # Move to the city
            valid_actions[f'goto_{map_const.DIR8_WEST}'].trigger_action(controller.ws_client)
        if unit_id in unit_ids:
            # This unit is not transporter, cannot perform unload
            assert ('unit_unload' not in valid_actions)
            # The unit is being transported, cannot perform load
            assert ('board' not in valid_actions)

    # controller.send_end_turn()
    controller.get_info_and_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        print(f"{unit_id} is transported by {unit_focus.punit['transported_by']}")
        # These units is being transported.
        assert (unit_focus.punit['transported'])
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        if unit_id == 886:
            print(f"Unit {unit_id}\'s homecity: {unit_focus.punit['homecity']}")
            print('Unit 886 changes homecity')
            valid_actions['set_homecity'].trigger_action(controller.ws_client)
            old_homecity = unit_focus.punit['homecity']

    controller.get_info_and_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Unit's homecity can be changed when it is on the boat.
        if unit_id == 886:
            print(f"Unit {unit_id}\'s homecity: {unit_focus.punit['homecity']}")
            assert (old_homecity != unit_focus.punit['homecity'])

        # if unit_id == 1912 or unit_id == 1964:
        #     print(f'Unit: {unit_id}')
        #     for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        #         if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
        #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    for unit_id in boat_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # Both boats are in a city, can unload.
        assert ('unit_unload' in valid_actions)

        if unit_id == 1549:
            print(f"Boat {unit_id}'s move left before unload: {unit_focus.punit['movesleft']}")
            # Boat 1549 unloads its units.
            valid_actions['unit_unload'].trigger_action(controller.ws_client)

    print('Unit 1549 unloads its units.')

    controller.get_info_and_observation()

    unit_focus = unit_opt.unit_data[1549]
    print(f"Boat {1549}'s move left after unload: {unit_focus.punit['movesleft']}")

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 1912 or unit_id == 886:
            assert (unit_focus.punit['transported'])
        else:
            # Unit 1964 has been unloaded.
            assert (unit_focus.punit['transported'] == 0)
            assert ('board' in valid_actions)
            valid_actions['board'].trigger_action(controller.ws_client)
            print(f'Unit {unit_id} loading.')
        # print(unit_focus.punit)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

    controller.get_info_and_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # All units have been onboard.
        assert (unit_focus.punit['transported'] > 0)
        assert ('board' not in valid_actions)
        assert ('deboard' in valid_actions)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        print(f"{unit_id} is transported by {unit_focus.punit['transported_by']}")
        print(f"Unit {unit_id}\'s activity: {unit_focus.punit['activity']}")
        valid_actions['deboard'].trigger_action(controller.ws_client)

    print('All units deboard.')
    controller.get_info_and_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # All units have deboarded.
        assert (unit_focus.punit['transported'] == 0)
        assert ('board' in valid_actions)
        assert ('deboard' not in valid_actions)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        print(f"Unit {unit_id}\'s activity: {unit_focus.punit['activity']}")
        print(f"Unit{unit_id}\'s move left: {unit_focus.punit['movesleft']}")

        if unit_id == 886 or unit_id == 1964:
            valid_actions['board'].trigger_action(controller.ws_client)

    print('Units 886 and 1964 board again.')
    controller.get_info_and_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        # print(f"Unit{unit_id}\'s move left: {unit_focus.punit['movesleft']}")
        if unit_id == 886:
            print('Unit 886 join city when on the boat')
            valid_actions['join_city'].trigger_action(controller.ws_client)
        if unit_id == 1964:
            print('Unit 1964 fortify when on the boat')
            valid_actions['fortify'].trigger_action(controller.ws_client)

    controller.get_info_and_observation()
    assert (886 not in unit_opt.unit_data)
    unit_id = 1964
    unit_focus = unit_opt.unit_data[unit_id]
    # Is fortifying
    assert (unit_focus.punit['activity'] == 10)

    controller.send_end_turn()
    controller.get_info_and_observation()
    # Fortified
    assert (unit_focus.punit['activity'] == 4)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    print('Unit 1964 perform trade_route')
    valid_actions['trade_route_-1'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    assert (1964 not in unit_opt.unit_data)

    unit_id = 1912
    unit_focus = unit_opt.unit_data[unit_id]
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # All units have deboarded.
    assert (unit_focus.punit['transported'] == 0)
    assert ('board' in valid_actions)
    assert ('deboard' not in valid_actions)
    valid_actions['board'].trigger_action(controller.ws_client)
    print('Units 1912 board again.')
    controller.get_info_and_observation()

    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # print(valid_actions.keys())
    valid_actions['fortify'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    print(f"Unit 1912 participate in activity: {unit_focus.punit['activity']}")

    print('Unit 1912 disembark')
    valid_actions['disembark_0'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # print(valid_actions.keys())

    print('Unit 1912 embark again')
    valid_actions['embark_7_1549'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # print(valid_actions.keys())
    valid_actions['fortify'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    print(f"Unit 1912 participate in activity: {unit_focus.punit['activity']}")
    #### The board and deboard actions do not change unit's activity.
    print('Unit 1912 deboard')
    valid_actions['deboard'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # print(valid_actions.keys())
    print(f"Unit 1912 participate in activity: {unit_focus.punit['activity']}")
    print('Unit 1912 board')
    valid_actions['board'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(valid_actions.keys())
    print(f"Unit 1912 is participating in activity {unit_focus.punit['activity']} during board")

    # Test activity on the sea
    print(f"Unit 1912 is transported by: {unit_focus.punit['transported_by']}")
    valid_actions = unit_opt.get_actions(unit_focus.punit['transported_by'], valid_only=True)
    print(f"Transporter {unit_focus.punit['transported_by']} valid action: {valid_actions.keys()}")
    print(f"Transporter {unit_focus.punit['transported_by']} move to south east")
    valid_actions['goto_7'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    print(f"Unit 1912 participates in activity: {unit_focus.punit['activity']}")
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    # valid_actions['disembark_0'].trigger_action(controller.ws_client)
    # controller.get_info_and_observation()
    print('Unit 1912 do marketplace')
    valid_actions['marketplace_0'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    assert (1912 not in unit_opt.unit_data)

def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T376_load_deboard_unload')
    test_load_deboard_unload(controller)


if __name__ == '__main__':
    main()
