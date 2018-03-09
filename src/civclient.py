'''
/**********************************************************************
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

***********************************************************************/
'''

import random
from connectivity.Basehandler import CivPropController
from connectivity.client_state import C_S_PREPARING, ClientState, C_S_RUNNING

from players.player_ctrl import PlayerCtrl, PLRF_AI
from players.diplomacy import DiplomacyCtrl
from players.government import GovernmentCtrl

from game.game_ctrl import GameCtrl
from game.ruleset import RulesetCtrl
from game.options_ctrl import OptionCtrl

from units.unit_ctrl import UnitCtrl
from map.map_ctrl import MapCtrl
from city.city_ctrl import CityCtrl
from research.tech_ctrl import TechCtrl
from utils.fc_events import E_UNDEFINED
from utils.fc_types import packet_nation_select_req, packet_player_phase_done
from utils.freecivlog import freelog

class CivClient(CivPropController):
    def __init__(self, a_bot, user_name, client_port=6001):
        self.ai_skill_level = 3
        self.nation_select_id = -1
        self.bot = a_bot
        self.turn = -1
        self.client_port = client_port
        self.user_name = user_name

        self.game_ctrl = None
        self.opt_ctrl = None
        self.rule_ctrl = None
        self.map_ctrl = None

        self.clstate = None
        self.player_ctrl = None

        self.dipl_ctrl = None
        self.tech_ctrl = None
        self.city_ctrl = None

        self.unit_ctrl = None
        self.gov_ctrl = None

        self.controller_list = {}

    def init_controller(self):
        CivPropController.__init__(self, self.ws_client)

        self.register_handler(25, "handle_chat_msg")
        self.register_handler(28, "handle_early_chat_msg")

        self.register_handler(115, "handle_conn_info")
        self.register_handler(126, "handle_start_phase")
        self.register_handler(125, "handle_end_phase")

        self.register_handler(128, "handle_begin_turn")
        self.register_handler(129, "handle_end_turn")

        self.game_ctrl = GameCtrl(self.ws_client)
        self.opt_ctrl = OptionCtrl(self.ws_client)
        self.rule_ctrl = RulesetCtrl(self.ws_client)
        self.map_ctrl = MapCtrl(self.ws_client, self.rule_ctrl)

        self.clstate = ClientState(self.ws_client, self.rule_ctrl)

        self.dipl_ctrl = DiplomacyCtrl(self.ws_client, self.clstate, self.rule_ctrl, self.bot)
        self.player_ctrl = PlayerCtrl(self.ws_client, self.clstate, self.rule_ctrl, self.dipl_ctrl)

        self.tech_ctrl = TechCtrl(self.ws_client, self.rule_ctrl, self.player_ctrl)
        self.city_ctrl = CityCtrl(self.ws_client, self.rule_ctrl, self.player_ctrl, self.clstate,
                                  self.game_ctrl, self.map_ctrl)

        self.unit_ctrl = UnitCtrl(self.ws_client, self.rule_ctrl, self.map_ctrl,
                                  self.player_ctrl, self.city_ctrl, self.dipl_ctrl)

        self.gov_ctrl = GovernmentCtrl(self.ws_client, self.city_ctrl, self.rule_ctrl)

        self.controller_list = {"game": self.game_ctrl,
                                "rules": self.rule_ctrl,
                                "map": self.map_ctrl,
                                "player": self.player_ctrl,
                                "city": self.city_ctrl,
                                "tech": self.tech_ctrl,
                                "unit": self.unit_ctrl,
                                "options": self.opt_ctrl,
                                "dipl": self.dipl_ctrl,
                                "gov": self.gov_ctrl,
                                "client": self.clstate}
        for ctrl in self.controller_list:
            self.controller_list[ctrl].register_with_parent(self)

    def init_control(self, ws_client):
        """
        When the WebSocket connection is open and ready to communicate, then
        send the first login message to the server.
        """
        self.ws_client = ws_client

        self.init_controller()

        freeciv_version = "+Freeciv.Web.Devel-3.0"
        sha_password = None
        google_user_subject = None

        login_message = {"pid": 4, "username": self.user_name,
                         "capability": freeciv_version, "version_label": "-dev",
                         "major_version" : 2, "minor_version" : 5, "patch_version" : 99,
                         "port": self.client_port, "password" : sha_password,
                         "subject" : google_user_subject}

        self.ws_client.send(login_message)

    def assign_packets(self, p_list):
        """Distributes packets to the handlers of the controllers"""
        if p_list is None:
            return
        try:
            for packet in p_list:
                if packet is None:
                    continue
                self.handle_pack(packet['pid'], packet)
        except Exception:
            raise

    def prepare_game(self):
        names, opts = self.player_ctrl.pregame_getplayer_options()
        if names != []:
            self.pregame_choose_player(opts[0]["name"], opts[0]["playerid"], "pick_nation")

    def pregame_choose_player(self, name, player_id, option="pick_nation"):
        if name == None:
            return
        name = name.split(" ")[0]

        if option != "pick_nation":
            self.ws_client.send_message("/%s %s" % (option, name))
        else:
            self.pregame_choose_nation(player_id)

        self.clstate.pregame_start_game()
        #/* set state of Start game button depending on if user is ready. */

        #self.clstate.update_metamessage_on_gamestart()
        #if self.player_ctrl.is_player_ready():

    def pregame_choose_nation(self, player_id):
        namelist = self.rule_ctrl.get_nation_options()
        nation_name = namelist[random.randint(0, len(namelist))]
        self.submit_nation_choice(nation_name, player_id)

    def submit_nation_choice(self, chosen_nation, choosing_player):
        player_num = self.clstate.player_num()
        if (chosen_nation == -1 or player_num == None
            or choosing_player == None or choosing_player < 0):
            return

        pplayer = self.player_ctrl.get_player(choosing_player)
        pnation = self.rule_ctrl.nations[chosen_nation]

        if pplayer == None:
            return

        leader_name = pplayer['name']

        if pplayer['flags'][PLRF_AI] > 0:
            leader_name = pnation['leader_name'][0]

        style = pnation['style']

        test_packet = {"pid" : packet_nation_select_req,
                       "player_no" : choosing_player,
                       "nation_no" : chosen_nation,
                       "is_male" : True, #/* FIXME */
                       "name" : leader_name,
                       "style" : style}

        self.ws_client.send_request(test_packet)
        #clearInterval(nation_select_id)

    def change_ruleset(self, to):
        #"""Change the ruleset to"""
        
        #send_message("/rulesetdir " + to)
        #// reset some ruleset defined settings.
        #send_message("/set nationset all")
        #submit_nation_choice(chosen_nation, choosing_player)
        raise Exception("Not implemented")

    def handle_early_chat_msg(self, packet):
        """
        Handle an early message packet. Thease have format like other chat
      messages but server sends them only about events related to establishing
      the connection and other setup in the early phase. They are a separate
      packet just so that client knows thse to be already relevant when it's
      only setting itself up - other chat messages might be just something
      sent to all clients, and we might want to still consider ourselves
      "not connected" (not receivers of those messages) until we are fully
      in the game.
        """
        #/* Handle as a regular chat message for now. */
        self.handle_chat_msg(packet)

    def handle_chat_msg(self, packet):
        """#/* 100% complete */"""
        message = packet['message']
        conn_id = packet['conn_id']
        event = packet['event']

        if message is None:
            return
        if event is None or event < 0 or event >= E_UNDEFINED:
            print('Undefined message event type')
            print(packet)
            print("\r\n")
            packet['event'] = event = E_UNDEFINED

        if conn_id in self.clstate.connections:
            message = "<b>" + self.clstate.connections[conn_id]['username'] + ":</b>" + message
        else:
            if "/metamessage" in message:
                return  #//don't spam message dialog on game start.
            if "Metaserver message string" in message:
                return  #//don't spam message dialog on game start.

        packet['message'] = message
        print(packet)
        print("\r\n")

        if "You are logged in as" in message:
            self.prepare_game()

    def handle_start_phase(self, packet):
        """Handle signal from server to start phase - prior to starting turn"""
        print("Starting Phase")
        self.clstate.update_client_state(C_S_RUNNING)

    def handle_end_phase(self, packet):
        #chatbox_clip_messages()
        pass

    def handle_begin_turn(self, packet):
        """Handle signal from server to start turn"""
        
        self.turn += 1
        if self.clstate.client_is_observer() or not self.clstate.is_playing():
            self.send_end_turn()
            return

        pplayer = self.clstate.cur_player()

        self.bot.conduct_turn(pplayer, self.controller_list)
        self.send_end_turn()

    def handle_end_turn(self, packet):
        """Handle signal from server to end turn"""
        #reset_unit_anim_list()
        pass

    def handle_conn_info(self, packet):
        """
            Remove, add, or update dummy connection struct representing some
            connection to the server, with info from packet_conn_info.
            Updates player and game connection lists.
            Calls update_players_dialog() in case info for that has changed.
            99% done.
        """

        pconn = self.clstate.find_conn_by_id(packet['id'])

        if not packet['used']:
            # Forget the connection
            if pconn is None:
                freelog("Server removed unknown connection " + packet['id'])
                return
            self.clstate.client_remove_cli_conn(pconn)
            pconn = None
        else:
            pplayer = self.player_ctrl.valid_player_by_number(packet['player_num'])
            if pplayer == None:
                return
            packet['playing'] = pplayer

            if self.clstate.has_id(packet["id"]):
                self.clstate.init_state(packet)

            self.clstate.conn_list_append(packet)

        if self.clstate.has_id(packet["id"]) and self.clstate.cur_player() != packet['playing']:
            self.clstate.set_client_state(C_S_PREPARING)

        #/* FIXME: not implemented yet.
        #update_players_dialog()
        #update_conn_list_dialog()

    def send_end_turn(self):
        """Ends the current turn."""
        if self.rule_ctrl.game_info == {}:
            return

        packet = {"pid" : packet_player_phase_done, "turn" : self.rule_ctrl.game_info['turn']}
        self.ws_client.send_request(packet)
        #update_turn_change_timer()