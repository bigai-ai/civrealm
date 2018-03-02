'''
Created on 13.02.2018

@author: christian
'''
from mapping.tile import TileState
from research.tech import TechCtrl, TECH_UNKNOWN, TECH_KNOWN, TECH_PREREQS_KNOWN
from city.city import CityState, INCITE_IMPOSSIBLE_COST
from game_info import ruleset
from copy import copy
from utils.fc_types import ACTION_UPGRADE_UNIT, packet_unit_do_action,\
    packet_unit_load, packet_unit_unload, ACTION_PARADROP, ACTION_AIRLIFT,\
    ACTIVITY_GEN_ROAD, ACTION_HOME_CITY, packet_unit_autosettlers,\
    ACTION_DISBAND_UNIT, ACTION_RECYCLE_UNIT, packet_city_name_suggestion_req,\
    ACTION_JOIN_CITY, ACTIVITY_FALLOUT, ACTIVITY_POLLUTION,\
    packet_unit_change_activity, ACTIVITY_IRRIGATE, ACTIVITY_BASE, ACTIVITY_MINE,\
    ACTIVITY_TRANSFORM, ACTIVITY_SENTRY, ACTIVITY_EXPLORE, ACTIVITY_PILLAGE,\
    ACTIVITY_FORTIFYING, ACTION_FOUND_CITY, packet_unit_orders, ORDER_MOVE,\
    ACTIVITY_LAST, ACTION_COUNT, ACTION_SPY_STEAL_TECH_ESC,\
    ACTION_SPY_INCITE_CITY_ESC, ACTION_SPY_STEAL_TECH,\
    ACTION_SPY_TARGETED_STEAL_TECH, ACTION_SPY_BRIBE_UNIT,\
    packet_unit_action_query, packet_unit_get_actions, ACTION_SPY_INCITE_CITY,\
    ACTION_SPY_TARGETED_SABOTAGE_CITY_ESC, ACTION_SPY_TARGETED_SABOTAGE_CITY,\
    ACTION_SPY_TARGETED_STEAL_TECH_ESC, ORDER_PERFORM_ACTION, ACTION_NUKE,\
    ACTION_ATTACK
from game_info.game import EXTRA_NONE
import urllib
from units.action_dialog import action_prob_possible, encode_building_id
from utils import base_action
from game_info.ruleset import EXTRA_RIVER, EXTRA_ROAD, EXTRA_RAIL

class UnitAction(base_action.Action):
    def __init__(self, cur_focus, ws_client):
        base_action.Action.__init__(self, ws_client)
        self.focus = cur_focus
        self.trigger_focus = None

    def prepare_trigger(self):
        self.trigger_focus = copy(self.focus)

    def trigger_action(self):
        if self.trigger_focus is None:
            raise Exception("Focus of trigger needs to be set via prepare_trigger")
        base_action.Action.trigger_action(self)

    def is_action_valid(self):
        raise Exception("Not implemented - To be implemented by specific Action classes")

    def _action_packet(self):
        raise Exception("Not implemented - To be implemented by specific Action classes")

    def unit_do_action(self, actor_id, target_id, action_type, value=0, name="", sending=True):
        """Tell server action of actor_id towards unit target_id with the respective
        action_type"""

        packet = {"pid"         : packet_unit_do_action,
                  "actor_id"    : actor_id,
                  "target_id"   : target_id,
                  "value"       : value,
                  "name"        : name,
                  "action_type" : action_type
                }
        if sending:
            self.ws_client.send_request(packet)
        else:
            return packet

    def _request_new_unit_activity(self, punit, activity, target):
        packet = {"pid" : packet_unit_change_activity, "unit_id" : punit['id'],
                  "activity" : activity, "target" : target }
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
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_SENTRY, EXTRA_NONE)

class ActWait(StdAction):
    """Tell the unit to wait (focus to next unit with moves left)"""
    action_key = "wait"
    def _action_packet(self):
        raise Exception("Irrelevant for Bot")

