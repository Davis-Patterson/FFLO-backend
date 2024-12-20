from .base import *
from decouple import config
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = ['fflo-backend-86fee1187c21.herokuapp.com']

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://<username>:<password>@localhost:5432/<database>'
    )
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware ...
] + MIDDLEWARE

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
