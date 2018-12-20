'''
Created on 09.03.2018

@author: christian
'''
from freecivbot.utils.base_state import ListState
from freecivbot.utils.fc_types import O_SHIELD, O_GOLD, O_FOOD

class UnitState(ListState):
    def __init__(self, unit_ctrl, rule_ctrl, city_ctrl):
        ListState.__init__(self)
        self.unit_ctrl = unit_ctrl
        self.rule_ctrl = rule_ctrl
        self.city_ctrl = city_ctrl
        
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