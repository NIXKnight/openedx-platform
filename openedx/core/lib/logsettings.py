"""Get log settings."""

import logging
import platform
import sys
import warnings
from logging.handlers import SysLogHandler

LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


def get_logger_config(log_dir,
                      logging_env="no_env",
                      local_loglevel='INFO',
                      service_variant=""):

    """

    Return the appropriate logging config dictionary. You should assign the
    result of this to the LOGGING var in your settings. The reason it's done
    this way instead of registering directly is because I didn't want to worry
    about resetting the logging state if this is called multiple times when
    settings are extended.
    """

    # Revert to INFO if an invalid string is passed in
    if local_loglevel not in LOG_LEVELS:
        local_loglevel = 'INFO'

    hostname = platform.node().split(".")[0]
    syslog_format = ("[service_variant={service_variant}]"
                     "[%(name)s][env:{logging_env}] %(levelname)s "
                     "[{hostname}  %(process)d] [%(filename)s:%(lineno)d] "
                     "- %(message)s").format(service_variant=service_variant,
                                             logging_env=logging_env,
                                             hostname=hostname)

    logger_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)s %(process)d '
                          '[%(name)s] %(filename)s:%(lineno)d - %(message)s',
            },
            'syslog_format': {'format': syslog_format},
            'raw': {'format': '%(message)s'},
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stderr,
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'local': {
                'level': local_loglevel,
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'formatter': 'syslog_format',
                'facility': SysLogHandler.LOG_LOCAL0,
            },
            'tracking': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'raw',
                'stream': sys.stdout
            },
        },
        'loggers': {
            'tracking': {
                'handlers': ['tracking'],
                'level': 'DEBUG',
                'propagate': False,
            },
            '': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            },
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
            },
            # requests is so loud at INFO (logs every connection) that we
            # force it to warn by default.
            'requests.packages.urllib3': {
                'level': 'WARN'
            }
        }
    }

    return logger_config


def log_python_warnings():
    """
    Stop ignoring DeprecationWarning, ImportWarning, and PendingDeprecationWarning;
    log all Python warnings to the main log file.

    Not used in test runs, so pytest can collect the warnings triggered for
    each test case.
    """
    warnings.simplefilter('default')
    warnings.filterwarnings('ignore', 'Not importing directory ')
    warnings.filterwarnings('ignore', 'Setting _field_data is deprecated')
    warnings.filterwarnings('ignore', 'Setting _field_data via the constructor is deprecated')
    try:
        # There are far too many of these deprecation warnings in startup to output for every management command;
        # suppress them until we've fixed at least the most common ones as reported by the test suite
        from django.utils.deprecation import RemovedInDjango20Warning, RemovedInDjango21Warning
        warnings.simplefilter('ignore', RemovedInDjango20Warning)
        warnings.simplefilter('ignore', RemovedInDjango21Warning)
    except ImportError:
        pass
    logging.captureWarnings(True)
