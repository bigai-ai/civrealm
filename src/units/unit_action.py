'''
Created on 31.01.2018

@author: christian
'''
from connectivity.Basehandler import CivEvtHandler
from utils.fc_types import ACTION_FOUND_CITY, ACTIVITY_IDLE,\
    packet_unit_sscs_set
from utils.fc_types import USSDT_QUEUE

from units.unit_actions import ActDisband, ActTransform, ActForest, ActAirbase,\
    ActMine, ActFortress, ActIrrigation, ActFallout, ActPollution, ActAutoSettler,\
    ActExplore, ActParadrop, ActBuild, ActFortify, ActBuildRoad,\
    ActBuildRailRoad, ActHomecity, ActUnloadUnit, ActLoadUnit, ActPillage,\
    ActAirlift, ActUpgrade, ActNoorders, ActGoto, UnitAction

class FocusUnit():
    """Stores all relevant information for deciding on valid actions for the
    unit in focus"""
    def __init__(self, rule_ctrl, map_ctrl, unit_ctrl):
        self.rule_ctrl = rule_ctrl
        self.map_ctrl = map_ctrl
        self.unit_ctrl = unit_ctrl

        self.punit = None
        self.ptype = None
        self.ptile = None
        self.pcity = None
        self.pplayer = None
        self.units_on_tile = None

        self.obsolete_type = None
        self.transporter = None
        self.trans_capacity = None
        self.can_move = None
        self.move_dir = None
        self.action_probabilities = None

    def set_focus(self, punit, ptype, ptile, pcity, pplayer):
        """Sets the focus to unit punit having type ptype acting on ptile, pcity owned by pplayer"""
        self.punit = punit
        self.ptype = ptype
        self.ptile = ptile
        self.pcity = pcity
        self.pplayer = pplayer
        self.units_on_tile = self.tile_units(ptile)

        if ptype['obsoleted_by'] in self.rule_ctrl.unit_types:
            self.obsolete_type = self.rule_ctrl.unit_types[ptype['obsoleted_by']]
        else:
            self.obsolete_type = None

        self.transporter = None
        self.trans_capacity = 0

        self.can_move = self.unit_ctrl.can_actor_unit_move(punit, ptile)
        self.move_dir = self.map_ctrl.get_direction_for_step(self.map_ctrl.index_to_tile(punit["tile"]),
                                                             ptile) if self.can_move else None

        for tunit in self.units_on_tile:
            trans_type = self.rule_ctrl.unit_type(tunit)
            if trans_type['transport_capacity'] > 0:
                self.transporter = tunit
                self.trans_capacity = trans_type['transport_capacity']

    #Core functions to control focus units--------------------------------------------------
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
        self.trans_capacity = None
        self.can_move = None
        self.move_dir = None
        self.action_probabilities = None

class UnitActionCtrl(CivEvtHandler):
    def __init__(self, ws_client, map_ctrl, city_ctrl, rule_ctrl, unit_ctrl):
        CivEvtHandler.__init__(self, ws_client)
        self.map_ctrl = map_ctrl
        self.city_ctrl = city_ctrl
        self.rule_ctrl = rule_ctrl
        self.unit_ctrl = unit_ctrl

        self.action_classes = None

        self.focus = FocusUnit(rule_ctrl, map_ctrl, unit_ctrl)
        self.base_action = UnitAction(self.focus, ws_client)

        self.register_handler(44, "handle_city_name_suggestion_info")

    def _load_unit_actions(self):
        action_list = [ActDisband, ActTransform, ActMine, ActForest,
                                  ActFortress, ActAirbase, ActIrrigation, ActFallout,
                                  ActPollution, ActAutoSettler, ActExplore,
                                  ActParadrop, ActBuild, ActFortify, ActBuildRoad,
                                  ActBuildRailRoad, ActPillage, ActHomecity, ActAirlift,
                                  ActUpgrade, ActLoadUnit, ActUnloadUnit, ActNoorders, ActGoto
                                   #ActTileInfo, ActActSel, ActSEntry, ActWait, , ActNuke
                                   ]

        self.action_classes = dict([(action_class.action_key, action_class) for action_class in action_list])

    def set_current_focus(self, punit, ptype, ptile, pcity, pplayer):
        self.focus.set_focus(punit, ptype, ptile, pcity, pplayer)

    def _unit_can_still_act(self, punit):
        return punit['movesleft'] > 0 and not punit['done_moving'] and \
               not punit['ai']  and punit['activity'] == ACTIVITY_IDLE

    def get_action_options(self, dir8):
        if self.action_classes is None:
            self._load_unit_actions()
        action_options = dict([((action_key, dir8), None) for action_key in self.action_classes])
        if not self._unit_can_still_act(self.focus.punit):
            return action_options

        for action_key in self.action_classes.keys():
            action = self.action_classes[action_key](self.focus, self.ws_client)
            if action.is_action_valid():
                action.prepare_trigger()
                action_options[(action_key, dir8)] = action
        return action_options

    def request_unit_act(self, pval):
        funits = self._get_units_in_focus()
        for punit in funits:
            packet = {"pid": packet_unit_sscs_set, "unit_id" : punit['id'],
                      "type": USSDT_QUEUE,
                      "value"   : punit['tile'] if pval=="unit" else pval}

            #Have the server record that an action decision is wanted for this
            #unit.
            self.ws_client.send_request(packet)

    def request_unit_act_sel_vs(self, ptile):
        """An action selection dialog for the selected units against the specified
          tile is wanted."""
        self.request_unit_act(ptile['index'])

    def request_unit_act_sel_vs_own_tile(self):
        """An action selection dialog for the selected units against the specified
          unit"""
        self.request_unit_act("unit")

    def handle_city_name_suggestion_info(self, packet):
        """
      /* A suggested city name can contain an apostrophe ("'"). That character
       * is also used for single quotes. It shouldn't be added unescaped to a
       * string that later is interpreted as HTML. */
      /* TODO: Forbid city names containing an apostrophe or make sure that all
       * JavaScript using city names handles it correctly. Look for places
       * where a city name string is added to a string that later is
       * interpreted as HTML. Avoid the situation by directly using JavaScript
       * like below or by escaping the string. */
       """
        #/* Decode the city name. */
        #suggested_name = urllib.unquote(packet['name'])
        unit_id = packet['unit_id']
        """
        name_len = len(suggested_name)
        quoted_name = urllib.quote(suggested_name)
        print(packet)
        print(packet["name"])
        print(suggested_name)
        print(quoted_name)
        print(MAX_LEN_CITYNAME)
        if name_len == 0 or (name_len >= MAX_LEN_CITYNAME - 6) or (len(quoted_name) > MAX_LEN_CITYNAME - 6):
            raise Exception("City name is invalid. Please try a different shorter name.")
        """
        actor_unit = self.unit_ctrl.find_unit_by_number(unit_id)
        self.base_action.unit_do_action(unit_id, actor_unit['tile'],
                                        ACTION_FOUND_CITY, name=packet['name'], sending=True)

