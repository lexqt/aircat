# -*- coding: utf-8 -*-

import os
import csv


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class Error(Exception):
    pass


class GeoProvider(object):

    def __init__(self):
        self._country_names = country_names = {}
        self._country_latlon = country_latlon = {}
        self._city_names = city_names = {}
        self._city_alt_names = city_alt_names = {}
        self._city_latlon = city_latlon = {}
        self._airport_data = airport_data = {}

        # *** apinfo.ru ***

        # load export.csv
        # format: iata_code|icao_code|name_rus|name_eng|city_rus|city_eng|country_rus|country_eng|iso_code|latitude|longitude|runway_elevation
        # IATA -> (name, name_ru)
        # Country ISO alpha-2 -> (name, name_ru, iso_code, city_name)
        # Country ISO alpha-2 -> City name -> (name, name_ru)

        with open(os.path.join(DATA_DIR, 'apinfo.ru/export.csv'), 'rb') as f:
            reader = csv.reader(f, delimiter='|', quoting=csv.QUOTE_NONE)
            try:
                reader.next()  # pop headers line
            except StopIteration:
                pass
            try:
                for row in reader:
                    row = map(lambda c: c.decode('cp1251'), row)
                    airport_data[row[0]] = (row[3], row[2],
                                            row[8], row[5])
                    country_names[row[8]] = (row[7], row[6])
                    city_names.setdefault(row[8], {})[row[5]] = (row[5], row[4])
            except (IndexError, UnicodeDecodeError):
                raise Error('Invalid data file')

        # *** geonames.org ***

        # load cities1000.csv
        # format: geonameid, name, asciiname, alternatenames, latitude, longitude, feature class, feature code, country code, cc2, admin1 code, admin2 code, admin3 code, admin4 code, population, elevation, dem, timezone, modification date
        # Country ISO alpha-2 -> City name -> (lat, lon)
        # Country ISO alpha-2 -> City name -> List of alternative names

        with open(os.path.join(DATA_DIR, 'geonames.org/cities1000.csv'), 'rb') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            try:
                for row in reader:
                    row = map(lambda c: c.decode('utf8'), row)
                    name, asciiname = row[1], row[2]
                    city_latlon.setdefault(row[8], {})[asciiname] = (row[4], row[5])
                    alternatives = row[3]
                    if not alternatives:
                        continue
                    coll = city_alt_names.setdefault(row[8], {})
                    alternatives = frozenset(alternatives.split(',') + [name, asciiname])
                    for name in alternatives:
                        coll[name] = alternatives
            except (IndexError, UnicodeDecodeError):
                raise Error('Invalid data file')

        # *** maxmind.com ***

        # load country_latlon.csv
        # format: "iso 3166 country","latitude","longitude"
        # Country ISO alpha-2 -> (lat, lon)

        with open(os.path.join(DATA_DIR, 'maxmind.com/country_latlon.csv'), 'rb') as f:
            reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)
            try:
                reader.next()  # pop headers line
            except StopIteration:
                pass
            try:
                for row in reader:
                    country_latlon[row[0]] = (row[1], row[2])
            except IndexError:
                raise Error('Invalid data file')

    def country_names(self, iso_code):
        '''Return country name pair (name_eng, name_rus)'''

        return self._country_names.get(iso_code)

    def country_latlon(self, iso_code):
        '''Return country geo coords pair (latitude, longitude)'''

        return self._country_latlon.get(iso_code)

    def city_names(self, iso_code, name):
        '''Return city name pair (name_eng, name_rus)'''

        coll = self._city_names.get(iso_code)
        if not coll:
            return

        if name in coll:
            return coll[name]
        return self._try_alt_city_name(iso_code, name, coll)

    def city_latlon(self, iso_code, name):
        '''Return city geo coords pair (latitude, longitude)'''

        coll = self._city_latlon.get(iso_code)
        if not coll:
            return

        if name in coll:
            return coll[name]
        return self._try_alt_city_name(iso_code, name, coll)

    def airport_names(self, iata_code):
        '''Return airport name pair (name_eng, name_rus)'''

        d = self._airport_data.get(iata_code)
        if not d:
            return
        return d[0:2]

    def country_city_by_iata(self, iata_code):
        '''Return country ISO code and city name by airport IATA code'''

        d = self._airport_data.get(iata_code)
        if not d:
            return
        return d[2:4]

    def _try_alt_city_name(self, iso_code, name, coll):
        cities = self._city_alt_names.get(iso_code)
        if not cities or name not in cities:
            return
        for alt_name in cities[name]:
            if alt_name in coll:
                return coll[alt_name]
