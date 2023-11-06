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


import sys
import numpy as np
from collections import OrderedDict
from BitVector import BitVector

from civrealm.freeciv.connectivity.civ_connection import CivConnection

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.utils.utility import byte_to_bit_array
from civrealm.freeciv.utils.base_action import NoActions
from civrealm.freeciv.utils.freeciv_logging import fc_logger

from civrealm.freeciv.game.info_states import RuleState
from civrealm.freeciv.tech.tech_helpers import recreate_old_tech_req

"""
Freeciv Web Client.
This file contains the handling-code for packets from the civserver.
"""


class RulesetCtrl(CivPropController):
    def __init__(self, ws_client: CivConnection):
        super().__init__(ws_client)

        self.terrains = {}
        self.terrain_flag = {}
        self.resources = {}
        self.unit_types = {}

        self.unit_types_list = []
        self.unit_costs_list = []

        self.unit_classes = {}

        self.specialists = {}
        self.techs = {}
        self.actions = {}
        self.governments = {}
        self.goods = {}
        self.game_info = {}
        self.game_rules = {}
        self.ruleset_control = {}
        self.ruleset_summary = None
        self.ruleset_description = None
        self.terrain_control = None
        self.city_rules = {}
        self.improvements = {}

        self.improvement_types_list = []
        self.improvement_costs_list = []

        self.nation_groups = None
        self.nations = OrderedDict()
        self.effects = {}
        self.extras = {}

        self.prop_state = RuleState(self.game_info)
        self.prop_actions = NoActions(ws_client)

        self.ground_unit_transporter = ['Trireme', 'Caravel', 'Galleon', 'Frigate', 'Transport']
        self.missile_unit_transporter = ['Submarine']
        self.air_unit_transporter = ['Carrier']

        self.air_units = ['Fighter', 'Bomber', 'AWACS', 'Helicopter', 'Stealth_Fighter', 'Stealth_Bomber']
        self.missile_units = ['Cruise_Missile', 'Nuclear']
        self.ground_units = [
            'Settlers', 'Workers', 'Engineers', 'Warriors', 'Phalanx', 'Archers', 'Legion', 'Pikemen', 'Musketeers',
            'Partisan', 'Alpine_Troops', 'Riflemen', 'Marines', 'Paratroopers', 'Mech._Inf.', 'Horsemen', 'Chariot',
            'Knights', 'Dragoons', 'Cavalry', 'Armor', 'Catapult', 'Cannon', 'Artillery', 'Howitzer', 'Diplomat', 'Spy',
            'Caravan', 'Freight', 'Explorer']

    def register_all_handlers(self):
        self.register_handler(9, "handle_ruleset_tech_class")

        self.register_handler(140, "handle_ruleset_unit")
        self.register_handler(141, "handle_ruleset_game")
        self.register_handler(142, "handle_ruleset_specialist")
        self.register_handler(143, "handle_ruleset_government_ruler_title")
        self.register_handler(144, "handle_ruleset_tech")
        self.register_handler(145, "handle_ruleset_government")
        self.register_handler(146, "handle_ruleset_terrain_control")
        self.register_handler(147, "handle_ruleset_nation_groups")
        self.register_handler(148, "handle_ruleset_nation")
        self.register_handler(149, "handle_ruleset_city")

        self.register_handler(150, "handle_ruleset_building")
        self.register_handler(151, "handle_ruleset_terrain")
        self.register_handler(152, "handle_ruleset_unit_class")
        self.register_handler(153, "handle_ruleset_base")
        self.register_handler(155, "handle_ruleset_control")

        self.register_handler(161, "handle_single_want_hack_reply")
        self.register_handler(162, "handle_ruleset_choices")

        self.register_handler(175, "handle_ruleset_effect")
        self.register_handler(177, "handle_ruleset_resource")

        self.register_handler(220, "handle_ruleset_road")
        self.register_handler(224, "handle_ruleset_disaster")
        self.register_handler(225, "handle_rulesets_ready")
        self.register_handler(226, "handle_ruleset_extra_flag")
        self.register_handler(227, "handle_ruleset_trade")
        self.register_handler(228, "handle_ruleset_unit_bonus")
        self.register_handler(229, "handle_ruleset_unit_flag")

        self.register_handler(230, "handle_ruleset_unit_class_flag")
        self.register_handler(231, "handle_ruleset_terrain_flag")
        self.register_handler(232, "handle_ruleset_extra")
        self.register_handler(233, "handle_ruleset_achievement")
        self.register_handler(234, "handle_ruleset_tech_flag")
        self.register_handler(235, "handle_ruleset_action_enabler")
        self.register_handler(236, "handle_ruleset_nation_sets")
        self.register_handler(237, "handle_nation_availability")

        self.register_handler(239, "handle_ruleset_style")
        self.register_handler(240, "handle_ruleset_music")
        # self.register_handler(243, "handle_ruleset_multiplier")
        self.register_handler(246, "handle_ruleset_action")
        self.register_handler(247, "handle_ruleset_description_part")
        self.register_handler(248, "handle_ruleset_goods")
        self.register_handler(251, "handle_ruleset_summary")
        self.register_handler(252, "handle_ruleset_action_auto")

        self.register_handler(16, "handle_game_info")
        self.register_handler(127, "handle_new_year")
        self.register_handler(260, "handle_web_ruleset_unit_addition")

    def handle_ruleset_terrain(self, packet):
        # These two hacks are there since Freeciv-web doesn't support rendering Lake and Glacier correctly.
        if packet['name'] == "Lake":
            packet['graphic_str'] = packet['graphic_alt']
        if packet['name'] == "Glacier":
            packet['graphic_str'] = "tundra"

        self.terrains[packet['id']] = packet
        self.terrains[packet['id']]['output'] = np.array(self.terrains[packet['id']]['output'], dtype=np.ushort)
        self.terrains[packet['id']]['flags'] = byte_to_bit_array(packet['flags'])

    def handle_ruleset_resource(self, packet):
        self.resources[packet['id']] = packet
        self.resources[packet['id']]['output'] = np.array(self.resources[packet['id']]['output'], dtype=np.ushort)

    def handle_ruleset_control(self, packet):
        """
        Handle the ruleset control packet.
        This is the first ruleset packet the server sends.
        """
        self.ruleset_control = packet

        # Clear out any effects belonging to the previous ruleset
        self.effects = {}

        # Clear out the description of the previous ruleset
        self.ruleset_summary = None
        self.ruleset_description = None

    def handle_ruleset_summary(self, packet):
        """
        Ruleset summary.
        """
        self.ruleset_summary = packet['text']

    def handle_ruleset_description_part(self, packet):
        """
        Receive next part of the ruleset description.
        """

        if self.ruleset_description == None:
            self.ruleset_description = packet['text']
        else:
            self.ruleset_description += packet['text']

    def handle_ruleset_unit(self, packet):
        if packet['name'] != None:
            if '?unit:' in packet['name']:
                packet['name'] = packet['name'].replace('?unit:', '')

            self.unit_types[packet['id']] = packet
            # if packet['transport_capacity'] > 0:
            # print(packet)
            # print('\n')
            if packet['id'] >= len(self.unit_types_list):
                self.unit_types_list += [None] * (packet['id'] - len(self.unit_types_list) + 1)
                self.unit_costs_list += [None] * (packet['id'] - len(self.unit_costs_list) + 1)
            self.unit_types_list[packet['id']] = packet['name']
            self.unit_costs_list[packet['id']] = packet['build_cost']

    def handle_ruleset_game(self, packet):
        self.game_rules = packet

    def handle_ruleset_specialist(self, packet):
        self.specialists[packet['id']] = packet

    def handle_ruleset_government_ruler_title(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_tech(self, packet):
        packet['name'] = packet['name'].replace("?tech:", "")
        self.techs[packet['id']] = packet
        recreate_old_tech_req(packet)

    def handle_ruleset_tech_class(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_tech_flag(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_government(self, packet):
        self.governments[packet['id']] = packet

    def handle_ruleset_terrain_control(self, packet):
        self.terrain_control = packet

        # /* Separate since it is easier understand what SINGLE_MOVE means than to
        # * understand what terrain_control['move_fragments'] means. */
        self.SINGLE_MOVE = self.terrain_control['move_fragments']

    def handle_ruleset_nation_groups(self, packet):
        self.nation_groups = packet['groups']

    def handle_ruleset_nation(self, packet):
        self.nations[packet['id']] = packet

    def handle_ruleset_city(self, packet):
        self.city_rules[packet['style_id']] = packet

    def handle_ruleset_building(self, packet):
        self.improvements[packet['id']] = packet

        if packet['id'] >= len(self.improvement_types_list):
            self.improvement_types_list += [None] * (packet['id'] - len(self.improvement_types_list) + 1)
            self.improvement_costs_list += [None] * (packet['id'] - len(self.improvement_costs_list) + 1)
        self.improvement_types_list[packet['id']] = packet['name']
        self.improvement_costs_list[packet['id']] = packet['build_cost']

    def handle_ruleset_unit_class(self, packet):
        self.unit_classes[packet['id']] = packet

    def handle_ruleset_disaster(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_trade(self, packet):
        pass
        # /* TODO: implement*/

    def handle_rulesets_ready(self, packet):
        pass
        # /* TODO: implement*/

    def handle_single_want_hack_reply(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_choices(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_effect(self, packet):

        eff_type = packet["effect_type"]
        if not eff_type in self.effects.keys():
            # This is the first effect of this type
            self.effects[eff_type] = []

        self.effects[eff_type].append(packet)

    def handle_ruleset_unit_flag(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_unit_class_flag(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_unit_bonus(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_terrain_flag(self, packet):
        self.terrain_flag[packet['id']] = packet

    def handle_ruleset_achievement(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_action(self, packet):
        """
        Receive a generalized action.
        """
        self.actions[packet['id']] = packet

    def handle_ruleset_action_auto(self, packet):
        """
        Handle an action auto performer rule.
        """
        pass
        # /* TODO: implement*/

    def handle_ruleset_goods(self, packet):
        self.goods[packet['id']] = packet

    def handle_ruleset_extra(self, packet):
        """
          Packet handle_ruleset_extra handler. Also defines EXTRA_* variables
          dynamically.
        """
        self.extras[packet['id']] = packet
        self.extras[packet['name']] = packet

        setattr(sys.modules[__name__], ("EXTRA_" + packet['name']).upper(), packet['id'])

        if packet['name'] == "Railroad":
            setattr(sys.modules[__name__], "EXTRA_RAIL", packet['id'])
        if packet['name'] == "Oil Well":
            setattr(sys.modules[__name__], "EXTRA_OIL_WELL", packet['id'])
        if packet['name'] == "Village":
            setattr(sys.modules[__name__], "EXTRA_HUT", packet['id'])
        if packet['name'] == "Farmland":
            setattr(sys.modules[__name__], "EXTRA_IRRIGATION", packet['id'])

    def handle_ruleset_extra_flag(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_base(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_road(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_action_enabler(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_nation_sets(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_style(self, packet):
        pass
        # /* TODO: implement*/

    def handle_nation_availability(self, packet):
        pass
        # /* TODO: implement*/

    def handle_ruleset_music(self, packet):
        pass
        # /* TODO: implement*/

    def unittype_ids_alphabetic(self):
        """Returns a list containing the unittype ids sorted by unittype name."""

        unittype_names = [(unit_id, self.unit_types[unit_id]['name'])
                          for unit_id in self.unit_types.keys()]

        unit_type_id_list = sorted(unittype_names, key=lambda x: x[1])

        return [x[0] for x in unit_type_id_list]

    def tile_terrain(self, ptile):
        return self.terrains[ptile['terrain']]

    def is_ocean_tile(self, ptile):
        pterrain = self.tile_terrain(ptile)
        return (pterrain['graphic_str'] == "floor" or pterrain['graphic_str'] == "coast")

    def unit_type(self, unit):
        """Returns the type of the unit."""
        return self.unit_types[unit['type']]

    def unit_type_id_by_name(self, type_name):
        """Returns the type of the unit."""
        for unit_type_id, unit_type in self.unit_types.items():
            if unit_type['name'] == type_name:
                return unit_type_id
        return None

    def get_nation_options(self):
        """Shows the pick nation dialog."""
        # /* prepare a list of flags and nations. */
        nation_name_list = []
        for nation_id in self.nations:
            pnation = self.nations[nation_id]
            if pnation['is_playable']:
                nation_name_list.append(nation_id)
        fc_logger.debug("Available nations: " + str(nation_name_list))
        fc_logger.debug("Number of nations: " + str(len(self.nations)))
        return nation_name_list

    @staticmethod
    def ruledir_from_ruleset_name(ruleset_name, fall_back_dir):
        """Returns the ruleset directory of the ruleset based on its name."""
        # HACK: find current ruleset dir based on its name.
        rname = ruleset_name.lower()
        if "ruleset" in ruleset_name:
            rname = ruleset_name.split(" ")[0]

        if rname in ["classic", "civ2civ3", "multiplayer", "webperimental"]:
            return rname
        else:
            fc_logger.warning("Don't know the ruleset dir of \"" + ruleset_name
                              + "\". Guessing \"" + fall_back_dir + "\".")
            return fall_back_dir

    @staticmethod
    def tile_set_terrain(ptile, pterrain):
        ptile['terrain'] = pterrain

    def city_has_building(self, pcity, improvement_id):
        for z in range(self.ruleset_control["num_impr_types"]):
            if 'improvements' in pcity and pcity['improvements'][z] == 1 and z == improvement_id:
                return True
        return False

    def get_units_from_tech(self, tech_id):
        result = []
        for unit_type_id in self.unit_types:
            punit_type = self.unit_types[unit_type_id]
            for req in punit_type["build_reqs"]:
                if (req['kind'] == 1) & (req["value"] == tech_id):
                    result.append(punit_type)
        return result

    def get_improvements_from_tech(self, tech_id):
        """Returns a list containing improvement buildings which are available from a tech."""
        result = []
        for improvement_id in self.improvements:
            pimprovement = self.improvements[improvement_id]
            reqs = self.get_improvement_requirements(pimprovement)
            for req in reqs:
                if req == tech_id:
                    result.append(pimprovement)
        return result

    def get_improvement_requirements(self, improvement):
        """returns list of tech ids which are a requirement for the given improvement"""
        result = []
        if improvement != None and improvement['reqs'] != None:
            for req in improvement['reqs']:
                if req['kind'] == 1 and req['present']:
                    result.append(req['value'])
        return result

    @staticmethod
    def universal_build_shield_cost(target):
        """Return the number of shields it takes to build this universal."""
        return target['build_cost']

    def handle_game_info(self, packet):
        self.game_info.update(packet)

    def handle_new_year(self, packet):
        self.game_info['year'] = packet['year']
        # /* TODO: Support calender fragments. */
        self.game_info['fragments'] = packet['fragments']
        self.game_info['turn'] = packet['turn']

    def handle_web_ruleset_unit_addition(self, packet):
        utype_actions = BitVector(bitlist=byte_to_bit_array(packet['utype_actions']))
        self.unit_types[packet['id']]['utype_actions'] = utype_actions
