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

import urllib

from civrealm.freeciv.tech.tech_helpers import is_tech_known, is_tech_prereq_known, can_player_build_unit_direct

from civrealm.freeciv.city.city_state import CityState
from civrealm.freeciv.city.city_ctrl import INCITE_IMPOSSIBLE_COST
from civrealm.freeciv.game import ruleset
from civrealm.freeciv.game.game_ctrl import EXTRA_NONE
from civrealm.freeciv.utils.base_action import Action, ActionList
from civrealm.freeciv.units.action_dialog import action_prob_possible, encode_building_id

from civrealm.freeciv.map.tile import TileState
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.utility import find_set_bits
from civrealm.freeciv.utils.freeciv_logging import fc_logger
import civrealm.freeciv.utils.fc_types as fc_types


class FocusUnit():
    """Stores all relevant information for deciding on valid actions for the
    unit in focus"""

    def __init__(self, rule_ctrl, map_ctrl, city_ctrl, unit_ctrl):
        self.rule_ctrl = rule_ctrl
        self.map_ctrl = map_ctrl
        self.city_ctrl = city_ctrl
        self.unit_ctrl = unit_ctrl

        self.punit = None
        self.ptype = None
        self.ptile = None
        self.pterrain = None
        self.pcity = None
        self.pplayer = None
        self.units_on_tile = None

        self.obsolete_type = None
        self.transporter = None

        self.action_prob = {}

    def set_focus(self, punit, ptype, ptile, pterrain, pcity, pplayer):
        """Sets the focus to unit punit having type ptype acting on ptile, pcity owned by pplayer"""
        self.punit = punit
        self.ptype = ptype
        self.ptile = ptile
        self.pterrain = pterrain
        self.pcity = pcity
        self.pplayer = pplayer
        # Get all units on the current tile
        self.units_on_tile = self.tile_units(ptile)

        if ptype['obsoleted_by'] in self.rule_ctrl.unit_types:
            self.obsolete_type = self.rule_ctrl.unit_types[ptype['obsoleted_by']]
        else:
            self.obsolete_type = None

        # ground, air, or missile
        self.transported_type = ''
        # Check the transported_type of the unit.
        if self.ptype['name'] in self.rule_ctrl.air_units:
            self.transported_type = 'air'
        elif self.ptype['name'] in self.rule_ctrl.missile_units:
            self.transported_type = 'missile'
        elif self.ptype['name'] in self.rule_ctrl.ground_units:
            self.transported_type = 'ground'

    def get_transporter(self):
        self.transporter = None
        # Key: transporter id; Value: record how many units the transporter has carried.
        transport_count = {}

        if self.transported_type == 'ground':
            for tunit in self.units_on_tile:
                # This unit is tranported by a ground_unit_transporter
                if tunit['transported_by'] > 0 and self.rule_ctrl.unit_type(
                        self.unit_ctrl.units[tunit['transported_by']])['name'] in self.rule_ctrl.ground_unit_transporter:
                    # update transport_count
                    if tunit['transported_by'] in transport_count:
                        transport_count[tunit['transported_by']] = transport_count[tunit['transported_by']] + 1
                    else:
                        # Initialize count for this transporter
                        transport_count[tunit['transported_by']] = 1
                else:
                    trans_type = self.rule_ctrl.unit_type(tunit)
                    # This unit is a ground unit transporter
                    if trans_type['name'] in self.rule_ctrl.ground_unit_transporter:
                        if tunit['id'] not in transport_count:
                            # Initialize count for this transporter
                            transport_count[tunit['id']] = 0

            for transporter in transport_count:
                trans_unit = self.unit_ctrl.units[transporter]
                trans_type = self.rule_ctrl.unit_type(trans_unit)
                # As long as a transporter has a capacity, we let it be the transporter. TODO: update the mechanism to let the unit can select which transporter to load.
                if transport_count[transporter] < trans_type['transport_capacity']:
                    self.transporter = trans_unit

    # Core functions to control focus units--------------------------------------------------
    @staticmethod
    def tile_units(ptile):
        """Returns a list of units on the given tile. See update_tile_unit()."""
        if ptile is None:
            return None
        return ptile['units']

    def update_diplomat_act_probs(self, act_probs):
        self.action_probabilities = act_probs

    def clear_focus(self):
        """Clears list of units in focus"""
        self.punit = None
        self.ptype = None
        self.ptile = None
        self.pcity = None
        self.pplayer = None
        self.units_on_tile = None

        self.obsolete_type = None
        self.transporter = None

        self.action_probabilities = None


