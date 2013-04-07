# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from django.http import Http404

from locations.models import Country, City, Airport


class FirstLetterFilterMixin(object):

    def filter_by_first_letter(self, qs):
        fl = self.request.GET.get('fl_en')
        if not fl:
            fl = self.request.GET.get('fl_ru')
            if not fl:
                # no filtration required
                return qs
            attr = 'name_ru'
            qs = qs.order_by('name_ru')
        else:
            attr = 'name'
        fl = fl[0]
        kwargs = {}
        kwargs[attr + '__istartswith'] = fl
        return qs.filter(**kwargs)

    def get_filter_context_data(self):
        context = {}
        args = self.request.GET
        if args.get('fl_ru'):
            context['force_ru'] = True
        context['include_show_all'] = args.get('fl_en') or args.get('fl_ru')
        return context


class CountryListView(ListView, FirstLetterFilterMixin):

    model = Country

    def get_queryset(self):
        return self.filter_by_first_letter(Country.objects.all())

    def get_context_data(self, **kwargs):
        ctx = super(CountryListView, self).get_context_data(**kwargs)
        ctx.update(self.get_filter_context_data())
        return ctx


class CityListView(ListView, FirstLetterFilterMixin):

    model = City

    def dispatch(self, request, *args, **kwargs):
        self.country = get_object_or_404(Country, iso_code=kwargs['country'])
        return super(CityListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = City.objects.filter(country=self.country)
        return self.filter_by_first_letter(qs)

    def get_context_data(self, **kwargs):
        ctx = super(CityListView, self).get_context_data(**kwargs)
        ctx.update(self.get_filter_context_data())
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
