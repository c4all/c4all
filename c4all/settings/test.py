# Settings file optimized for test running. Sets up in-memory database,
# Nose test runner and disables South for the tests

from .base import *
import dj_database_url

DATABASES = {'default': dj_database_url.config(
    default='postgres://postgres@localhost:5432/c4all')}

# Disable cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

try:
    import django_nose  # noqa
    import os.path
    INSTALLED_APPS += (
        'django_nose',
    )
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    PROJECT_APPS = [
        app for app in INSTALLED_APPS if os.path.exists(
            os.path.join(ROOT_DIR, '..', app)
        )
    ]
    if PROJECT_APPS:
        NOSE_ARGS = ['--cover-package=' + ','.join(PROJECT_APPS)]
except ImportError:
    pass


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

LANGUAGE_CODE = 'en'