class ActNoorders(StdAction):
    """Tell the unit to have no orders this turn, set unit to done moving."""
    action_key = "noorders"
    def _action_packet(self):
        raise Exception("Irrelevant for Bot")
        #self.punit['done_moving'] = True

    def is_action_valid(self):
        return False

class ActDisband(StdAction):
    """Tell the units in focus to disband."""
    action_key = "disband"
    def _action_packet(self):
        #Do Recycle Unit if located inside a city.
        #FIXME: Only rulesets where the player can do Recycle Unit to all
        #domestic and allied cities are supported here.
        target_city = self.trigger_focus.pcity
        target_id = self.trigger_focus.punit['id'] if target_city is None else target_city['id']
        action_id = ACTION_DISBAND_UNIT if target_city is None else ACTION_RECYCLE_UNIT
        return self.unit_do_action(self.trigger_focus.punit['id'],target_id, action_id)

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

        packet = {"pid" : packet_info_text_req, "visible_unit" : punit_id,
                  "loc" : ptile['index'], "focus_unit": focus_unit_id}
        self.ws_client.send_request(packet)

class EngineerAction(UnitAction):
    def is_action_valid(self):
        if self.focus.ptype['name'] == "Engineers":
            return self.is_eng_action_valid()
        return False

    def is_eng_action_valid(self):
        raise Exception("Not implemented")

class ActTransform(EngineerAction):
    action_key = "transform"
    def is_eng_action_valid(self):
        return True
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_TRANSFORM, EXTRA_NONE)

class ActMine(EngineerAction):
    action_key = "mine"
    def is_eng_action_valid(self):
        return True
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_MINE, EXTRA_NONE)

class ActOnExtra(EngineerAction):
    """Base class for units that act on extras"""
    action_key = None
    def __init__(self, cur_focus, ws_client):
        EngineerAction.__init__(self, cur_focus, ws_client)
        self.extra_type = None

    def is_eng_action_valid(self):
        if self.extra_type is None:
            raise Exception("Extra type should be set")
        return TileState.tile_has_extra(self.focus.ptile, self.extra_type)

class ActForest(EngineerAction):
    """Action to create forest"""
    action_key = "forest"
    def is_eng_action_valid(self):
        terr_name = self.focus.rule_ctrl.tile_terrain(self.focus.ptile)['name']
        return terr_name == "Forest"
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_IRRIGATE, EXTRA_NONE)

class ActFortress(EngineerAction):
    """Action to create a fortress"""
    action_key = "fortress"
    def is_eng_action_valid(self):
        return TechCtrl.player_invention_state(self.focus.pplayer, 19) == TECH_KNOWN
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_BASE, EXTRA_NONE)


class ActAirbase(EngineerAction):
    """Action to create a airbase"""
    action_key = "airbase"
    def is_eng_action_valid(self):
        return TechCtrl.player_invention_state(self.focus.pplayer, 64) == TECH_KNOWN
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_BASE, ruleset.EXTRA_AIRBASE)

class ActIrrigation(ActOnExtra):
    """Action to create an irrigation"""
    action_key = "irrigation"
    def __init__(self, cur_focus, ws_client):
        self.extra_type = ruleset.EXTRA_IRRIGATION
        ActOnExtra.__init__(self, cur_focus, ws_client)
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_IRRIGATE, EXTRA_NONE)

class ActFallout(ActOnExtra):
    """Action to clean fallout"""
    action_key = "fallout"
    def __init__(self, cur_focus, ws_client):
        self.extra_type = ruleset.EXTRA_FALLOUT
        ActOnExtra.__init__(self, cur_focus, ws_client)
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_FALLOUT, EXTRA_NONE)
class ActPollution(ActOnExtra):
    """Action to remove pollution"""
    action_key = "pollution"
    def __init__(self, cur_focus, ws_client):
        self.extra_type = ruleset.EXTRA_POLLUTION
        ActOnExtra.__init__(self, cur_focus, ws_client)

    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_POLLUTION, EXTRA_NONE)

