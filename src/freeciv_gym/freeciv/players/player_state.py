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

from typing import Dict

from freeciv_gym.freeciv.utils.base_state import ListState
import freeciv_gym.freeciv.tech.tech_const as tech_const
import freeciv_gym.freeciv.players.player_const as player_const

from freeciv_gym.freeciv.players.diplomacy import DiplomacyState
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
from freeciv_gym.freeciv.connectivity.client_state import ClientState


class PlayerState(ListState):
    def __init__(
            self, player_ctrl, rule_ctrl: RulesetCtrl, clstate: ClientState, diplstates: DiplomacyState,
            players: Dict[int, Dict]):
        super().__init__()
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.clstate = clstate

        self.diplstates = diplstates
        self.players = players

        self.common_player_fields = [
            'name', 'score', 'team', 'is_alive', 'nation',
            'score', 'turns_alive', 'government', 'researching', 'government_name', 'research_name']
        self.my_player_fields = [
            'gold', 'culture', 'luxury', 'mood', 'revolution_finishes', 'science', 'science_cost',
            'bulbs_researched', 'researching_cost', 'embassy_txt', 'tech_goal', 'tech_upkeep',
            'techs_researched', 'total_bulbs_prod', 'target_government', 'tax']
        self.other_player_fields = ['love']
        self.all_player_fields = self.common_player_fields + self.my_player_fields + self.other_player_fields

    @property
    def my_player_id(self):
        return self.clstate.player_num()

    @property
    def my_player(self):
        return self.players[self.my_player_id]

    def _update_state(self, player):
        for player_id, player in self.players.items():
            self._state[player_id] = self._get_player_state(player)

    def _get_player_state(self, player):
        player_state = dict([(key, None) for key in self.all_player_fields])
        player_state.update(dict([(f'tech_{tech_id}', None) for tech_id in self.rule_ctrl.techs]))

        player_state['player_id'] = player['playerno']
        player_state.update(dict(
            [(key, value) for key, value in player.items()
                if key in self.all_player_fields]))

        if player['playerno'] == self.my_player_id:
            player_state.update(self._get_my_player_state())
        else:
            player_state.update(self._get_other_player_state(player))

        if player_state['government'] in self.rule_ctrl.governments:
            player_state['government_name'] = self.rule_ctrl.governments[player_state['government']]['name']
        if player_state['researching'] in self.rule_ctrl.governments:
            player_state['research_name'] = self.rule_ctrl.governments[player_state['researching']]['name']

        return player_state

    def _get_my_player_state(self):
        player_state = {}
        player_state['love'] = None
        player_state['embassy_txt'] = self.get_embassy_text(self.my_player_id)
        return player_state

    def _get_other_player_state(self, opponent):
        """
            Get opponent intelligence with data depending on the establishment of an embassy.
        """
        player_state = {}
        player_state['love'] = self.col_love(opponent)

        if self.my_player['real_embassy'][opponent['playerno']]:
            player_state.update(self.show_intelligence_report_embassy(opponent))
        else:
            player_state.update(self.show_intelligence_report_hearsay(opponent))
        return player_state

    def show_intelligence_report_hearsay(self, opponent):
        """ Return opponent intelligence intelligence when there's no embassy."""
        player_state = {}
        if opponent['government'] > 0:
            player_state['government'] = opponent['government']

        if opponent['gold'] > 0:
            player_state['gold'] = opponent['gold']

        if 'researching' in opponent and opponent['researching'] > 0 and opponent['researching'] in self.rule_ctrl.techs:
            player_state['research'] = opponent['researching']
            player_state['research_name'] = self.rule_ctrl.techs[opponent['researching']]['name']
        return player_state

    def show_intelligence_report_embassy(self, opponent):
        """ Return opponent intelligence intelligence when there's an embassy."""
        player_state = {}
        for a_field in ['gold', 'tax', 'science', 'luxury']:
            player_state[a_field] = opponent[a_field]

        player_state['government'] = opponent['government']

        research = self.player_ctrl.research_get(opponent)

        if research != None:
            player_state['researching'] = research['researching']
            if research['researching'] in self.rule_ctrl.techs:
                player_state['bulbs_researched'] = research['bulbs_researched']
                player_state['researching_cost'] = research['researching_cost']

        for tech_id in self.rule_ctrl.techs:
            player_state[f'tech_{tech_id}'] = research['inventions'][tech_id] == tech_const.TECH_KNOWN
        return player_state

    def get_score_text(self, player):
        if (player['score'] >= 0 or self.clstate.client_is_observer()
                or player['playerno'] == self.my_player_id):
            return player['score']
        else:
            return '?'

    def col_love(self, pplayer):
        if (self.clstate.client_is_observer() or self.player_ctrl.player_is_myself(pplayer['playerno'])
                or not pplayer['flags'][player_const.PLRF_AI] > 0):
            return '-'
        else:
            return self.love_text(pplayer['love'][self.my_player_id])

    @staticmethod
    def love_text(love):
        """
           Return a text describing an AI's love for you.  (Oooh, kinky!!)
          These words should be adjectives which can fit in the sentence
          "The x are y towards us"
          "The Babylonians are respectful towards us"
        """

        love_sizes = [-90, -70, -50, -25, -10, 10, 25, 50, 70, 90]
        love_tags = player_const.ATTITUDE_TXT[: -1]
        for lsize, ltag in zip(love_sizes, love_tags):
            if love <= player_const.MAX_AI_LOVE * lsize / 100:
                return ltag
        return player_const.ATTITUDE_TXT[-1]

    def get_embassy_text(self, player_id):
        if self.clstate.client_is_observer():
            return '-'

        pplayer = self.players[player_id]

        if player_id == self.my_player_id:
            return '-'
        elif self.my_player['real_embassy'][player_id] and pplayer['real_embassy'][self.my_player_id]:
            return 'Both'
        elif self.my_player['real_embassy'][player_id]:
            return 'We have embassy'
        elif pplayer['real_embassy'][self.my_player_id]:
            return 'They have embassy'
        else:
            return 'No embassy'

    @staticmethod
    def get_ai_level_text(player):
        ai_level = player['ai_skill_level']
        if 7 >= ai_level >= 0:
            return player_const.AI_SKILLS[ai_level]
        else:
            return 'Unknown'
