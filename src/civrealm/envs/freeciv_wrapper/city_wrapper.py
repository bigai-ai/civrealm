from .core import Wrapper, wrapper_override


@wrapper_override(["info"])
class PersistentCityProduction(Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.__turn = -1

    def info(self, info, observation):
        for city_id, city in observation.get("city", {}).items():
            if (
                (city["owner"] == self.unwrapped.civ_controller.player_ctrl.my_player_id)
                and (city["prod_process"] != 0)
                and (self.__turn != city["turn_last_built"] + 1)
            ):
                self._mask_out_city_production(
                    info["available_actions"]["city"][city_id]
                )
        self.__turn = info["turn"]
        return info

    def _mask_out_city_production(self, city_info):
        for action in city_info:
            if action.startswith("produce"):
                city_info[action] = False
