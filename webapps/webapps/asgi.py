"""
WSGI config for webapps project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import channels.asgi

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapps.settings")
channel_layer = channels.asgi.get_channel_layer()


#from django.core.wsgi import get_wsgi_application
#from whitenoise.django import DjangoWhiteNoise#

#application = get_wsgi_application()
#application = DjangoWhiteNoise(application)
