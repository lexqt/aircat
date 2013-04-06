# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import csv
import itertools

from django.core.exceptions import ValidationError
from django.db import connections, models, transaction, IntegrityError

import geoprovider
from locations.models import Country, City, Airport


class Error(Exception):
    pass


class DataImporter(object):

    """Import airport, city and country information into DB

    Uses two sources:
     - file-like object with CSV airport data
     - GeoProvider instance to get missing data like city and country
       coords, Russian names, etc

    Queries DB for existing countries, cities and airports to avoid
    duplicate insertion attempts.

    Currently stores `Country` and `City` objects cache to support
    automatic unique slug generation based on parent-child relations.
    May be optimized by storing only object ids and manual slug assignment
    during import process.
    """

    def __init__(self, columns, stdout=sys.stdout, stderr=sys.stderr):
        self.columns = columns
        self.stdout = stdout
        self.stderr = stderr
        try:
            self.gp = geoprovider.GeoProvider()
        except geoprovider.Error as e:
            raise Error('GeoProvider init error: {0}'.format(e))
        self.countries = {}  # iso -> Country
        self.cities = {}  # (iso, name) -> City
        self.saved_countries = set()  # iso
        self.saved_cities = set()  # (iso, name)
        self.saved_airports = set()  # iata

        self.inserted_airport_cnt = 0
        self.existing_airport_cnt = 0

    def start(self, f, buffer_size=200, encoding='utf8'):
        columns = self.columns
        gp = self.gp

        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        if encoding:
            try:
                f.readline().decode(encoding)
            except UnicodeDecodeError as e:
                raise Error('Invalid encoding: {0}'.format(encoding))
        f.seek(0)
        reader = csv.reader(f, dialect)

        has_geo_info = ('city_name' in columns) and ('country_name' in columns)
        self.inserted_airport_cnt = 0
        self.existing_airport_cnt = 0
        rows_cnt = 0
        skipped_no_iata = 0
        skipped_insuf_info = set()
        skipped_insuf_reason = {
            'country': 0,
            'city': 0,
            'airport': 0
        }
        countries_buf, cities_buf, airports_buf = {}, {}, {}
        self.stdout.write('Started processing input file with buffer={0} '
                          'for airport objects'.format(buffer_size))
        for row in reader:
            rows_cnt += 1
            try:
                if (encoding):
                    row = map(lambda c: c.decode(encoding), row)
                # get IATA code, country ISO code and city name
                iata = row[columns['iata']]
                if not iata:
                    skipped_no_iata += 1
                    continue  # skip airports without IATA code
                if iata in self.saved_airports:
                    continue  # already saved
                country_city = gp.country_city_by_iata(iata)
                if not country_city:
                    if not has_geo_info:
                        skipped_insuf_info.add(iata)
                        skipped_insuf_reason['country'] += 1
                        continue
                    else:
                        country_name, city_name = (
                                               row[columns['country_name']],
                                               row[columns['city_name']])
                        iso = gp.country_iso_code(country_name)
                        if not iso:
                            skipped_insuf_info.add(iata)
                            skipped_insuf_reason['country'] += 1
                            continue
                else:
                    iso, city_name = (country_city[0], country_city[1])
                    if has_geo_info:
                        gp.add_alt_city_name(iso, city_name,
                                             row[columns['city_name']])
                        # row[columns['country_name']]

                # construct Country
                country = self.get_country(iso)
                if not country:
                    skipped_insuf_info.add(iata)
                    skipped_insuf_reason['country'] += 1
                    continue

                # construct City
                city = self.get_city(city_name, country)
                if not city:
                    skipped_insuf_info.add(iata)
                    skipped_insuf_reason['city'] += 1
                    continue

                # construct Airport
                airport = self.get_airport(iata, row, city)
                if not airport:
                    skipped_insuf_info.add(iata)
                    skipped_insuf_reason['airport'] += 1
                    continue

                # Bulk create or add to buffer
                if len(airports_buf) >= buffer_size:
                    self.stdout.write(
                        'Buffer is full. Saving airports and related cities '
                        'and countries objects to DB...')
                    self.flush_obj_buffers(countries_buf.viewvalues(),
                                           cities_buf.viewvalues(),
                                           airports_buf.viewvalues())
                    countries_buf, cities_buf, airports_buf = {}, {}, {}
                    self.stdout.write('Processing file again...')

                if iso not in self.saved_countries:
                    countries_buf[iso] = country
                if (iso, city_name) not in self.saved_cities:
                    cities_buf[(iso, city_name)] = city
                if iata not in self.saved_airports:
                    airports_buf[iata] = airport

            except IndexError as e:
                self.stderr.write('SKIP: Invalid data row: {0}'.format(e))
                rows_cnt -= 1

        self.stdout.write('Saving remaining objects to DB...')
        self.flush_obj_buffers(countries_buf.viewvalues(),
                               cities_buf.viewvalues(),
                               airports_buf.viewvalues())

        self.stdout.write('******************')
        self.stdout.write('*** Statistics ***')
        self.stdout.write('******************')
        self.stdout.write('Total valid rows count: {0}'.format(rows_cnt))
        self.stdout.write('Inserted new Airport objects: {0}'.format(
                                                 self.inserted_airport_cnt))
        self.stdout.write('Skipped Airport objects (exists in DB): {0}'.format(
                                                 self.existing_airport_cnt))
        self.stdout.write('Skipped rows (no IATA code): {0}'.format(
                                                            skipped_no_iata))
        self.stdout.write('Skipped airports (insufficient info): '
                          '{0}. Skipped because wasn\'t able to '
                          'construct:'.format(len(skipped_insuf_info)))
        sr = skipped_insuf_reason
        self.stdout.write('\tcountries: {0}\n\tcities: {1}\n'
                          '\tairports: {2}'.format(sr['country'],
                                                   sr['city'],
                                                   sr['airport']))

    def get_country(self, iso):
        cache = self.countries
        if iso in cache:
            return cache[iso]

        try:
            # try load country from DB
            c = Country.objects.get(iso_code=iso)
            self.saved_countries.add(iso)
        except Country.DoesNotExist:
            # construct new country
            names = self.gp.country_names(iso)
            latlon = self.gp.country_latlon(iso)
            if not names or not latlon:
                return
            c = Country(iso_code=iso,
                        name=names[0], name_ru=names[1],
                        latitude=latlon[0], longitude=latlon[1])
        cache[iso] = c
        return c

    def get_city(self, name, country):
        iso = country.iso_code
        cache = self.cities
        if (iso, name) in cache:
            return cache[(iso, name)]

        try:
            # try load city from DB
            c = City.objects.get(country__iso_code=iso, name=name)
            self.saved_cities.add((iso, name))
        except City.DoesNotExist:
            # construct new city
            names = self.gp.city_names(iso, name)
            latlon = self.gp.city_latlon(iso, name)
            if not names or not latlon:
                return
            c = City(name=names[0], name_ru=names[1],
                     latitude=latlon[0], longitude=latlon[1],
                     country=country)
        cache[(iso, name)] = c
        return c

    def get_airport(self, iata, row, city):
        try:
            # try load airport from DB
            a = Airport.objects.get(iata_code=iata)
            self.existing_airport_cnt += 1
            self.saved_airports.add(iata)
            return a
        except Airport.DoesNotExist:
            pass

        # construct new airport
        cols = self.columns
        names = self.gp.airport_names(iata)
        if not names:
            if 'airport_name' not in cols:
                return
            # use only English name
            names = (row[cols['airport_name']], '')

        coords = (row[cols['lat']], row[cols['lon']],
                  row[cols['alt']])
        return Airport(
                   iata_code=iata,
                   name=names[0], name_ru=names[1],
                   latitude=coords[0], longitude=coords[1], altitude=coords[2],
                   city=city)

    def flush_obj_buffers(self, countries, cities, airports):
        saved_countries = self.bulk_save(Country, countries)
        for c in saved_countries:
            self.saved_countries.add(c.iso_code)

        # Setting ids on cities objects is necessary because airports objects
        # references them. But why we can't use bulk_create for
        # `City` model with AutoField pks
        # https://code.djangoproject.com/ticket/19527

        # skip cities for which parents (countries) wasn't saved
        saved_countries_filter = (lambda o:
                                  o.country.iso_code in self.saved_countries)
        saved_cities = self.bulk_save(
                City,
                itertools.ifilter(saved_countries_filter, cities),
                ('country',), real_bulk=False)
        for c in saved_cities:
            self.saved_cities.add((c.country.iso_code, c.name))

        # reassign cities after save to init foreign key fields
        for a in airports:
            a.city = a.city

        # skip airports for which parents (cities) wasn't saved
        saved_cities_filter = (
           lambda o:
           ((o.city.country.iso_code, o.city.name) in self.saved_cities))

        saved_airports = self.bulk_save(
                Airport,
                itertools.ifilter(saved_cities_filter, airports),
                ('city',))
        self.inserted_airport_cnt += len(saved_airports)
        for a in saved_airports:
            self.saved_airports.add(a.iata_code)

    def bulk_save(self, model_cls, objs, validation_exclude=None,
                  real_bulk=True):
        if not objs:
            return ()

        saved_objs = []
        for o in objs:
            try:
                o.make_slug()
            except ValueError:
                self.stderr.write('SKIP: Can not make slug for {0}'.format(o))
                continue
            try:
                # skip unique checks for performance
                o.clean_fields(exclude=validation_exclude)
                o.clean()
            except ValidationError as e:
                self.stderr.write(
                      'SKIP: Validation failed for {0}: {1}'.format(o, e))
                continue
            saved_objs.append(o)

        if not saved_objs:
            return ()

        retry_by_one = [False]

        def try_bulk():
            with transaction.commit_manually():
                try:
                    model_cls.objects.bulk_create(saved_objs)
                except IntegrityError as e:
                    self.stderr.write('Bulk insertion failed: {0}'.format(e))
                    self.stderr.write('Falling back to save one by one')
                    transaction.rollback()
                    retry_by_one[0] = True
                else:
                    transaction.commit()

        def try_one_by_one():
            for obj in saved_objs[:]:
                try:
                    obj.save(force_insert=True)
                except IntegrityError as e:
                    self.stderr.write('SKIP: failed to save {0}: {1}'.format(
                                                                    obj, e))
                    saved_objs.remove(obj)

        if real_bulk:
            try_bulk()
        else:
            conn = connections['default']
            if (conn.vendor == 'sqlite' and
                    isinstance(saved_objs[0]._meta.pk, models.AutoField)):
                with transaction.commit_on_success():
                    # emulate SQLite behaviour on the insert
                    # get one larger than the largest ROWID in the table
                    # ref: http://www.sqlite.org/autoinc.html
                    pk = City.objects.aggregate(
                                        max_pk=models.Max('pk'))['max_pk']
                    pk = (pk or 0) + 1  # pk is None if table is empty
                    for o in saved_objs:
                        o.pk = pk
                        pk += 1
                    try_bulk()
            else:
                try_one_by_one()

        if retry_by_one[0]:
            try_one_by_one()

        return saved_objs
