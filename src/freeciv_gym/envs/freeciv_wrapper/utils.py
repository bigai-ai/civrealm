from typing import (
    Union,
    Mapping,
    MutableMapping,
    Sequence,
    Callable,
    Hashable,
    Any,
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


def filter_apply_space(
    # apply func to a nested space recursively using arguments contained by a nested dict
    space: spaces.Space,
    func: Callable,
    args_dict: Union[dict, Any],
) -> spaces.Space:
    if isinstance(space, spaces.Dict) and isinstance(args_dict, dict):
        return type(space)(
            [
                (key, filter_space(space.spaces[key], args_dict[key]))
                if key in args_dict
                else (key, val)
                for key, val in space.items()
            ]
        )
    else:
        return func(args_dict)


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
