"""
    Freeciv-web - the web version of Freeciv. http://play.freeciv.org/
    Copyright (C) 2009-2015  The Freeciv-web project

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from connectivity.Basehandler import CivEvtHandler
from utils.fc_types import O_SCIENCE, O_TRADE, FC_INFINITY, VUT_IMPROVEMENT, VUT_UTYPE,\
    O_LUXURY, O_FOOD, O_SHIELD, O_GOLD, packet_city_buy, packet_city_change,\
    packet_city_sell, packet_city_worklist, packet_city_rename,\
    packet_city_change_specialist, MAX_NUM_ITEMS

from _collections import defaultdict
from math import floor
import urllib
from BitVector import BitVector
from utils.utility import byte_to_bit_array
from utils.freecivlog import freelog
from game_info.ruleset import RulesetCtrl

#/* The city_options enum. */
CITYO_DISBAND      = 0
CITYO_NEW_EINSTEIN = 1
CITYO_NEW_TAXMAN   = 2
CITYO_LAST         = 3

FEELING_BASE = 0        #/* before any of the modifiers below */
FEELING_LUXURY = 1        #/* after luxury */
FEELING_EFFECT = 2        #/* after building effects */
FEELING_NATIONALITY = 3      #/* after citizen nationality effects */
FEELING_MARTIAL = 4    #/* after units enforce martial order */
FEELING_FINAL = 5        #/* after wonders (final result) */

MAX_LEN_WORKLIST = 64
B_LAST = MAX_NUM_ITEMS
INCITE_IMPOSSIBLE_COST = 1000 * 1000 * 1000

class CityCtrl(CivEvtHandler):
    def __init__(self, ws_client=None,ruleset=None, player_ctrl=None, clstate=None, game_ctrl=None,
                 map_ctrl=None):
        CivEvtHandler.__init__(self, ws_client)

        #self.register_handler(13, "handle_scenario_description")
        self.cities = {}
        self.city_trade_routes = {}
        self.player_ctrl = player_ctrl
        self.game_ctrl = game_ctrl
        self.rulectrl = ruleset
        self.map_ctrl = map_ctrl
        self.clstate = clstate
        self.city_state = CityState(ruleset)

        self.active_city = None
        self.active_city_state = {}

        self.worklist_dialog_active = False
        self.production_selection = []
        self.worklist_selection = []
        self.city_prod_clicks = 0

        self.register_handler(30, "handle_city_remove")
        self.register_handler(31, "handle_city_info")
        self.register_handler(32, "handle_city_short_info")
        self.register_handler(256, "handle_web_city_info_addition")
        self.register_handler(249, "handle_traderoute_info")

    def get_current_state(self, pplayer):
        player_cities = {}

        for city_id in self.cities:
            pcity = self.cities[city_id]
            if pcity["owner"] == pplayer["playerno"]:
                player_cities[city_id] = self.city_state.get_full_state(pcity)

        player_cities["civ_pop"] = self.civ_population(self.clstate.cur_player()["playerno"])
        return player_cities

    def tile_city(self, ptile):
        """Return the city on this tile (or NULL), checking for city center."""
        if ptile is None:
            return None

        city_id = ptile['worked']
        if city_id in self.cities:
            pcity = self.cities[city_id]
            if CityState.is_city_center(pcity, ptile):
                return pcity
        return None

    def get_unit_homecity_name(self, punit):
        """Returns the name of the unit's homecity."""

        if punit['homecity'] != 0 and self.cities[punit['homecity']] != None:
            return urllib.unquote(self.cities[punit['homecity']]['name'])
        else:
            return None

    def remove_city(self, pcity_id):
        """Removes a city from the game_info"""
        if pcity_id is None or self.player_ctrl.cur_player is None:
            return

        pcity = self.cities[pcity_id]
        if pcity is None:
            return

        update = self.player_ctrl.cur_player.playerno and \
                 self.player_ctrl.city_owner(pcity).playerno == self.player_ctrl.cur_player.playerno

        del self.cities[pcity_id]

    def govern_cities(self):
        for city in self.cities:
            self.active_city = city
            self.govern_active_city()

    def calculate_new_worklist(self):
        pass

    def calculate_additional_actions(self):
        city_actions = [self.request_city_buy,
                        self.rename_city,
                        #self.city_sell_improvements
                        ]

    def govern_active_city(self):
        """ Return all data about the city """

        self.city_prod_clicks = 0
        self.production_selection = []
        self.worklist_selection = []

        tmp = CityState(self.rulectrl)
        self.active_city_state = tmp.get_full_state(self.active_city)

        self.calculate_new_worklist()
        self.calculate_additional_actions()
        """
        for punit in tile_units(city_tile(pcity)):
            self.unit_ctrl.govern_unit(punit)
            #get_unit_city_info(punit)
            #city_dialog_activate_unit(

        for sunit in get_supported_units(pcity):
            self.unit_ctrl.govern_unit(sunit)
        """
        """
        #/* Handle citizens and specialists */
        citizen_types = ["angry", "unhappy", "content", "happy"]

        for citizen in citizen_types:
            if pcity['ppl_' + citizen] is None:
                continue
            for i in range(pcity['ppl_' + citizen][FEELING_FINAL]):
                sprite = get_specialist_image_sprite("citizen." + citizen + "_" + (i % 2))


        for u in range('specialists_size'):
            spec_type_name = specialists[u]['plural_name']
            spec_gfx_key = "specialist." + specialists[u]['rule_name'] + "_0"

        """
        """
      $("#specialist_panel").html(specialist_html)

      $('#disbandable_city').off()
      $('#disbandable_city').prop('checked',
                                  pcity['city_options'] != None and pcity['city_options'].isSet(CITYO_DISBAND))
      $('#disbandable_city').click(function() {
        var options = pcity['city_options']
        var packet = {
          "pid"     : packet_city_options_req,
          "city_id" : active_city['id'],
          "options" : options.raw
        }

        /* Change the option value referred to by the packet. */
        if ($('#disbandable_city').prop('checked')) {
          options.set(CITYO_DISBAND)
        } else {
          options.unset(CITYO_DISBAND)
        }

        /* Send the (now updated) city options. */
        send_request(JSON.stringify(packet))

      })

      if (is_small_screen()) {
       $(".ui-tabs-anchor").css("padding", "2px")
      }
        """

    def request_city_buy(self):
        """Show buy production in city dialog"""
        pcity = self.active_city
        pplayer = self.player_ctrl.cur_player

        #// reset dialog page.
        buy_price_string = ""
        buy_question_string = ""

        if pcity['production_kind'] == VUT_UTYPE:
            punit_type = self.rulectrl.unit_types[pcity['production_value']]
            if punit_type != None:
                buy_price_string = punit_type['name'] + " costs " + pcity['buy_gold_cost'] + " gold."
                buy_question_string = "Buy " + punit_type['name'] + " for " + pcity['buy_gold_cost'] + " gold?"
        else:
            improvement = self.rulectrl.improvements[pcity['production_value']]
            if improvement != None:
                buy_price_string = improvement['name'] + " costs " + pcity['buy_gold_cost'] + " gold."
                buy_question_string = "Buy " + improvement['name'] + " for " + pcity['buy_gold_cost'] + " gold?"

        treasury_text = "<br>Treasury contains " + pplayer['gold'] + " gold."

        if pcity['buy_gold_cost'] > pplayer['gold']:
            freelog("Buy It!" + buy_price_string + treasury_text)
            return

    def city_sell_improvement(self, improvement_id):
        packet = {"pid" : packet_city_sell, "city_id" : self.active_city['id'],
                  "build_id": improvement_id}
        self.ws_client.send_request(packet)

    def send_city_buy(self):
        """Buy whatever is being built in the city."""
        if self.active_city != None:
            packet = {"pid" : packet_city_buy, "city_id" : self.active_city['id']}
            self.ws_client.send_request(packet)

    def send_city_change(self, city_id, kind, value):
        """Change city production."""

        packet = {"pid" : packet_city_change, "city_id" : city_id,
                  "production_kind": kind, "production_value" : value}
        self.ws_client.send_request(packet)

    def send_city_worklist(self, city_id):
        """Notifies the server about a change in the city worklist."""

        worklist = self.cities[city_id]['worklist']
        overflow = worklist.length - MAX_LEN_WORKLIST
        if overflow > 0:
            worklist = worklist[:MAX_LEN_WORKLIST-1]

        packet = {"pid"     : packet_city_worklist,
                 "city_id" : city_id,
                 "worklist": worklist}
        self.ws_client.send_request(packet)

    def send_city_worklist_add(self, city_id, kind, value):
        pcity = self.cities[city_id]
        if len(pcity['worklist']) >= MAX_LEN_WORKLIST:
            return

        pcity['worklist'].append({"kind" : kind, "value" : value})
        self.send_city_worklist(city_id)


    def city_change_production(self):
        if len(self.production_selection) == 1:
            self.send_city_change(self.active_city['id'],
                                  self.production_selection[0].kind,
                                  self.production_selection[0].value)

    def city_add_to_worklist(self):
        if len(self.production_selection) > 0:
            self.active_city['worklist'].update(self.production_selection)
            self.send_city_worklist(self.active_city['id'])

    """
    def do_city_map_click(ptile):
    {
      var packet = None
      var c_tile = index_to_tile(active_city['tile'])
      if (ptile['worked'] == active_city['id']) {
        packet = {"pid" : packet_city_make_specialist,
                 "city_id" : active_city['id'],
                     "worker_x" : ptile['x'],
             "worker_y" : ptile['y']}
      } else {
        packet = {"pid" : packet_city_make_worker,
                 "city_id" : active_city['id'],
                     "worker_x" : ptile['x'],
             "worker_y" : ptile['y']}
      }
      send_request(JSON.stringify(packet))

    }
    """

    def rename_city(self, suggested_name):
        """Rename a city"""
        if self.active_city is None:
            return
        packet = {"pid" : packet_city_rename,
                  "name" : urllib.quote(unicode(suggested_name).encode('utf-8')),
                  "city_id" : self.active_city['id'] }
        self.ws_client.send_request(packet)


    def city_change_specialist(self, city_id, from_specialist_id):
        packet = {"pid": packet_city_change_specialist,
                        "city_id" : city_id,
                        "from" : from_specialist_id,
                        "to" : (from_specialist_id + 1) % 3}
        self.ws_client.send_request(packet)

    def get_city_traderoutes(self, pcity):
        """Shows traderoutes of active city"""

        trade_data = defaultdict(list)

        routes = self.city_trade_routes[pcity['id']]

        if self.active_city['traderoute_count'] != 0 and routes is None:
            #/* This city is supposed to have trade routes. It doesn't.  */
            print("Can't find the trade routes " + pcity['name'] + " is said to have")
            return

        for i in range(pcity['traderoute_count']):
            if routes[i] is None:
                continue
            tcity_id = routes[i]['partner']

            if tcity_id == 0 or tcity_id is None:
                continue

            good = self.rulectrl.goods[routes[i]['goods']]
            if good is None:
                print("Missing good type " + routes[i]['goods'])
                good = {'name': "Unknown"}

            tcity = self.cities[tcity_id]
            if tcity is None:
                continue

            trade_data["trade_"+good['name']].append((tcity['name'], routes[i]['value']))

        return trade_data

    def handle_city_remove(self, packet):
        self.remove_city(packet['city_id'])

    def handle_traderoute_info(self, packet):
        """  A traderoute-info packet contains information about one end of a traderoute"""
        if self.city_trade_routes[packet['city']] is None:
            #This is the first trade route received for this city.
            self.city_trade_routes[packet['city']] = {}

        self.city_trade_routes[packet['city']][packet['index']] = packet

    def handle_city_info(self, packet):
        """
          The city_info packet is used when the player has full information about a
          city, including it's internals.

          It is followed by web_city_info_addition that gives additional
          information only needed by Freeciv-web. Its processing will therefore
          stop while it waits for the corresponding web_city_info_addition packet.
        """
        #/* Decode the city name. */
        packet['name'] = urllib.unquote(packet['name'])

        #/* Decode bit vectors. */
        packet['improvements'] = BitVector(bitlist = byte_to_bit_array(packet['improvements']))
        packet['city_options'] = BitVector(bitlist = byte_to_bit_array(packet['city_options']))

        if packet['id'] not in self.cities:
            self.cities[packet['id']] = packet
            """
            if (C_S_RUNNING == client_state() and !observing and benchmark_start == 0
                and client.conn.playing != None and packet['owner'] == client.conn.playing.playerno) {
              show_city_dialog_by_id(packet['id'])
            }
            """
        else:
            self.cities[packet['id']].update(packet)


        self.map_ctrl.set_tile_worked(packet)
        #/* manually update tile relation.*/

    #Stop the processing here. Wait for the web_city_info_addition packet.
    #The processing of this packet will continue once it arrives. */

    def handle_web_city_info_addition(self, packet):
        """
        The web_city_info_addition packet is a follow up packet to
          city_info packet. It gives some information the C clients calculates on
          their own. It is used when the player has full information about a city,
          including it's internals.
        """

        if packet["id"] not in self.cities[packet['id']]:
            #/* The city should have been sent before the additional info. */
            print("packet_web_city_info_addition for unknown city ", packet['id'])
            return
        else:
            # Merge the information from web_city_info_addition into the recently
            # received city_info.
            self.cities[packet['id']].update(packet)

    def city_can_buy(self, pcity):
        improvement = self.rulectrl.improvements[pcity['production_value']]

        return (not pcity['did_buy'] and
                pcity['turn_founded'] != self.game_ctrl.game_info['turn'] and
                improvement['name'] != "Coinage")

    def handle_city_short_info(self, packet):
        """
        /* 99% complete
       TODO: does this loose information? */
        """
        #/* Decode the city name. */
        packet['name'] = urllib.unquote(packet['name'])

        #/* Decode bit vectors. */
        packet['improvements'] = BitVector(bitlist = byte_to_bit_array(packet['improvements']))

        if not (packet['id'] in self.cities):
            self.cities[packet['id']] = packet
        else:
            self.cities[packet['id']].update(packet)

    def find_city_by_number(self, cid):
        return self.cities[cid]

    def civ_population(self, playerno):
        """
          Count the # of thousand citizen in a civilisation.
        """
        population = 0
        for city_id in self.cities:
            pcity = self.cities[city_id]
            if playerno == pcity['owner']:
                population += CityState.city_population(pcity)
        return population * 1000

    def player_has_wonder(self, playerno, improvement_id):
        """returns true if the given player has the given wonder (improvement)"""
        for city_id in self.cities:
            pcity = self.cities[city_id]
            if (self.player_ctrl.city_owner(pcity).playerno == playerno and
                self.rulectrl.city_has_building(pcity, improvement_id)):
                return True
        return False

