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
from utils.fc_types import MAX_NUM_ITEMS, packet_player_research,\
    packet_player_tech_goal, RPT_CERTAIN, TRI_NO, VUT_NONE, TRI_YES, VUT_ADVANCE,\
    VUT_GOVERNMENT, VUT_IMPROVEMENT, VUT_TERRAIN, VUT_NATION, VUT_UTYPE,\
    VUT_UTFLAG, VUT_UCLASS, VUT_UCFLAG, VUT_OTYPE, VUT_SPECIALIST, VUT_MINSIZE,\
    VUT_AI_LEVEL, VUT_TERRAINCLASS, VUT_MINYEAR, VUT_TERRAINALTER, VUT_CITYTILE,\
    VUT_GOOD, VUT_TERRFLAG, VUT_NATIONALITY, VUT_BASEFLAG, VUT_ROADFLAG,\
    VUT_EXTRA, VUT_TECHFLAG, VUT_ACHIEVEMENT, VUT_DIPLREL, VUT_MAXTILEUNITS,\
    VUT_STYLE, VUT_MINCULTURE, VUT_UNITSTATE, VUT_MINMOVES, VUT_MINVETERAN,\
    VUT_MINHP, VUT_AGE, VUT_NATIONGROUP, VUT_TOPO, VUT_IMPR_GENUS, VUT_ACTION,\
    VUT_MINTECHS, VUT_EXTRAFLAG, VUT_MINCALFRAG, VUT_SERVERSETTING, TRI_MAYBE,\
    RPT_POSSIBLE, VUT_COUNT
from utils.freeciv_wiki import freeciv_wiki_docs
from utils.freecivlog import freelog

from connectivity.Basehandler import CivEvtHandler
from research.reqtree import reqtree_civ2civ3, reqtree_multiplayer, reqtree



"""
/* TECH_KNOWN is self-explanatory, TECH_PREREQS_KNOWN are those for which all
 * requirements are fulfilled all others (including those which can never
 * be reached) are TECH_UNKNOWN */
"""

TECH_UNKNOWN = 0
TECH_PREREQS_KNOWN = 1
TECH_KNOWN = 2

AR_ONE = 0
AR_TWO = 1
AR_ROOT = 2
AR_SIZE = 3


TF_BONUS_TECH = 0 #/* player gets extra tech if rearched first */
TF_BRIDGE = 1    #/* "Settler" unit types can build bridges over rivers */
TF_RAILROAD = 2  #/* "Settler" unit types can build rail roads */
TF_POPULATION_POLLUTION_INC = 3  #/* Increase the pollution factor created by population by one */
TF_FARMLAND = 4  #/* "Settler" unit types can build farmland */
TF_BUILD_AIRBORNE = 5 #/* Player can build air units */
TF_LAST = 6

"""
/*
  [kept for amusement and posterity]
typedef int Tech_type_id
  Above typedef replaces old "enum tech_type_id" see comments about
  Unit_type_id in unit.h, since mainly apply here too, except don't
  use Tech_type_id very widely, and don't use (-1) flag values. (?)
*/
/* [more accurately]
 * Unlike most other indices, the Tech_type_id is widely used, because it
 * so frequently passed to packet and scripting.  The client menu routines
 * sometimes add and substract these numbers.
 */
"""
A_NONE = 0
A_FIRST = 1
A_LAST = MAX_NUM_ITEMS
A_UNSET = A_LAST + 1
A_FUTURE  = A_LAST + 2
A_UNKNOWN = A_LAST + 3
A_LAST_REAL = A_UNKNOWN

A_NEVER = None
U_NOT_OBSOLETED = None

