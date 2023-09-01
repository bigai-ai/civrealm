# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# #  Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
import gymnasium
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES


@pytest.fixture
def env():
    env = gymnasium.make("freeciv/FreecivCode-v0")
    yield env
    env.close()


ctrl_type = 'city'


def test_city_dict(env):
    observation, info = env.reset()

    if observation[ctrl_type]:
        city_dict = observation[ctrl_type]['city_dict']
        assert ctrl_type in info['available_actions']

        info_actions = info['available_actions'][ctrl_type]

        for city in city_dict:
            city_id = int(city.split(' ')[1])
            assert (city_id in info_actions)

            city_action_set = city_dict[city]['avail_actions']

            for action_name in city_action_set:
                assert (info_actions[city_id][action_name] is True)

        for city_id in info_actions:
            pcity = env.civ_controller.city_ctrl.cities[city_id]
            if (env.civ_controller.turn_manager.turn == 1 or
                    env.civ_controller.turn_manager.turn == pcity['turn_last_built'] + 1):
                city = 'City' + ' ' + str(city_id)

                for action_name in info_actions[city_id]:
                    if info_actions[city_id][action_name]:
                        assert action_name in city_dict[city]['avail_actions']