class UnitActions(ActionList):
    def __init__(self, ws_client, unit_ctrl, rule_ctrl, player_ctrl, map_ctrl, city_ctrl):
        super().__init__(ws_client)
        self.unit_ctrl = unit_ctrl
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.map_ctrl = map_ctrl
        self.city_ctrl = city_ctrl
        self.unit_data = {}
        # The action class related to dynamic target units.
        self.target_unit_action_class = {fc_types.ACTION_TRANSPORT_EMBARK: ActEmbark}
        # The actions added dynamically. Need to clear the added actions after every step.
        self.target_unit_action_keys = {fc_types.ACTION_TRANSPORT_EMBARK: []}
        # Key: actor_id, value: (cancelled activity, cancelled activity extra target).
        self.cancel_order_dict = {}

    def update(self, pplayer):
        for unit_id in self.unit_ctrl.units.keys():
            punit = self.unit_ctrl.units[unit_id]
            # An unit is no longer own unit, need to remove it from unit_data.
            if punit["owner"] != self.player_ctrl.my_player_id and unit_id in self.unit_data:
                # fc_logger.debug('delete unit_data in unit_actions update.')
                # fc_logger.debug(f'punit: {punit}')
                # fc_logger.debug(f'self.unit_data.keys(): {self.unit_data.keys()}')
                del self.unit_data[unit_id]
            if punit["owner"] == self.player_ctrl.my_player_id:
                self._update_unit_data(punit, pplayer, unit_id)
                self.reset_action_pro(unit_id)
                if self.actor_exists(unit_id):
                    continue

                self.add_actor(unit_id)
                self.add_unit_order_commands(unit_id)
                # Add actions that query action probability
                self.add_unit_get_pro_order_commands(unit_id)
        
        self.clear_target_unit_actions()
        self.cancel_orders_before_query_pro()
        self.query_action_probablity()

    # This function cancels units' activity before querying action probability for them. Because the server will return 0 probability for the units under activity, this operation ensures the action probability can be returned by the server. We will restore the units' activity state when we handle the returned action probability packet by triggering the units' action corresponding to the cancelled activity.
    def cancel_orders_before_query_pro(self):
        if len(self.cancel_order_dict) > 0:
            print(self.cancel_order_dict)
            # for key in self.cancel_order_dict:
            #     print(self.unit_ctrl.units[key])
        # This dict should be cleared after we restore the activity.
        assert (len(self.cancel_order_dict) == 0)
        for unit_id in self.unit_data.keys():
            if self._can_query_action_pro(unit_id):
                punit = self.unit_data[unit_id].punit
                activity = punit['activity']
                # We need this for fortress/airbase/buoy actions.
                activity_tgt = punit['activity_tgt']
                # If ssa_controller is not 0, it means unit is controlled by rule (e.g., auto_worker), we don't need to query pro for this kind of units.
                if activity != fc_types.ACTIVITY_IDLE and punit['ssa_controller'] == 0:
                    # Record the activity to be cancelled.
                    self.cancel_order_dict[unit_id] = (activity, activity_tgt)
                    # Cancel order
                    self._action_dict[unit_id]['cancel_order'].trigger_action(self.ws_client)

                # if unit_id == 103:
                #     fc_logger.info(f'**Cancel order. {punit}')

    # This function is called during handle_unit_actions() in unit_ctrl. Restore the activity being cancelled before querying the action probability.
    def restore_activity(self, unit_id):
        # The unit has been cancelled its activity.
        if unit_id in self.cancel_order_dict:
            cancelled_activity = self.cancel_order_dict[unit_id]
            if cancelled_activity[0] != fc_types.ACTIVITY_SENTRY and cancelled_activity[0] != fc_types.ACTIVITY_GOTO and cancelled_activity[0] != fc_types.ACTIVITY_EXPLORE:
                # Get the action corresponding to the cancelled activity.
                if cancelled_activity[0] == fc_types.ACTIVITY_BASE or cancelled_activity[0] == fc_types.ACTIVITY_GEN_ROAD:
                    action_key = fc_types.ACTIVITY_ACTION_MAP[cancelled_activity[0]][cancelled_activity[1]]
                else:
                    action_key = fc_types.ACTIVITY_ACTION_MAP[cancelled_activity[0]]
                # Restore the activity.
                self._action_dict[unit_id][action_key].trigger_action(self.ws_client)

                # if unit_id == 103:
                #     fc_logger.info(f'++Restore activity. {self.unit_data[unit_id].punit}')

            del self.cancel_order_dict[unit_id]

    # Use this to delete old probability before query the new pro.

    def reset_action_pro(self, unit_id):
        self.unit_data[unit_id].action_prob = {}

    # Reset the target_unit_action_keys and remove the previously added target_unit_actions.
    def clear_target_unit_actions(self):
        for action_idx in self.target_unit_action_keys:
            # Has added some target_unit_actions for this action
            if len(self.target_unit_action_keys[action_idx]) > 0:
                for added_action in self.target_unit_action_keys[action_idx]:
                    # The added_action is tuple: (actor_id, action_key).
                    self.remove_action(added_action[0], added_action[1])
                self.target_unit_action_keys[action_idx].clear()

    def _update_unit_data(self, punit, pplayer, unit_id):
        if unit_id not in self.unit_data:
            self.unit_data[unit_id] = FocusUnit(self.rule_ctrl, self.map_ctrl, self.city_ctrl, self.unit_ctrl)

        ptype = self.rule_ctrl.unit_type(punit)
        ptile = self.map_ctrl.index_to_tile(punit['tile'])
        # ptile['terrain'] = self.rule_ctrl.tile_terrain(ptile)
        pterrain = self.rule_ctrl.tile_terrain(ptile)
        pcity = self.city_ctrl.tile_city(ptile)
        # May add ally_units, all neighbor units for other actions.
        # # The enemy_units is useful for the actions that target the enemy units, e.g., attack.
        # enemy_units = self.get_adjacent_enemy_units(ptile)
        self.unit_data[unit_id].set_focus(punit, ptype, ptile, pterrain, pcity, pplayer)

    def update_unit_action_pro(self, actor_unit_id, target_unit_id, dir, prob):
        for action_key in self.target_unit_action_keys:
            # The action that targets a unit is possible. Need to add it dynamically.
            if action_prob_possible(prob[action_key]):
                unit_focus = self.unit_data[actor_unit_id]
                action = self.target_unit_action_class[action_key](unit_focus, dir, target_unit_id)
                self.add_action(actor_unit_id, action)
                # Record the added action for auto-removing.
                self.target_unit_action_keys[action_key].append((actor_unit_id, action.action_key))

        self.unit_data[actor_unit_id].action_prob[dir] = prob

    def add_unit_order_commands(self, unit_id):
        """Enables and disables the correct units commands for the unit in focus."""

        unit_focus = self.unit_data[unit_id]

        for act_class in [ActTransform, ActMine, ActCultivate, ActPlant, ActFortress, ActAirbase, ActIrrigation, ActFallout, ActPollution,  ActKeepActivity,
                          ActParadrop, ActBuildCity, ActJoinCity, ActFortify, ActBuildRoad,
                          ActBuildRailRoad, ActPillage, ActHomecity, ActAirlift, ActUpgrade, ActDeboard,
                          ActBoard, ActUnloadUnit, ActCancelOrder,
                          # ActDisband, ActAutoSettler, ActExplore, ActNoOrders,
                          # ActTileInfo, ActActSel, ActSEntry, ActWait, ActNuke
                          ]:
            self.add_action(unit_id, act_class(unit_focus))

        for act_class in [
                ActGoto, ActAttack, ActConquerCity, ActSpyBribeUnit, ActSpyStealTech, ActSpySabotageCity, ActHutEnter,
                ActDisembark, ActTradeRoute, ActMarketplace, ActEmbassyStay, ActInvestigateSpend]:
            for dir8 in map_const.DIR8_ORDER:
                self.add_action(unit_id, act_class(unit_focus, dir8))

        # Add stay (i.e., no move) direction for this two action.
        for act_class in [ActTradeRoute, ActMarketplace]:
            self.add_action(unit_id, act_class(unit_focus, map_const.DIR8_STAY))

    def add_unit_get_pro_order_commands(self, unit_id):
        unit_focus = self.unit_data[unit_id]

        # for act_class in [ActGetAttackPro, ActGetActionPro]:
        for act_class in [ActGetActionPro]:
            for dir8 in map_const.DIR8_ORDER:
                self.add_get_pro_action(unit_id, act_class(unit_focus, dir8))
            # Also query the action pro for the current tile.
            self.add_get_pro_action(unit_id, act_class(unit_focus, map_const.DIR8_STAY))

    # Query action probablity from server
    def query_action_probablity(self):
        has_query = False
        for unit_id in self.unit_data.keys():
            # If a unit has no move left, it will not send get_pro action. Its corresponding action_prob will be {}.
            valid_actions = self.get_get_pro_actions(unit_id, valid_only=True)
            if len(valid_actions) > 0:
                has_query = True
            for action in valid_actions:
                valid_actions[action].trigger_action(self.ws_client)

        # In case we do not have actions needed to query the probability, we need to seed a message to trigger the server return a message. Otherwise, the lock_control() in get_observation will keep waiting for the server message which would be a ping packet that arrives every several seconds. This will make the running very slow.
        if not has_query:
            self.ws_client.send_message(f'No action probability query needed.')

    def _can_actor_act(self, unit_id):
        punit = self.unit_data[unit_id].punit
        return punit['movesleft'] > 0 and not punit['done_moving'] and \
            punit['ssa_controller'] == fc_types.SSA_NONE and not punit['keep_activity']
        # punit['ssa_controller'] == SSA_NONE and punit['activity'] == ACTIVITY_IDLE

    def _can_query_action_pro(self, unit_id):
        punit = self.unit_data[unit_id].punit
        # If an unit has orders or action_decision_want, we don't query its action pro here.
        return punit['movesleft'] > 0 and not punit['done_moving'] and \
            punit['ssa_controller'] == fc_types.SSA_NONE and not punit['has_orders'] and punit['action_decision_want'] == fc_types.ACT_DEC_NOTHING
        # punit['ssa_controller'] == SSA_NONE and punit['activity'] == ACTIVITY_IDLE and not punit['has_orders'] and punit['action_decision_want'] == ACT_DEC_NOTHING

    def get_get_pro_actions(self, actor_id, valid_only=False):
        if self.actor_exists(actor_id):
            if valid_only:
                act_dict = {}
            else:
                act_dict = dict([(key, None) for key in self._get_pro_action_dict[actor_id]])
            if self._can_query_action_pro(actor_id):
                for action_key in self._get_pro_action_dict[actor_id]:
                    action = self._get_pro_action_dict[actor_id][action_key]
                    if action.is_action_valid():
                        act_dict[action_key] = action
            return act_dict

     # Return the adjacent units of the given tile
    def get_adjacent_units(self, tile):
        tile_dict = self.map_ctrl.get_adjacent_tiles(tile)
        unit_dict = {}
        for tile in tile_dict:
            if len(tile_dict[tile]['units']) > 0:
                unit_dict[tile] = tile_dict[tile]['units']
        return unit_dict

    # Return the adjacent own units of the given tile
    def get_adjacent_own_units(self, tile):
        tile_dict = self.map_ctrl.get_adjacent_tiles(tile)
        unit_dict = {}
        for tile in tile_dict:
            for unit in tile_dict[tile]['units']:
                # TODO: check whether it is possible that units from other players (e.g., ally) are in the same tile as own units
                # If one unit is own unit, then other units are also own units.
                if unit['owner'] == self.player_ctrl.my_player_id:
                    unit_dict[tile] = tile_dict[tile]['units']
                    break
        return unit_dict

    # TODO: Need to consider the ally's player id
    # Return the adjacent enemy units of the given tile
    def get_adjacent_enemy_units(self, ptile):
        tile_dict = self.map_ctrl.get_adjacent_tiles(ptile)
        unit_dict = {}
        for tile in tile_dict:
            for unit in tile_dict[tile]['units']:
                if unit['owner'] != self.player_ctrl.my_player_id:
                    unit_dict[tile] = tile_dict[tile]['units']
                    break
        return unit_dict

# This action changes the keep_activity state of a unit to true. Once this state is true, the unit will not perform actions in this turn anymore. This mimics the human player's decision that a unit does not need further orders in this turn.


class ActKeepActivity(Action):
    action_key = 'keep_activity'

    def __init__(self, focus):
        self.focus = focus

    def is_action_valid(self):
        # We always allow to set the keep_activity state
        return True

    def _action_packet(self):
        return 'keep_activity'

    def trigger_action(self, ws_client):
        ws_client.send_message(f"Unit {self.focus.punit['id']} keeps activity.")
        self.focus.punit['keep_activity'] = True


class UnitAction(Action):
    def __init__(self, focus):
        self.focus = focus

    def is_action_valid(self):
        raise Exception("Not implemented - To be implemented by specific Action classes")

    def _action_packet(self):
        raise Exception("Not implemented - To be implemented by specific Action classes")

    def utype_can_do_action(self, unit, action_id):
        if not unit['type'] in self.focus.rule_ctrl.unit_types:
            fc_logger.error('Nonexist unit type.')
            return False
        putype = self.focus.rule_ctrl.unit_types[unit['type']]
        if not 'utype_actions' in putype:
            fc_logger.error('utype_can_do_action(): bad unit type.')
            return False
        if action_id >= fc_types.ACTION_COUNT or action_id < 0:
            fc_logger.error(f'utype_can_do_action(): invalid action id: {action_id}')
            return False

        return putype['utype_actions'][action_id]

    def unit_do_action(self, actor_id, target_id, action_type, value=0, name=""):
        """Tell server action of actor_id towards unit target_id with the respective
        action_type"""

        packet = {"pid": fc_types.packet_unit_do_action,
                  "actor_id": actor_id,
                  "extra_id": EXTRA_NONE,
                  "target_id": target_id,
                  "sub_tgt_id": 0,
                  "value": value,
                  "name": name,
                  "action_type": action_type
                  }
        return packet

    def _request_new_unit_activity(self, activity, target):
        packet = {"pid": fc_types.packet_unit_change_activity, "unit_id": self.focus.punit['id'],
                  "activity": activity, "target": target}
        return packet

    def _unit_do_activity(self, actor_id, activity, target):
        packet = {"pid": fc_types.packet_unit_change_activity, "unit_id": actor_id,
                  "activity": activity, "target": target}
        return packet


