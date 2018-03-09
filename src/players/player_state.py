'''
Created on 08.03.2018

@author: christian
'''
from utils.base_state import PlainState
from research.tech_helpers import TECH_KNOWN

MAX_NUM_PLAYERS = 30
MAX_AI_LOVE = 1000
#/* The plr_flag_id enum. */
PLRF_AI = 0
PLRF_SCENARIO_RESERVED = 1
PLRF_COUNT = 2
AI_SKILLS = ["Away", "Handicapped", "Novice", "Easy", "Normal", "Hard", "Cheating", "Experimental"]

class PlayerState(PlainState):
    def __init__(self, rule_ctrl, player_ctrl, clstate, diplstates, players):
        PlainState.__init__(self)
        self.rule_ctrl = rule_ctrl
        self.player_ctrl = player_ctrl
        self.clstate = clstate
        
        self.diplstates = diplstates
        self.players = players
    
    def _update_state(self, pplayer):
        player_id = pplayer["playerno"]
        player_fields = ["culture", "current_research_cost", "gold", "government", "is_alive", 
                 "luxury", "mood", "nation", "net_income", "revolution_finishes", 
                 "science", "science_cost", "score", "target_government", "tax", 
                 "tech_goal", "tech_upkeep", "techs_researched", "total_bulbs_prod",
                 "turns_alive"]
         
        self._state.update(dict([(key,value) for key,value in pplayer.items() if key in player_fields]))
        no_humans = 0
        no_ais = 0
        
        for pnum, opp_id in enumerate(self.players):
            opponent = self.players[opp_id]
            if opponent == pplayer:
                continue
            self._update_opponent_state(pplayer, opponent, "opponent_%i" % pnum)
            if opponent["is_alive"]:
                if opponent['flags'][PLRF_AI] != 0:
                    no_ais += 1
                elif pplayer['nturns_idle'] <= 4:
                    no_humans += 1
        
        self._state["no_humans"] = no_humans
        self._state["no_ais"] = no_ais
        
        #cbo = get_current_bulbs_output()
        #bulbs = cbo.self_bulbs - cbo.self_upkeep
        researched = pplayer['bulbs_researched']
        research_cost = pplayer['current_research_cost']
        self._state["research_progress"] = researched * 1. / research_cost if research_cost != 0 else 0

        self._state["team_no"] = pplayer['team']
        self._state["embassy_txt"] = self.get_embassy_text(player_id)
    
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
        if opponent['flags'][PLRF_AI] != 0:
            self._state[op_id + "plr_type"] = self.get_ai_level_text(opponent) + " AI"
        else:
            self._state[op_id + "plr_type"] = "Human"
        
        if pplayer["real_embassy"][opponent["playerno"]]:
            self.update_opponent_state_embassy(opponent, op_id)
        else:
            self.update_opponent_state_hearsay(opponent, op_id)
        
        self._state[op_id]
    
    def update_opponent_state_hearsay(self, pplayer, op_id):
        """ Return opponent intelligence intelligence when there's no embassy."""
    
        if pplayer['government'] > 0:
            self._state[op_id + "gov"] = pplayer['government']
            self._state[op_id + "gov_name"] = self.rule_ctrl.governments[pplayer['government']]['name']
    
        if pplayer['gold'] > 0:
            self._state[op_id + "gold"] = pplayer['gold']
    
        if "researching" in pplayer and pplayer['researching'] > 0 and pplayer['researching'] in self.rule_ctrl.techs:
            self._state[op_id + "research"] = pplayer['researching']
            self._state[op_id + "research_name"] = self.rule_ctrl.techs[pplayer['researching']]['name']
    
    def update_opponent_state_embassy(self, pplayer, op_id):
        """ Return opponent intelligence intelligence when there's an embassy."""
        
        for a_field in ["gold", "tax", "science", "luxury"]:
            self._state[op_id + a_field] = pplayer[a_field]
        
        self._state[op_id + "gov"] = pplayer["government"]
        self._state[op_id + "gov_name"] = self.rule_ctrl.governments[pplayer['government']]['name']
        self._state[op_id + "capital"] = None
        #TODO:To be implemented
        
        research = self.player_ctrl.research_get(pplayer)
        
        #TODO: future techs
        
        if research != None:
            self._state[op_id + "research"] = research['researching']
            if research['researching'] in self.rule_ctrl.techs:
                self._state[op_id + "research_name"] = self.rule_ctrl.techs[research['researching']]['name']
                self._state[op_id + "bulbs_researched"] = research['bulbs_researched']
                self._state[op_id + "researching_cost"] = research['researching_cost']
                researched = research['bulbs_researched']
                research_cost = research['current_research_cost']
                self._state[op_id + "research_progress"] = researched * 1. / research_cost if research_cost != 0 else 0
        
        for tech_id in self.rule_ctrl.techs:
            self._state[op_id + "invention_%i" % tech_id] = research['inventions'][tech_id] == TECH_KNOWN
    
    def get_score_text(self, player):
        if (player['score'] > 0 or self.clstate.client_is_observer()
            or (self.clstate.is_playing() and player['playerno'] == self.clstate.cur_player()['playerno'])):
            return player['score']
        else:
            return "?"
    
    def col_love(self, pplayer):
        if (self.clstate.client_is_observer() or self.player_ctrl.player_is_myself(pplayer['playerno'])
            or not pplayer['flags'][PLRF_AI]> 0):
            return "-"
        else:
            return self.love_text(pplayer['love'][self.clstate.cur_player()['playerno']])

    @staticmethod
    def love_text(love):
        """
           Return a text describing an AI's love for you.  (Oooh, kinky!!)
          These words should be adjectives which can fit in the sentence
          "The x are y towards us"
          "The Babylonians are respectful towards us"
        """

        love_sizes = [-90, -70, -50, -25, -10, 10, 25, 50, 70, 90]
        love_tags = ["Genocidal", "Belligerent", "Hostile", "Uncooperative",
                     "Uneasy", "Neutral", "Respectful", "Helpful",
                     "Enthusiastic", "Admiring"]
        for lsize, ltag in zip(love_sizes, love_tags):
            if love <= MAX_AI_LOVE* lsize / 100:
                return ltag
        return "Worshipful"
    
    def get_embassy_text(self, player_id):
        if self.clstate.client_is_observer() and not self.clstate.is_playing():
            return "-"

        pplayer = self.players[player_id]

        cur_player = self.clstate.cur_player()
        if player_id == cur_player['playerno']:
            return "-"
        elif cur_player["real_embassy"][player_id]:
            return "We have embassy"
        elif pplayer.real_embassy[cur_player['playerno']]:
            return "They have embassy"
        else:
            return "No embassy"
    
    @staticmethod
    def get_ai_level_text(player):
        ai_level = player['ai_skill_level']
        if 7 >= ai_level >= 0:
            return AI_SKILLS[ai_level]
        else:
            return "Unknown"
