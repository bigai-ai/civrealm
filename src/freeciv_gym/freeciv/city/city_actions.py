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

from math import floor, sqrt

from freeciv_gym.freeciv.connectivity.civ_connection import CivConnection
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.freeciv.map.map_ctrl import MapCtrl

from freeciv_gym.freeciv.utils.base_action import Action, ActionList
from freeciv_gym.freeciv.utils.fc_types import packet_city_make_specialist,\
    packet_city_change_specialist, packet_city_make_worker, packet_city_buy,\
    packet_city_sell, packet_city_change, VUT_UTYPE,\
    VUT_IMPROVEMENT, packet_city_rename, packet_city_worklist, packet_city_refresh
from freeciv_gym.freeciv.map.map_ctrl import CityTileMap

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger

MAX_LEN_WORKLIST = 64
MAX_SPECIALISTS = 20

"""
before any of the modifiers below 
after luxury
after building effects
after citizen nationality effects 
after units enforce martial order
after wonders: final result
"""

FEELING_BASE = 0
FEELING_LUXURY = 1
FEELING_EFFECT = 2
FEELING_NATIONALITY = 3
FEELING_MARTIAL = 4
FEELING_FINAL = 5

IG_IMPROVEMENT = 2


class CityActions(ActionList):
    def __init__(self, ws_client: CivConnection, city_list: list, rulectrl: RulesetCtrl, map_ctrl: MapCtrl):
        super().__init__(ws_client)
        self.cities = city_list
        self.rulectrl = rulectrl
        self.map_ctrl = map_ctrl
        self.city_map = CityTileMap(1, map_ctrl)

        self.tiles_shared = dict()

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):

        for city_id in self.cities:
            pcity = self.cities[city_id]
            if pcity["owner"] != pplayer["playerno"]:
                if self.actor_exists(city_id):
                    del self._action_dict[city_id]
                continue
            if self.actor_exists(city_id):
                continue
            self.add_actor(city_id)

            r_city = int(floor(sqrt(pcity["city_radius_sq"])))
            for dx in range(-r_city, r_city+1):
                for dy in range(-r_city, r_city+1):
                    if dx == 0 and dy == 0:
                        continue

                    self.add_action(city_id, CityWorkTile(pcity, dx, dy, self.city_map, pplayer, self.tiles_shared))
                    self.add_action(city_id, CityUnworkTile(pcity, dx, dy, self.city_map, pplayer, self.tiles_shared))

            for specialist_num in range(pcity['specialists_size']):
                self.add_action(city_id, CityChangeSpecialist(pcity, specialist_num))

            self.add_action(city_id, CityBuyProduction(pcity, pplayer))

            for unit_type_id in self.rulectrl.unit_types:
                punit_type = self.rulectrl.unit_types[unit_type_id]
                self.add_action(city_id, CityChangeUnitProduction(pcity, punit_type))

            for improvement_id in self.rulectrl.improvements:

                pimprovement = self.rulectrl.improvements[improvement_id]
                self.add_action(city_id, CityChangeImprovementProduction(pcity, pimprovement))

                """
                logic from freeciv server: freeciv/common/improvement.c
                func: can_city_sell_building / is_building_sellable / is_improvement              
                """
                if pimprovement['genus'] == IG_IMPROVEMENT:
                    self.add_action(city_id, CitySellImprovement(pcity, improvement_id, pimprovement["name"]))


