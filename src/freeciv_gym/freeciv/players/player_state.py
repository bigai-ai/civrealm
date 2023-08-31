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

from freeciv_gym.freeciv.utils.base_state import PlainState
import freeciv_gym.freeciv.tech.tech_const as tech_const
import freeciv_gym.freeciv.players.player_const as player_const


# from freeciv_gym.freeciv.players.player_ctrl import PlayerCtrl
# from freeciv_gym.freeciv.players.diplomacy import DiplomacyState
# from freeciv_gym.freeciv.game.ruleset import RulesetCtrl
# from freeciv_gym.freeciv.connectivity.client_state import ClientState


class PlayerState(PlainState):
    # def __init__(self, rule_ctrl: RulesetCtrl, player_ctrl: PlayerCtrl, clstate: ClientState, diplstates: DiplomacyState, players):
    def __init__(self, rule_ctrl, player_ctrl, clstate, diplstates, players):
        super().__init__()
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.clstate = clstate

        self.diplstates = diplstates
        self.players = players

        self.player_fields = ["culture", "researching_cost", "gold", "government", "is_alive",
                              "luxury", "mood", "nation", "net_income", "revolution_finishes",
                              "science", "science_cost", "score", "target_government", "tax",
                              "tech_goal", "tech_upkeep", "techs_researched", "total_bulbs_prod",
                              "turns_alive"]

    @property
    def my_player_id(self):
        return self.clstate.player_num()

    @property
    def my_player(self):
        return self.players[self.my_player_id]

    def _update_state(self, player):
        if self._state == {}:
            self._state.update(dict([("my_" + key, None) for key in self.player_fields]))

        self._state['my_player_id'] = self.my_player_id
        self._state.update(
            dict([("my_" + key, value) for key, value in self.my_player.items() if key in self.player_fields]))
        no_humans = 0
        no_ais = 0

        for pnum, opp_id in enumerate(self.players):
            opponent = self.players[opp_id]
            if opponent == self.my_player:
                continue
            self._update_opponent_state(self.my_player, opponent, "opponent_%i_" % pnum)
            if opponent["is_alive"]:
                if opponent['flags'][player_const.PLRF_AI] != 0:
                    no_ais += 1
                elif self.my_player['nturns_idle'] <= 4:
                    no_humans += 1

        self._state["no_humans"] = no_humans
        self._state["no_ais"] = no_ais

        # cbo = get_current_bulbs_output()
        # bulbs = cbo.self_bulbs - cbo.self_upkeep
        researched = self.my_player['bulbs_researched']
        if 'researching_cost' in self.my_player:
            research_cost = self.my_player['researching_cost']
        else:
            research_cost = 0

        self._state["research_progress"] = researched * 1. / research_cost if research_cost != 0 else 0

        self._state["team_no"] = self.my_player['team']
        self._state["embassy_txt"] = self.get_embassy_text(self.my_player_id)

    def _update_opponent_state(self, pplayer, opponent, op_id):
        """
            Get opponent intelligence with data depending on the establishment of an embassy.
        """

        self._state.update(dict([(op_id + a_field, None) for a_field in
                                 ["gov", "gov_name", "gold", "tax", "science", "luxury",
                                  "capital", "bulbs_researched", "researching_cost",
                                  "research_progress", "research", "research_name"]]))
        self._state.update(dict([(op_id + "invention_%i" % tech_id, None)
                                 for tech_id in self.rule_ctrl.techs]))

        self._state[op_id + "col_love"] = self.col_love(opponent)
        self._state[op_id + "plr_score"] = self.get_score_text(opponent)
        if opponent['flags'][player_const.PLRF_AI] != 0:
            self._state[op_id + "plr_type"] = self.get_ai_level_text(opponent) + " AI"
        else:
            self._state[op_id + "plr_type"] = "Human"

        if pplayer["real_embassy"][opponent["playerno"]]:
            self.show_intelligence_report_embassy(opponent, op_id)
        else:
            self.show_intelligence_report_hearsay(opponent, op_id)

    def show_intelligence_report_hearsay(self, pplayer, op_id):
        """ Return opponent intelligence intelligence when there's no embassy."""
        if pplayer['government'] > 0:
            self._state[op_id + "gov"] = pplayer['government']
            self._state[op_id + "gov_name"] = self.rule_ctrl.governments[pplayer['government']]['name']

        if pplayer['gold'] > 0:
            self._state[op_id + "gold"] = pplayer['gold']

        if "researching" in pplayer and pplayer['researching'] > 0 and pplayer['researching'] in self.rule_ctrl.techs:
            self._state[op_id + "research"] = pplayer['researching']
            self._state[op_id + "research_name"] = self.rule_ctrl.techs[pplayer['researching']]['name']

    def show_intelligence_report_embassy(self, pplayer, op_id):
        """ Return opponent intelligence intelligence when there's an embassy."""
        for a_field in ["gold", "tax", "science", "luxury"]:
            self._state[op_id + a_field] = pplayer[a_field]

        self._state[op_id + "gov"] = pplayer["government"]
        self._state[op_id + "gov_name"] = self.rule_ctrl.governments[pplayer['government']]['name']
        self._state[op_id + "capital"] = None

        research = self.player_ctrl.research_get(pplayer)

        if research != None:
            self._state[op_id + "research"] = research['researching']
            if research['researching'] in self.rule_ctrl.techs:
                self._state[op_id + "research_name"] = self.rule_ctrl.techs[research['researching']]['name']
                self._state[op_id + "bulbs_researched"] = research['bulbs_researched']
                self._state[op_id + "researching_cost"] = research['researching_cost']
                researched = research['bulbs_researched']
                research_cost = research['researching_cost']
                self._state[op_id + "research_progress"] = researched * 1. / research_cost if research_cost != 0 else 0

        for tech_id in self.rule_ctrl.techs:
            self._state[op_id + "invention_%i" % tech_id] = research['inventions'][tech_id] == tech_const.TECH_KNOWN

    def get_score_text(self, player):
        if (player['score'] >= 0 or self.clstate.client_is_observer()
                or player['playerno'] == self.my_player_id):
            return player['score']
        else:
            return "?"

    def col_love(self, pplayer):
        if (self.clstate.client_is_observer() or self.player_ctrl.player_is_myself(pplayer['playerno'])
                or not pplayer['flags'][player_const.PLRF_AI] > 0):
            return "-"
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
            return "-"

        pplayer = self.players[player_id]

        if player_id == self.my_player_id:
            return "-"
        elif self.my_player["real_embassy"][player_id] and pplayer['real_embassy'][self.my_player_id]:
            return "Both"
        elif self.my_player["real_embassy"][player_id]:
            return "We have embassy"
        elif pplayer['real_embassy'][self.my_player_id]:
            return "They have embassy"
        else:
            return "No embassy"

    @staticmethod
    def get_ai_level_text(player):
        ai_level = player['ai_skill_level']
        if 7 >= ai_level >= 0:
            return player_const.AI_SKILLS[ai_level]
        else:
            return "Unknown"
