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
from civrealm.freeciv.utils.fc_types import EXTRA_ROAD, EXTRA_RAILROAD, EXTRA_IRRIGATION
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T203_pillage')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_pillage(controller):
    fc_logger.info("test_pillage")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_id = [551, 843, 507]
    # for unit_id in unit_opt.unit_data.keys():
    #     punit = unit_opt.unit_ctrl.units[unit_id]
    #     unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    #     print(
    #         f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    #     # Get valid actions
    #     valid_actions = unit_opt.get_actions(unit_id, valid_only=True)

    valid_actions = unit_opt.get_actions(551, valid_only=True)
    valid_actions['plant'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    assert (unit_opt.unit_ctrl.units[551]['activity'] != 0)
    print(f"Unit 551 participate in activity {unit_opt.unit_ctrl.units[551]['activity']}")

    for worker in worker_id:
        valid_actions = unit_opt.get_actions(worker, valid_only=True)
        # pillage is valid for all works
        assert ('pillage' in valid_actions)
        if worker == 551:
            # Trigger pillage action for 138 worker
            valid_actions['pillage'].trigger_action(controller.ws_client)

    # Update state
    controller.get_info_and_observation()
    worker_id = [843, 507]

    for worker in worker_id:
        valid_actions = unit_opt.get_actions(worker, valid_only=True)
        # pillage is valid for all workers
        assert ('pillage' in valid_actions)
        if worker == 843:
            # Trigger pillage action for 843 worker
            valid_actions['pillage'].trigger_action(controller.ws_client)

    # Update state
    controller.get_info_and_observation()
    worker_id = 507

    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # The current tile has two extras and there are already two workers are doing pillage, so pillage is not valid for the remaining worker. Note that the internal data in tiles will have three extras because the existence of railroad requires the existence of road. However, before the railroad is pillaged, the road cannot be pillaged.
    assert ('pillage' not in valid_actions)

    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[worker_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])

    # Currently has three extras, but can only pillage two
    assert (unit_tile['extras'][EXTRA_ROAD] == 1)
    assert (unit_tile['extras'][EXTRA_IRRIGATION] == 1)
    assert (unit_tile['extras'][EXTRA_RAILROAD] == 1)

    print('Begin pillaging railroad and irrigation, needs one turn to finish ...')
    controller.send_end_turn()
    controller.get_info_and_observation()

    # Pillage remove railroad and irrigation
    assert (unit_tile['extras'][EXTRA_ROAD] == 1)
    assert (not unit_tile['extras'][EXTRA_RAILROAD] == 1)
    assert (not (unit_tile['extras'][EXTRA_IRRIGATION] == 1))

    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    assert ('pillage' in valid_actions)
    valid_actions['pillage'].trigger_action(controller.ws_client)

    print('Begin pillaging road, needs one turn to finish ...')
    controller.send_end_turn()
    controller.get_info_and_observation()
    # Pillage remove road
    assert (not (unit_tile['extras'][EXTRA_ROAD] == 1))

    # Move to a city
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    valid_actions[f'goto_{map_const.DIR8_SOUTHEAST}'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()

    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # In city, there is railroad extra. But we cannot pillage it
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    assert (not 'pillage' in valid_actions)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T203_pillage')
    test_pillage(controller)


if __name__ == '__main__':
    main()
