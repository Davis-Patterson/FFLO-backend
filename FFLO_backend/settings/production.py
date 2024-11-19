from .base import *
from decouple import config
import dj_database_url

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['your-render-app.onrender.com', 'your-custom-domain.com']

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', '')
    )
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware ...
]

# Simplified static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