class CityWorkTile(Action):
    action_key = "city_work"

    def __init__(self, pcity, dx, dy, city_map: CityTileMap, pplayer, tiles_shared):
        super().__init__()
        self.dx = dx
        self.dy = dy
        self.pcity = pcity
        self.cur_player = pplayer
        self.tiles_shared = tiles_shared
        self.city_map = city_map
        self.city_map.update_map(pcity["city_radius_sq"])

        self.ctile = city_map.map_ctrl.city_tile(pcity)
        self.ptile = city_map.map_ctrl.map_pos_to_tile(self.ctile["x"] + dx, self.ctile["y"] + dy)

        self.output_idx = self.city_map.get_city_dxy_to_index(dx, dy, self.ctile)
        if self.output_idx is None:
            self.action_key += "_None_%i_%i" % (dx, dy)
        else:
            self.action_key += "_%i_%i_%i" % (self.output_idx, dx, dy)

    def is_action_valid(self):
        if self.city_map.map_ctrl.is_out_of_map(self.ctile['x'] + self.dx, self.ctile['y'] + self.dy):
            return False

        if self.output_idx is None:
            return False

        if self.unit_occupies_tile():
            return False

        if not self.gives_shared_tiles():
            return False

        return ('worked' in self.ptile and self.ptile['worked'] == 0 and 'specialists' in self.pcity
                and sum(self.pcity['specialists']) > 0 and self.ptile['known'] != 0
                and 'output_food' in self.pcity and self.output_idx is not None)

    """
    logic from freeciv/common/city.c
    func: base_city_can_work_tile & unit_occupies_tile
    """
    def unit_occupies_tile(self):
        tile = self.city_map.map_ctrl.prop_state.tiles[self.ptile['index']]
        units_on_tile = tile['units']
        if len(units_on_tile) == 0:
            return False

        owner_of_units = units_on_tile[0]['owner']
        if owner_of_units != self.cur_player['playerno'] and owner_of_units != 255:
            return True

        return False

    def gives_shared_tiles(self):
        tile_owner = self.ptile['owner']
        if self.cur_player['playerno'] == tile_owner:
            return True

        if tile_owner in self.tiles_shared and self.tiles_shared[tile_owner][self.cur_player['playerno']] == 1:
            return True

        return False

    def get_output_at_tile(self):
        if "output_food" in self.pcity:
            idx = self.output_idx
            output_food = self.pcity['output_food'][idx]
            output_shield = self.pcity['output_shield'][idx]
            output_trade = self.pcity['output_trade'][idx]
            return output_food, output_shield, output_trade

    def _action_packet(self):
        packet = {"pid": packet_city_make_worker,
                  "city_id": self.pcity['id'],
                  "tile_id": self.ptile['index']}
        self.wait_for_pid = [(31, self.pcity['tile']), (15, self.ptile['index'])]
        # self.wait_for_pid = 31
        return packet

    def _refresh_state_packet(self):
        return {"pid": packet_city_refresh,
                "city_id": self.pcity['id']}


class CityUnworkTile(CityWorkTile):
    action_key = "city_unwork"

    def is_action_valid(self):
        if self.city_map.map_ctrl.is_out_of_map(self.ctile['x'] + self.dx, self.ctile['y'] + self.dy):
            return False

        if self.output_idx is None:
            return False

        return ('worked' in self.ptile and self.ptile['worked'] == self.pcity['id']
                and 'output_food' in self.pcity and self.output_idx is not None)

    def _action_packet(self):
        packet = {"pid": packet_city_make_specialist,
                  "city_id": self.pcity['id'],
                  "tile_id": self.ptile['index']}
        self.wait_for_pid = [(31, self.pcity['tile']), (15, self.ptile['index'])]
        # self.wait_for_pid = 31
        return packet


class CityChangeSpecialist(Action):
    action_key = "city_change_specialist"

    def __init__(self, pcity, specialist_num):
        super().__init__()
        self.specialist_num = specialist_num
        self.pcity = pcity
        self.action_key += "_%i" % specialist_num

    def is_action_valid(self):
        return (self.pcity["specialists_size"] > self.specialist_num
                and self.pcity['specialists'][self.specialist_num] > 0)

    def _action_packet(self):
        # from_specialist_id = self.pcity["specialists"][self.specialist_num][id]
        packet = {"pid": packet_city_change_specialist,
                  "city_id": self.pcity["id"],
                  "from": self.specialist_num,
                  "to": (self.specialist_num + 1) % 3}
        self.wait_for_pid = (31, self.pcity['tile'])
        # self.wait_for_pid = 31
        return packet

    def _refresh_state_packet(self):
        return {"pid": packet_city_refresh,
                "city_id": self.pcity['id']}


class CityBuyProduction(Action):
    action_key = "city_buy_production"

    def __init__(self, pcity, pplayer):
        super().__init__()
        self.pcity = pcity
        self.pplayer = pplayer
        self.kind = self.pcity['production_kind']
        self.value = self.pcity['production_value']

    def is_action_valid(self):
        if "buy_cost" not in self.pcity or self.pcity['did_buy']:
            return False
        if self.pcity['production_kind'] == VUT_IMPROVEMENT and self.pcity['production_value'] == 67:
            return False
        if self.pcity['changed_from_kind'] == 0 and self.pcity['changed_from_value'] == 0:
            return False
        if city_unhappy(self.pcity):
            return False

        return self.pplayer['gold'] >= self.pcity['buy_cost'] > 0

    def _action_packet(self):
        """Buy whatever is being built in the city."""
        packet = {"pid": packet_city_buy, "city_id": self.pcity['id']}
        self.wait_for_pid = (31, self.pcity['tile'])
        # self.wait_for_pid = 31
        return packet


