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


ctrl_type = 'unit'


def test_unit_dict(env):
    observation, info = env.reset()

    if observation[ctrl_type]:
        unit_dict = observation[ctrl_type]['unit_dict']
        assert ctrl_type in info['available_actions']

        info_actions = info['available_actions'][ctrl_type]

        for unit in unit_dict:
            unit_id = int(unit.split(' ')[1])
            assert (unit_id in info_actions)

            unit_action_set = unit_dict[unit]['avail_actions']

            for action_name in unit_action_set:
                assert (info_actions[unit_id][action_name] is True)

        for unit_id in info_actions:
            punit = env.civ_controller.unit_ctrl.units[unit_id]
            if punit['activity'] == 0:
                unit = UNIT_TYPES[punit['type']] + ' ' + str(unit_id)

                for action_name in info_actions[unit_id]:
                    if info_actions[unit_id][action_name]:
                        assert action_name in unit_dict[unit]['avail_actions']