class UnitActionVsTile(UnitAction):
    def action_packet(self):
        raise Exception("Not implemented")

    def is_action_valid(self):
        raise Exception("Not implemented")


class StdAction(UnitAction):
    def is_action_valid(self):
        return True


class ActSEntry(StdAction):
    action_key = "sentry"

    def _action_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_SENTRY, EXTRA_NONE)


class ActCancelOrder(UnitAction):
    """Cancel the existing activity of a unit."""
    action_key = "cancel_order"

    def is_action_valid(self):
        # # It is meaningless to cancel order for transported unit.
        # if self.focus.punit['transported'] and self.focus.punit['transported_by'] > 0:
        #     return False
        # Only when the unit has a non-idle activity, we can cancel its order.
        return self.focus.punit['activity'] != fc_types.ACTIVITY_IDLE

    def _action_packet(self):
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        packet = self._request_new_unit_activity(fc_types.ACTIVITY_IDLE, EXTRA_NONE)
        return packet


class ActWait(StdAction):
    """Tell the unit to wait (focus to next unit with moves left)"""
    action_key = "wait"

    def _action_packet(self):
        raise Exception("Irrelevant for Bot")


class ActNoOrders(StdAction):
    """Tell the unit to have no orders this turn, set unit to done moving."""
    action_key = "no_orders"

    def _action_packet(self):
        raise Exception("Irrelevant for Bot")
        # self.punit['done_moving'] = True

    def is_action_valid(self):
        return False


class ActDisband(StdAction):
    """Tell the units in focus to disband."""
    action_key = "disband"

    def _action_packet(self):
        # Do Recycle Unit if located inside a city.
        # FIXME: Only rulesets where the player can do Recycle Unit to all
        # domestic and allied cities are supported here.
        target_city = self.focus.pcity
        target_id = self.focus.punit['id'] if target_city is None else target_city['id']
        action_id = fc_types.ACTION_DISBAND_UNIT if target_city is None else fc_types.ACTION_DISBAND_UNIT_RECOVER
        self.wait_for_pid = (62, self.focus.punit['id'])
        return self.unit_do_action(self.focus.punit['id'], target_id, action_id)


class ActActSel(StdAction):
    action_key = "action_selection"


class ActTileInfo(StdAction):
    action_key = "tile_info"

    def is_action_valid(self):
        return False

    def key_tile_info(self):
        """Requests information on a seen tile"""
        if self.current_focus != []:
            punit = self.current_focus[0]
            ptile = self.map_ctrl.index_to_tile(punit['tile'])
            if ptile != None:
                self.popit_req(ptile)

    def popit_req(self, ptile):
        """ request tile popup """
        if ptile == None:
            return

        infos['location']['x'] = ptile['x']
        infos['location']['y'] = ptile['y']
        if tile_get_known(ptile) in [TILE_KNOWN_UNSEEN, TILE_UNKNOWN]:
            show_dialog_message("Tile info", "Location: x:" + ptile['x'] + " y:" + ptile['y'])
            return

        punit_id = 0
        punit = find_visible_unit(ptile)
        if punit != None:
            punit_id = punit['id']

        focus_unit_id = 0
        if self.current_focus != []:
            focus_unit_id = current_focus[0]['id']

        packet = {"pid": packet_info_text_req, "visible_unit": punit_id,
                  "loc": ptile['index'], "focus_unit": focus_unit_id}
        self.ws_client.send_request(packet)


class EngineerAction(UnitAction):
    # If a unit is performing an engineering action, we don't show it in the valid action list again. If the unit continues to perform the same action again, we cannot receive response from the server.
    def is_action_valid(self):
        if self.focus.punit['movesleft'] == 0:
            return False  # raise Exception("Unit has no moves left to build city")

        # Transported unit cannot do engineer action.
        if self.focus.punit['transported'] and self.focus.punit['transported_by'] > 0 and self.focus.pcity is None:
            return False
        # if self.focus.ptype['name'] in ["Workers", "Engineers"]:
        return self.is_eng_action_valid()
        # return False

    def is_eng_action_valid(self):
        raise Exception("Not implemented")

    def _eng_packet(self):
        raise Exception("Not implemented")

    def _action_packet(self):
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return self._eng_packet()


class ActTransform(EngineerAction):
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_TRANSFORM]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_TRANSFORM_TERRAIN):
            return False

        # Is already performing transform, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_TRANSFORM:
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_TRANSFORM_TERRAIN])

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_TRANSFORM, EXTRA_NONE)


class ActMine(EngineerAction):
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_MINE]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_MINE):
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        # If the tile already has MINE extra, we cannot do mine again.
        if TileState.tile_has_extra(
                self.focus.ptile, fc_types.EXTRA_MINE) or TileState.tile_has_extra(
                self.focus.ptile, fc_types.EXTRA_OIL_MINE):
            return False

        # Is already performing mine, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_MINE:
            return False

        # # FIXME: This is server bug. When under irrigation, cannot change to mine activity.
        # if self.focus.punit['activity'] == fc_types.ACTIVITY_IRRIGATE:
        #     return False

        units = FocusUnit.tile_units(self.focus.ptile)
        for unit in units:
            # If another unit in this tile is irrigating, we cannot mine
            if (unit['id'] != self.focus.punit['id']) and (unit['activity'] == fc_types.ACTIVITY_IRRIGATE):
                return False

        # Mine on hill and mountain terrain is alway valid.
        if self.focus.pterrain['name'] == 'Hills' or self.focus.pterrain['name'] == 'Mountains':
            return True

        # Mine Desert needs Construction
        if self.focus.pterrain['name'] == 'Desert' and is_tech_known(self.focus.pplayer, 19):
            return True

        # Mine Glacier needs refining
        if self.focus.pterrain['name'] == 'Glacier' and is_tech_known(self.focus.pplayer, 68):
            return True

        # mining_time > 0 only means it is possible to mine. But whether can mine also depends on the technology, e.g., desert needs construction and glacier needs refining.
        # and self.focus.ptile['terrain']['mining_time'] > 0:
            # return True
        return False
        # return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_MINE])

    def _eng_packet(self):
        # If the unit is currently irrigating, we cancel the activity first.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_IRRIGATE:
            cancel_order_action = ActCancelOrder(self.focus)
            cancel_order_action.trigger_action(self.focus.unit_ctrl.ws_client)
        return self._request_new_unit_activity(fc_types.ACTIVITY_MINE, EXTRA_NONE)


class ActOnExtra(EngineerAction):
    """Base class for units that act on extras"""
    action_key = None

    def __init__(self, cur_focus):
        super().__init__(cur_focus)
        self.extra_type = None

    # Temporarily block other actions on extra
    def is_action_valid(self):
        return False

    def is_eng_action_valid(self):
        if self.extra_type is None:
            raise Exception("Extra type should be set")
        return TileState.tile_has_extra(self.focus.ptile, self.extra_type)


class ActCultivate(EngineerAction):
    """Action to deforest"""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_CULTIVATE]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_CULTIVATE):
            return False

        # Is already performing cultivate, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_CULTIVATE:
            return False

        # terr_name = self.focus.rule_ctrl.tile_terrain(self.focus.ptile)['name']
        # return terr_name == "Forest"
        # return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_CULTIVATE])
        return self.focus.pterrain['cultivate_time'] > 0

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_CULTIVATE, EXTRA_NONE)


class ActPlant(EngineerAction):
    """Action to create forest"""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_PLANT]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_PLANT):
            return False

        # Is already performing plant, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_PLANT:
            return False

        # terr_name = self.focus.rule_ctrl.tile_terrain(self.focus.ptile)['name']
        # # Forest can only be planted on grassland or plains
        # return terr_name == "Grassland" or terr_name == "Plains"
        # return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_PLANT])
        return self.focus.pterrain['plant_time'] > 0

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_PLANT, EXTRA_NONE)


class ActFortress(EngineerAction):
    """Action to create a fortress"""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_BASE][fc_types.EXTRA_FORTRESS]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_BASE):
            return False

        # If the tile already has FORTRESS or BUOY extra, we cannot do FORTRESS again.
        if TileState.tile_has_extra(
                self.focus.ptile, fc_types.EXTRA_FORTRESS) or TileState.tile_has_extra(
                self.focus.ptile, fc_types.EXTRA_BUOY):
            return False

        # Is already performing fortress, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_BASE and (
                self.focus.punit['activity_tgt'] == fc_types.EXTRA_FORTRESS or self.focus.punit['activity_tgt'] == fc_types.EXTRA_BUOY):
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        return is_tech_known(self.focus.pplayer, 19)

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_BASE, EXTRA_NONE)


class ActAirbase(EngineerAction):
    """Action to create a airbase"""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_BASE][fc_types.EXTRA_AIRBASE]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_BASE):
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        # If the tile already has airbase extra, we cannot do airbase again.
        if TileState.tile_has_extra(self.focus.ptile, fc_types.EXTRA_AIRBASE):
            return False

        # Is already performing airbase, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_BASE and self.focus.punit['activity_tgt'] == fc_types.EXTRA_AIRBASE:
            return False

        return is_tech_known(self.focus.pplayer, 64)

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_BASE, ruleset.EXTRA_AIRBASE)