#-------Further unit specific actions
class ActAutoSettler(UnitAction):
    """Call to request (from the server) that the focus unit is put into autosettler mode."""
    action_key = "autosettlers"
    def is_action_valid(self):
        return self.focus.ptype["name"] in ["Settlers", "Workers", "Engineers"]

    def _action_packet(self):
        packet = {"pid" : packet_unit_autosettlers,
                  "unit_id" : self.trigger_focus.punit['id']}
        return packet

class ActExplore(UnitAction):
    action_key = "explore"
    def is_action_valid(self):
        return self.focus.ptype["name"] == "Explorer"

    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_EXPLORE, EXTRA_NONE)

class ActParadrop(UnitAction):
    """Tell the units to paradrop."""
    action_key = "paradrop"
    def is_action_valid(self):
        return self.focus.ptype["name"] == "Paratroopers"

    def _action_packet(self):
        return self.unit_do_action(self.trigger_focus.punit['id'],
                                   self.trigger_focus.ptile['index'],
                                   ACTION_PARADROP)

class ActBuild(UnitAction):
    """Request that a city is built."""
    action_key = "build"
    def __init__(self, cur_focus, ws_client):
        UnitAction.__init__(self, cur_focus, ws_client)
        self.next_city_name = None

    def is_action_valid(self):
        if self.focus.punit['movesleft'] == 0:
            raise Exception("Unit has no moves left to build city")
        return self.focus.ptype["name"] in ["Settlers", "Engineers"]

    def _action_packet(self):
        target_city = self.trigger_focus.pcity
        unit_id = self.trigger_focus.punit["id"]
        #Do Join City if located inside a city.
        if target_city is None:
            if self.next_city_name is None:
                packet = {"pid": packet_city_name_suggestion_req,
                          "unit_id": unit_id }
                return packet
            else:
                return self.found_new_city(unit_id)
        else:
            return self.unit_do_action(unit_id, target_city['id'], ACTION_JOIN_CITY)

    def set_next_city_name(self, suggested_name):
        self.next_city_name = suggested_name

    def found_new_city(self, unit_id):
        """Shows the Request city name dialog to the user."""
        actor_unit = self.trigger_focus.punit
        return self.unit_do_action(unit_id, actor_unit['tile'], ACTION_FOUND_CITY,
                                   name=urllib.quote(self.next_city_name, safe='~()*!.\''))

class ActFortify(UnitAction):
    action_key = "fortify"
    def is_action_valid(self):
        return not self.focus.ptype['name'] in ["Settlers", "Workers"]
    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_FORTIFYING, EXTRA_NONE)


class ActBuildRoad(EngineerAction):
    """Tell the units in focus to build road."""
    action_key = "road"
    def is_eng_action_valid(self):
        road_known = TechCtrl.player_invention_state(self.focus.pplayer, 8) == TECH_KNOWN
        tile_no_river = not TileState.tile_has_extra(self.focus.ptile, EXTRA_RIVER)
        no_road_yet = not TileState.tile_has_extra(self.focus.ptile, EXTRA_ROAD)
        return road_known and tile_no_river and no_road_yet

    def _action_packet(self):
        extra_id = self.focus.rule_ctrl.extras['Road']['id']
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_GEN_ROAD, extra_id)

class ActBuildRailRoad(EngineerAction):
    """Tell the units in focus to build or railroad."""
    action_key = "railroad"
    def is_eng_action_valid(self):
        railroad_known = TechCtrl.player_invention_state(self.focus.pplayer, 65) == TECH_KNOWN
        already_road = TileState.tile_has_extra(self.focus.ptile, EXTRA_ROAD)
        no_rail_yet = TileState.tile_has_extra(self.focus.ptile, EXTRA_RAIL)
        return railroad_known and already_road and no_rail_yet

    def _action_packet(self):
        extra_id = self.focus.rule_ctrl.extras['Railroad']['id']
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_GEN_ROAD, extra_id)

