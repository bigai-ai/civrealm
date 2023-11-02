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


import numpy as np
import gymnasium

from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.freeciv.map.map_ctrl import MapCtrl
from civrealm.freeciv.city.city_ctrl import CityCtrl

from civrealm.freeciv.utils.base_state import DictState
from civrealm.freeciv.utils.fc_types import O_SHIELD, O_GOLD, O_FOOD


class UnitState(DictState):
    def __init__(self, unit_ctrl, rule_ctrl: RulesetCtrl, map_ctrl: MapCtrl, city_ctrl: CityCtrl):
        super().__init__()
        self.unit_ctrl = unit_ctrl
        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl
        self.map_ctrl = map_ctrl

        self.common_unit_fields = ['owner', 'hp', 'veteran', 'x', 'y']
        self.type_unit_fields = [
            'rule_name', 'attack_strength', 'defense_strength', 'firepower', 'build_cost', 'convert_time',
            'converted_to', 'obsoleted_by', 'hp', 'move_rate', 'vision_radius_sq', 'worker']
        self.my_unit_fields = ['home_city', 'moves_left', 'upkeep_food', 'upkeep_shield', 'upkeep_gold']

    def _update_state(self, pplayer):
        """ 
            Function returns the current state of all units of player pplayer
        """
        self._state = {}
        for unit_id in self.unit_ctrl.units.keys():
            punit = self.unit_ctrl.units[unit_id]
            self._state[unit_id] = self._get_unit_state(punit, punit['owner'] == pplayer['playerno'])

    def _get_unit_state(self, punit, unit_owned):
        """Returns a dictionary of all infos relevant for unit_state."""
        unit_state = {}
        unit_state['owner'] = punit['owner']
        unit_state['health'] = punit['hp']
        unit_state['veteran'] = punit['veteran']

        # Info from the unit's tile
        tile = self.map_ctrl.index_to_tile(punit['tile'])
        unit_state['x'] = tile['x']
        unit_state['y'] = tile['y']

        # Info from the unit's type
        ptype = self.rule_ctrl.unit_type(punit)
        for type_desc in self.type_unit_fields:
            unit_state['type_'+type_desc] = ptype[type_desc]
        unit_state['type_can_transport'] = ptype['transport_capacity'] > 0

        # Info that differs between own and foreign units
        if unit_owned:
            # Can use self.city_ctrl.get_unit_homecity_name(punit) to get a string of the home city name
            unit_state['home_city'] = punit['homecity']
            # Can use unit_helpers.get_unit_moves_left(self.rule_ctrl, punit) to get a string of the moves left
            unit_state['moves_left'] = punit['movesleft']
            unit_state['upkeep_food'] = punit['upkeep'][O_FOOD]
            unit_state['upkeep_shield'] = punit['upkeep'][O_SHIELD]
            unit_state['upkeep_gold'] = punit['upkeep'][O_GOLD]
        else:
            unit_state['home_city'] = -1
            unit_state['moves_left'] = -1
            unit_state['upkeep_food'] = -1
            unit_state['upkeep_shield'] = -1
            unit_state['upkeep_gold'] = -1

        return unit_state

    def get_observation_space(self):
        unit_space = gymnasium.spaces.Dict({
            # Common unit fields
            'owner': gymnasium.spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
            'health': gymnasium.spaces.Box(low=0, high=100, shape=(1,), dtype=np.uint8),
            'veteran': gymnasium.spaces.Box(low=0, high=1, shape=(1,), dtype=np.uint8),
            # TODO: may change this to actual map size
            'x': gymnasium.spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),
            'y': gymnasium.spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8),

            # Unit type fields
            'type_rule_name': gymnasium.spaces.Box(low=0, high=len(self.rule_ctrl.unit_types)-1, shape=(1,), dtype=np.uint8),
            'type_attack_strength': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_defense_strength': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_firepower': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_build_cost': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_convert_time': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_converted_to': gymnasium.spaces.Box(low=0, high=len(self.rule_ctrl.unit_types)-1, shape=(1,), dtype=np.uint8),
            'type_obsoleted_by': gymnasium.spaces.Box(low=0, high=len(self.rule_ctrl.unit_types)-1, shape=(1,), dtype=np.uint8),
            'type_hp': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_move_rate': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_vision_radius_sq': gymnasium.spaces.Box(low=0, high=65535, shape=(1,), dtype=np.uint16),
            'type_worker': gymnasium.spaces.Discrete(1),  # Boolean
            'type_can_transport': gymnasium.spaces.Discrete(1),  # Boolean

            # My unit specific fields
            'home_city': gymnasium.spaces.Box(low=-1, high=len(self.city_ctrl.cities)-1, shape=(1,), dtype=np.int16),
            'moves_left': gymnasium.spaces.Box(low=-1, high=32767, shape=(1,), dtype=np.int16),
            'upkeep_food': gymnasium.spaces.Box(low=-1, high=32767, shape=(1,), dtype=np.int16),
            'upkeep_shield': gymnasium.spaces.Box(low=-1, high=32767, shape=(1,), dtype=np.int16),
            'upkeep_gold': gymnasium.spaces.Box(low=-1, high=32767, shape=(1,), dtype=np.int16),
        })

        return gymnasium.spaces.Dict({unit_id: unit_space for unit_id in self.unit_ctrl.units.keys()})

# TODO: add plant time, mining time etc. to the unit state. This information is useful for plant/mine/irrigate/... action.
