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

from math import floor, sqrt

from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.freeciv.map.map_ctrl import MapCtrl

from civrealm.freeciv.utils.base_action import Action, ActionList
from civrealm.freeciv.utils.fc_types import (packet_city_make_specialist, packet_city_change_specialist,
                                             packet_city_make_worker, packet_city_buy, packet_city_sell,
                                             packet_city_change, VUT_UTYPE, VUT_IMPROVEMENT, packet_city_refresh)
from civrealm.freeciv.map.map_ctrl import CityTileMap
import civrealm.freeciv.players.player_const as player_const

MAX_LEN_WORKLIST = 64
MAX_SPECIALISTS = 20

IG_GREAT_WONDER = 0
IG_SMALL_WONDER = 1
IG_IMPROVEMENT = 2
IG_SPECIAL = 3
IG_CONVERT = 4

TILE_UNKNOWN = 0
TILE_KNOWN_UNSEEN = 1
TILE_KNOWN_SEEN = 2


class CityActions(ActionList):
    def __init__(self, ws_client: CivConnection, city_list: dict, rulectrl: RulesetCtrl, map_ctrl: MapCtrl):
        super().__init__(ws_client)
        self.cities = city_list
        self.rulectrl = rulectrl
        self.map_ctrl = map_ctrl
        self.city_map = CityTileMap(1, map_ctrl)

        self.tiles_shared = dict()
        self.turn = {'turn': 1}
        self.city_unhappiness = dict()
        self.diplomacy_states = dict()

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

                    self.add_action(city_id, CityWorkTile(pcity, dx, dy, self.city_map, pplayer, self.rulectrl, self.diplomacy_states))
                    self.add_action(city_id, CityUnworkTile(pcity, dx, dy, self.city_map, pplayer, self.rulectrl, self.diplomacy_states))

            self.add_action(city_id, CityBuyProduction(pcity, pplayer, self.rulectrl, self.turn, self.city_unhappiness))

            for specialist_num in range(pcity['specialists_size']):
                self.add_action(city_id, CityChangeSpecialist(pcity, specialist_num))

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

            """ self.add_action(city_id, CityKeepProduction(pcity, self.ws_client)) """


class CityWorkTile(Action):
    action_key = "city_work"

    def __init__(self, pcity, dx, dy, city_map: CityTileMap, pplayer, rule_ctrl, diplomacy_states):
        super().__init__()
        self.dx = dx
        self.dy = dy
        self.pcity = pcity
        self.cur_player = pplayer
        self.rule_ctrl = rule_ctrl
        self.diplomacy_states = diplomacy_states

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

        if 'worked' in self.ptile and self.ptile['worked'] != 0:
            return False

        if 'specialists' in self.pcity and sum(self.pcity['specialists']) <= 0:
            return False

        if self.ptile['known'] != TILE_KNOWN_SEEN:
            return False

        """
        logic is not complete here
        server func: get_city_tile_output_bonus
        temporarily do not consider working on 'inaccessible' and 'boiling ocean' tiles after getting advanced techs 
        """
        if self.rule_ctrl.terrains[self.ptile['terrain']]['name'].lower() in ['inaccessible', 'boiling ocean']:
            return False

        """
        temporarily do not consider radiating
        for p in self.rule_ctrl.terrains[self.ptile['terrain']]['flags']:
            if (self.rule_ctrl.terrains[self.ptile['terrain']]['flags'][p] == 1 and 
                    self.rule_ctrl.terrain_flag[p]['name'].lower() == 'radiating'):
                return False
        """

        return True

    """
    logic from freeciv/common/city.c
    func: base_city_can_work_tile & unit_occupies_tile
    """

    def unit_occupies_tile(self):
        tile = self.city_map.map_ctrl.prop_state.tiles[self.ptile['index']]
        units_on_tile = tile['units']
        if len(units_on_tile) == 0:
            return False

        for unit in units_on_tile:
            owner_of_unit = unit['owner']

            # diplomacy actions can be done out of player's own phase, thus the tracked diplomacy states may be out of date, making invalid actions cannot be detected in time, thus we assume that a tile with units of other players is not workable, although it is if the other player is not in war with my_player
            """
            if owner_of_unit != self.cur_player['playerno'] and owner_of_unit != 255 and owner_of_unit in self.diplomacy_states and self.diplomacy_states[owner_of_unit] == player_const.DS_WAR:
                return True
            """
            if owner_of_unit != self.cur_player['playerno'] and owner_of_unit != 255:
                return True

        return False

    def gives_shared_tiles(self):
        tile_owner = self.ptile['owner']
        if self.cur_player['playerno'] == tile_owner or tile_owner == 255:
            return True

        """
        gives_shared_tiles in player packet pid = 51 changes very frequently
        
        if tile_owner in self.tiles_shared and self.tiles_shared[tile_owner][self.cur_player['playerno']] == 1:
            return True
        """

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
        return packet

    """
    def _refresh_state_packet(self):
        return {"pid": packet_city_refresh,
                "city_id": self.pcity['id']}
    """