class ActPillage(UnitAction):
    action_key = "pillage"
    def is_action_valid(self):
        tile_valid = self.focus.pcity is None or (self.focus.pcity != None and \
                                                  CityState.city_owner_player_id(self.focus.pcity) != self.focus.pplayer["playerno"])
        return self.focus.pplayer != None and self.focus.ptype['attack_strength'] > 0 and tile_valid

    def _action_packet(self):
        return self._request_new_unit_activity(self.trigger_focus.punit,
                                               ACTIVITY_PILLAGE, EXTRA_NONE)

class ActHomecity(UnitAction):
    """Changes unit homecity to the city on same tile."""
    action_key = "homecity"
    def is_action_valid(self):
        if self.focus.pcity is None:
            return False
        return self.focus.punit['homecity'] not in [0, self.focus.pcity['id']]

    def _action_packet(self):
        return self.unit_do_action(self.trigger_focus.punit['id'],
                                   self.trigger_focus.pcity['id'], ACTION_HOME_CITY)

class ActAirlift(UnitAction):
    """Tell the units to airlift."""
    action_key = "airlift"
    def is_action_valid(self):
        if self.focus.pcity is None:
            return False
        return self.focus.rule_ctrl.city_has_building(self.focus.pcity, 0)

    def _action_packet(self):
        return self.unit_do_action(self.trigger_focus.punit['id'],
                                   self.trigger_focus.pcity['id'],
                                   ACTION_AIRLIFT)

class ActUpgrade(UnitAction):
    """Tell units to upgrade"""
    action_key = "upgrade"
    def is_action_valid(self):
        if self.focus.pcity is None:
            return False
        return self.focus.ptype != None and self.focus.obsolete_type != None and \
               TechCtrl.can_player_build_unit_direct(self.focus.pplayer, self.focus.obsolete_type)

    def _action_packet(self):
        target_id = self.trigger_focus.pcity['id'] if self.trigger_focus.pcity != None else 0
        return self.unit_do_action(self.trigger_focus.punit['id'], target_id, ACTION_UPGRADE_UNIT)

class ActLoadUnit(UnitAction):
    """Tell the units in focus to load on a transport."""
    action_key = "unit_load"
    def is_action_valid(self):
        if self.focus.pcity is None:
            return False

        return self.focus.trans_capacity > 0 and \
               self.focus.transporter["id"] != self.focus.punit["id"]

    def _action_packet(self):
        """Assuming only valid triggers"""
        packet = {"pid"      : packet_unit_load,
                  "cargo_id" : self.trigger_focus.punit['id'],
                  "transporter_id"   : self.trigger_focus.transporter['id'],
                  "transporter_tile" : self.trigger_focus.punit['tile']
                  }
        return packet

class ActUnloadUnit(UnitAction):
    """Unload unit from transport"""
    action_key = "unit_unload"
    def is_action_valid(self):
        return self.focus.punit['transported'] and self.focus.punit['transported_by'] > 0

    def _action_packet(self):
        """Assuming only valid triggers"""
        packet = {"pid"         : packet_unit_unload,
                  "cargo_id"    : self.trigger_focus.punit['id'],
                  "transporter_id" : self.trigger_focus.punit['transported_by']
                 }
        return packet

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

class ActSpySteal(DiplomaticAction):
    """ The player may change his mind after selecting targeted tech theft and
        * go for the untargeted version after concluding that no listed tech is
        * worth the extra risk. """
    action_id = ACTION_SPY_STEAL_TECH
    def __init__(self, cur_focus, ws_client):
        DiplomaticAction.__init__(self, cur_focus, ws_client)
        self.tech_id = None

    def is_dipl_action_valid(self):
        if self.focus.pcity is None or self.focus.action_probabilities is None:
            return False
        return action_prob_possible(self.focus.action_probabilities[self.action_id])

    def set_target_tech(self, tech_id):
        """Select technology that should be targeted by spy"""
        self.tech_id = tech_id

    def _action_packet(self):
        packet = self.unit_do_action(self.trigger_focus.punit["id"], self.trigger_focus.pcity['id'],
                                     self.action_id, sending=False)
        return packet

