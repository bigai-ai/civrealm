# Copyright (C) 2023  The CivRealm project
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

import pytest
import random
from civrealm.freeciv.civ_controller import CivController
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T241_2023-09-12-14_20')
    yield controller

    controller.handle_end_turn(None)
    controller.close()


def find_keys_with_keyword(dictionary, keyword):
    keys = []
    for key in dictionary:
        if keyword in key:
            keys.append(dictionary[key])
    return keys


def test_city_buy_prod(controller):
    fc_logger.info("test_city_buy_if_anarchy")
    _, options = get_first_observation_option(controller)

    city_opt = options['city']
    """ a city which was in disorder at the last turn """
    city_id = 695
    pcity = city_opt.cities[city_id]

    """ pcity is not in disorder at this turn """
    assert not controller.city_ctrl.city_unhappy(pcity)

    valid_city_buy_actions = find_keys_with_keyword(city_opt.get_actions(city_id, valid_only=True),
                                                    'city_buy_production')

    """ city cannot buy at this turn """
    if 'anarchy' in pcity:
        assert len(valid_city_buy_actions) == 0
    else:

        """ city_unhappiness cannot prune some invalid 'buy' actions """
        assert len(valid_city_buy_actions) > 0
        city_buy_action = random.choice(valid_city_buy_actions)
        assert (city_buy_action.is_action_valid())

        did_buy_1 = pcity['did_buy']
        city_buy_action.trigger_action(controller.ws_client)
        controller.get_info_and_observation()
        did_buy_2 = pcity['did_buy']
        """ however this invalid 'buy' action does not work """
        assert did_buy_1 == 0 and did_buy_2 == 0

    controller.send_end_turn()
    controller.get_info_and_observation()

    """ city can buy at the next turn """
    valid_city_buy_actions = find_keys_with_keyword(city_opt.get_actions(city_id, valid_only=True),
                                                    'city_buy_production')
    assert len(valid_city_buy_actions) > 0

    city_buy_action = random.choice(valid_city_buy_actions)
    assert (city_buy_action.is_action_valid())

    did_buy_1 = pcity['did_buy']

    city_buy_action.trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    did_buy_2 = pcity['did_buy']
    """ 'buy' action works at this turn """
    assert did_buy_1 == 0 and did_buy_2 == 1
