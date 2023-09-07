from typing import (
    Union,
    Mapping,
    MutableMapping,
    Sequence,
    Callable,
    Hashable,
    Any,
    Dict,
)
from collections.abc import Mapping, Sequence
from copy import deepcopy

from gymnasium.core import spaces

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")


def get_space_keys(space: spaces.Dict) -> dict:
    # Obtain nested space keys only
    result = {}

    for key, val in space.spaces.items():
        if isinstance(val, spaces.Dict):
            # if subspace is Dict-like, get keys recursively
            subresult = get_space_keys(val)
            result[key] = subresult

        else:
            # if subspace is not Dict-like, get its key and continue
            result[key] = {}
    return result


def get_keys(data: Mapping) -> dict:
    # Obtain nested dict-like data keys only
    result = {}

    for key, val in data.items():
        if isinstance(val, Mapping):
            # if subspace is Dict-like, get keys recursively
            subresult = get_keys(val)
            result[key] = subresult

        else:
            # if subspace is not Dict-like, get its key and continue
            result[key] = {}
    return result


def get_missing_keys(space_keys: dict, filter_keys: Union[Mapping, Sequence]) -> dict:
    # Get nested keys in filter_keys missing from space_keys
    missing = {}
    if isinstance(filter_keys, Sequence):
        # if filter_keys is list or tuple-like, return missing keys directly
        missing = {key: {} for key in filter_keys if key not in space_keys}

    elif isinstance(filter_keys, Mapping):
        # if filter_keys is dict-like, return missing keys recursively
        for key, val in filter_keys.items():
            if key not in space_keys:
                # if current key is missing from the current level of space-keys
                missing[key] = val

            elif not (submissing := get_missing_keys(space_keys[key], val)):
                # if some key is missing from sub-space keys
                missing[key] = submissing
    return missing


def complete_filter_keys(
    # generate the full set of nested keys filtered by filter_keys
    space_keys: dict,
    filter_keys: Union[Mapping, Sequence],
    filter_out: bool = False,
) -> dict:
    result = {}
    if isinstance(filter_keys, Sequence):
        result = {
            key: val
            for key, val in space_keys.items()
            if bool(key in filter_keys) ^ filter_out
        }

    elif isinstance(filter_keys, Mapping):
        for key, val in space_keys.items():
            if filter_out and not key in filter_keys:
                result[key] = val
            elif filter_out and key in filter_keys and filter_keys[key]:
                if subresult := complete_filter_keys(val, filter_keys[key], filter_out):
                    result[key] = subresult
            elif not filter_out and key in filter_keys:
                result[key] = (
                    complete_filter_keys(val, filter_keys[key], filter_out)
                    if filter_keys[key]
                    else val
                )
    return result


def filter_space(space: spaces.Space, filter_keys: dict) -> spaces.Space:
    # filter a space by a complete filter key
    if isinstance(space, spaces.Dict):
        return type(space)(
            [
                (key, filter_space(space.spaces[key], filter_keys[key]))
                for key in filter_keys
            ]
        )
    else:
        return deepcopy(space)


def filter_apply_space_with_args(
    # apply func to a nested space recursively using arguments contained by a nested dict
    space: spaces.Space,
    func: Callable,
    args_dict: Union[dict, Any],
) -> spaces.Space:
    if isinstance(space, spaces.Dict) and isinstance(args_dict, dict):
        return type(space)(
            [
                (
                    key,
                    filter_apply_space_with_args(
                        space.spaces[key], func, args_dict[key]
                    ),
                )
                if key in args_dict
                else (key, val)
                for key, val in space.items()
            ]
        )
    else:
        return func(space, args_dict)


def filter_apply(
    # apply dict-like funcs to a nested dict-like data recursively using node values as arguments
    data: Mapping,
    func: Mapping[Hashable, Union[Mapping, Callable]],
):
    result = {}
    for key, val in data.items():
        if key in func:
            result[key] = (
                filter_apply(val, func[key])
                if isinstance(func[key], Mapping)
                else func[key](val)
            )
        else:
            result[key] = val
    return result


