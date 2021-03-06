import logging
from boogie.configurations import DjangoConf, env
from .apps import InstalledAppsConf
from .celery import CeleryConf
from .constance import ConstanceConf
from .log import LoggingConf
from .middleware import MiddlewareConf
from .options import EjOptions
from .paths import PathsConf
from .security import SecurityConf
from .themes import ThemesConf
from .. import fixes

log = logging.getLogger('ej')


class Conf(ThemesConf,
           ConstanceConf,
           MiddlewareConf,
           CeleryConf,
           SecurityConf,
           LoggingConf,
           PathsConf,
           InstalledAppsConf,
           DjangoConf,
           EjOptions):
    """
    Configuration class for the EJ platform.

    Settings are created as attributes of a Conf instance and injected in
    the global namespace.
    """

    def get_using_sqlite(self):
        return 'sqlite3' in self.DATABASE_DEFAULT['ENGINE']

    def get_using_postgres(self):
        return 'postgresql' in self.DATABASE_DEFAULT['ENGINE']

    USING_DOCKER = env(False, name='USING_DOCKER')
    HOSTNAME = env('localhost')

    #
    # Accounts
    #
    AUTH_USER_MODEL = 'ej_users.User'
    ACCOUNT_AUTHENTICATION_METHOD = 'email'
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_UNIQUE_EMAIL = True
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    LOGIN_REDIRECT_URL = '/'
    SOCIALACCOUNT_PROVIDERS = {
        'facebook': {
            'SCOPE': ['email'],
            'METHOD': 'js_sdk'  # instead of 'oauth2'
        }
    }

    # MANAGER CONFIGURATION
    # See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
    MANAGERS = ADMINS = [
        ('Bruno Martin, Luan Guimarães, Ricardo Poppi, Henrique Parra', 'bruno@hacklab.com.br'),
        ('Laury Bueno', 'laury@hacklab.com.br'),
    ]

    #
    # Third party modules
    #
    MIGRATION_MODULES = {
        'sites': 'ej.contrib.sites.migrations'
    }

    EJ_CONVERSATIONS_URLMAP = {
        'conversation-detail': '/conversations/{conversation.slug}/',
        'conversation-list': '/conversations/',
    }

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        ),
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 50,
        'DEFAULT_VERSION': 'v1',
    }

    # REST_AUTH_REGISTER_SERIALIZERS = {
    #     'REGISTER_SERIALIZER': 'ej_users.serializers.RegistrationSerializer'
    # }


Conf.save_settings(globals())

#
# Apply fixes and wait for services to start
#
fixes.apply_all()
