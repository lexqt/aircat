# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from locations.views import (
     CountryListView, CityListView, AirportListView,
     CountryDetailView, CityDetailView, AirportDetailView)

urlpatterns = patterns('',
    url(r'^countries$', CountryListView.as_view(), name='countries'),
    url(r'^country/(?P<slug>[\w-]+)$', CountryDetailView.as_view(),
        name='country'),
    url(r'^cities/(?P<country>[A-Z]{2})$', CityListView.as_view(),
        name='cities'),
    url(r'^city/(?P<slug>[\w-]+)$', CityDetailView.as_view(), name='city'),
    url(r'^airports/(?P<city>\d+)$', AirportListView.as_view(),
        name='airports'),
    url(r'^airport/(?P<slug>[\w-]+)$', AirportDetailView.as_view(),
        name='airport'),
)