class CityUnworkTile(CityWorkTile):
    action_key = "city_unwork"

    def is_action_valid(self):
        if self.city_map.map_ctrl.is_out_of_map(self.ctile['x'] + self.dx, self.ctile['y'] + self.dy):
            return False

        return ('worked' in self.ptile and self.ptile['worked'] == self.pcity['id']
                and 'output_food' in self.pcity and self.output_idx is not None)

    def _action_packet(self):
        packet = {"pid": packet_city_make_specialist,
                  "city_id": self.pcity['id'],
                  "tile_id": self.ptile['index']}
        self.wait_for_pid = [(31, self.pcity['tile']), (15, self.ptile['index'])]
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
        return packet

    """
    def _refresh_state_packet(self):
        return {"pid": packet_city_refresh,
                "city_id": self.pcity['id']}
    """


class CityBuyProduction(Action):
    action_key = "city_buy_production"

    def __init__(self, pcity, pplayer, rule_ctrl, turn, city_unhappiness):
        super().__init__()
        self.pcity = pcity
        self.pplayer = pplayer
        self.rule_ctrl = rule_ctrl
        self.turn = turn
        self.city_unhappiness = city_unhappiness

    def is_action_valid(self):
        if 'buy_cost' not in self.pcity:
            return False
        if self.pcity['buy_cost'] <= 0:
            return False

        if self.pcity['did_buy']:
            return False

        """ in case self.turn is not consistent with 'turn' from server """
        if self.pcity['turn_founded'] == self.turn['turn'] or self.pcity['changed_from_kind'] == 0:
            return False

        if (self.pcity['production_kind'] == VUT_IMPROVEMENT and
                self.rule_ctrl.improvements[self.pcity['production_value']]['genus'] == IG_CONVERT):
            return False

        """
        if self.kind == VUT_UTYPE and self.pcity['anarchy'] != 0:
            return False
        
        we use city_unhappiness to double check if the city is in disorder as 
        packet = 31 defined here: freeciv/common/networking/packets.def does not have 'anarchy' key
        while 'anarchy' has been added to packet = 31 in our updated docker image
        """
        if self.pcity['production_kind'] == VUT_UTYPE:
            if 'anarchy' in self.pcity and self.pcity['anarchy'] != 0:
                return False
            if self.pcity['id'] in self.city_unhappiness and self.city_unhappiness[self.pcity['id']]:
                return False

        return self.pplayer['gold'] >= self.pcity['buy_cost']

    def _action_packet(self):
        """Buy whatever is being built in the city """
        packet = {"pid": packet_city_buy,
                  "city_id": self.pcity['id']}

        if 'anarchy' in self.pcity or self.city_unhappiness:
            self.wait_for_pid = (31, self.pcity['tile'])
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
        """ already sold something here this turn """
        if self.pcity['did_sell']:
            return False

        return self.pcity['improvements'][self.improvement_id] == 1

    def _action_packet(self):
        packet = {"pid": packet_city_sell,
                  "city_id": self.pcity['id'],
                  "build_id": self.improvement_id}
        self.wait_for_pid = (31, self.pcity['tile'])
        return packet


