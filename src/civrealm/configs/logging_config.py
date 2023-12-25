import time
import os
from civrealm.configs import fc_args

if fc_args['debug.logging_path'] is not None:
    logging_dir = os.path.expanduser(fc_args['debug.logging_path'])
else:
    logging_dir = os.path.normpath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '..', '..', '..', 'logs'))

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname) -3s [%(filename)s:%(lineno)d] %(message)s'
        },
    },
    'handlers': {
        'rootFileHandler': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': os.path.join(logging_dir, f"{time.strftime('%Y.%m.%d')}_root.log"),
            'mode': 'w',
        },
        'civrealmFileHandler': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            # Change time.strftime('%%Y.%%m.%%d') to time.strftime('%%Y.%%m.%%d_%%H:%%M:%%S') to create a new file for each script
            'filename': os.path.join(logging_dir, f"{time.strftime('%Y.%m.%d')}_{fc_args['username']}.log"),
            'mode': 'a',
        },
        'consoleHandler': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'handlers': ['rootFileHandler'],
            'level': 'INFO',
            'propagate': False
        },
        'root': {
            'handlers': ['rootFileHandler'],
            'level': 'INFO',
            'propagate': False
        },
        'civrealm': {
            'handlers': ['civrealmFileHandler'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}