# class ActIrrigation(ActOnExtra):
class ActIrrigation(EngineerAction):
    """Action to create an irrigation"""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_IRRIGATE]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_IRRIGATE):
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        # Is already performing irrigation, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_IRRIGATE:
            return False

        # # FIXME: This is server bug. When under mine, cannot change to irrigation activity.
        # if self.focus.punit['activity'] == fc_types.ACTIVITY_MINE:
        #     return False

        units = FocusUnit.tile_units(self.focus.ptile)
        for unit in units:
            # If another unit in this tile is mining, we cannot irrigate
            if (unit['id'] != self.focus.punit['id']) and (unit['activity'] == fc_types.ACTIVITY_MINE):
                return False

        # if self.focus.action_prob == {}:
        #     fc_logger.info(self.focus.punit)
        #     print(self.focus.punit)
        #     print(self.focus.ptype)
        #     print(f"({self.focus.ptile['x']}, {self.focus.ptile['y']})")

        return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_IRRIGATE])

    def _eng_packet(self):
        # If the unit is currently mining, we cancel the activity first.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_MINE:
            cancel_order_action = ActCancelOrder(self.focus)
            cancel_order_action.trigger_action(self.focus.unit_ctrl.ws_client)
        return self._request_new_unit_activity(fc_types.ACTIVITY_IRRIGATE, EXTRA_NONE)


class ActFallout(ActOnExtra):
    """Action to clean fallout"""
    action_key = "fallout"

    def __init__(self, cur_focus):
        self.extra_type = ruleset.EXTRA_FALLOUT
        super().__init__(cur_focus)

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_FALLOUT, EXTRA_NONE)


# class ActPollution(ActOnExtra):
class ActPollution(EngineerAction):
    """Action to remove pollution"""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_POLLUTION]

    # def __init__(self, cur_focus):
    #     self.extra_type = fc_types.EXTRA_POLLUTION
    #     super().__init__(cur_focus)

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_CLEAN_POLLUTION):
            return False

        # Is already removing pollution, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_POLLUTION:
            return False

        # terr_name = self.focus.rule_ctrl.tile_terrain(self.focus.ptile)['name']
        # return terr_name == "Forest"
        # return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_CULTIVATE])
        # return self.focus.pterrain['pollution_time'] > 0
        return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_CLEAN_POLLUTION])

    def _eng_packet(self):
        return self._request_new_unit_activity(fc_types.ACTIVITY_POLLUTION, EXTRA_NONE)

# -------Further unit specific actions


class ActAutoSettler(UnitAction):
    """Call to request (from the server) that the focus unit is put into autosettler mode."""
    action_key = "autosettlers"

    def is_action_valid(self):
        return False
        return self.focus.ptype["name"] in ["Settlers", "Workers", "Engineers"]

    def _action_packet(self):
        packet = {"pid": fc_types.packet_unit_autosettlers,
                  "unit_id": self.focus.punit['id']}
        return packet


class ActExplore(UnitAction):
    action_key = "explore"

    def is_action_valid(self):
        # Is already performing explore, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_EXPLORE:
            return False
        return self.focus.ptype["name"] == "Explorer"

    def _action_packet(self):
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return self._request_new_unit_activity(fc_types.ACTIVITY_EXPLORE, EXTRA_NONE)


class ActParadrop(UnitAction):
    """Tell the units to paradrop."""
    action_key = "paradrop"

    def is_action_valid(self):
        return self.focus.ptype["name"] == "Paratroopers"

    def _action_packet(self):
        return self.unit_do_action(self.focus.punit['id'],
                                   self.focus.ptile['index'],
                                   fc_types.ACTION_PARADROP)


class ActBuildCity(UnitAction):
    """Request that a city is built."""
    action_key = "build_city"

    def __init__(self, cur_focus):
        super().__init__(cur_focus)
        self.next_city_name = None

    def is_action_valid(self):
        if self.focus.punit['movesleft'] == 0:
            return False  # raise Exception("Unit has no moves left to build city")

        # Check whether the unit type can do the given action
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_FOUND_CITY):
            return False
        # if self.focus.ptype["name"] not in ["Settlers", "Engineers"]:
            # return False
        # target_city = self.focus.pcity
        # # Already has a city, cannot build
        # if target_city != None:
        #     return False

        # _map = self.focus.map_ctrl
        # unit_tile = _map.index_to_tile(self.focus.punit["tile"])
        # unit_owner = self.focus.punit['owner']
        # for city_id in self.focus.unit_ctrl.city_ctrl.cities.keys():
        #     pcity = self.focus.unit_ctrl.city_ctrl.cities[city_id]
        #     city_tile = _map.index_to_tile(pcity["tile"])
        #     if city_tile['owner'] != unit_owner:
        #         # If settler is on a foreign territory
        #         return False
        #     dx, dy = _map.map_distance_vector(unit_tile, city_tile)
        #     dist = _map.map_vector_to_sq_distance(dx, dy)
        #     if dist < pcity["city_radius_sq"]:
        #         return False
        return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_FOUND_CITY])

    def _action_packet(self):
        unit_id = self.focus.punit["id"]
        self.wait_for_pid = None
        if self.next_city_name is None:
            packet = {"pid": fc_types.packet_city_name_suggestion_req,
                      "unit_id": unit_id}
            self.wait_for_pid = (44, self.focus.punit['id'])
            # self.wait_for_pid = 44
            return packet
        else:
            return self.found_new_city(unit_id)

    def set_next_city_name(self, suggested_name):
        self.next_city_name = suggested_name

    def found_new_city(self, unit_id):
        """Shows the Request city name dialog to the user."""
        actor_unit = self.focus.punit
        self.wait_for_pid = (31, actor_unit['tile'])
        return self.unit_do_action(
            unit_id, actor_unit['tile'],
            fc_types.ACTION_FOUND_CITY, name=urllib.parse.quote(self.next_city_name, safe='~()*!.\''))


class ActJoinCity(UnitAction):
    """Join an existing city."""
    action_key = "join_city"

    def __init__(self, cur_focus):
        super().__init__(cur_focus)

    def is_action_valid(self):
        if self.focus.punit['movesleft'] == 0:
            return False  # raise Exception("Unit has no moves left to build city")

        # Check whether the unit type can do the given action
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_JOIN_CITY):
            return False

        return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_JOIN_CITY])

    def _action_packet(self):
        target_city = self.focus.pcity
        if target_city == None:
            fc_logger.error('The unit does not locate inside a city, should not call _action_packet() for ActJoin')
            assert (False)
        unit_id = self.focus.punit["id"]
        # Join city will cause the removal of unit. Wait for the unit remove packet.
        self.wait_for_pid = (62, unit_id)
        # self.wait_for_pid = 62
        return self.unit_do_action(unit_id, target_city['id'], fc_types.ACTION_JOIN_CITY)


class ActFortify(UnitAction):
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_FORTIFIED]

    def is_action_valid(self):
        # return not self.focus.ptype['name'] in ["Settlers", "Workers"]
        # Check whether the unit type can do the given action
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_FORTIFY):
            return False

        if self.focus.punit['transported'] and self.focus.punit['transported_by'] > 0 and self.focus.pcity is None:
            return False

        return (self.focus.punit['activity'] != fc_types.ACTIVITY_FORTIFIED and self.focus.punit['activity'] != fc_types.ACTIVITY_FORTIFYING)

    def _action_packet(self):
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return self._request_new_unit_activity(fc_types.ACTIVITY_FORTIFYING, EXTRA_NONE)


class ActBuildRoad(EngineerAction):
    """Tell the units in focus to build road."""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_GEN_ROAD][fc_types.EXTRA_ROAD]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_ROAD):
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        # Is already performing road building, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_GEN_ROAD:
            return False

        bridge_known = is_tech_known(self.focus.pplayer, 8)
        tile_no_river = not TileState.tile_has_extra(self.focus.ptile, fc_types.EXTRA_RIVER)
        no_road_yet = not TileState.tile_has_extra(self.focus.ptile, fc_types.EXTRA_ROAD)
        return (bridge_known or tile_no_river) and no_road_yet

    def _eng_packet(self):
        extra_id = self.focus.rule_ctrl.extras['Road']['id']
        return self._request_new_unit_activity(fc_types.ACTIVITY_GEN_ROAD, extra_id)


class ActBuildRailRoad(EngineerAction):
    """Tell the units in focus to build or railroad."""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_GEN_ROAD][fc_types.EXTRA_RAILROAD]

    def is_eng_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_ROAD):
            return False

        # If locate inside a city, cannot perform this action.
        if self.focus.pcity != None:
            return False

        # Is already performing road building, no need to show this action again.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_GEN_ROAD:
            return False

        railroad_known = is_tech_known(self.focus.pplayer, 65)
        already_road = TileState.tile_has_extra(self.focus.ptile, fc_types.EXTRA_ROAD)
        no_rail_yet = not TileState.tile_has_extra(self.focus.ptile, fc_types.EXTRA_RAILROAD)
        return railroad_known and already_road and no_rail_yet

    def _eng_packet(self):
        extra_id = self.focus.rule_ctrl.extras['Railroad']['id']
        return self._request_new_unit_activity(fc_types.ACTIVITY_GEN_ROAD, extra_id)


