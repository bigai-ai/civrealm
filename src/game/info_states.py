'''
Created on 07.03.2018

@author: christian
'''
from utils.base_state import PlainState

class GameState(PlainState):
    def __init__(self, scenario_info, calendar_info):
        PlainState.__init__(self)
        self.scenario_info = scenario_info
        self.calendar_info = calendar_info

    def _update_state(self, pplayer):
        if pplayer != None:
            return
            #self._state.update(self.calendar_info)
            #self._state.update(self.scenario_info)

class ServerState(PlainState):
    def __init__(self, server_settings):
        PlainState.__init__(self)
        self.server_settings = server_settings

    def _update_state(self, pplayer):
        if pplayer != None:
            return
            #self._state.update(self.server_settings)

class RuleState(PlainState):
    def __init__(self, game_info):
        PlainState.__init__(self)
        self.game_info = game_info

    def _update_state(self, pplayer):
        if pplayer != None:
            return
            #self._state.update(self.game_info)