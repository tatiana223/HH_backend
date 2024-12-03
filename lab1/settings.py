import os
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for airlineion
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in airlineion secret!
SECRET_KEY = 'django-insecure-jug1gtqrsut0pl-3)__4@*wybxdqibme=0p==sh6_h)njz)9ok'

# SECURITY WARNING: don't run with debug turned on in airlineion!
DEBUG = True


ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # DRF
    'drf_yasg',
    'rest_framework',
    # Наше приложение
    'app',

]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Сессии хранятся в базе данных
SESSION_COOKIE_AGE = 3600  # Продолжительность сессии в секундах
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Сессия будет закрываться при закрытии браузера


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ]

}

ROOT_URLCONF = 'lab1.urls'



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'lab1.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',   # Используется PostgreSQL
        'NAME': 'employment_db', # Имя базы данных
        'USER': 'postgres', # Имя пользователя
        'PASSWORD': '1234', # Пароль пользователя
        'HOST': 'pgdb', # Наименование контейнера для базы данных в Docker Compose
        'PORT': '5432',  # Порт базы данных
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field


SESSION_CACHE_ALIAS = 'default'  # Использование кэша по умолчанию
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # Убедитесь, что Redis работает и доступен
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

AWS_STORAGE_BUCKET_NAME = 'images'
AWS_ACCESS_KEY_ID = 'minio'
AWS_SECRET_ACCESS_KEY = 'minio123'
AWS_S3_ENDPOINT_URL = 'minio:9000'
MINIO_USE_SSL = False

REDIS_HOST = 'redis'
REDIS_PORT = 6379

INSTALLED_APPS += ['corsheaders']

MIDDLEWARE += ['corsheaders.middleware.CorsMiddleware']

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React
]