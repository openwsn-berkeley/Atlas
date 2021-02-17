LOGGING_CONFIG = { 
    'version':                    1,
    'disable_existing_loggers':   True,
    'formatters': { 
        'formatter_console': { 
            #'format':             '%(message)s',
            'style':              '{',
            'format':             '{message}',
        },
        'formatter_file': {
            'style':              '{',
            'format':             '{asctime} [{levelname:>8}] {name:>12}: {message}',
        },
    },
    'handlers': { 
        'handler_console': { 
            'level':              'INFO',
            'formatter':          'formatter_console',
            'class':              'logging.StreamHandler',
        },
        'handler_file': {
            'level':              'DEBUG',
            'formatter':          'formatter_file',
            'class':              'logging.handlers.RotatingFileHandler',
            'filename':           'Atlas.log',
            'maxBytes':           1000000,
            'backupCount':        10
        },
    },
    'loggers': { 
        '': { # root
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
        'RunSim': { 
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
        'Orchestrator': { 
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
        'DotBot': { 
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
    } 
}
