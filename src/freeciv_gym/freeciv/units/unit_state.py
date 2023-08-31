# Copyright (C) 2023  The Freeciv-gym project
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


from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.freeciv.map.map_ctrl import MapCtrl
from freeciv_gym.freeciv.city.city_ctrl import CityCtrl

from freeciv_gym.freeciv.utils.base_state import ListState
from freeciv_gym.freeciv.utils.fc_types import O_SHIELD, O_GOLD, O_FOOD


class UnitState(ListState):
    def __init__(self, unit_ctrl, rule_ctrl: RulesetCtrl, map_ctrl: MapCtrl, city_ctrl: CityCtrl):
        super().__init__()
        self.unit_ctrl = unit_ctrl
        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl
        self.map_ctrl = map_ctrl

    def _update_state(self, pplayer):
        """ 
            Function returns the current state of all units of player pplayer
        """
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
        for type_desc in ['rule_name', 'attack_strength', 'defense_strength', 'firepower', 'build_cost',
                          'convert_time', 'converted_to', 'obsoleted_by', 'hp', 'move_rate', 'vision_radius_sq',
                          'worker']:
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

# TODO: add plant time, mining time etc. to the unit state. This information is useful for plant/mine/irrigate/... action.
