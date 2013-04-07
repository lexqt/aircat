# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from django.http import Http404

from locations.models import Country, City, Airport


class CountryListView(ListView):

    model = Country


class CityListView(ListView):

    model = City

    def dispatch(self, request, *args, **kwargs):
        self.country = get_object_or_404(Country, iso_code=kwargs['country'])
        return super(CityListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return City.objects.filter(country=self.country)

    def get_context_data(self, **kwargs):
        ctx = super(CityListView, self).get_context_data(**kwargs)
        ctx['country'] = self.country
        return ctx


class AirportListView(ListView):

    model = Airport

    def dispatch(self, request, *args, **kwargs):
        try:
            city = City.objects.select_related().get(id=kwargs['city'])
        except City.DoesNotExist:
            raise Http404
        self.city = city
        self.country = city.country
        return super(AirportListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Airport.objects.filter(city=self.city)

    def get_context_data(self, **kwargs):
        ctx = super(AirportListView, self).get_context_data(**kwargs)
        ctx['city'] = self.city
        ctx['country'] = self.country
        return ctx


class CountryDetailView(DetailView):

    model = Country


class CityDetailView(DetailView):

    model = City

    def get_queryset(self):
        return City.objects.select_related()

    def get_context_data(self, **kwargs):
        ctx = super(CityDetailView, self).get_context_data(**kwargs)
        ctx['country'] = self.object.country
        return ctx


class AirportDetailView(DetailView):

    model = City

    def get_queryset(self):
        return Airport.objects.select_related()

    def get_context_data(self, **kwargs):
        ctx = super(AirportDetailView, self).get_context_data(**kwargs)
        ctx['city'] = self.object.city
        ctx['country'] = self.object.city.country
        return ctx
