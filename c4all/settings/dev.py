from .base import *
import dj_database_url

LANGUAGE_CODE = 'en'

DEBUG = (ENV_SETTING('DEBUG', 'true') == 'true')
COMPRESS_ENABLED = (ENV_SETTING('COMPRESS_ENABLED', 'true') == 'true')

DATABASES = {'default': dj_database_url.config(
    default='postgres://postgres@localhost:5432/c4all')}

EMAIL_BACKEND = ENV_SETTING(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)

# Disable caching while in development
CACHES = {
    'default': {
        'BACKEND': ENV_SETTING(
            'CACHE_BACKEND',
            'django.core.cache.backends.dummy.DummyCache'
        )
    }
}

# Add SQL statement logging in development
if (ENV_SETTING('SQL_DEBUG', 'false') == 'true'):
    LOGGING['loggers']['django.db'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False
    }

# Enable django-compressor if it's installed
if COMPRESS_ENABLED:
    try:
        import compressor  # noqa
        INSTALLED_APPS += ('compressor',)
        STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)
    except ImportError:
        pass