class CitySellImprovement(Action):
    """Sell city improvement"""
    action_key = "city_sell_improvement"

    def __init__(self, pcity, improvement_id, improvement_name):
        super().__init__()
        self.pcity = pcity
        self.improvement_id = improvement_id
        self.improvement_name = improvement_name
        self.action_key += "_%s" % improvement_name

    def is_action_valid(self):
        return self.pcity['improvements'][self.improvement_id] == 1

    def _action_packet(self):
        packet = {"pid": packet_city_sell, "city_id": self.pcity['id'],
                  "build_id": self.improvement_id}
        self.wait_for_pid = (31, self.pcity['tile'])
        # self.wait_for_pid = 31
        return packet


class CityChangeProduction(Action):
    """Change city production."""
    action_key = "change_production"

    def __init__(self, pcity, prod_kind, prod_value, prod_name):
        super().__init__()
        self.pcity = pcity
        self.prod_kind = prod_kind
        self.prod_value = prod_value
        self.prod_name = prod_name
        self.action_key += "_%s_%i" % (prod_name, prod_value)

    def is_action_valid(self):
        raise Exception("To be overwritten")

    def _action_packet(self):
        packet = {"pid": packet_city_change, "city_id": self.pcity["id"],
                  "production_kind": self.prod_kind, "production_value": self.prod_value}
        self.wait_for_pid = (31, self.pcity['tile'])
        # self.wait_for_pid = 31
        return packet

    def _refresh_state_packet(self):
        return {"pid": packet_city_refresh,
                "city_id": self.pcity['id']}


class CityChangeUnitProduction(CityChangeProduction):
    action_key = "change_unit_prod"

    def __init__(self, pcity, punit_type):
        super().__init__(pcity, VUT_UTYPE, punit_type["id"], punit_type["name"])
        self.punit_type = punit_type

    def is_action_valid(self):
        if (self.punit_type['name'] == "Barbarian Leader" or
                self.punit_type['name'] == "Leader" or self.pcity['did_buy']):
            return False
        if self.pcity['production_kind'] == self.prod_kind and self.pcity['production_value'] == self.prod_value:
            return False

        return self.can_city_build_unit_now(self.pcity, self.punit_type["id"])

    @staticmethod
    def can_city_build_unit_now(pcity, punittype_id):
        """
          Return whether given city can build given building returns FALSE if
          the building is obsolete.
        """
        return (pcity is not None and pcity['can_build_unit'] is not None and punittype_id < len(pcity['can_build_unit'])
                and pcity['can_build_unit'][punittype_id] > 0)

    def get_impact_of_action(self):
        return dict([(key, self.punit_type[key]) for key in ["name", "helptext", "rule_name",
                                                             "build_cost", "attack_strength",
                                                             "defense_strength", "firepower"]])


class CityChangeImprovementProduction(CityChangeProduction):
    action_key = "change_improve_prod"

    def __init__(self, pcity, pimprovement):
        super().__init__(pcity, VUT_IMPROVEMENT, pimprovement["id"], pimprovement["name"])
        self.pimprovement = pimprovement

    def is_action_valid(self):
        if self.pcity['did_buy'] or self.pimprovement['name'] == "Coinage":
            return False
        if self.pcity['production_kind'] == self.prod_kind and self.pcity['production_value'] == self.prod_value:
            return False

        return self.can_city_build_improvement_now(self.pcity, self.prod_value)

    @staticmethod
    def can_city_build_improvement_now(pcity, pimprove_id):
        """
        Return whether given city can build given building; returns FALSE if
        the building is obsolete.
        """
        return pcity is not None and pcity['can_build_improvement'] is not None and (
            pcity['can_build_improvement'][pimprove_id] > 0
            if pimprove_id < len(pcity['can_build_improvement']) else False)

    def get_impact_of_action(self):
        build_cost = self.pimprovement['build_cost']
        if self.pimprovement['name'] == "Coinage":
            build_cost = "-"

        infos = dict([(key, self.pimprovement[key]) for key in ["name", "helptext", "rule_name"]])
        infos["build_cost"] = build_cost
        return infos


"""
logic from freeciv-web
freeciv-web/freeciv-web/src/main/webapp/javascript/city.js
lines: 1934 - 1939
"""


def city_unhappy(pcity):
    return (pcity['ppl_happy'][FEELING_FINAL] <
            pcity['ppl_unhappy'][FEELING_FINAL] + 2 * pcity['ppl_angry'][FEELING_FINAL])