class CityState():
    def __init__(self, ruleset):
        self.rulectrl = ruleset

    def get_full_state(self, pcity):
        cur_state = {}

        for cp in ["id", "size", "food_stock", "granary_size",
                   "granary_turn", "production_kind", "production_value"]:
            if cp in pcity:
                cur_state[cp] = pcity[cp]
            else:
                cur_state[cp] = None

        cur_state["name"] = pcity['name']

        cur_state["luxury"] = pcity['prod'][O_LUXURY]
        cur_state["science"] = pcity['prod'][O_SCIENCE]

        for str_item, o_item in [("food", O_FOOD), ("gold", O_GOLD),
                                 ("shield", O_SHIELD), ("trade", O_TRADE)]:
            cur_state["prod_"+str_item] = pcity['prod'][o_item]
            cur_state["surplus_"+str_item] = pcity['surplus'][o_item]

        cur_state["bulbs"] = pcity["prod"][O_SHIELD]
        cur_state["city_waste"] = pcity['waste'][O_SHIELD]
        cur_state["city_corruption"] = pcity['waste'][O_TRADE]
        cur_state["city_pollution"] = pcity['pollution']
        cur_state["state"] = CityState.get_city_state(pcity)
        try:
            cur_state["growth_in"] = CityState.city_turns_to_growth_text(pcity)
        except:
            cur_state["growth_in"] = None
        cur_state["turns_to_prod_complete"] = self.get_city_production_time(pcity)
        cur_state["prod_process"] = self.get_production_progress(pcity)
        """
        cur_state["impr_int"] = {}
        cur_state["impr_name"] = {}

        for z in range(self.rulectrl.ruleset_control["num_impr_types"]):
            imp_name = self.rulectrl.improvements[z]['name']
            cur_state["impr_int"][z] = False
            cur_state["impr_name"][imp_name] = False

            if 'improvements' in pcity and pcity['improvements'][z]==1:
                cur_state["impr_int"][z] = True
                cur_state["impr_name"][imp_name] = True
        """
    @staticmethod
    def is_city_center(city, tile):
        return (city['tile'] == tile['index'])

    @staticmethod
    def is_free_worked(city, tile):
        return (city['tile'] == tile['index'])

    @staticmethod
    def city_owner_player_id(pcity):
        if pcity is None:
            return None
        return pcity['owner']

    def does_city_have_improvement(self, pcity, improvement_name):
        if pcity is None or pcity['improvements'] is None:
            return False

        for z in range(self.rulectrl.ruleset_control["num_impr_types"]):
            if pcity['improvements'] != None and \
               pcity['improvements'].isSet(z) and \
               self.rulectrl.improvements[z] != None and \
               self.rulectrl.improvements[z]['name'] == improvement_name:
                return True
        return False

    @staticmethod
    def city_turns_to_build(pcity, target, include_shield_stock):
        """
         Calculates the turns which are needed to build the requested
         improvement in the city.  GUI Independent.
        """

        city_shield_surplus =  pcity['surplus'][O_SHIELD]
        city_shield_stock = pcity['shield_stock'] if include_shield_stock else 0
        cost = RulesetCtrl.universal_build_shield_cost(target)

        if include_shield_stock and (pcity['shield_stock'] >= cost):
            return 1
        elif ( pcity['surplus'][O_SHIELD] > 0):
            return floor((cost - city_shield_stock - 1) / city_shield_surplus + 1)
        else:
            return FC_INFINITY

    def get_city_production_time(self, pcity):
        """Returns the number of turns to complete current city production."""

        if pcity is None:
            return FC_INFINITY

        if pcity['production_kind'] == VUT_UTYPE:
            punit_type = self.rulectrl.unit_types[pcity['production_value']]
            return self.city_turns_to_build(pcity, punit_type, True)

        if pcity['production_kind'] == VUT_IMPROVEMENT:
            improvement = self.rulectrl.improvements[pcity['production_value']]
            if improvement['name'] == "Coinage":
                return FC_INFINITY
            return self.city_turns_to_build(pcity, improvement, True)

        return FC_INFINITY

    @staticmethod
    def city_turns_to_growth_text(pcity):
        """Create text describing city growth."""
        turns = pcity['granary_turns']

        if turns == 0:
            return "blocked"
        elif turns > 1000000:
            return "never"
        elif turns < 0:
            return "Starving in " + abs(turns) + " turns"
        else:
            return turns + " turns"

    @staticmethod
    def city_population(pcity):
        """Returns how many thousand citizen live in this city."""
        #/*  Sum_{i=1}^{n} i  ==  n*(n+1)/2  */
        return pcity['size'] * (pcity['size'] + 1) * 5

    @staticmethod
    def get_city_state(pcity):
        """Returns the city state: Celebrating, Disorder or Peace."""
        if pcity is None:
            return
        if pcity['was_happy'] and pcity['size'] >= 3:
            return "Celebrating"
        elif pcity['unhappy']:
            return "Disorder"
        else:
            return "Peace"

    @staticmethod
    def is_wonder(improvement):
        return improvement['soundtag'][0] == 'w'

    def get_production_progress(self, pcity):
        """ Returns city production progress, eg. the string "5 / 30"""

        if pcity is None:
            return FC_INFINITY

        if pcity['production_kind'] == VUT_UTYPE:
            punit_type = self.rulectrl.unit_types[pcity['production_value']]
            return  pcity['shield_stock'] / RulesetCtrl.universal_build_shield_cost(punit_type)

        if pcity['production_kind'] == VUT_IMPROVEMENT:
            improvement = self.rulectrl.improvements[pcity['production_value']]
            if improvement['name'] == "Coinage":
                return FC_INFINITY
            return  pcity['shield_stock'] / RulesetCtrl.universal_build_shield_cost(improvement)

        return FC_INFINITY

