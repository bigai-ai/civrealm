'''
Created on 07.03.2018

@author: christian
'''
from freecivbot.utils.base_state import PlainState

class MapState(PlainState):
    def __init__(self, player_map):
        PlainState.__init__(self)
        self.player_map = player_map

    def _update_state(self, pplayer):
        return self.player_map