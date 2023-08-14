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

from collections import defaultdict
import urllib
from BitVector import BitVector

from freeciv_gym.freeciv.utils.base_controller import CivPropController
from freeciv_gym.freeciv.utils.fc_types import MAX_NUM_ITEMS
from freeciv_gym.freeciv.utils.utility import byte_to_bit_array

from freeciv_gym.freeciv.city.city_state import CityState
from freeciv_gym.freeciv.city.city_actions import CityActions

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger

# /* The city_options enum. */
CITYO_DISBAND = 0
CITYO_NEW_EINSTEIN = 1
CITYO_NEW_TAXMAN = 2
CITYO_LAST = 3

B_LAST = MAX_NUM_ITEMS
INCITE_IMPOSSIBLE_COST = 1000 * 1000 * 1000


class CityCtrl(CivPropController):
    def __init__(self, ws_client=None, ruleset=None, clstate=None, game_ctrl=None,
                 map_ctrl=None):
        super().__init__(ws_client)

        # self.register_handler(13, "handle_scenario_description")
        self.cities = {}
        self.city_trade_routes = {}
        self.game_ctrl = game_ctrl
        self.rulectrl = ruleset
        self.map_ctrl = map_ctrl
        self.clstate = clstate

        self.prop_state = CityState(ruleset, self.cities)
        self.prop_actions = CityActions(ws_client, ruleset, self.cities, map_ctrl)

    def register_all_handlers(self):
        self.register_handler(30, "handle_city_remove")
        self.register_handler(31, "handle_city_info")
        self.register_handler(32, "handle_city_short_info")
        self.register_handler(256, "handle_web_city_info_addition")
        self.register_handler(249, "handle_traderoute_info")
        self.register_handler(46, "handle_city_nationalities")
        self.register_handler(138, "handle_city_rally_point")
        self.register_handler(514, "handle_city_update_counters")

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
            return urllib.parse.unquote(self.cities[punit['homecity']]['name'])
        else:
            return None

    def remove_city(self, pcity_id):
        """Removes a city from the game"""
        if pcity_id is None or pcity_id not in self.cities:
            return

        self.prop_actions.remove_actor(pcity_id)
        del self.cities[pcity_id]

    def get_city_traderoutes(self, pcity):
        """Get traderoutes of city pcity"""

        trade_data = defaultdict(list)
        if self.city_trade_routes == {} or pcity["id"] not in self.city_trade_routes:
            return {}

        routes = self.city_trade_routes[pcity['id']]

        if pcity['traderoute_count'] != 0 and routes is None:
            # /* This city is supposed to have trade routes. It doesn't.  */
            fc_logger.info("Can't find the trade routes " + pcity['name'] + " is said to have")
            return

        for i in range(pcity['traderoute_count']):
            if routes[i] is None:
                continue
            tcity_id = routes[i]['partner']

            if tcity_id == 0 or tcity_id is None:
                continue

            good = self.rulectrl.goods[routes[i]['goods']]
            if good is None:
                fc_logger.info("Missing good type " + routes[i]['goods'])
                good = {'name': "Unknown"}

            tcity = self.cities[tcity_id]
            if tcity is None:
                continue

            trade_data["trade_"+good['name']].append((tcity['name'], routes[i]['value']))

        return trade_data

    def handle_city_update_counters(self, packet):
        fc_logger.info(packet)

    def handle_city_rally_point(self, packet):
        fc_logger.info(packet)

    def handle_city_nationalities(self, packet):
        fc_logger.info(packet)

    def handle_city_remove(self, packet):
        self.remove_city(packet['city_id'])

    def handle_traderoute_info(self, packet):
        """  A traderoute-info packet contains information about one end of a traderoute"""
        if packet['city'] not in self.city_trade_routes:
            # This is the first trade route received for this city.
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
        # /* Decode the city name. */
        packet['name'] = urllib.parse.unquote(packet['name'])
        # /* Decode bit vectors. */
        packet['improvements'] = BitVector(bitlist=byte_to_bit_array(packet['improvements']))
        packet['city_options'] = BitVector(bitlist=byte_to_bit_array(packet['city_options']))

        # logger.info("handle_city_info packet: ", packet)

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

        # logger.info("handle_city_info self.cities: ", self.cities)
        self.map_ctrl.set_tile_worked(packet)
        # /* manually update tile relation.*/

    # TODO_NEW: every time a city is built, the packet 31 will be sent twice, and the info is different, e.g., the output trade. Should find out why

    # Stop the processing here. Wait for the web_city_info_addition packet.
    # The processing of this packet will continue once it arrives. */

    def handle_web_city_info_addition(self, packet):
        """
        The web_city_info_addition packet is a follow up packet to
          city_info packet. It gives some information the C clients calculates on
          their own. It is used when the player has full information about a city,
          including it's internals.
        """

        packet['can_build_unit'] = BitVector(bitlist=byte_to_bit_array(packet['can_build_unit']))
        packet['can_build_improvement'] = BitVector(bitlist=byte_to_bit_array(packet['can_build_improvement']))

        # logger.info("handle_web_city_info_addition packet: ", packet)
        if packet["id"] not in self.cities:
            # /* The city should have been sent before the additional info. */
            fc_logger.info("packet_web_city_info_addition for unknown city ", packet['id'])
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
        # /* Decode the city name. */
        packet['name'] = urllib.parse.unquote(packet['name'])

        # /* Decode bit vectors. */
        packet['improvements'] = BitVector(bitlist=byte_to_bit_array(packet['improvements']))

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

    '''
    def player_has_wonder(self, playerno, improvement_id):
        """returns true if the given player has the given wonder (improvement)"""
        for city_id in self.cities:
            pcity = self.cities[city_id]
            if (self.player_ctrl.city_owner(pcity)["playerno"] == playerno and
                    self.rulectrl.city_has_building(pcity, improvement_id)):
                return True
        return False
    '''
