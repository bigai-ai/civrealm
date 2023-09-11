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
from freeciv_gym.envs.freeciv_wrapper.tensor_wrapper import TensorWrapper
from freeciv_gym.envs.freeciv_wrapper.utils import default_tensor_config


class FreecivTensorEnv(Wrapper):
    """Freeciv gym environment with Tensor actions"""

    metadata = FreecivBaseEnv.metadata

    def __init__(
        self,
        username: str = fc_args["username"],
        client_port: int = fc_args["client_port"],
        config: dict = default_tensor_config,
    ):
        tensor_env = TensorWrapper(
            FreecivBaseEnv(username=username, client_port=client_port), config = config
        )
        super().__init__(tensor_env)
        self._cached_reset_result = self.env.reset()
        self.first_reset = True


    def reset(self):
        if self.first_reset:
            obs, info = self._cached_reset_result
            return obs, info
        observation, info = self.env.reset()
        return batchdict(observation), info