def filter_data(data: dict, filter_keys: dict) -> Mapping:
    # filter a nested dict-like data by a complete filter key
    if isinstance(data, dict):
        return type(data)(
            [(key, filter_data(data[key], filter_keys[key])) for key in filter_keys]
        )
    else:
        return data


def nested_apply(data: MutableMapping, func: Callable, copy=False) -> MutableMapping:
    # apply func to a nested dict-like data using node values as arguments
    if copy:
        data = deepcopy(data)
    for key, val in data.items():
        if isinstance(val, Mapping):
            nested_apply(val[key], func)
        else:
            data[key] = func(val)
    return data


from freeciv_gym.freeciv.utils.unit_improvement_const import (
    UNIT_TYPES,
    UNIT_COSTS,
    IMPR_COSTS,
)
import numpy as np
from BitVector import BitVector


default_config = {
    "filter_observation": [
        "map",
        "unit",
        "player",
        "rules",
        "city",
    ],
    "resize": {
        "unit": 128,
        "city": 32,
        "others_unit": 128,
        "others_city": 64,
        "others_player": 10,
    },
}

obs_possible_size = {
    "rules": 120,
    "player": 26,
    "city": 227,
    "unit":  125,
    "others_player":  22,
    "others_unit":  64,
    "others_city":  86,
        }

noop = (
    lambda x: (np.array(x) * np.array([1])).astype(np.int32)
    if isinstance(x, list)
    else (x * np.array([1])).astype(np.int32)
)


def expand_dim(dim):
    def expand_at(obs):
        return (np.expand_dims(obs, axis=dim)).astype(np.int32)

    return expand_at


def update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def bitvector_to_onehot(bitvec: BitVector):
    onehot = np.zeros(len(str(bitvec)), dtype=np.int32)
    for i, char in enumerate(str(bitvec)):
        if char == "1":
            onehot[i] += 1
    return onehot


def onehotifier_maker(category):
    if isinstance(category, int):

        def onehot(obs):
            if isinstance(obs, np.ndarray):
                shape = obs.shape
            else:
                shape = (1,)
                obs = int(obs)
            result = (
                np.zeros([*shape, category], dtype=np.int32)
                if shape != (1,)
                else np.zeros([category], dtype=np.int32)
            )
            with np.nditer(obs, op_flags=["readonly"], flags=["multi_index"]) as it:
                for x in it:
                    index = (
                        (
                            *(it.multi_index),
                            x,
                        )
                        if shape != (1,)
                        else (x,)
                    )
                    result[index] = 1
            return result

    elif isinstance(category, list):

        def onehot(obs):
            if isinstance(obs, np.ndarray):
                shape = obs.shape
            else:
                shape = (1,)
            result = (
                np.zeros([*shape, len(category)], dtype=np.int32)
                if shape != (1,)
                else np.zeros([len(category)], dtype=np.int32)
            )
            with np.nditer(obs, op_flags=["readonly"], flags=["multi_index"]) as it:
                for x in it:
                    index = (
                        (
                            *(it.multi_index),
                            category.index(x),
                        )
                        if shape != (1,)
                        else (category.index(x),)
                    )
                    result[index] = 1
            return result

    else:
        raise NotImplemented(f"Not implemented yet for type {type(category)}")
    return onehot


def rprint(dict, prefix_space=""):
    for key, val in dict.items():
        if isinstance(val, Dict):
            print(prefix_space + f"{key}:")
            rprint(dict[key], prefix_space + "  ")
        else:
            print(
                f"{prefix_space}{key}: {val.shape if isinstance(val,np.ndarray) else 'b' if isinstance(val, bool) else 'i' if isinstance(val, int) else {type(val)}}"
            )


map_ops = {
    "status": onehotifier_maker(3),
    "terrain": onehotifier_maker(14),
    "extras": noop,
    "output": noop,
    "tile_owner": expand_dim(-1),
    "city_owner": expand_dim(-1),
    "unit": noop,
    "unit_owner": expand_dim(-1),
}

