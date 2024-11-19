import os

settings_module = os.getenv('DJANGO_SETTINGS_MODULE', 'FFLO_backend.settings.development')

if settings_module:
    module = __import__(settings_module, globals(), locals(), ['*'])
    for setting in dir(module):
        if setting.isupper():
            locals()[setting] = getattr(module, setting)
