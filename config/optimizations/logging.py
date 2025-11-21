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
            # Import optionnel pour le formatage JSON des logs
            # Utiliser __import__ pour éviter l'avertissement du linter si le module n'est pas installé
            json_log_formatter = __import__('json_log_formatter', fromlist=['JSONFormatter'])
            formatters['json'] = {
                '()': 'json_log_formatter.JSONFormatter',
            }
        except ImportError:
            # json_log_formatter n'est pas installé, on continue sans format JSON
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
            # Logger spécifique pour l'app utilisateurs - niveau ERROR pour capturer toutes les erreurs
            'apps.utilisateurs': {'level': 'ERROR', 'handlers': ['console'], 'propagate': False},
            'apps.utilisateurs.views': {'level': 'ERROR', 'handlers': ['console'], 'propagate': False},
        },
    }
