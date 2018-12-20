'''
Created on 08.03.2018

@author: christian
'''
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
            self.add_action(actor_id, ActChooseResearchTech(pplayer, tech_id))
            self.add_action(actor_id, ActChooseResearchGoal(pplayer, tech_id))

class ActChooseResearchTech(Action):
    action_key = "research_tech"
    def __init__(self, pplayer, new_tech_id):
        Action.__init__(self)
        self.pplayer = pplayer
        self.new_tech_id = new_tech_id
        self.action_key += "_%i" % new_tech_id

    def is_action_valid(self):
        return is_tech_prereq_known(self.pplayer, self.new_tech_id)

    def _action_packet(self):
        packet = {"pid" : packet_player_research, "tech" : self.new_tech_id}
        return packet

class ActChooseResearchGoal(ActChooseResearchTech):
    action_key = "set_tech_goal"
    def is_action_valid(self):
        return is_tech_unknown(self.pplayer, self.new_tech_id)

    def _action_packet(self):
        packet = {"pid" : packet_player_tech_goal, "tech" : self.new_tech_id}
        return packet