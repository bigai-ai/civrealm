import re
from collections.abc import Mapping
from typing import Dict

import numpy as np


def noop(value):
    if isinstance(value, list):
        return (np.array(value) * np.array([1])).astype(np.int32)
    return (value * np.array([1])).astype(np.int32)


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


def resize_data(data: np.ndarray, size: int):
    remain_shape = data.shape[1:]
    data = data.copy()
    data.resize([size, *remain_shape], refcheck=False)
    return data.astype(np.int32)


def add_shape(shape_1, shape_2):
    return (
        *shape_1[:-1],
        shape_1[-1] + shape_2[-1],
    )


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
                    if x != 255:
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
        raise NotImplementedError(f"Not implemented yet for type {type(category)}")
    return onehot


def rprint(dic, prefix_space=""):
    for key, val in dic.items():
        if isinstance(val, Dict):
            print(prefix_space + f"{key}:")
            rprint(dic[key], prefix_space + "  ")
        else:
            val = (
                val.shape
                if isinstance(val, np.ndarray)
                else "b"
                if isinstance(val, bool)
                else "i"
                if isinstance(val, int)
                else {type(val)}
            )
            print(f"{prefix_space}{key}:  {val}")


def rprinta(dic, prefix_space=""):
    if isinstance(dic, dict) and not isinstance(next(iter(dic.values())), Dict):
        distinct_starting_keys = {}
        for key in dic.keys():
            match = re.match(r"([a-zA-Z_]*)_*(\d_)*", key)
            starting_key = match.group(1)
            if starting_key in distinct_starting_keys:
                distinct_starting_keys[starting_key] += 1
            else:
                distinct_starting_keys[starting_key] = 1
        for key, count in distinct_starting_keys.items():
            print(f"{prefix_space}{key}:  {count}")
    else:
        for key, val in dic.items():
            print(prefix_space + f"{key}:")
            rprinta(val, prefix_space + "  ")
