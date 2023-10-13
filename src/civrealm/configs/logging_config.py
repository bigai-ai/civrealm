import time
from civrealm.configs import fc_args

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
            'filename': f"logs/{time.strftime('%Y.%m.%d')}_root.log",
            'mode': 'a',
        },
        'civrealmFileHandler': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            # Change time.strftime('%%Y.%%m.%%d') to time.strftime('%%Y.%%m.%%d_%%H:%%M:%%S') to create a new file for each script
            'filename': f"logs/{time.strftime('%Y.%m.%d')}_{fc_args['username']}.log",
            'mode': 'w',
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
