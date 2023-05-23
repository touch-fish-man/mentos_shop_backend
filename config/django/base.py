"""
Django settings for proxy_admin project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import datetime

from pathlib import Path
import os
import pymysql

if os.environ.get('DJANGO_ENV') != 'prod' or os.environ.get('DJANGO_ENV') != 'test':
    pymysql.version_info = (1, 4, 6, "final", 0)
    pymysql.install_as_MySQLdb()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
from config.env import env

env.read_env(os.path.join(BASE_DIR, "config/.env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-bm6dtprdt+2j$whkuls$)q&qos%=loadtrg7qs^ytrwkhgx*ff'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'drf_yasg',
    "apps.users",
    "apps.tickets",
    "apps.orders",
    "apps.proxy_server",
    "apps.site_settings",
    "captcha",
    "django_extensions",
    "apps.rewards",
    "apps.products",
    "django_celery_beat",
    'django_celery_results',
    "apps.tasks",
    'drf_api_logger',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware',
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
ROOT_URLCONF = 'config.urls'
STATIC_URL = "/static/"

# # # 设置django的静态文件目录
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
# ]
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
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
DRF_API_LOGGER_DATABASE = True
DRF_API_LOGGER_SKIP_URL_NAME = ['checkout']
WSGI_APPLICATION = 'config.wsgi.application'
# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        "ATOMIC_REQUESTS": False,
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mentos_proxy',
        'USER': 'mentos_shop',
        'PASSWORD': '347dpWjxkKwrheBt',
        'HOST': 'rm-0xifvzx2x3769byjm.mysql.rds.aliyuncs.com',
        'PORT': 3066,
        "ATOMIC_REQUESTS": False}

}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators
AUTHENTICATION_BACKENDS = (
    'apps.authentication.utils.AuthBackend',
)
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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]
AUTH_USER_MODEL = "users.User"
# 验证码
CAPTCHA_IMAGE_SIZE = (120, 40)  # 图片大小
CAPTCHA_LENGTH = 4  # 字符个数
CAPTCHA_TIMEOUT = 1  # 超时(minutes)
CAPTCHA_OUTPUT_FORMAT = "%(image)s %(text_field)s %(hidden_field)s "
CAPTCHA_FONT_SIZE = 30  # 字体大小
CAPTCHA_LETTER_ROTATION = (-25, 25)  # 字体旋转角度
CAPTCHA_FOREGROUND_COLOR = "#da649d"  # 前景色
CAPTCHA_BACKGROUND_COLOR = "#F5F7F4"  # 背景色
# 字体
# CAPTCHA_FONT_PATH = os.path.join(BASE_DIR, "static/PangPangZhuRouTi-2.otf")
CAPTCHA_NOISE_FUNCTIONS = (
    "captcha.helpers.noise_arcs",  # 线
    # "captcha.helpers.noise_dots",  # 点
)
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.random_char_challenge'  # 字母验证码
# CAPTCHA_CHALLENGE_FUNCT = "captcha.helpers.math_challenge"  # 加减乘除验证码
LOGIN_URL = "/#/login"

SWAGGER_SETTINGS = {
    # 基础样式
    "SECURITY_DEFINITIONS": {"basic": {"type": "basic"}},
    # 如果需要登录才能够查看接口文档, 登录的链接使用restframework自带的.
    # "LOGIN_URL": "auth/apilogin",
    'LOGIN_URL': 'rest_framework:login',
    "LOGOUT_URL": "rest_framework:logout",
    # 'DOC_EXPANSION': None,
    # 'SHOW_REQUEST_HEADERS':True,
    # 'USE_SESSION_AUTH': True,
    # 'DOC_EXPANSION': 'list',
    # 接口文档中方法列表以首字母升序排列
    "APIS_SORTER": "alpha",
    # 如果支持json提交, 则接口文档中包含json输入框
    "JSON_EDITOR": True,
    # 方法列表字母排序
    "OPERATIONS_SORTER": "alpha",
    "VALIDATOR_URL": None,
    "AUTO_SCHEMA_TYPE": 2,  # 分组根据url层级分，0、1 或 2 层
    "DEFAULT_AUTO_SCHEMA_CLASS": "apps.core.swagger.CustomSwaggerAutoSchema",
    "DEFAULT_PAGINATOR_INSPECTORS": ['apps.core.swagger_ext.LimitOffsetPaginationInspector',
                                     'drf_yasg.inspectors.CoreAPICompatInspector', ]
}
REST_FRAMEWORK = {
    # 配置默认页面大小
    'PAGE_SIZE': 10,
    # 配置默认的分页类
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.CustomLimitOffsetPagination',
    # 配置默认的过滤类
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter'),
    # 配置默认权限
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     'rest_framework.permissions.IsAuthenticated',
    # ),

    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # 时间相关的字段

    # 配置异常处理器
    # 'EXCEPTION_HANDLER': 'api.exceptions.exception_handler',

    # 配置默认解析器
    # 'DEFAULT_PARSER_CLASSES': (
    # 'rest_framework.parsers.JSONParser',
    # 'rest_framework.parsers.FormParser',
    # 'rest_framework.parsers.MultiPartParser',
    # ),

    # 配置默认限流类
    # 'DEFAULT_THROTTLE_CLASSES': (),

    # 配置默认授权类
    # 'DEFAULT_PERMISSION_CLASSES': (
    # 'rest_framework.permissions.IsAuthenticated',
    # ),
    "EXCEPTION_HANDLER": "apps.core.exceptions.CustomExceptionHandler",
    # 配置默认认证类
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework.authentication.SessionAuthentication',
        'apps.core.middlewares.CsrfExemptSessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),

    # 关闭api调试界面
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',  # json渲染
        # 'rest_framework.renderers.BrowsableAPIRenderer',  # 浏览器渲染(生产环境可关掉)
    )
}

SIMPLE_JWT = {
    # token有效时长
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=30),
    # token刷新后的有效时间
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1), }

REDIS_PASSWORD = 'xB8U0Q6gyrMpRYA7'
REDIS_HOST = '177.8.0.14'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://{}:6379/1".format(REDIS_HOST),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": REDIS_PASSWORD,
        }
    }
}
# 配置日志
SERVER_LOGS_FILE = os.path.join(BASE_DIR, "logs", "django.log")
ERROR_LOGS_FILE = os.path.join(BASE_DIR, "logs", "error.log")
if not os.path.exists(os.path.join(BASE_DIR, "logs")):
    os.makedirs(os.path.join(BASE_DIR, "logs"))

# 格式:[2020-04-22 23:33:01][micoservice.apps.ready():16] [INFO] 这是一条日志:
# 格式:[日期][模块.函数名称():行号] [级别] 信息
STANDARD_LOG_FORMAT = (
    "[%(asctime)s][%(name)s.%(funcName)s():%(lineno)d] [%(levelname)s] %(message)s"
)
CONSOLE_LOG_FORMAT = (
    "[%(asctime)s][%(name)s.%(funcName)s():%(lineno)d] [%(levelname)s] %(message)s"
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": STANDARD_LOG_FORMAT},
        "console": {
            "format": CONSOLE_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "format": CONSOLE_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": SERVER_LOGS_FILE,
            "maxBytes": 1024 * 1024 * 100,  # 100 MB
            "backupCount": 5,  # 最多备份5个
            "formatter": "standard",
            "encoding": "utf-8",
        },
        "error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOGS_FILE,
            "maxBytes": 1024 * 1024 * 100,  # 100 MB
            "backupCount": 3,  # 最多备份3个
            "formatter": "standard",
            "encoding": "utf-8",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        # default日志
        "": {
            "handlers": ["console", "error", "file"],
            "level": "INFO",
        },
        "django": {
            "handlers": ["console", "error", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "scripts": {
            "handlers": ["console", "error", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # 数据库相关日志
        "django.db.backends": {
            "handlers": [],
            "propagate": True,
            "level": "INFO",
        },
    },
}
# ---------需要动态配置的配置项----------------
# discord oauth2 配置
DISCORD_CLIENT_ID = env('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = env('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = env('DISCORD_REDIRECT_URI')
DISCORD_BIND_REDIRECT_URI = env('DISCORD_BIND_REDIRECT_URI')

# shopify 配置
SHOPIFY_API_KEY = env('SHOPIFY_API_KEY')
SHOPIFY_API_SECRET = env('SHOPIFY_API_SECRET')
SHOPIFY_SHOP_URL = env('SHOPIFY_SHOP_URL')
SHOPIFY_APP_KEY = env('SHOPIFY_APP_KEY')
SHOPIFY_WEBHOOK_KEY = env('SHOPIFY_WEBHOOK_KEY')
# SHOPIFY_PRIVATE_APP_PASSWORD = env('SHOPIFY_PRIVATE_APP_PASSWORD')

# 邮件相关配置
EMAIL_METHOD = env('EMAIL_METHOD')  # 邮件发送方式 mailgun or sendgrid
EMAIL_CODE_EXPIRE = int(env('EMAIL_CODE_EXPIRE'))  # 邮件验证码过期时间
# smtp 配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 发送邮件配置
# sendgrid 配置
SENDGRID_API_KEY = env('SENDGRID_API_KEY')
# mailgun 配置
MAILGUN_API_KEY = env('MAILGUN_API_KEY')
MAILGUN_SENDER_DOMAIN = env('MAILGUN_SENDER_DOMAIN')

# 系统配置
# 客服联系方式配置
SUPPORT_TWITTER = env('SUPPORT_TWITTER')
SUPPORT_DISCORD = env('SUPPORT_DISCORD')
# 等级积分配置
INVITE_LEVEL_POINTS_PER_USER = int(env('INVITE_LEVEL_POINTS_PER_USER'))  # 邀请一个用户获得等级积分
BILLING_RATE = float(env('BILLING_RATE'))  # 消费获得等级积分比例 金额 * 比例 = 等级积分 消费后获得等级积分
LEVEL_POINTS_TO_UPGRADE = int(env('LEVEL_POINTS_TO_UPGRADE'))  # 升级所需等级积分
LEVEL_POINTS_DECAY_RATE = float(env('LEVEL_POINTS_DECAY_RATE'))  # 每月等级积分衰减比例
LEVEL_POINTS_DECAY_DAY = int(env('LEVEL_POINTS_DECAY_DAY'))  # 每月等级积分衰减日
MIN_LEVEL = int(env('MIN_LEVEL'))  # 最低等级
MAX_LEVEL = int(env('MAX_LEVEL'))  # 最高等级
LEVEL_DISCOUNT_RATE = float(env('LEVEL_DISCOUNT_RATE'))  # 等级折扣比例 1 - 等级折扣比例 * (等级 - 1) = 折扣
# 邀请返利配置
INVITE_REBATE_RATE = float(env('INVITE_REBATE_RATE'))  # 邀请返利比例 金额 * 比例 = 返利金额 受邀用户完成订单后返利给邀请人
# ---------需要动态配置的配置项----------------
FRONTEND_URL = env('FRONTEND_URL')

DISCORD_BOT_TOKEN = env('DISCORD_BOT_TOKEN')
DISCORD_BOT_CHANNELS = env('DISCORD_BOT_CHANNELS')
POINTS_PER_MESSAGE = int(env('POINTS_PER_MESSAGE'))
MAX_POINTS_PER_DAY = int(env('MAX_POINTS_PER_DAY'))
# 导入邮件模板配置
from .email_templates import *
from .celery import *
