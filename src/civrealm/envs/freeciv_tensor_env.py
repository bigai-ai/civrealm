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
from civrealm.envs.freeciv_base_env import FreecivBaseEnv
from civrealm.envs.freeciv_wrapper import (GameOverScoreInfo,
                                           PenalizeConsecutiveTurnDoneReward,
                                           TensorWrapper, Wrapper)
from civrealm.envs.freeciv_wrapper.config import default_tensor_config


class FreecivTensorEnv(Wrapper):
    """CivRealm environment with Tensor actions"""

    metadata = FreecivBaseEnv.metadata

    def __init__(
        self,
        username: str = fc_args["username"],
        client_port: int = fc_args["client_port"],
        config: dict = default_tensor_config,
    ):
        tensor_env = GameOverScoreInfo(
            TensorWrapper(
                env=PenalizeConsecutiveTurnDoneReward(
                    FreecivBaseEnv(username=username, client_port=client_port),
                    penalty=-1,
                ),
                config=config,
            )
        )
        super().__init__(tensor_env)
        self._cached_reset_result = super().reset()
        # reset during init to get valid obs space
        self.first_reset = True

    def reset(self, **kwargs):
        if self.first_reset and len(kwargs) == 0:
            # use cached reset during init for first reset
            obs, info = self._cached_reset_result
            self.first_reset = False
            return obs, info
        return super().reset(**kwargs)
