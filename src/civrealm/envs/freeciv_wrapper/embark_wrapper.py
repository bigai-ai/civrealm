from .core import Wrapper, wrapper_override


@wrapper_override(["action", "info"])
class EmbarkWrapper(Wrapper):
    """
    Unify embark actions of all units to 'embark_{dir8}' where dir8 in `[0,...7]`
    indicating 8 directions.

    Sometimes a unit can embark multiple carrier on the same direction. In that
    case, the wrapper automatically choose the carrier with the smallest unit id.

    Attributes
    ----------
    embarkable_units : dict
        a dict of embarkable units with key=(embarking_unit_id, dir8) and value=[carrier_ids]
    """

    def __init__(self, env):
        self.embarkable_units = {}
        super().__init__(env)

    def action(self, action):
        """
        Translate `embark_{dir8}` action into embark actions that can be handled by FreecivBaseEnv.
        """
        if action is None:
            return action
        (actor_name, entity_id, action_name) = action
        if actor_name != "unit":
            return action
        if action_name[:6] != "embark":
            return action

        dir8 = int(action_name.split("_")[-1])

        if len(self.embarkable_units.get((entity_id, dir8), [])) > 0:
            assert dir8 <= 8
            target_id = sorted(self.embarkable_units[(entity_id, dir8)])[0]
            action_name = f"embark_{dir8}_{target_id}"

        return (actor_name, entity_id, action_name)

    def info(self, info):
        """
        Complete or modify embark actions in info['availble_actions']['unit']

        If a unit has no `embark_.*` action, then set all `embark_{dir8}` action to False

        If a unit has `embark_{dir}=True`, set all `embark_{other_dirs}` action to False

        If a unit has `embark_{carrier_id}_{dir}=True`, store that carrier_id
        and set its `embark_{dir8}` accordingly.
        """

        self.embarkable_units = {}
        unit_actions = info["available_actions"].get("unit", {})

        if len(unit_actions) == 0:
            return info

        for unit_id, actions in unit_actions.items():
            unavailable_embarks = ["embark_" + f"{i}" for i in range(8)]
            for action in list(actions.keys()):
                if action[:6] != "embark":
                    continue

                args = action.split("_")

                if len(args) == 3:
                    # action ==  embark_dir_id
                    [dir8, target_id] = map(int, args[1::])
                    if (unit_dir := (unit_id, dir8)) not in self.embarkable_units:
                        self.embarkable_units[unit_dir] = [target_id]
                    else:
                        self.embarkable_units[unit_dir].append(target_id)
                    actions.pop(action)
                    embark_action = f"embark_{dir8}"
                else:
                    # action ==  embark_dir
                    assert (
                        len(args) == 2
                    ), f"Expected embark_{{dir}}_{{target_id}},\
                            but got unsupported embark action name {action}"
                    dir8 = int(action.split("_")[-1])
                    embark_action = f"embark_{dir8}"
                actions[f"embark_{dir8}"] = True
                if embark_action in unavailable_embarks:
                    unavailable_embarks.remove(embark_action)

            for embark_action in unavailable_embarks:
                # set unavailable embark actions to False
                actions[embark_action] = False

        info["available_actions"]["unit"] = unit_actions

        return info