class ActPillage(UnitAction):
    """Pillages Irrigation, Mine, Oil Mine, Farmland, Fortress, Airbase, Buoy, Ruins, Road and Railroad from tiles."""
    action_key = fc_types.ACTIVITY_ACTION_MAP[fc_types.ACTIVITY_PILLAGE]

    def is_action_valid(self):
        # tile_valid = self.focus.pcity is None or (self.focus.pcity != None and CityState.city_owner_player_id(
        #     self.focus.pcity) != self.focus.pplayer["playerno"])
        # return self.focus.pplayer != None and self.focus.ptype['attack_strength'] > 0 and tile_valid

        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_PILLAGE):
            return False

        # Is already performing pillage, no need to show this action again.
        # TODO: if we support the choosing of pillage target in the future, we need to refine this logic.
        if self.focus.punit['activity'] == fc_types.ACTIVITY_PILLAGE:
            return False

        # If locate inside own city, cannot perform this action.
        if self.focus.pcity != None and CityState.city_owner_player_id(
                self.focus.pcity) == self.focus.pplayer["playerno"]:
            return False

        has_road = False
        has_railroad = False

        extra_num = 0
        # If locate in other player's city, we cannot pillage the city's road. But we can pillage other extras.
        extra_list = [fc_types.EXTRA_IRRIGATION, fc_types.EXTRA_MINE, fc_types.EXTRA_OIL_MINE, fc_types.EXTRA_FARMLAND,
                      fc_types.EXTRA_FORTRESS, fc_types.EXTRA_AIRBASE, fc_types.EXTRA_BUOY, fc_types.EXTRA_RUINS]
        if self.focus.pcity == None:
            extra_list.extend([fc_types.EXTRA_ROAD, fc_types.EXTRA_RAILROAD])

        for extra in extra_list:
            if TileState.tile_has_extra(self.focus.ptile, extra):
                extra_num += 1
                if extra == fc_types.EXTRA_ROAD:
                    has_road = True
                if extra == fc_types.EXTRA_RAILROAD:
                    has_railroad = True
        # When have both road and railroad, we cannot pillage them simultaneously. Instead, we need to pillage railroad first and then road. Therefore, the available extra number should decrease by 1.
        if has_road and has_railroad:
            extra_num -= 1

        if extra_num == 0:
            return False

        pillage_num = 0
        units = FocusUnit.tile_units(self.focus.ptile)
        for unit in units:
            if unit['activity'] == fc_types.ACTIVITY_PILLAGE:
                pillage_num += 1

        if pillage_num == extra_num:
            return False
        # can_pillage_extra = TileState.tile_has_extra(self.focus.ptile, EXTRA_IRRIGATION) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_MINE) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_OIL_MINE) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_FARMLAND) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_FORTRESS) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_AIRBASE) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_BUOY) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_RUINS) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_ROAD) or \
        #     TileState.tile_has_extra(self.focus.ptile, EXTRA_RAILROAD)

        # for extra in [
        #         EXTRA_IRRIGATION, EXTRA_MINE, EXTRA_OIL_MINE, EXTRA_FARMLAND, EXTRA_FORTRESS, EXTRA_AIRBASE, EXTRA_BUOY,
        #         EXTRA_RUINS, EXTRA_ROAD, EXTRA_RAILROAD]:
        #     if TileState.tile_has_extra(self.focus.ptile, extra):
        #         fc_logger.debug(f'Has extra: {extra}')

        # for unit in units:
        #     if unit['activity'] == fc_types.ACTIVITY_PILLAGE:
        #         fc_logger.debug(f'Other unit: {unit}')

        # fc_logger.debug(f'pillage_num: {pillage_num}')
        # fc_logger.debug(f'extra_num: {extra_num}')
        # fc_logger.debug(f'Self unit: {self.focus.punit}')

        return True

    def _action_packet(self):
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return self._request_new_unit_activity(fc_types.ACTIVITY_PILLAGE, EXTRA_NONE)


class ActHomecity(UnitAction):
    """Changes unit homecity to the city on same tile."""
    action_key = "set_homecity"

    def is_action_valid(self):
        if self.focus.pcity is None:
            return False

        return action_prob_possible(self.focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_HOME_CITY])

        # if self.focus.punit['homecity'] == 0 or self.focus.punit['homecity'] == self.focus.pcity['id']:
        #     return False
        # if self.focus.punit['homecity'] != self.focus.pcity['id']:
        #     return True
        # return False

    def _action_packet(self):
        self.wait_for_pid = (63, self.focus.punit['id'])
        return self.unit_do_action(self.focus.punit['id'],
                                   self.focus.pcity['id'], fc_types.ACTION_HOME_CITY)


class ActTradeRoute(UnitAction):
    """Establish a trade route from the homecity to the arrived city. This action will cost the unit."""
    action_key = "trade_route"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        return action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_TRADE_ROUTE])

        # if self.focus.punit['homecity'] == 0 or self.focus.punit['homecity'] == self.focus.pcity['id']:
        #     return False
        # if self.focus.punit['homecity'] != self.focus.pcity['id']:
        #     return True
        # return False

    def _action_packet(self):
        if self.dir8 == map_const.DIR8_STAY:
            newtile = self.focus.ptile
        else:
            newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        target_city = self.focus.city_ctrl.tile_city(newtile)
        if target_city != None:
            self.target_city_id = target_city['id']

        # self.wait_for_pid = (249, self.target_city_id)
        self.wait_for_pid = (62, self.focus.punit['id'])
        return self.unit_do_action(self.focus.punit['id'],
                                   self.target_city_id, fc_types.ACTION_TRADE_ROUTE)


class ActMarketplace(UnitAction):
    """If the arrived city has established a trade route with the homecity, a unit can do marketplace action to get one-time revenue. This action will cost the unit."""
    action_key = "marketplace"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        return action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_MARKETPLACE])

        # if self.focus.punit['homecity'] == 0 or self.focus.punit['homecity'] == self.focus.pcity['id']:
        #     return False
        # if self.focus.punit['homecity'] != self.focus.pcity['id']:
        #     return True
        # return False

    def _action_packet(self):
        if self.dir8 == map_const.DIR8_STAY:
            newtile = self.focus.ptile
        else:
            newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        target_city = self.focus.city_ctrl.tile_city(newtile)
        if target_city != None:
            self.target_city_id = target_city['id']

        # self.wait_for_pid = (249, self.target_city_id)
        self.wait_for_pid = (62, self.focus.punit['id'])
        return self.unit_do_action(self.focus.punit['id'],
                                   self.target_city_id, fc_types.ACTION_MARKETPLACE)


class ActAirlift(UnitAction):
    """Tell the units to airlift."""
    action_key = "airlift"

    def is_action_valid(self):
        if self.focus.pcity is None:
            return False
        return self.focus.rule_ctrl.city_has_building(self.focus.pcity, 0)

    def _action_packet(self):
        return self.unit_do_action(self.focus.punit['id'],
                                   self.focus.pcity['id'],
                                   fc_types.ACTION_AIRLIFT)


class ActUpgrade(UnitAction):
    """Tell units to upgrade"""
    action_key = "upgrade"

    def is_action_valid(self):
        if self.focus.pcity is None:
            return False
        return self.focus.ptype != None and self.focus.obsolete_type != None and \
            can_player_build_unit_direct(self.focus.pplayer, self.focus.obsolete_type)

    def _action_packet(self):
        target_id = self.focus.pcity['id'] if self.focus.pcity != None else 0
        return self.unit_do_action(self.focus.punit['id'], target_id, fc_types.ACTION_UPGRADE_UNIT)


class ActDeboard(UnitAction):
    """A unit performs this action to deboard from a transport. This action does not cost move."""
    action_key = "deboard"

    def is_action_valid(self):
        # The unit has not been transported, cannot do deboard action.
        if self.focus.punit['transported'] == False:
            return False
        else:
            # Check whether the unit is a ground unit.
            if self.focus.transported_type == 'ground':
                # If the unit is not in a city, cannot perform deboard action.
                if self.focus.pcity is None:
                    return False
                return True
            else:
                # Check air units and missile units later
                return False

    def _action_packet(self):
        packet = self.unit_do_action(
            self.focus.punit['id'],
            self.focus.punit['transported_by'],
            fc_types.ACTION_TRANSPORT_DEBOARD)
        self.wait_for_pid = (63, self.focus.punit['id'])
        return packet


class ActBoard(UnitAction):
    """A unit performs this action to board on a transport. This action does not cost move."""
    action_key = "board"

    def is_action_valid(self):
        # If unit is a transporter, cannot load onto another unit.
        if self.focus.ptype['transport_capacity'] > 0:
            return False
        # The unit has been transported, cannot do load action again.
        if self.focus.punit['transported']:
            return False
        # Check whether the unit is a ground unit.
        if self.focus.transported_type == 'ground':
            # If the unit is not in a city, cannot perform load action.
            if self.focus.pcity is None:
                return False
            # Get the current avaliable transporter
            self.focus.get_transporter()
            return self.focus.transporter is not None
        else:
            # Check air units and missile units later
            return False

    def _action_packet(self):
        # """Assuming only valid triggers"""
        # packet = {"pid": packet_unit_load,
        #           "cargo_id": self.focus.punit['id'],
        #           "transporter_id": self.focus.transporter['id'],
        #           "transporter_tile": self.focus.punit['tile']
        #           }
        packet = self.unit_do_action(
            self.focus.punit['id'],
            self.focus.transporter['id'],
            fc_types.ACTION_TRANSPORT_BOARD)
        self.wait_for_pid = (63, self.focus.punit['id'])
        return packet


