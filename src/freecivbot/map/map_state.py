'''
Created on 07.03.2018

@author: christian
'''
from freecivbot.utils.base_state import PlainState
import json

class MapState(PlainState):
    def __init__(self, player_map):
        PlainState.__init__(self)
        self._state = player_map

    def json_struct(self):
        return dict([(key, self._state[key].to_list()) for key in self._state.keys()])

    def _update_state(self, pplayer):
        return self._state