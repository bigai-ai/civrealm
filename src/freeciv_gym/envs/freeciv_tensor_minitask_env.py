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
from freeciv_gym.envs.freeciv_minitask_env import FreecivMinitaskEnv
from freeciv_gym.envs.freeciv_wrapper import (MinitaskDelayedReward,
                                              MinitaskDenseReward,
                                              TensorWrapper)
from freeciv_gym.envs.freeciv_wrapper.utils import default_tensor_config


class FreecivTensorMinitaskEnv(Wrapper):
    """Freeciv gym environment with Tensor actions"""

    metadata = FreecivMinitaskEnv.metadata

    def __init__(
        self,
        username: str = fc_args["username"],
        client_port: int = fc_args["client_port"],
        config: dict = default_tensor_config,
    ):
        tensor_env = TensorWrapper(
            env=MinitaskDenseReward(
                FreecivMinitaskEnv(username="minitask", client_port=client_port)
            ),
            config=config,
        )
        super().__init__(tensor_env)

        self._cached_reset_result = self.env.reset()
        # reset during init to get valid obs space
        self.first_reset = True

    def reset(self, **kwargs):
        if self.first_reset:
            # use cached reset during init for first reset
            obs, info = self._cached_reset_result
            self.first_reset = False
            return obs, info
        return self.env.reset(**kwargs)
