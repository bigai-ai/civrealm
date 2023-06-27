# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from freeciv_gym.freeciv.utils.fc_types import MAX_NUM_ITEMS
from freeciv_gym.freeciv.misc.freeciv_wiki import freeciv_wiki_docs

from freeciv_gym.freeciv.utils.base_controller import CivPropController
from freeciv_gym.freeciv.research.tech_state import TechState
from freeciv_gym.freeciv.research.tech_actions import TechActions
from freeciv_gym.freeciv.research.tech_helpers import is_tech_known

"""
/* TECH_KNOWN is self-explanatory, TECH_PREREQS_KNOWN are those for which all
 * requirements are fulfilled all others (including those which can never
 * be reached) are TECH_UNKNOWN */
"""

AR_ONE = 0
AR_TWO = 1
AR_ROOT = 2
AR_SIZE = 3


TF_BONUS_TECH = 0  # /* player gets extra tech if rearched first */
TF_BRIDGE = 1  # /* "Settler" unit types can build bridges over rivers */
TF_RAILROAD = 2  # /* "Settler" unit types can build rail roads */
TF_POPULATION_POLLUTION_INC = 3  # /* Increase the pollution factor created by population by one */
TF_FARMLAND = 4  # /* "Settler" unit types can build farmland */
TF_BUILD_AIRBORNE = 5  # /* Player can build air units */
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
A_FUTURE = A_LAST + 2
A_UNKNOWN = A_LAST + 3
A_LAST_REAL = A_UNKNOWN

A_NEVER = None
U_NOT_OBSOLETED = None


class TechCtrl(CivPropController):
    def __init__(self, ws_client, rule_ctrl, player_ctrl):
        super().__init__(ws_client)
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.reqtree = None

        self.prop_state = TechState(rule_ctrl, self)
        self.prop_actions = TechActions(ws_client, rule_ctrl)
        self.is_tech_tree_init = False
        self.wikipedia_url = "http://en.wikipedia.org/wiki/"

    def register_all_handlers(self):
        pass

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
        if not is_tech_known(pplayer, punittype['build_reqs'][0]['value']):
            return False

        # FIXME: add support for global advances, check for building reqs etc.*/

        return True
