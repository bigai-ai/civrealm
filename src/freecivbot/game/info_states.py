'''
Created on 07.03.2018

@author: christian
'''
from freecivbot.utils.base_state import PlainState, ListState


class GameState(PlainState):
    def __init__(self, scenario_info, calendar_info):
        PlainState.__init__(self)
        self.scenario_info = scenario_info
        self.calendar_info = calendar_info

    def _update_state(self, pplayer):
        if pplayer != None:
            self._state.update(self.calendar_info)
            del self._state["calendar_fragment_name"]
            self._state.update(self.scenario_info)


class ServerState(ListState):
    def __init__(self, server_settings):
        PlainState.__init__(self)
        self.server_settings = server_settings

    def _update_state(self, pplayer):
        if pplayer != None:
            pass
            # TODO: Treating fields that are lists to be treated later on
            # self._state.update(self.server_settings)


class RuleState(PlainState):
    def __init__(self, game_info):
        PlainState.__init__(self)
        self.game_info = game_info

    def _update_state(self, pplayer):
        if pplayer != None:
            self._state.update(self.game_info)
            # TODO: Treating fields that are lists to be treated later on
            for key in ["global_advances", "granary_food_ini", "great_wonder_owners",
                        "min_city_center_output", "diplchance_initial_odds"]:
                del self._state[key]