unit_ops = {
    "type_rule_name": onehotifier_maker(UNIT_TYPES),
    "x": noop,
    "y": noop,
    "owner": noop,
    "type_attack_strength": noop,
    "type_defense_strength": noop,
    "type_firepower": noop,
    "type_build_cost": noop,
    "type_convert_time": noop,
    "type_obsoleted_by": onehotifier_maker(53),
    "type_hp": noop,
    "type_move_rate": noop,
    "type_vision_radius_sq": noop,
    "type_worker": noop,
    "type_can_transport": noop,
    "home_city": noop,
    "moves_left": noop,
    "health": noop,
    "veteran": noop,
    "upkeep_food": noop,
    "upkeep_shield": noop,
    "upkeep_gold": noop,
}

others_unit_ops = {
    "id": noop,
    "owner": noop,
    "x": noop,
    "y": noop,
    "type": onehotifier_maker(52),
    "veteran": noop,
    "transported": noop,
    "hp": noop,
    "activity": noop,
    "activity_tgt": noop,
    "transported_by": noop,
    "keep_activity": noop,
    "occupied": noop,
}

city_ops = {
    "id": noop,
    "x": noop,
    "y": noop,
    "owner": noop,
    "size": noop,
    "food_stock": noop,
    "granary_size": noop,
    "granary_turns": noop,
    "production_value": noop,
    "luxury": noop,
    "science": noop,
    "prod_food": noop,
    "surplus_food": noop,
    "prod_gold": noop,
    "surplus_gold": noop,
    "prod_shield": noop,
    "surplus_shield": noop,
    "prod_trade": noop,
    "surplus_trade": noop,
    "bulbs": noop,
    "city_waste": noop,
    "city_corruption": noop,
    "city_pollution": noop,
    "state": onehotifier_maker(5),
    "turns_to_prod_complete": noop,
    "prod_process": noop,
    "production_value": onehotifier_maker(120),
    "ppl_angry": noop,
    "ppl_unhappy": noop,
    "ppl_content": noop,
    "ppl_happy": noop,
    "city_radius_sq": noop,
    "buy_cost": noop,
    "shield_stock": noop,
    "before_change_shields": noop,
    "disbanded_shields": noop,
    "caravan_shields": noop,
    "last_turns_shield_surplus": noop,
    "improvements": noop,
}

others_city_ops = {
    "id": noop,
    "owner": noop,
    "size": noop,
    "style": onehotifier_maker(10),
    "capital": noop,
    "occupied": noop,
    "walls": noop,
    "happy": noop,
    "unhappy": noop,
    "improvements": noop,
}

others_player_ops = {
    "owner_id": noop,
    "love": onehotifier_maker(
        [
            "Genocidal",
            "Belligerent",
            "Hostile",
            "Uncooperative",
            "Uneasy",
            "Neutral",
            "Respectful",
            "Helpful",
            "Enthusiastic",
            "Admiring",
            "Worshipful",
        ]
    ),
    "score": noop,
    "is_alive": onehotifier_maker(2),
    "diplomatic_state": onehotifier_maker(8),
}
player_ops = {
    "turn": noop,
    "culture": noop,
    "reasearching_cost": noop,
    "gold": noop,
    "government": onehotifier_maker(6),
    "is_alive": noop,
    "luxury": noop,
    "net_income": lambda x: np.array([0], dtype=np.int32)
    if x is None
    else x * np.array([1], dtype=np.int32),
    "revolution_finishes": noop,
    "science": noop,
    "science_cost": noop,
    "score": noop,
    "target_government": onehotifier_maker(7),
    "tax": noop,
    "my_tech_goal": lambda x: onehotifier_maker(89)(88 if x == 253 else x),
    "tech_upkeep": noop,
    "techs_researched": noop,
    "total_bulbs_prod": noop,
    "turns_alive": noop,
    "no_humans": noop,
    "no_ais": noop,
    "research_progress": noop,
    "team_no": noop,
}

rules_ops = {
    # TODO: get build_cost from info?
    "build_cost": lambda _: np.array(UNIT_COSTS + IMPR_COSTS)
}


def resize_data(data: np.ndarray, size: int):
    remain_shape = data.shape[1:]
    data = data.copy()
    data.resize([size, *remain_shape],refcheck=False)
    return data


def deref_dict(data):
    return {k: (v.item() if isinstance(v, np.ndarray) else v) for k, v in data.items()}