class TechCtrl(CivEvtHandler):
    def __init__(self, ws_client, rule_ctrl, player_ctrl):
        CivEvtHandler.__init__(self, ws_client)
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.reqtree = None
        self.tech_state = None
        self.tech_options = None
        self.is_tech_tree_init = False
        self.wikipedia_url = "http://en.wikipedia.org/wiki/"

    @staticmethod
    def player_invention_state(pplayer, tech_id):
        """
          Returns state of the tech for current pplayer.
          This can be: TECH_KNOWN, TECH_UNKNOWN, or TECH_PREREQS_KNOWN
          Should be called with existing techs or A_FUTURE

          If pplayer is None this checks whether any player knows the tech (used
          by the client).
        """
        if (pplayer is None) or ("inventions" not in pplayer) or tech_id >= len(pplayer["inventions"]):
            return TECH_UNKNOWN
        else:
            #/* Research can be None in client when looking for tech_leakage
            # * from player not yet received. */
            return pplayer['inventions'][tech_id]
            
        #/* FIXME: add support for global advances
        #if (tech != A_FUTURE and game_info.info.global_advances[tech_id]) {
        #  return TECH_KNOWN
        #} else {
        #  return TECH_UNKNOWN
        #}*/
            
    def get_current_state(self, pplayer):
        if self.tech_state is None:
            self.init_tech_state()

        for tech_id in self.tech_state.keys():
            ptech = self.rule_ctrl.techs[tech_id]
            cur_tech = self.tech_state[tech_id]
            cur_tech['is_researching'] =  pplayer['researching'] == ptech['id']
            cur_tech['is_tech_goal'] = pplayer['tech_goal'] == ptech['id']
            cur_tech['inv_state'] = TechCtrl.player_invention_state(pplayer, ptech['id'])
            cur_tech['is_req_for_goal'] = self.is_tech_req_for_goal(ptech['id'],
                                                                    pplayer['tech_goal'])

            cur_tech['reqs'] = {}
            for req in ptech['research_reqs']:
                req_active = ReqCtrl.is_req_active(pplayer, req, RPT_CERTAIN)
                self.tech_state[tech_id]['reqs'][req['value']] = req_active

    def get_current_options(self, pplayer):
        if self.tech_options is None:
            self.tech_options = {"cur_player": {}}
            for tech_id in self.tech_state.keys():
                act1 = ActChooseResearchTech(self.ws_client, pplayer, tech_id)
                act2 = ActChooseResearchGoal(self.ws_client, pplayer, tech_id)
                self.tech_options["cur_player"][act1.action_key] = act1
                self.tech_options["cur_player"][act2.action_key] = act2
        return self.tech_options

    def init_tech_state(self):
        if self.rule_ctrl.ruleset_control['name'] == "Civ2Civ3 ruleset":
            self.reqtree = reqtree_civ2civ3
        elif self.rule_ctrl.ruleset_control['name'] in ["Multiplayer ruleset", "Longturn-Web-X ruleset"]: 
            self.reqtree = reqtree_multiplayer
        else:
            self.reqtree = reqtree

        print(self.rule_ctrl.ruleset_control['name'])

        self.tech_state = {}
        for tech_id in self.rule_ctrl.techs:
            ptech = self.rule_ctrl.techs[tech_id]
            str_id = "%i"%tech_id
            if str_id not in self.reqtree or self.reqtree[str_id] is None:
                continue

            self.tech_state[tech_id] = cur_tech = {'name': ptech['name']}
            cur_tech['sup_units'] = self.rule_ctrl.get_units_from_tech(tech_id)
            cur_tech['sup_improvements'] = self.rule_ctrl.get_improvements_from_tech(tech_id)
        return self.tech_state

    def is_tech_req_for_goal(self, check_tech_id, goal_tech_id):
        """
         Determines if the technology 'check_tech_id' is a requirement
         for reaching the technology 'goal_tech_id'.
        """
        if check_tech_id == goal_tech_id:
            return True
        if goal_tech_id == 0 or check_tech_id == 0:
            return False

        if goal_tech_id not in self.rule_ctrl.techs:
            return False

        goal_tech = self.rule_ctrl.techs[goal_tech_id]

        for rid in goal_tech['req']:
            if rid == check_tech_id:
                return True
            elif self.is_tech_req_for_goal(check_tech_id, rid):
                return True
        return False

    def is_tech_req_for_tech(self, check_tech_id, next_tech_id):
        """
         Determines if the technology 'check_tech_id' is a direct requirement
         for reaching the technology 'next_tech_id'.
        """
        if check_tech_id == next_tech_id:
            return False
        if next_tech_id == 0 or check_tech_id == 0:
            return False

        next_tech = self.rule_ctrl.techs[next_tech_id]
        if next_tech is None:
            return False

        for rid in next_tech['req']:
            if check_tech_id == rid:
                return True
        return False

    def get_wiki_tech_info(self, tech_name):
        if freeciv_wiki_docs is None or freeciv_wiki_docs[tech_name] is None:
            return

        tech_info = freeciv_wiki_docs[tech_name]['summary']
        tech_url = self.wikipedia_url + freeciv_wiki_docs[tech_name]['title']
        return tech_url, tech_info

    def get_tech_info(self, unit_type_id, improvement_id):
        """Shows info about a tech, unit or improvement based on helptext and wikipedia."""
        tech_info = {}
        if unit_type_id != None:
            punit_type = self.rule_ctrl.unit_types[unit_type_id]
            for info_key in ["helptext", "build_cost", "attack_strength",
                             "defense_strength", "firepower", "hp", "move_rate",
                             "vision_radius_sq"]:
                tech_info[info_key] = punit_type[info_key]

        if improvement_id != None:
            tech_info["helptext"] = self.rule_ctrl.improvements[improvement_id]['helptext']

        return tech_info
    @staticmethod
    def can_player_build_unit_direct(pplayer, punittype):
        """
        Whether player can build given unit somewhere,
        ignoring whether unit is obsolete and assuming the
        player has a coastal city.
        """

        if TechCtrl.player_invention_state(pplayer, punittype['tech_requirement']) != TECH_KNOWN:
            return False

        #FIXME: add support for global advances, check for building reqs etc.*/

        return True

