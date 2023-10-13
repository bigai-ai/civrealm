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

from BitVector.BitVector import BitVector

from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.game.options_ctrl import OptionCtrl
from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.freeciv.players.diplomacy_state_ctrl import DiplomacyCtrl
from civrealm.freeciv.map.map_ctrl import MapCtrl
from civrealm.freeciv.city.city_ctrl import CityCtrl
from civrealm.freeciv.players.player_ctrl import PlayerCtrl

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.units.spacerace import SpaceCtrl
from civrealm.freeciv.units.action_dialog import action_prob_possible
from civrealm.freeciv.utils.fc_types import O_FOOD, O_SHIELD, O_GOLD, ACTION_SPY_INCITE_CITY, ACTION_SPY_INCITE_CITY_ESC,\
    ACTION_UPGRADE_UNIT, ACTION_COUNT, ACTION_SPY_BRIBE_UNIT, ACT_DEC_ACTIVE, ACT_DEC_NOTHING,\
    ACT_DEC_PASSIVE, packet_unit_get_actions, packet_unit_sscs_set,\
    USSDT_UNQUEUE, USSDT_QUEUE, ACTION_FOUND_CITY

from civrealm.freeciv.game.game_ctrl import IDENTITY_NUMBER_ZERO
import civrealm.freeciv.players.player_const as player_const
from civrealm.freeciv.units.unit_actions import UnitActions, UnitAction, FocusUnit
from civrealm.freeciv.units.unit_state import UnitState
import urllib
import re
import civrealm.freeciv.utils.fc_types as fc_types
from civrealm.freeciv.utils.freeciv_logging import fc_logger

# TODO: update the below list after meets more unit type and terrain.
# The units on land
LAND_UNIT = ['Warriors', 'Explorer', 'Workers', 'Settlers']
LAND_UNIT_INACCESS_TERRAIN = [0, 2, 3]

REQEST_PLAYER_INITIATED = 0
REQEST_BACKGROUND_REFRESH = 1
REQEST_BACKGROUND_FAST_AUTO_ATTACK = 2


