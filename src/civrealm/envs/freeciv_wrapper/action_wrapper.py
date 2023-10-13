from typing import Any, Optional

import numpy as np
from gymnasium import spaces

from civrealm.configs import fc_args
from civrealm.freeciv.utils.fc_types import (ACTIVITY_FORTIFIED,
                                             ACTIVITY_FORTIFYING,
                                             ACTIVITY_IDLE, ACTIVITY_SENTRY)

from .core import Wrapper
from .utils import update

debug_print = fc_args["debug.tensor_debug"]


class TensorAction(Wrapper):
    def __init__(self, env, config):
        self.action_config = config
        self.actor_type_list = self.action_config["actor_type_list"]
        self.action_list = []
        self.mask = {}
        self.turn = -1
        self.embarkable_units = {}
        super().__init__(env)
        self.action_space = spaces.Dict(
            {
                # actor_type_dim = 4; 0 for city, 1 for unit, 2 for gov, 3 for turn done
                "actor_type": spaces.Discrete(len(self.actor_type_list)),
                "city_id": spaces.Discrete(self.action_config["resize"]["city"]),
                "city_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["city"].values())
                ),
                "unit_id": spaces.Discrete(self.action_config["resize"]["unit"]),
                "unit_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["unit"].values())
                ),
                "gov_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["gov"].values())
                ),
            }
        )

    def step(self, action):
        # Get {k:value.item()} if value is array
        action = {
            k: (v.item() if isinstance(v, np.ndarray) else v) for k, v in action.items()
        }

        tensor_action = self.action(action)
        if debug_print:
            print(tensor_action)
        obs, reward, terminated, truncated, info = self.env.step(tensor_action)
        if debug_print:
            print(f"reward:{reward},done:{terminated or truncated}")

        obs = self.update_obs_with_mask(obs, info, action)
        return obs, reward, terminated, truncated, info

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        obs, info = self.env.reset(seed=seed, options=options, **kwargs)
        obs = self.update_obs_with_mask(obs, info)
        return obs, info

    def action(self, action):
        actor_type = action["actor_type"]
        actor_name = self.actor_type_list[actor_type]

        if actor_name == "turn done":
            return None
        if actor_name == "gov":
            entity_pos = None
            entity_id = self.get_wrapper_attr("my_player_id")
            action_index = action["gov_action_type"]
        else:
            entity_pos, action_index = (
                action[actor_name + "_id"],
                action[actor_name + "_action_type"],
            )
            entity_id = self.get_wrapper_attr(actor_name + "_ids")[
                action[actor_name + "_id"]
            ]

        assert (
            self.mask[actor_name + "_action_type_mask"][entity_pos, action_index] == 1
        ), f"{actor_name} action of id pos {entity_pos}, action type index {action_index} is masked"

        action_name = sorted(list(self.action_list[actor_name][entity_id].keys()))[
            action_index
        ]

        if actor_name == "unit":
            action_name = self._handle_embark_action_name(entity_id, action_name)

        return (actor_name, entity_id, action_name)

    def update_obs_with_mask(self, observation, info, action=None):
        # Update mask and update obs with mask dict
        info = self._handle_embark_info(info)
        if info["turn"] != self.turn:
            self.reset_mask()
        self.action_list = info["available_actions"]
        self.turn = info["turn"]
        self._update_mask(observation, info, action)
        return update(observation, self.mask)

    def reset_mask(self):
        # Reset mask
        sizes = self.action_config["resize"]
        self.mask["actor_type_mask"] = np.ones(
            len(self.actor_type_list), dtype=np.int32
        )

        # Units/Cities/Players and others Masks
        for field in ["unit", "city", "others_unit", "others_city", "others_player"]:
            self.mask[field + "_mask"] = np.ones(sizes[field], dtype=np.int32)[
                ..., np.newaxis
            ]

        # Units/Cities Id Masks same as their Masks
        self.mask["unit_id_mask"] = self.mask["unit_mask"]
        self.mask["city_id_mask"] = self.mask["city_mask"]

        # Action type mask
        for field in ["city", "unit"]:
            self.mask[field + "_action_type_mask"] = np.ones(
                (
                    sizes[field],
                    sum(self.action_config["action_layout"][field].values()),
                ),
                dtype=np.int32,
            )
        self.mask["gov_action_type_mask"] = np.ones(
            (sum(self.action_config["action_layout"]["gov"].values()),),
            dtype=np.int32,
        )

    def _update_mask(self, observation, info, action):
        # update self.mask using action, observation and info
        if action:
            self._mask_from_action(action)
        self._mask_from_obs(observation)
        self._mask_from_info(info)

    def _mask_from_action(self, action):
        # Mask out actions that have been performed in this turn.
        actor_type = action["actor_type"]
        actor_name = self.actor_type_list[actor_type]
        if actor_name == "unit":
            self.mask["unit_action_type_mask"][
                action["unit_id"], action["unit_action_type"]
            ] *= 0
        elif actor_name == "city":
            self.mask["city_action_type_mask"][action["city_id"]] *= 0
        elif actor_name == "gov":
            self.mask["gov_action_type_mask"] *= 0

    def _mask_from_obs(self, observation):
        # Mask mutable entities using observation

        # Mask out trailing spaces for unit and city
        self.mask["unit_mask"][len(self.get_wrapper_attr("unit_ids")) : :, :] *= 0
        self.mask["city_mask"][len(self.get_wrapper_attr("city_ids")) : :, :] *= 0
        self.mask["unit_action_type_mask"][
            len(self.get_wrapper_attr("unit_ids")) : :, :
        ] *= 0
        self.mask["city_action_type_mask"][
            len(self.get_wrapper_attr("city_ids")) : :, :
        ] *= 0

        # Mask city
        for pos, unit_id in enumerate(
            self.get_wrapper_attr("city_ids")[: self.action_config["resize"]["city"]]
        ):
            city = observation["city"][unit_id]
            # The following two conditions are used to check if
            # 1.  the city is just built or is building coinage, and
            # 2. the city has just built a unit or an improvement last turn and
            #    there are some production points left in stock.
            if (city["prod_process"] != 0) and (
                self.turn != city["turn_last_built"] + 1
            ):
                self.mask["city_mask"][pos] *= 0
                self.mask["city_action_type_mask"][pos] *= 0

        # Mask Unit
        for pos, unit_id in enumerate(
            self.get_wrapper_attr("unit_ids")[: self.action_config["resize"]["unit"]]
        ):
            unit = observation["unit"][unit_id]
            if unit["moves_left"] == 0 or self.civ_controller.unit_ctrl.units[unit_id][
                "activity"
            ] not in [
                ACTIVITY_IDLE,
                ACTIVITY_FORTIFIED,
                ACTIVITY_SENTRY,
                ACTIVITY_FORTIFYING,
            ]:  # agent busy or fortified
                self.mask["unit_mask"][pos] *= 0
                self.mask["unit_action_type_mask"][pos] *= 0

        self.mask["unit_id_mask"] = self.mask["unit_mask"]
        self.mask["city_id_mask"] = self.mask["city_mask"]
        self.mask["others_unit_mask"][
            len(self.get_wrapper_attr("others_unit_ids")) : :, :
        ] *= 0
        self.mask["others_city_mask"][
            len(self.get_wrapper_attr("others_city_ids")) : :, :
        ] *= 0

    def _mask_from_info(self, info):
        others_player_num = len(info["available_actions"].get("player", {}).keys())
        self.mask["others_player_mask"][others_player_num::, :] = 0

        # Mask City and Unit
        for mutable in ["city", "unit"]:
            entities = info["available_actions"].get(mutable, {})
            if len(entities) == 0:
                self.mask[mutable + "_action_type_mask"] *= 0
                self.mask[mutable + "_id_mask"] *= 0
                continue
            for i, entity_id in enumerate(
                self.env.get_wrapper_attr(mutable + "_ids")[
                    : self.action_config["resize"][mutable]
                ]
            ):
                actions = entities.get(entity_id, {})
                if len(actions) == 0:
                    self.mask[mutable + "_action_type_mask"][i] *= 0
                    continue
                for action_id, act_name in enumerate(sorted(list(actions.keys()))):
                    self.mask[mutable + "_action_type_mask"][i, action_id] *= int(
                        actions[act_name]
                    )
                self.mask[mutable + "_id_mask"][i] = int(
                    any(self.mask[mutable + "_action_type_mask"][i])
                )
        for mutable in ["city", "unit"]:
            actor_type_index = self.actor_type_list.index(mutable)
            self.mask["actor_type_mask"][actor_type_index] = int(
                any(self.mask[mutable + "_id_mask"])
            )

        # Mask Gov
        gov = info["available_actions"].get("gov", {})
        if len(gov) > 0:
            my_player_id = self.get_wrapper_attr("my_player_id")
            for action_id, act_name in enumerate(
                sorted(list(gov[my_player_id].keys()))
            ):
                self.mask["gov_action_type_mask"][action_id] *= int(
                    gov[my_player_id][act_name]
                )
        else:
            self.mask["gov_action_type_mask"] *= 0
        actor_type_index = self.actor_type_list.index("gov")
        self.mask["actor_type_mask"][actor_type_index] = int(
            any(self.mask["gov_action_type_mask"])
        )

    def _handle_embark_info(self, info):
        # Merge two possible embark actions:
        # embark_dir8 and embark_dir8_target into a single embark_dir8 representation

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

    def _handle_embark_action_name(self, unit_id, action_name):
        # Transform embark_dir8 back to its original representation of two possibilities:
        # embark_dir8 and embark_dir8_target

        if action_name[:6] != "embark":
            return action_name
        dir8 = int(action_name.split("_")[-1])

        if len(self._embarkable_units.get((unit_id, dir8), [])) == 0:
            # the original representation is already embark_dir8
            return action_name

        assert dir8 <= 8
        target_id = sorted(self._embarkable_units[(unit_id, dir8)])[0]
        embark_action_name = f"embark_{dir8}_{target_id}"
        return embark_action_name
