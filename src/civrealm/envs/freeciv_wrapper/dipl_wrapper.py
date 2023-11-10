from .core import Wrapper, wrapper_override


@wrapper_override(["observation", "info", "action"])
class DiplomacyLoop(Wrapper):
    def __init__(self, env):
        self.is_negotiating = False
        self.dealing_with_incoming = False
        self.max_dipl_actions = 10
        self.dipl_action_left = 10
        self.__turn = -1
        super().__init__(CancelReturnedTreaties(env))

    def observation(self, observation, info):
        dipls = observation.get("dipl", {})

        # agent is negotiating if clause map is non-empty
        self.is_negotiating = any(
            len(dipl["diplomacy_clause_map"]) > 0 for dipl in dipls.values()
        )

        if self.__turn != info["turn"] and self.is_negotiating:
            # start dealing with incoming at the start of turn
            self.dealing_with_incoming = True
            self.dipl_action_left = self.max_dipl_actions

        # if agent stop negotiating then it must stop dealing with incoming
        self.dealing_with_incoming = self.dealing_with_incoming and self.is_negotiating

        self.__turn = info["turn"]

        return observation

    def action(self, action):
        if action is None:
            return None
        if action[0] == "dipl":
            self.dipl_action_left -= 1
        return action

    def info(self, info):
        if self.dealing_with_incoming:
            # deal with incoming with only accepting or cancelling treaty
            return self._accept_or_cancel(info)

        if self.is_negotiating and self.dipl_action_left <= 0:
            return self._mask_dipl(info)

        return info

    def _accept_or_cancel(self, info):
        info = self._mask_all_but_dipl(info)

        for player, dipl_actions in info["available_actions"]["dipl"].items():
            accept_treaty = dipl_actions[f"accept_treaty_{player}"]
            stop_negotiation = dipl_actions[f"stop_negotiation_{player}"]

            for action in dipl_actions:
                # mask out all dipl actions
                dipl_actions[action] = False

            # restore accept_treaty and stop negotiation actions
            dipl_actions[f"accept_treaty_{player}"] = accept_treaty
            dipl_actions[f"stop_negotiation_{player}"] = stop_negotiation

        return info

    def _mask_dipl(self, info):
        actions = info["available_actions"]

        def recursive_mask(actions):
            for name, action in actions.items():
                if isinstance(action, dict):
                    actions[name] = recursive_mask(action)
                else:
                    assert action in [True, False]
                    actions[name] = False
            return actions

        actions["dipl"] = recursive_mask(actions["dipl"])

        info["available_actions"] = actions
        return info

    def _mask_all_but_dipl(self, info):
        actions = info["available_actions"]

        def recursive_mask(actions):
            for name, action in actions.items():
                if isinstance(action, dict):
                    actions[name] = recursive_mask(action)
                else:
                    assert action in [True, False]
                    actions[name] = False
            return actions

        for name in list(actions.keys()):
            if name != "dipl":
                actions[name] = recursive_mask(actions[name])

        info["available_actions"] = actions
        return info


@wrapper_override(["info", "action"])
class TruncateDiplCity(Wrapper):
    def __init__(self, env):
        config = env.get_wrapper_attr("config")
        self.city_size = config["resize"]["city"]
        self.others_city_size = config["resize"]["others_city"]
        super().__init__(env)

    def info(self, info, observation):
        my_player_id = self.get_wrapper_attr("my_player_id")
        city_ids = self.get_wrapper_attr("city_ids")[: self.city_size]
        others_city_ids = self.get_wrapper_attr("others_city_ids")[
            : self.others_city_size
        ]

        for player, actions in info["available_actions"].get("dipl", {}).items():
            for act_name in list(actions.keys()):
                args = act_name.split("TradeCity")
                if len(args) > 1:
                    post_args = args[1].split("_")
                    city = int(post_args[-3])
                    if int(post_args[-2]) == player and city in others_city_ids:
                        city_index = others_city_ids.index(city)
                    elif city in city_ids:
                        city_index = city_ids.index(city)
                    else:
                        del actions[act_name]
                        continue
                    trunc_name = f"trunc_{args[0]}TradeCity_{city_index}_{post_args[-2]}_{post_args[-1]}"
                    actions[trunc_name] = (
                        actions[act_name]
                        if not self.unwrapped.civ_controller.city_ctrl.cities[city][
                            "capital"
                        ]
                        else False
                    )
                    del actions[act_name]
            for no_city_index in range(len(city_ids), self.city_size):
                actions[
                    f"trunc_trade_city_clause_TradeCity_{no_city_index}_{my_player_id}_{player}"
                ] = False
                actions[
                    f"trunc_remove_clause_TradeCity_{no_city_index}_{my_player_id}_{player}"
                ] = False
            for no_city_index in range(len(others_city_ids), self.others_city_size):
                actions[
                    f"trunc_trade_city_clause_TradeCity_{no_city_index}_{player}_{my_player_id}"
                ] = False
                actions[
                    f"trunc_remove_clause_TradeCity_{no_city_index}_{player}_{my_player_id}"
                ] = False
            info[player] = actions
        return info

    def action(self, action):
        if action is None:
            return action
        if action[-1].startswith("trunc"):
            args = action[-1].split("TradeCity")
            post_args = args[1].split("_")
            if int(post_args[-1]) == self.get_wrapper_attr("my_player_id"):
                city_index = self.get_wrapper_attr("others_city_ids")[
                    int(post_args[-3])
                ]
            else:
                city_index = self.get_wrapper_attr("city_ids")[int(post_args[-3])]
            action_name = (
                f"{args[0][6:]}TradeCity_{city_index}_{post_args[-2]}_{post_args[-1]}"
            )
            return action[0], action[1], action_name
        return action


@wrapper_override(["observation", "info"])
class CancelReturnedTreaties(Wrapper):
    def __init__(self, env):
        self.__turn = -1
        self.new_info = None
        super().__init__(env)

    def observation(self, observation, info):
        my_player_id = self.unwrapped.civ_controller.player_ctrl.my_player_id
        self.new_info = None

        if self.__turn == info["turn"]:
            # only cancel returned treaties at the start of a new turn
            return observation
        self.__turn = info["turn"]

        for player, dipl in observation.get("dipl", {}).items():
            if dipl.get("meeting_initializer", -1) == my_player_id:
                observation, _, _, _, info = self.unwrapped.step(
                    ("dipl", player, f"stop_negotiation_{player}")
                )
                self.new_info = info
        return observation

    def info(self, info):
        if self.new_info is None:
            return info
        return self.new_info
