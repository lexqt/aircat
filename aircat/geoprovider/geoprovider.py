# -*- coding: utf-8 -*-

import os
import csv


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class Error(Exception):
    pass


class GeoProvider(object):

    files = {
        'apinfo.ru': {
            'path': 'apinfo.ru/export.csv',
            'delimiter': '|',
            'quote': csv.QUOTE_NONE,
            'encoding': 'cp1251',
            'pop_headers': True
        },
        'geonames.org/countries': {
            'path': 'geonames.org/countryInfoCSV.csv',
            'delimiter': '\t',
            'quote': csv.QUOTE_NONE,
            'encoding': 'utf8',
            'pop_headers': True
        },
        'geonames.org/countries_ru': {
            'path': 'geonames.org/countryInfoCSV_ru.csv',
            'delimiter': '\t',
            'quote': csv.QUOTE_NONE,
            'encoding': 'utf8',
            'pop_headers': True
        },
        'geonames.org/cities': {
            'path': 'geonames.org/cities1000.csv',
            'delimiter': '\t',
            'quote': csv.QUOTE_NONE,
            'encoding': 'utf8'
        },
        'maxmind.com/country_latlon': {
            'path': 'maxmind.com/country_latlon.csv',
            'delimiter': ',',
            'quote': csv.QUOTE_NONE,
            'pop_headers': True
        },
    }

    def __init__(self):
        self._country_names = country_names = {}
        self._country_codes = country_codes = {}
        self._country_latlon = country_latlon = {}
        self._city_names = city_names = {}
        self._city_alt_names = city_alt_names = {}
        self._city_latlon = city_latlon = {}
        self._airport_data = airport_data = {}

        # *** geonames.org ***

        # load countries data
        # format: iso alpha2, iso alpha3, iso numeric, fips code, name, capital, areaInSqKm, population, continent, languages, currency, geonameId
        # Country ISO alpha-2 -> (name, name_ru)
        # Country name -> Country ISO alpha-2

        fmeta = self.files['geonames.org/countries']
        with open(os.path.join(DATA_DIR, fmeta['path']), 'rb') as f:
            reader = self.prepare_reader(f, fmeta)
            try:
                for row in reader:
                    iso, name = row[0], row[4]
                    country_names[iso] = (name, None)
                    country_codes[name] = iso
            except IndexError:
                raise Error('Invalid data file')

        fmeta = self.files['geonames.org/countries_ru']
        with open(os.path.join(DATA_DIR, fmeta['path']), 'rb') as f:
            reader = self.prepare_reader(f, fmeta)
            try:
                for row in reader:
                    iso, name_ru = row[0], row[4]
                    country_codes[name_ru] = iso
                    if iso not in country_names:
                        continue
                    country_names[iso] = (country_names[iso][0], name_ru)
            except IndexError:
                raise Error('Invalid data file')

        # load cities data
        # format: geonameid, name, asciiname, alternatenames, latitude, longitude, feature class, feature code, country code, cc2, admin1 code, admin2 code, admin3 code, admin4 code, population, elevation, dem, timezone, modification date
        # Country ISO alpha-2 -> City name -> (lat, lon)
        # Country ISO alpha-2 -> City name -> Set of alternative names

        fmeta = self.files['geonames.org/cities']
        with open(os.path.join(DATA_DIR, fmeta['path']), 'rb') as f:
            reader = self.prepare_reader(f, fmeta)
            try:
                for row in reader:
                    name, asciiname, iso = row[1], row[2], row[8]
                    city_latlon.setdefault(iso, {})[asciiname] = (row[4],
                                                                  row[5])
                    alternatives = row[3]
                    if not alternatives:
                        continue
                    coll = city_alt_names.setdefault(iso, {})
                    alternatives = set(alternatives.split(',') +
                                       [name, asciiname])
                    for name in alternatives:
                        coll[name] = alternatives
            except IndexError:
                raise Error('Invalid data file')

        # *** maxmind.com ***

        # load country coords data
        # format: "iso 3166 country","latitude","longitude"
        # Country ISO alpha-2 -> (lat, lon)

        fmeta = self.files['maxmind.com/country_latlon']
        with open(os.path.join(DATA_DIR, fmeta['path']), 'rb') as f:
            reader = self.prepare_reader(f, fmeta)
            try:
                for row in reader:
                    country_latlon[row[0]] = (row[1], row[2])
            except IndexError:
                raise Error('Invalid data file')

        # *** apinfo.ru ***

        # load airports dump
        # format: iata_code|icao_code|name_rus|name_eng|city_rus|city_eng|country_rus|country_eng|iso_code|latitude|longitude|runway_elevation
        # IATA -> (name, name_ru, iso_code, city_name)
        # Country name -> Country ISO alpha-2
        # Country ISO alpha-2 -> City name -> (name, name_ru)

        fmeta = self.files['apinfo.ru']
        with open(os.path.join(DATA_DIR, fmeta['path']), 'rb') as f:
            reader = self.prepare_reader(f, fmeta)
            try:
                for row in reader:
                    iata, aname_ru, aname = row[0], row[2], row[3]
                    ciname_ru, ciname = row[4], row[5]
                    coname_ru, coname, iso = row[6], row[7], row[8]
                    airport_data[iata] = (aname, aname_ru,
                                            iso, ciname)
                    country_codes[coname] = iso
                    country_codes[coname_ru] = iso
                    city_names.setdefault(iso, {})[ciname] = (ciname,
                                                              ciname_ru)
            except IndexError:
                raise Error('Invalid data file')

    def country_names(self, iso_code):
        """Return country name pair (name_eng, name_rus)"""
        return self._country_names.get(iso_code)

    def country_latlon(self, iso_code):
        """Return country geo coords pair (latitude, longitude)"""
        return self._country_latlon.get(iso_code)

    def country_iso_code(self, name):
        """Return ISO code by country name"""
        return self._country_codes.get(name)

    def city_names(self, iso_code, name):
        """Return city name pair (name_eng, name_rus)"""
        coll = self._city_names.get(iso_code)
        if not coll:
            return

        if name in coll:
            return coll[name]
        return self._try_alt_city_name(iso_code, name, coll)

    def city_latlon(self, iso_code, name):
        """Return city geo coords pair (latitude, longitude)"""
        coll = self._city_latlon.get(iso_code)
        if not coll:
            return

        if name in coll:
            return coll[name]
        return self._try_alt_city_name(iso_code, name, coll)

    def airport_names(self, iata_code):
        """Return airport name pair (name_eng, name_rus)"""
        d = self._airport_data.get(iata_code)
        if not d:
            return
        return d[0:2]

    def country_city_by_iata(self, iata_code):
        """Return country ISO code and city name by airport IATA code"""
        d = self._airport_data.get(iata_code)
        if not d:
            return
        return d[2:4]

    def add_alt_city_name(self, iso_code, name, alt_name):
        if name == alt_name:
            return
        cities = self._city_alt_names.get(iso_code)
        if not cities or name not in cities or alt_name in cities:
            return
        coll = cities[name]
        coll.add(alt_name)
        cities[alt_name] = coll

    def _try_alt_city_name(self, iso_code, name, coll):
        cities = self._city_alt_names.get(iso_code)
        if not cities or name not in cities:
            return
        for alt_name in cities[name]:
            if alt_name in coll:
                return coll[alt_name]

    @classmethod
    def prepare_reader(cls, f, fmeta):
        reader = csv.reader(f, delimiter=fmeta['delimiter'],
                    quoting=fmeta['quote'])
        if 'pop_headers' in fmeta:
            try:
                reader.next()
            except StopIteration:
                pass
        if 'encoding' not in fmeta:
            return reader
        return _ReaderWrapper(reader, fmeta['encoding'])


class _ReaderWrapper(object):

    def __init__(self, reader, encoding):
        self.reader = reader
        self.encoding = encoding

    def __iter__(self):
        return self

    def next(self):
        while True:
            # skip empty rows
            row = self.reader.next()
            if row:
                break
        return map(lambda c: c.decode(self.encoding), row)