class ActUnloadUnit(UnitAction):
    """A transporter performs this action to unload all units carried by it. This action does not cost move."""
    action_key = "unit_unload"

    def is_action_valid(self):
        # The unit cannot transport
        if self.focus.ptype['transport_capacity'] == 0 or 'occupied' not in self.focus.punit:
            return False

        if self.focus.punit['occupied'] == False:
            return False

        # Only when in a city, the transporter can unload all units.
        if self.focus.pcity == None:
            return False

        return True

    def _action_packet(self):
        # Get the units in the same tile. Note that not all these units are transported by the focus unit.
        units = self.focus.ptile['units']
        packets = []
        for unit in units:
            # The unit is transported by the focus transporter
            if unit['transported_by'] == self.focus.punit['id']:
                packets.append(self._unit_do_activity(unit['id'], fc_types.ACTIVITY_IDLE, EXTRA_NONE))
                packets.append(self.unit_do_action(
                    self.focus.punit["id"],
                    unit['id'],
                    fc_types.ACTION_TRANSPORT_UNLOAD))

        # for (var i = 0; i < units_on_tile.length; i++) {
        #     var punit = units_on_tile[i];

        #     if (punit['transported'] && punit['transported_by'] > 0
        #         && punit['owner'] == client.conn.playing.playerno) {
        #     request_new_unit_activity(punit, ACTIVITY_IDLE, EXTRA_NONE);
        #     request_unit_do_action(ACTION_TRANSPORT_DEBOARD, punit['id'],
        #                             punit['transported_by']);
        #     } else {
        #     request_new_unit_activity(punit, ACTIVITY_IDLE, EXTRA_NONE);
        #     request_unit_do_action(ACTION_TRANSPORT_UNLOAD,
        #                             punit['transported_by'],
        #                             punit['id']);
        #     }
        # }

        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return packets


class DiplomaticAction(UnitAction):
    """Base class for all diplomatic actions"""

    def is_action_valid(self):
        if self.focus.ptype['name'] in ["Spy", "Diplomat"]:
            return self.is_dipl_action_valid()
        return False

    def is_dipl_action_valid(self):
        """Abstract function to check validity of action -
           to be overwritten by specific diplomat action"""
        raise Exception("Not implemented - should be overwritten by %s" % self.__class__)


class ActSpyCityAction(DiplomaticAction):
    """Spy on city"""
    action_key = None
    action_id = None

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_dipl_action_valid(self):
        # return self.focus.pcity != None and action_prob_possible(self.focus.action_probabilities[self.action_id])
        return action_prob_possible(self.focus.action_prob[self.dir8][self.action_id])

    def _action_packet(self):
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        target_city = self.focus.unit_ctrl.city_ctrl.tile_city(newtile)
        if target_city is not None:
            self.target_city_id = target_city['id']
        else:
            self.target_city_id = -1
        # packet = self.unit_do_action(self.focus.punit["id"], self.focus.pcity['id'],
        #                              self.action_id)
        packet = self.unit_do_action(self.focus.punit["id"], self.target_city_id,
                                     self.action_id)
        # packet = {"pid": packet_unit_action_query,
        #           "diplomat_id": self.focus.punit['id'],
        #           "target_id": self.focus.pcity['id'],
        #           "action_type": self.action_id
        #           }
        if self.focus.ptype['name'].lower() == 'diplomat':
            self.wait_for_pid = (62, self.focus.punit['id'])
        elif self.focus.ptype['name'].lower() == 'spy':
            self.wait_for_pid = (63, self.focus.punit['id'])
        else:
            raise AssertionError('Unit type error in ActSpyCityAction.')
        return packet

# class ActSpySteal(DiplomaticAction):


class ActSpyStealTech(ActSpyCityAction):
    """ The player may change his mind after selecting targeted tech theft and
        * go for the untargeted version after concluding that no listed tech is
        * worth the extra risk. """
    action_key = 'spy_steal_tech'
    action_id = fc_types.ACTION_SPY_STEAL_TECH


class ActSpyStealTechESC(ActSpyStealTech):
    """Action to steal technology and then escape- unspecific"""
    action_key = 'spy_steal_tech_esc'
    action_id = fc_types.ACTION_SPY_STEAL_TECH_ESC


class ActSpyStealTechTargeted(ActSpyStealTech):
    """Action to steal specific technology"""
    action_key = 'sply_steal_tech_targeted'
    action_id = fc_types.ACTION_SPY_TARGETED_STEAL_TECH

    def __init__(self, cur_focus):
        super().__init__(cur_focus)
        self._prep_tech_tree()

    def _prep_tech_tree(self):
        self.tech_valid = dict([(tech_id, False) for tech_id in self.focus.techs])

    def is_dipl_action_valid(self):
        self._prep_tech_tree()
        if not ActSpyStealTech.is_dipl_action_valid():
            return self.tech_valid

        for tech_id in self.focus.rule_ctrl.techs:
            tgt_kn = is_tech_known(self.focus.unit_ctrl.player_ctrl.city_owner(self.focus.pcity), tech_id)

            if not tgt_kn:
                continue

            """ Can steal a tech if the target player knows it and the actor player
            * has the pre requirements. Some rulesets allows the player to steal
            * techs the player don't know the prereqs of."""

            # /* Actor and target player tech known state. */
            self.tech_valid[tech_id] = is_tech_prereq_known(self.focus.pplayer, tech_id)

        return self.tech_valid

    def set_target_tech(self, tech_id):
        self.tech_id = tech_id

    def _action_packet(self):
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.focus.pcity['id'],
                                     self.action_id,
                                     self.tech_id)
        return packet


class ActSpyStealTechTargetedESC(ActSpyStealTechTargeted):
    action_key = 'spy_steal_tech_targeted_esc'
    action_id = fc_types.ACTION_SPY_TARGETED_STEAL_TECH_ESC


class ActSpySabotageCity(ActSpyCityAction):
    """Sabotage City"""
    action_key = 'spy_sabotage_city'
    action_id = fc_types.ACTION_SPY_SABOTAGE_CITY


class ActSpySabotageCityESC(ActSpyCityAction):
    """Sabotage City"""
    action_key = 'spy_sabotage_city_esc'
    action_id = fc_types.ACTION_SPY_SABOTAGE_CITY_ESC


class ActSpyInciteCity(ActSpyCityAction):
    """Incite City"""
    action_key = 'spy_incite_city'
    action_id = fc_types.ACTION_SPY_INCITE_CITY


class ActSpyInciteCityESC(ActSpyCityAction):
    """Incite City"""
    action_key = 'spy_incite_city_esc'
    action_id = fc_types.ACTION_SPY_INCITE_CITY_ESC


class ActSpyUnitAction(DiplomaticAction):
    """Base class for spy actions against units"""
    action_id = None
    action_key = None

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_dipl_action_valid(self):
        # return self.focus.target_unit != None and action_prob_possible(self.focus.action_probabilities[self.action_id])
        return action_prob_possible(self.focus.action_prob[self.dir8][self.action_id])

    def _action_packet(self):
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        if len(newtile['units']) > 0:
            self.target_unit_id = newtile['units'][0]['id']
        else:
            self.target_unit_id = -1
        # packet = {"pid": packet_unit_action_query,
        #           "diplomat_id": self.focus.punit['id'],
        #           "target_id": self.target_unit_id,
        #           "action_type": self.action_id
        #           }
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_unit_id,
                                     self.action_id)

        self.wait_for_pid = (63, self.focus.punit['id'])
        return packet


class ActSpyBribeUnit(ActSpyUnitAction):
    """ Bribe Unit"""
    action_id = fc_types.ACTION_SPY_BRIBE_UNIT
    action_key = "spy_bribe_unit"


