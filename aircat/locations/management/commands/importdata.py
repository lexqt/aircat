# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import itertools
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from locations.management import dataimporter


class Command(BaseCommand):

    default_format = ('row_num,airport_name,city_name,country_name,iata,icao,'
                      'lat,lon,alt,dst,utc_offset')
    required_cols = ('iata', 'lat', 'lon', 'alt', )

    option_list = BaseCommand.option_list + (
        make_option('--buffer',
            action='store',
            dest='buffer_size',
            default=200,
            type='int',
            help='Set buffer size for bulk insert operations'),
    )

    args = '[<input_file> <input_format>]'
    help = '''Imports airport data from csv into DB, complementing it with
              country/city information.
              Default "input_format": ''' + default_format

    def handle(self, *args, **options):
        args_cnt = len(args)
        if args_cnt < 1 or args_cnt > 2:
            raise CommandError('Command takes one required and one optional'
                               ' argument')

        input_file = args[0]
        if not os.path.isfile(input_file):
            raise CommandError('Specified input file is not a file')

        cols_format = args[1] if args_cnt > 1 else self.default_format
        columns = cols_format.split(',')
        columns = dict(itertools.izip(columns, itertools.count()))
        for c in self.required_cols:
            if c not in columns:
                raise CommandError('Missed required column: {0}'.format(c))

        try:
            with open(input_file, 'rb') as f:
                self.stdout.write('Initializing data importer '
                                  '(this may take some time)... ', ending='')
                self.stdout.flush()
                try:
                    importer = dataimporter.DataImporter(
                        columns, stdout=self.stdout, stderr=self.stderr)
                except dataimporter.Error:
                    self.stdout.write('ERROR')
                    raise CommandError('Can not continue processing')
                else:
                    self.stdout.write('DONE')

                importer.start(f, buffer_size=options['buffer_size'])
        except IOError as e:
            raise CommandError('Can not open file: {0}'.format(e))