class CityChangeProduction(Action):
    """Change city production."""
    action_key = "produce"

    def __init__(self, pcity, prod_kind, prod_value, prod_name):
        super().__init__()
        self.pcity = pcity
        self.prod_kind = prod_kind
        self.prod_value = prod_value
        self.prod_name = prod_name
        self.action_key += "_%s" % prod_name

    def is_action_valid(self):
        raise Exception("To be overwritten")

    def _action_packet(self):
        packet = {"pid": packet_city_change,
                  "city_id": self.pcity["id"],
                  "production_kind": self.prod_kind,
                  "production_value": self.prod_value}

        self.wait_for_pid = (31, self.pcity['tile'])
        return packet

    def city_can_change_build(self):
        if self.pcity['did_buy'] and self.pcity['shield_stock'] > 0:
            return False
        return True

    def under_production(self):
        return self.pcity['production_kind'] == self.prod_kind and self.pcity['production_value'] == self.prod_value

    """
    def _refresh_state_packet(self):
        return {"pid": packet_city_refresh,
                "city_id": self.pcity['id']}
    """


class CityChangeUnitProduction(CityChangeProduction):

    def __init__(self, pcity, punit_type):
        super().__init__(pcity, VUT_UTYPE, punit_type["id"], punit_type["name"])
        self.punit_type = punit_type

    def is_action_valid(self):
        if (not self.city_can_change_build() or self.punit_type['name'] == "Barbarian Leader"
                or self.punit_type['name'] == "Leader"):
            return False

        if self.under_production():
            return False

        return self.can_city_build_unit_now(self.pcity, self.punit_type["id"])

    @staticmethod
    def can_city_build_unit_now(pcity, punittype_id):
        """
          Return whether given city can build given building returns FALSE if
          the building is obsolete.
        """
        if 'can_build_unit' in pcity:
            if len(pcity['can_build_unit']) > punittype_id:
                return pcity['can_build_unit'][punittype_id] > 0

        return False

    def get_impact_of_action(self):
        return dict([(key, self.punit_type[key]) for key in ["name", "helptext", "rule_name",
                                                             "build_cost", "attack_strength",
                                                             "defense_strength", "firepower"]])


class CityChangeImprovementProduction(CityChangeProduction):

    def __init__(self, pcity, pimprovement):
        super().__init__(pcity, VUT_IMPROVEMENT, pimprovement["id"], pimprovement["name"])
        self.pimprovement = pimprovement

    def is_action_valid(self):
        if not self.city_can_change_build() or self.under_production():
            return False

        """ may already be included in can_city_build_improvement_now """
        if self.pimprovement['genus'] != IG_CONVERT and self.pcity['improvements'][self.prod_value] == 1:
            return False

        return self.can_city_build_improvement_now(self.pcity, self.prod_value)

    @staticmethod
    def can_city_build_improvement_now(pcity, pimprove_id):
        """
        Return whether given city can build given building; returns FALSE if
        the building is obsolete.
        """
        if 'can_build_improvement' in pcity:
            if len(pcity['can_build_improvement']) > pimprove_id:
                return pcity['can_build_improvement'][pimprove_id] > 0

        return False

    def get_impact_of_action(self):
        build_cost = self.pimprovement['build_cost']
        if self.pimprovement['name'] == "Coinage":
            build_cost = "-"

        infos = dict([(key, self.pimprovement[key]) for key in ["name", "helptext", "rule_name"]])
        infos["build_cost"] = build_cost
        return infos


# TODO: Check if necessary to add this action to action_dict of city
class CityKeepProduction(Action):
    action_key = 'city_keep_production'

    def __init__(self, pcity, ws_client):
        super().__init__()
        self.pcity = pcity
        self.ws_client = ws_client

    def is_action_valid(self):
        """ always valid """
        return True

    def _action_packet(self):
        return 'keep_production'

    def trigger_action(self, ws_client):
        self.ws_client.send_message(f"City {self.pcity['id']} keeps production.")