class ActSpyStealESC(ActSpySteal):
    """Action to steal technology - unspecific"""
    action_id = ACTION_SPY_STEAL_TECH_ESC

class ActSpyStealTargeted(ActSpySteal):
    """Action to steal specific technology"""
    action_id = ACTION_SPY_TARGETED_STEAL_TECH
    def __init__(self, cur_focus, ws_client):
        ActSpySteal.__init__(self, cur_focus, ws_client)
        self._prep_tech_tree()

    def _prep_tech_tree(self):
        self.tech_valid = dict([(tech_id, False) for tech_id in self.focus.techs])

    def is_dipl_action_valid(self):
        self._prep_tech_tree()
        if not ActSpySteal.is_dipl_action_valid():
            return self.tech_valid

        for tech_id in self.focus.rule_ctrl.techs:
            tgt_kn = TechCtrl.player_invention_state(city_owner(self.pcity), tech_id)

            if tgt_kn != TECH_KNOWN:
                continue
            #/* Actor and target player tech known state. */
            act_kn = TechCtrl.player_invention_state(self.focus.pplayer, tech_id)

            """ Can steal a tech if the target player knows it and the actor player
            * has the pre requirements. Some rulesets allows the player to steal
            * techs the player don't know the prereqs of."""

            self.tech_valid[tech_id] = act_kn == TECH_PREREQS_KNOWN

        return self.tech_valid

    def set_target_tech(self, tech_id):
        self.tech_id = tech_id

    def _action_packet(self):
        packet = self.unit_do_action(self.trigger_focus.punit['id'],
                                     self.trigger_focus.pcity['id'],
                                     self.action_id,
                                     self.tech_id, sending=False)
        return packet

class ActSpyStealTargetedESC(ActSpyStealTargeted):
    action_id = ACTION_SPY_TARGETED_STEAL_TECH_ESC

class ActSpyCityAction(DiplomaticAction):
    """Spy on city"""
    action_id = None
    def is_dipl_action_valid(self):
        return self.focus.pcity != None and action_prob_possible(self.focus.action_probabilities[self.action_id])

    def _action_packet(self):
        packet = {"pid"         : packet_unit_action_query,
                  "diplomat_id" : self.trigger_focus.punit['id'],
                  "target_id"   : self.trigger_focus.pcity['id'],
                  "action_type" : self.action_id
                }
        return packet

class ActSpySabotageCity(ActSpyCityAction):
    """Sabotage City"""
    action_id = ACTION_SPY_TARGETED_SABOTAGE_CITY

class ActSpySabotageCityESC(ActSpyCityAction):
    """Sabotage City"""
    action_id = ACTION_SPY_TARGETED_SABOTAGE_CITY_ESC

class ActSpyInciteCity(ActSpyCityAction):
    """Incite City"""
    action_id = ACTION_SPY_INCITE_CITY

class ActSpyInciteCityESC(ActSpyCityAction):
    """Incite City"""
    action_id = ACTION_SPY_INCITE_CITY_ESC

class ActSpyUnitAction(DiplomaticAction):
    """Base class for spy actions against units"""
    action_id = None
    def is_dipl_action_valid(self):
        return self.focus.target_unit != None and action_prob_possible(self.focus.action_probabilities[self.action_id])

    def _action_packet(self):
        packet = {"pid"         : packet_unit_action_query,
                  "diplomat_id" : self.trigger_focus.punit['id'],
                  "target_id"   : self.trigger_focus.target_unit['id'],
                  "action_type" : self.action_id
                }
        return packet

class ActSpyBribeUnit(ActSpyUnitAction):
    """ Bribe Unit"""
    action_id = ACTION_SPY_BRIBE_UNIT