class ActSpyUpgradeUnit(ActSpyUnitAction):
    """Upgrade Unit"""
    action_id = fc_types.ACTION_UPGRADE_UNIT
    """
    target_units = self.tile_units(target_tile)
        if target_unit != None and len(target_units) > 1:
            act_id, packet = self._select_tgt_unit(actor_unit, target_tile, target_units)
            action_options[act_id] = packet
    """
    @staticmethod
    def _select_tgt_unit(actor_unit, target_tile, potential_tgt_units):
        """Create a dialog where a unit select what other unit to act on."""
        action_options = {}

        for tgt_unit in potential_tgt_units:
            packet = {"pid": fc_types.packet_unit_get_actions,
                      "actor_unit_id": actor_unit["id"],
                      "target_unit_id": tgt_unit["id"],
                      "target_tile_id": target_tile["id"],
                      "disturb_player": True
                      }

            action_options[tgt_unit['id']] = packet
        return action_options

    def popup_bribe_dialog(self, actor_unit, target_unit, cost, act_id):
        """Show the player the price of bribing the unit and, if bribing is
        possible, allow him to order it done."""

        bribe_possible = cost <= self.unit_ctrl.unit_owner(actor_unit)['gold']
        packet = self.unit_do_action(actor_unit['id'], target_unit['id'], act_id, sending=False)

        return bribe_possible, packet

    def popup_incite_dialog(self, actor_unit, target_city, cost, act_id):
        """
            Show the player the price of inviting the city and, if inciting is
            possible, allow him to order it done.
        """
        incite_possible = cost != INCITE_IMPOSSIBLE_COST and cost <= self.unit_ctrl.unit_owner(actor_unit)['gold']
        packet = self.unit_do_action(actor_unit['id'], target_city['id'], act_id, sending=False)
        return incite_possible, packet

    def popup_unit_upgrade_dlg(self, actor_unit, target_city, cost, act_id):
        """
            Show the player the price of upgrading the unit and, if upgrading is
            affordable, allow him to order it done.
        """
        upgrade_possible = cost <= self.unit_ctrl.unit_owner(actor_unit)['gold']
        packet = self.unit_do_action(actor_unit['id'], target_city['id'], act_id, sending=False)
        return upgrade_possible, packet

    def popup_sabotage_dialog(self, actor_unit, target_city, city_imprs, act_id):
        """Select what improvement to sabotage when doing targeted sabotage city."""
        action_options = {}
        # /* List the alternatives */
        for i in range(self.rule_ctrl.ruleset_control["num_impr_types"]):
            improvement = self.rule_ctrl.improvements[i]
            if city_imprs.isSet(i) and improvement['sabotage'] > 0:
                """ The building is in the city. The probability of successfully
                   * sabotaging it as above zero. """

                packet = self.unit_do_action(actor_unit['id'], target_city['id'], act_id,
                                             encode_building_id(improvement['id']),
                                             sending=False)
                action_options[improvement["id"]] = packet


class ActGoto(StdAction):
    """Moved the unit in focus in the specified direction."""
    action_key = "goto"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.dir8 = dir8
        self.action_key += "_%i" % dir8
        self.newtile = None
        self.move_dir = None

    def is_action_valid(self):
        # if self.focus.punit['transported']:
        # return False
        # print(f"unit id: {self.focus.punit['id']}")
        # print(self.focus.action_prob.keys())
        if not action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_UNIT_MOVE]):
            return False
        self.newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        if not self.focus.unit_ctrl.can_actor_unit_move(self.focus.punit, self.newtile):
            return False
        target_idx = self.focus.map_ctrl.index_to_tile(self.focus.punit["tile"])
        self.move_dir = self.focus.map_ctrl.get_direction_for_step(target_idx, self.newtile)

        return not (self.move_dir is None or self.move_dir == -1)

    def _action_packet(self):
        actor_unit = self.focus.punit
        dir8 = self.move_dir
        target_tile = self.newtile
        # packet = {"pid"       : packet_unit_orders,
        #           "unit_id"   : actor_unit['id'],
        #           "src_tile"  : actor_unit['tile'],
        #           "length"    : 1,
        #           "repeat"    : False,
        #           "vigilant"  : False,
        #           "orders"    : [ORDER_MOVE],
        #           "dir"       : [dir8],
        #           "activity"  : [ACTIVITY_LAST],
        #           "target"    : [EXTRA_NONE],
        #           "action"    : [ACTION_COUNT],
        #           "dest_tile" : target_tile['index'],
        #           "extra"     : [EXTRA_NONE]
        #           }
        packet = {"pid": fc_types.packet_unit_orders,
                  "unit_id": actor_unit['id'],
                  "src_tile": actor_unit['tile'],
                  "length": 1,
                  "repeat": False,
                  "vigilant": False,
                  "orders": [{"order": fc_types.ORDER_MOVE,
                              "activity": fc_types.ACTIVITY_LAST,
                              "target": EXTRA_NONE,
                              "sub_target": 0,
                              "action": fc_types.ACTION_COUNT,
                              "dir": dir8
                              }],
                  #   "extra"     : [EXTRA_NONE]
                  "dest_tile": target_tile['index']
                  }
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return packet


class ActHutEnter(StdAction):
    """Moved the unit in focus in the specified direction."""
    action_key = "hut_enter"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.dir8 = dir8
        self.action_key += "_%i" % dir8
        self.newtile = None
        self.move_dir = None

    def is_action_valid(self):
        # if self.focus.punit['transported']:
        # return False
        if not action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_HUT_ENTER]):
            return False
        self.newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        if not self.focus.unit_ctrl.can_actor_unit_move(self.focus.punit, self.newtile):
            return False
        target_idx = self.focus.map_ctrl.index_to_tile(self.focus.punit["tile"])
        self.move_dir = self.focus.map_ctrl.get_direction_for_step(target_idx, self.newtile)

        return not (self.move_dir is None or self.move_dir == -1)

    def _action_packet(self):
        # When the unit is on a certain activity, we need to cancel the order before we enter hut.
        if self.focus.punit['activity'] != fc_types.ACTIVITY_IDLE:
            cancel_order_action = ActCancelOrder(self.focus)
            cancel_order_action.trigger_action(self.focus.unit_ctrl.ws_client)
        self.wait_for_pid = (63, self.focus.punit['id'])
        # self.wait_for_pid = 63
        return self.unit_do_action(self.focus.punit['id'],
                                   self.newtile['index'],
                                   fc_types.ACTION_HUT_ENTER)

# Use ActGetActionPro to replace this action
# class ActGetAttackPro(UnitAction):
#     """Attack unit on target tile"""
#     action_key = "get_attack"

#     def __init__(self, focus, dir8):
#         super().__init__(focus)
#         self.action_key += "_%i" % dir8
#         self.dir8 = dir8

#     def is_action_valid(self):
#         # The dir8 direction has an enemy unit
#         # TODO: we assume only one unit in the tile for now
#         if self.dir8 in self.focus.enemy_units:
#             # It seems that the target_unit_id in the _action_packet does not matter for now. The target_tile_id is required.
#             self.target_unit_id = self.focus.enemy_units[self.dir8][0]['id']
#             self.target_tile_id = self.focus.enemy_units[self.dir8][0]['tile']
#         else:
#             self.target_unit_id = None
#             self.target_tile_id = None

#         unit_type = self.focus.ptype
#         # TODO: check which unit types cannot perform the attack action.
#         worker = unit_type['worker'] or unit_type['name'] == 'Explorer'
#         return self.target_unit_id != None and not worker

#     def _action_packet(self):
#         actor_unit = self.focus.punit
#         packet = {"pid": packet_unit_get_actions,
#                   "actor_unit_id": actor_unit['id'],
#                   "target_tile_id": self.target_tile_id,
#                   "target_unit_id": self.target_unit_id,
#                   "target_extra_id": -1,
#                   "request_kind": 0
#                   }
#         self.wait_for_pid = 90

#         return packet

# TODO: the pro from the current server is inaccurate for build_road and pillage action. Add more notes if find other inaccurate action pro. Fix those actions if the server is updated to provide accurate pro in the future.


