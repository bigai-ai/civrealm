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


from civrealm.freeciv.misc.freeciv_wiki import freeciv_wiki_docs

from civrealm.freeciv.connectivity.civ_connection import CivConnection
from civrealm.freeciv.game.ruleset import RulesetCtrl
from civrealm.freeciv.players.player_ctrl import PlayerCtrl

from civrealm.freeciv.utils.base_controller import CivPropController
from civrealm.freeciv.tech.tech_state import TechState
from civrealm.freeciv.tech.tech_actions import TechActions

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


class TechCtrl(CivPropController):
    def __init__(self, ws_client: CivConnection, rule_ctrl: RulesetCtrl, player_ctrl: PlayerCtrl):
        super().__init__(ws_client)
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.reqtree = None

        self.prop_state = TechState(rule_ctrl, player_ctrl)
        self.prop_actions = TechActions(ws_client, rule_ctrl, player_ctrl)
        self.is_tech_tree_init = False
        self.wikipedia_url = "http://en.wikipedia.org/wiki/"

    def register_all_handlers(self):
        pass

    def get_wiki_tech_info(self, tech_name):
        if freeciv_wiki_docs is None or freeciv_wiki_docs[tech_name] is None:
            return None, None

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
