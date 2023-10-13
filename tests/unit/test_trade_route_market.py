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
    controller.set_parameter('debug.load_game', 'testcontroller_T379_2023-08-09-06_16')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_trade_route_market(controller):
    fc_logger.info("test_trade_route_market")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        if (ptile['x'] == 45 and ptile['y'] == 30) or (ptile['x'] == 45 and ptile['y'] == 29):
            print(
                f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}, activity: {unit_focus.punit['activity']}.")

        #     for i in range(len(unit_focus.action_prob[map_const.DIR8_SOUTH])):
        #         if unit_focus.action_prob[map_const.DIR8_SOUTH][i] != {'min': 0, 'max': 0}:
        #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_SOUTH][i]}')

        #     for i in range(len(unit_focus.action_prob[map_const.DIR8_NORTHEAST])):
        #         if unit_focus.action_prob[map_const.DIR8_NORTHEAST][i] != {'min': 0, 'max': 0}:
        #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_NORTHEAST][i]}')

    # Transported units are in (45, 30)
    unit_ids = [1964, 1912, 1743]
    action_list = []
    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

        trade_route = False
        trade_route_num = 0
        for key in valid_actions.keys():
            if key.startswith('trade_route'):
                trade_route_num += 1
                trade_route = True
        assert (trade_route)
        if unit_id == 1743 or unit_id == 1912:
            assert (trade_route_num == 1)
        if unit_id == 1912:
            valid_actions['fortify'].trigger_action(controller.ws_client)
        # Unit 1964 is adjacent to two cities, so it has two trade_route options.
        if unit_id == 1964:
            assert (trade_route_num == 2)
            valid_actions['fortify'].trigger_action(controller.ws_client)
        if unit_id == 1743:
            # Unit 1743 changes its homecity.
            valid_actions['set_homecity'].trigger_action(controller.ws_client)

    # controller.send_end_turn()
    controller.get_info_and_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f"Unit {unit_id}, valid action keys: {valid_actions.keys()}, activity: {unit_focus.punit['activity']}")

        trade_route = False
        trade_route_num = 0
        for key in valid_actions.keys():
            if key.startswith('trade_route'):
                trade_route_num += 1
                trade_route = True

        # This unit has changed the homecity to the current city, cannot build trade route anymore.
        if unit_id == 1743:
            assert (not trade_route)
            assert (trade_route_num == 0)

        # Unit 1964 is adjacent to two cities, so it has two trade_route options.
        if unit_id == 1964:
            assert (trade_route)
            assert (trade_route_num == 2)

        if unit_id == 1912:
            assert (trade_route)
            assert (trade_route_num == 1)
            print('Unit 1912 build trade route')
            valid_actions['trade_route_-1'].trigger_action(controller.ws_client)

    city_id = 414
    # The trade route is empty before 1912 build one.
    assert (city_id not in controller.city_ctrl.city_trade_routes)

    controller.send_end_turn()
    controller.get_info_and_observation()

    # Unit 1912 has built a trade route.
    assert (controller.city_ctrl.city_trade_routes[city_id] != {})
    # Unit 1912 has been removed.
    del unit_ids[1]

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f"Unit {unit_id}, valid action keys: {valid_actions.keys()}, activity: {unit_focus.punit['activity']}")

        trade_route = False
        trade_route_num = 0
        for key in valid_actions.keys():
            if key.startswith('trade_route'):
                trade_route_num += 1
                trade_route = True

        marketplace = False
        marketplace_num = 0
        for key in valid_actions.keys():
            if key.startswith('marketplace'):
                marketplace_num += 1
                marketplace = True

        if unit_id == 1964:
            assert (trade_route)
            # One adjacent city has set up a trade route with its home city
            assert (trade_route_num == 1)
            assert (marketplace)
            assert (marketplace_num == 1)
            print('Unit 1964 performs marketplace action.')
            valid_actions['marketplace_6'].trigger_action(controller.ws_client)

    controller.get_info_and_observation()

    # Unit 1964 has been removed due to market action.
    assert (1964 not in unit_opt.unit_data)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T379_2023-08-09-06_16')
    test_trade_route_market(controller)


if __name__ == '__main__':
    main()