from utils.base_action import Action

class ActChooseResearchTech(Action):
    action_key = "research_tech"
    def __init__(self, ws_client, pplayer, new_tech_id):
        Action.__init__(self, ws_client)
        self.pplayer = pplayer
        self.new_tech_id = new_tech_id
        self.action_key += "_%i" % new_tech_id

    def is_action_valid(self):
        return TechCtrl.player_invention_state(self.pplayer, self.new_tech_id) == TECH_PREREQS_KNOWN

    def _action_packet(self):
        packet = {"pid" : packet_player_research, "tech" : self.new_tech_id}
        return packet

class ActChooseResearchGoal(ActChooseResearchTech):
    action_key = "set_tech_goal"
    def is_action_valid(self):
        return TechCtrl.player_invention_state(self.pplayer, self.new_tech_id) == TECH_UNKNOWN

    def _action_packet(self):
        packet = {"pid" : packet_player_tech_goal, "tech" : self.new_tech_id}
        return packet

"""
/* Range of requirements.
 * Used in the network protocol.
 * Order is important -- wider ranges should come later -- some code
 * assumes a total order, or tests for e.g. >= REQ_RANGE_PLAYER.
 * Ranges of similar types should be supersets, for example:
 *  - the set of Adjacent tiles contains the set of CAdjacent tiles,
 *    and both contain the center Local tile (a requirement on the local
 *    tile is also within Adjacent range)
 *  - World contains Alliance contains Player (a requirement we ourselves
 *    have is also within Alliance range). */
"""
REQ_RANGE_LOCAL = 0
REQ_RANGE_CADJACENT = 1
REQ_RANGE_ADJACENT = 2
REQ_RANGE_CITY = 3
REQ_RANGE_TRADEROUTE = 4
REQ_RANGE_CONTINENT = 5
REQ_RANGE_PLAYER = 6
REQ_RANGE_TEAM = 7
REQ_RANGE_ALLIANCE = 8
REQ_RANGE_WORLD = 9
REQ_RANGE_COUNT = 10  # /* keep this last */


