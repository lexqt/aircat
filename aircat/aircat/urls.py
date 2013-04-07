from django.conf.urls import patterns, include, url

from aircat.views import IndexView


urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='home'),
    url(r'^locations/', include(
                          'locations.urls', namespace='loc', app_name='loc')),
)
