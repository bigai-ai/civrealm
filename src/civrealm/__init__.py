# Copyright (C) 2023  The CivRealm project
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


from gymnasium.envs.registration import register

register(
    id='freeciv/FreecivBase-v0',
    entry_point='civrealm.envs:FreecivBaseEnv',
)
register(
    id='freeciv/FreecivTensor-v0',
    entry_point='civrealm.envs:FreecivTensorEnv',
)
register(
    id='freeciv/FreecivTensorMinitask-v0',
    entry_point='civrealm.envs:FreecivTensorMinitaskEnv',
)
register(
    id='freeciv/FreecivLLM-v0',
    entry_point='civrealm.envs:FreecivLLMEnv',
)
register(
    id='freeciv/FreecivMinitask-v0',
    entry_point='civrealm.envs:FreecivMinitaskEnv',
)