class ActSpyUpgradeUnit(ActSpyUnitAction):
    """Upgrade Unit"""
    action_id = ACTION_UPGRADE_UNIT
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
            packet = {"pid"            : packet_unit_get_actions,
                      "actor_unit_id"  : actor_unit["id"],
                      "target_unit_id" : tgt_unit["id"],
                      "target_tile_id" : target_tile["id"],
                      "disturb_player" : True
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
        #/* List the alternatives */
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

    def is_action_valid(self):
        dir8 = self.focus.move_dir
        return not (dir8 is None or dir8 == -1)

    def _action_packet(self):
        actor_unit = self.trigger_focus.punit
        dir8 = self.trigger_focus.move_dir
        target_tile = self.trigger_focus.ptile
        packet = {"pid"       : packet_unit_orders,
                  "unit_id"   : actor_unit['id'],
                  "src_tile"  : actor_unit['tile'],
                  "length"    : 1,
                  "repeat"    : False,
                  "vigilant"  : False,
                  "orders"    : [ORDER_MOVE],
                  "dir"       : [dir8],
                  "activity"  : [ACTIVITY_LAST],
                  "target"    : [EXTRA_NONE],
                  "action"    : [ACTION_COUNT],
                  "dest_tile" : target_tile['index']
                  }
        return packet

class ActNuke(UnitAction):
    """Start a goto that will end in the unit(s) detonating in a nuclear explosion."""
    action_key = "nuke"
    def is_action_valid(self):
        return self.focus.ptype["name"] == "Nuclear"

    def key_unit_nuke(self):
        #/* The last order of the goto is the nuclear detonation. */
        self.activate_goto_last(ORDER_PERFORM_ACTION, ACTION_NUKE)

class ActAttack(UnitAction):
    """Attack unit on target tile"""
    action_key = "attack"
    def is_action_valid(self):
        return action_prob_possible(self.focus.action_probabilities[ACTION_ATTACK])

    def _action_packet(self):
        return self.unit_do_action(self.trigger_focus.punit['id'],
                                   self.trigger_focus.ptile['index'],
                                   ACTION_ATTACK,
                                   sending=False)

    """
    def order_wants_direction(order, act_id, ptile):

        #  Returns True if the order preferably should be performed from an
        #  adjacent tile.

        action = actions[act_id]
        if order == ORDER_PERFORM_ACTION and action == None:
            #/* Bad action id or action rule data not received and stored
            # * properly. */
            freelog("Asked to put invalid action " + act_id + " in an order.")
            return False

        if order in [ORDER_MOVE, ORDER_ACTION_MOVE]:
            return True
        elif order == ORDER_PERFORM_ACTION:
            if action['min_distance'] > 0:
                #Always illegal to do to a target on the actor's own tile.
                return True

            if action['max_distance'] < 1:
                #Always illegal to perform to a target on a neighbor tile. */
                return False

            #FIXME: allied units and cities shouldn't always make actions be
            #performed from the neighbor tile.

            if tile_city(ptile) != None or tile_units(ptile).length != 0:
                #Won't be able to move to the target tile to perform the action on top of it.
                return True

            return False
        else:
            return False


    def activate_goto(self):
        #Activate a regular goto.
        self.map_ctrl.clear_goto_tiles()
        self.activate_goto_last(ORDER_LAST, ACTION_COUNT)

    def activate_goto_last(self, last_order, last_action):
        #Activate a goto and specify what to do once there.
        self.goto_active = True
        #/* Set what the unit should do on arrival. */
        self.goto_last_order = last_order
        self.goto_last_action = last_action

        if len(self.current_focus) == 0:
            self.deactivate_goto(False)

    def deactivate_goto(self):
        self.goto_active = False

        self.goto_request_map = {}
        self.goto_turns_request_map = {}
        self.map_ctrl.clear_goto_tiles()

        #/* Clear the order this action would have performed. */
        self.goto_last_order = ORDER_LAST
        self.goto_last_action = ACTION_COUNT

    def handle_goto_path(self, packet):
        raise Exception("Go to has been disabled for Bot")
        #if goto_active:
        #    update_goto_path(packet)

    def get_goto_options(self, ptile):
        if current_focus.length <= 0:
            return {}

        #send goto order for all units in focus.
        for punit in current_focus:
            #Get the path the server sent using PACKET_GOTO_PATH.
            goto_path = goto_request_map[punit['id'] + "," + ptile['x'] + "," + ptile['y']]
            if goto_path == None:
                continue

            #The tile the unit currently is standing on.
            old_tile = index_to_tile(punit['tile'])

            #Create an order to move along the path. */
            #Create an order to move along the path.
            packet = {
                "pid"      : packet_unit_orders,
                "unit_id"  : punit['id'],
                "src_tile" : old_tile['index'],
                "length"   : goto_path['length'],
                "repeat"   : False,
                "vigilant" : False,
                "dest_tile": ptile['index']}
                #/* Each individual order is added later. */

                #/* Add each individual order. */
            packet['orders'] = []
            packet['dir'] = []
            packet['activity'] = []
            packet['target'] = []
            packet['action'] = []


            for i in range(goto_path['length']):
                #/* TODO: Have the server send the full orders in stead of just the
                #* dir part. Use that data in stead. */

                if goto_path['dir'][i] == -1:
                    #Assume that this means refuel.
                    packet['orders'][i] = ORDER_FULL_MP
                elif goto_path['length'] != i + 1:
                    #Don't try to do an action in the middle of the path.
                    packet['orders'][i] = ORDER_MOVE
                else:
                    #It is OK to end the path in an action.
                    packet['orders'][i] = ORDER_ACTION_MOVE

                packet['dir'][i] = goto_path['dir'][i]
                packet['activity'][i] = ACTIVITY_LAST
                packet['target'][i] = EXTRA_NONE
                packet['action'][i] = ACTION_COUNT

            if goto_last_order != ORDER_LAST:
                #/* The final order is specified. */
                #/* Should the final order be performed from the final tile or
                #* from the tile before it? In some cases both are legal. */
                if (not order_wants_direction(goto_last_order, goto_last_action,
                                             ptile)):
                    #/* Append the final order. */
                    pos = packet['length']

                    #/* Increase orders length */
                    packet['length'] = packet['length'] + 1

                    #/* Initialize the order to "empthy" values. */
                    packet['orders'][pos] = ORDER_LAST
                    packet['dir'][pos] = -1
                    packet['activity'][pos] = ACTIVITY_LAST
                    packet['target'][pos] = EXTRA_NONE
                    packet['action'][pos] = ACTION_COUNT
                else:
                    #/* Replace the existing last order with the final order */
                    pos = packet['length'] - 1

                #/* Set the final order. */
                packet['orders'][pos] = goto_last_order

                #/* Perform the final action. */
                packet['action'][pos] = goto_last_action

            #/* The last order has now been used. Clear it. */
            goto_last_order = ORDER_LAST
            goto_last_action = ACTION_COUNT

        if punit['id'] != goto_path['unit_id']:
            #/* Shouldn't happen. Maybe an old path wasn't cleared out. */
            console.log("Error: Tried to order unit " + punit['id']
                      + " to move along a path made for unit "
                      + goto_path['unit_id'])
            return

        #/* Send the order to move using the orders system. */
        self.ws_client.send_request(packet)
        if punit['movesleft'] > 0:
            unit_move_sound_play(punit)
        elif (not has_movesleft_warning_been_shown):
            has_movesleft_warning_been_shown = True
            ptype = unit_type(punit)
            message_log.update({
                event: E_BAD_COMMAND,
                message: ptype['name'] + " has no moves left. Press turn done for the next turn."
                })

        clear_goto_tiles()


    def get_tile_options(self, ptile, qtype, first_time_called):
        #Handles everything when the user clicked a tile

        if ptile == None or client_is_observer():
            return

        sunits = self.tile_units(ptile)
        pcity = self.city_ctrl.tile_city(ptile)

        if goto_active:
            self.get_goto_options(self, ptile)
            #deactivate_goto(True)
            #update_unit_focus()
        elif current_focus.length > 0:
            request_unit_act_sel_vs(ptile)
        else:
            if pcity != None:
                if pcity['owner'] == client.conn.playing.playerno:
                    if (sunits != None and sunits.length > 0
                        and sunits[0]['activity'] == ACTIVITY_IDLE):
                        set_unit_focus_and_redraw(sunits[0])

                    elif (not goto_active):
                        show_city_dialog(pcity)
                return

            if sunits != None and sunits.length == 0:
                #/* Clicked on a tile with no units. */
                set_unit_focus_and_redraw(None)

            elif (sunits != None and sunits.length > 0 ):
                if sunits[0]['owner'] == client.conn.playing.playerno:
                    if sunits.length == 1:
                        #/* A single unit has been clicked with the mouse. */
                        var unit = sunits[0]
                        set_unit_focus_and_activate(unit)
                    else:
                        #/* more than one unit is on the selected tile. */
                        set_unit_focus_and_redraw(sunits[0])
                        update_active_units_dialog()

                elif (pcity == None):
                    #// clicked on a tile with units owned by other players.
                    current_focus = sunits
                    #$("#game_unit_orders_default").hide()
                    update_active_units_dialog()

def request_goto_path(unit_id, dst_x, dst_y):
    #Request GOTO path for unit with unit_id, and dst_x, dst_y in map coords.
    if goto_request_map[unit_id + "," + dst_x + "," + dst_y] == None:
        goto_request_map[unit_id + "," + dst_x + "," + dst_y] = True

        packet = {"pid" : packet_goto_path_req, "unit_id" : unit_id,
                  "goal" : map_pos_to_tile(dst_x, dst_y)['index']}

        self.ws_client.send_request(packet)
        current_goto_turns = None
        $("#unit_text_details").html("Choose unit goto")
        setTimeout(update_mouse_cursor, 700)
    else:
        update_goto_path(goto_request_map[unit_id + "," + dst_x + "," + dst_y])

def check_request_goto_path():
    if (goto_active and current_focus.length > 0
        and prev_mouse_x == mouse_x and prev_mouse_y == mouse_y):

        var ptile
        clear_goto_tiles()
        if (renderer == RENDERER_2DCANVAS) {
          ptile = canvas_pos_to_tile(mouse_x, mouse_y)
        } else {
          ptile = webgl_canvas_pos_to_tile(mouse_x, mouse_y)
        }
        if (ptile != None) {
          /* Send request for goto_path to server. */
          for (var i = 0 i < current_focus.length i++) {
            request_goto_path(current_focus[i]['id'], ptile['x'], ptile['y'])
          }
        }
      }
      prev_mouse_x = mouse_x
      prev_mouse_y = mouse_y

    }

/****************************************************************************
  Show the GOTO path in the unit_goto_path packet.
****************************************************************************/
function update_goto_path(goto_packet)
{
  var punit = units[goto_packet['unit_id']]
  if (punit == None) return
  var t0 = index_to_tile(punit['tile'])
  var ptile = t0
  var goaltile = index_to_tile(goto_packet['dest'])

  if (renderer == RENDERER_2DCANVAS) {
    for (var i = 0 i < goto_packet['dir'].length i++) {
      if (ptile == None) break
      var dir = goto_packet['dir'][i]

      if (dir == -1) {
        /* Assume that this means refuel. */
        continue
      }

      ptile['goto_dir'] = dir
      ptile = mapstep(ptile, dir)
    }
  } else {
    webgl_render_goto_line(ptile, goto_packet['dir'])
  }

  current_goto_turns = goto_packet['turns']

  goto_request_map[goto_packet['unit_id'] + "," + goaltile['x'] + "," + goaltile['y']] = goto_packet
  goto_turns_request_map[goto_packet['unit_id'] + "," + goaltile['x'] + "," + goaltile['y']]
      = current_goto_turns

  if (current_goto_turns != undefined) {
    $("#active_unit_info").html("Turns for goto: " + current_goto_turns)
  }
  update_mouse_cursor()
}


        further_actions = [quicksave, civclient_benchmark(0), show_debug_info,
                           send_end_turn]

    def city_dialog_activate_unit(self, punit):
        self._request_new_unit_activity(punit, ACTIVITY_IDLE, EXTRA_NONE)

    """
