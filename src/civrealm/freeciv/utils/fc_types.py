import importlib
import os
from civrealm.configs import fc_args, fc_web_args
from enum import Enum, unique

@unique
class FC_TYPES_VERSION(Enum):
    STABLE_VERSION = 13
    DEV_VERSION = 14

def load_version(version):
    config_module = importlib.import_module(f'civrealm.freeciv.utils.version.v{version}')
    return config_module

def get_version():
    if fc_args["service"] == "freeciv-web" and fc_web_args["tag"] == "latest":
        return FC_TYPES_VERSION.DEV_VERSION.value
    return FC_TYPES_VERSION.STABLE_VERSION.value

globals().update(
    load_version(
        get_version()
    ).__dict__
)

# Server-side agents (freeciv 3.x): autoworker / autoexplore are requested with
# packet_unit_server_side_agent_set, not with a unit activity.
packet_unit_server_side_agent_set = 74
SSA_AUTOWORKER = 1
SSA_AUTOEXPLORE = 2
SSA_NONE = 0
