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
from BitVector.BitVector import BitVector

from connectivity.Basehandler import CivEvtHandler
from utils.fc_types import O_FOOD, O_SHIELD, O_GOLD, ACTION_SPY_INCITE_CITY, ACTION_SPY_INCITE_CITY_ESC,\
    ACTION_UPGRADE_UNIT, ACTION_COUNT, ACTION_SPY_BRIBE_UNIT, ACT_DEC_NOTHING,\
    ACT_DEC_PASSIVE, packet_unit_get_actions, packet_unit_sscs_set,\
    USSDT_UNQUEUE

from units.spacerace import SpaceCtrl
from units.action_dialog import action_prob_possible
from units.unit_action import UnitActionCtrl, FocusUnit

from game_info.game import IDENTITY_NUMBER_ZERO
from players.diplomacy import DS_ALLIANCE, DS_TEAM
from mapping.map import DIR8_NORTH, DIR8_NORTHEAST, DIR8_EAST, DIR8_SOUTHEAST,\
    DIR8_SOUTHWEST, DIR8_WEST, DIR8_SOUTH, DIR8_STAY

class UnitCtrl(CivEvtHandler):
    def __init__(self, ws_client, rule_ctrl, map_ctrl, player_ctrl, city_ctrl, dipl_ctrl):
        CivEvtHandler.__init__(self, ws_client)
        self.units = {}
        self.rule_ctrl = rule_ctrl
        self.map_ctrl = map_ctrl
        self.player_ctrl = player_ctrl
        self.city_ctrl = city_ctrl
        self.dipl_ctrl = dipl_ctrl
        self.unit_action_ctrl = UnitActionCtrl(ws_client, map_ctrl, city_ctrl, rule_ctrl,
                                               self)
        self.space_ctrl = SpaceCtrl(ws_client, player_ctrl)

        self.register_handler(62, "handle_unit_remove")
        self.register_handler(63, "handle_unit_info")
        self.register_handler(64, "handle_unit_short_info")
        self.register_handler(65, "handle_unit_combat_info")
        self.register_handler(85, "handle_unit_action_answer")
        self.register_handler(90, "handle_unit_actions")

        self.register_handler(45, "handle_city_sabotage_list")

        self.register_handler(18, "handle_nuke_tile_info")
        self.register_handler(241, "handle_worker_task")
        self.register_handler(258, "handle_goto_path")

        self.unit_action_ctrl.register_with_parent(self)
        self.space_ctrl.register_with_parent(self)

    def get_current_state(self, pplayer):
        """
            Function returns the current state of all units of player pplayer
        """
        player_units = {}
        for unit_id in self.units.keys():
            punit = self.units[unit_id]

            if self.unit_owner(punit) == pplayer:
                player_units[unit_id] = self._get_unit_infos(punit)
        return player_units

    def get_current_options(self, pplayer):
        """
            Returns the action options for all units of player pplayer
        """
        player_unit_options = {}

        if self.player_ctrl.clstate.client_is_observer():
            return player_unit_options

        for unit_id in self.units.keys():
            punit = self.units[unit_id]
            if self.unit_owner(punit) == pplayer:
                ptile = self.map_ctrl.index_to_tile(punit['tile'])
                if ptile is None:
                    continue
                move_dirs = [DIR8_NORTH, DIR8_NORTHEAST, DIR8_EAST, DIR8_SOUTHEAST,
                             DIR8_SOUTH, DIR8_SOUTHWEST, DIR8_WEST, DIR8_NORTHEAST]

                player_unit_options[unit_id] = self.get_unit_order_commands(punit, ptile, DIR8_STAY)
                for dir8 in move_dirs:
                    player_unit_options[unit_id].update(self.get_unit_order_commands(punit, ptile, dir8))


        return player_unit_options

    def get_unit_order_commands(self, punit, ptile, dir8=DIR8_STAY):
        """Enables and disables the correct units commands for the unit in focus."""
        ptype = self.rule_ctrl.unit_type(punit)
        pplayer = self.player_ctrl.clstate.cur_player()

        newtile = self.map_ctrl.mapstep(ptile, dir8) if dir8 != DIR8_STAY else ptile

        pcity = self.city_ctrl.tile_city(newtile)

        self.unit_action_ctrl.set_current_focus(punit, ptype, newtile, pcity, pplayer)
        unit_actions = self.unit_action_ctrl.get_action_options(dir8)

        return unit_actions

    def trigger_action(self, unit_id, a_action, target_tile=None):
        """
            Triggers action for unit punit and action a_action
        """
        punit = self._idex_lookup_unit(unit_id)
        self.unit_action_ctrl.trigger_action(punit, a_action, target_tile)

    def _get_unit_infos(self, aunit):
        unit_state = {}

        ptype = self.rule_ctrl.unit_type(aunit)
        unit_state["type"] = {}
        #name, helptext, attack_strength, defense_strength, firepower
        unit_state["type"].update(ptype)
        unit_state["can_transport"] = ptype['transport_capacity'] > 0
        unit_state["home_city"] = self.city_ctrl.get_unit_homecity_name(aunit)
        unit_state["moves_left"] = self.get_unit_moves_left(aunit)
        unit_state["health"] = aunit['hp']
        unit_state["veteran"] = aunit['veteran']
        return unit_state

    def unit_owner(self, punit):
        """return player object for player owning punit"""
        return self.player_ctrl.player_by_number(punit['owner'])

    def get_supported_units(self, pcity):
        """Returns a list of units supported by this city."""
        if pcity is None:
            return None
        result = []
        for unit_id in self.units.keys():
            punit = self.units[unit_id]
            if punit['homecity'] == pcity['id']:
                result.append(punit)

        return result

    def _idex_lookup_unit(self, uid):
        """ Return unit object for unit_id uid"""
        if uid in self.units.keys():
            return self.units[uid]
        else:
            return None

    def _player_find_unit_by_id(self, pplayer, unit_id):
        """
         If the specified player owns the unit with the specified id,
         return pointer to the unit struct.  Else return NULL.
         Uses fast idex_lookup_city.

         pplayer may be NULL in which case all units registered to
         hash are considered - even those not currently owned by any
         player. Callers expect this behavior.
        """
        punit = self._idex_lookup_unit(unit_id)

        if punit is None:
            return None

        if pplayer != None or self.unit_owner(punit) == pplayer:
            return punit

        return None

    def _update_tile_unit(self, punit):
        """
        Updates the index of which units can be found on a tile.
        Note: This must be called after a unit has moved to a new tile.
        See: clear_tile_unit()
        """
        if punit is None:
            return

        ptile = self.map_ctrl.index_to_tile(punit['tile'])
        tile_units = FocusUnit.tile_units(ptile)

        if tile_units is None:
            return

        for tile_unit in tile_units:
            if tile_unit['id'] == punit['id']:
                break
        else:
            ptile['units'].append(punit)

    @staticmethod
    def unit_list_size(unit_list):
        """Returns the length of the unit list"""
        if unit_list is None:
            return 0
        else:
            return len(unit_list)

    @staticmethod
    def get_unit_moves_left(punit):
        """Returns a string saying how many moves a unit has left."""
        if punit is None:
            return 0

        return punit['movesleft']

    def unit_has_goto(self, punit):
        """ don't show goto activity for enemy units. I'm not 100% sure this is correct."""
        pplayer = self.player_ctrl.cur_player

        if pplayer is None or punit['owner'] != pplayer.playerno:
            return False

        return punit['goto_tile'] != -1

    def get_unit_city_info(self, punit):
        """Returns a text about the unit to be shown in the city dialog, containing
         unit type name, home city, upkeep."""

        ptype = self.rule_ctrl.unit_type(punit)

        ptype['name']

        if punit['upkeep'] != None:
            punit['upkeep'][O_FOOD]
            punit['upkeep'][O_SHIELD]
            punit['upkeep'][O_GOLD]

        self.get_unit_moves_left(punit)

        home_city = self.city_ctrl.get_unit_homecity_name(punit)
        if home_city != None:
            pass

    def find_unit_by_number(self, uid):
        """
          Find unit out of all units in game_info: now uses fast idex method,
          instead of looking through all units of all players.
        """
        if uid in self.units.keys():
            return self.units[uid]
        else:
            return None

    def unit_distance_compare(self, unit_a, unit_b):
        if unit_a is None or unit_b is None:
            return 0
        ptile_a = self.map_ctrl.index_to_tile(unit_a['tile'])
        ptile_b = self.map_ctrl.index_to_tile(unit_b['tile'])

        if ptile_a is None or ptile_b is None:
            return 0

        if ptile_a['x'] == ptile_b['x'] and ptile_a['y'] == ptile_b['y']:
            return 0
        elif ptile_a['x'] > ptile_b['x'] or ptile_a['y'] > ptile_b['y']:
            return 1
        else:
            return -1

    #-------------------Functions for removing a unit----------------------------
    def handle_unit_remove(self, packet):
        """
          Handle a remove-unit packet, sent by the server to tell us any time a
          unit is no longer there.                             99% complete.
        """
        punit = self.find_unit_by_number(packet['unit_id'])
        if punit is None:
            return

        #/* TODO: Close diplomat dialog if the diplomat is lost */
        #/* TODO: Notify agents. */
        self._clear_tile_unit(punit)
        self._client_remove_unit(punit)

    def _client_remove_unit(self, punit):
        #if self.unit_action_ctrl.unit_is_in_focus(punit):
        #    self.unit_action_ctrl.clear_focus()

        del self.units[punit['id']]

    def _clear_tile_unit(self, punit):
        """
            Updates the index of which units can be found on a tile.
            Note: This must be called before a unit has moved to a new tile.
        """
        if punit is None:
            return
        ptile = self.map_ctrl.index_to_tile(punit['tile'])
        if ptile is None or ptile['units'] is None:
            return -1

        idx = ptile['units'].index(punit)
        if idx >= 0:
            del ptile['units'][idx]

    def handle_city_sabotage_list(self, packet):
        """
          Handle the response the a request asking what buildings a potential
          victim of targeted sabotage city victim.
        """
        popup_sabotage_dialog(self.find_unit_by_number(packet['diplomat_id']),
                              self.city_ctrl.find_city_by_number(packet['city_id']),
                              BitVector(bitlist = packet['improvements']),
                              packet['action_id'])

    def handle_unit_info(self, packet):
        self.handle_unit_packet_common(packet)

    def handle_unit_short_info(self, packet):
        """/* 99% complete FIXME: does this loose information? */"""
        self.handle_unit_packet_common(packet)


    def handle_unit_packet_common(self, packet_unit):
        """
        Called to do basic handling for a unit_info or short_unit_info packet.

        Both owned and foreign units are handled you may need to check unit
        owner, or if unit equals focus unit, depending on what you are doing.

        Note: Normally the server informs client about a new "activity" here.
        For owned units, the new activity can be a result of:
        - The player issued a command (a request) with the client.
        - The server side AI did something.
        - An enemy encounter caused a sentry to idle. (See "Wakeup Focus").

        Depending on what caused the change, different actions may be taken.
        Therefore, this def is a bit of a jungle, and it is advisable
        to read thoroughly before changing.

        Exception: When the client puts a unit in focus, it's status is set to
        idle immediately, before informing the server about the new status. This
        is because the server can never deny a request for idle, and should not
        be concerned about which unit the client is focusing on.
        """

        punit = self._player_find_unit_by_id(self.unit_owner(packet_unit), packet_unit['id'])
        self._clear_tile_unit(punit)

        game_unit = self.find_unit_by_number(packet_unit['id'])

        if punit is None and game_unit != None:
            # This means unit has changed owner. We deal with this here
            # by simply deleting the old one and creating a new one. */
            self.handle_unit_remove(packet_unit['id'])


        old_tile = None
        if punit != None:
            old_tile = self.map_ctrl.index_to_tile(punit['tile'])

        if not packet_unit['id'] in self.units:
            #This is a new unit. */
            self.unit_actor_wants_input(packet_unit)
            packet_unit['anim_list'] = []
            self.units[packet_unit['id']] = packet_unit
            self.units[packet_unit['id']]['facing'] = 6
        elif not ('action_decision_want' in self.units[packet_unit['id']]) or \
             self.units[packet_unit['id']]['action_decision_want'] != packet_unit['action_decision_want']:
            #The unit's action_decision_want has changed. */
            self.unit_actor_wants_input(packet_unit)

        self.units[packet_unit['id']].update(packet_unit)

        self._update_tile_unit(self.units[packet_unit['id']])
        """
        if current_focus.length > 0 and current_focus[0]['id'] == packet_unit['id']:
            update_active_units_dialog()
            update_unit_order_commands()

        if current_focus[0]['done_moving'] != packet_unit['done_moving']:
            update_unit_focus()
        """
        #TODO: update various dialogs and mapview. */

    def unit_actor_wants_input(self, pdiplomat):
        """Handle server request for user input about diplomat action to do."""

        if not self.player_ctrl.clstate.can_client_control():
            return

        if not 'action_decision_want' in pdiplomat or \
           pdiplomat['owner'] != self.player_ctrl.clstate.cur_player()['playerno']:
            #/* No authority to decide for this unit. */
            return

        if pdiplomat['action_decision_want'] == ACT_DEC_NOTHING:
            #/* The unit doesn't want a decision. */
            return

        if pdiplomat['action_decision_want'] == ACT_DEC_PASSIVE:
            #/* The player isn't interested in getting a pop up for a mere
            #* arrival. */
            return

        self.process_diplomat_arrival(pdiplomat, pdiplomat['action_decision_tile'])

    def process_diplomat_arrival(self, pdiplomat, target_tile_id):
        """
          /* No queue. An action selection dialog is opened at once. If multiple
           * action selection dialogs are open at once one will hide all others.
           * The hidden dialogs are based on information from the time they
           * were opened. It is therefore more outdated than it would have been if
           * the server was asked the moment before the action selection dialog
           * was shown.
           *
           * The C client's bundled with Freeciv asks right before showing the
           * action selection dialog. They used to have a custom queue for it.
           * Freeciv patch #6601 (SVN r30682) made the desire for an action
           * decision a part of a unit's data. They used it to drop their custom
           * queue and move unit action decisions to the unit focus queue.
        """

        ptile = self.map_ctrl.index_to_tile(target_tile_id)
        if pdiplomat != None and ptile != None:
            """Ask the server about what actions pdiplomat can do. The server's
             * reply will pop up an action selection dialog for it.
            """
        packet = {
          "pid" : packet_unit_get_actions,
          "actor_unit_id" : pdiplomat['id'],
          "target_unit_id" : IDENTITY_NUMBER_ZERO,
          "target_tile_id": target_tile_id,
          "disturb_player": True
          }
        self.ws_client.send_request(packet)

    def handle_unit_combat_info(self, packet):
        attacker = self.units[packet['attacker_unit_id']]
        defender = self.units[packet['defender_unit_id']]
        attacker_hp = packet['attacker_hp']
        defender_hp = packet['defender_hp']

    def handle_unit_action_answer(self, packet):
        """Handle the requested follow up question about an action"""

        diplomat_id = packet['diplomat_id']
        target_id = packet['target_id']
        cost = packet['cost']
        action_type = packet['action_type']

        target_city = self.city_ctrl.find_city_by_number(target_id)
        actor_unit = self.find_unit_by_number(diplomat_id)

        if actor_unit is None:
            print("Bad actor unit (" + diplomat_id
                        + ") in unit action answer.")
            return

        if action_type == ACTION_SPY_BRIBE_UNIT:
            target_unit = self.find_unit_by_number(target_id)
            if target_unit is None:
                print("Bad target unit (" + target_id + ") in unit action answer.")
                return
            else:
                popup_bribe_dialog(actor_unit, target_unit, cost, action_type)
                return
        elif (action_type == ACTION_SPY_INCITE_CITY
             or action_type == ACTION_SPY_INCITE_CITY_ESC):
            if target_city is None:
                print("Bad target city (" + target_id + ") in unit action answer.")
                return
            else:
                popup_incite_dialog(actor_unit, target_city, cost, action_type)
                return
        elif action_type == ACTION_UPGRADE_UNIT:
            if target_city is None:
                print("Bad target city (" + target_id + ") in unit action answer.")
                return
            else:
                popup_unit_upgrade_dlg(actor_unit, target_city, cost, action_type)
                return

        elif action_type == ACTION_COUNT:
            print("unit_action_answer: Server refused to respond.")
        else:
            print("unit_action_answer: Invalid answer.")

    def handle_unit_actions(self, packet):
        """Handle server reply about what actions an unit can do."""

        actor_unit_id = packet['actor_unit_id']
        target_unit_id = packet['target_unit_id']
        target_city_id = packet['target_city_id']
        target_tile_id = packet['target_tile_id']
        action_probabilities = packet['action_probabilities']
        disturb_player = packet['disturb_player']

        pdiplomat = self.find_unit_by_number(actor_unit_id)
        target_unit = self.find_unit_by_number(target_unit_id)
        target_city = self.city_ctrl.find_city_by_number(target_city_id)
        ptile = self.map_ctrl.index_to_tile(target_tile_id)

        hasActions = False

        #/* The dead can't act. */
        if pdiplomat != None and ptile != None:
            for prob in action_probabilities:
                if action_prob_possible(prob):
                    hasActions = True

        if disturb_player:
            """
            /* Clear the unit's action_decision_want. This was the reply to a
             * foreground request caused by it. Freeciv-web doesn't save open
             * action selection dialogs. It doesn't even wait for any other action
             * selection dialog to be answered before requesting data for the next
             * one. This lack of a queue allows it to be cleared here. */
            """
            unqueue = {
                      "pid"     : packet_unit_sscs_set,
                      "unit_id" : actor_unit_id,
                      "type"    : USSDT_UNQUEUE,
                      "value"   : IDENTITY_NUMBER_ZERO
                      }
            self.ws_client.send_request(unqueue)

        if hasActions and disturb_player:

            action_options = self.unit_action_ctrl.get_disturbed_action_options(
                                                         pdiplomat, action_probabilities,
                                                         ptile, target_unit, target_city)
        elif hasActions:
            #/* This was a background request. */
            #/* No background requests are currently made. */
            print("Received the reply to a background request I didn't do.")


    def handle_worker_task(self, packet):
        #TODO: Implement */
        pass

    def handle_nuke_tile_info(self, packet):
        pass

    def can_actor_unit_move(self, actor_unit, target_tile):
        """Returns true unless a situation were a regular move always would be
        impossible is recognized."""
        idx = self.map_ctrl.index_to_tile
        if idx(actor_unit['tile']) == target_tile:
            #/* The unit is already on this tile. */
            return False

        if (-1 == self.map_ctrl.get_direction_for_step(idx(actor_unit['tile']),
                                                       target_tile)):
            #/* The target tile is too far away. */
            return False

        for tile_unit in target_tile['units']:
            tgt_owner_id = self.unit_owner(tile_unit)['playerno']

            if (tgt_owner_id != self.unit_owner(actor_unit)['playerno'] and
                self.dipl_ctrl.check_not_dipl_states(tgt_owner_id, [DS_ALLIANCE, DS_TEAM])):
                #/* Can't move to a non allied foreign unit's tile. */
                return False

        if self.city_ctrl.tile_city(target_tile) != None:
            tgt_owner_id = self.player_ctrl.city_owner(self.city_ctrl.tile_city(target_tile))['playerno']

            if tgt_owner_id == self.unit_owner(actor_unit)['playerno']:
                #This city isn't foreign. */
                return True

            if self.dipl_ctrl.check_in_dipl_states(tgt_owner_id, [DS_ALLIANCE, DS_TEAM]):
                #/* This city belongs to an ally. */
                return True

            return False

        """/* It is better to show the "Keep moving" option one time to much than
            * one time to little. */"""
        return True
