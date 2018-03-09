'''
Created on 08.03.2018

@author: christian
'''
from utils.base_state import PlainState
from utils.fc_types import RPT_CERTAIN
from research.reqtree import reqtree, reqtree_multiplayer, reqtree_civ2civ3
from research.req_info import ReqCtrl

class TechState(PlainState):
    def __init__(self, rule_ctrl, tech_ctrl):
        PlainState.__init__(self)
        self.rule_ctrl = rule_ctrl
        self.tech_ctrl = tech_ctrl
        
    def _update_state(self, pplayer):
        if self._state == {}:
            self.init_tech_state()

        for tech_id in self._state.keys():
            ptech = self.rule_ctrl.techs[tech_id]
            cur_tech = self._state[tech_id]
            cur_tech['is_researching'] =  pplayer['researching'] == ptech['id']
            cur_tech['is_tech_goal'] = pplayer['tech_goal'] == ptech['id']
            cur_tech['inv_state'] = self.tech_ctrl.player_invention_state(pplayer, ptech['id'])
            cur_tech['is_req_for_goal'] = self.rule_ctrl.is_tech_req_for_goal(ptech['id'],
                                                                    pplayer['tech_goal'])

            cur_tech['reqs'] = {}
            for req in ptech['research_reqs']:
                req_active = ReqCtrl.is_req_active(pplayer, req, RPT_CERTAIN)
                self.tech_state[tech_id]['reqs'][req['value']] = req_active
    
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