class UnitCtrl(CivPropController):
    def __init__(
            self, ws_client: CivConnection, option_ctrl: OptionCtrl, rule_ctrl: RulesetCtrl, map_ctrl: MapCtrl,
            player_ctrl: PlayerCtrl, city_ctrl: CityCtrl, dipl_ctrl: DiplomacyCtrl):
        super().__init__(ws_client)
        self.units = {}
        self.rule_ctrl = rule_ctrl
        self.map_ctrl = map_ctrl
        self.player_ctrl = player_ctrl
        self.city_ctrl = city_ctrl
        self.dipl_ctrl = dipl_ctrl
        self.option_ctrl = option_ctrl

        self.base_action = UnitAction(None)

        self.prop_state = UnitState(self, rule_ctrl, map_ctrl, city_ctrl)
        self.prop_actions = UnitActions(ws_client, self, rule_ctrl, player_ctrl, map_ctrl, city_ctrl)

        self.space_ctrl = SpaceCtrl(ws_client, player_ctrl)

        # self.unit_action_ctrl.register_with_parent(self)
        self.space_ctrl.register_with_parent(self)
        # store city name to prevent duplicate city names which can cause error
        self.city_name_list = []

    def register_all_handlers(self):
        self.register_handler(44, "handle_city_name_suggestion_info")

        self.register_handler(62, "handle_unit_remove")
        self.register_handler(63, "handle_unit_info")
        self.register_handler(64, "handle_unit_short_info")
        self.register_handler(65, "handle_unit_combat_info")
        self.register_handler(85, "handle_unit_action_answer")
        self.register_handler(90, "handle_unit_actions")

        self.register_handler(45, "handle_city_sabotage_list")

        self.register_handler(18, "handle_nuke_tile_info")
        self.register_handler(241, "handle_worker_task")
        # self.register_handler(258, "handle_goto_path")

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

    def my_units_have_type(self, type_name: str):
        """Check if my units has the type of unit."""
        unit_type_id = self.rule_ctrl.unit_type_id_by_name(type_name)

        for _, punit in self.units.items():
            if punit['owner'] == self.player_ctrl.my_player_id and punit['type'] == unit_type_id:
                return True
        return False

    def have_attack_unit(self):
        """Check if my units have attack unit."""
        for _, punit in self.units.items():
            if punit['owner'] == self.player_ctrl.my_player_id:
                unit_type = self.rule_ctrl.unit_type(punit)
                attack_strength = unit_type['attack_strength']
                if attack_strength > 0:
                    return True
        return False

    def have_units(self):
        """Check if my units have units."""
        for _, punit in self.units.items():
            if punit['owner'] == self.player_ctrl.my_player_id:
                return True
        return False

    def _player_find_unit_by_id(self, pplayer, unit_id):
        """
         If the specified player owns the unit with the specified id,
         return pointer to the unit struct.  Else return NULL.
         Uses fast idex_lookup_city.

         pplayer may be NULL in which case all units registered to
         hash are considered - even those not currently owned by any
         player. Callers expect this behavior.
        """
        punit = self.find_unit_by_number(unit_id)

        if punit is None:
            return None
        # TODO: make sure the fix from "or" to "and" is correct.
        # The implementation with "or" is the same as that of freeciv-web while it seems incorrect based on the function description.
        if pplayer != None and self.unit_owner(punit) == pplayer:
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

        found = False
        for tile_unit in tile_units:
            if tile_unit['id'] == punit['id']:
                found = True
                break

        if not found:
            ptile['units'].append(punit)

    @staticmethod
    def unit_list_size(unit_list):
        """Returns the length of the unit list"""
        if unit_list is None:
            return 0
        else:
            return len(unit_list)

    # Reset the keep_activity state of units. Called this method when handle the begin_turn packet.
    def reset_keep_activity_state(self):
        for unit_id in self.units:
            # We set the state for all units (including the enemy units). This state is useless for enemy units.
            self.units[unit_id]['keep_activity'] = False

    def unit_has_goto(self, punit):
        """ don't show goto activity for enemy units. I'm not 100% sure this is correct."""
        pplayer = self.player_ctrl.cur_player

        if pplayer is None or punit['owner'] != pplayer.playerno:
            return False

        return punit['goto_tile'] != -1

    def find_unit_by_number(self, uid):
        """
          Find unit out of all units in game: now uses fast idex method,
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

    # -------------------Functions for removing a unit----------------------------
    def handle_unit_remove(self, packet):
        """
          Handle a remove-unit packet, sent by the server to tell us any time a
          unit is no longer there.                             99% complete.
        """
        # fc_logger.debug(f'Remove unit: {packet}')
        punit = self.find_unit_by_number(packet['unit_id'])
        if punit is None:
            return

        # /* TODO: Close diplomat dialog if the diplomat is lost */
        # /* TODO: Notify agents. */
        self._clear_tile_unit(punit)
        self._client_remove_unit(punit)

    def _client_remove_unit(self, punit):
        # if self.unit_action_ctrl.unit_is_in_focus(punit):
        #    self.unit_action_ctrl.clear_focus()
        if punit['owner'] == self.player_ctrl.my_player_id:
            self.prop_state.remove_dict_item(punit["id"])
            self.prop_actions.remove_actor(punit["id"])
            if punit['id'] in self.prop_actions.unit_data:
                del self.prop_actions.unit_data[punit['id']]
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
                              BitVector(bitlist=packet['improvements']),
                              packet['action_id'])

    def handle_unit_info(self, packet):
        self.handle_unit_packet_common(packet)

    def handle_unit_short_info(self, packet):
        """/* 99% complete FIXME: does this loose information? */"""
        self.handle_unit_packet_common(packet)

    def handle_unit_packet_common(self, packet_unit):
        """
        Called to do basic handling for a unit_info or short_unit_info packet.

        Both owned and foreign units are handled; you may need to check unit
        owner, or if unit equals focus unit, depending on what you are doing.

        Note: Normally the server informs client about a new "activity" here.
        For owned units, the new activity can be a result of:
        - The player issued a command (a request) with the client.
        - The server side AI did something.
        - An enemy encounter caused a sentry to idle. (See "Wakeup Focus").

        Depending on what caused the change, different actions may be taken.
        Therefore, this function is a bit of a jungle, and it is advisable
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
            game_unit['unit_id'] = game_unit['id']
            self.handle_unit_remove(game_unit)

        old_tile = None
        if punit != None:
            old_tile = self.map_ctrl.index_to_tile(punit['tile'])

        if not packet_unit['id'] in self.units:
            # This is a new unit. */
            # self.unit_actor_wants_input(packet_unit)
            # The info of units from other players does not contain the action_decision_want key.
            if 'action_decision_want' in packet_unit:
                if self.should_ask_server_for_actions(packet_unit):
                    self.action_decision_handle(packet_unit)
            packet_unit['anim_list'] = []
            self.units[packet_unit['id']] = packet_unit
            self.units[packet_unit['id']]['facing'] = 6
            # We can normally handle the packets for new units before the begin_turn packet. One exception is the case where we bribe an enemy unit during a turn. In this case, the bribed unit is a new unit. We need to set its keep_activity state here. Otherwise, the _can_actor_act() will have key error.
            self.units[packet_unit['id']]['keep_activity'] = False
        else:
            if punit != None:
                if 'action_decision_want' in packet_unit:
                    if (punit['action_decision_want'] != packet_unit['action_decision_want'] or punit['action_decision_tile'] != packet_unit['action_decision_tile']) and self.should_ask_server_for_actions(packet_unit):
                        self.action_decision_handle(packet_unit)
        self.units[packet_unit['id']].update(packet_unit)
        self._update_tile_unit(self.units[packet_unit['id']])
        # Clear action_decision_want (resulting from the saved human operation or units moving into some area) if exist.
        if 'action_decision_want' in packet_unit:
            if packet_unit['action_decision_want'] != ACT_DEC_NOTHING:
                self.action_decision_clear_want(packet_unit['id'])
        """
        if current_focus.length > 0 and current_focus[0]['id'] == packet_unit['id']:
            update_active_units_dialog()
            update_unit_order_commands()

        if current_focus[0]['done_moving'] != packet_unit['done_moving']:
            update_unit_focus()
        """
        # TODO: update various dialogs and mapview. */

    def should_ask_server_for_actions(self, punit):
        return (punit['action_decision_want'] == ACT_DEC_ACTIVE) or (punit['action_decision_want'] == ACT_DEC_PASSIVE and self.option_ctrl.popup_actor_arrival)

    def action_decision_handle(self, punit):
        # In freeciv-web implementation, there are codes for auto_attack query and action_decision_tile query, we omit them here because our client would not issue auto-attack or goal command.
        pass

    # Have the server record that a decision no longer is wanted for the specified unit.
    def action_decision_clear_want(self, old_actor_id):
        old = self.find_unit_by_number(old_actor_id)
        if old != None and old['action_decision_want'] != ACT_DEC_NOTHING:
            unqueue_packet = {
                "pid": packet_unit_sscs_set,
                "unit_id": old_actor_id,
                "type": USSDT_UNQUEUE,
                "value": IDENTITY_NUMBER_ZERO
            }
            self.ws_client.send_request(unqueue_packet, wait_for_pid=(63, old_actor_id))
            # self.ws_client.send_request(unqueue_packet, wait_for_pid=63)
            # if old_actor_id == 1912:
            #     print(old_actor_id)
            #     print(old)
            #     fc_logger.info('Clear decision want.')

    # def unit_actor_wants_input(self, pdiplomat):
    #     """Handle server request for user input about diplomat action to do."""

    #     if not self.player_ctrl.clstate.can_client_control():
    #         return

    #     if not 'action_decision_want' in pdiplomat or \
    #        pdiplomat['owner'] != self.player_ctrl.my_player_id:
    #         # /* No authority to decide for this unit. */
    #         return

    #     if pdiplomat['action_decision_want'] == ACT_DEC_NOTHING:
    #         # /* The unit doesn't want a decision. */
    #         return

    #     if pdiplomat['action_decision_want'] == ACT_DEC_PASSIVE:
    #         # /* The player isn't interested in getting a pop up for a mere
    #         # * arrival. */
    #         return

    #     self.process_diplomat_arrival(pdiplomat, pdiplomat['action_decision_tile'])

    # def process_diplomat_arrival(self, pdiplomat, target_tile_id):
    #     """
    #       /* No queue. An action selection dialog is opened at once. If multiple
    #        * action selection dialogs are open at once one will hide all others.
    #        * The hidden dialogs are based on information from the time they
    #        * were opened. It is therefore more outdated than it would have been if
    #        * the server was asked the moment before the action selection dialog
    #        * was shown.
    #        *
    #        * The C client's bundled with Freeciv asks right before showing the
    #        * action selection dialog. They used to have a custom queue for it.
    #        * Freeciv patch #6601 (SVN r30682) made the desire for an action
    #        * decision a part of a unit's data. They used it to drop their custom
    #        * queue and move unit action decisions to the unit focus queue.
    #     """

    #     ptile = self.map_ctrl.index_to_tile(target_tile_id)
    #     if pdiplomat != None and ptile != None:
    #         """Ask the server about what actions pdiplomat can do. The server's
    #          * reply will pop up an action selection dialog for it.
    #         """
    #     packet = {
    #         "pid": packet_unit_get_actions,
    #         "actor_unit_id": pdiplomat['id'],
    #         "target_unit_id": IDENTITY_NUMBER_ZERO,
    #         "target_tile_id": target_tile_id,
    #         "disturb_player": True
    #     }
    #     self.ws_client.send_request(packet)

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
            fc_logger.info("Bad actor unit (" + diplomat_id
                           + ") in unit action answer.")
            return

        if action_type == ACTION_SPY_BRIBE_UNIT:
            target_unit = self.find_unit_by_number(target_id)
            if target_unit is None:
                fc_logger.info("Bad target unit (" + target_id + ") in unit action answer.")
                return
            else:
                popup_bribe_dialog(actor_unit, target_unit, cost, action_type)
                return
        elif (action_type == ACTION_SPY_INCITE_CITY
              or action_type == ACTION_SPY_INCITE_CITY_ESC):
            if target_city is None:
                fc_logger.info("Bad target city (" + target_id + ") in unit action answer.")
                return
            else:
                popup_incite_dialog(actor_unit, target_city, cost, action_type)
                return
        elif action_type == ACTION_UPGRADE_UNIT:
            if target_city is None:
                fc_logger.info("Bad target city (" + target_id + ") in unit action answer.")
                return
            else:
                popup_unit_upgrade_dlg(actor_unit, target_city, cost, action_type)
                return

        elif action_type == ACTION_COUNT:
            fc_logger.info("unit_action_answer: Server refused to respond.")
        else:
            fc_logger.info("unit_action_answer: Invalid answer.")

    def handle_unit_actions(self, packet):
        """Handle server reply about what actions an unit can do."""

        actor_unit_id = packet['actor_unit_id']
        target_tile_id = packet['target_tile_id']
        # The unit_id and city_id in packet are meaningless.
        target_unit_id = packet['target_unit_id']
        # target_city_id = packet['target_city_id']
        target_extra_id = packet['target_extra_id']
        action_probabilities = packet['action_probabilities']
        pdiplomat = self.find_unit_by_number(actor_unit_id)
        ptile = self.map_ctrl.index_to_tile(target_tile_id)
        # target_unit = self.find_unit_by_number(target_unit_id)
        # target_city = self.city_ctrl.find_city_by_number(target_city_id)
        # target_extra = self.rule_ctrl.extras[target_extra_id]

        hasActions = False

        # The dead can't act
        if pdiplomat != None and ptile != None:
            for prob in action_probabilities:
                if action_prob_possible(prob):
                    hasActions = True
                    break

        # Update action probability for this unit
        target_tile = self.map_ctrl.index_to_tile(target_tile_id)
        unit_tile = self.map_ctrl.index_to_tile(self.units[actor_unit_id]['tile'])
        move_dir = self.map_ctrl.get_direction_for_step(unit_tile, target_tile)
        self.prop_actions.update_unit_action_pro(actor_unit_id, target_unit_id, move_dir, action_probabilities)

        self.prop_actions.restore_activity(actor_unit_id)

        # if (target_tile['x'] == 55 and target_tile['y'] == 39) or (target_tile['x'] == 55 and target_tile['y'] == 40):
        #     fc_logger.info(f'actor_unit_id: {actor_unit_id}, target_tile_id: {target_tile_id}, target_extra_id: {target_extra_id}, action_probabilities: {action_probabilities}')
        #     for i in range(len(action_probabilities)):
        #         if action_probabilities[i] != {'min': 0, 'max': 0}:
        #             fc_logger.info(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {action_probabilities[i]}')

        # if (actor_unit_id == 886):
        #     print(f'actor_unit_id: {actor_unit_id}, target_unit_id: {target_unit_id}, target_tile_id: {target_tile_id}')
        #     for i in range(len(action_probabilities)):
        #         if action_probabilities[i] != {'min': 0, 'max': 0}:
        #             fc_logger.info(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {action_probabilities[i]}')

        # print(f"unit_id: {actor_unit_id}, target_position: ({target_tile['x']}, {target_tile['y']}), extra: {self.rule_ctrl.extras[target_extra_id]['name'] if target_extra_id != -1 else None}.")

        # fc_logger.info(f'Length of probability: {len(action_probabilities)}.')
        # fc_logger.info(f'hasActions: {hasActions}')

        # Below is doing some dialog pop and selection in web and gtk gui. We comment out for our client.
        # TODO: ensure the action selection/confirm operation is implemented in other parts of our client.
        # request_kind = packet['request_kind']
        # if request_kind == REQEST_PLAYER_INITIATED:
        #     if hasActions:
        #         popup_action_selection(pdiplomat, action_probabilities,
        #                      ptile, target_extra, target_unit, target_city)
        #     else:
        #     # Nothing to do
        #         action_selection_no_longer_in_progress(actor_unit_id)
        #         action_decision_clear_want(actor_unit_id)
        #         action_selection_next_in_focus(actor_unit_id)
        # elif request_kind == REQEST_BACKGROUND_REFRESH:
        #         action_selection_refresh(pdiplomat,
        #                      target_city, target_unit, ptile,
        #                      target_extra,
        #                      action_probabilities)
        # elif request_kind == REQEST_BACKGROUND_FAST_AUTO_ATTACK:
        #         action_decision_maybe_auto(pdiplomat, action_probabilities,
        #                        ptile, target_extra,
        #                        target_unit, target_city)
        # else:
        #     raise RuntimeError("handle_unit_actions(): unrecognized request_kind %d", packet['request_kind'])

    def handle_worker_task(self, packet):
        # TODO: Implement */
        pass

    def handle_nuke_tile_info(self, packet):
        pass

    def can_actor_unit_move(self, actor_unit, target_tile):
        """Returns true unless a situation were a regular move always would be
        impossible is recognized."""
        idx = self.map_ctrl.index_to_tile
        if idx(actor_unit['tile']) == target_tile:
            # /* The unit is already on this tile. */
            return False

        if (-1 == self.map_ctrl.get_direction_for_step(idx(actor_unit['tile']),
                                                       target_tile)):
            # /* The target tile is too far away for one-step move. */
            return False

        # # If the unit cannot access the terrain, return False
        # if self.rule_ctrl.unit_type(actor_unit)['name'] in LAND_UNIT and target_tile['terrain'] in LAND_UNIT_INACCESS_TERRAIN:
        #     return False

        for tile_unit in target_tile['units']:
            tgt_owner_id = self.unit_owner(tile_unit)['playerno']

            if (tgt_owner_id != self.unit_owner(actor_unit)['playerno'] and
                    self.dipl_ctrl.check_not_dipl_states(tgt_owner_id, [player_const.DS_ALLIANCE, player_const.DS_TEAM])):
                # /* Can't move to a non allied foreign unit's tile. */
                return False

        if self.city_ctrl.tile_city(target_tile) != None:
            tgt_owner_id = self.player_ctrl.city_owner(self.city_ctrl.tile_city(target_tile))['playerno']

            if tgt_owner_id == self.unit_owner(actor_unit)['playerno']:
                # This city isn't foreign. */
                return True

            if self.dipl_ctrl.check_in_dipl_states(tgt_owner_id, [player_const.DS_ALLIANCE, player_const.DS_TEAM]):
                # /* This city belongs to an ally. */
                return True

            return False

        """/* It is better to show the "Keep moving" option one time to much than
            * one time to little. */"""
        return True

    def request_unit_act(self, pval):
        funits = self._get_units_in_focus()
        for punit in funits:
            packet = {"pid": packet_unit_sscs_set, "unit_id": punit['id'],
                      "type": USSDT_QUEUE,
                      "value": punit['tile'] if pval == "unit" else pval}

            # Have the server record that an action decision is wanted for this
            # unit.
            self.ws_client.send_request(packet)

    def request_unit_act_sel_vs(self, ptile):
        """An action selection dialog for the selected units against the specified
          tile is wanted."""
        self.request_unit_act(ptile['index'])

    def request_unit_act_sel_vs_own_tile(self):
        """An action selection dialog for the selected units against the specified
          unit"""
        self.request_unit_act("unit")

    def decode_special_characters(self, name):
        pattern = r"%[0-9A-Fa-f]{2}%[0-9A-Fa-f]{2}"
        special_char_list = re.findall(pattern, name)
        if len(special_char_list) > 0:
            for i in range(len(special_char_list)):
                sub_pattern = special_char_list[i]
                name = re.sub(sub_pattern, urllib.parse.unquote(sub_pattern), name)
        # replace empty space encoding with empty space
        pattern = r"%20"
        replacement = " "
        name = re.sub(pattern, replacement, name)
        return name

    def handle_city_name_suggestion_info(self, packet):
        """
      /* A suggested city name can contain an apostrophe ("'"). That character
       * is also used for single quotes. It shouldn't be added unescaped to a
       * string that later is interpreted as HTML. */
       """
        # /* Decode the city name. */
        unit_id = packet['unit_id']
        actor_unit = self.find_unit_by_number(unit_id)
        suggested_name = self.decode_special_characters(packet['name'])
        # suggested_name = urllib.parse.quote(packet['name'], safe='~()*!.\'').replace("%", "")
        if suggested_name in self.city_name_list:
            duplicate_name_num = sum(city_name.startswith(suggested_name) for city_name in self.city_name_list)
            suggested_name = '{}_{}'.format(suggested_name, duplicate_name_num)
        self.city_name_list.append(suggested_name)

        packet = self.base_action.unit_do_action(unit_id, actor_unit['tile'], ACTION_FOUND_CITY, name=suggested_name)
        self.ws_client.send_request(packet, wait_for_pid=(31, actor_unit['tile']))
        # self.ws_client.send_request(packet, wait_for_pid=31)