class ReqCtrl(CivEvtHandler):
    def __init__(self, ws_client):
        CivEvtHandler.__init__(self, ws_client)
        self.requirements = {}
    @staticmethod
    def is_req_active(target_player, req, prob_type):
        """
          Checks the requirement to see if it is active on the given target.

          target gives the type of the target
          (player,city,building,tile) give the exact target
          req gives the requirement itself

          Make sure you give all aspects of the target when calling this function:
          for instance if you have TARGET_CITY pass the city's owner as the target
          player as well as the city itself as the target city.
        """

        result = TRI_NO
        """
          /* Note the target may actually not exist.  In particular, effects that
           * have a VUT_SPECIAL or VUT_TERRAIN may often be passed to this function
           * with a city as their target.  In this case the requirement is simply
           * not met. */
        """
        if req['kind'] == VUT_NONE:
            result = TRI_YES
        elif req['kind'] == VUT_ADVANCE:
            #/* The requirement is filled if the player owns the tech. */
            result = ReqCtrl.is_tech_in_range(target_player, req['range'], req['value'])
        elif req['kind'] in [VUT_GOVERNMENT, VUT_IMPROVEMENT, VUT_TERRAIN, VUT_NATION,
                             VUT_UTYPE, VUT_UTFLAG, VUT_UCLASS, VUT_UCFLAG, VUT_OTYPE,
                             VUT_SPECIALIST, VUT_MINSIZE, VUT_AI_LEVEL, VUT_TERRAINCLASS,
                             VUT_MINYEAR, VUT_TERRAINALTER, VUT_CITYTILE, VUT_GOOD, VUT_TERRFLAG,
                             VUT_NATIONALITY, VUT_BASEFLAG, VUT_ROADFLAG, VUT_EXTRA, VUT_TECHFLAG,
                             VUT_ACHIEVEMENT, VUT_DIPLREL, VUT_MAXTILEUNITS, VUT_STYLE,
                             VUT_MINCULTURE, VUT_UNITSTATE, VUT_MINMOVES, VUT_MINVETERAN,
                             VUT_MINHP, VUT_AGE, VUT_NATIONGROUP, VUT_TOPO, VUT_IMPR_GENUS,
                             VUT_ACTION, VUT_MINTECHS, VUT_EXTRAFLAG, VUT_MINCALFRAG,
                             VUT_SERVERSETTING]:

            #//FIXME: implement
            freelog("Unimplemented requirement type " + req['kind'])

        elif req['kind'] == VUT_COUNT:
            return False
        else:
            freelog("Unknown requirement type " + req['kind'])

        if result == TRI_MAYBE:
            return prob_type == RPT_POSSIBLE

        if req['present']:
            return result == TRI_YES
        else:
            return result == TRI_NO

    @staticmethod
    def are_reqs_active(target_player, reqs, prob_type):

        """
          Checks the requirement(s) to see if they are active on the given target.

          target gives the type of the target
          (player,city,building,tile) give the exact target

          reqs gives the requirement vector.
          The function returns TRUE only if all requirements are active.

          Make sure you give all aspects of the target when calling this function:
          for instance if you have TARGET_CITY pass the city's owner as the target
          player as well as the city itself as the target city.
        """

        for req in reqs:
            if not ReqCtrl.is_req_active(target_player, req, prob_type):
                return False
        return True

    @staticmethod
    def is_tech_in_range(target_player, trange, tech):
        """Is there a source tech within range of the target?"""

        if trange == REQ_RANGE_PLAYER:
            target = TRI_YES if TechCtrl.player_invention_state(target_player, tech) == TECH_KNOWN else TRI_NO
            return target_player != None and target

        elif trange in [REQ_RANGE_TEAM, REQ_RANGE_ALLIANCE, REQ_RANGE_WORLD]:
            #/* FIXME: Add support for the above ranges. Freeciv's implementation
            #* currently (25th Jan 2017) lives in common/requirements.c */
            freelog("Unimplemented tech requirement range " + range)
            return TRI_MAYBE
        elif trange in [REQ_RANGE_LOCAL, REQ_RANGE_CADJACENT, REQ_RANGE_ADJACENT,
                        REQ_RANGE_CITY, REQ_RANGE_TRADEROUTE, REQ_RANGE_CONTINENT,
                        REQ_RANGE_COUNT]:

            freelog("Invalid tech req range " + range)
            return TRI_MAYBE
        else:
            return TRI_MAYBE