class CityProduction():
    def __init__(self, pcity, ruleset):
        self.cur_city = pcity
        self.production_list = self.generate_production_list(pcity)
        self.worklist_selection = self.get_worklist(pcity)
        self.rulectrl = ruleset

    def generate_production_list(self, pcity):
        production_list = []

        for unit_type_id in self.rulectrl.unit_types:
            punit_type = self.rulectrl.unit_types[unit_type_id]
            #/* FIXME: web client doesn't support unit flags yet, so this is a hack: */
            if punit_type['name'] == "Barbarian Leader" or punit_type['name'] == "Leader":
                continue

            if CityProduction.can_city_build_unit_now(pcity, punit_type):
                production_list.append({"kind": VUT_UTYPE,
                                        "value" : punit_type['id'],
                                        "text" : punit_type['name'],
    	                                "helptext" : punit_type['helptext'],
                                        "rule_name" : punit_type['rule_name'],
                                        "build_cost" : punit_type['build_cost'],
                                        "unit_details" : punit_type['attack_strength'] + ", "
                                                     + punit_type['defense_strength'] + ", "
                                                     + punit_type['firepower'],
                                        })

        for improvement_id in self.rulectrl.improvements:
            pimprovement = self.rulectrl.improvements[improvement_id]
            if CityProduction.can_city_build_improvement_now(pcity, pimprovement):
                build_cost = pimprovement['build_cost']
                if pimprovement['name'] == "Coinage":
                    build_cost = "-"

                production_list.append({"kind": VUT_IMPROVEMENT,
                                      "value" : pimprovement['id'],
                                      "text" : pimprovement['name'],
    	                              "helptext" : pimprovement['helptext'],
                                      "rule_name" : pimprovement['rule_name'],
                                      "build_cost" : build_cost,
                                      "unit_details" : "-",
                                      "sprite" : None})
        return production_list

    @staticmethod
    def can_city_build_unit_direct(pcity, punittype):
        """
            Return whether given city can build given unit, ignoring whether unit
            is obsolete.
        """
        #/* TODO: implement*/
        return True

    @staticmethod
    def can_city_build_unit_now(pcity, pimprove):
        """
          Return whether given city can build given building returns FALSE if
          the building is obsolete.
        """

        return (pcity != None and pcity['can_build_improvement'] != None and
                pcity['can_build_improvement'][pimprove['id']] == "1")

    @staticmethod
    def can_city_build_improvement_now(pcity, pimprove_id):
        """
        Return whether given city can build given building; returns FALSE if
        the building is obsolete.
        """
        return  pcity != None and pcity['can_build_improvement'] != None and \
              pcity['can_build_improvement'][pimprove_id] == "1"

    @staticmethod
    def worklist_not_empty(pcity):
        return pcity['worklist'] != None and len(pcity['worklist']) != 0

    @staticmethod
    def workitem_is_valid(workitem):
        return not (workitem["kind"] is None or workitem["value"] is None or len(workitem) == 0)

    def get_worklist(self, pcity):
        """Populates data to the production tab in the city dialog."""
        universals_list = []

        if pcity is None:
            return

        if not self.worklist_not_empty(pcity):
            return

        work_list = pcity['worklist']
        for work_item in work_list:
            kind = work_item['kind']
            value = work_item['value']
            if not self.workitem_is_valid(work_item):
                continue
            push_base = None

            if kind == VUT_IMPROVEMENT:
                push_base = self.rulectrl.improvements[value]
            elif kind == VUT_UTYPE:
                push_base = self.rulectrl.unit_types[value]
            else:
                return None

            build_cost = push_base['build_cost']
            if push_base['name'] == "Coinage":
                build_cost = "-"

            universals_list.append({"name" : push_base['name'],
                                    "helptext" : push_base['helptext'],
                                    "build_cost" : build_cost})
        return universals_list

        """
        value = parseFloat($(this).data('value'))
        kind = parseFloat($(this).data('kind'))
        if city_prod_clicks == 0:
            send_city_change(pcity['id'], kind, value)
        else:
            send_city_worklist_add(pcity['id'], kind, value)
        city_prod_clicks += 1

        handle_worklist_select,
        handle_worklist_unselect
        handle_current_worklist_click
        handle_current_worklist_direct_remove
        """

    @staticmethod
    def find_universal_in_worklist(universal, worklist):
        for i, work_item in enumerate(worklist):
            if (work_item.kind == universal.kind and
                work_item.value == universal.value):
                return i
        return -1
    """
    def handle_worklist_select(self, kind, value):
        selected = {"kind":kind, "value": value}
        idx = CityProduction.find_universal_in_worklist(selected, self.production_list)
        if idx < 0:
            self.production_list.append(selected)
            self.update_worklist_actions()

    def handle_worklist_unselect(self, kind, value):
        selected = {"kind":kind, "value": value}
        idx = CityProduction.find_universal_in_worklist(selected, self.production_selist)
        if idx >= 0:
            del self.production_list[idx]
            self.update_worklist_actions()

    def handle_current_worklist_select(self, idx):
        for i in range(len(self.worklist_selection))[::-1]:
            if i < 0 or self.worklist_selection[i] < idx:
                self.worklist_selection.splice(i + 1, 0, idx)
                self.update_worklist_actions()

    def handle_current_worklist_unselect(self, idx):
        #Handles the removal of an item from the selection in the tasklist.
        for i in range(len(self.worklist_selection))[::-1]:
            if i >= 0 and self.worklist_selection[i] == idx:
                self.worklist_selection.splice.splice(i, 1)
                self.update_worklist_actions()
    """
