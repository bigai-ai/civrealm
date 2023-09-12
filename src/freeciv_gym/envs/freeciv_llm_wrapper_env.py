# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from gymnasium.core import Wrapper

from freeciv_gym.configs import fc_args
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.envs.freeciv_wrapper.llm_wrapper import LLMWrapper


class FreecivLLMWrapperEnv(Wrapper):
    """Freeciv gym environment with llm actions"""

    metadata = FreecivBaseEnv.metadata

    def __init__(self,
                 username: str = fc_args["username"],
                 client_port: int = fc_args["client_port"]):

        llm_env = LLMWrapper(FreecivBaseEnv(username=username, client_port=client_port))
        super().__init__(llm_env)

