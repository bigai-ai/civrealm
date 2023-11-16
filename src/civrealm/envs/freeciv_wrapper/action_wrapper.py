from copy import deepcopy
from typing import Any, Dict, Optional

import numpy as np
from gymnasium import spaces

from civrealm.configs import fc_args
from civrealm.envs.freeciv_wrapper.tensor_base_wrapper import TensorBase
from civrealm.freeciv.utils.fc_types import (ACTIVITY_FORTIFIED,
                                             ACTIVITY_FORTIFYING,
                                             ACTIVITY_IDLE, ACTIVITY_SENTRY)

from .city_wrapper import PersistentCityProduction
from .core import Wrapper
from .dipl_wrapper import DiplomacyLoop, TruncateDiplCity
from .embark_wrapper import EmbarkWrapper
from .tech_wrapper import CombineTechResearchGoal
from .utils import update

tensor_debug = fc_args["debug.tensor_debug"]


class TensorAction(Wrapper):
    """
    A wrapper that defines tensor action spaces,  transforms tensor actions into
    actions that could be handeled by FreecivBaseEnv instance, and adds masks to
    observations.

    TensorAction wrapper is composed of five wrappers, including `TruncateDiplCity`,
    `DiplomacyLoop`, `CombineTechResearchGoal`, `PersistentCityProduction`, and `EmbarkWrapper`.



    Parameters
    ----------
    env: TensorBase
        A FreecivBaseEnv instance that has been wrapped by TensorBase.

    Attributes
    ----------
    aciton_config: dict
        a dict that configs that specify sizes of mutable entities and action layout.
    mask: dict
        a dict of masks of type numpy ndarray indicating available actions and entities. 0-> unavilalbe, 1->availble.
    available_actions: dict
        cached info['available_actions'], a dict that indicates available actions.
    action_space: gymnasium.spaces.Dict
        a gymnasium.spaces.Dict with keys `['actor_type','city_id','unit_id',
        'dipl_id','city_action_type','unit_action_type','dipl_action_type',
        'gov_action_type','tech_action_type']`
    """

    def __init__(self, env: TensorBase):
        self.action_config = env.get_wrapper_attr("config")
        self.action_config["resize"]["dipl"] = self.action_config["resize"][
            "others_player"
        ]
        self.actor_type_list = self.action_config["actor_type_list"]
        self.available_actions = {}
        self.mask = {}
        self.__turn = -1
        self.__dealing_with_incoming = False

        super().__init__(
            TruncateDiplCity(
                DiplomacyLoop(
                    CombineTechResearchGoal(
                        PersistentCityProduction(EmbarkWrapper(env))
                    )
                )
            )
        )

        self.action_space = spaces.Dict(
            {
                "actor_type": spaces.Discrete(len(self.actor_type_list)),
                "city_id": spaces.Discrete(self.action_config["resize"]["city"]),
                "city_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["city"].values())
                ),
                "unit_id": spaces.Discrete(self.action_config["resize"]["unit"]),
                "unit_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["unit"].values())
                ),
                "dipl_id": spaces.Discrete(self.action_config["resize"]["dipl"]),
                "dipl_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["dipl"].values())
                ),
                "gov_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["gov"].values())
                ),
                "tech_action_type": spaces.Discrete(
                    sum(self.action_config["action_layout"]["tech"].values())
                ),
            }
        )

    def step(self, action):
        # Get {k:value.item()} if value is array
        action = {
            k: (v.item() if isinstance(v, np.ndarray) else v) for k, v in action.items()
        }

        base_action = self.action(action)
        if tensor_debug:
            print(base_action)
        obs, reward, terminated, truncated, info = self.env.step(base_action)
        if tensor_debug:
            print(f"reward:{reward},done:{terminated or truncated}")

        obs = self.update_obs_with_mask(obs, info, action)
        return obs, reward, terminated, truncated, info

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        obs, info = self.env.reset(seed=seed, options=options, **kwargs)
        obs = self.update_obs_with_mask(obs, info)
        return obs, info

    def action(self, action):
        """
        Translate tensor action, a dict of keys `['actor_type','city_id','unit_id',
        'dipl_id','city_action_type','unit_action_type','dipl_action_type',
        'gov_action_type','tech_action_type']` to `FreecivBaseEnv` action,
        a tuple `(actor_type, entity_id, action_name)`.

        """
        if tensor_debug:
            self._check_action_layout()

        actor_type = action["actor_type"]
        actor_name = self.actor_type_list[actor_type]

        if actor_name == "turn done":
            return None
        if actor_name in ["gov", "tech"]:
            entity_pos = None
            entity_id = self.get_wrapper_attr("my_player_id")
            action_index = action[actor_name + "_action_type"]
        else:
            entity_pos, action_index = (
                action[actor_name + "_id"],
                action[actor_name + "_action_type"],
            )
            entity_id = self.get_wrapper_attr(actor_name + "_ids")[
                action[actor_name + "_id"]
            ]

        if tensor_debug:
            assert (
                self.mask[actor_name + "_action_type_mask"][entity_pos, action_index]
                == 1
            ), f"{actor_name} action of id pos {entity_pos}, \
                    action type index {action_index} is masked"

        action_name = sorted(
            list(self.available_actions[actor_name][entity_id].keys())
        )[action_index]

        return (actor_name, entity_id, action_name)

    def update_obs_with_mask(self, observation, info, action=None):
        """
        Update self.mask using observation, info and action from the unwrapped env,
        and add self.mask to the observation of the wrapped env.
        """
        if info[
            "turn"
        ] != self.__turn or self.__dealing_with_incoming != self.get_wrapper_attr(
            "dealing_with_incoming"
        ):
            self.reset_mask()
        self.available_actions = deepcopy(info["available_actions"])
        self.__turn = info["turn"]
        self.__dealing_with_incoming = self.get_wrapper_attr("dealing_with_incoming")
        self._update_mask(observation, info, action)

        return update(observation, deepcopy(self.mask))

    def reset_mask(self):
        """
        Reset self.mask

        This is usually called at the start of a new turn to reset masks.
        """
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

        # Dipl id mask
        self.mask["dipl_id_mask"] = np.ones(sizes["dipl"], dtype=np.int32)[
            ..., np.newaxis
        ]

        # Action type mask
        for field in ["city", "unit", "dipl"]:
            self.mask[field + "_action_type_mask"] = np.ones(
                (
                    sizes[field],
                    sum(self.action_config["action_layout"][field].values()),
                ),
                dtype=np.int32,
            )
        for field in ["gov", "tech"]:
            self.mask[field + "_action_type_mask"] = np.ones(
                (sum(self.action_config["action_layout"][field].values()),),
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
            # self.mask["unit_action_type_mask"][
            #     action["unit_id"], action["unit_action_type"]
            # ] = 0
            pass
        elif actor_name == "city":
            # self.mask["city_action_type_mask"][action["city_id"], :] = 0
            pass
        elif actor_name == "gov":
            self.mask["gov_action_type_mask"][:] &= 0
        elif actor_name == "tech":
            self.mask["tech_action_type_mask"][:] &= 0

    def _mask_from_obs(self, observation):
        # Mask mutable entities using observation

        # Mask out trailing spaces for unit and city
        self.mask["unit_id_mask"][len(self.get_wrapper_attr("unit_ids")) : :, :] = 0
        self.mask["city_id_mask"][len(self.get_wrapper_attr("city_ids")) : :, :] = 0
        self.mask["dipl_id_mask"][len(self.get_wrapper_attr("dipl_ids")) : :, :] = 0
        self.mask["unit_mask"] = self.mask["unit_id_mask"].copy()
        self.mask["city_mask"] = self.mask["city_id_mask"].copy()

        self.mask["unit_action_type_mask"][
            len(self.get_wrapper_attr("unit_ids")) : :, :
        ] = 0
        self.mask["city_action_type_mask"][
            len(self.get_wrapper_attr("city_ids")) : :, :
        ] = 0

        # Mask Unit
        for pos, unit_id in enumerate(
            self.get_wrapper_attr("unit_ids")[: self.action_config["resize"]["unit"]]
        ):
            unit = observation["unit"][unit_id]
            if unit["moves_left"] == 0 or self.unwrapped.civ_controller.unit_ctrl.units[
                unit_id
            ]["activity"] not in [
                ACTIVITY_IDLE,
                ACTIVITY_FORTIFIED,
                ACTIVITY_SENTRY,
                ACTIVITY_FORTIFYING,
            ]:  # agent busy or fortified
                self.mask["unit_id_mask"][pos] &= 0
                self.mask["unit_action_type_mask"][pos, :] &= 0

        self.mask["others_unit_mask"][
            len(self.get_wrapper_attr("others_unit_ids")) : :, :
        ] &= 0
        self.mask["others_city_mask"][
            len(self.get_wrapper_attr("others_city_ids")) : :, :
        ] &= 0

        if self.get_wrapper_attr("researching"):
            self.mask["tech_action_type_mask"][:] &= 0
        if not self.get_wrapper_attr("researching") and tensor_debug:
            print(f"techs_researched: {self.get_wrapper_attr('techs_researched')}")

    def _mask_from_info(self, info):
        others_player_num = len(info["available_actions"].get("player", {}).keys())
        self.mask["others_player_mask"][others_player_num::, :] &= 0

        # Mask City and Unit
        for mutable in ["city", "unit", "dipl"]:
            entities = info["available_actions"].get(mutable, {})
            if len(entities) == 0:
                self.mask[mutable + "_action_type_mask"][:, :] &= 0
                self.mask[mutable + "_id_mask"][:] &= 0
                continue
            for i, entity_id in enumerate(
                self.env.get_wrapper_attr(mutable + "_ids")[
                    : self.action_config["resize"][mutable]
                ]
            ):
                actions = entities.get(entity_id, {})
                if len(actions) == 0:
                    self.mask[mutable + "_action_type_mask"][i, :] &= 0
                    self.mask[mutable + "_id_mask"][i] &= 0
                    continue
                for action_id, act_name in enumerate(sorted(list(actions.keys()))):
                    self.mask[mutable + "_action_type_mask"][i, action_id] &= int(
                        actions[act_name]
                    )
                self.mask[mutable + "_id_mask"][i] &= int(
                    any(self.mask[mutable + "_action_type_mask"][i])
                )
        for mutable in ["city", "unit", "dipl"]:
            actor_type_index = self.actor_type_list.index(mutable)
            self.mask["actor_type_mask"][actor_type_index] &= int(
                any(self.mask[mutable + "_id_mask"])
            )

        # Mask Gov and Tech
        for immutable in ["gov", "tech"]:
            options = info["available_actions"].get(immutable, {})
            if len(options) == 0:
                self.mask[immutable + "_action_type_mask"][:] &= 0
                continue
            my_player_id = self.get_wrapper_attr("my_player_id")
            for action_id, act_name in enumerate(
                sorted(list(options[my_player_id].keys()))
            ):
                self.mask[immutable + "_action_type_mask"][action_id] &= int(
                    options[my_player_id][act_name]
                )
        for immutable in ["gov", "tech"]:
            actor_type_index = self.actor_type_list.index(immutable)
            self.mask["actor_type_mask"][actor_type_index] &= int(
                any(self.mask[immutable + "_action_type_mask"])
            )

    def _check_action_layout(self):
        action_layout = self.action_config["action_layout"]
        for field in ["city", "unit"]:
            for id, entity in self.available_actions.get(field, {}).items():
                assert len(entity) == sum(action_layout[field].values())
        assert len(
            self.available_actions["gov"][self.get_wrapper_attr("my_player_id")]
        ) == sum(action_layout["gov"].values())
