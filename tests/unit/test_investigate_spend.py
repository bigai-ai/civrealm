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
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option
import civrealm.freeciv.utils.fc_types as fc_types


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T385_embassy_investigate')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_investigate_spend(controller):
    fc_logger.info("test_investigate_spend")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    unit_id = 2021

    # Get valid actions
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    investigate_spend = False
    for action_key in valid_actions:
        if action_key.startswith('investigate_spend'):
            investigate_spend = True

    # Can investigate city
    assert (investigate_spend)

    valid_actions['fortify'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    print(f"Partificate in activity {unit_opt.unit_data[unit_id].punit['activity']}")

    # unit_focus = unit_opt.unit_data[unit_id]
    # for i in range(len(unit_focus.action_prob[map_const.DIR8_NORTHWEST])):
    #     if unit_focus.action_prob[map_const.DIR8_NORTHWEST][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_NORTHWEST][i]}')

    # other_player_id = controller.city_ctrl.cities[885]['owner']
    # # Embassy has not been established
    # assert (controller.player_ctrl.players[controller.player_ctrl.my_player_id]['real_embassy'][other_player_id] == 0)
    target_city = controller.city_ctrl.cities[885]
    assert ('can_build_improvement' not in target_city)
    print(target_city)

    print('Investigate city.')
    valid_actions['investigate_spend_0'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    # This info of the target_city has been investigated.
    assert ('can_build_improvement' in target_city)
    print(target_city)

    # The unit has been consumed.
    assert (unit_id not in unit_opt.unit_data)


def main():
    fc_args['username'] = 'testcontroller'
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T385_embassy_investigate')
    test_investigate_spend(controller)
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


if __name__ == '__main__':
    main()
