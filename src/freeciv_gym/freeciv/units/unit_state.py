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
            if punit["owner"] == pplayer["playerno"]:
                self._state[unit_id] = self._get_unit_infos(punit)

    def _get_unit_infos(self, aunit):
        """Returns a dictionary of all infos relevant for unit_state"""
        unit_state = {}

        ptype = self.rule_ctrl.unit_type(aunit)
        for type_desc in ["rule_name", "attack_strength", "defense_strength", "firepower", "build_cost",
                          "convert_time", "converted_to", "hp", "move_rate", "vision_radius_sq",
                          "worker"]:
            unit_state["type_"+type_desc] = ptype[type_desc]

        tile = self.map_ctrl.index_to_tile(aunit['tile'])
        unit_state['x'] = tile['x']
        unit_state['y'] = tile['y']

        unit_state["can_transport"] = ptype['transport_capacity'] > 0
        unit_state["home_city"] = self.city_ctrl.get_unit_homecity_name(aunit)
        if unit_state["home_city"] == None:
            unit_state["home_city"] = -1
        unit_state["moves_left"] = self.unit_ctrl.get_unit_moves_left(aunit)
        unit_state["health"] = aunit['hp']
        unit_state["veteran"] = aunit['veteran']

        unit_state["upkeep_food"] = aunit['upkeep'][O_FOOD] if "upkeep" in aunit else -1
        unit_state["upkeep_shield"] = aunit['upkeep'][O_SHIELD] if "upkeep" in aunit else -1
        unit_state["upkeep_gold"] = aunit['upkeep'][O_GOLD] if "upkeep" in aunit else -1

        return unit_state

# TODO: add plant time, mining time etc. to the unit state. This information is useful for plant/mine/irrigate/... action.