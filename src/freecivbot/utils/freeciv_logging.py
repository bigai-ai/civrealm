import os
import logging
import logging.config

# You can set the level to logging.DEBUG or logging.WARN if you want to change the amount of output.
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logging.conf')
log_file_path = os.path.normpath(log_file_path)

logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
logger = logging.getLogger('freecivGym')
logger.setLevel(logging.DEBUG)
