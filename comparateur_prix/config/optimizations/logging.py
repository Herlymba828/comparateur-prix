import os

# Structured logging configuration (safe defaults; JSON optional)
# Enable JSON logs by setting LOG_JSON=true in environment.

def get_logging_config():
    log_json = os.getenv('LOG_JSON', 'false').lower() == 'true'

    formatters = {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        }
    }

    if log_json:
        try:
            import json_log_formatter  # noqa: F401
            formatters['json'] = {
                '()': 'json_log_formatter.JSONFormatter',
            }
        except Exception:
            pass

    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if log_json and 'json' in formatters else 'verbose',
        },
    }

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'root': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
        },
        'loggers': {
            'django.request': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
            'django.db.backends': {'level': os.getenv('LOG_SQL_LEVEL', 'WARNING'), 'handlers': ['console'], 'propagate': False},
        },
    }
