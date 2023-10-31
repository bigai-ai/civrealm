from .core import Wrapper, wrapper_override


@wrapper_override(["observation", "info"])
class DiplomacyLoop(Wrapper):
    def __init__(self, env):
        self.is_negotiating = False
        self.dealing_with_incoming = False
        self.__turn = -1
        super().__init__(CancelReturnedTreaties(env))

    def observation(self, observation, info):
        dipls = observation.get("dipl",{})

        # agent is negotiating if clause map is non-empty
        self.is_negotiating = any(
            len(dipl["diplomacy_clause_map"]) > 0 for dipl in dipls.values()
        )

        if self.__turn != info["turn"] and self.is_negotiating:
            # start dealing with incoming at the start of turn
            self.dealing_with_incoming = True

        # if agent stop negotiating then it must stop dealing with incoming
        self.dealing_with_incoming = self.dealing_with_incoming and self.is_negotiating

        self.__turn = info["turn"]

        return observation

    def info(self, info):
        if self.dealing_with_incoming:
            # deal with incoming with only accepting or cancelling treaty
            return self._accept_or_cancel(info)

        if self.is_negotiating:
            # continue negotiation: mask out all actions abut diplomacy
            return self._mask_all_but_dipl(info)

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

        for player, dipl in observation.get("dipl",{}).items():
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