class ActGetActionPro(UnitAction):
    """Attack unit on target tile"""
    action_key = "get_action_pro"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        if self.dir8 == map_const.DIR8_STAY:
            newtile = self.focus.ptile
            self.target_tile_id = newtile['index']

            # if self.focus.punit['id'] == 886:
            #     for u in newtile['units']:
            #         print(u)

            # if len(newtile['units']) > 0:
            #     self.target_unit_id = []
            #     for idx in range(len(newtile['units'])):
            #         self.target_unit_id.append(newtile['units'][idx]['id'])
            # else:
            #     self.target_unit_id = -1
            self.target_unit_id = -1

            # self.target_city = self.focus.unit_ctrl.city_ctrl.tile_city(newtile)
            # if self.target_city == None:
            #     self.target_city_id = -1
            # else:
            #     self.target_city_id = self.target_city['id']
            # if self.focus.punit['id'] in [1549, 1099, 886, 1964, 1912]:
            #     print(self.target_city_id)
            # extra = newtile['extras']
            # set_bits = find_set_bits(extra)
            # if len(set_bits) == 0:
            #     self.target_extra_id = [-1]
            # else:
            #     self.target_extra_id = set_bits+[-1]
            # fc_logger.info(f"self.focus.punit['id']: {self.focus.punit['id']}, extras: {set_bits}, self.target_extra_id: {self.target_extra_id}")
            # # elif len(set_bits) == 1:
            # #     self.target_extra_id = set_bits[0]
            # # else:
            # #     self.target_extra_id = set_bits

            self.target_extra_id = -1
        else:
            newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
            if newtile is None:
                self.focus.action_prob[self.dir8] = [{'min': 0, 'max': 0}]*(fc_types.ACTION_COUNT+1)
                return False
            self.target_tile_id = newtile['index']
            if len(newtile['units']) > 0:
                self.target_unit_id = []
                for idx in range(len(newtile['units'])):
                    self.target_unit_id.append(newtile['units'][idx]['id'])
            else:
                self.target_unit_id = -1
                # self.target_city = self.focus.unit_ctrl.city_ctrl.tile_city(newtile)
                # if self.target_city == None:
                #     self.target_city_id = -1
                # else:
                #     self.target_city_id = self.target_city['id']
                # extra = newtile['extras']
                # set_bits = find_set_bits(extra)
                # if len(set_bits) == 0:
                #     self.target_extra_id = -1
                # elif len(set_bits) == 1:
                #     self.target_extra_id = set_bits[0]
                # else:
                #     self.target_extra_id = set_bits
            self.target_extra_id = -1
        return True

    def _action_packet(self):
        if type(self.target_extra_id) == int and type(self.target_unit_id) == int:
            actor_unit = self.focus.punit
            packet = {"pid": fc_types.packet_unit_get_actions,
                      "actor_unit_id": actor_unit['id'],
                      "target_tile_id": self.target_tile_id,
                      # "target_city_id": self.target_city_id,
                      "target_unit_id": self.target_unit_id,
                      "target_extra_id": self.target_extra_id,
                      "request_kind": 1
                      }
            self.wait_for_pid = (90, self.focus.punit['id'])
            # self.wait_for_pid = 90
            return packet
        else:
            if type(self.target_extra_id) == list and type(self.target_unit_id) == int:
                packets = []
                self.wait_for_pid = (90, self.focus.punit['id'])
                # self.wait_for_pid = 90
                for extra_id in self.target_extra_id:
                    actor_unit = self.focus.punit
                    packet = {"pid": fc_types.packet_unit_get_actions,
                              "actor_unit_id": actor_unit['id'],
                              "target_tile_id": self.target_tile_id,
                              # "target_city_id": self.target_city_id,
                              "target_unit_id": self.target_unit_id,
                              "target_extra_id": extra_id,
                              "request_kind": 1
                              }
                    packets.append(packet)
                return packets

            if type(self.target_extra_id) == int and type(self.target_unit_id) == list:
                packets = []
                self.wait_for_pid = (90, self.focus.punit['id'])
                # self.wait_for_pid = 90
                for unit_id in self.target_unit_id:
                    actor_unit = self.focus.punit
                    packet = {"pid": fc_types.packet_unit_get_actions,
                              "actor_unit_id": actor_unit['id'],
                              "target_tile_id": self.target_tile_id,
                              # "target_city_id": self.target_city_id,
                              "target_unit_id": unit_id,
                              "target_extra_id": self.target_extra_id,
                              "request_kind": 1
                              }
                    packets.append(packet)
                return packets

            # Both target_extra_id and target_unit_id is a list. We currently do not handle this case.
            actor_unit = self.focus.punit
            packet = {"pid": fc_types.packet_unit_get_actions,
                      "actor_unit_id": actor_unit['id'],
                      "target_tile_id": self.target_tile_id,
                      # "target_city_id": self.target_city_id,
                      "target_unit_id": self.target_unit_id[0],
                      "target_extra_id": self.target_extra_id[0],
                      "request_kind": 1
                      }
            self.wait_for_pid = (90, self.focus.punit['id'])
            # self.wait_for_pid = 90
            return packet


class ActNuke(UnitAction):
    """Start a goto that will end in the unit(s) detonating in a nuclear explosion."""
    action_key = "nuke"

    def is_action_valid(self):
        return self.focus.ptype["name"] == "Nuclear"

    def key_unit_nuke(self):
        # /* The last order of the goto is the nuclear detonation. */
        self.activate_goto_last(fc_types.ORDER_PERFORM_ACTION, fc_types.ACTION_NUKE)


class ActEmbassyStay(UnitAction):
    """Establish embassy. This action will consume the unit."""
    action_key = "embassy_stay"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_ESTABLISH_EMBASSY_STAY):
            return False
        return action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_ESTABLISH_EMBASSY_STAY])

    def _action_packet(self):
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)

        target_city = self.focus.city_ctrl.tile_city(newtile)
        if target_city != None:
            self.target_city_id = target_city['id']

        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_city_id,
                                     fc_types.ACTION_ESTABLISH_EMBASSY_STAY)

        self.wait_for_pid = (62, self.focus.punit['id'])
        return packet


class ActAttack(UnitAction):
    """Attack unit on target tile"""
    action_key = "attack"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_ATTACK):
            return False
        return action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_ATTACK])

    def _action_packet(self):
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        self.target_tile_id = newtile['index']
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_tile_id,
                                     fc_types.ACTION_ATTACK)

        self.wait_for_pid = (65, self.focus.punit['id'])
        return packet


class ActConquerCity(UnitAction):
    """Conquer city on target tile"""
    action_key = "conquer_city"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_CONQUER_CITY):
            return False
        return action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_CONQUER_CITY])

    def _action_packet(self):
        # When the unit is on a certain activity, we need to cancel the order before we conquer.
        if self.focus.punit['activity'] != fc_types.ACTIVITY_IDLE:
            cancel_order_action = ActCancelOrder(self.focus)
            cancel_order_action.trigger_action(self.focus.unit_ctrl.ws_client)
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        pcity = self.focus.city_ctrl.tile_city(newtile)
        self.target_city_id = pcity['id']
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_city_id,
                                     fc_types.ACTION_CONQUER_CITY)

        self.wait_for_pid = (63, self.focus.punit['id'])
        return packet


class ActInvestigateSpend(UnitAction):
    """Investigate the city with a diplomat. This action will consume the unit."""
    action_key = "investigate_spend"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_INV_CITY_SPEND):
            return False
        return action_prob_possible(self.focus.action_prob[self.dir8][fc_types.ACTION_INV_CITY_SPEND])

    def _action_packet(self):
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        pcity = self.focus.city_ctrl.tile_city(newtile)
        self.target_city_id = pcity['id']
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_city_id,
                                     fc_types.ACTION_INV_CITY_SPEND)

        # Investigate city should get city additional info as a response.
        self.wait_for_pid = (256, self.target_city_id)
        return packet


class ActDisembark(UnitAction):
    """Disembark a transported unit on target tile. This action costs the unit's move."""
    action_key = "disembark"

    def __init__(self, focus, dir8):
        super().__init__(focus)
        self.action_key += "_%i" % dir8
        self.dir8 = dir8

    def is_action_valid(self):
        # if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_TRANSPORT_DISEMBARK1):
        #     return False

        self.action_key = None
        valid_key_num = 0
        # We check for all disembark key because we are not sure which disembark key corresponds to which situation.
        for key in [fc_types.ACTION_TRANSPORT_DISEMBARK1, fc_types.ACTION_TRANSPORT_DISEMBARK2, fc_types.
                    ACTION_TRANSPORT_DISEMBARK3, fc_types.ACTION_TRANSPORT_DISEMBARK4]:
            if action_prob_possible(self.focus.action_prob[self.dir8][key]):
                self.action_key = key
                valid_key_num += 1
        # We assume there is only one valid disembark action for a given situation.
        assert (valid_key_num < 2)
        return self.action_key != None

    def _action_packet(self):
        # When the unit is on a certain activity, we need to cancel the order before we disembark.
        if self.focus.punit['activity'] != fc_types.ACTIVITY_IDLE:
            cancel_order_action = ActCancelOrder(self.focus)
            cancel_order_action.trigger_action(self.focus.unit_ctrl.ws_client)

        self.wait_for_pid = (63, self.focus.punit['id'])
        newtile = self.focus.map_ctrl.mapstep(self.focus.ptile, self.dir8)
        self.target_tile_id = newtile['index']
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_tile_id,
                                     self.action_key)
        return packet


class ActEmbark(UnitAction):
    """Embark a unit on a target transporter. This action costs the unit's move."""
    action_key = "embark"

    def __init__(self, focus, dir8, target_unit_id):
        super().__init__(focus)
        self.action_key += f'_{dir8}_{target_unit_id}'
        self.target_unit_id = target_unit_id
        # We store the direction in case the observation needs this information
        self.dir8 = dir8

    def is_action_valid(self):
        if not self.utype_can_do_action(self.focus.punit, fc_types.ACTION_TRANSPORT_EMBARK):
            return False

        # Only when the action is added, the is_action_valid() can be called. Since this action targets a unit, we consider it as valid as long as we add it.
        return True

    def _action_packet(self):
        # When the unit is on a certain activity, we need to cancel the order before we embark.
        if self.focus.punit['activity'] != fc_types.ACTIVITY_IDLE:
            cancel_order_action = ActCancelOrder(self.focus)
            cancel_order_action.trigger_action(self.focus.unit_ctrl.ws_client)
        self.wait_for_pid = (63, self.focus.punit['id'])
        packet = self.unit_do_action(self.focus.punit['id'],
                                     self.target_unit_id,
                                     fc_types.ACTION_TRANSPORT_EMBARK)
        return packet


def order_wants_direction(order, act_id, ptile):

    #  Returns True if the order preferably should be performed from an
    #  adjacent tile.

    action = actions[act_id]
    if order == fc_types.ORDER_PERFORM_ACTION and action == None:
        # /* Bad action id or action rule data not received and stored
        # * properly. */
        logger.warning("Asked to put invalid action " + act_id + " in an order.")
        return False

    if order in [fc_types.ORDER_MOVE, ORDER_ACTION_MOVE]:
        return True
    elif order == fc_types.ORDER_PERFORM_ACTION:
        if action['min_distance'] > 0:
            # Always illegal to do to a target on the actor's own tile.
            return True

        if action['max_distance'] < 1:
            # Always illegal to perform to a target on a neighbor tile. */
            return False

        # FIXME: allied units and cities shouldn't always make actions be
        # performed from the neighbor tile.

        if tile_city(ptile) != None or tile_units(ptile).length != 0:
            # Won't be able to move to the target tile to perform the action on top of it.
            return True

        return False
    else:
        return False
