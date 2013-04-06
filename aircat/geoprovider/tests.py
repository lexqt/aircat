# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest

from geoprovider import GeoProvider


class GeoProviderTest(unittest.TestCase):
    '''Test GeoProvider functionality on concrete dataset (*.csv from data dir)
    '''

    @classmethod
    def setUpClass(cls):
        cls.gp = GeoProvider()

    def test_country_names(self):
        # geonames.org/countryInfoCSV{,_ru}.csv contain rows:
        # RU  ...  Russia
        # RU  ...  Россия
        # US  ...  United States
        # US  ...  США
        self.assertEqual(self.gp.country_names('RU'),
                         ('Russia', 'Россия'))
        self.assertEqual(self.gp.country_names('US'),
                         ('United States', 'США'))
        self.assertIsNone(self.gp.country_names('XX'))

    def test_country_iso_code(self):
        # apinfo.ru/export.csv contains rows:
        # ...|Россия|Russian Federation|RU|...
        # ...|США|United States|US|...
        # geonames.org/countryInfoCSV.csv contains rows:
        # RU  ...  Russia
        self.assertEqual(self.gp.country_iso_code('Russian Federation'), 'RU')
        self.assertEqual(self.gp.country_iso_code('Russia'), 'RU')
        self.assertEqual(self.gp.country_iso_code('United States'), 'US')
        self.assertIsNone(self.gp.country_iso_code('XX'))

    def test_country_latlon(self):
        # maxmind.com/country_latlon.csv contains rows:
        # RU,60.0000,100.0000
        # US,38.0000,-97.0000
        self.assertEqual(self.gp.country_latlon('RU'),
                         ('60.0000', '100.0000'))
        self.assertEqual(self.gp.country_latlon('US'),
                         ('38.0000', '-97.0000'))
        self.assertIsNone(self.gp.country_latlon('XX'))

    def test_city_names(self):
        # apinfo.ru/export.csv contains rows:
        # ...|Санкт-Петербург|St Petersburg|...|RU|...
        # ...||Leesburg|...|US|...
        self.assertEqual(self.gp.city_names('RU', 'St Petersburg'),
                         ('St Petersburg', 'Санкт-Петербург'))
        self.assertEqual(self.gp.city_names('US', 'Leesburg'),
                         ('Leesburg', ''))
        self.assertIsNone(self.gp.city_names('XX', 'XX City'))

    def test_city_latlon(self):
        # geonames.org/cities1000.csv contains rows:
        # ...  Moscow  ...  55.75222  37.61556  ...  RU  ...
        # ...  New York City  ...  40.71427  -74.00597  ...  US  ...
        self.assertEqual(self.gp.city_latlon('RU', 'Moscow'),
                         ('55.75222', '37.61556'))
        self.assertEqual(self.gp.city_latlon('US', 'New York City'),
                         ('40.71427', '-74.00597'))
        self.assertIsNone(self.gp.city_latlon('XX', 'XX City'))

    def test_airport_names(self):
        # apinfo.ru/export.csv contains rows:
        # SVO|UUEE|Шереметьево|Sheremetyevo|Москва|Moscow|...
        # WTC|WATC||World Trade Center|Нью-Йорк|New York|...
        self.assertEqual(self.gp.airport_names('SVO'),
                         ('Sheremetyevo', 'Шереметьево'))
        self.assertEqual(self.gp.airport_names('WTC'),
                         ('World Trade Center', ''))
        self.assertIsNone(self.gp.airport_names('XXX'))

    def test_country_city_by_iata(self):
        # apinfo.ru/export.csv contains rows:
        # SVO|UUEE|...|Moscow|...|Russian Federation|RU|...
        # WTC|WATC|...|New York|...|United States|US|...
        self.assertEqual(self.gp.country_city_by_iata('SVO'),
                         ('RU', 'Moscow'))
        self.assertEqual(self.gp.country_city_by_iata('WTC'),
                         ('US', 'New York'))
        self.assertIsNone(self.gp.country_city_by_iata('XXX'))

    def test_alternative_city_names(self):
        # geonames.org/cities1000.csv contains rows:
        # ...  Saint Petersburg  ...  ...,Saint-Petersburg,...,St Petersburg,St. Petersburg,...  ...  RU  ...
        # apinfo.ru/export.csv uses only one form - "St Petersburg"
        spb_names_pair = ('St Petersburg', 'Санкт-Петербург')
        spb_latlon_pair = ('59.89444', '30.26417')
        for alt_name in ('Saint Petersburg', 'Saint-Petersburg', 'St. Petersburg'):
            self.assertEqual(self.gp.city_names('RU', alt_name),
                             spb_names_pair)
            self.assertEqual(self.gp.city_latlon('RU', alt_name),
                             spb_latlon_pair)
        self.assertIsNone(self.gp.city_names('RU', 'Saint X Petersburg'))


if __name__ == '__main__':
    unittest.main()
