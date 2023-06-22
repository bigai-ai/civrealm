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

from freecivbot.utils.base_action import Action, ActionList
from freecivbot.utils.fc_types import packet_player_research, packet_player_tech_goal
from freecivbot.research.tech_helpers import is_tech_unknown, is_tech_prereq_known


class TechActions(ActionList):
    def __init__(self, ws_client, rule_ctrl):
        ActionList.__init__(self, ws_client)
        self.rule_ctrl = rule_ctrl

    def _can_actor_act(self, actor_id):
        return True

    def update(self, pplayer):
        actor_id = "cur_player"
        if self.actor_exists(actor_id):
            return

        self.add_actor(actor_id)
        for tech_id in self.rule_ctrl.techs:
            tech_name = self.rule_ctrl.techs[tech_id]["name"]
            self.add_action(actor_id, ActChooseResearchTech(pplayer, tech_id, tech_name))
            self.add_action(actor_id, ActChooseResearchGoal(pplayer, tech_id, tech_name))


class ActChooseResearchTech(Action):
    action_key = "research_tech"

    def __init__(self, pplayer, new_tech_id, new_tech_name):
        Action.__init__(self)
        self.pplayer = pplayer
        self.new_tech_id = new_tech_id
        self.action_key += "_%s_%i" % (new_tech_name, new_tech_id)

    def is_action_valid(self):
        return is_tech_prereq_known(self.pplayer, self.new_tech_id)

    def _action_packet(self):
        packet = {"pid": packet_player_research, "tech": self.new_tech_id}
        return packet


class ActChooseResearchGoal(ActChooseResearchTech):
    action_key = "set_tech_goal"

    def is_action_valid(self):
        return is_tech_unknown(self.pplayer, self.new_tech_id)

    def _action_packet(self):
        packet = {"pid": packet_player_tech_goal, "tech": self.new_tech_id}
        return packet
