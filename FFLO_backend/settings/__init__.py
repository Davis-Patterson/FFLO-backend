import os
from decouple import config

settings_module = config('DJANGO_SETTINGS_MODULE', 'FFLO_backend.settings.development')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

if settings_module:
    module = __import__(settings_module, globals(), locals(), ['*'])
    for setting in dir(module):
        if setting.isupper():
            locals()[setting] = getattr(module, setting)
