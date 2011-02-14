from django.conf import settings
from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', 'main.views.homepage', name='homepage'),
    url(r'^trade/$', 'main.views.trade', name='trade'),
    url(r'^position/$', 'main.views.position', name='position'),
    url(r'^helloworld/$', 'main.views.helloworld', name='helloworld'),
)

# includes
urlpatterns += patterns('',
    (r'^accounts/', include('accounts.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^adminfiles/', include('adminfiles.urls')),
)

# dev niceties
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        (r'^raw_template/(?P<template>.*)', 'django.views.generic.simple.direct_to_template'),
        (r'^messages_test/$', 'main.views.messages_test'),
    )
