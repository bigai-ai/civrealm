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

from civrealm.configs import fc_args
from civrealm.envs.freeciv_minitask_env import FreecivMinitaskEnv
from civrealm.envs.freeciv_wrapper import (MinitaskDelayedReward,
                                           MiniTaskGameOverScoreInfo,
                                           TensorWrapper, Wrapper)
from civrealm.envs.freeciv_wrapper.config import default_tensor_config


class FreecivTensorMinitaskEnv(Wrapper):
    """CivRealm environment with Tensor actions"""

    metadata = FreecivMinitaskEnv.metadata

    def __init__(
        self,
        minitask_pattern=None,
        username: str = fc_args["username"],
        client_port: int = fc_args["client_port"],
        config: dict = default_tensor_config,
    ):
        tensor_env = MiniTaskGameOverScoreInfo(
            TensorWrapper(
                env=MinitaskDelayedReward(
                    FreecivMinitaskEnv(username="minitask", client_port=client_port),
                    success_reward=100,
                    replacement=False,
                ),
                config=config,
            )
        )
        super().__init__(tensor_env)
        self.minitask_pattern = minitask_pattern
        # print(f'Env port: {tensor_env.get_port()}')
        self._cached_reset_result = super().reset(
            minitask_pattern=self.minitask_pattern
        )
        # reset during init to get valid obs space
        self.first_reset = True

    def reset(self, **kwargs):
        if self.first_reset and len(kwargs) == 0:
            # use cached reset during init for first reset
            obs, info = self._cached_reset_result
            self.first_reset = False
            return obs, info
        if "minitask_pattern" in kwargs:
            return super().reset(**kwargs)
        return super().reset(minitask_pattern=self.minitask_pattern, **kwargs)
