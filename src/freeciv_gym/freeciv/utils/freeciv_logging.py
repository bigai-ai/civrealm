# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import logging.config

# You can set the level to logging.DEBUG or logging.WARN if you want to change the amount of output.
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../logging.conf')
log_file_path = os.path.normpath(log_file_path)

logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
fc_logger = logging.getLogger('freecivGym')
fc_logger.setLevel(logging.DEBUG)
