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

import logging
import logging.config

from freeciv_gym.configs.logging_config import LOGGING_CONFIG

# # You can set the level to logging.DEBUG or logging.WARN if you want to change the amount of output.
logging.config.dictConfig(LOGGING_CONFIG)
fc_logger = logging.getLogger('freecivGym')


# class DummyLogger():
#     def __init__(self) -> None:
#         self.handlers = ['']
#     def info(self, msg):
#         pass
#     def debug(self, msg):
#         pass
#     def warning(self, msg):
#         pass
#     def error(self, msg):
#         pass

# fc_logger = DummyLogger()