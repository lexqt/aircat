# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse
from django.core.validators import MinLengthValidator
from django.utils.text import slugify

class Location(models.Model):

    class Meta:
        abstract = True

    name = models.CharField('название', max_length=100)
    name_ru = models.CharField('русское название', max_length=100, blank=True)
    slug = models.SlugField(max_length=100, unique=True)

    latitude = models.DecimalField('широта', max_digits=9, decimal_places=6)
    longitude = models.DecimalField('долгота', max_digits=9, decimal_places=6)

    def make_slug(self, *args):
        """Generate and set slug for model"""
        raise NotImplementedError

    def extended_name(self):
        """Returns both names (en, ru) when available"""
        if self.name_ru:
            return '{0} ({1})'.format(self.name, self.name_ru)
        return self.name

    def name_ru_preferable(self):
        return self.name_ru if self.name_ru else self.name

    def get_absolute_url(self):
        url_name = (self.__class__.__name__.lower()
                        if not hasattr(self, '_url_name')
                        else self._url_name)
        return reverse('loc:{0}'.format(url_name), kwargs={'slug': self.slug})

    def __unicode__(self):
        return self.name


class Country(Location):

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'
        ordering = ['name']
        unique_together = ('name',)

    iso_code = models.CharField('ISO код', primary_key=True, max_length=2,
                                validators=[MinLengthValidator(2)],
                                help_text='ISO 3166-1 alpha-2 код страны')

    def make_slug(self, *args):
        if args:
            self.slug = slugify_args(args)
            return
        if not self.name:
            raise ValueError
        self.slug = slugify_args(self.iso_code, self.name)


class City(Location):

    class Meta:
        verbose_name = 'город'
        verbose_name_plural = 'города'
        ordering = ['name']
        unique_together = ('country', 'name')

    country = models.ForeignKey(Country, related_name='cities',
                                db_column='country_iso',
                                verbose_name='страна')

    def make_slug(self, *args):
        if args:
            self.slug = slugify_args(args)
            return
        try:
            self.country
        except Country.DoesNotExist:
            raise ValueError
        if not self.name or not self.country.iso_code:
            raise ValueError
        self.slug = slugify_args(self.country.iso_code, self.name)


class Airport(Location):

    class Meta:
        verbose_name = 'аэропорт'
        verbose_name_plural = 'аэропорты'
        ordering = ['name']
        unique_together = ('city', 'name')

    altitude = models.IntegerField('высота')

    iata_code = models.CharField('IATA код', primary_key=True, max_length=3,
                                validators=[MinLengthValidator(3)],
                                help_text='IATA код аэропорта')
    city = models.ForeignKey(City, related_name='airports',
                                verbose_name='город')

    def make_slug(self, *args):
        if args:
            self.slug = slugify_args(args)
            return
        if not self.iata_code or not self.name:
            raise ValueError
        self.slug = slugify_args(self.iata_code, self.name)


def slugify_args(*args):
    if not args:
        raise ValueError
    return slugify('-'.join(args))
